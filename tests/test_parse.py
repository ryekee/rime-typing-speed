import importlib

rime_speed = importlib.import_module("rime_speed")


def test_parse_valid_line():
    line = '{"t":100,"c":3,"han":2,"lat":1,"dig":0,"oth":0,"k":5,"s":"rime_ice"}'
    cm = rime_speed.parse_line(line)
    assert cm.t == 100 and cm.c == 3 and cm.han == 2 and cm.lat == 1
    assert cm.k == 5 and cm.s == "rime_ice"


def test_parse_blank_and_malformed_returns_none():
    assert rime_speed.parse_line("") is None
    assert rime_speed.parse_line("   ") is None
    assert rime_speed.parse_line("not json") is None
    assert rime_speed.parse_line('{"c":3}') is None  # missing required t


def test_parse_defaults_missing_optional_fields():
    cm = rime_speed.parse_line('{"t":1,"c":2}')
    assert cm.han == 0 and cm.lat == 0 and cm.k == 0 and cm.s == ""


def test_read_log_sorts_and_skips_bad(tmp_path):
    p = tmp_path / "commits.jsonl"
    p.write_text(
        '{"t":200,"c":1}\n'
        "garbage\n"
        "\n"
        '{"t":100,"c":2}\n'
    )
    commits = rime_speed.read_log(p)
    assert [c.t for c in commits] == [100, 200]


def test_read_log_missing_file_returns_empty(tmp_path):
    assert rime_speed.read_log(tmp_path / "nope.jsonl") == []
