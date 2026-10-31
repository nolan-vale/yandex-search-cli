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
    client_class.assert_called_once_with("key", "folder", timeout=30)
    client.web_search.assert_called_once_with(
        "site:example.com topic",
        search_type="SEARCH_TYPE_RU",
        num_results=3,
        page=0,
        region=None,
        pages=1,
        period=None,
        sort_mode=None,
        sort_order=None,
    )


@pytest.mark.parametrize(
    ("period", "api_period"),
    [
        ("all", "PERIOD_ALL_TIME"),
        ("day", "PERIOD_DAY"),
        ("2weeks", "PERIOD_2_WEEKS"),
        ("month", "PERIOD_MONTH"),
    ],
)
def test_search_passes_freshness_filter_to_client(period, api_period, monkeypatch):
    monkeypatch.setattr("yandex_cli.main._creds", lambda: ("key", "folder"))
    client = mock.Mock()
    client.web_search.return_value = []
    monkeypatch.setattr(
        "yandex_cli.main.YandexSearchClient", mock.Mock(return_value=client)
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["yandex-search", "topic", "--period", period, "--pages", "2", "--json"],
    )
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        search()

    assert json.loads(stdout.getvalue()) == []
    assert client.web_search.call_args.kwargs["period"] == api_period
    assert client.web_search.call_args.kwargs["pages"] == 2


def test_search_rejects_negative_page_before_credentials(monkeypatch):
    creds = mock.Mock()
    monkeypatch.setattr("yandex_cli.main._creds", creds)
    monkeypatch.setattr(sys, "argv", ["yandex-search", "topic", "--page", "-1"])

    with pytest.raises(SystemExit):
        search()

    creds.assert_not_called()


@pytest.mark.parametrize(
    ("args", "mode", "order"),
    [
        (["--sort", "time"], "SORT_MODE_BY_TIME", None),
        (["--sort", "time", "--order", "asc"], "SORT_MODE_BY_TIME", "SORT_ORDER_ASC"),
        (["--sort", "time", "--order", "desc"], "SORT_MODE_BY_TIME", "SORT_ORDER_DESC"),
        (["--sort", "relevance"], "SORT_MODE_BY_RELEVANCE", None),
    ],
)
def test_search_passes_sorting_with_period_and_pagination(
    args, mode, order, monkeypatch
):
    monkeypatch.setattr("yandex_cli.main._creds", lambda: ("key", "folder"))
    client = mock.Mock()
    client.web_search.return_value = []
    monkeypatch.setattr(
        "yandex_cli.main.YandexSearchClient", mock.Mock(return_value=client)
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["yandex-search", "topic", "--period", "day", "--pages", "2", "--json", *args],
    )
    with contextlib.redirect_stdout(io.StringIO()):
        search()
    assert client.web_search.call_args.kwargs["sort_mode"] == mode
    assert client.web_search.call_args.kwargs["sort_order"] == order
    assert client.web_search.call_args.kwargs["period"] == "PERIOD_DAY"
    assert client.web_search.call_args.kwargs["pages"] == 2


@pytest.mark.parametrize(
    "args",
    [
        ["--order", "asc"],
        ["--sort", "relevance", "--order", "desc"],
        ["--sort", "invalid"],
        ["--sort", "time", "--order", "invalid"],
    ],
)
def test_search_rejects_invalid_sorting_before_credentials(args, monkeypatch):
    credentials = mock.Mock()
    monkeypatch.setattr("yandex_cli.main._creds", credentials)
    monkeypatch.setattr(sys, "argv", ["yandex-search", "topic", *args])
    with contextlib.redirect_stderr(io.StringIO()), pytest.raises(SystemExit) as exc:
        search()
    assert exc.value.code == 2
    credentials.assert_not_called()


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
    client.generative_search.assert_called_once_with(
        messages=[{"role": "ROLE_USER", "content": "question"}],
        site=None,
        doc_format=None,
        lang=None,
        date_filter=None,
    )


@pytest.mark.parametrize("input_source", ["file", "stdin"])
@pytest.mark.parametrize("follow_up", [None, "How do I connect it to MCP?"])
def test_gen_sends_dialogue_from_file_or_stdin(
    input_source, follow_up, tmp_path, monkeypatch
):
    history = [
        {"role": "user", "content": "What is Yandex Search API?"},
        {"role": "assistant", "content": "A web search service."},
    ]
    question = "How do I connect it to MCP?"
    if follow_up is None:
        history.append({"role": "user", "content": question})
    raw = json.dumps(history)
    if input_source == "file":
        path = tmp_path / "conversation.json"
        path.write_text(raw, encoding="utf-8")
        messages_file = str(path)
    else:
        monkeypatch.setattr(sys, "stdin", io.StringIO(raw))
        messages_file = "-"
    args = ["yandex-gen"]
    if follow_up is not None:
        args.append(follow_up)
    args.extend(
        [
            "--messages-file",
            messages_file,
            "--site",
            "yandex.cloud",
            "--timeout",
            "12",
            "--json",
        ]
    )
    monkeypatch.setattr(sys, "argv", args)
    monkeypatch.setattr("yandex_cli.main._creds", lambda: ("key", "folder"))
    client = mock.Mock()
    response = {"message": {"content": "Use the search MCP server."}, "sources": []}
    client.generative_search.return_value = response
    client_class = mock.Mock(return_value=client)
    monkeypatch.setattr("yandex_cli.main.YandexSearchClient", client_class)
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        gen()

    assert json.loads(stdout.getvalue()) == response
    client_class.assert_called_once_with("key", "folder", timeout=12)
    client.generative_search.assert_called_once_with(
        messages=[
            {"role": "ROLE_USER", "content": "What is Yandex Search API?"},
            {"role": "ROLE_ASSISTANT", "content": "A web search service."},
            {"role": "ROLE_USER", "content": question},
        ],
        site="yandex.cloud",
        doc_format=None,
        lang=None,
        date_filter=None,
    )
    if input_source == "file":
        assert path.read_text(encoding="utf-8") == raw


def test_gen_passes_all_filters_with_dialogue_and_preserves_json(monkeypatch):
    monkeypatch.setattr("yandex_cli.main._creds", lambda: ("key", "folder"))
    monkeypatch.setattr(
        sys, "stdin", io.StringIO('[{"role":"assistant","content":"context"}]')
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yandex-gen",
            "follow-up",
            "--messages-file",
            "-",
            "--site",
            "example.com",
            "--format",
            "PDF",
            "--lang",
            "RU",
            "--date",
            ">=20250101",
            "--json",
        ],
    )
    response = {"message": {"content": "answer"}, "sources": []}
    client = mock.Mock()
    client.generative_search.return_value = response
    monkeypatch.setattr(
        "yandex_cli.main.YandexSearchClient", mock.Mock(return_value=client)
    )
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        gen()
    assert json.loads(stdout.getvalue()) == response
    client.generative_search.assert_called_once_with(
        messages=[
            {"role": "ROLE_ASSISTANT", "content": "context"},
            {"role": "ROLE_USER", "content": "follow-up"},
        ],
        site="example.com",
        doc_format="pdf",
        lang="ru",
        date_filter=">=20250101",
    )


@pytest.mark.parametrize(
    "args",
    [
        ["--format", "docx"],
        ["--lang", "rus"],
        ["--lang", "ru-RU"],
        ["--date", "2025-01-01"],
        ["--date", "20260229"],
        ["--date", "202513*"],
        ["--date", "20251231..20250101"],
    ],
)
def test_gen_rejects_invalid_filters_before_credentials(args, monkeypatch):
    credentials = mock.Mock()
    monkeypatch.setattr("yandex_cli.main._creds", credentials)
    monkeypatch.setattr(sys, "argv", ["yandex-gen", "query", *args])
    with contextlib.redirect_stderr(io.StringIO()), pytest.raises(SystemExit) as exc:
        gen()
    assert exc.value.code == 2
    credentials.assert_not_called()


@pytest.mark.parametrize(
    "contents",
    [
        pytest.param(b"not-json-private-message", id="invalid-json"),
        pytest.param(b"\xff", id="invalid-utf8"),
        pytest.param(b"{}", id="not-an-array"),
        pytest.param(b"null", id="null"),
        pytest.param(b"[]", id="empty-history"),
        pytest.param(b"[null]", id="non-object-message"),
        pytest.param(b'[{"role":"system","content":"private"}]', id="unsupported-role"),
        pytest.param(b'[{"role":"user","content":" "}]', id="empty-content"),
    ],
)
def test_gen_rejects_invalid_history_before_credentials(
    contents, tmp_path, monkeypatch
):
    path = tmp_path / "conversation.json"
    path.write_bytes(contents)
    credentials = mock.Mock()
    monkeypatch.setattr("yandex_cli.main._creds", credentials)
    monkeypatch.setattr(sys, "argv", ["yandex-gen", "--messages-file", str(path)])
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr), pytest.raises(SystemExit) as exc:
        gen()
    assert exc.value.code == 2
    credentials.assert_not_called()
    assert "private" not in stderr.getvalue()


def test_gen_rejects_missing_history_file_before_credentials(tmp_path, monkeypatch):
    credentials = mock.Mock()
    monkeypatch.setattr("yandex_cli.main._creds", credentials)
    monkeypatch.setattr(
        sys, "argv", ["yandex-gen", "--messages-file", str(tmp_path / "missing.json")]
    )
    with contextlib.redirect_stderr(io.StringIO()), pytest.raises(SystemExit) as exc:
        gen()
    assert exc.value.code == 2
    credentials.assert_not_called()


@pytest.mark.parametrize(
    "query", [None, " ", "x" * 16385], ids=["missing", "blank", "long"]
)
def test_gen_rejects_invalid_query_before_credentials(query, monkeypatch):
    credentials = mock.Mock()
    monkeypatch.setattr("yandex_cli.main._creds", credentials)
    monkeypatch.setattr(
        sys, "argv", ["yandex-gen", *([query] if query is not None else [])]
    )
    with contextlib.redirect_stderr(io.StringIO()), pytest.raises(SystemExit) as exc:
        gen()
    assert exc.value.code == 2
    credentials.assert_not_called()
