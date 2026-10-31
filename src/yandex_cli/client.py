from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import date
from typing import Any

from yandex_cli._common import post_json
from yandex_cli.parsers import parse_image_xml, parse_web_xml

DOCUMENT_FORMATS = {
    name: f"DOC_FORMAT_{name.upper()}"
    for name in ("pdf", "xls", "ods", "rtf", "ppt", "odp", "swf", "odt", "odg", "doc")
}


def validate_language(value: str) -> str:
    if not re.fullmatch(r"[a-zA-Z]{2}", value):
        raise ValueError("language must be a two-letter ISO 639-1 code")
    return value.lower()


def validate_date_filter(value: str) -> str:
    if match := re.fullmatch(r"(?:[<>]=?)?([0-9]{8})", value):
        date.fromisoformat(match[1])
    elif match := re.fullmatch(r"([0-9]{8})\.\.([0-9]{8})", value):
        start, end = date.fromisoformat(match[1]), date.fromisoformat(match[2])
        if start > end:
            raise ValueError("date range start must not be after its end")
    elif match := re.fullmatch(r"([0-9]{4})([0-9]{2})?\*", value):
        date(int(match[1]), int(match[2] or 1), 1)
    else:
        raise ValueError(
            "date must be YYYYMMDD, a < / <= / > / >= comparison, "
            "YYYYMMDD..YYYYMMDD, YYYYMM* or YYYY*"
        )
    return value


def prepare_messages(
    query: str | None = None, messages: list[dict[str, str]] | None = None
) -> list[dict[str, str]]:
    if messages is not None and not isinstance(messages, list):
        raise TypeError("messages must be a JSON array")
    conversation = list(messages) if messages is not None else []
    if query is not None:
        conversation.append({"role": "ROLE_USER", "content": query})
    if not 1 <= len(conversation) <= 100:
        raise ValueError("generative search requires 1 to 100 messages")

    roles = {
        "user": "ROLE_USER",
        "assistant": "ROLE_ASSISTANT",
        "ROLE_USER": "ROLE_USER",
        "ROLE_ASSISTANT": "ROLE_ASSISTANT",
    }
    normalized = []
    for index, message in enumerate(conversation, 1):
        if not isinstance(message, dict):
            raise TypeError(f"message {index} must be a JSON object")
        role = message.get("role")
        if not isinstance(role, str) or role not in roles:
            raise ValueError(
                f"message {index} role must be user, assistant, ROLE_USER or ROLE_ASSISTANT"
            )
        content = message.get("content")
        if not isinstance(content, str) or not content.strip() or len(content) > 16384:
            raise ValueError(
                f"message {index} content must be non-empty text of at most 16384 characters"
            )
        normalized.append({"role": roles[role], "content": content})
    return normalized


@dataclass(frozen=True)
class YandexSearchClient:
    api_key: str
    folder_id: str
    timeout: float = 30

    def web_search(
        self,
        query_text: str,
        *,
        search_type: str,
        num_results: int,
        page: int,
        region: str | None = None,
        pages: int = 1,
        period: str | None = None,
        sort_mode: str | None = None,
        sort_order: str | None = None,
    ) -> list[dict]:
        body: dict = {
            "folderId": self.folder_id,
            "query": {
                "searchType": search_type,
                "queryText": query_text,
                "page": page,
            },
            "groupSpec": {
                "groupMode": "GROUP_MODE_FLAT",
                "groupsOnPage": num_results,
                "docsInGroup": 1,
            },
            "maxPassages": 2,
        }
        if region:
            body["region"] = region
        if period:
            body["period"] = period
        if sort_mode or sort_order:
            body["sortSpec"] = {}
            if sort_mode:
                body["sortSpec"]["sortMode"] = sort_mode
            if sort_order:
                body["sortSpec"]["sortOrder"] = sort_order

        docs = []
        seen = set()
        for offset in range(pages):
            request_body = {**body, "query": {**body["query"], "page": page + offset}}
            data = self._post_dict(
                "/web/search", request_body, timeout=self.timeout, label="web search"
            )
            batch = parse_web_xml(data.get("rawData"))
            if not batch:
                break
            for doc in batch:
                url = doc["url"]
                if pages == 1 or not url or url not in seen:
                    docs.append(doc)
                    seen.add(url)
        return docs

    def generative_search(
        self,
        query: str | None = None,
        *,
        site: str | None = None,
        messages: list[dict[str, str]] | None = None,
        doc_format: str | None = None,
        lang: str | None = None,
        date_filter: str | None = None,
    ) -> dict:
        body: dict = {
            "folderId": self.folder_id,
            "messages": prepare_messages(query, messages),
            "fixMisspell": True,
        }
        if site:
            body["site"] = {"site": [site]}
        filters = []
        if doc_format is not None:
            try:
                format_enum = DOCUMENT_FORMATS[doc_format.lower()]
            except KeyError as exc:
                raise ValueError("unsupported document format") from exc
            filters.append({"format": format_enum})
        if lang is not None:
            filters.append({"lang": validate_language(lang)})
        if date_filter is not None:
            filters.append({"date": validate_date_filter(date_filter)})
        if filters:
            body["searchFilters"] = filters

        data = post_json("/gen/search", self.api_key, body, timeout=self.timeout)
        if isinstance(data, list):
            if not data:
                sys.exit("Yandex generative search returned an empty response")
            result = data[0]
        elif isinstance(data, dict):
            result = data
        else:
            sys.exit("Yandex generative search returned an unexpected response shape")
        if not isinstance(result, dict):
            sys.exit("Yandex generative search returned an unexpected response shape")
        return result

    def image_search(
        self,
        query_text: str,
        *,
        search_type: str,
        num_results: int,
        page: int,
        region: str | None = None,
    ) -> list[dict]:
        body: dict = {
            "folderId": self.folder_id,
            "query": {
                "searchType": search_type,
                "queryText": query_text,
                "page": page,
            },
            "docsOnPage": num_results,
        }
        if region:
            sys.exit("Yandex image search does not support --region")

        data = self._post_dict(
            "/image/search", body, timeout=self.timeout, label="image search"
        )
        return parse_image_xml(data.get("rawData"))

    def reverse_image_search(
        self,
        *,
        url: str | None = None,
        cbir_id: str | None = None,
        site: str | None = None,
        page: int = 0,
        family_mode: str | None = None,
    ) -> dict:
        body: dict = {"folderId": self.folder_id, "page": page}
        if url:
            body["url"] = url
        else:
            body["id"] = cbir_id
        if site:
            body["site"] = site
        if family_mode:
            body["familyMode"] = family_mode

        return self._post_dict(
            "/image/search_by_image",
            body,
            timeout=self.timeout,
            label="reverse image search",
        )

    def wordstat_top(
        self,
        phrase: str,
        *,
        num_phrases: int,
        regions: list[str] | None = None,
        devices: list[str] | None = None,
    ) -> dict:
        body: dict = {
            "folderId": self.folder_id,
            "phrase": phrase,
            "numPhrases": num_phrases,
        }
        if regions:
            body["regions"] = regions
        if devices:
            body["devices"] = devices
        return self._post_dict(
            "/wordstat/topRequests",
            body,
            timeout=self.timeout,
            label="wordstat top",
        )

    def wordstat_dynamics(
        self,
        phrase: str,
        *,
        period: str,
        from_date: str,
        to_date: str | None = None,
        regions: list[str] | None = None,
        devices: list[str] | None = None,
    ) -> dict:
        body: dict = {
            "folderId": self.folder_id,
            "phrase": phrase,
            "period": period,
            "fromDate": from_date,
        }
        if to_date:
            body["toDate"] = to_date
        if regions:
            body["regions"] = regions
        if devices:
            body["devices"] = devices
        return self._post_dict(
            "/wordstat/dynamics",
            body,
            timeout=self.timeout,
            label="wordstat dynamics",
        )

    def wordstat_regions(
        self,
        phrase: str,
        *,
        region_scope: str,
        devices: list[str] | None = None,
    ) -> dict:
        body: dict = {
            "folderId": self.folder_id,
            "phrase": phrase,
            "region": region_scope,
        }
        if devices:
            body["devices"] = devices
        return self._post_dict(
            "/wordstat/regions",
            body,
            timeout=self.timeout,
            label="wordstat regions",
        )

    def wordstat_regions_tree(self) -> dict:
        return self._post_dict(
            "/wordstat/getRegionsTree",
            {"folderId": self.folder_id},
            timeout=self.timeout,
            label="wordstat regions tree",
        )

    def _post_dict(
        self, path: str, body: dict[str, Any], *, timeout: float, label: str
    ) -> dict:
        data = post_json(path, self.api_key, body, timeout=timeout)
        if not isinstance(data, dict):
            sys.exit(f"Yandex {label} returned an unexpected response shape")
        return data
