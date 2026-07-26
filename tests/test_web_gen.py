import base64
import contextlib
import io
import json
import sys
from unittest import mock

import pytest

from yandex_cli.main import _parse_web_xml, gen, search


WEB_XML = """<?xml version="1.0" encoding="utf-8"?>
<yandexsearch version="1.0">
<response>
<results>
<grouping>
<group>
<doc>
<url>https://example.com/page</url>
<domain>example.com</domain>
<title>Example Page</title>
<modtime>20260115T120000</modtime>
<passages><passage>Example passage</passage></passages>
</doc>
</group>
</grouping>
</results>
</response>
</yandexsearch>
"""


def _web_b64() -> str:
    return base64.b64encode(WEB_XML.encode("utf-8")).decode()


def test_parse_web_xml_extracts_document_fields():
    docs = _parse_web_xml(_web_b64())

    assert docs == [
        {
            "title": "Example Page",
            "url": "https://example.com/page",
            "domain": "example.com",
            "date": "2026-01-15",
            "passages": ["Example passage"],
        }
    ]


def test_search_json_entrypoint_outputs_parsed_docs(monkeypatch):
    monkeypatch.setattr("yandex_cli.main._creds", lambda: ("key", "folder"))
    client = mock.Mock()
    client.web_search.return_value = [{"url": "https://example.com/page"}]
    client_class = mock.Mock(return_value=client)
    monkeypatch.setattr("yandex_cli.main.YandexSearchClient", client_class)
    monkeypatch.setattr(
        sys,
        "argv",
        ["yandex-search", "topic", "--site", "example.com", "-n", "3", "--json"],
    )
    stdout = io.StringIO()

    with contextlib.redirect_stdout(stdout):
        search()

    payload = json.loads(stdout.getvalue())
    assert payload[0]["url"] == "https://example.com/page"
    client_class.assert_called_once_with("key", "folder")
    client.web_search.assert_called_once_with(
        "site:example.com topic",
        search_type="SEARCH_TYPE_RU",
        num_results=3,
        page=0,
        region=None,
    )


def test_search_rejects_negative_page_before_credentials(monkeypatch):
    creds = mock.Mock()
    monkeypatch.setattr("yandex_cli.main._creds", creds)
    monkeypatch.setattr(sys, "argv", ["yandex-search", "topic", "--page", "-1"])

    with pytest.raises(SystemExit):
        search()

    creds.assert_not_called()


def test_gen_json_entrypoint_accepts_list_response(monkeypatch):
    monkeypatch.setattr("yandex_cli.main._creds", lambda: ("key", "folder"))
    client = mock.Mock()
    client.generative_search.return_value = {"message": {"content": "answer"}}
    monkeypatch.setattr(
        "yandex_cli.main.YandexSearchClient", mock.Mock(return_value=client)
    )
    monkeypatch.setattr(sys, "argv", ["yandex-gen", "question", "--json"])
    stdout = io.StringIO()

    with contextlib.redirect_stdout(stdout):
        gen()

    payload = json.loads(stdout.getvalue())
    assert payload["message"]["content"] == "answer"
    client.generative_search.assert_called_once_with("question", site=None)
