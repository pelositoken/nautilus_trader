import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from parse_tt_raw import parse_file, parse_value  # noqa: E402


def test_values():
    assert parse_value("$1.23M") == 1.23e6
    assert parse_value("2.94K") == 2940.0
    assert parse_value("$0.0612") == 0.0612
    assert parse_value("$103,587.82") == 103587.82
    assert parse_value("—") is None


def test_multi_table_keeps_each_header(tmp_path):
    f = tmp_path / "tvl__T2__Q17.md"
    f.write_text(
        "| Date | Stray | Header |\n\n"
        "| Day | Jupiter | Raydium |\n|---|---|---|\n| June 1, 2026 | $3.17B | $674M |\n\n"
        "| Day | Ethena | Jito |\n|---|---|---|\n| June 1, 2026 | $5.43B | $793M |\n"
    )
    tables = parse_file(f)
    assert [t[0][1] for t in tables] == ["Jupiter", "Ethena"]
    assert tables[0][1][0][1] == "$3.17B" and tables[1][1][0][1] == "$5.43B"


def test_same_in_every_row():
    from parse_tt_raw import same_in_every_row
    got = same_in_every_row("Same in every row: Ether.fi —; OP Mainnet 215M; Polygon —.\n")
    assert got == [("Ether.fi", None), ("OP Mainnet", 215e6), ("Polygon", None)]
