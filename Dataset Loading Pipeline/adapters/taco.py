"""
Adapter for TACO (Test-Aimed Code Object) dataset.

TACO is a large-scale, diverse dataset of test-aimed code objectives for
code generation and understanding tasks.

Dataset: https://huggingface.co/datasets/BAAI/TACO
"""

from typing import Dict, Any, Optional
from adapters.base import BaseAdapter
from schemas import create_sample, DifficultyLevel
from adapters.solutions import first_solution
from utils.language_detector import detect_language


class TACOAdapter(BaseAdapter):
    """Adapter for TACO dataset."""
    
    def __init__(self):
        super().__init__(
            name="taco",
            hf_name="BAAI/TACO",
            description="TACO - Test-Aimed Code Object dataset",
            source_url="https://huggingface.co/datasets/BAAI/TACO",
        )
    
    def preprocess(self, sample: Dict[str, Any]) -> Optional[create_sample]:
        """
        Convert TACO sample to unified format.
        
        TACO samples contain:
        - question: Problem description
        - solutions: List of solutions (may be JSON string)
        - difficulty: Problem difficulty
        - test_list: Test cases
        """
        question = sample.get("question", "").strip()
        solutions = sample.get("solutions", "")
        difficulty = sample.get("difficulty", "")
        test_list = sample.get("test_list", [])
        
        # Extract first valid solution
        solution = first_solution(solutions)
        if not solution or not question:
            return None
        
        # Normalize difficulty
        if difficulty:
            difficulty = str(difficulty).lower().strip()
            if difficulty not in ("easy", "medium", "hard"):
                difficulty = DifficultyLevel.UNKNOWN.value
        else:
            difficulty = DifficultyLevel.UNKNOWN.value
        
        # Prepare tests if available
        tests = []
        if isinstance(test_list, list):
            tests = test_list
        
        # Detect language
        language = detect_language(solution)
        if language == "unknown":
            language = "python"  # Default for TACO
        
        return create_sample(
            dataset=self.name,
            id=sample.get("problem_id", ""),
            instruction="Solve the following programming problem.",
            input=question,
            output=solution,
            language=language,
            license="apache-2.0",
            tests=tests,
            difficulty=difficulty,
            metadata={
                "test_count": len(tests),
            },
        )


# Backward compatibility
_adapter = None

def _get_adapter():
    global _adapter
    if _adapter is None:
        _adapter = TACOAdapter()
    return _adapter

def process(dataset):
    """Legacy interface for streaming preprocessing."""
    adapter = _get_adapter()
    for sample in dataset:
        processed = adapter.preprocess(sample)
        if processed:
            yield processed.to_dict()
