#!/usr/bin/env python3
"""rime-speed — measure Chinese commit (typing) speed on the Rime input method.

Single-file, standard-library-only CLI. See docs/superpowers for design.
"""
from __future__ import annotations

import json
import sys
import time
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


def gross_speed(commits, session_gap: int = 300) -> float:
    total_chars = 0
    total_secs = 0
    for s in split_sessions(commits, session_gap):
        if len(s) < 2:
            continue
        total_chars += sum(c.c for c in s[1:])
        total_secs += s[-1].t - s[0].t
    if total_secs <= 0:
        return 0.0
    return total_chars / total_secs * 60.0


def peak_speed(commits, window_seconds: int = 60) -> float:
    n = len(commits)
    if n < 2:
        return 0.0
    pref = [0] * (n + 1)
    for i, c in enumerate(commits):
        pref[i + 1] = pref[i] + c.c
    best = 0.0
    start = 0
    for end in range(n):
        while commits[end].t - commits[start].t > window_seconds:
            start += 1
        if end > start:
            chars = pref[end + 1] - pref[start + 1]
            span = commits[end].t - commits[start].t
            if span > 0:
                best = max(best, chars / span * 60.0)
    return best


class Summary(NamedTuple):
    chars: int
    han: int
    commits: int
    sessions: int
    active_seconds: int
    net_cpm: float
    gross_cpm: float
    peak_cpm: float
    eff: float


def efficiency(commits) -> float:
    chars = sum(c.c for c in commits)
    keys = sum(c.k for c in commits)
    if keys <= 0:
        return 0.0
    return chars / keys


def by_hour(commits) -> Dict[int, int]:
    out: Dict[int, int] = {}
    for c in commits:
        hour = time.localtime(c.t).tm_hour
        out[hour] = out.get(hour, 0) + c.c
    return out


def summarize(commits, idle_threshold: int = 5, session_gap: int = 300,
              window_seconds: int = 60) -> Summary:
    commits = sorted(commits, key=lambda c: c.t)
    secs, _ = active_seconds_and_chars(commits, idle_threshold)
    return Summary(
        chars=sum(c.c for c in commits),
        han=sum(c.han for c in commits),
        commits=len(commits),
        sessions=len(split_sessions(commits, session_gap)),
        active_seconds=secs,
        net_cpm=net_speed(commits, idle_threshold),
        gross_cpm=gross_speed(commits, session_gap),
        peak_cpm=peak_speed(commits, window_seconds),
        eff=efficiency(commits),
    )


def by_schema(commits, **opts) -> Dict[str, Summary]:
    groups: Dict[str, list] = {}
    for c in commits:
        groups.setdefault(c.s, []).append(c)
    return {s: summarize(cs, **opts) for s, cs in groups.items()}


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    print("rime-speed: not implemented yet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
