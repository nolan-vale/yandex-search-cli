import base64

from yandex_cli.image_search import _format_images, _format_search_by_image, _parse_image_xml


def test_format_search_by_image_lists_results_with_dimensions():
    data = {
        "images": [
            {
                "url": "https://example.com/a.jpg",
                "format": "IMAGE_FORMAT_JPEG",
                "width": 800,
                "height": 600,
                "passage": "A photo of a cat",
                "host": "example.com",
                "pageTitle": "Cats page",
                "pageUrl": "https://example.com/cats",
            }
        ],
        "page": 0,
        "id": "cbir-abc123",
    }
    output = _format_search_by_image(data)
    assert "[1] Cats page" in output
    assert "https://example.com/a.jpg" in output
    assert "800x600" in output
    assert "A photo of a cat" in output
    assert "cbir-abc123" in output


def test_format_search_by_image_handles_missing_title():
    data = {"images": [{"url": "https://example.com/b.jpg", "pageUrl": "", "host": ""}], "page": 0, "id": ""}
    output = _format_search_by_image(data)
    assert "(no title)" in output


def test_format_search_by_image_handles_empty_results():
    data = {"images": [], "page": 2, "id": ""}
    output = _format_search_by_image(data)
    assert "page 2" in output


# --- yandex-image-search (text query) — parser built from a real captured
# response. Sample captured 2026-07-06 via a live POST to /v2/image/search
# for the query "python logo" (see the implementation plan's Task 8 spike
# step). The tag names and values below (url, domain, modtime,
# image-properties/{thumbnail-link,thumbnail-width,thumbnail-height,
# original-width,original-height,html-link,image-link,file-size,mime-type},
# and an empty <properties/> with no <title>) are copied verbatim from that
# real response, not guessed.

SAMPLE_XML = """<?xml version="1.0" encoding="utf-8"?>
<yandexsearch version="1.0">
<request>
<query>python logo</query>
<page>0</page>
</request>
<response date="20260706T105204">
<reqid>1783335124331161-14475302689891271797-balancer-l7leveler-kubr-yp-sas-71-BAL</reqid>
<found priority="all">2224</found>
<results>
<grouping attr="ii" mode="deep" groups-on-page="2" docs-in-group="1" curcateg="-1">
<page first="1" last="2">0</page>
<group>
<categ attr="ii" id="8301354167870916188"/>
<doccount>1</doccount>
<doc id="ZEEAD0431C48F5305">
<url>https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Python_logo_and_wordmark.svg/1280px-Python_logo_and_wordmark.svg.png</url>
<domain>upload.wikimedia.org</domain>
<modtime>20190520T160617</modtime>
<size>0</size>
<charset>utf-8</charset>
<image-properties>
<id>012db0b6a07e497679a04a8707825b212af233a9-5208099-images-thumbs</id>
<shard>0</shard>
<thumbnail-link>http://avatars.mds.yandex.net/i?id=012db0b6a07e497679a04a8707825b212af233a9-5208099-images-thumbs</thumbnail-link>
<thumbnail-width>480</thumbnail-width>
<thumbnail-height>142</thumbnail-height>
<original-width>500</original-width>
<original-height>148</original-height>
<html-link>https://en.wikipedia.org/wiki/CPython</html-link>
<image-link>https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Python_logo_and_wordmark.svg/500px-Python_logo_and_wordmark.svg.png</image-link>
<file-size>12727</file-size>
<mime-type>png</mime-type>
</image-properties>
<mime-type>text/html</mime-type>
<properties/>
</doc>
</group>
<group>
<categ attr="ii" id="9216922198140848375"/>
<doccount>1</doccount>
<doc id="Z3840EAA491A9CDB9">
<url>https://res.cloudinary.com/startup-grind/image/upload/python.jpg</url>
<domain>res.cloudinary.com</domain>
<modtime>20160313T202209</modtime>
<size>0</size>
<charset>utf-8</charset>
<image-properties>
<id>16ae9ce2fb83491ae5f15416024264f539c31dbc-12752373-images-thumbs</id>
<shard>0</shard>
<thumbnail-link>http://avatars.mds.yandex.net/i?id=16ae9ce2fb83491ae5f15416024264f539c31dbc-12752373-images-thumbs</thumbnail-link>
<thumbnail-width>480</thumbnail-width>
<thumbnail-height>270</thumbnail-height>
<original-width>1920</original-width>
<original-height>1080</original-height>
<html-link>https://www.comoinstalar.com.br/instalar-python-no-windows-em-3-passos/</html-link>
<image-link>https://www.comoinstalar.com.br/wp-content/uploads/2022/04/Python-Emblema.jpg</image-link>
<file-size>27841</file-size>
<mime-type>jpg</mime-type>
</image-properties>
<mime-type>text/html</mime-type>
<properties/>
</doc>
</group>
<found priority="all">2212</found>
<found-docs priority="all">2212</found-docs>
</grouping>
</results>
</response>
<resource-usage>
<cpu-time-sum>2013445</cpu-time-sum>
<cpu-time-max>19968</cpu-time-max>
</resource-usage>
</yandexsearch>
"""


def _sample_b64() -> str:
    return base64.b64encode(SAMPLE_XML.encode("utf-8")).decode()


def test_parse_image_xml_extracts_known_fields():
    results = _parse_image_xml(_sample_b64())
    assert len(results) == 2

    first = results[0]
    assert first["url"] == (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/"
        "Python_logo_and_wordmark.svg/1280px-Python_logo_and_wordmark.svg.png"
    )
    assert first["domain"] == "upload.wikimedia.org"
    assert first["width"] == 500
    assert first["height"] == 148
    assert first["thumbnail_url"] == (
        "http://avatars.mds.yandex.net/i?id=012db0b6a07e497679a04a8707825b212af233a9-5208099-images-thumbs"
    )
    assert first["page_url"] == "https://en.wikipedia.org/wiki/CPython"
    assert first["format"] == "png"
    # Real captured responses have an empty <properties/> with no <title> child.
    assert first["title"] == ""

    second = results[1]
    assert second["width"] == 1920
    assert second["height"] == 1080
    assert second["page_url"] == "https://www.comoinstalar.com.br/instalar-python-no-windows-em-3-passos/"
    assert second["format"] == "jpg"


def test_parse_image_xml_handles_empty_results():
    empty_xml = """<?xml version="1.0" encoding="utf-8"?>
<yandexsearch version="1.0">
<response date="20260706T105204">
<results>
<grouping attr="ii" mode="deep" groups-on-page="0" docs-in-group="1" curcateg="-1">
</grouping>
</results>
</response>
</yandexsearch>
"""
    raw_b64 = base64.b64encode(empty_xml.encode("utf-8")).decode()
    assert _parse_image_xml(raw_b64) == []


def test_format_images_lists_results_with_dimensions_and_no_title_fallback():
    results = _parse_image_xml(_sample_b64())
    output = _format_images(results)
    assert "[1] (no title)" in output
    assert "500x148  png" in output
    assert "https://en.wikipedia.org/wiki/CPython" in output
    assert "upload.wikimedia.org" in output
