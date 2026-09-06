from __future__ import annotations

import argparse

from medevalops.config import DEFAULT_MODEL, PROCESSED_DIR
from medevalops.data import read_private_items
from medevalops.inference import HFChoiceScorer, write_inference_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic forced-choice LLM evaluation.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--limit", type=int, default=None, help="Debug-only item limit.")
    args = parser.parse_args()

    path = PROCESSED_DIR / "eval_items.jsonl"
    if not path.exists():
        raise SystemExit("Missing processed data. Run: python -m scripts.download_data")
    items = read_private_items(path)
    if args.limit is not None:
        items = items[: args.limit]
    scorer = HFChoiceScorer(model_name=args.model, device=args.device)
    predictions, metadata = scorer.score(items, batch_size=args.batch_size)
    paths = write_inference_outputs(predictions, metadata)
    print(f"Predictions: {paths[0]}")
    print(f"Run metadata: {paths[1]}")


if __name__ == "__main__":
    main()

