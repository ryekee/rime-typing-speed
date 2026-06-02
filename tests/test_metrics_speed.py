import importlib

import pytest

rime_typing_speed = importlib.import_module("rime_typing_speed")


def C(t, c):
    return rime_typing_speed.Commit(t=t, c=c, han=c, lat=0, dig=0, oth=0, k=0, s="rime_ice")


def test_gross_speed_one_session():
    commits = [C(0, 2), C(2, 3), C(4, 2), C(20, 5), C(22, 4)]
    # one session (max gap 16 < 300); chars after first = 14; span 22s
    assert rime_typing_speed.gross_speed(commits, session_gap=300) == pytest.approx(14 / 22 * 60)


def test_gross_speed_ignores_singleton_sessions():
    commits = [C(0, 5), C(10_000, 3)]  # two singletons -> no measurable span
    assert rime_typing_speed.gross_speed(commits, session_gap=300) == 0.0


def test_peak_speed_short_window():
    commits = [C(0, 2), C(2, 3), C(4, 2), C(20, 5), C(22, 4)]
    # best 5s window is 20->22: 4 chars / 2s * 60 = 120
    assert rime_typing_speed.peak_speed(commits, window_seconds=5) == pytest.approx(120.0)


def test_peak_speed_trivial_inputs():
    assert rime_typing_speed.peak_speed([]) == 0.0
    assert rime_typing_speed.peak_speed([C(0, 9)]) == 0.0
