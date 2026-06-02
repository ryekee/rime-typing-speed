import importlib
from pathlib import Path

rime_typing_speed = importlib.import_module("rime_typing_speed")


def test_data_dir_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("RIME_SPEED_DATA_DIR", str(tmp_path))
    assert rime_typing_speed.data_dir() == tmp_path
    assert rime_typing_speed.log_path() == tmp_path / "commits.jsonl"


def test_rime_dir_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("RIME_DIR", str(tmp_path))
    assert rime_typing_speed.rime_dir() == tmp_path
    assert rime_typing_speed.lua_dest() == tmp_path / "lua" / "speed_logger.lua"


def test_embedded_lua_matches_repo_file():
    repo_lua = Path(__file__).resolve().parent.parent / "lua" / "speed_logger.lua"
    if not repo_lua.exists():
        import pytest
        pytest.skip("repo lua file not present (e.g. installed wheel)")
    assert rime_typing_speed._SPEED_LOGGER_LUA == repo_lua.read_text(encoding="utf-8")
