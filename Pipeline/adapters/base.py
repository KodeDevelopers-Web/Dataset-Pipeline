"""
BaseAdapter - Abstract base class for dataset adapters.

Every dataset adapter should inherit from BaseAdapter and implement
the required methods. This ensures consistency and enables the pipeline
to work with adapters uniformly.

Example adapter implementation:

    class MyDatasetAdapter(BaseAdapter):
        def __init__(self):
            super().__init__(
                name="my_dataset",
                hf_name="my_dataset/my_config",
                description="My dataset",
            )

        def load(self):
            # Load dataset from HuggingFace or local source
            return load_dataset(self.hf_name)

        def preprocess(self, sample):
            # Transform raw sample to unified schema
            return create_sample(
                dataset=self.name,
                id=sample.get("id"),
                instruction=sample.get("prompt"),
                output=sample.get("completion"),
                language="python",
            )
"""

from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Optional
from datasets import Dataset, IterableDataset
from schemas import UnifiedSample


class BaseAdapter(ABC):
    """
    Abstract base class for dataset adapters.
    
    Every adapter should:
    1. Inherit from BaseAdapter
    2. Call super().__init__() with appropriate parameters
    3. Implement preprocess() to convert samples to UnifiedSample
    4. Optionally override download(), load(), validate()
    
    The pipeline handles:
    - Downloading
    - Checkpointing
    - Error handling
    - Validation
    - Deduplication
    - Export
    """

    def __init__(
        self,
        name: str,
        hf_name: str,
        description: str,
        source_url: Optional[str] = None,
    ):
        """
        Initialize adapter.
        
        Args:
            name: Unique identifier (e.g., "apps", "humaneval")
            hf_name: HuggingFace dataset ID or local identifier
            description: Human-readable description
            source_url: URL to dataset documentation
        """
        self.name = name
        self.hf_name = hf_name
        self.description = description
        self.source_url = source_url or f"https://huggingface.co/datasets/{hf_name}"

    @abstractmethod
    def preprocess(self, sample: Dict[str, Any]) -> Optional[UnifiedSample]:
        """
        Convert a raw sample from the dataset into UnifiedSample format.
        
        This is the core method that must be implemented by each adapter.
        
        Args:
            sample: Raw sample from the dataset
            
        Returns:
            UnifiedSample if sample is valid and should be included
            None if sample should be skipped
            
        Note:
            - Return None to filter out invalid/unwanted samples
            - All string fields should be stripped and normalized
            - Language should be detected automatically if possible
        """
        pass

    def load(self) -> Dataset | IterableDataset:
        """
        Load the dataset from HuggingFace or other source.
        
        Override this method if your dataset is not on HuggingFace
        or requires special loading logic.
        
        Returns:
            HuggingFace Dataset or IterableDataset
        """
        from datasets import load_dataset
        return load_dataset(self.hf_name)

    def validate(self, dataset: Dataset | IterableDataset) -> bool:
        """
        Validate that the loaded dataset has the expected structure.
        
        This is called before preprocessing and can be overridden to
        check dataset integrity.
        
        Args:
            dataset: Loaded dataset
            
        Returns:
            True if dataset is valid, False otherwise
        """
        return True

    def stream(self) -> Iterator[UnifiedSample]:
        """
        Stream preprocessed samples from this dataset.
        
        This is the main entry point used by the pipeline. It handles:
        1. Loading the dataset
        2. Validating it
        3. Preprocessing each sample
        4. Filtering out None results
        
        Yields:
            UnifiedSample objects
        """
        dataset = self.load()
        
        if not self.validate(dataset):
            raise ValueError(f"Dataset validation failed for {self.name}")
        
        for sample in dataset:
            processed = self.preprocess(sample)
            if processed is not None:
                yield processed

    def get_info(self) -> Dict[str, str]:
        """Get adapter metadata."""
        return {
            "name": self.name,
            "hf_name": self.hf_name,
            "description": self.description,
            "source_url": self.source_url,
        }
