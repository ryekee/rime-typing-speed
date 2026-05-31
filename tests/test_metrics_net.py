import importlib

rime_speed = importlib.import_module("rime_speed")


def C(t, c):
    return rime_speed.Commit(t=t, c=c, han=c, lat=0, dig=0, oth=0, k=0, s="rime_ice")


def test_split_sessions_breaks_on_large_gap():
    commits = [C(0, 1), C(10, 1), C(10_000, 1), C(10_005, 1)]
    sessions = rime_speed.split_sessions(commits, session_gap=300)
    assert [len(s) for s in sessions] == [2, 2]


def test_active_seconds_and_chars_skips_idle_gaps():
    # gaps: 2,2,(16 idle),2  with idle_threshold=5
    commits = [C(0, 2), C(2, 3), C(4, 2), C(20, 5), C(22, 4)]
    secs, chars = rime_speed.active_seconds_and_chars(commits, idle_threshold=5)
    assert secs == 6        # 2 + 2 + 2
    assert chars == 9       # 3 + 2 + 4 (chars at the end of each kept interval)


def test_net_speed_cpm():
    commits = [C(0, 2), C(2, 3), C(4, 2), C(20, 5), C(22, 4)]
    assert rime_speed.net_speed(commits, idle_threshold=5) == 90.0  # 9 / 6 * 60


def test_net_speed_empty_is_zero():
    assert rime_speed.net_speed([]) == 0.0
    assert rime_speed.net_speed([C(0, 5)]) == 0.0
