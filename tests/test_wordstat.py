# tests/test_wordstat.py
from yandex_cli.wordstat import _format_dynamics, _format_regions, _format_top, _rfc3339


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
    data = {"totalCount": 10, "results": [{"phrase": "x", "count": 10}], "associations": []}
    output = _format_top(data)
    assert "Related phrases" not in output


def test_rfc3339_converts_date_to_utc_timestamp():
    assert _rfc3339("2026-01-15") == "2026-01-15T00:00:00Z"


def test_format_dynamics_formats_date_count_and_share():
    data = {"results": [{"date": "2026-01-01T00:00:00Z", "count": 500, "share": 0.0123}]}
    output = _format_dynamics(data)
    assert "2026-01-01" in output
    assert "500" in output
    assert "1.2300%" in output


def test_format_regions_includes_affinity_index():
    data = {"results": [{"region": "213", "count": 300, "share": 0.05, "affinityIndex": 1.42}]}
    output = _format_regions(data)
    assert "213" in output
    assert "1.42" in output
