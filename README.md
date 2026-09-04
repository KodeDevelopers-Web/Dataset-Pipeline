# Dataset Preparation Pipeline

A production-ready, modular pipeline for preparing high-quality training datasets for frontier-level coding AI models.

**Current Version**: 2.0 (Production-Ready)

## Features

✅ **6 Dataset Adapters** - Automated download and preprocessing  
✅ **Unified Schema** - Consistent format across all datasets  
✅ **Automatic Language Detection** - 35+ programming languages supported  
✅ **Smart Deduplication** - MinHash-based duplicate removal  
✅ **Streaming Processing** - Memory-efficient handling of millions of samples  
✅ **Comprehensive Validation** - Detailed error reporting  
✅ **Rich Statistics** - Language distribution, token counts, quality metrics  
✅ **Checkpointing** - Resume interrupted processing seamlessly  
✅ **Multiple Export Formats** - JSONL, Parquet, HuggingFace Datasets  
✅ **YAML Configuration** - Flexible, environment-aware settings  
✅ **Production Logging** - Detailed logs with debug support  
✅ **Type Hints** - Full Python 3.11+ type annotations  
✅ **Comprehensive Documentation** - Developer guide included  

## Quick Start

### Installation

```bash
git clone https://github.com/KodeDevelopers-Web/Dataset-Pipeline.git
cd Dataset-Pipeline
python -m venv .venv
# Activate the virtualenv (see platform-specific instructions below)
# Install runtime dependencies from the packaged requirements file
pip install -r "Dataset Loading Pipeline/requirements.txt"
```

Note: the project's Python code lives inside the "Dataset Loading Pipeline" directory. You can either run commands by specifying that path (e.g. `python "Dataset Loading Pipeline/pipeline.py"`) or change directory into it before running pipeline commands:

```bash
cd "Dataset Loading Pipeline"
```

### Run Full Pipeline

From the `Dataset Loading Pipeline` directory:

```bash
python pipeline.py
```

This will automatically:
1. Download enabled datasets
2. Preprocess and normalize samples
3. Clean and validate data
4. Remove duplicates
5. Generate statistics
6. Export in configured formats

## Supported Datasets

### Core Code Problems (9)

- **MBPP** - 427 basic Python problems
- **APPS** - 10k competitive programming problems
- **HumanEval** - 164 code generation benchmarks
- **CodeAlpaca** - 20k instruction-tuned examples
- **EvolCode** - 80k evolved code examples
- **TACO** - Large-scale test-aimed code dataset
- **LiveCodeBench** - Real-world coding benchmarks
- **CodeContests** - Competitive programming from judges
- **The Stack v2** - 500M+ code samples (600+ languages)

### Instruction-Following (2)

- **OpenCoder** - Instruction-tuned code examples
- **WizardCoder** - Evolved instruction following dataset

### Debugging & SWE (1)

- **SWE-bench** - Real GitHub issues and solutions

### Repository Understanding (2)

- **RepoBench** - Repository-level code understanding
- **CrossCodeEval** - Cross-repository code evaluation

### Code Modification (2)

- **CommitPackFT** - Code change patterns from commits
- **GitHub Issues** - Issue resolution patterns

### Documentation (8)

Adapters for processing documentation datasets:
- Python, JavaScript, TypeScript, React
- Node.js, FastAPI, Django
- Docker, Kubernetes

*(Placeholder adapters ready for implementation)*

## Architecture

### Core Components

```
Input Datasets
    ↓
Adapters (convert to unified schema)
    ↓
Preprocessing (clean & normalize)
    ↓
Filtering (language, license, quality)
    ↓
Deduplication (MinHash-based)
    ↓
Validation (schema & content checks)
    ↓
Statistics (language dist., token counts, etc.)
    ↓
Export (JSONL, Parquet, HuggingFace)
```

### Unified Schema

Every dataset is converted to:

```json
{
    "id": "unique_id",
    "dataset": "source_dataset",
    "language": "python",
    "license": "mit",
    "instruction": "Task description",
    "input": "Function signature or context",
    "output": "Solution or expected output",
    "tests": [{"input": "...", "expected": "..."}],
    "difficulty": "medium",
    "metadata": {}
}
```

## Configuration

### Environment Variables

```bash
PIPELINE_CACHE_DIR=/path/to/cache
PIPELINE_OUTPUT_DIR=/path/to/output
PIPELINE_WORKERS=4
PIPELINE_LOG_LEVEL=DEBUG
```

### config.yaml

```yaml
# Paths
cache_dir: ./cache
output_dir: ./output

# Processing
workers: 1
batch_size: 32

# Export formats
export_formats:
  - jsonl
  - parquet

# Enabled datasets (empty = all)
enabled_datasets: []
disabled_datasets: []

# Logging
log_level: INFO
```

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for complete configuration options.

## Usage

### Command Line

```bash
# Run full pipeline with default config (from project root):
python "Dataset Loading Pipeline/pipeline.py"

# Process specific datasets (preprocessing only):
python "Dataset Loading Pipeline/preprocess.py"

# View configuration
python -c "from config import print_config; print_config()" 
# (run this from within Dataset Loading Pipeline directory or set PYTHONPATH appropriately)
```

### Programmatic Usage

```python
from pipeline import run_pipeline
from config import get_config, get_datasets_config
from adapters.humaneval import HumanEvalAdapter

# Run full pipeline
run_pipeline()

# Or process specific dataset
adapter = HumanEvalAdapter()
for sample in adapter.stream():
    print(sample)
```

## Supported Languages

The pipeline automatically detects these 35+ languages:

Python, C, C++, C#, Java, Kotlin, Scala, Groovy  
JavaScript, TypeScript, HTML, CSS  
Go, Rust, Zig, Swift, Objective-C  
PHP, Ruby, Perl, Lua  
Haskell, OCaml, Elixir, Erlang, Clojure, F#  
R, Julia, MATLAB, SQL  
Bash, PowerShell  
Dart, Assembly, Fortran, COBOL

## Export Formats

### JSONL (Default)

```bash
# Streaming-friendly, one JSON per line
{"id": "1", "dataset": "humaneval", ...}
{"id": "2", "dataset": "humaneval", ...}
```

### Parquet

```python
# Columnar, highly compressible, efficient querying
from datasets import load_dataset
dataset = load_dataset("parquet", data_files="output.parquet")
```

### HuggingFace Datasets

```python
# Native HF format, cacheable, versioned
from datasets import load_from_disk
dataset = load_from_disk("output_dir")
```

## Performance

Processing Statistics (on typical hardware):

- **Download**: 100-500 samples/sec (network limited)
- **Preprocessing**: 1000-5000 samples/sec
- **Deduplication**: 5000-10000 samples/sec
- **Validation**: 10000-50000 samples/sec

Memory usage: <2GB for processing (streaming-based)

## Quality Metrics

The pipeline generates comprehensive statistics:

```
Total Samples: 1,234,567
  - HumanEval: 164
  - APPS: 10,200
  - MBPP: 427
  - ...

Languages:
  - Python: 45.2%
  - JavaScript: 15.3%
  - Java: 12.1%
  - ...

Licenses:
  - MIT: 40.1%
  - Apache-2.0: 25.3%
  - Unknown: 34.6%

Token Statistics:
  - Average: 256 tokens
  - Min: 10 tokens
  - Max: 4096 tokens

Quality:
  - With Tests: 45,230 (3.6%)
  - Duplicates Removed: 123,456 (9.8%)
```

## Project Structure

```
.
├── adapters/              # Dataset adapters
│   ├── base.py           # BaseAdapter class
│   ├── humaneval.py      # HumanEval adapter
│   ├── mbpp.py           # MBPP adapter
│   └── ...
├── exporters/            # Export format implementations
│   └── base.py           # Exporter classes
├── utils/                # Utility modules
│   ├── language_detector.py    # Language detection
│   ├── validator.py            # Validation logic
│   ├── statistics.py           # Statistics collection
│   ├── cleaner.py             # Data cleaning
│   ├── tokenizer.py           # Token counting
│   ├── checkpoint.py          # Checkpointing
│   └── logger.py              # Logging
├── schemas.py            # Unified schema definition
├── config.py             # Configuration system
├── pipeline.py           # Main pipeline orchestration
├── preprocess.py         # Preprocessing pipeline
├── merge.py              # Merging and filtering
├── deduplicate.py        # Deduplication logic
├── validate.py           # Validation (legacy)
├── requirements.txt      # Python dependencies
├── DEVELOPER_GUIDE.md    # Architecture and development guide
└── README.md             # This file
```

## Adding New Datasets

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for detailed instructions on:
- Creating a new adapter
- Registering in configuration
- Testing the adapter
- Handling dataset-specific requirements

## Troubleshooting

### Dataset Download Fails

```bash
# Increase retry attempts
PIPELINE_DOWNLOAD_RETRY_ATTEMPTS=5 python "Dataset Loading Pipeline/pipeline.py"
```

### Out of Memory

```bash
# Reduce batch size and workers
PIPELINE_BATCH_SIZE=8 PIPELINE_WORKERS=1 python "Dataset Loading Pipeline/pipeline.py"
```

### Language Detection Not Working

```python
from utils.language_detector import detect_language
lang = detect_language(your_code_sample)
```

## Roadmap

- [ ] Streaming dataset support for Stack v2
- [ ] AST-based deduplication for code
- [ ] Parallel dataset processing
- [ ] Web UI for monitoring
- [ ] Integration with Hugging Face Hub
- [ ] Automated quality scoring
- [ ] Custom transformer pipelines
- [ ] Unit tests and CI

## Requirements

- Python 3.11+
- ~2GB RAM (streaming-based, memory efficient)
- Internet connection for downloading datasets
- Optional: GPU for future enhancement

## License

MIT - See LICENSE file

## Contributing

Contributions welcome! Areas needing help:

1. Adding new dataset adapters
2. Improving language detection
3. Performance optimization
4. Documentation
5. Testing

## Acknowledgments

Built for **ChatKode** - An AI coding and software engineering assistant.

Data sources: HuggingFace Hub, GitHub, DeepMind, OpenAI, Princeton NLP, BAAI, and more.

---

**For development information, see [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)**

---

# Installation (detailed)

Create a virtual environment.

```bash
python -m venv .venv
```

Activate it.

Windows

```bash
.venv\Scripts\activate
```

Linux/macOS

```bash
source .venv/bin/activate
```

Install dependencies.

```bash
pip install -r "Dataset Loading Pipeline/requirements.txt"
```

---

# Configure Datasets

Edit `config.py` inside the `Dataset Loading Pipeline` directory.

Example:

```python
DATASETS = [

    {
        "id": "stack",
        "hf_name": "bigcode/the-stack-v2",
        "split": "train",
        "streaming": True,
        "adapter": "stack_v2"
    },

    {
        "id": "mbpp",
        "hf_name": "google-research-datasets/mbpp",
        "split": "train",
        "streaming": False,
        "adapter": "mbpp"
    }

]
```

---

# Running the Pipeline

```bash
python "Dataset Loading Pipeline/pipeline.py"
```

Pipeline:

```
Download

↓

Adapter

↓

Cleaner

↓

Language Filter

↓

License Filter

↓

Quality Filter

↓

Validation

↓

Deduplication

↓

Statistics

↓

JSONL Export
```

---

# Output

The pipeline generates:

```
output/

├── train.jsonl
└── validation.jsonl
```

---

# Supported Export Formats

Instruction format

```json
{
  "instruction": "...",
  "input": "...",
  "output": "..."
}
```

Chat format

```json
{
  "messages": [
    {
      "role": "user",
      "content": "..."
    },
    {
      "role": "assistant",
      "content": "..."
    }
  ]
}
```

---

# Supported Datasets

Current adapters:

- The Stack V2
- MBPP
- APPS
- CodeSearchNet

Adding another dataset only requires creating a new adapter.

---

# Future Improvements

Version 3 roadmap:

- SQLite-backed deduplication
- Parallel preprocessing
- Checkpointing
- Resume interrupted runs
- Language-specific quality filters
- YAML configuration
- Multiple export backends
- HTML reports
- Unit tests

---

# License

Use only datasets whose licenses allow your intended use.

Always review the license terms of every dataset before training or distributing a model.

---

# Author

Divyanshu (Dataset Engineering & Pipeline Developer)
