"""
List Token Terminal export jobs (metric, group, window) that have no saved file
yet, holdout windows first, and split them into N job files for retry agents.

Usage: python scripts/tt_todo.py PREFIX N metric [metric ...]
Writes data/tt_raw/_jobs_{PREFIX}{i}.txt (one "metric group window start end" per line).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "tt_raw"
GROUPS = ["G1", "G2", "G3", "G4", "G5", "G6"]
HOLDOUT = {"Q14", "Q15", "Q16", "Q17", "Q18"}


def windows() -> dict[str, tuple[str, str]]:
    text = (ROOT / "docs" / "tt_export_protocol.md").read_text()
    return {m[0]: (m[1], m[2]) for m in re.findall(r"(Q\d\d) (\d{4}-\d\d-\d\d)\.\.(\d{4}-\d\d-\d\d)", text)}


def have(metric: str, group: str, win: str) -> bool:
    # a full window file, or both halves of a split window, counts as done
    if (RAW / f"{metric}__{group}__{win}.md").exists():
        return True
    return (RAW / f"{metric}__{group}__{win}a.md").exists() and (RAW / f"{metric}__{group}__{win}b.md").exists()


def main() -> None:
    prefix, n = sys.argv[1], int(sys.argv[2])
    metrics = sys.argv[3:]
    wins = windows()
    jobs = [(m, g, w) for m in metrics for w in wins for g in GROUPS if not have(m, g, w)]
    jobs.sort(key=lambda j: (j[2] not in HOLDOUT, metrics.index(j[0]), j[2], j[1]))
    for f in RAW.glob(f"_jobs_{prefix}*.txt"):
        f.unlink()
    for i in range(n):
        part = jobs[i::n]
        (RAW / f"_jobs_{prefix}{i}.txt").write_text("".join(f"{m} {g} {w} {wins[w][0]} {wins[w][1]}\n" for m, g, w in part))
    print(f"{len(jobs)} jobs -> {n} files")


if __name__ == "__main__":
    main()
