import importlib

rime_typing_speed = importlib.import_module("rime_typing_speed")


def test_discover_prefers_schema_list(tmp_path):
    (tmp_path / "default.yaml").write_text(
        "schema_list:\n"
        "  - schema: rime_ice\n"
        "  - schema: double_pinyin_flypy\n"
    )
    (tmp_path / "rime_ice.schema.yaml").write_text("x")
    assert rime_typing_speed.discover_schemas(tmp_path) == ["rime_ice", "double_pinyin_flypy"]


def test_discover_custom_overrides_default(tmp_path):
    (tmp_path / "default.yaml").write_text("schema_list:\n  - schema: rime_ice\n")
    (tmp_path / "default.custom.yaml").write_text(
        "patch:\n  schema_list:\n    - schema: t9\n"
    )
    assert rime_typing_speed.discover_schemas(tmp_path) == ["t9"]


def test_discover_falls_back_to_glob(tmp_path):
    (tmp_path / "rime_ice.schema.yaml").write_text("x")
    (tmp_path / "t9.schema.yaml").write_text("x")
    assert sorted(rime_typing_speed.discover_schemas(tmp_path)) == ["rime_ice", "t9"]
