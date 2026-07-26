import json
from pathlib import Path
from unittest import mock

import pytest
import requests

from yandex_cli._common import (
    creds,
    handle_error,
    nonnegative_int,
    parse_raw_xml,
    positive_int,
    post_json,
)


class Response:
    def __init__(self, status_code=200, payload=None, text="", json_error=False):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise ValueError("not json")
        return self._payload


def test_creds_reads_valid_config(tmp_path, monkeypatch):
    config_dir = tmp_path / ".search-api"
    config_dir.mkdir()
    (config_dir / "config.json").write_text(
        json.dumps({"apiKey": "key", "folderId": "folder"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    assert creds() == ("key", "folder")


def test_creds_rejects_empty_config_values(tmp_path, monkeypatch):
    config_dir = tmp_path / ".search-api"
    config_dir.mkdir()
    (config_dir / "config.json").write_text(
        json.dumps({"apiKey": "", "folderId": "folder"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    with pytest.raises(SystemExit, match="apiKey must be a non-empty string"):
        creds()


def test_creds_reads_environment_when_config_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("YANDEX_API_KEY", "key")
    monkeypatch.setenv("YANDEX_FOLDER_ID", "folder")

    assert creds() == ("key", "folder")


def test_positive_int_rejects_zero():
    with pytest.raises(Exception, match="must be >= 1"):
        positive_int("0")


def test_nonnegative_int_rejects_negative():
    with pytest.raises(Exception, match="must be >= 0"):
        nonnegative_int("-1")


def test_handle_error_exits_with_yandex_error_body():
    resp = Response(status_code=500, payload={"message": "backend unavailable"})

    with pytest.raises(
        SystemExit, match="Yandex Search API error 500: backend unavailable"
    ):
        handle_error(resp)


def test_post_json_exits_on_network_error():
    with mock.patch(
        "yandex_cli._common.requests.post",
        side_effect=requests.Timeout("timed out"),
    ):
        with pytest.raises(SystemExit, match="Request to Yandex Search API failed"):
            post_json("/web/search", "key", {"folderId": "folder"}, timeout=1)


def test_post_json_exits_on_invalid_json():
    with mock.patch(
        "yandex_cli._common.requests.post",
        return_value=Response(status_code=200, json_error=True),
    ):
        with pytest.raises(SystemExit, match="returned invalid JSON"):
            post_json("/web/search", "key", {"folderId": "folder"}, timeout=1)


def test_parse_raw_xml_rejects_missing_raw_data():
    with pytest.raises(SystemExit, match="missing rawData"):
        parse_raw_xml(None, "web search")


def test_parse_raw_xml_rejects_invalid_base64():
    with pytest.raises(SystemExit, match="invalid rawData XML"):
        parse_raw_xml("not-base64", "web search")
