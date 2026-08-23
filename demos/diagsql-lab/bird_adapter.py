from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from diagsql.bird_interact import load_bird_jsonl, summarize_bird_records


def summarize_path(path: str | Path) -> dict[str, Any]:
    records = load_bird_jsonl(path)
    return summarize_bird_records(records).as_dict()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize BIRD-INTERACT / Mini-Interact ambiguity annotations without using evaluator-only labels at runtime."
    )
    parser.add_argument("jsonl", type=Path, help="Path to a downloaded BIRD-INTERACT JSONL file")
    args = parser.parse_args()
    print(json.dumps(summarize_path(args.jsonl), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
