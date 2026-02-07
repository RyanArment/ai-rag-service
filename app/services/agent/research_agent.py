"""
Agentic multi-step research for SEC filings.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.services.rag.pipeline import RAGPipeline
from app.services.sec.edgar_client import EdgarClient
from app.services.sec.ingestion import SECFilingIngestionService
from app.services.sec.comparator import FilingComparator
from app.services.sec.cross_reference import extract_accession_numbers

logger = get_logger(__name__)


class ResearchAgent:
    """Multi-step agent to search, ingest, and answer SEC questions."""

    def __init__(self):
        self.edgar_client = EdgarClient()
        self.ingestor = SECFilingIngestionService()
        self.rag = RAGPipeline(top_k=6, context_window=5000)
        self.comparator = FilingComparator()

    async def run(
        self,
        db: Session,
        question: str,
        form_types: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        max_results: int = 5,
        include_compare: bool = True,
    ) -> Dict[str, Any]:
        logger.info(
            "Research agent start",
            extra={"question_length": len(question), "max_results": max_results},
        )

        search_results = await self.edgar_client.search_filings(
            query=question,
            start=0,
            count=max_results,
            form_types=form_types,
            date_from=date_from,
            date_to=date_to,
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
                company_name=result.company_name,
                filing_url=result.filing_url,
            )
            ingested.append(filing)

        filter_payload: Dict[str, Any] = {"source_type": "sec_filing"}
        if form_types and len(form_types) == 1:
            filter_payload["form_type"] = form_types[0]
        if date_from:
            filter_payload["filed_date_from"] = datetime.fromisoformat(date_from).date()
        if date_to:
            filter_payload["filed_date_to"] = datetime.fromisoformat(date_to).date()

        rag_result = await self.rag.query_async(
            question=question,
            filter=filter_payload,
        )

        references = []
        for source in rag_result.get("sources", []):
            references.extend(extract_accession_numbers(source.get("content", "")))

        compare_result = None
        if include_compare and len(ingested) >= 2:
            compare_result = await self.comparator.compare(
                accession_a=ingested[0].accession_number,
                accession_b=ingested[1].accession_number,
                focus_topic=question,
            )

        return {
            "answer": rag_result.get("answer"),
            "sources": rag_result.get("sources"),
            "ingested_filings": [
                {
                    "accession_number": f.accession_number,
                    "form_type": f.form_type,
                    "filed_date": f.filed_date.isoformat() if f.filed_date else None,
                    "document_id": str(f.document_id) if f.document_id else None,
                }
                for f in ingested
            ],
            "references": references,
            "comparison": compare_result,
        }
