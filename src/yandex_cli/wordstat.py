# src/yandex_cli/wordstat.py
import argparse
import json
from datetime import datetime, timezone

import requests

from yandex_cli._common import BASE_URL, creds, handle_error, headers

DEVICES = {
    "all": "DEVICE_ALL",
    "desktop": "DEVICE_DESKTOP",
    "phone": "DEVICE_PHONE",
    "tablet": "DEVICE_TABLET",
}

PERIODS = {
    "monthly": "PERIOD_MONTHLY",
    "weekly": "PERIOD_WEEKLY",
    "daily": "PERIOD_DAILY",
}

REGION_SCOPES = {
    "all": "REGION_ALL",
    "cities": "REGION_CITIES",
    "regions": "REGION_REGIONS",
}


def _rfc3339(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _format_top(data: dict) -> str:
    lines = [f"Total matching queries: {data.get('totalCount', 0)}", "", "Top phrases:"]
    for r in data.get("results", []):
        lines.append(f"  {r['count']:>8}  {r['phrase']}")
    associations = data.get("associations", [])
    if associations:
        lines.append("")
        lines.append("Related phrases:")
        for r in associations:
            lines.append(f"  {r['count']:>8}  {r['phrase']}")
    return "\n".join(lines)


def _format_dynamics(data: dict) -> str:
    lines = []
    for r in data.get("results", []):
        lines.append(f"{r['date'][:10]}  {r['count']:>8}  {r['share']:.4%}")
    return "\n".join(lines)


def _format_regions(data: dict) -> str:
    lines = []
    for r in data.get("results", []):
        lines.append(
            f"{r['region']:>8}  count={r['count']:<8} share={r['share']:.4%}  affinity={r['affinityIndex']:.2f}"
        )
    return "\n".join(lines)


def _add_regions_filter_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument("-r", "--region", dest="regions", action="append", default=None,
                   help="region ID to filter by (repeatable)")


def _add_device_and_json_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("-d", "--device", dest="devices", action="append", default=None,
                   choices=list(DEVICES), help="device type to filter by (repeatable)")
    p.add_argument("--json", action="store_true", help="raw JSON output")


def wordstat() -> None:
    p = argparse.ArgumentParser(
        description="Yandex Wordstat — search query frequency statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  yandex-wordstat top "python framework"
  yandex-wordstat top "python framework" -n 20 --device desktop
  yandex-wordstat dynamics "python framework" --period monthly --from 2026-01-01
  yandex-wordstat regions "python framework" --scope cities
""",
    )
    sub = p.add_subparsers(dest="command", required=True)

    top_p = sub.add_parser("top", help="most popular queries containing a keyword")
    top_p.add_argument("phrase")
    top_p.add_argument("-n", "--num-phrases", type=int, default=20,
                        help="number of phrases in the response (default: 20)")
    _add_regions_filter_arg(top_p)
    _add_device_and_json_args(top_p)

    dyn_p = sub.add_parser("dynamics", help="query frequency over time")
    dyn_p.add_argument("phrase")
    dyn_p.add_argument("--period", default="monthly", choices=list(PERIODS),
                        help="aggregation period (default: monthly)")
    dyn_p.add_argument("--from", dest="from_date", required=True,
                        help="start date, YYYY-MM-DD")
    dyn_p.add_argument("--to", dest="to_date", default=None,
                        help="end date, YYYY-MM-DD (default: today)")
    _add_regions_filter_arg(dyn_p)
    _add_device_and_json_args(dyn_p)

    reg_p = sub.add_parser("regions", help="geographic distribution of a keyword's queries")
    reg_p.add_argument("phrase")
    reg_p.add_argument("--scope", default="all", choices=list(REGION_SCOPES),
                        help="show distribution by cities, regions, or everywhere (default: all)")
    _add_device_and_json_args(reg_p)

    args = p.parse_args()
    api_key, folder_id = creds()

    if args.command == "top":
        body: dict = {"folderId": folder_id, "phrase": args.phrase, "numPhrases": args.num_phrases}
        if args.regions:
            body["regions"] = args.regions
        if args.devices:
            body["devices"] = [DEVICES[d] for d in args.devices]
        resp = requests.post(f"{BASE_URL}/wordstat/topRequests", headers=headers(api_key), json=body, timeout=15)
        handle_error(resp)
        data = resp.json()
        print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else _format_top(data))
    elif args.command == "dynamics":
        body = {
            "folderId": folder_id,
            "phrase": args.phrase,
            "period": PERIODS[args.period],
            "fromDate": _rfc3339(args.from_date),
        }
        if args.to_date:
            body["toDate"] = _rfc3339(args.to_date)
        if args.regions:
            body["regions"] = args.regions
        if args.devices:
            body["devices"] = [DEVICES[d] for d in args.devices]
        resp = requests.post(f"{BASE_URL}/wordstat/dynamics", headers=headers(api_key), json=body, timeout=15)
        handle_error(resp)
        data = resp.json()
        print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else _format_dynamics(data))
    elif args.command == "regions":
        body = {"folderId": folder_id, "phrase": args.phrase, "region": REGION_SCOPES[args.scope]}
        if args.devices:
            body["devices"] = [DEVICES[d] for d in args.devices]
        resp = requests.post(f"{BASE_URL}/wordstat/regions", headers=headers(api_key), json=body, timeout=15)
        handle_error(resp)
        data = resp.json()
        print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else _format_regions(data))
