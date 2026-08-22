"""
download.py
Production dataset downloader.
Features
--------
- Streaming and non-streaming dataset support
- Automatic retries
- Schema inspection
- Dataset validation
- Generator-based interface
- No global state
"""

from __future__ import annotations
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Tuple
from urllib.parse import quote
from datasets import Dataset, IterableDataset, load_dataset
from huggingface_hub import HfApi
from config import DATASETS
from utils.checkpoint import checkpoint_manager
from utils.logger import info, warning, error

HFDataset = Dataset | IterableDataset

SCRIPT_ERROR = "Dataset scripts are no longer supported"
DOWNLOAD_RETRY_ATTEMPTS = 3
DOWNLOAD_RETRY_DELAY = 5
STREAM_RETRY_ATTEMPTS = 3
STREAM_RETRY_DELAY = 5
_RETRYABLE_MESSAGE_PARTS = (
    "connection",
    "connect",
    "connection reset",
    "connection aborted",
    "connection refused",
    "timed out",
    "timeout",
    "temporarily unavailable",
    "temporary failure",
    "network",
    "remote end closed",
    "incomplete read",
    "chunkedencodingerror",
    "ssl",
    "502",
    "503",
    "504",
)

# Maps a file extension to the `datasets` builder name that can read it.
# Order matters: this is also the preference order when a repo ships
# more than one raw format (e.g. both .arrow and .json backups).
_BUILDER_BY_EXT = {
    ".parquet": "parquet",
    ".arrow": "arrow",
    ".jsonl": "json",
    ".json": "json",
    ".csv": "csv",
}

def is_retryable_exception(exc: BaseException) -> bool:
    """
    Best-effort classification for transient Hub/network failures.
    """
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return True

    message = str(exc).lower()
    return any(part in message for part in _RETRYABLE_MESSAGE_PARTS)


# Retry
def retry(
    operation,
    attempts: int = DOWNLOAD_RETRY_ATTEMPTS,
    delay: int = DOWNLOAD_RETRY_DELAY,
    on_exhausted=None,
):
    """
    Retry a callable several times before raising.
    """
    last_exception = None
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except RuntimeError as exc:
            # Not a transient/network failure -- retrying identical calls
            # will just fail 3 more times for no benefit. Fail fast so
            # load_single() can switch strategy immediately.
            if SCRIPT_ERROR in str(exc):
                raise
            last_exception = exc
            warning(
                f"Attempt {attempt}/{attempts} failed: {exc}"
            )
            if attempt != attempts:
                time.sleep(delay)
        except Exception as exc:
            last_exception = exc
            warning(
                f"Attempt {attempt}/{attempts} failed: {exc}"
            )
            if attempt != attempts:
                time.sleep(delay)

    if on_exhausted is not None and last_exception is not None:
        on_exhausted(last_exception)

    raise last_exception

# Script-less fallback loader
def _hf_data_files(repo_id: str, revision: str | None = None) -> Dict[str, List[str]]:
    """
    List a dataset repo's actual data files on the Hub, grouped by the
    `datasets` builder that can read them. Loading-script .py files (and
    anything else not in _BUILDER_BY_EXT) are ignored.
    """
    api = HfApi()
    files = api.list_repo_files(repo_id, repo_type="dataset", revision=revision)

    grouped: Dict[str, List[str]] = {}
    for filename in files:
        builder = _BUILDER_BY_EXT.get(Path(filename).suffix.lower())
        if builder:
            grouped.setdefault(builder, []).append(filename)

    return grouped


def load_without_script(dataset_cfg: Dict[str, Any]) -> HFDataset:
    """
    Fallback for repos whose loading script `datasets` now refuses to run
    (RuntimeError: "Dataset scripts are no longer supported"). Instead of
    executing the repo's .py script, this reads the underlying data files
    (parquet/arrow/json/csv) directly -- either files committed alongside
    the script on the main branch, or the ones the Hub's own dataset
    viewer auto-generated on the `refs/convert/parquet` branch.

    Not every scripted dataset has raw data files either place; if none
    are found, this raises and the dataset stays skipped, same as before.
    """
    repo_id = dataset_cfg["hf_name"]
    split = dataset_cfg["split"]

    revision = None
    grouped = _hf_data_files(repo_id)
    if not grouped:
        # Some repos only publish the converted files on the
        # dataset-viewer's auto-generated branch rather than main.
        revision = "refs/convert/parquet"
        grouped = _hf_data_files(repo_id, revision=revision)

    if not grouped:
        raise RuntimeError(
            f"{repo_id} only ships a loading script -- no parquet/arrow/"
            f"json/csv data files found on main or refs/convert/parquet "
            f"to fall back to."
        )

    for builder in ("parquet", "arrow", "json", "csv"):
        candidates = grouped.get(builder)
        if not candidates:
            continue

        # Prefer files whose path mentions the requested split
        # (e.g. "train/0000.parquet"); fall back to all of them if the
        # repo doesn't lay files out that way.
        split_files = [f for f in candidates if split in f.lower()]
        data_files = split_files or candidates

        ref = revision or "main"
        base = f"https://huggingface.co/datasets/{repo_id}/resolve/{ref}/"
        urls = [base + quote(f) for f in data_files]

        info(
            f"{dataset_cfg['id']}: loading {len(urls)} raw {builder} "
            f"file(s) directly (bypassing the loading script)"
            + (f" [revision={revision}]" if revision else "")
        )

        return load_dataset(
            builder,
            data_files={split: urls},
            split=split,
            streaming=dataset_cfg["streaming"],
        )

    raise RuntimeError(
        f"{repo_id}: found data files but none in a supported format "
        f"({', '.join(grouped)})."
    )

# Dataset Loader
def load_single(dataset_cfg: Dict[str, Any]) -> HFDataset:
    """
    Load one Hugging Face dataset.
    """
    kwargs = {
        "path": dataset_cfg["hf_name"],
        "split": dataset_cfg["split"],
        "streaming": dataset_cfg["streaming"]
    }

    config_name = dataset_cfg.get("config")
    if config_name:
        kwargs["name"] = config_name
    info(
        f"Loading dataset: {dataset_cfg['id']}"
    )

    try:
        dataset = retry(
            lambda: load_dataset(**kwargs),
            on_exhausted=lambda exc: checkpoint_manager.force_save_active(
                "exception"
            ),
        )
    except RuntimeError as exc:
        if SCRIPT_ERROR not in str(exc):
            raise
        warning(
            f"{dataset_cfg['id']}: repo still ships a legacy loading "
            f"script ({exc}); falling back to its raw data files"
        )
        dataset = retry(
            lambda: load_without_script(dataset_cfg),
            on_exhausted=lambda exc: checkpoint_manager.force_save_active(
                "exception"
            ),
        )

    info(
        f"Loaded dataset: {dataset_cfg['id']}"
    )
    return dataset

# Dataset Validation
def validate_dataset(dataset: HFDataset):
    if dataset is None:
        raise RuntimeError(
            "Dataset is None."
        )
    return True

# Schema Inspection
def inspect_schema(
    dataset: HFDataset,
    samples: int = 3
) -> Dict[str, str]:
    """
    Inspect dataset schema.

    Returns
    -------
    Dict[field_name, python_type]
    """
    iterator = iter(dataset)
    discovered = {}
    for _ in range(samples):
        try:
            sample = next(iterator)
        except StopIteration:
            break

        for key, value in sample.items():
            discovered[key] = type(value).__name__

    info("Detected schema:")
    for key in sorted(discovered):
        info(
            f"  {key:<25} {discovered[key]}"
        )

    return discovered

# Download Iterator

def download_all() -> Iterator[
    Tuple[
        Dict[str, Any],
        HFDataset
    ]
]:
    """
    Yields

        (dataset_config, dataset)

    instead of using global variables.
    """
    for dataset_cfg in DATASETS:
        try:
            dataset = load_single(
                dataset_cfg
            )
            validate_dataset(
                dataset
            )
            inspect_schema(
                dataset
            )
            yield (
                dataset_cfg,
                dataset
            )

        except Exception as exc:
            error(
                f"Failed loading "
                f"{dataset_cfg['id']}: {exc}"
            )
            checkpoint_manager.force_save_active("exception")
            raise

# Build loaded dictionary
loaded = {}

# Utility
def dataset_summary():
    print()
    print("=" * 50)
    print("Configured Datasets")
    print("=" * 50)

    for dataset in DATASETS:
        print()
        print(
            f"ID        : {dataset['id']}"
        )
        print(
            f"Dataset   : {dataset['hf_name']}"
        )
        print(
            f"Split     : {dataset['split']}"
        )
        print(
            f"Streaming : "
            f"{dataset['streaming']}"
        )
        print(
            f"Adapter   : "
            f"{dataset['adapter']}"
        )
    print()

# Main
if __name__ == "__main__":

    dataset_summary()
    for config, dataset in download_all():
        print()
        print(
            f"Ready -> {config['id']}"
        )
