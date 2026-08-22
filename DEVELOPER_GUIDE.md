# Developer Guide

This guide helps contributors understand, run, and extend the Dataset Preparation Pipeline. It documents repository layout, development workflows, how to add new dataset adapters, testing, configuration, and operational notes.

## Quick orientation

- Primary language: Python (3.11+).
- Main entry points: `pipeline.py`, `preprocess.py`.
- Important modules: `config.py` (configuration loader), `schemas.py` (unified sample schema), `adapters/` (dataset adapters), `utils/` (helpers: checkpointing, logging, tokenization, etc.).

## Repository layout (top-level)

```
Dataset-Pipeline/                  # repository root
├── Dataset Loading Pipeline/      # main pipeline package
│   ├── adapters/                  # adapters that convert raw datasets into unified schema
│   │   ├── base.py                # BaseAdapter class and adapter contract
│   │   ├── apps.py                # APPS adapter (example)
│   │   ├── mbpp.py                # MBPP adapter
│   │   └── ...
│   ├── exporters/                 # exporters for JSONL/Parquet/HF
│   ├── utils/                     # utility helpers (checkpoint, logger, tokenizer, etc.)
│   ├── config.py                  # configuration loader and defaults
│   ├── schemas.py                 # UnifiedSample dataclass and validation
│   ├── pipeline.py                # orchestrates full pipeline run
│   ├── preprocess.py              # adapter-driven streaming preprocessing
│   ├── download.py                # dataset download & HF loader wrappers
│   ├── deduplicate.py             # MinHash-based deduplication logic
│   ├── validate.py                # legacy validation utilities
│   ├── requirements.txt           # runtime dependencies
│   └── tests/                     # (placeholder) unit/integration tests
├── README.md
├── DEVELOPER_GUIDE.md             # <-- this file
├── LICENSE
└── .gitignore
```

Notes: the repository stores the main code under the folder named `Dataset Loading Pipeline`. Importers use module-style imports (e.g., `from config import get_config`).

## How to run locally (developer flow)

1. Clone the repository

```bash
git clone https://github.com/KodeDevelopers-Web/Dataset-Pipeline.git
cd Dataset-Pipeline
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate     # Windows (PowerShell/CMD variations)
pip install -r "Dataset Loading Pipeline/requirements.txt"
```

2. Quick smoke run (small, safe)

```bash
# Run the preprocessing iterator and print a few samples
python "Dataset Loading Pipeline/preprocess.py"

# Run the full pipeline (will download configured datasets)
python "Dataset Loading Pipeline/pipeline.py"
```

3. Common environment variables (example)

```bash
PIPELINE_CACHE_DIR=/path/to/cache
PIPELINE_OUTPUT_DIR=/path/to/output
PIPELINE_WORKERS=4
PIPELINE_LOG_LEVEL=DEBUG
```

## Configuration

- The canonical configuration loader is `Dataset Loading Pipeline/config.py`.
- Defaults are in `DEFAULT_CONFIG` and `DEFAULT_DATASETS` inside that file.
- `get_config()` merges defaults, an optional `config.yaml` at the repo root, and environment variables (highest priority).
- Use `config.save_config()` to write a YAML file from a Python dict (requires PyYAML).

Key fields you'll likely adjust:
- `cache_dir`, `output_dir`, `log_dir` — paths used by the pipeline
- `workers`, `batch_size`, `chunk_size` — performance tuning
- `export_formats` — `jsonl`, `parquet`, etc.
- `enabled_datasets` / `disabled_datasets` — control which adapters run

## Unified Schema (schemas.py)

- All adapters should emit `UnifiedSample` dataclass objects (use `create_sample()` helper in `schemas.py`).
- Required fields: `id`, `dataset`, `language`, `license`, `instruction`, `output`.
- Use `UnifiedSample.validate()` to run local checks before yielding a sample.

## Adapters: adding a new dataset

1. Create a new adapter module in `Dataset Loading Pipeline/adapters/` (e.g., `mydataset.py`).
2. Implement either:
   - A class inheriting from `BaseAdapter` and implement `preprocess()` (preferred), or
   - A module-level `process(hf_dataset)` generator that yields dicts compatible with the unified schema (existing adapters follow both patterns; `preprocess.py` expects `adapters.{adapter}` to provide a `process()` generator).

Minimum example (preferred BaseAdapter):

```python
# Dataset Loading Pipeline/adapters/mydataset.py
from adapters.base import BaseAdapter
from schemas import create_sample

class MyDatasetAdapter(BaseAdapter):
    def __init__(self):
        super().__init__(name="mydataset", hf_name="owner/mydataset", description="My dataset")

    def preprocess(self, raw_sample: dict):
        # Map raw fields to unified schema
        return create_sample(
            dataset=self.name,
            id=str(raw_sample.get("id", "")),
            instruction=raw_sample.get("prompt", "").strip(),
            output=raw_sample.get("completion", "").strip(),
            language=raw_sample.get("language", "python"),
            license=raw_sample.get("license", "unknown"),
        )

adapter = MyDatasetAdapter()

def process(hf_dataset):
    # The pipeline imports adapters as modules and expects a module-level
    # `process()` generator in the current codebase, so provide this wrapper.
    for raw in hf_dataset:
        sample = adapter.preprocess(raw)
        if sample:
            yield sample
```

3. Add adapter to `DEFAULT_DATASETS` in `Dataset Loading Pipeline/config.py` or control inclusion via `config.yaml` or environment variables.

4. Test locally: run `preprocess.py` and verify samples are produced and validated.

## Checkpointing & resume

- Checkpointing is implemented under `utils/checkpoint.py` and used by `preprocess.py`.
- When an adapter has produced samples up to position N, a checkpoint is written so interrupted runs resume where they left off.
- On adapter errors the pipeline attempts configurable retry logic controlled by `download_retry` and `stream_retry` settings in `config.py`.

## Deduplication

- The deduplication logic is in `deduplicate.py` (MinHash-based).
- Global toggles and hyperparameters are in `config.py`: `USE_MINHASH`, `MINHASH_PERMUTATIONS`, `SIMILARITY_THRESHOLD`.

## Logging

- The project uses `utils/logger.py`. Configure log level with `log_level` setting in `get_config()` or `PIPELINE_LOG_LEVEL` env var.
- Logs are written to `log_dir` by default (created at startup).

## Tests & CI

- There is a `tests/` dir under `Dataset Loading Pipeline` with placeholders. Add unit tests for adapters and core modules.
- Suggested test targets:
  - Adapter `preprocess()` outputs match `UnifiedSample` shape
  - `schemas.UnifiedSample.validate()` rejects malformed samples
  - Checkpointing behavior for resume
  - Deduplication reproducibility for sample inputs

## Development workflow

- Branch per feature/adapter. Follow semantic commit messages.
- Run linters and type-checkers (project uses type hints for Python 3.11+). Add `pyproject.toml` / `pre-commit` in future to standardize checks.

## Troubleshooting

- If downloads fail, increase retry attempts or run the adapter manually with a small subset.
- If memory spikes, lower `batch_size` and `workers`.
- If language detection is wrong, inspect `utils/language_detector.py` and add dataset-specific overrides in your adapter.

## Contributing

- Follow the adapter template above.
- Add tests for new logic to `Dataset Loading Pipeline/tests/`.
- Update `DEFAULT_DATASETS` when adding a widely-used dataset or provide instructions to enable it through `config.yaml`.

## Contacts

For repository-level questions contact the maintainers via the GitHub repo issues.

---

End of developer guide.
