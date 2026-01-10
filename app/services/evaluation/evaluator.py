"""
Main evaluation orchestrator.
"""
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from app.services.evaluation.base import BaseEvaluator, EvaluationReport, EvaluationResult
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class Evaluator:
    """
    Main evaluator that runs multiple metrics on test sets.
    """
    
    def __init__(self, metrics: List[BaseEvaluator]):
        """
        Initialize evaluator with list of metrics.
        
        Args:
            metrics: List of evaluator instances to run
        """
        self.metrics = metrics
        logger.info(f"Initialized evaluator with {len(metrics)} metrics")
    
    def evaluate_single(
        self,
        question: str,
        expected_answer: Optional[str],
        actual_answer: str,
        context: Optional[List[str]] = None,
    ) -> List[EvaluationResult]:
        """
        Evaluate a single Q&A pair with all metrics.
        
        Returns:
            List of EvaluationResult objects, one per metric
        """
        results = []
        
        for metric in self.metrics:
            try:
                result = metric.evaluate(
                    question=question,
                    expected_answer=expected_answer,
                    actual_answer=actual_answer,
                    context=context,
                )
                results.append(result)
            except Exception as e:
                logger.error(
                    f"Error evaluating with {metric.get_metric_name()}: {e}",
                    exc_info=True
                )
                results.append(EvaluationResult(
                    metric_name=metric.get_metric_name(),
                    score=0.0,
                    details={"error": str(e)}
                ))
        
        return results
    
    def evaluate_batch(
        self,
        test_set: List[Dict[str, Any]],
        test_set_name: str = "default",
    ) -> EvaluationReport:
        """
        Evaluate a batch of Q&A pairs.
        
        Args:
            test_set: List of dicts with keys: question, expected_answer (optional), actual_answer, context (optional)
            test_set_name: Name for this test set
            
        Returns:
            EvaluationReport with aggregated results
        """
        evaluation_id = str(uuid.uuid4())
        all_results = []
        
        logger.info(
            f"Starting batch evaluation",
            extra={
                "evaluation_id": evaluation_id,
                "test_set_name": test_set_name,
                "num_questions": len(test_set),
            }
        )
        
        for idx, item in enumerate(test_set):
            question = item.get("question", "")
            expected_answer = item.get("expected_answer")
            actual_answer = item.get("actual_answer", "")
            context = item.get("context")
            
            results = self.evaluate_single(
                question=question,
                expected_answer=expected_answer,
                actual_answer=actual_answer,
                context=context,
            )
            
            all_results.extend(results)
            
            if (idx + 1) % 10 == 0:
                logger.info(f"Evaluated {idx + 1}/{len(test_set)} questions")
        
        # Calculate overall scores per metric
        metric_scores: Dict[str, List[float]] = {}
        for result in all_results:
            if result.metric_name not in metric_scores:
                metric_scores[result.metric_name] = []
            metric_scores[result.metric_name].append(result.score)
        
        # Calculate averages
        metric_averages = {
            metric_name: sum(scores) / len(scores)
            for metric_name, scores in metric_scores.items()
        }
        
        overall_score = sum(metric_averages.values()) / len(metric_averages) if metric_averages else None
        
        report = EvaluationReport(
            evaluation_id=evaluation_id,
            test_set_name=test_set_name,
            total_questions=len(test_set),
            results=all_results,
            overall_score=overall_score,
            metadata={
                "metric_averages": metric_averages,
                "metrics_used": [m.get_metric_name() for m in self.metrics],
            }
        )
        
        logger.info(
            f"Batch evaluation complete",
            extra={
                "evaluation_id": evaluation_id,
                "overall_score": overall_score,
                "metric_averages": metric_averages,
            }
        )
        
        return report
    
    def save_report(self, report: EvaluationReport, filepath: str) -> None:
        """Save evaluation report to JSON file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            json.dump(report.dict(), f, indent=2, default=str)
        
        logger.info(f"Saved evaluation report to {filepath}")
    
    def load_test_set(self, filepath: str) -> List[Dict[str, Any]]:
        """Load test set from JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "test_set" in data:
            return data["test_set"]
        else:
            raise ValueError(f"Invalid test set format in {filepath}")
