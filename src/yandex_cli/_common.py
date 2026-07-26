from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import sys
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
            api_key = cfg["apiKey"]
            folder_id = cfg["folderId"]
            if not isinstance(api_key, str) or not api_key.strip():
                raise ValueError("apiKey must be a non-empty string")
            if not isinstance(folder_id, str) or not folder_id.strip():
                raise ValueError("folderId must be a non-empty string")
            return api_key, folder_id
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as e:
            sys.exit(f"Invalid config at {config_path}: {e}")
    api_key = os.environ.get("YANDEX_API_KEY", "")
    folder_id = os.environ.get("YANDEX_FOLDER_ID", "")
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


def handle_error(resp: requests.Response) -> None:
    if resp.status_code == 401:
        sys.exit("Authentication failed — check your API key")
    if resp.status_code == 403:
        sys.exit("Access denied — check your folder ID and API permissions")
    if resp.status_code == 429:
        sys.exit("Rate limit exceeded — slow down or upgrade your Yandex Cloud quota")
    if resp.status_code >= 400:
        detail = _error_detail(resp)
        suffix = f": {detail[:500]}" if detail else ""
        sys.exit(f"Yandex Search API error {resp.status_code}{suffix}")


def post_json(path: str, api_key: str, body: dict[str, Any], timeout: int) -> Any:
    try:
        resp = requests.post(
            f"{BASE_URL}{path}",
            headers=headers(api_key),
            json=body,
            timeout=timeout,
        )
    except requests.RequestException as e:
        sys.exit(f"Request to Yandex Search API failed: {e}")

    handle_error(resp)

    try:
        return resp.json()
    except ValueError:
        sys.exit("Yandex Search API returned invalid JSON")


def parse_raw_xml(raw_b64: object, endpoint: str) -> ET.Element:
    if not isinstance(raw_b64, str) or not raw_b64:
        sys.exit(f"Yandex {endpoint} response missing rawData")
    try:
        xml_bytes = base64.b64decode(raw_b64, validate=True)
        return ET.fromstring(xml_bytes.decode("utf-8"))
    except (
        binascii.Error,
        UnicodeDecodeError,
        ET.ParseError,
        DefusedXmlException,
    ) as e:
        sys.exit(f"Yandex {endpoint} response contained invalid rawData XML: {e}")
