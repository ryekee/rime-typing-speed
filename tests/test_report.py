import importlib

rime_typing_speed = importlib.import_module("rime_typing_speed")


def C(t, c, s="rime_ice"):
    return rime_typing_speed.Commit(t=t, c=c, han=c, lat=0, dig=0, oth=0, k=2, s=s)


def test_day_bounds_span_is_one_day():
    start, end = rime_typing_speed.day_bounds("2026-05-31")
    assert end - start == 86400


def test_filter_range_inclusive_start_exclusive_end():
    commits = [C(99, 1), C(100, 1), C(199, 1), C(200, 1)]
    out = rime_typing_speed.filter_range(commits, 100, 200)
    assert [c.t for c in out] == [100, 199]


def test_format_today_contains_headline_numbers():
    commits = [C(0, 2), C(2, 3), C(4, 2)]
    summary = rime_typing_speed.summarize(commits)
    text = rime_typing_speed.format_today(summary, rime_typing_speed.by_schema(commits))
    assert "字/分钟" in text
    assert "7" in text          # total chars
    assert "净速度" in text
    assert "毛速度" in text


def test_format_report_includes_label_and_schema():
    commits = [C(0, 2, s="rime_ice"), C(3, 3, s="t9")]
    summary = rime_typing_speed.summarize(commits)
    text = rime_typing_speed.format_report(
        "本周", summary, rime_typing_speed.by_schema(commits), rime_typing_speed.by_hour(commits)
    )
    assert "本周" in text
    assert "rime_ice" in text and "t9" in text
