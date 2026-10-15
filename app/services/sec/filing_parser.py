"""
SEC filing HTML parser and section extractor.
"""
import re
from dataclasses import dataclass
from typing import List

from bs4 import BeautifulSoup


@dataclass
class FilingSection:
    title: str
    text: str


def html_to_text(html: str) -> str:
    """Convert HTML to plain text."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join([line for line in lines if line])


def extract_filing_text(raw: str, form_type: str = "10-K") -> str:
    """Extract readable prose from a primary HTML file or SEC full-submission .txt."""
    raw = raw.strip()
    if not raw:
        return ""

    base_form = (form_type or "10-K").upper().split("-")[0]

    if "<TYPE>" in raw.upper():
        selected = None
        fallback = None
        for part in re.split(r"(?im)^<TYPE>\s*", raw)[1:]:
            type_line, _, rest = part.partition("\n")
            doc_type = type_line.strip().upper()
            text_match = re.search(r"(?is)<TEXT>\s*(.*?)\s*</TEXT>", rest)
            if not text_match:
                continue
            body = text_match.group(1).strip()
            if doc_type.startswith(base_form) or base_form in doc_type:
                selected = body
                break
            if fallback is None and doc_type.split("-")[0] in {"10-K", "10-Q", "8-K", "20-F", "6-K"}:
                fallback = body
        content = selected or fallback
        if not content:
            return html_to_text(raw) if "<html" in raw.lower() else raw
        if "<html" in content.lower()[:4000]:
            return html_to_text(content)
        return content

    if "<html" in raw.lower()[:4000]:
        return html_to_text(raw)
    return raw


def extract_sections(text: str) -> List[FilingSection]:
    """Extract SEC item-based sections from plain text."""
    pattern = re.compile(r"(?i)\bitem\s+\d+[a-z]?\b\.?")
    matches = list(pattern.finditer(text))

    if not matches:
        return [FilingSection(title="Full Document", text=text)]

    sections: List[FilingSection] = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        title = text[start:match.end()].strip().replace("\n", " ")
        section_text = text[start:end].strip()
        if len(section_text) < 200:
            continue
        sections.append(FilingSection(title=title, text=section_text))

    if not sections:
        return [FilingSection(title="Full Document", text=text)]

    return sections
