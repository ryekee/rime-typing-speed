import importlib

import pytest

rime_speed = importlib.import_module("rime_speed")

LINE = '  "engine/processors/@before 0": lua_processor@*speed_logger'


def test_merge_into_empty_file_creates_patch_block():
    out = rime_speed.merge_processor_patch("")
    assert "patch:" in out
    assert LINE in out
    assert rime_speed.PATCH_BEGIN.strip() in out and rime_speed.PATCH_END.strip() in out


def test_merge_inserts_under_existing_block_patch():
    src = "patch:\n  key/foo: bar\n"
    out = rime_speed.merge_processor_patch(src)
    assert "key/foo: bar" in out          # existing content preserved
    assert LINE in out
    assert out.count("patch:") == 1       # did not add a second patch key


def test_merge_is_idempotent():
    once = rime_speed.merge_processor_patch("patch:\n  key/foo: bar\n")
    twice = rime_speed.merge_processor_patch(once)
    assert once == twice


def test_merge_appends_patch_when_absent():
    src = "# just a comment\nsome_other_key: 1\n"
    out = rime_speed.merge_processor_patch(src)
    assert "some_other_key: 1" in out
    assert "patch:" in out and LINE in out


def test_merge_rejects_inline_patch_mapping():
    with pytest.raises(rime_speed.PatchError):
        rime_speed.merge_processor_patch("patch: { foo: bar }\n")


def test_remove_is_inverse_of_merge():
    src = "patch:\n  key/foo: bar\n"
    merged = rime_speed.merge_processor_patch(src)
    removed = rime_speed.remove_processor_patch(merged)
    assert LINE not in removed
    assert "key/foo: bar" in removed
    assert rime_speed.PATCH_BEGIN not in removed


def test_remove_noop_when_absent():
    src = "patch:\n  key/foo: bar\n"
    assert rime_speed.remove_processor_patch(src) == src


def test_merge_then_remove_is_inverse_empty_file():
    merged = rime_speed.merge_processor_patch("")
    assert rime_speed.remove_processor_patch(merged) == ""


def test_merge_then_remove_is_inverse_no_patch_key():
    src = "# comment\nkey: 1\n"
    merged = rime_speed.merge_processor_patch(src)
    assert rime_speed.remove_processor_patch(merged) == src
