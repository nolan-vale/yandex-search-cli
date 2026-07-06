# tests/test_wordstat.py
from yandex_cli.wordstat import _format_top


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
