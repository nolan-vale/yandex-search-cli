from __future__ import annotations

import argparse
import base64
import json
import textwrap
import defusedxml.ElementTree as ET

import requests

from yandex_cli._common import BASE_URL, creds as _creds, handle_error as _handle_error, headers as _headers

SEARCH_TYPES = {
    "ru": "SEARCH_TYPE_RU",
    "com": "SEARCH_TYPE_COM",
    "tr": "SEARCH_TYPE_TR",
    "kk": "SEARCH_TYPE_KK",
    "be": "SEARCH_TYPE_BE",
    "uz": "SEARCH_TYPE_UZ",
}


def _xml_text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    return "".join(el.itertext()).strip()


def _parse_web_xml(raw_b64: str) -> list[dict]:
    xml_bytes = base64.b64decode(raw_b64)
    root = ET.fromstring(xml_bytes.decode("utf-8"))
    docs = []
    for doc in root.iter("doc"):
        url = _xml_text(doc.find("url"))
        title = _xml_text(doc.find("title"))
        domain = _xml_text(doc.find("domain"))
        modtime = _xml_text(doc.find("modtime"))
        date = modtime[:8] if len(modtime) >= 8 else ""
        if date:
            date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        passages = [_xml_text(p) for p in doc.iter("passage") if _xml_text(p)]
        docs.append({"title": title, "url": url, "domain": domain, "date": date, "passages": passages})
    return docs


def _print_web(docs: list[dict]) -> None:
    for i, doc in enumerate(docs, 1):
        title = doc["title"] or "(no title)"
        meta_parts = [p for p in [doc["date"], doc["domain"]] if p]
        meta = "  ·  ".join(meta_parts)

        print(f"[{i}] {title}")
        print(f"    {doc['url']}")
        if meta:
            print(f"    {meta}")
        for passage in doc["passages"]:
            if passage:
                indented = "\n".join(
                    "    " + ln for ln in textwrap.fill(passage, width=100).splitlines()
                )
                print(indented)
        print()


def _print_gen(data: dict) -> None:
    if data.get("isAnswerRejected"):
        print("[answer rejected — safety restrictions]")
        return

    msg = data.get("message", {})
    text = msg.get("content", "")
    print(text)

    sources = data.get("sources", [])
    if sources:
        print("\nSources:")
        for i, src in enumerate(sources, 1):
            mark = "✓" if src.get("used") else "·"
            print(f"  [{i}] {mark} {src.get('title', '')}")
            print(f"       {src.get('url', '')}")

    fixed = data.get("fixedMisspellQuery", "")
    if fixed:
        print(f"\n[corrected: '{fixed}']")


def search() -> None:
    p = argparse.ArgumentParser(
        description="Yandex web search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  yandex-search "умный город цифровая платформа"
  yandex-search "python frameworks" -n 15
  yandex-search "django docs" --site docs.djangoproject.com
  yandex-search "AI news" -t com --json | jq '.[].url'
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
                   help="restrict results to this domain (e.g. habr.com)")
    p.add_argument("--json", action="store_true",
                   help="JSON output: array of {title, url, domain, date, passages}")
    args = p.parse_args()

    api_key, folder_id = _creds()

    query_text = f"site:{args.site} {args.query}" if args.site else args.query

    body: dict = {
        "folderId": folder_id,
        "query": {
            "searchType": SEARCH_TYPES[args.type],
            "queryText": query_text,
            "page": args.page,
        },
        "groupSpec": {
            "groupsOnPage": args.num_results,
            "docsInGroup": 1,
        },
        "maxPassages": 2,
    }
    if args.region:
        body["query"]["region"] = args.region

    resp = requests.post(f"{BASE_URL}/web/search", headers=_headers(api_key), json=body, timeout=15)
    _handle_error(resp)
    data = resp.json()

    docs = _parse_web_xml(data["rawData"])

    if args.json:
        print(json.dumps(docs, ensure_ascii=False, indent=2))
    else:
        _print_web(docs)
        print(f"── {len(docs)} results ──")


def gen() -> None:
    p = argparse.ArgumentParser(
        description="Yandex generative search (YandexGPT) — answers with cited sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  yandex-gen "объясни трансформеры в машинном обучении"
  yandex-gen "как настроить nginx" --site nginx.org
  yandex-gen "запрос" --json
""",
    )
    p.add_argument("query")
    p.add_argument("--site", default=None,
                   help="restrict sources to this domain")
    p.add_argument("--json", action="store_true",
                   help="raw JSON output")
    args = p.parse_args()

    api_key, folder_id = _creds()

    body: dict = {
        "folderId": folder_id,
        "messages": [{"content": args.query, "role": "ROLE_USER"}],
        "fixMisspell": True,
    }
    if args.site:
        body["site"] = [args.site]

    resp = requests.post(f"{BASE_URL}/gen/search", headers=_headers(api_key), json=body, timeout=30)
    _handle_error(resp)
    data = resp.json()

    result = data[0] if isinstance(data, list) else data

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_gen(result)
