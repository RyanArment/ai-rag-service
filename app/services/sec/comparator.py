"""
Filing comparison service.
"""
from typing import Any, Dict, List, Optional

from app.core.logging_config import get_logger
from app.services.embeddings.embedding_router import get_embedding_model
from app.services.vector_store.vector_store_router import get_vector_store
from app.services.llm_router import get_llm_client

logger = get_logger(__name__)


class FilingComparator:
    """Compare two SEC filings using RAG context."""

    async def compare(
        self,
        accession_a: str,
        accession_b: str,
        focus_topic: Optional[str] = None,
        top_k: int = 6,
    ) -> Dict[str, Any]:
        query = focus_topic or "Compare the filings and highlight key differences and similarities."
        embedding_model = get_embedding_model()
        query_embedding = await embedding_model.embed_async(query)

        vector_store = get_vector_store()
        results_a = vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter={"accession_number": accession_a, "source_type": "sec_filing"},
        )
        results_b = vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter={"accession_number": accession_b, "source_type": "sec_filing"},
        )

        context_a = "\n\n".join([r.document.content for r in results_a])
        context_b = "\n\n".join([r.document.content for r in results_b])

        prompt = f"""You are a securities analyst. Compare the two SEC filings below.
Focus: {query}

Filing A (accession {accession_a}):
{context_a}

Filing B (accession {accession_b}):
{context_b}

Provide a structured comparison with citations to each filing section where possible."""

        llm_client = get_llm_client()
        response = await llm_client.ask_async(prompt=prompt, temperature=0.2)

        return {
            "answer": response.content,
            "sources": {
                "filing_a": [
                    {"content": r.document.content, "score": r.score, "metadata": r.document.metadata}
                    for r in results_a
                ],
                "filing_b": [
                    {"content": r.document.content, "score": r.score, "metadata": r.document.metadata}
                    for r in results_b
                ],
            },
            "model": response.model,
            "provider": response.provider,
            "usage": response.usage,
        }
