import importlib

import pytest

rime_speed = importlib.import_module("rime_speed")


@pytest.fixture
def mk():
    """Build a Commit with sensible defaults; han defaults to c (all-CJK)."""
    def _mk(t, c=1, k=0, s="rime_ice", han=None, lat=0, dig=0, oth=0):
        han = c if han is None else han
        return rime_speed.Commit(t=t, c=c, han=han, lat=lat, dig=dig, oth=oth, k=k, s=s)
    return _mk
