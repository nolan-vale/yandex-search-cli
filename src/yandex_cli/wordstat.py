# src/yandex_cli/wordstat.py
import argparse
import json
from datetime import datetime, timezone

from yandex_cli._common import creds, positive_int
from yandex_cli.client import YandexSearchClient

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
        lines.append(f"  {r.get('count', 0):>8}  {r.get('phrase', '')}")
    associations = data.get("associations", [])
    if associations:
        lines.append("")
        lines.append("Related phrases:")
        for r in associations:
            lines.append(f"  {r.get('count', 0):>8}  {r.get('phrase', '')}")
    return "\n".join(lines)


def _format_dynamics(data: dict) -> str:
    lines = []
    for r in data.get("results", []):
        share = float(r.get("share", 0) or 0)
        lines.append(f"{r.get('date', '')[:10]}  {r.get('count', 0):>8}  {share:.4%}")
    return "\n".join(lines)


def _format_regions(data: dict) -> str:
    lines = []
    for r in data.get("results", []):
        share = float(r.get("share", 0) or 0)
        affinity = float(r.get("affinityIndex", 0) or 0)
        lines.append(
            f"{r.get('region', ''):>8}  count={r.get('count', 0):<8} "
            f"share={share:.4%}  affinity={affinity:.2f}"
        )
    return "\n".join(lines)


def _format_regions_tree(data: dict, indent: int = 0) -> str:
    lines = []
    for region in data.get("regions", []):
        lines.append(
            "  " * indent + f"{region.get('id', '')}: {region.get('label', '')}"
        )
        if region.get("children"):
            lines.append(
                _format_regions_tree({"regions": region["children"]}, indent + 1)
            )
    return "\n".join(lines)


def _add_regions_filter_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "-r",
        "--region",
        dest="regions",
        action="append",
        default=None,
        help="region ID to filter by (repeatable)",
    )


def _add_device_and_json_args(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "-d",
        "--device",
        dest="devices",
        action="append",
        default=None,
        choices=list(DEVICES),
        help="device type to filter by (repeatable)",
    )
    p.add_argument("--json", action="store_true", help="JSON output")


def _rfc3339_arg(date_str: str) -> str:
    try:
        return _rfc3339(date_str)
    except ValueError as e:
        raise argparse.ArgumentTypeError("must be YYYY-MM-DD") from e


def wordstat() -> None:
    p = argparse.ArgumentParser(
        description="Yandex Wordstat — search query frequency statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  yandex-wordstat top "python framework"
  yandex-wordstat top "python framework" -n 20 --device desktop
  yandex-wordstat dynamics "python framework" --period monthly --from 2026-01-01
  yandex-wordstat regions "python framework" --scope cities
  yandex-wordstat regions-tree
""",
    )
    sub = p.add_subparsers(dest="command", required=True)

    top_p = sub.add_parser("top", help="most popular queries containing a keyword")
    top_p.add_argument("phrase")
    top_p.add_argument(
        "-n",
        "--num-phrases",
        type=positive_int,
        default=20,
        help="number of phrases in the response (default: 20)",
    )
    _add_regions_filter_arg(top_p)
    _add_device_and_json_args(top_p)

    dyn_p = sub.add_parser("dynamics", help="query frequency over time")
    dyn_p.add_argument("phrase")
    dyn_p.add_argument(
        "--period",
        default="monthly",
        choices=list(PERIODS),
        help="aggregation period (default: monthly)",
    )
    dyn_p.add_argument(
        "--from",
        dest="from_date",
        type=_rfc3339_arg,
        required=True,
        help="start date, YYYY-MM-DD",
    )
    dyn_p.add_argument(
        "--to",
        dest="to_date",
        type=_rfc3339_arg,
        default=None,
        help="end date, YYYY-MM-DD (default: today)",
    )
    _add_regions_filter_arg(dyn_p)
    _add_device_and_json_args(dyn_p)

    reg_p = sub.add_parser(
        "regions", help="geographic distribution of a keyword's queries"
    )
    reg_p.add_argument("phrase")
    reg_p.add_argument(
        "--scope",
        default="all",
        choices=list(REGION_SCOPES),
        help="show distribution by cities, regions, or everywhere (default: all)",
    )
    _add_device_and_json_args(reg_p)

    tree_p = sub.add_parser("regions-tree", help="list Wordstat-supported region IDs")
    tree_p.add_argument("--json", action="store_true", help="JSON output")

    args = p.parse_args()
    api_key, folder_id = creds()
    client = YandexSearchClient(api_key, folder_id)

    if args.command == "top":
        data = client.wordstat_top(
            args.phrase,
            num_phrases=args.num_phrases,
            regions=args.regions,
            devices=[DEVICES[d] for d in args.devices] if args.devices else None,
        )
        print(
            json.dumps(data, ensure_ascii=False, indent=2)
            if args.json
            else _format_top(data)
        )
    elif args.command == "dynamics":
        data = client.wordstat_dynamics(
            args.phrase,
            period=PERIODS[args.period],
            from_date=args.from_date,
            to_date=args.to_date,
            regions=args.regions,
            devices=[DEVICES[d] for d in args.devices] if args.devices else None,
        )
        print(
            json.dumps(data, ensure_ascii=False, indent=2)
            if args.json
            else _format_dynamics(data)
        )
    elif args.command == "regions":
        data = client.wordstat_regions(
            args.phrase,
            region_scope=REGION_SCOPES[args.scope],
            devices=[DEVICES[d] for d in args.devices] if args.devices else None,
        )
        print(
            json.dumps(data, ensure_ascii=False, indent=2)
            if args.json
            else _format_regions(data)
        )
    elif args.command == "regions-tree":
        data = client.wordstat_regions_tree()
        print(
            json.dumps(data, ensure_ascii=False, indent=2)
            if args.json
            else _format_regions_tree(data)
        )
