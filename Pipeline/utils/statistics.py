"""
Dataset Statistics Collection and Reporting

Automatically collects and reports comprehensive statistics about datasets
including language distribution, token counts, metadata, etc.
"""

from typing import Dict, Any, List
from collections import Counter, defaultdict
import json
from pathlib import Path
from datetime import datetime
from utils.tokenizer import sample_tokens


class StatisticsCollector:
    """Collects comprehensive statistics about processed samples."""
    
    def __init__(self):
        self.total_samples = 0
        self.samples_per_dataset = Counter()
        self.language_distribution = Counter()
        self.license_distribution = Counter()
        self.difficulty_distribution = Counter()
        self.token_counts = []
        self.instruction_lengths = []
        self.output_lengths = []
        self.input_lengths = []
        self.empty_fields = Counter()
        self.has_tests = 0
        self.validation_failures = 0
        self.duplicate_percentage = 0.0
        self.skipped_samples = 0
        
        # Per-dataset tracking
        self.dataset_stats = defaultdict(lambda: {
            "count": 0,
            "avg_tokens": 0,
            "languages": Counter(),
            "licenses": Counter(),
        })
    
    def update(self, sample: Dict[str, Any]):
        """
        Update statistics with a new sample.
        
        Args:
            sample: Preprocessed sample
        """
        self.total_samples += 1
        
        # Dataset tracking
        dataset = sample.get("dataset", "unknown")
        self.samples_per_dataset[dataset] += 1
        self.dataset_stats[dataset]["count"] += 1
        
        # Language tracking
        language = sample.get("language", "unknown")
        self.language_distribution[language] += 1
        self.dataset_stats[dataset]["languages"][language] += 1
        
        # License tracking
        license_name = sample.get("license", "unknown")
        self.license_distribution[license_name] += 1
        self.dataset_stats[dataset]["licenses"][license_name] += 1
        
        # Difficulty tracking
        difficulty = sample.get("difficulty", "unknown")
        self.difficulty_distribution[difficulty] += 1
        
        # Token counts
        try:
            tokens = sample_tokens(sample)
            self.token_counts.append(tokens)
        except:
            pass
        
        # Field lengths
        instruction = sample.get("instruction", "")
        input_text = sample.get("input", "")
        output = sample.get("output", "")
        
        self.instruction_lengths.append(len(instruction))
        self.output_lengths.append(len(output))
        self.input_lengths.append(len(input_text))
        
        # Empty fields
        if not instruction.strip():
            self.empty_fields["instruction"] += 1
        if not output.strip():
            self.empty_fields["output"] += 1
        
        # Test tracking
        if sample.get("tests"):
            self.has_tests += 1
    
    def set_duplicate_stats(self, total: int, unique: int):
        """
        Set deduplication statistics.
        
        Args:
            total: Total samples before dedup
            unique: Unique samples after dedup
        """
        if total > 0:
            self.duplicate_percentage = 100 * (total - unique) / total
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        def safe_avg(values):
            return sum(values) / len(values) if values else 0
        
        return {
            "total_samples": self.total_samples,
            "samples_per_dataset": dict(self.samples_per_dataset),
            "language_distribution": dict(self.language_distribution),
            "license_distribution": dict(self.license_distribution),
            "difficulty_distribution": dict(self.difficulty_distribution),
            "average_tokens": safe_avg(self.token_counts),
            "min_tokens": min(self.token_counts) if self.token_counts else 0,
            "max_tokens": max(self.token_counts) if self.token_counts else 0,
            "average_instruction_length": safe_avg(self.instruction_lengths),
            "average_output_length": safe_avg(self.output_lengths),
            "average_input_length": safe_avg(self.input_lengths),
            "samples_with_tests": self.has_tests,
            "duplicate_percentage": self.duplicate_percentage,
            "empty_fields": dict(self.empty_fields),
        }
    
    def report(self, output_file: Path = None):
        """
        Generate and save a statistics report.
        
        Args:
            output_file: Path to save report (optional)
        """
        summary = self.get_summary()
        
        print("\n" + "=" * 70)
        print("DATASET STATISTICS REPORT")
        print("=" * 70)
        print(f"Total Samples: {summary['total_samples']:,}")
        print(f"\nSamples per Dataset:")
        for dataset, count in sorted(summary['samples_per_dataset'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {dataset}: {count:,}")
        
        print(f"\nLanguage Distribution (top 10):")
        lang_sorted = sorted(summary['language_distribution'].items(), key=lambda x: x[1], reverse=True)
        for language, count in lang_sorted[:10]:
            percent = 100 * count / summary['total_samples']
            print(f"  {language}: {count:,} ({percent:.1f}%)")
        
        print(f"\nLicense Distribution:")
        for license_name, count in sorted(summary['license_distribution'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {license_name}: {count:,}")
        
        print(f"\nToken Statistics:")
        print(f"  Average: {summary['average_tokens']:.0f}")
        print(f"  Min: {summary['min_tokens']}")
        print(f"  Max: {summary['max_tokens']}")
        
        print(f"\nContent Length Statistics:")
        print(f"  Avg Instruction: {summary['average_instruction_length']:.0f} chars")
        print(f"  Avg Input: {summary['average_input_length']:.0f} chars")
        print(f"  Avg Output: {summary['average_output_length']:.0f} chars")
        
        print(f"\nQuality Metrics:")
        print(f"  Samples with Tests: {summary['samples_with_tests']:,}")
        print(f"  Duplicate Percentage: {summary['duplicate_percentage']:.2f}%")
        
        print("=" * 70 + "\n")
        
        # Save to JSON if requested
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                json.dump(summary, f, indent=2, default=str)
            print(f"Statistics saved to {output_file}")
    
    def report_markdown(self, output_file: Path = None) -> str:
        """
        Generate a markdown report.
        
        Args:
            output_file: Path to save report (optional)
            
        Returns:
            Markdown formatted report
        """
        summary = self.get_summary()
        
        report = f"""# Dataset Statistics Report

Generated: {datetime.now().isoformat()}

## Summary

- **Total Samples**: {summary['total_samples']:,}
- **Duplicate Percentage**: {summary['duplicate_percentage']:.2f}%
- **Average Tokens**: {summary['average_tokens']:.0f}

## Samples per Dataset

| Dataset | Count | Percentage |
|---------|-------|-----------|
"""
        
        total = summary['total_samples']
        for dataset, count in sorted(summary['samples_per_dataset'].items(), key=lambda x: x[1], reverse=True):
            percent = 100 * count / total if total else 0
            report += f"| {dataset} | {count:,} | {percent:.1f}% |\n"
        
        report += "\n## Language Distribution\n\n| Language | Count | Percentage |\n|----------|-------|----------|\n"
        for language, count in sorted(summary['language_distribution'].items(), key=lambda x: x[1], reverse=True):
            percent = 100 * count / total if total else 0
            report += f"| {language} | {count:,} | {percent:.1f}% |\n"
        
        report += f"""
## Token Statistics

- Min: {summary['min_tokens']}
- Max: {summary['max_tokens']}
- Average: {summary['average_tokens']:.0f}

## Content Length

- Avg Instruction: {summary['average_instruction_length']:.0f} chars
- Avg Input: {summary['average_input_length']:.0f} chars
- Avg Output: {summary['average_output_length']:.0f} chars

## Quality Metrics

- Samples with Tests: {summary['samples_with_tests']:,}
- Empty Instructions: {summary['empty_fields'].get('instruction', 0):,}
- Empty Outputs: {summary['empty_fields'].get('output', 0):,}
"""
        
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                f.write(report)
            print(f"Markdown report saved to {output_file}")
        
        return report
