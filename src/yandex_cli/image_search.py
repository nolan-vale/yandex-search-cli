import argparse
import json

import requests

from yandex_cli._common import BASE_URL, creds, handle_error, headers

FAMILY_MODES = {
    "none": "FAMILY_MODE_NONE",
    "moderate": "FAMILY_MODE_MODERATE",
    "strict": "FAMILY_MODE_STRICT",
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
