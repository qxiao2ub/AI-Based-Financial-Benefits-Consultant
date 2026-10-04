from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_ALLOWED_DOMAINS = {
    "gov.uk", "www.gov.uk", "nhs.uk", "www.nhs.uk", "nhsbsa.nhs.uk", "www.nhsbsa.nhs.uk",
    "mygov.scot", "www.mygov.scot", "socialsecurity.gov.scot", "www.socialsecurity.gov.scot",
    "nidirect.gov.uk", "www.nidirect.gov.uk", "moneyhelper.org.uk", "www.moneyhelper.org.uk",
    "citizensadvice.org.uk", "www.citizensadvice.org.uk", "turn2us.org.uk", "www.turn2us.org.uk",
}


@dataclass
class ParsedPage:
    url: str
    title: str
    text: str


def is_allowed_url(url: str, allowed_domains: Iterable[str] = DEFAULT_ALLOWED_DOMAINS) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.netloc.lower() in set(allowed_domains)


def fetch_and_parse_page(url: str, timeout: int = 10) -> ParsedPage:
    """Fetch one allow-listed public guidance page and extract readable text.

    This parser is a research/MVP feature. Production deployments should review source terms,
    robots.txt, caching, provenance, accessibility and content-freshness requirements.
    """
    if not is_allowed_url(url):
        raise ValueError(f"URL is not in the approved UK source allow-list: {url}")
    headers = {"User-Agent": "UKFinancialBenefitsConsultantMVP/1.0 (benefits research prototype)"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "form"]):
        tag.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else url
    text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
    return ParsedPage(url=url, title=title, text=text[:22000])
