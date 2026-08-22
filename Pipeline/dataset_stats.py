"""
dataset_stats.py

Collects dataset statistics during pipeline execution.

NOTE: this file used to be named statistics.py, which silently shadowed
Python's own stdlib `statistics` module (any `import statistics` deep in
a dependency, e.g. inside transformers/torch, would resolve to this file
instead) and caused a circular-import ImportError. Keep this filename.
"""

from collections import Counter
from utils.tokenizer import sample_tokens


class StatisticsCollector:
    """
    Collects statistics while samples are processed.
    """

    def __init__(self):
        self.language_counter = Counter()
        self.source_counter = Counter()

        self.total_samples = 0
        self.total_tokens = 0

        self.longest = 0
        self.shortest = float("inf")

    def update(self, sample):
        """
        Update statistics using one processed sample.
        """

        tokens = sample_tokens(sample)

        self.total_samples += 1
        self.total_tokens += tokens

        self.longest = max(self.longest, tokens)
        self.shortest = min(self.shortest, tokens)

        self.language_counter.update(
            [sample.get("language", "Unknown")]
        )

        self.source_counter.update(
            [sample.get("source", "Unknown")]
        )

    @property
    def average_tokens(self):
        if self.total_samples == 0:
            return 0.0

        return self.total_tokens / self.total_samples

    def report(self):
        """
        Print collected statistics.
        """

        shortest = (
            self.shortest
            if self.shortest != float("inf")
            else 0
        )

        print()
        print("=" * 50)
        print("DATASET STATISTICS")
        print("=" * 50)

        print(f"Samples        : {self.total_samples:,}")
        print(f"Tokens         : {self.total_tokens:,}")
        print(f"Average Tokens : {self.average_tokens:.2f}")
        print(f"Longest Sample : {self.longest}")
        print(f"Shortest Sample: {shortest}")

        print()
        print("Languages")
        print("-" * 50)

        for language, count in sorted(
            self.language_counter.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            print(f"{language:<20}{count:,}")

        print()
        print("Sources")
        print("-" * 50)

        for source, count in sorted(
            self.source_counter.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            print(f"{source:<20}{count:,}")