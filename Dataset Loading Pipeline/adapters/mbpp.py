"""
Adapter for MBPP (Mostly Basic Programming Problems) dataset.

MBPP is a benchmark consisting of 427 hand-written Python programming problems
with unit tests and reference solutions.

Dataset: https://huggingface.co/datasets/google-research-datasets/mbpp
"""

from typing import Dict, Any, Optional
from adapters.base import BaseAdapter
from schemas import create_sample, DifficultyLevel


class MBPPAdapter(BaseAdapter):
    """Adapter for MBPP dataset."""
    
    def __init__(self):
        super().__init__(
            name="mbpp",
            hf_name="google-research-datasets/mbpp",
            description="MBPP - Mostly Basic Programming Problems",
            source_url="https://huggingface.co/datasets/google-research-datasets/mbpp",
        )
    
    def preprocess(self, sample: Dict[str, Any]) -> Optional[create_sample]:
        """
        Convert MBPP sample to unified format.
        
        MBPP samples contain:
        - task_id: Unique identifier
        - text: Problem description
        - code: Reference implementation
        - test_list: List of test cases
        """
        task_id = sample.get("task_id", "")
        text = sample.get("text", "").strip()
        code = sample.get("code", "").strip()
        test_list = sample.get("test_list", [])
        
        if not text or not code:
            return None
        
        return create_sample(
            dataset=self.name,
            id=str(task_id),
            instruction=text,
            input="",
            output=code,
            language="python",
            license="cc-by-4.0",
            tests=test_list if isinstance(test_list, list) else [],
            difficulty=DifficultyLevel.EASY.value,
            metadata={
                "test_count": len(test_list) if test_list else 0,
            }
        )


# Backward compatibility: module-level function for existing code
_adapter = None

def _get_adapter():
    global _adapter
    if _adapter is None:
        _adapter = MBPPAdapter()
    return _adapter

def process(dataset):
    """Legacy interface for streaming preprocessing."""
    adapter = _get_adapter()
    for sample in dataset:
        processed = adapter.preprocess(sample)
        if processed:
            yield processed.to_dict()
