import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from edgehunt.sim import non_overlap, simulate  # noqa: E402


def run(o, h, l, c, d=1, sd=1.0, t=2.0, mb=10, cost=0.0):
    a = lambda x: np.asarray(x, np.float64)  # noqa: E731
    return simulate(a(o), a(h), a(l), a(c), np.array([0]), np.array([d], np.int8), a([sd]), t, mb, cost)


def test_target_long():
    xi, r, why = run([100, 100], [100.5, 103], [99.5, 100], [100, 102])
    assert why[0] == 2 and xi[0] == 1 and abs(r[0] - 2.0) < 1e-9


def test_same_bar_both_is_loss():
    xi, r, why = run([100], [103], [98], [100])
    assert why[0] == 1 and abs(r[0] + 1.0) < 1e-9


def test_gap_through_stop_fills_at_open():
    xi, r, why = run([100, 97], [100.5, 97.5], [99.5, 96], [100, 97])
    assert why[0] == 1 and abs(r[0] + 3.0) < 1e-9


def test_short_target_and_time_exit():
    xi, r, why = run([100, 100], [100.2, 100.1], [99.8, 97.9], [100, 98], d=-1)
    assert why[0] == 2 and abs(r[0] - 2.0) < 1e-9
    xi, r, why = run([100, 100, 100], [100.2] * 3, [99.8] * 3, [100, 100, 100.5], mb=3)
    assert why[0] == 3 and xi[0] == 2 and abs(r[0] - 0.5) < 1e-9


def test_costs_in_r():
    # 1% risk, 0.1% per side cost -> -0.2R drag
    xi, r, why = run([100, 100], [100.5, 103], [99.5, 100], [100, 102], cost=0.001)
    assert abs(r[0] - (2.0 - 0.2)) < 1e-9


def test_non_overlap():
    keep = non_overlap(np.array([0, 0, 0, 1]), np.array([1, 3, 6, 2]), np.array([5, 7, 8, 4]))
    assert keep.tolist() == [True, False, True, True]


def test_pbo_detects_noise_and_skill():
    from edgehunt.pbo import pbo
    rng = np.random.default_rng(0)
    noise = rng.normal(0, 1, (1600, 50))
    assert 0.3 < pbo(noise)["pbo"] < 0.7  # pure noise: selection is a coin flip
    skill = noise.copy()
    skill[:, 0] += 0.3  # one strategy truly better everywhere
    assert pbo(skill)["pbo"] < 0.05
