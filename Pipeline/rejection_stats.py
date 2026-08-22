"""
rejection_stats.py

Collects rejection statistics for the pipeline.
"""

from collections import Counter


class RejectionStatistics:
    """
    Tracks every rejected sample and its reason.
    """

    def __init__(self):
        self.total = 0
        self.reasons = Counter()

    def reject(self, reason: str):
        """
        Record one rejected sample.
        """

        self.total += 1
        self.reasons[reason] += 1

    def report(self):
        """
        Print rejection statistics.
        """

        print()
        print("=" * 50)
        print("REJECTION REPORT")
        print("=" * 50)

        if self.total == 0:
            print("No rejected samples.")
            return

        for reason, count in sorted(
            self.reasons.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            percentage = (
                count / self.total
            ) * 100

            print(
                f"{reason:<30}"
                f"{count:>10,}"
                f" ({percentage:5.2f}%)"
            )

        print("-" * 50)
        print(
            f"{'Total Rejected':<30}"
            f"{self.total:>10,}"
        )


rejection_stats = RejectionStatistics()


def reject(reason: str):
    """Record one rejected sample through the shared singleton."""

    rejection_stats.reject(reason)


def report():
    """Print rejection statistics from the shared singleton."""

    rejection_stats.report()