"""
Markdown skeletons for demo filing drafts (not legal templates).
"""
from typing import Any, Dict, List, Optional

TEMPLATES: Dict[str, Dict[str, Any]] = {
    "8k-general": {
        "id": "8k-general",
        "name": "Form 8-K (general)",
        "form_type": "8-K",
        "description": "Current report outline with Items 1.01–9.01 placeholders.",
        "body": """# FORM 8-K
## CURRENT REPORT

**Company:** {{COMPANY_NAME}}
**Date of report:** {{REPORT_DATE}}
**Commission file number:** [TBD]

---

### Item [X.XX]. [Entry Title]

[Describe the event or disclosure. Reference material terms, dates, and parties.]

### Item 9.01. Financial Statements and Exhibits

(d) Exhibits.

| Exhibit | Description |
|---------|-------------|
| [TBD]   | [TBD]       |

---

**Signature**

Pursuant to the requirements of the Securities Exchange Act of 1934, the registrant has duly caused this report to be signed on its behalf by the undersigned hereunto duly authorized.

| | |
|---|---|
| **{{COMPANY_NAME}}** | |
| By: | _________________________ |
| Name: | [TBD] |
| Title: | [TBD] |
| Date: | {{REPORT_DATE}} |
""",
    },
    "10k-risk-factors": {
        "id": "10k-risk-factors",
        "name": "10-K Risk Factors (section)",
        "form_type": "10-K",
        "description": "Item 1A-style risk factor section draft from peer disclosures.",
        "body": """# ITEM 1A. RISK FACTORS

**Company:** {{COMPANY_NAME}}
**Draft prepared:** {{REPORT_DATE}}

Investing in our securities involves a high degree of risk. You should carefully consider the risks described below, together with all other information in this report, before making an investment decision.

## Risk factor summary

- [Bullet summary of principal risks — TBD]

---

## [Risk category 1 — e.g., Operational]

[Detailed risk disclosure in plain language. Include specific triggers, dependencies, and mitigations where known from context.]

## [Risk category 2 — e.g., Regulatory]

[Detailed risk disclosure.]

## [Risk category 3 — e.g., Market / competition]

[Detailed risk disclosure.]

---

*This section is a working draft for internal review only and does not constitute legal or filing advice.*
""",
    },
    "mda-excerpt": {
        "id": "mda-excerpt",
        "name": "MD&A excerpt",
        "form_type": "10-Q",
        "description": "Management discussion & analysis style narrative.",
        "body": """# MANAGEMENT'S DISCUSSION AND ANALYSIS
## OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS

**Company:** {{COMPANY_NAME}}
**Period covered:** [TBD fiscal period]
**Draft prepared:** {{REPORT_DATE}}

### Overview

[High-level business and macro context.]

### Results of operations

**Revenue.** [Drivers, segments, year-over-year or quarter-over-quarter commentary.]

**Cost of revenue / gross margin.** [TBD]

**Operating expenses.** [R&D, SG&A, etc.]

### Liquidity and capital resources

[Cash, debt, covenants, known commitments.]

### Critical accounting estimates

[If applicable from context.]

### Forward-looking statements

This draft may contain forward-looking statements subject to risks and uncertainties described in our SEC filings.
""",
    },
}


def list_templates(include_body: bool = False) -> List[Dict[str, Any]]:
    items = []
    for t in TEMPLATES.values():
        entry = {
            "id": t["id"],
            "name": t["name"],
            "form_type": t.get("form_type"),
            "description": t.get("description"),
        }
        if include_body:
            entry["body"] = t["body"]
        items.append(entry)
    return items


def get_template(template_id: str) -> Optional[Dict[str, Any]]:
    return TEMPLATES.get(template_id)
