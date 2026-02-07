"""
Cross-reference extraction for SEC filings.
"""
import re
from typing import List, Dict


ACCESSION_PATTERN = re.compile(r"\b\d{10}-\d{2}-\d{6}\b")


def extract_accession_numbers(text: str, context_window: int = 80) -> List[Dict[str, str]]:
    """Extract accession numbers with surrounding context."""
    results: List[Dict[str, str]] = []
    for match in ACCESSION_PATTERN.finditer(text):
        start = max(0, match.start() - context_window)
        end = min(len(text), match.end() + context_window)
        results.append(
            {
                "accession_number": match.group(0),
                "context": text[start:end],
            }
        )
    return results
