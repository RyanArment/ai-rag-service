"""
Background ingestion queue helpers.
"""
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.database.repositories import SECIngestionJobRepository
from app.services.sec.ingestion import SECFilingIngestionService

logger = get_logger(__name__)


class SECFilingQueueProcessor:
    """Process SEC ingestion jobs."""

    def __init__(self):
        self.ingestor = SECFilingIngestionService()

    async def process_next(self, db: Session) -> bool:
        job = SECIngestionJobRepository.claim_next_pending(db=db)
        if not job:
            return False

        try:
            await self.ingestor.ingest_filing(
                db=db,
                cik=job.cik,
                accession_number=job.accession_number,
                form_type=job.form_type,
                filed_date=job.filed_date.isoformat() if job.filed_date else None,
                company_name=job.company_name,
                filing_url=job.filing_url,
            )
            SECIngestionJobRepository.mark_completed(db=db, job=job)
            return True
        except Exception as exc:
            logger.error(f"Ingestion job failed: {exc}", exc_info=True)
            SECIngestionJobRepository.mark_failed(db=db, job=job, error_message=str(exc))
            return True
