#!/usr/bin/env python3
"""
Background worker for SEC ingestion queue.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import SEC_WORKER_POLL_SECONDS
from app.core.logging_config import setup_logging, get_logger
from app.database.database import get_db_context
from app.services.sec.queue import SECFilingQueueProcessor

setup_logging()
logger = get_logger(__name__)


async def run_worker() -> None:
    processor = SECFilingQueueProcessor()
    logger.info("SEC ingestion worker started")
    while True:
        with get_db_context() as db:
            processed = await processor.process_next(db=db)
        if not processed:
            await asyncio.sleep(SEC_WORKER_POLL_SECONDS)


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("SEC ingestion worker stopped")
