from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


DEFAULT_ALLOWED_DOMAINS = {
    "usa.gov", "www.usa.gov", "healthcare.gov", "www.healthcare.gov", "hud.gov", "www.hud.gov",
    "acf.hhs.gov", "www.acf.hhs.gov", "fns.usda.gov", "www.fns.usda.gov", "studentaid.gov",
    "www.studentaid.gov", "va.gov", "www.va.gov", "irs.gov", "www.irs.gov", "childcare.gov",
    "www.childcare.gov", "211.org", "www.211.org", "nfcc.org", "www.nfcc.org"
}


@dataclass
class ParsedPage:
    url: str
    title: str
    text: str


def is_allowed_url(url: str, allowed_domains: Iterable[str] = DEFAULT_ALLOWED_DOMAINS) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    return parsed.netloc.lower() in set(allowed_domains)


def fetch_and_parse_page(url: str, timeout: int = 10) -> ParsedPage:
    """Fetch a public page from an allow-listed source and extract text.

    Production note: add robots.txt checks, vendor terms review, caching, provenance, and content freshness checks.
    """
    if not is_allowed_url(url):
        raise ValueError(f"URL is not in the allowed source list: {url}")
    headers = {"User-Agent": "FinancialBenefitsConsultantMVP/0.1 (+research prototype)"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else url
    text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
    return ParsedPage(url=url, title=title, text=text[:20000])


def parse_catalog_sources(catalog: List[dict]) -> List[ParsedPage]:
    pages: List[ParsedPage] = []
    for benefit in catalog:
        try:
            pages.append(fetch_and_parse_page(benefit["source_url"]))
        except Exception as exc:
            pages.append(ParsedPage(url=benefit.get("source_url", ""), title="Fetch failed", text=str(exc)))
    return pages
