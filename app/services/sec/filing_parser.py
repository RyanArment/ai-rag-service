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
