"""
Adapter for EvolCode (Evol-Instruct-Code) dataset.

Evol-Instruct-Code-80k-v1 is an evolved code instruction dataset created
by applying evolutionary transformation techniques to instruction-following examples.

Dataset: https://huggingface.co/datasets/nickrosh/Evol-Instruct-Code-80k-v1
"""

from typing import Dict, Any, Optional
from adapters.base import BaseAdapter
from schemas import create_sample
from utils.language_detector import detect_language


class EvolCodeAdapter(BaseAdapter):
    """Adapter for EvolCode dataset."""
    
    def __init__(self):
        super().__init__(
            name="evolcode",
            hf_name="nickrosh/Evol-Instruct-Code-80k-v1",
            description="EvolCode - Evolved instruction-following code examples",
            source_url="https://huggingface.co/datasets/nickrosh/Evol-Instruct-Code-80k-v1",
        )
    
    def preprocess(self, sample: Dict[str, Any]) -> Optional[create_sample]:
        """
        Convert EvolCode sample to unified format.
        
        EvolCode samples contain:
        - instruction: Task description (evolved/improved)
        - output: Code solution
        """
        instruction = sample.get("instruction", "").strip()
        output = sample.get("output", "").strip()
        
        if not instruction or not output:
            return None
        
        # Try to detect language from output
        language = detect_language(output)
        if language == "unknown":
            language = "python"  # Default for EvolCode
        
        return create_sample(
            dataset=self.name,
            id=sample.get("id", ""),
            instruction=instruction,
            input="",
            output=output,
            language=language,
            license="cc-by-nc-sa-4.0",
            metadata={},
        )


# Backward compatibility
_adapter = None

def _get_adapter():
    global _adapter
    if _adapter is None:
        _adapter = EvolCodeAdapter()
    return _adapter

def process(dataset):
    """Legacy interface for streaming preprocessing."""
    adapter = _get_adapter()
    for sample in dataset:
        processed = adapter.preprocess(sample)
        if processed:
            yield processed.to_dict()