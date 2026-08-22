"""
pipeline.py
Main pipeline for dataset preparation.
Stages:
Download
↓
Preprocess
↓
Merge
↓
Deduplicate
↓
Statistics
↓
Export
"""

import rejection_stats
from deduplicate import deduplicate
from config import DATASETS
from dataset_stats import StatisticsCollector
from export_jsonl import JsonlExporter
from utils.checkpoint import checkpoint_manager
from utils.logger import info

def _resume_artifacts():
    for dataset in DATASETS:
        checkpoint = checkpoint_manager.load(dataset["id"])
        if not checkpoint:
            continue
        if checkpoint.get("completed", False):
            continue
        if int(checkpoint.get("processed", 0) or 0) <= 0:
            continue
        return checkpoint.get("artifacts", {})
    return None


def run_pipeline():
    stats = StatisticsCollector()
    append_output = checkpoint_manager.has_incomplete_resume()
    exporter = JsonlExporter(
        append=append_output,
        resume_artifacts=_resume_artifacts(),
    )
    iterator = None
    interrupted = False

    if append_output:
        info("Resume checkpoint detected. Appending to existing output files.")

    try:
        iterator = deduplicate()
        for sample in iterator:
            stats.update(sample)
            exporter.write(sample)

    except KeyboardInterrupt:
        interrupted = True
        info("Interrupted by user. Saving checkpoint and shutting down.")
        checkpoint_manager.force_save_active("shutdown")
        if iterator is not None:
            iterator.close()

    except BaseException:
        checkpoint_manager.force_save_active("exception")
        if iterator is not None:
            iterator.close()
        raise

    finally:
        exporter.close()

    if interrupted:
        info("Pipeline interrupted gracefully.")
        return

    stats.report()
    rejection_stats.report()
    exporter.report()

    print()
    print("=" * 50)
    print("PIPELINE COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    run_pipeline()
