"""
Export Formats Module

Provides exporters for different output formats:
- JSONL (line-delimited JSON)
- Parquet (columnar format)
- HuggingFace Datasets (cached/versioned)
- Arrow (Apache Arrow format)
"""

from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Optional
from pathlib import Path
import json


class BaseExporter(ABC):
    """Abstract base class for exporters."""
    
    def __init__(self, path: Path, compression: Optional[str] = None):
        """
        Initialize exporter.
        
        Args:
            path: Output path
            compression: Optional compression method (gzip, snappy, etc.)
        """
        self.path = Path(path)
        self.compression = compression
        self.path.parent.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def write(self, sample: Dict[str, Any]):
        """Write a single sample."""
        pass
    
    @abstractmethod
    def close(self):
        """Finalize export and close resources."""
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Get export information."""
        pass


class JSONLExporter(BaseExporter):
    """
    Export to JSONL (line-delimited JSON) format.
    
    Simple, streaming-friendly format where each line is a valid JSON object.
    """
    
    def __init__(self, path: Path, append: bool = False, compression: Optional[str] = None):
        """
        Initialize JSONL exporter.
        
        Args:
            path: Output file path
            append: If True, append to existing file
            compression: Optional compression (gzip, brotli, etc.)
        """
        super().__init__(path, compression)
        self.sample_count = 0
        
        mode = "a" if (append and self.path.exists()) else "w"
        
        # Handle compression
        if compression == "gzip":
            import gzip
            self.file = gzip.open(self.path, f"{mode}t", encoding="utf-8")
        elif compression == "brotli":
            try:
                import brotli
                # Brotli doesn't support streaming writes well, use manual buffering
                self.file = open(self.path, mode, encoding="utf-8")
            except ImportError:
                raise ImportError("brotli not installed. Install with: pip install brotli")
        else:
            self.file = open(self.path, mode, encoding="utf-8")
    
    def write(self, sample: Dict[str, Any]):
        """Write sample as JSON line."""
        self.file.write(json.dumps(sample, ensure_ascii=False) + "\n")
        self.sample_count += 1
    
    def close(self):
        """Close file."""
        if self.file:
            self.file.close()
    
    def get_info(self) -> Dict[str, Any]:
        """Get export information."""
        return {
            "format": "jsonl",
            "path": str(self.path),
            "samples": self.sample_count,
            "compression": self.compression or "none",
            "file_size": self.path.stat().st_size if self.path.exists() else 0,
        }


class ParquetExporter(BaseExporter):
    """
    Export to Parquet format.
    
    Columnar format useful for analysis and efficient storage.
    Requires pyarrow.
    """
    
    def __init__(self, path: Path, batch_size: int = 1000, compression: str = "snappy"):
        """
        Initialize Parquet exporter.
        
        Args:
            path: Output file path (.parquet extension)
            batch_size: Number of samples to batch before writing
            compression: Compression method (snappy, gzip, brotli, etc.)
        """
        super().__init__(path, compression)
        
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            raise ImportError("pyarrow not installed. Install with: pip install pyarrow")
        
        self.pa = pa
        self.pq = pq
        self.batch_size = batch_size
        self.compression = compression or "snappy"
        
        self.samples_buffer = []
        self.sample_count = 0
        self.writer = None
        self.schema = None
    
    def _flush_buffer(self):
        """Write buffered samples to parquet file."""
        if not self.samples_buffer:
            return
        
        import pyarrow as pa
        import pyarrow.parquet as pq
        
        # Create table from samples
        # Convert to appropriate types
        data_dict = {}
        for key in self.samples_buffer[0].keys():
            data_dict[key] = [
                sample.get(key) for sample in self.samples_buffer
            ]
        
        table = pa.Table.from_pydict(data_dict)
        
        if self.writer is None:
            # First batch - create writer
            self.writer = pq.ParquetWriter(
                self.path,
                table.schema,
                compression=self.compression,
            )
        
        self.writer.write_table(table)
        self.samples_buffer = []
    
    def write(self, sample: Dict[str, Any]):
        """Add sample to buffer and flush if needed."""
        self.samples_buffer.append(sample)
        self.sample_count += 1
        
        if len(self.samples_buffer) >= self.batch_size:
            self._flush_buffer()
    
    def close(self):
        """Flush remaining samples and close writer."""
        self._flush_buffer()
        if self.writer:
            self.writer.close()
    
    def get_info(self) -> Dict[str, Any]:
        """Get export information."""
        return {
            "format": "parquet",
            "path": str(self.path),
            "samples": self.sample_count,
            "compression": self.compression,
            "file_size": self.path.stat().st_size if self.path.exists() else 0,
        }


class HFDatasetExporter(BaseExporter):
    """
    Export to HuggingFace Datasets format.
    
    Saves data in HF's cached dataset format for easy loading with `load_dataset()`.
    Requires datasets library.
    """
    
    def __init__(self, path: Path, dataset_name: str = "prepared_dataset"):
        """
        Initialize HF Dataset exporter.
        
        Args:
            path: Output directory path
            dataset_name: Name for the dataset
        """
        super().__init__(path, compression=None)
        
        try:
            import datasets
        except ImportError:
            raise ImportError("datasets not installed. Install with: pip install datasets")
        
        self.datasets = datasets
        self.dataset_name = dataset_name
        self.samples = []
        self.sample_count = 0
    
    def write(self, sample: Dict[str, Any]):
        """Add sample to buffer."""
        self.samples.append(sample)
        self.sample_count += 1
    
    def close(self):
        """Create and save HF Dataset."""
        from datasets import Dataset
        
        # Create dataset from samples
        dataset = Dataset.from_dict({
            key: [sample[key] for sample in self.samples]
            for key in self.samples[0].keys() if self.samples
        })
        
        # Save using HF cache format
        dataset.save_to_disk(str(self.path))
    
    def get_info(self) -> Dict[str, Any]:
        """Get export information."""
        return {
            "format": "huggingface_dataset",
            "path": str(self.path),
            "samples": self.sample_count,
            "dataset_name": self.dataset_name,
        }


def create_exporter(
    format: str,
    path: Path,
    **kwargs
) -> BaseExporter:
    """
    Factory function to create appropriate exporter.
    
    Args:
        format: Export format ('jsonl', 'parquet', 'hf', etc.)
        path: Output path
        **kwargs: Additional arguments for exporter
        
    Returns:
        Appropriate exporter instance
    """
    format_lower = format.lower()
    
    if format_lower in ("jsonl", "json"):
        return JSONLExporter(path, **kwargs)
    elif format_lower == "parquet":
        return ParquetExporter(path, **kwargs)
    elif format_lower in ("hf", "huggingface", "dataset"):
        return HFDatasetExporter(path, **kwargs)
    else:
        raise ValueError(f"Unknown export format: {format}")
