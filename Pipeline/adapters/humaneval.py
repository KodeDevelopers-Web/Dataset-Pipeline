"""
Adapter for OpenAI HumanEval dataset.

OpenAI's HumanEval is a code generation benchmark consisting of 164 hand-crafted
programming problems with unit tests.

Dataset: https://huggingface.co/datasets/openai/openai_humaneval
"""

from typing import Dict, Any, Optional
from adapters.base import BaseAdapter
from schemas import create_sample, DifficultyLevel
from utils.language_detector import detect_language


class HumanEvalAdapter(BaseAdapter):
    """Adapter for OpenAI HumanEval dataset."""
    
    def __init__(self):
        super().__init__(
            name="humaneval",
            hf_name="openai/openai_humaneval",
            description="OpenAI HumanEval - Code generation benchmark",
            source_url="https://huggingface.co/datasets/openai/openai_humaneval",
        )
    
    def preprocess(self, sample: Dict[str, Any]) -> Optional[create_sample]:
        """
        Convert HumanEval sample to unified format.
        
        HumanEval samples contain:
        - task_id: Unique identifier
        - prompt: Function signature and description
        - canonical_solution: Reference implementation
        - test: Unit tests
        - entry_point: Function name to implement
        """
        task_id = sample.get("task_id", "")
        prompt = sample.get("prompt", "").strip()
        solution = sample.get("canonical_solution", "").strip()
        tests = sample.get("test", "").strip()
        
        if not prompt or not solution:
            return None
        
        # Extract entry point (function name) for better context
        entry_point = sample.get("entry_point", "")
        
        return create_sample(
            dataset=self.name,
            id=task_id,
            instruction="Write a Python function that satisfies the following specification.",
            input=prompt,
            output=solution,
            language="python",
            license="mit",
            difficulty=DifficultyLevel.MEDIUM.value,
            metadata={
                "entry_point": entry_point,
                "tests": tests,
                "source": "openai",
            }
        )


# Backward compatibility: module-level function for existing code
_adapter = None

def _get_adapter():
    global _adapter
    if _adapter is None:
        _adapter = HumanEvalAdapter()
    return _adapter

def process(dataset):
    """Legacy interface for streaming preprocessing."""
    adapter = _get_adapter()
    for sample in dataset:
        processed = adapter.preprocess(sample)
        if processed:
            yield processed.to_dict()
