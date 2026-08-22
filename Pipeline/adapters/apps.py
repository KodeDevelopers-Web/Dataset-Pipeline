"""
Adapter for APPS (Automated Problem-solving Programming set) dataset.

APPS is a benchmark for code generation with 10,000 competitive programming
problems with multiple solutions and test cases.

Dataset: https://huggingface.co/datasets/codeparrot/apps
"""

from typing import Dict, Any, Optional
from adapters.base import BaseAdapter
from schemas import create_sample, DifficultyLevel
from adapters.solutions import first_solution
from utils.language_detector import detect_language, normalize_language


class APPSAdapter(BaseAdapter):
    """Adapter for APPS dataset."""
    
    def __init__(self):
        super().__init__(
            name="apps",
            hf_name="codeparrot/apps",
            description="APPS - Automated Problem-solving Programming set",
            source_url="https://huggingface.co/datasets/codeparrot/apps",
        )
    
    def preprocess(self, sample: Dict[str, Any]) -> Optional[create_sample]:
        """
        Convert APPS sample to unified format.
        
        APPS samples contain:
        - problem_id: Unique identifier
        - question: Problem description
        - solutions: List of reference solutions (may be JSON string)
        - starter_code: Starter code provided to participants
        - difficulty: Difficulty level
        - input_output: Test cases
        """
        problem_id = sample.get("problem_id", "")
        question = sample.get("question", "").strip()
        solutions = sample.get("solutions", "")
        starter_code = sample.get("starter_code", "").strip()
        
        # Extract first valid solution
        solution = first_solution(solutions)
        if not solution:
            return None
        
        if not question:
            return None
        
        # Build input with starter code if available
        input_text = question
        if starter_code:
            input_text += f"\n\nStarter Code:\n{starter_code}"
        
        # Parse difficulty
        difficulty = sample.get("difficulty", "")
        if difficulty:
            difficulty = normalize_language(str(difficulty).lower())
            if difficulty not in ("easy", "medium", "hard"):
                difficulty = DifficultyLevel.UNKNOWN.value
        else:
            difficulty = DifficultyLevel.UNKNOWN.value
        
        # Extract test cases if available
        input_output = sample.get("input_output", {})
        tests = []
        if isinstance(input_output, dict):
            inputs = input_output.get("inputs", [])
            outputs = input_output.get("outputs", [])
            for inp, out in zip(inputs, outputs):
                tests.append({
                    "input": inp,
                    "expected": out,
                })
        
        # Detect language from solution
        language = detect_language(solution)
        if language == "unknown":
            language = "python"  # Default for APPS
        
        return create_sample(
            dataset=self.name,
            id=str(problem_id),
            instruction="Solve the following programming problem.",
            input=input_text,
            output=solution,
            language=language,
            license="mit",
            tests=tests,
            difficulty=difficulty,
            metadata={
                "test_count": len(tests),
                "has_starter": bool(starter_code),
            }
        )


# Backward compatibility: module-level function for existing code
_adapter = None

def _get_adapter():
    global _adapter
    if _adapter is None:
        _adapter = APPSAdapter()
    return _adapter

def process(dataset):
    """Legacy interface for streaming preprocessing."""
    adapter = _get_adapter()
    for sample in dataset:
        processed = adapter.preprocess(sample)
        if processed:
            yield processed.to_dict()

