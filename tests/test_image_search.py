from yandex_cli.image_search import _format_search_by_image


def test_format_search_by_image_lists_results_with_dimensions():
    data = {
        "images": [
            {
                "url": "https://example.com/a.jpg",
                "format": "IMAGE_FORMAT_JPEG",
                "width": 800,
                "height": 600,
                "passage": "A photo of a cat",
                "host": "example.com",
                "pageTitle": "Cats page",
                "pageUrl": "https://example.com/cats",
            }
        ],
        "page": 0,
        "id": "cbir-abc123",
    }
    output = _format_search_by_image(data)
    assert "[1] Cats page" in output
    assert "https://example.com/a.jpg" in output
    assert "800x600" in output
    assert "A photo of a cat" in output
    assert "cbir-abc123" in output


def test_format_search_by_image_handles_missing_title():
    data = {"images": [{"url": "https://example.com/b.jpg", "pageUrl": "", "host": ""}], "page": 0, "id": ""}
    output = _format_search_by_image(data)
    assert "(no title)" in output


def test_format_search_by_image_handles_empty_results():
    data = {"images": [], "page": 2, "id": ""}
    output = _format_search_by_image(data)
    assert "page 2" in output
