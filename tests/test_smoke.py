import importlib


def test_module_imports():
    mod = importlib.import_module("rime_typing_speed")
    assert hasattr(mod, "main")
