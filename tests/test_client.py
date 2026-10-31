import base64
from copy import deepcopy
from unittest import mock

import pytest

from yandex_cli.client import YandexSearchClient

WEB_XML = """<?xml version="1.0" encoding="utf-8"?>
<yandexsearch><response><results><grouping><group><doc>
<url>https://example.com/page</url>
<domain>example.com</domain>
<title>Example Page</title>
<modtime>20260115T120000</modtime>
<passages><passage>Example passage</passage></passages>
</doc></group></grouping></results></response></yandexsearch>
"""


IMAGE_XML = """<?xml version="1.0" encoding="utf-8"?>
<yandexsearch><response><results><grouping><group><doc>
<url>https://example.com/a.png</url>
<domain>example.com</domain>
<image-properties>
<thumbnail-link>https://thumb.example.com/a.png</thumbnail-link>
<original-width>10</original-width>
<original-height>20</original-height>
<html-link>https://example.com/page</html-link>
<mime-type>png</mime-type>
</image-properties>
</doc></group></grouping></results></response></yandexsearch>
"""


def _b64(xml: str) -> str:
    return base64.b64encode(xml.encode("utf-8")).decode()


def test_client_web_search_builds_request_and_parses_results():
    post_json = mock.Mock(return_value={"rawData": _b64(WEB_XML)})
    with mock.patch("yandex_cli.client.post_json", post_json):
        docs = YandexSearchClient("key", "folder").web_search(
            "site:example.com topic",
            search_type="SEARCH_TYPE_RU",
            num_results=3,
            page=2,
            region="213",
        )

    assert docs[0]["url"] == "https://example.com/page"
    assert post_json.call_args.args[:2] == ("/web/search", "key")
    body = post_json.call_args.args[2]
    assert body["folderId"] == "folder"
    assert body["query"] == {
        "searchType": "SEARCH_TYPE_RU",
        "queryText": "site:example.com topic",
        "page": 2,
    }
    assert body["region"] == "213"
    assert body["groupSpec"]["groupMode"] == "GROUP_MODE_FLAT"
    assert body["groupSpec"]["groupsOnPage"] == 3
    assert "period" not in body
    assert "sortSpec" not in body


@pytest.mark.parametrize(
    "period", ["PERIOD_ALL_TIME", "PERIOD_DAY", "PERIOD_2_WEEKS", "PERIOD_MONTH"]
)
def test_client_web_search_keeps_period_on_every_page(period):
    post_json = mock.Mock(return_value={"rawData": _b64(WEB_XML)})
    with mock.patch("yandex_cli.client.post_json", post_json):
        YandexSearchClient("key", "folder").web_search(
            "topic",
            search_type="SEARCH_TYPE_RU",
            num_results=3,
            page=1,
            pages=2,
            period=period,
        )

    bodies = [call.args[2] for call in post_json.call_args_list]
    assert [body["query"]["page"] for body in bodies] == [1, 2]
    assert all(body["period"] == period for body in bodies)
    assert all("period" not in body["query"] for body in bodies)


def test_client_web_search_rejects_non_dict_response():
    with (
        mock.patch("yandex_cli.client.post_json", return_value=[]),
        pytest.raises(SystemExit, match="web search returned an unexpected"),
    ):
        YandexSearchClient("key", "folder").web_search(
            "topic",
            search_type="SEARCH_TYPE_RU",
            num_results=1,
            page=0,
        )


@pytest.mark.parametrize(
    ("sort_mode", "sort_order", "expected"),
    [
        (
            "SORT_MODE_BY_TIME",
            None,
            {"sortMode": "SORT_MODE_BY_TIME"},
        ),
        (
            "SORT_MODE_BY_TIME",
            "SORT_ORDER_ASC",
            {"sortMode": "SORT_MODE_BY_TIME", "sortOrder": "SORT_ORDER_ASC"},
        ),
        (
            "SORT_MODE_BY_TIME",
            "SORT_ORDER_DESC",
            {"sortMode": "SORT_MODE_BY_TIME", "sortOrder": "SORT_ORDER_DESC"},
        ),
        (
            "SORT_MODE_BY_RELEVANCE",
            None,
            {"sortMode": "SORT_MODE_BY_RELEVANCE"},
        ),
    ],
)
def test_client_keeps_sorting_and_period_on_every_page(sort_mode, sort_order, expected):
    post_json = mock.Mock(return_value={"rawData": _b64(WEB_XML)})
    with mock.patch("yandex_cli.client.post_json", post_json):
        YandexSearchClient("key", "folder").web_search(
            "topic",
            search_type="SEARCH_TYPE_RU",
            num_results=3,
            page=0,
            pages=2,
            region="54",
            period="PERIOD_MONTH",
            sort_mode=sort_mode,
            sort_order=sort_order,
        )
    bodies = [call.args[2] for call in post_json.call_args_list]
    assert [body["query"]["page"] for body in bodies] == [0, 1]
    assert all(body["sortSpec"] == expected for body in bodies)
    assert all(body["period"] == "PERIOD_MONTH" for body in bodies)
    assert all(body["region"] == "54" for body in bodies)


@pytest.mark.parametrize(
    ("site", "site_options"),
    [
        (None, {}),
        ("example.com", {"site": {"site": ["example.com"]}}),
    ],
)
def test_client_generative_search_builds_request_and_accepts_list_response(
    site, site_options
):
    with mock.patch(
        "yandex_cli.client.post_json",
        return_value=[{"message": {"content": "answer"}}],
    ) as post_json:
        result = YandexSearchClient("key", "folder", timeout=12).generative_search(
            "question",
            site=site,
        )

    assert result["message"]["content"] == "answer"
    post_json.assert_called_once_with(
        "/gen/search",
        "key",
        {
            "folderId": "folder",
            "messages": [{"content": "question", "role": "ROLE_USER"}],
            "fixMisspell": True,
            **site_options,
        },
        timeout=12,
    )


def test_client_generative_search_rejects_empty_list_response():
    with (
        mock.patch("yandex_cli.client.post_json", return_value=[]),
        pytest.raises(SystemExit, match="empty response"),
    ):
        YandexSearchClient("key", "folder").generative_search("question")


def test_client_generative_search_appends_follow_up_without_changing_history():
    history = [
        {"role": "user", "content": "What is Yandex Search API?"},
        {"role": "assistant", "content": "A web search service."},
    ]
    original = deepcopy(history)
    response = {"message": {"content": "Use the search MCP server."}, "sources": []}
    with mock.patch("yandex_cli.client.post_json", return_value=response) as post_json:
        result = YandexSearchClient("key", "folder").generative_search(
            "How do I connect it to MCP?", messages=history, site="yandex.cloud"
        )

    assert result == response
    assert history == original
    body = post_json.call_args.args[2]
    assert body["messages"] == [
        {"role": "ROLE_USER", "content": "What is Yandex Search API?"},
        {"role": "ROLE_ASSISTANT", "content": "A web search service."},
        {"role": "ROLE_USER", "content": "How do I connect it to MCP?"},
    ]
    assert body["site"] == {"site": ["yandex.cloud"]}


def test_client_generative_search_accepts_a_complete_dialogue():
    messages = [
        {"role": "ROLE_USER", "content": "Find search APIs."},
        {"role": "ROLE_ASSISTANT", "content": "Yandex Search API is one option."},
        {"role": "ROLE_USER", "content": "Does it support Russian?"},
    ]
    with mock.patch("yandex_cli.client.post_json", return_value={}) as post_json:
        YandexSearchClient("key", "folder").generative_search(messages=messages)

    assert post_json.call_args.args[2]["messages"] == messages


def test_client_combines_generative_filters_with_site_and_dialogue():
    response = {"message": {"content": "answer"}, "sources": []}
    with mock.patch("yandex_cli.client.post_json", return_value=response) as post_json:
        result = YandexSearchClient("key", "folder", timeout=12).generative_search(
            "follow-up",
            messages=[{"role": "assistant", "content": "context"}],
            site="example.com",
            doc_format="PDF",
            lang="RU",
            date_filter=">=20250101",
        )
    assert result == response
    post_json.assert_called_once_with(
        "/gen/search",
        "key",
        {
            "folderId": "folder",
            "messages": [
                {"role": "ROLE_ASSISTANT", "content": "context"},
                {"role": "ROLE_USER", "content": "follow-up"},
            ],
            "fixMisspell": True,
            "site": {"site": ["example.com"]},
            "searchFilters": [
                {"format": "DOC_FORMAT_PDF"},
                {"lang": "ru"},
                {"date": ">=20250101"},
            ],
        },
        timeout=12,
    )


@pytest.mark.parametrize(
    ("doc_format", "expected"),
    [
        ("pdf", "DOC_FORMAT_PDF"),
        ("xls", "DOC_FORMAT_XLS"),
        ("ods", "DOC_FORMAT_ODS"),
        ("rtf", "DOC_FORMAT_RTF"),
        ("ppt", "DOC_FORMAT_PPT"),
        ("odp", "DOC_FORMAT_ODP"),
        ("swf", "DOC_FORMAT_SWF"),
        ("odt", "DOC_FORMAT_ODT"),
        ("odg", "DOC_FORMAT_ODG"),
        ("doc", "DOC_FORMAT_DOC"),
    ],
)
def test_client_serializes_document_format_filter(doc_format, expected):
    with mock.patch("yandex_cli.client.post_json", return_value={}) as post_json:
        YandexSearchClient("key", "folder").generative_search(
            "query", doc_format=doc_format
        )
    assert post_json.call_args.args[2]["searchFilters"] == [{"format": expected}]


@pytest.mark.parametrize(
    "date_filter",
    [
        "20240229",
        "<20250101",
        "<=20250101",
        ">20250101",
        ">=20250101",
        "20250101..20251231",
        "20250101..20250101",
        "202501*",
        "2025*",
    ],
)
def test_client_serializes_supported_date_filters(date_filter):
    with mock.patch("yandex_cli.client.post_json", return_value={}) as post_json:
        YandexSearchClient("key", "folder").generative_search(
            "query", date_filter=date_filter
        )
    assert post_json.call_args.args[2]["searchFilters"] == [{"date": date_filter}]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"doc_format": "mp3"},
        {"lang": "eng"},
        {"lang": "r1"},
        {"date_filter": "2026-01-01"},
        {"date_filter": "20260229"},
        {"date_filter": "20250230"},
        {"date_filter": "00000101"},
        {"date_filter": "202500*"},
        {"date_filter": "202513*"},
        {"date_filter": "20251231..20250101"},
        {"date_filter": ">>20250101"},
        {"date_filter": "20250101..garbage"},
        {"date_filter": "*"},
        {"date_filter": ""},
    ],
)
def test_client_rejects_invalid_generative_filters_before_network(kwargs):
    with (
        mock.patch("yandex_cli.client.post_json") as post_json,
        pytest.raises(ValueError),
    ):
        YandexSearchClient("key", "folder").generative_search("query", **kwargs)
    post_json.assert_not_called()


@pytest.mark.parametrize(
    ("messages", "query", "exception", "error"),
    [
        pytest.param({}, None, TypeError, "JSON array", id="object-instead-of-array"),
        pytest.param([], None, ValueError, "1 to 100", id="no-messages"),
        pytest.param([None], None, TypeError, "JSON object", id="non-object-message"),
        pytest.param([{}], None, ValueError, "role", id="missing-role"),
        pytest.param([{"role": []}], None, ValueError, "role", id="non-text-role"),
        pytest.param(
            [{"role": "system", "content": "unsupported"}],
            None,
            ValueError,
            "role",
            id="unsupported-role",
        ),
        pytest.param(
            [{"role": "user"}], None, ValueError, "content", id="missing-content"
        ),
        pytest.param(
            [{"role": "user", "content": 42}],
            None,
            ValueError,
            "content",
            id="non-text-content",
        ),
        pytest.param(
            [{"role": "user", "content": " "}],
            None,
            ValueError,
            "content",
            id="blank-content",
        ),
        pytest.param(
            [{"role": "user", "content": "x" * 16385}],
            None,
            ValueError,
            "16384",
            id="message-too-long",
        ),
        pytest.param(None, " ", ValueError, "content", id="blank-query"),
        pytest.param(None, "x" * 16385, ValueError, "16384", id="query-too-long"),
        pytest.param(
            [{"role": "user", "content": "question"}] * 100,
            "follow-up",
            ValueError,
            "1 to 100",
            id="follow-up-exceeds-message-limit",
        ),
    ],
)
def test_client_rejects_invalid_dialogue_before_network(
    messages, query, exception, error
):
    with (
        mock.patch("yandex_cli.client.post_json") as post_json,
        pytest.raises(exception, match=error),
    ):
        YandexSearchClient("key", "folder").generative_search(query, messages=messages)
    post_json.assert_not_called()


def test_client_accepts_api_message_count_and_length_limits():
    messages = [{"role": "user", "content": "x" * 16384}] * 100
    with mock.patch("yandex_cli.client.post_json", return_value={}) as post_json:
        YandexSearchClient("key", "folder").generative_search(messages=messages)
    assert len(post_json.call_args.args[2]["messages"]) == 100


def test_client_image_search_builds_request_and_parses_results():
    post_json = mock.Mock(return_value={"rawData": _b64(IMAGE_XML)})
    with mock.patch("yandex_cli.client.post_json", post_json):
        images = YandexSearchClient("key", "folder").image_search(
            "python logo",
            search_type="SEARCH_TYPE_COM",
            num_results=4,
            page=1,
        )

    assert images[0]["url"] == "https://example.com/a.png"
    assert post_json.call_args.args[:2] == ("/image/search", "key")
    assert post_json.call_args.args[2]["docsOnPage"] == 4


def test_client_reverse_image_search_builds_request():
    post_json = mock.Mock(return_value={"images": [], "id": "cbir", "page": 0})
    with mock.patch("yandex_cli.client.post_json", post_json):
        result = YandexSearchClient("key", "folder").reverse_image_search(
            url="https://example.com/a.png",
            site="example.com",
            page=2,
            family_mode="FAMILY_MODE_STRICT",
        )

    assert result["images"] == []
    assert post_json.call_args.args[:2] == ("/image/search_by_image", "key")
    assert post_json.call_args.args[2] == {
        "folderId": "folder",
        "page": 2,
        "url": "https://example.com/a.png",
        "site": "example.com",
        "familyMode": "FAMILY_MODE_STRICT",
    }


def test_client_wordstat_methods_build_requests():
    client = YandexSearchClient("key", "folder")
    post_json = mock.Mock(return_value={"results": []})
    with mock.patch("yandex_cli.client.post_json", post_json):
        client.wordstat_top(
            "python",
            num_phrases=5,
            regions=["213"],
            devices=["DEVICE_DESKTOP"],
        )
        client.wordstat_dynamics(
            "python",
            period="PERIOD_MONTHLY",
            from_date="2026-01-01T00:00:00Z",
        )
        client.wordstat_regions("python", region_scope="REGION_CITIES")
        client.wordstat_regions_tree()

    assert [call.args[0] for call in post_json.call_args_list] == [
        "/wordstat/topRequests",
        "/wordstat/dynamics",
        "/wordstat/regions",
        "/wordstat/getRegionsTree",
    ]
