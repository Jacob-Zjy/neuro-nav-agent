from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = PROJECT_ROOT / "figures"
DOCS_DIR = PROJECT_ROOT / "docs"

SOURCE_URL = (
    "https://huggingface.co/datasets/tchenglv/PromptCBLUE/resolve/"
    "refs%2Fconvert%2Fparquet/default/validation/0000.parquet"
)
SOURCE_FILENAME = "promptcblue_validation.parquet"
SOURCE_SHA256 = "62746b21d7a50924c312e6d8233d06d955ec0b7ad15790a49ef0ef3c405e6616"
SOURCE_ROWS = 7656

TASKS = ("KUAKE-QIC", "KUAKE-QQR", "KUAKE-QTR")
EXPECTED_TASK_ROWS = {"KUAKE-QIC": 440, "KUAKE-QQR": 400, "KUAKE-QTR": 400}

DEFAULT_MODEL = "Qwen/Qwen3-0.6B"
STRATEGIES = ("direct", "rubric")
SEED = 20260906

TASK_SHORT = {
    "KUAKE-QIC": "Intent",
    "KUAKE-QQR": "Query relation",
    "KUAKE-QTR": "Title relevance",
}

