from __future__ import annotations

import argparse
import base64
import binascii
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

import defusedxml.ElementTree as ET
from defusedxml.common import DefusedXmlException
import requests

BASE_URL = "https://searchapi.api.cloud.yandex.net/v2"

SEARCH_TYPES = {
    "ru": "SEARCH_TYPE_RU",
    "com": "SEARCH_TYPE_COM",
    "tr": "SEARCH_TYPE_TR",
    "kk": "SEARCH_TYPE_KK",
    "be": "SEARCH_TYPE_BE",
    "uz": "SEARCH_TYPE_UZ",
}


def xml_text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    return "".join(el.itertext()).strip()


def creds() -> tuple[str, str]:
    config_path = Path.home() / ".search-api" / "config.json"
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
            if not isinstance(cfg, dict):
                raise ValueError("configuration must be a JSON object")
            api_key = cfg["apiKey"]
            folder_id = cfg["folderId"]
            if not isinstance(api_key, str) or not api_key.strip():
                raise ValueError("apiKey must be a non-empty string")
            if not isinstance(folder_id, str) or not folder_id.strip():
                raise ValueError("folderId must be a non-empty string")
            return api_key.strip(), folder_id.strip()
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as e:
            sys.exit(f"Invalid config at {config_path}: {e}")
    api_key = os.environ.get("YANDEX_API_KEY", "").strip()
    folder_id = os.environ.get("YANDEX_FOLDER_ID", "").strip()
    if not api_key or not folder_id:
        sys.exit(
            "Credentials not found.\n"
            'Option 1: create ~/.search-api/config.json with {"apiKey": "...", "folderId": "..."}\n'
            "Option 2: export YANDEX_API_KEY=... && export YANDEX_FOLDER_ID=..."
        )
    return api_key, folder_id


def headers(api_key: str) -> dict:
    return {"Authorization": f"Api-Key {api_key}", "Content-Type": "application/json"}


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError("must be an integer") from e
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def nonnegative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError("must be an integer") from e
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def result_count(value: str) -> int:
    parsed = positive_int(value)
    if parsed > 100:
        raise argparse.ArgumentTypeError("must be between 1 and 100")
    return parsed


def positive_seconds(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("must be a finite number > 0")
    return parsed


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--timeout",
        type=positive_seconds,
        default=30,
        help="HTTP connect/read timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version('yandex-search-cli')}",
    )


def _error_detail(resp: requests.Response) -> str:
    try:
        data = resp.json()
    except ValueError:
        data = resp.text

    if isinstance(data, dict):
        for key in ("message", "error", "description"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        details = data.get("details")
        if details:
            return json.dumps(details, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)

    return str(data).strip()


def handle_error(resp: requests.Response, secrets: tuple[str, ...] = ()) -> None:
    if resp.status_code == 401:
        sys.exit("Authentication failed — check your API key")
    if resp.status_code == 403:
        sys.exit("Access denied — check your folder ID and API permissions")
    if resp.status_code == 429:
        sys.exit("Rate limit exceeded — slow down or upgrade your Yandex Cloud quota")
    if resp.status_code >= 400:
        detail = _error_detail(resp)
        for secret in sorted(filter(None, secrets), key=len, reverse=True):
            detail = detail.replace(secret, "[REDACTED]")
        suffix = f": {detail[:500]}" if detail else ""
        sys.exit(f"Yandex Search API error {resp.status_code}{suffix}")


def _retry_delay(resp: requests.Response, attempt: int) -> float:
    value = getattr(resp, "headers", {}).get("Retry-After", "")
    try:
        delay = float(value)
    except (TypeError, ValueError):
        try:
            delay = (
                parsedate_to_datetime(value) - datetime.now(timezone.utc)
            ).total_seconds()
        except (TypeError, ValueError, OverflowError):
            delay = 2**attempt
    return min(30, max(0, delay)) if math.isfinite(delay) else 2**attempt


def post_json(path: str, api_key: str, body: dict[str, Any], timeout: float) -> Any:
    # Retry only retrieval calls. Generative requests may incur additional work.
    attempts = 1 if path == "/gen/search" else 3
    for attempt in range(attempts):
        try:
            resp = requests.post(
                f"{BASE_URL}{path}",
                headers=headers(api_key),
                json=body,
                timeout=timeout,
            )
        except (requests.ConnectionError, requests.Timeout) as exc:
            if attempt + 1 < attempts:
                time.sleep(2**attempt)
                continue
            sys.exit(f"Request to Yandex Search API failed ({type(exc).__name__})")
        except requests.RequestException as exc:
            sys.exit(f"Request to Yandex Search API failed ({type(exc).__name__})")

        if resp.status_code in (429, 500, 502, 503, 504) and attempt + 1 < attempts:
            delay = _retry_delay(resp, attempt)
            resp.close()
            time.sleep(delay)
            continue
        break

    handle_error(resp, secrets=(api_key, body.get("folderId", "")))

    try:
        return resp.json()
    except ValueError:
        sys.exit("Yandex Search API returned invalid JSON")


def parse_raw_xml(raw_b64: object, endpoint: str) -> ET.Element:
    if not isinstance(raw_b64, str) or not raw_b64:
        sys.exit(f"Yandex {endpoint} response missing rawData")
    try:
        xml_bytes = base64.b64decode(raw_b64, validate=True)
        root = ET.fromstring(xml_bytes.decode("utf-8"))
    except (
        binascii.Error,
        UnicodeDecodeError,
        ET.ParseError,
        DefusedXmlException,
    ) as e:
        sys.exit(f"Yandex {endpoint} response contained invalid rawData XML: {e}")
    error = root.find(".//error")
    if error is not None:
        code = error.get("code", "")
        if code != "15":
            safe_code = code if code.isdecimal() else "unknown"
            sys.exit(
                f"Yandex {endpoint} XML error {safe_code}; check query, credentials and quota"
            )
    return root
