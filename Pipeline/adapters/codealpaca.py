"""
Adapter for CodeAlpaca dataset.

CodeAlpaca-20k is an instruction-tuning dataset with 20,000 code examples
converted from the Stanford Alpaca format for code generation.

Dataset: https://huggingface.co/datasets/sahil2801/CodeAlpaca-20k
"""

from typing import Dict, Any, Optional
from adapters.base import BaseAdapter
from schemas import create_sample
from utils.language_detector import detect_language


class CodeAlpacaAdapter(BaseAdapter):
    """Adapter for CodeAlpaca dataset."""
    
    def __init__(self):
        super().__init__(
            name="codealpaca",
            hf_name="sahil2801/CodeAlpaca-20k",
            description="CodeAlpaca - 20k code instruction examples",
            source_url="https://huggingface.co/datasets/sahil2801/CodeAlpaca-20k",
        )
    
    def preprocess(self, sample: Dict[str, Any]) -> Optional[create_sample]:
        """
        Convert CodeAlpaca sample to unified format.
        
        CodeAlpaca samples contain:
        - instruction: Task description
        - input: Input/context (may be empty)
        - output: Model output/solution
        """
        instruction = sample.get("instruction", "").strip()
        input_text = sample.get("input", "").strip()
        output = sample.get("output", "").strip()
        
        if not instruction or not output:
            return None
        
        # Try to detect language from output
        language = detect_language(output)
        
        return create_sample(
            dataset=self.name,
            id=sample.get("id", ""),
            instruction=instruction,
            input=input_text,
            output=output,
            language=language,
            license="cc-by-4.0",
            metadata={},
        )


# Backward compatibility
_adapter = None

def _get_adapter():
    global _adapter
    if _adapter is None:
        _adapter = CodeAlpacaAdapter()
    return _adapter

def process(dataset):
    """Legacy interface for streaming preprocessing."""
    adapter = _get_adapter()
    for sample in dataset:
        processed = adapter.preprocess(sample)
        if processed:
            yield processed.to_dict()