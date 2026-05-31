import importlib

rime_speed = importlib.import_module("rime_speed")


def test_write_lua_creates_file(monkeypatch, tmp_path):
    monkeypatch.setenv("RIME_DIR", str(tmp_path))
    dest = rime_speed.write_lua()
    assert dest.exists()
    assert dest == tmp_path / "lua" / "speed_logger.lua"
    assert "commit_notifier" in dest.read_text(encoding="utf-8")


def test_ensure_data_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("RIME_SPEED_DATA_DIR", str(tmp_path / "d"))
    rime_speed.ensure_data_dir()
    assert (tmp_path / "d").is_dir()


def test_patch_schema_custom_creates_and_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setenv("RIME_DIR", str(tmp_path))
    changed1 = rime_speed.patch_schema_custom(tmp_path, "rime_ice")
    changed2 = rime_speed.patch_schema_custom(tmp_path, "rime_ice")
    cust = tmp_path / "rime_ice.custom.yaml"
    assert changed1 is True and changed2 is False
    assert "speed_logger" in cust.read_text(encoding="utf-8")


def test_patch_preserves_existing_custom(monkeypatch, tmp_path):
    monkeypatch.setenv("RIME_DIR", str(tmp_path))
    cust = tmp_path / "rime_ice.custom.yaml"
    cust.write_text("patch:\n  menu/page_size: 7\n", encoding="utf-8")
    rime_speed.patch_schema_custom(tmp_path, "rime_ice")
    body = cust.read_text(encoding="utf-8")
    assert "menu/page_size: 7" in body and "speed_logger" in body


def test_unpatch_removes_only_our_lines(monkeypatch, tmp_path):
    monkeypatch.setenv("RIME_DIR", str(tmp_path))
    cust = tmp_path / "rime_ice.custom.yaml"
    cust.write_text("patch:\n  menu/page_size: 7\n", encoding="utf-8")
    rime_speed.patch_schema_custom(tmp_path, "rime_ice")
    rime_speed.unpatch_schema_custom(tmp_path, "rime_ice")
    body = cust.read_text(encoding="utf-8")
    assert "menu/page_size: 7" in body and "speed_logger" not in body
