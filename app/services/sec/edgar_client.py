"""
SEC EDGAR API client.
"""
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import SEC_USER_AGENT, SEC_RATE_LIMIT_PER_SEC, SEC_CACHE_DIR
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class FilingSearchResult:
    cik: str
    accession_number: str
    form_type: str
    filed_date: Optional[str]
    filing_url: Optional[str]
    company_name: Optional[str]


class EdgarClient:
    """Minimal EDGAR client for search and filing download."""

    def __init__(self):
        self._last_request_ts = 0.0
        self._rate_limit = max(1.0, SEC_RATE_LIMIT_PER_SEC)
        self._headers = {
            "User-Agent": SEC_USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
        }
        self._accession_pattern = re.compile(r"^[0-9-]{10,25}$")

    def _sanitize_accession(self, accession_number: str) -> str:
        if not accession_number or not self._accession_pattern.fullmatch(accession_number):
            raise ValueError("Invalid accession number format")
        if any(sep in accession_number for sep in ("/", "\\", "..")):
            raise ValueError("Invalid accession number format")
        return accession_number

    def _throttle(self) -> None:
        min_interval = 1.0 / self._rate_limit
        now = time.monotonic()
        elapsed = now - self._last_request_ts
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_ts = time.monotonic()

    async def _get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._throttle()
        async with httpx.AsyncClient(timeout=30.0, headers=self._headers) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def _get_text(self, url: str) -> str:
        self._throttle()
        async with httpx.AsyncClient(timeout=30.0, headers=self._headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    async def search_filings(
        self,
        query: str,
        start: int = 0,
        count: int = 10,
        form_types: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[FilingSearchResult]:
        """Search filings using EDGAR full-text search (EFTS)."""
        params: Dict[str, Any] = {
            "q": query,
            "start": start,
            "count": count,
        }
        if form_types:
            params["forms"] = ",".join(form_types)
        if date_from:
            params["from"] = date_from
        if date_to:
            params["to"] = date_to

        data = await self._get_json("https://efts.sec.gov/LATEST/search-index", params=params)

        results: List[FilingSearchResult] = []
        hits = data.get("hits", {}).get("hits", [])
        for hit in hits:
            source = hit.get("_source", {}) if isinstance(hit, dict) else {}
            ciks = source.get("ciks") or []
            cik_value = ciks[0] if isinstance(ciks, list) and ciks else source.get("cik")
            cik = str(cik_value or "").zfill(10)
            accession_number = source.get("accessionNo") or source.get("accession_number") or source.get("adsh")
            form_type = source.get("formType") or source.get("form_type") or source.get("form")
            filed_date = source.get("filedDate") or source.get("filed_date") or source.get("file_date")
            company_name = None
            display_names = source.get("display_names") or source.get("companyName") or source.get("company_name")
            if isinstance(display_names, list) and display_names:
                company_name = display_names[0]
            elif isinstance(display_names, str):
                company_name = display_names
            filing_url = source.get("linkToFilingDetails") or source.get("filingDetail")
            if not filing_url and cik and accession_number:
                accession_no_nodash = str(accession_number).replace("-", "")
                cik_str = str(int(cik)) if cik.isdigit() else cik.lstrip("0")
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik_str}/{accession_no_nodash}/{accession_number}-index.html"
            results.append(
                FilingSearchResult(
                    cik=cik,
                    accession_number=accession_number or "",
                    form_type=form_type or "",
                    filed_date=filed_date,
                    filing_url=filing_url,
                    company_name=company_name,
                )
            )

        return results

    async def get_company_submissions(self, cik: str) -> Dict[str, Any]:
        """Get submissions JSON for a company."""
        cik_padded = str(cik).zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        return await self._get_json(url)

    async def get_filing_index(self, cik: str, accession_number: str) -> Dict[str, Any]:
        """Get filing index JSON for a given accession number."""
        accession_number = self._sanitize_accession(accession_number)
        accession_no_nodash = accession_number.replace("-", "")
        cik_str = str(int(cik))
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_str}/{accession_no_nodash}/index.json"
        return await self._get_json(url)

    async def download_primary_filing_html(self, cik: str, accession_number: str) -> str:
        """Download the primary HTML document for a filing."""
        accession_number = self._sanitize_accession(accession_number)
        cache_path = os.path.join(SEC_CACHE_DIR, f"{accession_number}.html")
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as handle:
                return handle.read()

        index_json = await self.get_filing_index(cik=cik, accession_number=accession_number)
        items = index_json.get("directory", {}).get("item", [])

        candidate = None
        html_items = []
        txt_items = []
        for item in items:
            name = item.get("name", "")
            lower_name = name.lower()
            if lower_name.endswith((".htm", ".html")):
                html_items.append(item)
            elif lower_name.endswith(".txt"):
                txt_items.append(item)

        def sorted_by_size(items_list):
            return sorted(items_list, key=lambda i: i.get("size", 0), reverse=True)

        # Prefer non-index HTML, then TXT, then any HTML (index pages last)
        non_index_html = [item for item in html_items if "index" not in item.get("name", "").lower()]
        candidates = (
            [item.get("name") for item in sorted_by_size(non_index_html)]
            + [item.get("name") for item in sorted_by_size(txt_items)]
            + [item.get("name") for item in sorted_by_size(html_items)]
        )
        candidates = [name for name in candidates if name]

        if not candidates:
            raise ValueError("No primary document found in filing index")

        accession_no_nodash = accession_number.replace("-", "")
        cik_str = str(int(cik))
        html = None
        for candidate in candidates:
            url = f"https://www.sec.gov/Archives/edgar/data/{cik_str}/{accession_no_nodash}/{candidate}"
            try:
                html = await self._get_text(url)
                break
            except httpx.HTTPStatusError as exc:
                if exc.response is not None and exc.response.status_code == 404:
                    continue
                raise

        if html is None:
            raise ValueError("No downloadable primary document found in filing index")

        os.makedirs(SEC_CACHE_DIR, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as handle:
            handle.write(html)

        return html
