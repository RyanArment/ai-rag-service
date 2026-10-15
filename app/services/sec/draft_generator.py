"""
Generate editable filing drafts from EDGAR context and markdown templates.
"""
from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.services.rag.pipeline import RAGPipeline
from app.services.sec.edgar_client import EdgarClient
from app.services.sec.filing_templates import get_template
from app.services.sec.ingestion import SECFilingIngestionService

logger = get_logger(__name__)

DRAFT_SYSTEM_PROMPT = """You are helping prepare an internal SEC filing draft for review.
This is not legal advice and must not be presented as a filed document.

Rules:
- Follow the supplied markdown template structure (keep headings and section order).
- Replace {{COMPANY_NAME}} and {{REPORT_DATE}} with provided values where appropriate.
- Use retrieved peer-filing context for tone, structure, and factual patterns only when supported by context.
- Mark missing facts as [TBD]; do not invent numbers, dates, or material events.
- Output only the completed draft markdown document with no preamble or commentary."""


class FilingDraftGenerator:
    """Search EDGAR, ingest filings, and fill a template via RAG."""

    def __init__(self):
        self.edgar_client = EdgarClient()
        self.ingestor = SECFilingIngestionService()
        self.rag = RAGPipeline(top_k=8, context_window=6000)

    async def generate(
        self,
        db: Session,
        template_id: str,
        query: str,
        instructions: Optional[str] = None,
        company_name: Optional[str] = None,
        form_types: Optional[List[str]] = None,
        max_results: int = 3,
        temperature: float = 0.35,
        max_tokens: Optional[int] = 4096,
    ) -> Dict[str, Any]:
        template = get_template(template_id)
        if not template:
            raise ValueError(f"Unknown template: {template_id}")

        report_date = date.today().isoformat()
        company = (company_name or "[Company Name]").strip()
        skeleton = (
            template["body"]
            .replace("{{COMPANY_NAME}}", company)
            .replace("{{REPORT_DATE}}", report_date)
        )

        effective_forms = form_types or ([template["form_type"]] if template.get("form_type") else None)

        search_results = await self.edgar_client.search_filings(
            query=query,
            start=0,
            count=max_results,
            form_types=effective_forms,
        )

        ingested = []
        for result in search_results:
            if not result.accession_number:
                continue
            filing = await self.ingestor.ingest_filing(
                db=db,
                cik=result.cik,
                accession_number=result.accession_number,
                form_type=result.form_type,
                filed_date=result.filed_date,
                company_name=result.company_name or company_name,
                filing_url=result.filing_url,
            )
            ingested.append(filing)

        filter_payload: Dict[str, Any] = {"source_type": "sec_filing"}
        if effective_forms and len(effective_forms) == 1:
            filter_payload["form_type"] = effective_forms[0]

        user_question = f"""Complete this filing draft template using the retrieved SEC filing context.

Company name: {company}
Report date: {report_date}
EDGAR search query used: {query}
Additional instructions: {instructions or "(none)"}

Template to complete:
{skeleton}
"""

        rag_result = await self.rag.query_async(
            question=user_question,
            system_prompt=DRAFT_SYSTEM_PROMPT,
            temperature=temperature,
            max_tokens=max_tokens,
            filter=filter_payload,
        )

        draft_text = (rag_result.get("answer") or "").strip()
        if not draft_text:
            draft_text = skeleton

        return {
            "draft": draft_text,
            "template_id": template_id,
            "template_name": template["name"],
            "company_name": company,
            "report_date": report_date,
            "ingested_filings": [
                {
                    "accession_number": f.accession_number,
                    "form_type": f.form_type,
                    "filed_date": f.filed_date.isoformat() if f.filed_date else None,
                    "status": f.status,
                }
                for f in ingested
            ],
            "sources": rag_result.get("sources") or [],
            "model": rag_result.get("model"),
            "provider": rag_result.get("provider"),
        }
