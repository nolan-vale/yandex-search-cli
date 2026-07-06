import json
import os
import sys
from pathlib import Path

import requests

BASE_URL = "https://searchapi.api.cloud.yandex.net/v2"


def creds() -> tuple[str, str]:
    config_path = Path.home() / ".search-api" / "config.json"
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text())
            return cfg["apiKey"], cfg["folderId"]
        except (KeyError, json.JSONDecodeError) as e:
            sys.exit(f"Invalid config at {config_path}: {e}")
    api_key = os.environ.get("YANDEX_API_KEY", "")
    folder_id = os.environ.get("YANDEX_FOLDER_ID", "")
    if not api_key or not folder_id:
        sys.exit(
            "Credentials not found.\n"
            "Option 1: create ~/.search-api/config.json with {\"apiKey\": \"...\", \"folderId\": \"...\"}\n"
            "Option 2: export YANDEX_API_KEY=... && export YANDEX_FOLDER_ID=..."
        )
    return api_key, folder_id


def headers(api_key: str) -> dict:
    return {"Authorization": f"Api-Key {api_key}", "Content-Type": "application/json"}


def handle_error(resp: requests.Response) -> None:
    if resp.status_code == 401:
        sys.exit("Authentication failed — check your API key")
    if resp.status_code == 403:
        sys.exit("Access denied — check your folder ID and API permissions")
    if resp.status_code == 429:
        sys.exit("Rate limit exceeded — slow down or upgrade your Yandex Cloud quota")
    resp.raise_for_status()
