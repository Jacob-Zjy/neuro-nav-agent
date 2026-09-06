from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .config import DEFAULT_MODEL, RESULTS_DIR, STRATEGIES
from .data import EvalItem
from .prompts import messages


@dataclass(frozen=True)
class Candidate:
    item_index: int
    choice: str
    prompt_ids: tuple[int, ...]
    choice_ids: tuple[int, ...]


class HFChoiceScorer:
    """Score every allowed label by conditional likelihood under a causal LLM."""

    def __init__(self, model_name: str = DEFAULT_MODEL, device: str = "auto") -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:  # pragma: no cover - exercised only without model extra
            raise RuntimeError('Install model dependencies with: pip install -e ".[model]"') from exc

        self.torch = torch
        self.device = self._resolve_device(device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        dtype = torch.bfloat16 if self.device == "cuda" else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(model_name, dtype=dtype)
        self.model.to(self.device)
        self.model.eval()
        self.model_name = model_name
        self.model_revision = getattr(self.model.config, "_commit_hash", None) or "unknown"

    def _resolve_device(self, requested: str) -> str:
        if requested == "auto":
            return "cuda" if self.torch.cuda.is_available() else "cpu"
        if requested == "cuda" and not self.torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false")
        if requested not in {"cuda", "cpu"}:
            raise ValueError("device must be auto, cuda, or cpu")
        return requested

    def _prefix_ids(self, item: EvalItem, strategy: str) -> tuple[int, ...]:
        rendered = self.tokenizer.apply_chat_template(
            messages(item, strategy),
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        token_ids = self.tokenizer(rendered, add_special_tokens=False)["input_ids"]
        return tuple(int(token_id) for token_id in token_ids)

    def _candidates(self, items: list[EvalItem], strategy: str) -> list[Candidate]:
        candidates: list[Candidate] = []
        for item_index, item in enumerate(items):
            prefix = self._prefix_ids(item, strategy)
            for choice in item.choices:
                choice_ids = tuple(
                    int(token_id)
                    for token_id in self.tokenizer(choice, add_special_tokens=False)["input_ids"]
                )
                if not choice_ids:
                    raise ValueError(f"Choice tokenized to an empty sequence: {choice!r}")
                candidates.append(Candidate(item_index, choice, prefix, choice_ids))
        return candidates

    def _score_batch(self, batch: list[Candidate]) -> list[float]:
        torch = self.torch
        sequences = [candidate.prompt_ids + candidate.choice_ids for candidate in batch]
        max_length = max(len(sequence) for sequence in sequences)
        pad_id = int(self.tokenizer.pad_token_id)
        input_ids = torch.full(
            (len(batch), max_length), pad_id, dtype=torch.long, device=self.device
        )
        attention_mask = torch.zeros_like(input_ids)
        for row_index, sequence in enumerate(sequences):
            length = len(sequence)
            input_ids[row_index, :length] = torch.tensor(
                sequence, dtype=torch.long, device=self.device
            )
            attention_mask[row_index, :length] = 1

        with torch.inference_mode():
            logits = self.model(input_ids=input_ids, attention_mask=attention_mask).logits

        scores: list[float] = []
        for row_index, candidate in enumerate(batch):
            prompt_length = len(candidate.prompt_ids)
            positions = torch.arange(
                prompt_length - 1,
                prompt_length + len(candidate.choice_ids) - 1,
                device=self.device,
            )
            target_ids = torch.tensor(
                candidate.choice_ids, dtype=torch.long, device=self.device
            )
            # Converting the full [batch, sequence, vocabulary] tensor to fp32
            # can exceed an 8 GB GPU for longer rubric prompts. Only the logits
            # at answer-token positions are needed for conditional likelihood.
            answer_logits = logits[row_index].index_select(0, positions).float()
            selected = answer_logits.gather(1, target_ids.unsqueeze(1)).squeeze(1)
            token_log_probs = selected - torch.logsumexp(answer_logits, dim=1)
            scores.append(float(token_log_probs.mean().cpu()))
        return scores

    def score(
        self,
        items: Iterable[EvalItem],
        *,
        strategies: tuple[str, ...] = STRATEGIES,
        batch_size: int = 32,
    ) -> tuple[pd.DataFrame, dict[str, object]]:
        item_list = list(items)
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        started = time.perf_counter()
        output_rows: list[dict[str, object]] = []

        for strategy in strategies:
            candidates = self._candidates(item_list, strategy)
            total_batches = math.ceil(len(candidates) / batch_size)
            choice_scores: dict[int, list[tuple[str, float]]] = {
                index: [] for index in range(len(item_list))
            }
            for start in range(0, len(candidates), batch_size):
                batch = candidates[start : start + batch_size]
                scores = self._score_batch(batch)
                for candidate, score in zip(batch, scores):
                    choice_scores[candidate.item_index].append((candidate.choice, score))
                batch_number = start // batch_size + 1
                if batch_number == 1 or batch_number % 25 == 0 or batch_number == total_batches:
                    print(
                        f"[{strategy}] batch {batch_number}/{total_batches} "
                        f"({min(start + len(batch), len(candidates))}/{len(candidates)} candidates)",
                        flush=True,
                    )

            for item_index, item in enumerate(item_list):
                pairs = choice_scores[item_index]
                raw_scores = np.asarray([score for _, score in pairs], dtype=float)
                shifted = raw_scores - raw_scores.max()
                probabilities = np.exp(shifted) / np.exp(shifted).sum()
                order = np.argsort(probabilities)[::-1]
                prediction_index = int(order[0])
                prediction = pairs[prediction_index][0]
                confidence = float(probabilities[prediction_index])
                margin = float(
                    probabilities[order[0]] - probabilities[order[1]]
                    if len(order) > 1
                    else 1.0
                )
                entropy = float(
                    -sum(float(prob) * math.log(max(float(prob), 1e-12)) for prob in probabilities)
                )
                output_rows.append(
                    {
                        "item_id": item.item_id,
                        "sample_id": item.sample_id,
                        "input_sha256": item.input_sha256,
                        "task": item.task,
                        "strategy": strategy,
                        "target": item.target,
                        "prediction": prediction,
                        "correct": prediction == item.target,
                        "confidence": confidence,
                        "margin": margin,
                        "entropy": entropy,
                        "normalized_entropy": entropy / math.log(len(item.choices)),
                        "choice_count": len(item.choices),
                        "character_count": len(item.prompt),
                        "choice_probabilities": json.dumps(
                            {choice: float(prob) for (choice, _), prob in zip(pairs, probabilities)},
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                    }
                )

        elapsed = time.perf_counter() - started
        metadata = {
            "model": self.model_name,
            "model_revision": self.model_revision,
            "device": self.device,
            "torch_version": self.torch.__version__,
            "cuda_version": self.torch.version.cuda,
            "gpu": self.torch.cuda.get_device_name(0) if self.device == "cuda" else None,
            "strategies": list(strategies),
            "items": len(item_list),
            "predictions": len(output_rows),
            "candidate_sequences": int(
                sum(len(item.choices) for item in item_list) * len(strategies)
            ),
            "batch_size": batch_size,
            "elapsed_seconds": elapsed,
            "scoring": "mean conditional log-probability over allowed label tokens",
            "decoding": "deterministic forced choice; no sampling",
        }
        return pd.DataFrame(output_rows), metadata


def write_inference_outputs(
    predictions: pd.DataFrame,
    metadata: dict[str, object],
    results_dir: Path = RESULTS_DIR,
) -> tuple[Path, Path]:
    results_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = results_dir / "predictions.csv"
    metadata_path = results_dir / "run_metadata.json"
    predictions.to_csv(prediction_path, index=False)
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return prediction_path, metadata_path
