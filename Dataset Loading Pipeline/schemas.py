"""
Unified Dataset Schema

Every dataset is normalized to this schema. This ensures consistency
across all sources and makes export/analysis straightforward.

Type Hints:
    - All string fields are required unless noted Optional
    - metadata: dict can contain arbitrary dataset-specific fields
    - tests: list of test cases (problem solving datasets only)
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum


class DifficultyLevel(str, Enum):
    """Programming problem difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    UNKNOWN = "unknown"


@dataclass
class UnifiedSample:
    """
    Universal dataset sample format.
    
    Fields:
        id: Unique identifier within dataset
        dataset: Source dataset name (e.g., "apps", "humaneval")
        language: Programming language (e.g., "python", "javascript")
        license: License type (e.g., "MIT", "Apache-2.0", "unknown")
        instruction: Task description/prompt
        input: Function signature, test input, or context
        output: Expected solution or output
        tests: Optional list of test cases [{"input": "...", "expected": "..."}]
        difficulty: Problem difficulty level
        metadata: Dataset-specific additional fields
    """
    id: str
    dataset: str
    language: str
    license: str
    instruction: str
    input: str
    output: str
    tests: List[Dict[str, Any]] = field(default_factory=list)
    difficulty: str = DifficultyLevel.UNKNOWN.value
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (compatible with JSON export)."""
        return asdict(self)

    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate sample completeness and correctness.
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # Required string fields
        for field_name in ("id", "dataset", "language", "license", "instruction", "output"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"Field '{field_name}' must be non-empty string")

        # Language validation
        if self.language.lower() not in SUPPORTED_LANGUAGES:
            errors.append(f"Language '{self.language}' not in supported list")

        # License validation (just check not empty)
        if self.license.lower() in ("unknown", "none", "", "null"):
            errors.append("License should be specified if available")

        # Output validation
        if len(self.output.strip()) < 1:
            errors.append("Output cannot be empty")

        # Metadata validation
        if not isinstance(self.metadata, dict):
            errors.append("Metadata must be a dictionary")

        # Tests validation
        if self.tests:
            if not isinstance(self.tests, list):
                errors.append("Tests must be a list")
            for i, test in enumerate(self.tests):
                if not isinstance(test, dict):
                    errors.append(f"Test {i} must be a dictionary")

        return len(errors) == 0, errors


# Supported programming languages
SUPPORTED_LANGUAGES = {
    "python",
    "c",
    "cpp",
    "csharp",
    "java",
    "kotlin",
    "scala",
    "groovy",
    "javascript",
    "typescript",
    "html",
    "css",
    "go",
    "rust",
    "zig",
    "swift",
    "objective-c",
    "php",
    "ruby",
    "perl",
    "lua",
    "haskell",
    "ocaml",
    "elixir",
    "erlang",
    "clojure",
    "fsharp",
    "r",
    "julia",
    "matlab",
    "sql",
    "bash",
    "powershell",
    "dart",
    "assembly",
    "fortran",
    "cobol",
}


def create_sample(
    dataset: str,
    id: str,
    instruction: str,
    output: str,
    language: str = "unknown",
    license: str = "unknown",
    input: str = "",
    tests: Optional[List[Dict[str, Any]]] = None,
    difficulty: str = DifficultyLevel.UNKNOWN.value,
    metadata: Optional[Dict[str, Any]] = None,
) -> UnifiedSample:
    """
    Factory function to create a unified sample with defaults.
    
    This makes it easier for adapters to create samples without worrying
    about field order or missing optional fields.
    """
    return UnifiedSample(
        id=id,
        dataset=dataset,
        language=language.lower().strip(),
        license=license.lower().strip(),
        instruction=instruction.strip(),
        input=input.strip() if input else "",
        output=output.strip(),
        tests=tests or [],
        difficulty=difficulty.lower().strip(),
        metadata=metadata or {},
    )
