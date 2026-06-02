import importlib

import pytest

rime_typing_speed = importlib.import_module("rime_typing_speed")


def C(t, c, k=0, s="rime_ice", han=None):
    han = c if han is None else han
    return rime_typing_speed.Commit(t=t, c=c, han=han, lat=0, dig=0, oth=0, k=k, s=s)


def test_keys_per_char():
    commits = [C(0, 2, k=4), C(2, 3, k=2)]  # 6 keys / 5 chars
    assert rime_typing_speed.keys_per_char(commits) == pytest.approx(6 / 5)


def test_keys_per_char_guards_zero():
    assert rime_typing_speed.keys_per_char([]) == 0.0              # no chars
    assert rime_typing_speed.keys_per_char([C(0, 5, k=0)]) == 0.0  # no keystrokes logged


def test_by_hour_buckets_local_chars():
    # 1970-01-01 00:00:10 local -> some hour; just assert chars sum routed to one bucket
    commits = [C(10, 2), C(20, 3)]
    h = rime_typing_speed.by_hour(commits)
    assert sum(h.values()) == 5


def test_by_schema_groups():
    commits = [C(0, 2, s="rime_ice"), C(2, 3, s="t9"), C(4, 1, s="rime_ice")]
    m = rime_typing_speed.by_schema(commits)
    assert set(m.keys()) == {"rime_ice", "t9"}
    assert m["rime_ice"].chars == 3
    assert m["t9"].chars == 3


def test_summarize_fields():
    commits = [C(0, 2, k=4), C(2, 3, k=2), C(4, 2, k=3)]
    s = rime_typing_speed.summarize(commits)
    assert s.chars == 7
    assert s.commits == 3
    assert s.sessions == 1
    assert s.net_cpm > 0
    assert s.kpc == pytest.approx(9 / 7)
