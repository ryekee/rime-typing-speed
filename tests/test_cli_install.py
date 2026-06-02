import importlib

rime_typing_speed = importlib.import_module("rime_typing_speed")


def _seed_rime(tmp_path):
    (tmp_path / "default.yaml").write_text(
        "schema_list:\n  - schema: rime_ice\n  - schema: t9\n"
    )
    (tmp_path / "rime_ice.schema.yaml").write_text("x")
    (tmp_path / "t9.schema.yaml").write_text("x")


def test_install_patches_all_schemas(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("RIME_DIR", str(tmp_path))
    monkeypatch.setenv("RIME_SPEED_DATA_DIR", str(tmp_path / "data"))
    _seed_rime(tmp_path)
    rc = rime_typing_speed.main(["install", "--no-deploy"])
    assert rc == 0
    assert (tmp_path / "lua" / "speed_logger.lua").exists()
    assert "speed_logger" in (tmp_path / "rime_ice.custom.yaml").read_text()
    assert "speed_logger" in (tmp_path / "t9.custom.yaml").read_text()
    assert (tmp_path / "data").is_dir()


def test_install_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setenv("RIME_DIR", str(tmp_path))
    monkeypatch.setenv("RIME_SPEED_DATA_DIR", str(tmp_path / "data"))
    _seed_rime(tmp_path)
    rime_typing_speed.main(["install", "--no-deploy"])
    before = (tmp_path / "rime_ice.custom.yaml").read_text()
    rime_typing_speed.main(["install", "--no-deploy"])
    after = (tmp_path / "rime_ice.custom.yaml").read_text()
    assert before == after


def test_uninstall_reverts(monkeypatch, tmp_path):
    monkeypatch.setenv("RIME_DIR", str(tmp_path))
    monkeypatch.setenv("RIME_SPEED_DATA_DIR", str(tmp_path / "data"))
    _seed_rime(tmp_path)
    rime_typing_speed.main(["install", "--no-deploy"])
    rime_typing_speed.main(["uninstall", "--no-deploy"])
    # install created these fresh; uninstall removes our block -> empty -> deleted
    assert not (tmp_path / "rime_ice.custom.yaml").exists()
    assert not (tmp_path / "t9.custom.yaml").exists()
    assert not (tmp_path / "lua" / "speed_logger.lua").exists()


def test_deploy_not_called_with_no_deploy(monkeypatch, tmp_path):
    monkeypatch.setenv("RIME_DIR", str(tmp_path))
    monkeypatch.setenv("RIME_SPEED_DATA_DIR", str(tmp_path / "data"))
    _seed_rime(tmp_path)
    called = {"n": 0}
    monkeypatch.setattr(rime_typing_speed, "deploy", lambda: called.__setitem__("n", called["n"] + 1))
    rime_typing_speed.main(["install", "--no-deploy"])
    assert called["n"] == 0
