import importlib

rime_typing_speed = importlib.import_module("rime_typing_speed")


def _write_log(tmp_path):
    p = tmp_path / "commits.jsonl"
    p.write_text(
        '{"t":1000,"c":2,"han":2,"k":4,"s":"rime_ice"}\n'
        '{"t":1002,"c":3,"han":3,"k":2,"s":"rime_ice"}\n'
        '{"t":1004,"c":2,"han":2,"k":3,"s":"t9"}\n'
    )
    return p


def test_report_command_prints_stats(tmp_path, capsys):
    log = _write_log(tmp_path)
    rc = rime_typing_speed.main(["report", "--log", str(log)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "字/分钟" in out
    assert "rime_ice" in out


def test_export_csv(tmp_path, capsys):
    log = _write_log(tmp_path)
    rc = rime_typing_speed.main(["export", "--log", str(log), "--csv"])
    out = capsys.readouterr().out
    assert rc == 0
    assert out.splitlines()[0] == "t,c,han,lat,dig,oth,k,s"
    assert "rime_ice" in out


def test_report_range_filters(tmp_path, capsys):
    log = _write_log(tmp_path)
    rc = rime_typing_speed.main(["report", "--log", str(log), "--from-ts", "1003", "--to-ts", "1010"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "t9" in out
    assert "rime_ice" not in out
