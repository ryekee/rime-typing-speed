#!/usr/bin/env python3
"""rime-speed — measure Chinese commit (typing) speed on the Rime input method.

Single-file, standard-library-only CLI. See docs/superpowers for design.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple


class Commit(NamedTuple):
    t: int
    c: int
    han: int
    lat: int
    dig: int
    oth: int
    k: int
    s: str


def parse_line(line: str) -> Optional[Commit]:
    line = line.strip()
    if not line:
        return None
    try:
        d = json.loads(line)
        return Commit(
            t=int(d["t"]),
            c=int(d["c"]),
            han=int(d.get("han", 0)),
            lat=int(d.get("lat", 0)),
            dig=int(d.get("dig", 0)),
            oth=int(d.get("oth", 0)),
            k=int(d.get("k", 0)),
            s=str(d.get("s", "")),
        )
    except (ValueError, TypeError, KeyError):
        return None


def read_log(path) -> List[Commit]:
    path = Path(path)
    if not path.exists():
        return []
    commits = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            cm = parse_line(line)
            if cm is not None:
                commits.append(cm)
    commits.sort(key=lambda c: c.t)
    return commits


def split_sessions(commits, session_gap: int = 300):
    sessions = []
    cur = []
    for cm in commits:
        if cur and cm.t - cur[-1].t > session_gap:
            sessions.append(cur)
            cur = []
        cur.append(cm)
    if cur:
        sessions.append(cur)
    return sessions


def active_seconds_and_chars(commits, idle_threshold: int = 5) -> Tuple[int, int]:
    secs = 0
    chars = 0
    for prev, cur in zip(commits, commits[1:]):
        gap = cur.t - prev.t
        if 0 < gap <= idle_threshold:
            secs += gap
            chars += cur.c
    return secs, chars


def net_speed(commits, idle_threshold: int = 5) -> float:
    secs, chars = active_seconds_and_chars(commits, idle_threshold)
    if secs <= 0:
        return 0.0
    return chars / secs * 60.0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    print("rime-speed: not implemented yet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
