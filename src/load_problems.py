"""Load 100 MBPP problems and cache them to data/problems.json.

MBPP ("Mostly Basic Python Problems") is a set of small, toy coding tasks that
ship with assert-style tests. We use the hand-checked `sanitized` config.
Sampling uses a fixed seed so every run of the experiment sees the same problems.

Usage:  python src/load_problems.py
"""

import json
import random
from pathlib import Path

from datasets import load_dataset, concatenate_datasets

N_PROBLEMS = 100
SEED = 0
OUT = Path(__file__).resolve().parent.parent / "data" / "problems.json"


def main():
    ds = load_dataset("google-research-datasets/mbpp", "sanitized")
    # The sanitized config is split into train/test/validation/prompt; pool them
    # all and sample, so the split names don't matter for this experiment.
    pool = concatenate_datasets([ds[s] for s in ds.keys()])
    rows = sorted(pool, key=lambda r: r["task_id"])

    rng = random.Random(SEED)
    picked = sorted(rng.sample(rows, N_PROBLEMS), key=lambda r: r["task_id"])

    problems = [
        {
            "task_id": r["task_id"],
            "prompt": r["prompt"],
            "reference_code": r["code"],
            "test_imports": r["test_imports"],
            "tests": r["test_list"],
        }
        for r in picked
    ]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(problems, indent=2))
    print(f"Wrote {len(problems)} problems to {OUT}")

    p = problems[0]
    print(f"\nExample: task {p['task_id']}\n{p['prompt']}\nTests:")
    for t in p["tests"]:
        print("  ", t)


if __name__ == "__main__":
    main()
