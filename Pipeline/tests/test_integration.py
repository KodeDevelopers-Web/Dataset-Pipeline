"""
Basic Integration Tests for Pipeline Components

Run with: pytest tests/test_integration.py
"""

import pytest
from pathlib import Path
import tempfile


class TestSchemas:
    """Test unified schema."""
    
    def test_create_sample(self):
        from schemas import create_sample
        
        sample = create_sample(
            dataset="test",
            id="1",
            instruction="Write code",
            output="print('hello')",
            language="python",
        )
        
        assert sample.id == "1"
        assert sample.dataset == "test"
        assert sample.language == "python"
        assert sample.output == "print('hello')"
    
    def test_sample_validation(self):
        from schemas import create_sample
        
        sample = create_sample(
            dataset="test",
            id="1",
            instruction="Write code",
            output="x = 1",
            language="python",
        )
        
        is_valid, errors = sample.validate()
        assert is_valid
        assert len(errors) == 0
    
    def test_invalid_sample(self):
        from schemas import UnifiedSample
        
        sample = UnifiedSample(
            id="",
            dataset="",
            language="",
            license="",
            instruction="",
            output="",
        )
        
        is_valid, errors = sample.validate()
        assert not is_valid
        assert len(errors) > 0


class TestLanguageDetector:
    """Test language detection."""
    
    def test_detect_python(self):
        from utils.language_detector import detect_language
        
        code = "def hello():\n    print('world')"
        lang = detect_language(code)
        assert lang == "python"
    
    def test_detect_javascript(self):
        from utils.language_detector import detect_language
        
        code = "function hello() { console.log('world'); }"
        lang = detect_language(code)
        assert lang == "javascript"
    
    def test_detect_from_extension(self):
        from utils.language_detector import detect_from_extension
        
        assert detect_from_extension("file.py") == "python"
        assert detect_from_extension("file.js") == "javascript"
        assert detect_from_extension("file.java") == "java"
    
    def test_normalize_language(self):
        from utils.language_detector import normalize_language
        
        assert normalize_language("python") == "python"
        assert normalize_language("PY") == "python"
        assert normalize_language("c++") == "cpp"
        assert normalize_language("unknown_lang") == "unknown"


class TestValidation:
    """Test validation system."""
    
    def test_validate_valid_sample(self):
        from utils.validator import validate_sample
        from schemas import create_sample
        
        sample = create_sample(
            dataset="test",
            id="1",
            instruction="Write code",
            output="x = 1",
            language="python",
        )
        
        result = validate_sample(sample.to_dict())
        assert result.is_valid
    
    def test_validate_invalid_sample(self):
        from utils.validator import validate_sample
        
        sample = {
            "id": "1",
            "dataset": "test",
            "language": "python",
            "license": "mit",
            "instruction": "Write code",
            "output": "",  # Empty output
        }
        
        result = validate_sample(sample)
        assert not result.is_valid


class TestAdapters:
    """Test adapter functionality."""
    
    def test_base_adapter_info(self):
        from adapters.humaneval import HumanEvalAdapter
        
        adapter = HumanEvalAdapter()
        info = adapter.get_info()
        
        assert info["name"] == "humaneval"
        assert "openai" in info["source_url"].lower()
    
    def test_adapter_preprocess(self):
        from adapters.humaneval import HumanEvalAdapter
        
        adapter = HumanEvalAdapter()
        
        sample = {
            "task_id": "HumanEval/0",
            "prompt": "def foo():",
            "canonical_solution": "    return 1",
            "test": "assert foo() == 1",
            "entry_point": "foo",
        }
        
        result = adapter.preprocess(sample)
        assert result is not None
        assert result.language == "python"
        assert result.dataset == "humaneval"


class TestExporters:
    """Test export functionality."""
    
    def test_jsonl_exporter(self):
        from exporters.base import JSONLExporter
        from schemas import create_sample
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.jsonl"
            
            exporter = JSONLExporter(output_path)
            
            sample = create_sample(
                dataset="test",
                id="1",
                instruction="Test",
                output="output",
                language="python",
            )
            
            exporter.write(sample.to_dict())
            exporter.close()
            
            assert output_path.exists()
            
            with open(output_path) as f:
                line = f.read()
                assert "test" in line
                assert "python" in line
    
    def test_exporter_factory(self):
        from exporters.base import create_exporter
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test JSONL
            exporter = create_exporter("jsonl", Path(tmpdir) / "test.jsonl")
            assert exporter is not None
            
            # Test unknown format
            with pytest.raises(ValueError):
                create_exporter("unknown", Path(tmpdir) / "test.xyz")


class TestConfiguration:
    """Test configuration system."""
    
    def test_get_config(self):
        from config import get_config
        
        config = get_config()
        assert "cache_dir" in config
        assert "output_dir" in config
        assert "max_tokens" in config
    
    def test_get_datasets_config(self):
        from config import get_datasets_config
        
        datasets = get_datasets_config()
        assert len(datasets) > 0
        
        # Check required fields
        for dataset in datasets:
            assert "id" in dataset
            assert "name" in dataset
            assert "adapter" in dataset
            assert "hf_name" in dataset


class TestRejectionStatistics:
    """Test rejection statistics reporting."""

    def test_module_report_is_available(self):
        import rejection_stats

        rejection_stats.report()

        assert hasattr(rejection_stats, "rejection_stats")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
