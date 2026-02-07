"""
SEC filing ingestion pipeline.
"""
import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.database.models import SECCompany, SECFiling
from app.database.repositories import DocumentRepository
from app.services.document_processor.processor import DocumentProcessor
from app.services.embeddings.embedding_router import get_embedding_model
from app.services.vector_store.vector_store_router import get_vector_store
from app.services.vector_store.base import Document as VectorDocument
from app.services.sec.edgar_client import EdgarClient
from app.services.sec.filing_parser import html_to_text, extract_sections

logger = get_logger(__name__)


class SECFilingIngestionService:
    """Ingest SEC filings into the vector store."""

    def __init__(self):
        self.client = EdgarClient()
        self.processor = DocumentProcessor(chunk_size=1200, chunk_overlap=200, chunk_strategy="sentence")

    def _get_or_create_company(self, db: Session, cik: str, company_name: Optional[str]) -> SECCompany:
        company = db.query(SECCompany).filter(SECCompany.cik == cik).first()
        if company:
            if company_name and not company.company_name:
                company.company_name = company_name
                db.commit()
            return company

        company = SECCompany(
            cik=cik,
            company_name=company_name,
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        return company

    async def ingest_filing(
        self,
        db: Session,
        cik: str,
        accession_number: str,
        form_type: str,
        filed_date: Optional[str],
        company_name: Optional[str] = None,
        filing_url: Optional[str] = None,
    ) -> SECFiling:
        """Download, parse, embed, and store a filing."""
        cik_padded = str(cik).zfill(10)
        company = self._get_or_create_company(db=db, cik=cik_padded, company_name=company_name)

        existing = db.query(SECFiling).filter(SECFiling.accession_number == accession_number).first()
        if existing and existing.status == "indexed":
            return existing

        filing = existing or SECFiling(
            accession_number=accession_number,
            company_id=company.id,
            form_type=form_type,
            filed_date=datetime.fromisoformat(filed_date).date() if filed_date else datetime.utcnow().date(),
            filing_url=filing_url or "",
            status="downloading",
            filing_metadata=json.dumps({"source": "edgar"}),
        )
        if not existing:
            db.add(filing)
        db.commit()
        db.refresh(filing)

        html = await self.client.download_primary_filing_html(cik=cik_padded, accession_number=accession_number)
        text = html_to_text(html)
        sections = extract_sections(text)

        db_document = DocumentRepository.create_document(
            db=db,
            filename=f"{accession_number}.html",
            file_size=len(html),
            file_type="sec_filing",
            status="processing",
        )

        chunks = []
        for section in sections:
            section_chunks = self.processor.process_text(
                section.text,
                metadata={
                    "source_type": "sec_filing",
                    "form_type": form_type,
                    "cik": cik_padded,
                    "accession_number": accession_number,
                    "filed_date": filed_date,
                    "filing_section": section.title,
                },
            )
            chunks.extend(section_chunks)

        embedding_model = get_embedding_model()
        texts = [chunk.content for chunk in chunks]
        embeddings = await embedding_model.embed_async(texts)

        vector_documents = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{db_document.id}_chunk_{i}"
            vector_documents.append(
                VectorDocument(
                    id=chunk_id,
                    content=chunk.content,
                    metadata={
                        **chunk.metadata,
                        "document_id": str(db_document.id),
                        "chunk_index": i,
                    },
                    embedding=embedding,
                )
            )

        vector_store = get_vector_store()
        vector_store.add_documents(vector_documents)

        DocumentRepository.update_document(
            db=db,
            document_id=db_document.id,
            status="completed",
            chunks_count=len(chunks),
        )

        filing.document_id = db_document.id
        filing.status = "indexed"
        db.commit()
        db.refresh(filing)

        logger.info(
            "SEC filing ingested",
            extra={
                "accession_number": accession_number,
                "document_id": str(db_document.id),
                "chunks": len(chunks),
            },
        )

        return filing
