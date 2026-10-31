from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path

from yandex_cli._common import (
    SEARCH_TYPES,
    add_common_args,
    nonnegative_int,
    positive_int,
    result_count,
)
from yandex_cli._common import (
    creds as _creds,
)
from yandex_cli.client import (
    DOCUMENT_FORMATS,
    YandexSearchClient,
    prepare_messages,
    validate_date_filter,
    validate_language,
)
from yandex_cli.parsers import parse_web_xml

_parse_web_xml = parse_web_xml

SEARCH_PERIODS = {
    "all": "PERIOD_ALL_TIME",
    "day": "PERIOD_DAY",
    "2weeks": "PERIOD_2_WEEKS",
    "month": "PERIOD_MONTH",
}
SORT_MODES = {"relevance": "SORT_MODE_BY_RELEVANCE", "time": "SORT_MODE_BY_TIME"}
SORT_ORDERS = {"asc": "SORT_ORDER_ASC", "desc": "SORT_ORDER_DESC"}


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
  yandex-search "AI news" --period day
  yandex-search "AI news" --sort time --order asc
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
        "--period",
        choices=list(SEARCH_PERIODS),
        help="freshness filter: all time, last 24 hours, last 2 weeks or last month",
    )
    p.add_argument(
        "--sort",
        choices=list(SORT_MODES),
        help="sort by relevance (default) or page update time (newest first)",
    )
    p.add_argument(
        "--order",
        choices=list(SORT_ORDERS),
        help="time sort order: asc (oldest first) or desc (default); requires --sort time",
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
    if args.order and args.sort != "time":
        p.error("--order requires --sort time")
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
        period=SEARCH_PERIODS.get(args.period),
        sort_mode=SORT_MODES.get(args.sort),
        sort_order=SORT_ORDERS.get(args.order),
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
  yandex-gen "smart city research" --format pdf --lang en --date '>=20250101'
  yandex-gen "а как включить HTTPS?" --messages-file conversation.json
  yandex-gen --messages-file - --json < conversation.json
  yandex-gen "запрос" --json
""",
    )
    p.add_argument("query", nargs="?", help="question to append to the conversation")
    p.add_argument(
        "--messages-file",
        metavar="FILE",
        help="JSON array of user/assistant messages; use - to read stdin",
    )
    p.add_argument("--site", default=None, help="restrict sources to this domain")
    p.add_argument(
        "--format",
        dest="doc_format",
        type=str.lower,
        choices=list(DOCUMENT_FORMATS),
        help="restrict source document format (e.g. pdf)",
    )
    p.add_argument(
        "--lang",
        type=validate_language,
        help="restrict source language using a two-letter ISO 639-1 code (e.g. ru)",
    )
    p.add_argument(
        "--date",
        type=validate_date_filter,
        help="source date: YYYYMMDD, '>YYYYMMDD', a range, YYYYMM* or YYYY*",
    )
    p.add_argument("--json", action="store_true", help="JSON output")
    add_common_args(p)
    args = p.parse_args()

    history = None
    if args.messages_file is not None:
        try:
            raw = (
                sys.stdin.read()
                if args.messages_file == "-"
                else Path(args.messages_file).read_text(encoding="utf-8")
            )
        except (OSError, UnicodeError):
            p.error("could not read --messages-file as UTF-8")
        try:
            history = json.loads(raw)
        except (ValueError, RecursionError):
            p.error("--messages-file must contain valid JSON")
        if not isinstance(history, list):
            p.error("--messages-file must contain a JSON array")
    try:
        messages = prepare_messages(args.query, history)
    except (TypeError, ValueError) as exc:
        p.error(str(exc))

    api_key, folder_id = _creds()
    client = YandexSearchClient(api_key, folder_id, timeout=args.timeout)
    result = client.generative_search(
        messages=messages,
        site=args.site,
        doc_format=args.doc_format,
        lang=args.lang,
        date_filter=args.date,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_gen(result)
