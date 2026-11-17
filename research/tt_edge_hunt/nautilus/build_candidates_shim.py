"""Recompute the research engine's stop distance (s x ATR of last completed TF bar)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from edgehunt.data import atr
from edgehunt.data import load_5m
from edgehunt.data import resample


def stop_distances(token: str, es, entry_idx: np.ndarray) -> np.ndarray:
    df5 = load_5m(token)
    bars = resample(df5, es.tf)
    a = atr(bars, 14)
    tf = pd.Timedelta(es.tf)
    atr5 = pd.Series(a.to_numpy(), index=bars.index + tf).reindex(df5.index).to_numpy()
    return es.stop_atr * atr5[entry_idx]
