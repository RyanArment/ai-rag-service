"""
Concrete evaluation metrics implementations.
"""
from typing import Optional, List, Dict, Any
import re

from app.services.evaluation.base import BaseEvaluator, EvaluationResult
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ExactMatchEvaluator(BaseEvaluator):
    """Exact string match evaluation."""
    
    def get_metric_name(self) -> str:
        return "exact_match"
    
    def evaluate(
        self,
        question: str,
        expected_answer: Optional[str],
        actual_answer: str,
        context: Optional[List[str]] = None,
    ) -> EvaluationResult:
        """Check if actual answer exactly matches expected."""
        if not expected_answer:
            return EvaluationResult(
                metric_name=self.get_metric_name(),
                score=0.0,
                details={"error": "No expected answer provided"}
            )
        
        score = 1.0 if actual_answer.strip().lower() == expected_answer.strip().lower() else 0.0
        
        return EvaluationResult(
            metric_name=self.get_metric_name(),
            score=score,
            details={
                "expected": expected_answer,
                "actual": actual_answer,
                "match": score == 1.0,
            }
        )


class F1ScoreEvaluator(BaseEvaluator):
    """F1 score based on token overlap."""
    
    def get_metric_name(self) -> str:
        return "f1_score"
    
    def _tokenize(self, text: str) -> set:
        """Simple tokenization (whitespace + punctuation)."""
        tokens = re.findall(r'\b\w+\b', text.lower())
        return set(tokens)
    
    def evaluate(
        self,
        question: str,
        expected_answer: Optional[str],
        actual_answer: str,
        context: Optional[List[str]] = None,
    ) -> EvaluationResult:
        """Calculate F1 score based on token overlap."""
        if not expected_answer:
            return EvaluationResult(
                metric_name=self.get_metric_name(),
                score=0.0,
                details={"error": "No expected answer provided"}
            )
        
        expected_tokens = self._tokenize(expected_answer)
        actual_tokens = self._tokenize(actual_answer)
        
        if not expected_tokens:
            return EvaluationResult(
                metric_name=self.get_metric_name(),
                score=0.0,
                details={"error": "Expected answer has no tokens"}
            )
        
        # Calculate precision, recall, F1
        intersection = expected_tokens & actual_tokens
        
        if not actual_tokens:
            precision = 0.0
        else:
            precision = len(intersection) / len(actual_tokens)
        
        recall = len(intersection) / len(expected_tokens)
        
        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * (precision * recall) / (precision + recall)
        
        return EvaluationResult(
            metric_name=self.get_metric_name(),
            score=f1,
            details={
                "precision": precision,
                "recall": recall,
                "expected_tokens": len(expected_tokens),
                "actual_tokens": len(actual_tokens),
                "common_tokens": len(intersection),
            }
        )


class SemanticSimilarityEvaluator(BaseEvaluator):
    """
    Semantic similarity using embeddings.
    Note: Requires embedding model to be implemented.
    """
    
    def __init__(self, embedding_model=None):
        self.embedding_model = embedding_model
    
    def get_metric_name(self) -> str:
        return "semantic_similarity"
    
    def evaluate(
        self,
        question: str,
        expected_answer: Optional[str],
        actual_answer: str,
        context: Optional[List[str]] = None,
    ) -> EvaluationResult:
        """Calculate cosine similarity between embeddings."""
        if not expected_answer:
            return EvaluationResult(
                metric_name=self.get_metric_name(),
                score=0.0,
                details={"error": "No expected answer provided"}
            )
        
        if not self.embedding_model:
            return EvaluationResult(
                metric_name=self.get_metric_name(),
                score=0.0,
                details={"error": "Embedding model not configured"}
            )
        
        # TODO: Implement embedding-based similarity
        # This is a placeholder for when embeddings are added
        return EvaluationResult(
            metric_name=self.get_metric_name(),
            score=0.0,
            details={"error": "Not yet implemented - requires embedding model"}
        )


class AnswerRelevanceEvaluator(BaseEvaluator):
    """
    Evaluates if the answer is relevant to the question.
    Uses LLM to judge relevance (requires LLM client).
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    def get_metric_name(self) -> str:
        return "answer_relevance"
    
    def evaluate(
        self,
        question: str,
        expected_answer: Optional[str],
        actual_answer: str,
        context: Optional[List[str]] = None,
    ) -> EvaluationResult:
        """Use LLM to judge if answer is relevant to question."""
        if not self.llm_client:
            return EvaluationResult(
                metric_name=self.get_metric_name(),
                score=0.0,
                details={"error": "LLM client not configured"}
            )
        
        # TODO: Implement LLM-based relevance scoring
        # This would use the LLM to judge relevance on a scale
        return EvaluationResult(
            metric_name=self.get_metric_name(),
            score=0.0,
            details={"error": "Not yet implemented - requires LLM judgment"}
        )
