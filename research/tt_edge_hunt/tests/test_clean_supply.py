import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from edgehunt.data import clean_supply  # noqa: E402


def test_placeholder_blip_and_break():
    idx = pd.date_range("2024-01-01", periods=8)
    df = pd.DataFrame({
        "OP": [214_748_364.0] * 3 + [645e6, 646e6, 647e6, 648e6, 649e6],
        "NEAR": [1.08e9, 1.08e9, 1.15e9, 1.081e9, 1.082e9, 1.083e9, 1.084e9, 1.085e9],
        "POL": [388e6, 388e6, 389e6, 5.55e9, 5.56e9, 5.57e9, 5.58e9, 5.59e9],
    }, index=idx)
    out = clean_supply(df)
    assert out["OP"].iloc[:3].isna().all() and out["OP"].iloc[3] == 645e6
    assert np.isnan(out["NEAR"].iloc[2]) and out["NEAR"].iloc[3] == 1.081e9
    assert out["POL"].iloc[:3].isna().all() and out["POL"].iloc[3] == 5.55e9
