import base64
import contextlib
import io
import sys
from unittest import mock

import pytest
import requests

from yandex_cli._common import creds, parse_raw_xml, post_json
from yandex_cli.client import YandexSearchClient
from yandex_cli.main import search
from yandex_cli.parsers import parse_web_xml


def raw(xml):
    return base64.b64encode(xml.encode()).decode()


def docs(*urls):
    entries = "".join(f"<doc><url>{url}</url></doc>" for url in urls)
    return {
        "rawData": raw(f"<yandexsearch><response>{entries}</response></yandexsearch>")
    }


class Response:
    def __init__(self, status=200, payload=None, headers=None):
        self.status_code = status
        self.payload = payload or {"ok": True}
        self.headers = headers or {}
        self.closed = False

    def json(self):
        return self.payload

    def close(self):
        self.closed = True


def test_pagination_deduplicates_urls_and_preserves_order():
    post = mock.Mock(
        side_effect=[
            docs("https://a.ru", "https://b.ru"),
            docs("https://b.ru", "https://c.ru"),
        ]
    )
    with mock.patch("yandex_cli.client.post_json", post):
        results = YandexSearchClient("key", "folder", timeout=12).web_search(
            "topic",
            search_type="SEARCH_TYPE_RU",
            num_results=2,
            page=1,
            pages=2,
            region="54",
        )
    assert [doc["url"] for doc in results] == [
        "https://a.ru",
        "https://b.ru",
        "https://c.ru",
    ]
    assert [call.args[2]["query"]["page"] for call in post.call_args_list] == [1, 2]
    assert all(call.args[2]["region"] == "54" for call in post.call_args_list)
    assert all(call.kwargs["timeout"] == 12 for call in post.call_args_list)


def test_pagination_stops_at_empty_page():
    post = mock.Mock(side_effect=[docs("https://a.ru"), docs()])
    with mock.patch("yandex_cli.client.post_json", post):
        results = YandexSearchClient("key", "folder").web_search(
            "topic", search_type="SEARCH_TYPE_RU", num_results=1, page=0, pages=3
        )
    assert len(results) == 1
    assert post.call_count == 2


@pytest.mark.parametrize("code", ["1", "18", "32", "42", "55", "100"])
def test_xml_errors_do_not_masquerade_as_empty_results(code):
    with pytest.raises(SystemExit, match=f"XML error {code}"):
        parse_raw_xml(
            raw(
                f'<yandexsearch><response><error code="{code}">error</error></response></yandexsearch>'
            ),
            "web search",
        )


def test_xml_no_results_is_successful_empty_list():
    assert (
        parse_web_xml(
            raw(
                '<yandexsearch><response><error code="15">no results</error></response></yandexsearch>'
            )
        )
        == []
    )


@pytest.mark.parametrize(
    "modtime, expected",
    [
        ("20260115T120000", "2026-01-15"),
        ("2026-01-15T12:00:00Z", "2026-01-15"),
        ("20260230", ""),
        ("garbage", ""),
        ("", ""),
    ],
)
def test_modification_dates_are_parsed_without_inventing_publication_dates(
    modtime, expected
):
    results = parse_web_xml(
        raw(f"<yandexsearch><doc><modtime>{modtime}</modtime></doc></yandexsearch>")
    )
    assert results[0]["date"] == expected


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_transient_http_failures_retry_with_retry_after(status):
    first = Response(status=status, headers={"Retry-After": "2"})
    with (
        mock.patch(
            "yandex_cli._common.requests.post", side_effect=[first, Response()]
        ) as post,
        mock.patch("yandex_cli._common.time.sleep") as sleep,
    ):
        assert post_json("/web/search", "key", {"folderId": "folder"}, timeout=12) == {
            "ok": True
        }
    assert post.call_count == 2
    assert first.closed
    sleep.assert_called_once_with(2)


def test_transient_connection_failure_recovers():
    with (
        mock.patch(
            "yandex_cli._common.requests.post",
            side_effect=[requests.ConnectionError(), Response()],
        ) as post,
        mock.patch("yandex_cli._common.time.sleep") as sleep,
    ):
        post_json("/web/search", "key", {"folderId": "folder"}, timeout=12)
    assert post.call_count == 2
    sleep.assert_called_once_with(1)


def test_retry_exhaustion_is_bounded():
    with (
        mock.patch(
            "yandex_cli._common.requests.post", return_value=Response(status=503)
        ) as post,
        mock.patch("yandex_cli._common.time.sleep") as sleep,
    ):
        with pytest.raises(SystemExit, match="503"):
            post_json("/web/search", "key", {"folderId": "folder"}, timeout=12)
    assert post.call_count == 3
    assert sleep.call_args_list == [mock.call(1), mock.call(2)]


def test_generative_requests_are_not_automatically_replayed():
    with (
        mock.patch(
            "yandex_cli._common.requests.post", return_value=Response(status=503)
        ) as post,
        mock.patch("yandex_cli._common.time.sleep") as sleep,
    ):
        with pytest.raises(SystemExit):
            post_json("/gen/search", "key", {"folderId": "folder"}, timeout=12)
    assert post.call_count == 1
    sleep.assert_not_called()


def test_authentication_failure_does_not_retry():
    with mock.patch(
        "yandex_cli._common.requests.post", return_value=Response(status=401)
    ) as post:
        with pytest.raises(SystemExit, match="Authentication failed"):
            post_json("/web/search", "key", {"folderId": "folder"}, timeout=12)
    assert post.call_count == 1


def test_error_body_redacts_credentials():
    response = Response(
        status=400, payload={"message": "bad private-api-key private-folder-id"}
    )
    with mock.patch("yandex_cli._common.requests.post", return_value=response):
        with pytest.raises(SystemExit) as exc:
            post_json(
                "/web/search",
                "private-api-key",
                {"folderId": "private-folder-id"},
                timeout=12,
            )
    assert "private-api-key" not in str(exc.value)
    assert "private-folder-id" not in str(exc.value)
    assert "[REDACTED]" in str(exc.value)


@pytest.mark.parametrize(
    "args",
    [
        ["topic", "-n", "101"],
        [" ", "--json"],
        ["x" * 401],
        ["x" * 390, "--site", "cyberleninka.ru"],
        ["topic", "--timeout", "nan"],
        ["topic", "--timeout", "-1"],
        ["topic", "--pages", "0"],
        ["topic", "-n", "100", "--pages", "4"],
        ["topic", "-t", "com", "--region", "213"],
    ],
)
def test_invalid_search_arguments_fail_before_credentials(args, monkeypatch):
    credentials = mock.Mock()
    monkeypatch.setattr("yandex_cli.main._creds", credentials)
    monkeypatch.setattr(sys, "argv", ["yandex-search", *args])
    with contextlib.redirect_stderr(io.StringIO()), pytest.raises(SystemExit) as exc:
        search()
    assert exc.value.code == 2
    credentials.assert_not_called()


def test_non_object_config_has_clean_error(tmp_path, monkeypatch):
    from pathlib import Path

    config = tmp_path / ".search-api"
    config.mkdir()
    (config / "config.json").write_text("[]")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    with pytest.raises(SystemExit, match="must be a JSON object"):
        creds()
