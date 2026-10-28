from __future__ import annotations

import argparse
import json
import textwrap

from yandex_cli._common import (
    SEARCH_TYPES,
    add_common_args,
    creds as _creds,
    nonnegative_int,
    positive_int,
    result_count,
)
from yandex_cli.client import YandexSearchClient
from yandex_cli.parsers import parse_web_xml

_parse_web_xml = parse_web_xml


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
    p.add_argument(
        "-n",
        "--num-results",
        type=result_count,
        default=10,
        help="number of results (default: 10)",
    )
    p.add_argument(
        "-t",
        "--type",
        default="ru",
        choices=list(SEARCH_TYPES),
        help="search type: ru, com, tr, kk, be, uz (default: ru)",
    )
    p.add_argument(
        "-r", "--region", default=None, help="search region code (e.g. 213 for Moscow)"
    )
    p.add_argument(
        "-p",
        "--page",
        type=nonnegative_int,
        default=0,
        help="page number, 0-indexed (default: 0)",
    )
    p.add_argument(
        "--site", default=None, help="restrict results to this domain (e.g. habr.com)"
    )
    p.add_argument(
        "--pages",
        type=positive_int,
        default=1,
        help="consecutive pages to collect; deduplicate URLs (default: 1)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="JSON output: array of {title, url, domain, date, passages}",
    )
    add_common_args(p)
    args = p.parse_args()
    query_text = f"site:{args.site} {args.query}" if args.site else args.query
    if not args.query.strip() or len(query_text) > 400:
        p.error("query must be non-empty and at most 400 characters including --site")
    if args.region and args.type not in ("ru", "tr"):
        p.error("--region is supported only for ru/tr search types")
    if (args.page + args.pages - 1) * args.num_results >= 250:
        p.error(
            "requested pages exceed the 250-result search window; reduce --page or --pages"
        )

    api_key, folder_id = _creds()
    client = YandexSearchClient(api_key, folder_id, timeout=args.timeout)
    docs = client.web_search(
        query_text,
        search_type=SEARCH_TYPES[args.type],
        num_results=args.num_results,
        page=args.page,
        region=args.region,
        pages=args.pages,
    )

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
    p.add_argument("--site", default=None, help="restrict sources to this domain")
    p.add_argument("--json", action="store_true", help="JSON output")
    add_common_args(p)
    args = p.parse_args()

    api_key, folder_id = _creds()
    client = YandexSearchClient(api_key, folder_id, timeout=args.timeout)
    result = client.generative_search(args.query, site=args.site)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_gen(result)
