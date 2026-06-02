import datetime
import importlib
import time

import pytest

rime_speed = importlib.import_module("rime_speed")


def _today():
    return datetime.date.fromtimestamp(time.time())


def _write(log, rows):
    log.write_text("".join(
        '{"t":%d,"c":%d,"han":%d,"lat":0,"dig":0,"oth":0,"k":0,"s":"%s"}\n' % r for r in rows
    ))


def test_resolve_period_none():
    assert rime_speed.resolve_period(None) == (None, None, None)


def test_resolve_period_today():
    d = _today().isoformat()
    lo, hi, label = rime_speed.resolve_period("today")
    assert (lo, hi) == rime_speed.day_bounds(d)
    assert label == d


def test_resolve_period_yesterday():
    y = (_today() - datetime.timedelta(days=1)).isoformat()
    lo, hi, label = rime_speed.resolve_period("yesterday")
    assert (lo, hi) == rime_speed.day_bounds(y)
    assert label == y


def test_resolve_period_week_is_7_days_ending_yesterday():
    today = _today()
    lo, hi, label = rime_speed.resolve_period("week")
    assert lo == rime_speed.day_bounds((today - datetime.timedelta(days=7)).isoformat())[0]
    assert hi == rime_speed.day_bounds(today.isoformat())[0]
    # label shows the inclusive range start .. yesterday
    assert (today - datetime.timedelta(days=7)).isoformat() in label
    assert (today - datetime.timedelta(days=1)).isoformat() in label


def test_resolve_period_explicit_date():
    lo, hi, label = rime_speed.resolve_period("2026-03-15")
    assert (lo, hi) == rime_speed.day_bounds("2026-03-15")
    assert label == "2026-03-15"


def test_resolve_period_invalid_raises():
    with pytest.raises(ValueError):
        rime_speed.resolve_period("notaperiod")


def test_report_yesterday_filters(tmp_path, capsys):
    today = _today()
    y_start = rime_speed.day_bounds((today - datetime.timedelta(days=1)).isoformat())[0]
    t_start = rime_speed.day_bounds(today.isoformat())[0]
    log = tmp_path / "c.jsonl"
    _write(log, [(y_start + 100, 5, 5, "rime_ice"), (t_start + 100, 9, 9, "t9")])
    rc = rime_speed.main(["report", "yesterday", "--log", str(log)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "rime_ice" in out
    assert "t9" not in out  # today excluded


def test_report_week_includes_range_excludes_today_and_old(tmp_path, capsys):
    today = _today()
    in_week = rime_speed.day_bounds((today - datetime.timedelta(days=3)).isoformat())[0] + 50
    today_ts = rime_speed.day_bounds(today.isoformat())[0] + 50
    old_ts = rime_speed.day_bounds((today - datetime.timedelta(days=8)).isoformat())[0] + 50
    log = tmp_path / "c.jsonl"
    _write(log, [(in_week, 4, 4, "rime_ice"), (today_ts, 7, 7, "t9"), (old_ts, 3, 3, "liangfen")])
    rc = rime_speed.main(["report", "week", "--log", str(log)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "rime_ice" in out      # within the week
    assert "t9" not in out        # today excluded
    assert "liangfen" not in out  # 8 days ago excluded


def test_report_backward_compat_day_flag(tmp_path, capsys):
    today = _today()
    y = (today - datetime.timedelta(days=1)).isoformat()
    y_start = rime_speed.day_bounds(y)[0]
    log = tmp_path / "c.jsonl"
    _write(log, [(y_start + 100, 5, 5, "rime_ice")])
    rc = rime_speed.main(["report", "--day", y, "--log", str(log)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "rime_ice" in out


def test_report_invalid_period_returns_error(tmp_path, capsys):
    log = tmp_path / "c.jsonl"
    log.write_text("")
    rc = rime_speed.main(["report", "bogus", "--log", str(log)])
    assert rc == 2
