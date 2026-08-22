"""
merge.py
Production merge pipeline.
Pipeline
HF Dataset
      ↓
Adapter
      ↓
Cleaner
      ↓
Language Filter
      ↓

Quality Filter
      ↓
Validation
      ↓
Deduplication
"""

from preprocess import preprocess
from rejection_stats import rejection_stats
from utils.cleaner import (
    clean_sample,
    is_valid
)
from language_filter import (
    filter_sample as language_filter
)
from license_filter import (
    filter_sample as license_filter
)
from quality_filter import (
    passes_quality
)
from validate import (
    validate_sample
)
from utils.logger import (
    info,
    warning
)

def merge():
    kept = 0
    removed = 0
    for sample in preprocess():
        sample = clean_sample(sample)
        if not is_valid(sample):
            removed += 1
            continue

        if not language_filter(sample):
            removed += 1
            rejection_stats.reject("Language Filter")
            continue

        if not license_filter(sample):
            removed += 1
            rejection_stats.reject("License Filter")
            continue

        if not passes_quality(sample):
            removed += 1
            rejection_stats.reject("Quality Filter")
            continue

        errors = validate_sample(sample)

        if errors:
            warning(str(errors))
            removed += 1

            for error in errors:
                rejection_stats.reject(error)
            
            continue

        kept += 1

        if kept % 10000 == 0:
            info(f"Merged {kept:,} samples")
        yield sample

    info("Merge completed")
    info(f"Accepted : {kept:,}")
    info(f"Rejected : {removed:,}")


if __name__ == "__main__":
    iterator = merge()
    for _ in range(5):
        print(next(iterator))