"""
export_jsonl.py

Exports processed samples to JSONL.
"""

import json
import os
import random
from pathlib import Path

from config import (
    TRAIN_FILE,
    VALIDATION_FILE,
    VALIDATION_PERCENT,
    RANDOM_SEED,
)

from config import EXPORT_FORMAT
from utils.checkpoint import checkpoint_manager

def to_instruction(sample):
    return {
        "instruction": sample["instruction"],
        "input": sample["input"],
        "output": sample["output"]
    }


def to_chat(sample):
    user = sample["instruction"]

    if sample["input"]:
        user += "\n\n" + sample["input"]

    return {
        "messages": [
            {
                "role": "user",
                "content": user
            },
            {
                "role": "assistant",
                "content": sample["output"]
            }
        ]
    }


def serialize(sample):
    if EXPORT_FORMAT == "chat":
        return to_chat(sample)

    return to_instruction(sample)


class JsonlExporter:

    def __init__(self, append=False, resume_artifacts=None):
        random.seed(RANDOM_SEED)

        self.train_path = Path(TRAIN_FILE)
        self.validation_path = Path(VALIDATION_FILE)

        self.train_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if append and resume_artifacts:
            self._truncate_to_checkpoint(resume_artifacts)

        mode = "a" if append else "w"

        self.train_file = self.train_path.open(
            mode,
            encoding="utf8"
        )

        self.validation_file = self.validation_path.open(
            mode,
            encoding="utf8"
        )

        self.train_count = 0
        self.validation_count = 0
        self._remove_checkpoint_hook = checkpoint_manager.add_before_save_hook(
            self.flush
        )

    def write(self, sample):
        line = json.dumps(
            serialize(sample),
            ensure_ascii=False
        ) + "\n"

        if random.random() < VALIDATION_PERCENT:

            self.validation_file.write(line)
            self.validation_count += 1

        else:

            self.train_file.write(line)
            self.train_count += 1

    def flush(self):
        for file in (self.train_file, self.validation_file):
            if file.closed:
                continue
            file.flush()
            os.fsync(file.fileno())
        return {
            "output": {
                "train_file": str(self.train_path),
                "train_bytes": self.train_path.stat().st_size,
                "validation_file": str(self.validation_path),
                "validation_bytes": self.validation_path.stat().st_size,
            }
        }

    def _truncate_to_checkpoint(self, artifacts):
        output = artifacts.get("output", {})
        targets = (
            (self.train_path, output.get("train_file"), output.get("train_bytes")),
            (
                self.validation_path,
                output.get("validation_file"),
                output.get("validation_bytes"),
            ),
        )
        for path, expected_path, size in targets:
            if size is None:
                continue
            if expected_path and Path(expected_path) != path:
                continue
            if path.exists() and path.stat().st_size > int(size):
                with path.open("r+b") as handle:
                    handle.truncate(int(size))

    def close(self):
        try:
            self.flush()
        finally:
            self._remove_checkpoint_hook()
            self.train_file.close()
            self.validation_file.close()

    def report(self):
        print()
        print("=" * 50)
        print("EXPORT SUMMARY")
        print("=" * 50)
        print(f"Training Samples   : {self.train_count:,}")
        print(f"Validation Samples : {self.validation_count:,}")


if __name__ == "__main__":
    print(
        "JsonlExporter is intended to be used "
        "from pipeline.py"
    )
