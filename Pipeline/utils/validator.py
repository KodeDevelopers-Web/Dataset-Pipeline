"""
Enhanced Validation System

Provides comprehensive validation for preprocessed samples with detailed
error reporting and recovery suggestions.
"""

from typing import Dict, Any, List, Tuple
from schemas import UnifiedSample
from utils.tokenizer import sample_tokens
from config import MAX_TOKENS, MIN_TOKENS


class ValidationResult:
    """Result of validating a sample."""
    
    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def __bool__(self):
        return self.is_valid
    
    def __str__(self):
        msg = "VALID" if self.is_valid else "INVALID"
        if self.errors:
            msg += f"\n  Errors: {len(self.errors)}"
            for error in self.errors[:3]:
                msg += f"\n    - {error}"
            if len(self.errors) > 3:
                msg += f"\n    ... and {len(self.errors) - 3} more"
        if self.warnings:
            msg += f"\n  Warnings: {len(self.warnings)}"
            for warning in self.warnings[:2]:
                msg += f"\n    - {warning}"
            if len(self.warnings) > 2:
                msg += f"\n    ... and {len(self.warnings) - 2} more"
        return msg


def validate_sample(sample: Dict[str, Any] | UnifiedSample) -> ValidationResult:
    """
    Validate a preprocessed sample.
    
    Checks:
    - Required fields present
    - Field types correct
    - Field lengths appropriate
    - UTF-8 validity
    - Token counts
    
    Args:
        sample: Sample to validate
        
    Returns:
        ValidationResult with detailed feedback
    """
    if isinstance(sample, UnifiedSample):
        sample_dict = sample.to_dict()
    else:
        sample_dict = sample
    
    errors = []
    warnings = []
    
    # Required fields
    required_fields = ["id", "dataset", "language", "license", "instruction", "output"]
    for field in required_fields:
        if field not in sample_dict:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(sample_dict[field], str):
            errors.append(f"Field '{field}' must be string, got {type(sample_dict[field]).__name__}")
        elif not sample_dict[field].strip():
            errors.append(f"Field '{field}' is empty")
    
    if errors:
        return ValidationResult(False, errors, warnings)
    
    # UTF-8 validation
    for field in ["instruction", "input", "output"]:
        try:
            sample_dict[field].encode("utf-8")
        except UnicodeEncodeError:
            errors.append(f"Field '{field}' contains invalid UTF-8")
    
    if errors:
        return ValidationResult(False, errors, warnings)
    
    # Output not just whitespace
    if not sample_dict["output"].strip():
        errors.append("Output cannot be only whitespace")
    
    # Language validation
    from schemas import SUPPORTED_LANGUAGES
    if sample_dict["language"].lower() not in SUPPORTED_LANGUAGES and sample_dict["language"].lower() != "unknown":
        warnings.append(f"Language '{sample_dict['language']}' not in supported list")
    
    # Token count validation
    try:
        tokens = sample_tokens(sample_dict)
        if tokens < MIN_TOKENS:
            warnings.append(f"Sample is very short ({tokens} tokens, min {MIN_TOKENS})")
        elif tokens > MAX_TOKENS:
            errors.append(f"Sample exceeds max tokens ({tokens} > {MAX_TOKENS})")
    except Exception as e:
        warnings.append(f"Could not count tokens: {e}")
    
    # Metadata validation
    metadata = sample_dict.get("metadata", {})
    if not isinstance(metadata, dict):
        errors.append(f"Metadata must be dict, got {type(metadata).__name__}")
    
    # Tests validation
    tests = sample_dict.get("tests", [])
    if not isinstance(tests, list):
        errors.append(f"Tests must be list, got {type(tests).__name__}")
    
    is_valid = len(errors) == 0
    return ValidationResult(is_valid, errors, warnings)


def validate_batch(samples: List[Dict[str, Any]]) -> Tuple[int, int, List[str]]:
    """
    Validate a batch of samples.
    
    Args:
        samples: List of samples to validate
        
    Returns:
        (valid_count, invalid_count, error_messages)
    """
    valid_count = 0
    invalid_count = 0
    error_messages = []
    
    for i, sample in enumerate(samples):
        result = validate_sample(sample)
        if result:
            valid_count += 1
        else:
            invalid_count += 1
            if error_messages:  # Only keep first few
                for error in result.errors:
                    error_messages.append(f"Sample {i}: {error}")
            if len(error_messages) > 20:
                break
    
    return valid_count, invalid_count, error_messages


def get_validation_stats(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get validation statistics for a batch.
    
    Args:
        samples: Samples to analyze
        
    Returns:
        Dictionary of validation statistics
    """
    valid = 0
    invalid = 0
    errors_by_type = {}
    warnings_by_type = {}
    
    for sample in samples:
        result = validate_sample(sample)
        if result:
            valid += 1
        else:
            invalid += 1
            for error in result.errors:
                error_type = error.split(":")[0]
                errors_by_type[error_type] = errors_by_type.get(error_type, 0) + 1
            for warning in result.warnings:
                warning_type = warning.split(":")[0]
                warnings_by_type[warning_type] = warnings_by_type.get(warning_type, 0) + 1
    
    return {
        "total": len(samples),
        "valid": valid,
        "invalid": invalid,
        "valid_percent": 100 * valid / len(samples) if samples else 0,
        "errors_by_type": errors_by_type,
        "warnings_by_type": warnings_by_type,
    }
