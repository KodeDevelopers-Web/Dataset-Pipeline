"""
preprocess.py
Converts every dataset into the unified training format.
Unified sample format
---------------------
{
    "instruction": str,
    "input": str,
    "output": str,
    "source": str,
    "language": str,
    "license": str
}
"""

from __future__ import annotations

import time
from importlib import import_module
from typing import Any, Dict, Iterator

from config import DATASETS
from download import (
    STREAM_RETRY_ATTEMPTS,
    STREAM_RETRY_DELAY,
    inspect_schema,
    is_retryable_exception,
    load_single,
    validate_dataset,
)
from utils.checkpoint import checkpoint_manager
from utils.logger import info, warning

UNKNOWN_METADATA_VALUES = {
    "",
    "unknown",
    "none",
    "null",
    "n/a",
}


class DatasetAdapter:
    def __init__(self):
        self.adapters = {}
        for dataset in DATASETS:
            module = import_module(
                f"adapters.{dataset['adapter']}"
            )
            self.adapters[dataset["id"]] = module

    def process(self) -> Iterator[Dict[str, Any]]:
        """
        Stream every configured dataset through its adapter.
        """
        for dataset_cfg in DATASETS:
            hf_name = dataset_cfg["id"]

            if checkpoint_manager.should_skip(hf_name):
                info(f"Skipping completed dataset {hf_name}")
                continue

            processed = checkpoint_manager.load_resume_position(hf_name)
            adapter = self.adapters[hf_name]

            with checkpoint_manager.track(hf_name, processed):
                yield from self._process_dataset(
                    dataset_cfg=dataset_cfg,
                    adapter=adapter,
                    processed=processed,
                )

    def _process_dataset(
        self,
        dataset_cfg: Dict[str, Any],
        adapter,
        processed: int,
    ) -> Iterator[Dict[str, Any]]:
        hf_name = dataset_cfg["id"]
        attempt = 1

        while True:
            try:
                info(f"Processing {hf_name}")
                hf_dataset = load_single(dataset_cfg)
                validate_dataset(hf_dataset)
                inspect_schema(hf_dataset)

                iterator = adapter.process(hf_dataset)
                self._skip_processed(iterator, hf_name, processed)

                for sample in iterator:
                    self._apply_dataset_metadata(sample, dataset_cfg)
                    next_processed = processed + 1
                    yield sample

                    processed = next_processed
                    checkpoint_manager.update_position(hf_name, processed)
                    checkpoint_manager.maybe_save(
                        hf_name,
                        processed,
                        reason="periodic",
                    )

                checkpoint_manager.mark_completed(hf_name, processed)
                return

            except (KeyboardInterrupt, GeneratorExit, SystemExit):
                checkpoint_manager.update_position(hf_name, processed)
                raise

            except Exception as exc:
                checkpoint_manager.update_position(hf_name, processed)
                checkpoint_manager.force_save(
                    hf_name,
                    processed,
                    reason="exception",
                )

                if (
                    attempt >= STREAM_RETRY_ATTEMPTS
                    or not is_retryable_exception(exc)
                ):
                    raise

                warning(
                    f"{hf_name}: transient failure at sample "
                    f"{processed:,}; retrying "
                    f"{attempt}/{STREAM_RETRY_ATTEMPTS} after "
                    f"{STREAM_RETRY_DELAY}s: {exc}"
                )
                attempt += 1
                time.sleep(STREAM_RETRY_DELAY)

    @staticmethod
    def _skip_processed(
        iterator: Iterator[Dict[str, Any]],
        hf_name: str,
        processed: int,
    ) -> None:
        if processed <= 0:
            return

        skipped = 0
        while skipped < processed:
            try:
                next(iterator)
            except StopIteration:
                warning(
                    f"{hf_name}: checkpoint requested sample "
                    f"{processed:,}, but dataset ended after "
                    f"{skipped:,} skipped samples"
                )
                return
            skipped += 1

    @staticmethod
    def _apply_dataset_metadata(
        sample: Dict[str, Any],
        dataset_cfg: Dict[str, Any],
    ) -> None:
        for field in ("language", "license"):
            configured_value = dataset_cfg.get(field)
            if not configured_value:
                continue

            current_value = str(sample.get(field, "")).strip().lower()
            if current_value in UNKNOWN_METADATA_VALUES:
                sample[field] = configured_value


adapter = DatasetAdapter()


def preprocess() -> Iterator[Dict[str, Any]]:
    """
    Generator yielding unified training samples.
    """
    yield from adapter.process()


if __name__ == "__main__":
    iterator = preprocess()
    for _ in range(5):
        print(next(iterator))
