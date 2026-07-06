from __future__ import annotations

import argparse
import base64
import json

import defusedxml.ElementTree as ET
import requests

from yandex_cli._common import BASE_URL, creds, handle_error, headers

FAMILY_MODES = {
    "none": "FAMILY_MODE_NONE",
    "moderate": "FAMILY_MODE_MODERATE",
    "strict": "FAMILY_MODE_STRICT",
}

SEARCH_TYPES = {
    "ru": "SEARCH_TYPE_RU",
    "com": "SEARCH_TYPE_COM",
    "tr": "SEARCH_TYPE_TR",
    "kk": "SEARCH_TYPE_KK",
    "be": "SEARCH_TYPE_BE",
    "uz": "SEARCH_TYPE_UZ",
}


def _format_search_by_image(data: dict) -> str:
    images = data.get("images", [])
    lines = []
    for i, img in enumerate(images, 1):
        lines.append(f"[{i}] {img.get('pageTitle') or '(no title)'}")
        lines.append(f"    {img.get('url', '')}")
        lines.append(f"    page: {img.get('pageUrl', '')}  ({img.get('host', '')})")
        w, h = img.get("width"), img.get("height")
        if w and h:
            lines.append(f"    {w}x{h}  {img.get('format', '')}")
        passage = img.get("passage", "")
        if passage:
            lines.append(f"    {passage}")
        lines.append("")
    lines.append(f"── page {data.get('page', 0)}, cbir id: {data.get('id', '')} ──")
    return "\n".join(lines)


def search_by_image() -> None:
    p = argparse.ArgumentParser(
        description="Yandex reverse image search — find pages containing a given image",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  yandex-image-search-by-image --url "https://example.com/photo.jpg"
  yandex-image-search-by-image --url "https://example.com/photo.jpg" --site habr.com
  yandex-image-search-by-image --cbir-id "abc123..." --page 1
  yandex-image-search-by-image --url "https://example.com/photo.jpg" --json
""",
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="image URL to search by")
    src.add_argument("--cbir-id", help="CBIR ID from a previous search result's `id` field")
    p.add_argument("--site", default=None, help="restrict results to this domain")
    p.add_argument("-p", "--page", type=int, default=0,
                   help="page number, 0-indexed (default: 0)")
    p.add_argument("--family-mode", default=None, choices=list(FAMILY_MODES),
                   help="content filtering: none, moderate, strict")
    p.add_argument("--json", action="store_true", help="raw JSON output")
    args = p.parse_args()

    api_key, folder_id = creds()

    body: dict = {"folderId": folder_id, "page": args.page}
    if args.url:
        body["url"] = args.url
    else:
        body["id"] = args.cbir_id
    if args.site:
        body["site"] = args.site
    if args.family_mode:
        body["familyMode"] = FAMILY_MODES[args.family_mode]

    resp = requests.post(f"{BASE_URL}/image/search_by_image", headers=headers(api_key), json=body, timeout=15)
    handle_error(resp)
    data = resp.json()

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(_format_search_by_image(data))


# --- yandex-image-search (text-query image search) ---
#
# ImageSearchService.Search returns {"rawData": "<base64 XML>"}, same shape
# as WebSearchService — but the tag names inside are not in img_search_service.proto.
# The schema below (doc -> url/domain/image-properties{thumbnail-link,
# original-width, original-height, html-link, mime-type}/properties{title?})
# was captured from a real live response for the query "python logo" on
# 2026-07-06 (see tests/test_image_search.py's SAMPLE_XML), following the
# same <results>/<grouping>/<group>/<doc> shape as main.py's _parse_web_xml.
# Notably, real responses had an empty <properties/> with no <title> child —
# source-page titles are not reliably available from this endpoint.


def _xml_text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    return "".join(el.itertext()).strip()


def _xml_int(el: ET.Element | None) -> int:
    text = _xml_text(el)
    return int(text) if text.isdigit() else 0


def _parse_image_xml(raw_b64: str) -> list[dict]:
    xml_bytes = base64.b64decode(raw_b64)
    root = ET.fromstring(xml_bytes.decode("utf-8"))
    images = []
    for doc in root.iter("doc"):
        props = doc.find("image-properties")
        images.append({
            "url": _xml_text(doc.find("url")),
            "domain": _xml_text(doc.find("domain")),
            "title": _xml_text(doc.find("properties/title")),
            "thumbnail_url": _xml_text(props.find("thumbnail-link")) if props is not None else "",
            "width": _xml_int(props.find("original-width")) if props is not None else 0,
            "height": _xml_int(props.find("original-height")) if props is not None else 0,
            "page_url": _xml_text(props.find("html-link")) if props is not None else "",
            "format": _xml_text(props.find("mime-type")) if props is not None else "",
        })
    return images


def _format_images(images: list[dict]) -> str:
    lines = []
    for i, img in enumerate(images, 1):
        lines.append(f"[{i}] {img.get('title') or '(no title)'}")
        lines.append(f"    {img.get('url', '')}")
        lines.append(f"    page: {img.get('page_url', '')}  ({img.get('domain', '')})")
        w, h = img.get("width"), img.get("height")
        if w and h:
            lines.append(f"    {w}x{h}  {img.get('format', '')}")
        thumb = img.get("thumbnail_url", "")
        if thumb:
            lines.append(f"    thumbnail: {thumb}")
        lines.append("")
    return "\n".join(lines)


def search() -> None:
    p = argparse.ArgumentParser(
        description="Yandex image search — find images matching a text query",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  yandex-image-search "python logo"
  yandex-image-search "python logo" -n 20
  yandex-image-search "sunset" --site unsplash.com
  yandex-image-search "sunset" --json
""",
    )
    p.add_argument("query")
    p.add_argument("-n", "--num-results", type=int, default=10,
                   help="number of results (default: 10)")
    p.add_argument("-t", "--type", default="ru", choices=list(SEARCH_TYPES),
                   help="search type: ru, com, tr, kk, be, uz (default: ru)")
    p.add_argument("-r", "--region", default=None,
                   help="search region code (e.g. 213 for Moscow)")
    p.add_argument("-p", "--page", type=int, default=0,
                   help="page number, 0-indexed (default: 0)")
    p.add_argument("--site", default=None,
                   help="restrict results to this domain (e.g. unsplash.com)")
    p.add_argument("--json", action="store_true",
                   help="JSON output: array of {url, domain, title, thumbnail_url, width, height, page_url, format}")
    args = p.parse_args()

    api_key, folder_id = creds()

    query_text = f"site:{args.site} {args.query}" if args.site else args.query

    body: dict = {
        "folderId": folder_id,
        "query": {
            "searchType": SEARCH_TYPES[args.type],
            "queryText": query_text,
            "page": args.page,
        },
        "docsOnPage": args.num_results,
    }
    if args.region:
        body["query"]["region"] = args.region

    resp = requests.post(f"{BASE_URL}/image/search", headers=headers(api_key), json=body, timeout=15)
    handle_error(resp)
    data = resp.json()

    images = _parse_image_xml(data["rawData"])

    if args.json:
        print(json.dumps(images, ensure_ascii=False, indent=2))
    else:
        print(_format_images(images))
        print(f"── {len(images)} results ──")
