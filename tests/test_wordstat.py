# tests/test_wordstat.py
import contextlib
import io
import json
import sys
from unittest import mock

import pytest

from yandex_cli.wordstat import (
    _format_dynamics,
    _format_regions,
    _format_regions_tree,
    _format_top,
    _rfc3339,
    _rfc3339_arg,
    wordstat,
)


def test_format_top_lists_results_and_associations():
    data = {
        "totalCount": 4200,
        "results": [{"phrase": "python framework", "count": 1000}],
        "associations": [{"phrase": "python library", "count": 500}],
    }
    output = _format_top(data)
    assert "4200" in output
    assert "python framework" in output
    assert "Related phrases" in output
    assert "python library" in output


def test_format_top_omits_associations_section_when_empty():
    data = {
        "totalCount": 10,
        "results": [{"phrase": "x", "count": 10}],
        "associations": [],
    }
    output = _format_top(data)
    assert "Related phrases" not in output


def test_rfc3339_converts_date_to_utc_timestamp():
    assert _rfc3339("2026-01-15") == "2026-01-15T00:00:00Z"


def test_rfc3339_arg_rejects_invalid_date():
    with pytest.raises(Exception, match="must be YYYY-MM-DD"):
        _rfc3339_arg("2026-99-99")


def test_format_dynamics_formats_date_count_and_share():
    data = {
        "results": [{"date": "2026-01-01T00:00:00Z", "count": 500, "share": 0.0123}]
    }
    output = _format_dynamics(data)
    assert "2026-01-01" in output
    assert "500" in output
    assert "1.2300%" in output


def test_format_regions_includes_affinity_index():
    data = {
        "results": [
            {"region": "213", "count": 300, "share": 0.05, "affinityIndex": 1.42}
        ]
    }
    output = _format_regions(data)
    assert "213" in output
    assert "1.42" in output


def test_format_regions_tree_indents_children():
    data = {
        "regions": [
            {
                "id": "225",
                "label": "Russia",
                "children": [{"id": "213", "label": "Moscow", "children": []}],
            }
        ]
    }
    output = _format_regions_tree(data)
    lines = output.splitlines()
    assert lines[0] == "225: Russia"
    assert lines[1] == "  213: Moscow"


def test_formatters_tolerate_missing_optional_fields():
    assert "0" in _format_top({"results": [{}]})
    assert "0.0000%" in _format_dynamics({"results": [{}]})
    assert "affinity=0.00" in _format_regions({"results": [{}]})
    assert ":" in _format_regions_tree({"regions": [{}]})


def test_wordstat_top_json_entrypoint_calls_client(monkeypatch):
    monkeypatch.setattr("yandex_cli.wordstat.creds", lambda: ("key", "folder"))
    client = mock.Mock()
    client.wordstat_top.return_value = {"results": [{"phrase": "python", "count": 1}]}
    client_class = mock.Mock(return_value=client)
    monkeypatch.setattr("yandex_cli.wordstat.YandexSearchClient", client_class)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yandex-wordstat",
            "top",
            "python",
            "-n",
            "5",
            "--region",
            "213",
            "--device",
            "desktop",
            "--json",
        ],
    )
    stdout = io.StringIO()

    with contextlib.redirect_stdout(stdout):
        wordstat()

    assert json.loads(stdout.getvalue())["results"][0]["phrase"] == "python"
    client_class.assert_called_once_with("key", "folder")
    client.wordstat_top.assert_called_once_with(
        "python",
        num_phrases=5,
        regions=["213"],
        devices=["DEVICE_DESKTOP"],
    )


def test_wordstat_dynamics_rejects_invalid_date_before_credentials(monkeypatch):
    creds = mock.Mock()
    monkeypatch.setattr("yandex_cli.wordstat.creds", creds)
    monkeypatch.setattr(
        sys,
        "argv",
        ["yandex-wordstat", "dynamics", "python", "--from", "bad-date"],
    )

    with pytest.raises(SystemExit):
        wordstat()

    creds.assert_not_called()
