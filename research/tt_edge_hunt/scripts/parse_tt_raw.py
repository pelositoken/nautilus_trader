"""
Parse verbatim Token Terminal connector responses (data/tt_raw/*.md) into
data/tt/fundamentals_long.csv (date, token, metric, value) and a validation
report data/tt/validation.txt.

Checks: every requested day present per window, no conflicting duplicate
values across files, parse failures listed (never silently dropped).
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from datetime import datetime
from datetime import timedelta
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "tt_raw"
OUT = ROOT / "data" / "tt"

PROJECT_TO_TOKEN = {
    "ethereum": "ETH", "solana": "SOL", "bnb chain": "BNB", "near protocol": "NEAR",
    "near": "NEAR", "uniswap": "UNI", "ethena": "ENA", "tron": "TRX", "sui": "SUI",
    "chainlink": "LINK", "avalanche": "AVAX", "aave": "AAVE", "injective": "INJ",
    "filecoin": "FIL", "ondo finance": "ONDO", "ondo": "ONDO", "arbitrum one": "ARB",
    "arbitrum": "ARB", "curve": "CRV", "aptos": "APT", "jupiter": "JUP",
    "celestia": "TIA", "render network": "RENDER", "render": "RENDER",
    "polygon": "POL", "pancakeswap": "CAKE", "op mainnet": "OP", "optimism": "OP",
    "raydium": "RAY", "ether.fi": "ETHFI", "sei network": "SEI", "sei": "SEI",
    "lido finance": "LDO", "lido": "LDO", "cosmos hub": "ATOM", "pendle": "PENDLE",
    "jito": "JTO",
}
GROUPS = {
    "G1": ["ETH", "SOL", "BNB", "NEAR", "UNI"],
    "G2": ["ENA", "TRX", "SUI", "LINK", "AVAX"],
    "G3": ["AAVE", "INJ", "FIL", "ONDO", "ARB"],
    "G4": ["CRV", "APT", "JUP", "TIA", "RENDER"],
    "G5": ["POL", "CAKE", "OP", "RAY", "ETHFI"],
    "G6": ["SEI", "LDO", "ATOM", "PENDLE", "JTO"],
}
SUFFIX = {"": 1.0, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}
NUM = re.compile(r"^(-)?\$?(-)?([0-9][0-9,]*\.?[0-9]*)\s*([KMBT]?)$")
FNAME = re.compile(r"^(?P<metric>[a-z_]+)__(?P<group>G\d)__(?P<win>Q\d\d)(?P<sub>[a-z]?)\.md$")


def windows() -> dict[str, tuple[date, date]]:
    text = (ROOT / "docs" / "tt_export_protocol.md").read_text()
    return {
        m[0]: (date.fromisoformat(m[1]), date.fromisoformat(m[2]))
        for m in re.findall(r"(Q\d\d) (\d{4}-\d\d-\d\d)\.\.(\d{4}-\d\d-\d\d)", text)
    }


def parse_value(cell: str) -> float | None:
    c = cell.strip().replace("−", "-")
    if c in {"", "-", "—", "–", "n/a", "N/A", "null"}:
        return None
    m = NUM.match(c)
    if not m:
        raise ValueError(f"unparseable cell: {cell!r}")
    v = float(m[3].replace(",", "")) * SUFFIX[m[4]]
    return -v if (m[1] or m[2]) else v


def parse_date(cell: str) -> date:
    c = cell.strip()
    for fmt in ("%B %d, %Y", "%Y-%m-%d", "%b %d, %Y"):
        try:
            return datetime.strptime(c, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"unparseable date: {cell!r}")


def parse_file(path: Path):
    header, rows = None, []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set(":- ") for c in cells):
            continue
        if header is None:
            header = cells
            continue
        if len(cells) != len(header):
            raise ValueError(f"{path.name}: ragged row {line!r}")
        rows.append(cells)
    if header is None:
        raise ValueError(f"{path.name}: no table")
    return header, rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    wins = windows()
    records: dict[tuple, set] = defaultdict(set)
    report: list[str] = []
    covered: dict[tuple, set] = defaultdict(set)  # (metric, group, win) -> dates seen
    for path in sorted(RAW.glob("*.md")):
        m = FNAME.match(path.name)
        if not m:
            report.append(f"SKIP unrecognised file {path.name}")
            continue
        metric, group, win = m["metric"], m["group"], m["win"]
        try:
            header, rows = parse_file(path)
        except ValueError as e:
            report.append(f"ERROR {e}")
            continue
        # columns: Date | [Project |] p1..p5  (long or pivoted layout)
        lower = [h.lower() for h in header]
        if "project" in lower:  # long layout: Project | Date | Value
            ip, idt = lower.index("project"), lower.index("date")
            iv = next(i for i in range(len(header)) if i not in (ip, idt))
            for r in rows:
                tok = PROJECT_TO_TOKEN.get(r[ip].lower())
                if tok is None:
                    report.append(f"WARN {path.name}: unknown project {r[ip]!r}")
                    continue
                d = parse_date(r[idt])
                covered[(metric, group, win)].add(d)
                v = parse_value(r[iv])
                if v is not None:
                    records[(d, tok, metric)].add(v)
            continue
        idt = lower.index("date")
        cols = {}
        for i, h in enumerate(header):
            if i == idt:
                continue
            tok = PROJECT_TO_TOKEN.get(h.lower())
            if tok is None:
                report.append(f"WARN {path.name}: unknown column {h!r}")
            else:
                cols[i] = tok
        missing_cols = set(GROUPS[group]) - set(cols.values())
        if missing_cols:
            report.append(f"WARN {path.name}: missing columns {sorted(missing_cols)}")
        for r in rows:
            try:
                d = parse_date(r[idt])
            except ValueError as e:
                report.append(f"ERROR {path.name}: {e}")
                continue
            covered[(metric, group, win)].add(d)
            for i, tok in cols.items():
                try:
                    v = parse_value(r[i])
                except ValueError as e:
                    report.append(f"ERROR {path.name}: {e}")
                    continue
                if v is not None:
                    records[(d, tok, metric)].add(v)
    # completeness per (metric, group, window)
    metrics = sorted({k[0] for k in covered} | {"fees", "revenue", "tvl", "user_dau",
                                                  "token_supply_circulating"})
    for metric in metrics:
        for group in GROUPS:
            for win, (a, b) in wins.items():
                need = {a + timedelta(days=i) for i in range((b - a).days + 1)}
                got = covered.get((metric, group, win), set())
                if not got:
                    report.append(f"MISSING {metric} {group} {win}")
                elif need - got:
                    report.append(f"GAP {metric} {group} {win}: {len(need - got)} days missing")
    rows_out = []
    for (d, tok, metric), vals in records.items():
        if len(vals) > 1:
            report.append(f"CONFLICT {metric} {tok} {d}: {sorted(vals)} (median kept)")
        rows_out.append((d, tok, metric, float(pd.Series(sorted(vals)).median())))
    df = pd.DataFrame(rows_out, columns=["date", "token", "metric", "value"])
    df = df.sort_values(["metric", "token", "date"])
    df.to_csv(OUT / "fundamentals_long.csv", index=False)
    cov = (df.groupby(["token", "metric"])["date"].agg(["min", "max", "count"]).unstack("metric"))
    cov.to_csv(OUT / "coverage.csv")
    (OUT / "validation.txt").write_text("\n".join(report) + "\n")
    print(f"{len(df)} values; {len(report)} report lines")
    kinds = defaultdict(int)
    for line in report:
        kinds[line.split()[0]] += 1
    print(dict(kinds))


if __name__ == "__main__":
    main()
