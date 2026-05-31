#!/usr/bin/env python3
"""rime-speed — measure Chinese commit (typing) speed on the Rime input method.

Single-file, standard-library-only CLI. See docs/superpowers for design.
"""
from __future__ import annotations

import sys


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    print("rime-speed: not implemented yet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
