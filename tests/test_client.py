import base64
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
        "region": "213",
    }
    assert body["groupSpec"]["groupsOnPage"] == 3


def test_client_web_search_rejects_non_dict_response():
    with mock.patch("yandex_cli.client.post_json", return_value=[]):
        with pytest.raises(SystemExit, match="web search returned an unexpected"):
            YandexSearchClient("key", "folder").web_search(
                "topic",
                search_type="SEARCH_TYPE_RU",
                num_results=1,
                page=0,
            )


def test_client_generative_search_accepts_list_response():
    with mock.patch(
        "yandex_cli.client.post_json",
        return_value=[{"message": {"content": "answer"}}],
    ) as post_json:
        result = YandexSearchClient("key", "folder").generative_search(
            "question",
            site="example.com",
        )

    assert result["message"]["content"] == "answer"
    assert post_json.call_args.args[:2] == ("/gen/search", "key")
    assert post_json.call_args.args[2]["site"] == ["example.com"]


def test_client_generative_search_rejects_empty_list_response():
    with mock.patch("yandex_cli.client.post_json", return_value=[]):
        with pytest.raises(SystemExit, match="empty response"):
            YandexSearchClient("key", "folder").generative_search("question")


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
