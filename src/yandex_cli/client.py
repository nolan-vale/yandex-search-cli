from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

from yandex_cli.parsers import parse_image_xml, parse_web_xml
from yandex_cli._common import post_json


@dataclass(frozen=True)
class YandexSearchClient:
    api_key: str
    folder_id: str

    def web_search(
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
            "groupSpec": {
                "groupsOnPage": num_results,
                "docsInGroup": 1,
            },
            "maxPassages": 2,
        }
        if region:
            body["query"]["region"] = region

        data = self._post_dict("/web/search", body, timeout=15, label="web search")
        return parse_web_xml(data.get("rawData"))

    def generative_search(self, query: str, *, site: str | None = None) -> dict:
        body: dict = {
            "folderId": self.folder_id,
            "messages": [{"content": query, "role": "ROLE_USER"}],
            "fixMisspell": True,
        }
        if site:
            body["site"] = [site]

        data = post_json("/gen/search", self.api_key, body, timeout=30)
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
            body["query"]["region"] = region

        data = self._post_dict("/image/search", body, timeout=15, label="image search")
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
            timeout=15,
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
            timeout=15,
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
            timeout=15,
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
            timeout=15,
            label="wordstat regions",
        )

    def wordstat_regions_tree(self) -> dict:
        return self._post_dict(
            "/wordstat/getRegionsTree",
            {"folderId": self.folder_id},
            timeout=15,
            label="wordstat regions tree",
        )

    def _post_dict(
        self, path: str, body: dict[str, Any], *, timeout: int, label: str
    ) -> dict:
        data = post_json(path, self.api_key, body, timeout=timeout)
        if not isinstance(data, dict):
            sys.exit(f"Yandex {label} returned an unexpected response shape")
        return data
