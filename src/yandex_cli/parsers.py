from __future__ import annotations

import defusedxml.ElementTree as ET

from yandex_cli._common import parse_raw_xml, xml_text


def parse_web_xml(raw_b64: object) -> list[dict]:
    root = parse_raw_xml(raw_b64, "web search")
    docs = []
    for doc in root.iter("doc"):
        modtime = xml_text(doc.find("modtime"))
        date = modtime[:8] if len(modtime) >= 8 else ""
        if date:
            date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        passages = [xml_text(p) for p in doc.iter("passage") if xml_text(p)]
        docs.append(
            {
                "title": xml_text(doc.find("title")),
                "url": xml_text(doc.find("url")),
                "domain": xml_text(doc.find("domain")),
                "date": date,
                "passages": passages,
            }
        )
    return docs


def xml_int(el: ET.Element | None) -> int:
    text = xml_text(el)
    return int(text) if text.isdigit() else 0


def parse_image_xml(raw_b64: object) -> list[dict]:
    root = parse_raw_xml(raw_b64, "image search")
    images = []
    for doc in root.iter("doc"):
        props = doc.find("image-properties")
        images.append(
            {
                "url": xml_text(doc.find("url")),
                "domain": xml_text(doc.find("domain")),
                "title": xml_text(doc.find("properties/title")),
                "thumbnail_url": xml_text(props.find("thumbnail-link"))
                if props is not None
                else "",
                "width": xml_int(props.find("original-width"))
                if props is not None
                else 0,
                "height": xml_int(props.find("original-height"))
                if props is not None
                else 0,
                "page_url": xml_text(props.find("html-link"))
                if props is not None
                else "",
                "format": xml_text(props.find("mime-type"))
                if props is not None
                else "",
            }
        )
    return images
