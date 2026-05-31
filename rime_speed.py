#!/usr/bin/env python3
"""rime-speed — measure Chinese commit (typing) speed on the Rime input method.

Single-file, standard-library-only CLI. See docs/superpowers for design.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
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
    """Assumes commits are sorted ascending by t."""
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
    """Assumes commits are sorted ascending by t."""
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


def day_bounds(date_str: str) -> Tuple[int, int]:
    """Local-time [start, end) unix bounds for a 'YYYY-MM-DD' day.

    Uses local midnight via time.mktime plus a fixed 86400s span. On DST
    transition days the span can be off by up to an hour; acceptable for
    typing stats. Note by_hour() uses time.localtime (DST-correct), so the
    two can disagree on transition nights.
    """
    d = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    start = int(time.mktime(d.timetuple()))
    return start, start + 86400


def filter_range(commits, start_ts: int, end_ts: int) -> List[Commit]:
    return [c for c in commits if start_ts <= c.t < end_ts]


def _fmt_minutes(seconds: int) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}分{s}秒" if m else f"{s}秒"


def format_today(summary: Summary, by_schema_map: Dict[str, Summary]) -> str:
    lines = [
        "今日打字统计",
        f"  上屏字数：{summary.chars}（汉字 {summary.han}）",
        f"  净速度：{summary.net_cpm:.1f} 字/分钟（活跃 {_fmt_minutes(summary.active_seconds)}）",
        f"  毛速度：{summary.gross_cpm:.1f} 字/分钟",
        f"  峰值速度：{summary.peak_cpm:.1f} 字/分钟",
        f"  码字效率：{summary.eff:.2f} 字/击键",
        f"  会话数：{summary.sessions}，上屏次数：{summary.commits}",
    ]
    if len(by_schema_map) > 1:
        lines.append("  按方案：")
        for name, s in sorted(by_schema_map.items(), key=lambda kv: -kv[1].chars):
            lines.append(f"    {name}: {s.chars} 字，净 {s.net_cpm:.1f} 字/分钟")
    return "\n".join(lines)


def format_report(label: str, summary: Summary, by_schema_map: Dict[str, Summary],
                  by_hour_map: Dict[int, int]) -> str:
    lines = [
        f"{label} 打字统计",
        f"  上屏字数：{summary.chars}（汉字 {summary.han}）",
        f"  净速度：{summary.net_cpm:.1f} 字/分钟",
        f"  毛速度：{summary.gross_cpm:.1f} 字/分钟",
        f"  峰值速度：{summary.peak_cpm:.1f} 字/分钟",
        f"  码字效率：{summary.eff:.2f} 字/击键",
        f"  会话数：{summary.sessions}，上屏次数：{summary.commits}",
    ]
    if by_schema_map:
        lines.append("  按方案：")
        for name, s in sorted(by_schema_map.items(), key=lambda kv: -kv[1].chars):
            lines.append(f"    {name}: {s.chars} 字，净 {s.net_cpm:.1f} 字/分钟")
    if by_hour_map:
        lines.append("  按小时（字数）：")
        for hour in sorted(by_hour_map):
            lines.append(f"    {hour:02d}:00  {by_hour_map[hour]}")
    return "\n".join(lines)


def data_dir() -> Path:
    env = os.environ.get("RIME_SPEED_DATA_DIR")
    if env:
        return Path(env)
    return Path.home() / "Library" / "Application Support" / "rime-speed"


def log_path() -> Path:
    return data_dir() / "commits.jsonl"


def rime_dir() -> Path:
    env = os.environ.get("RIME_DIR")
    if env:
        return Path(env)
    return Path.home() / "Library" / "Rime"


def lua_dest() -> Path:
    return rime_dir() / "lua" / "speed_logger.lua"


_SPEED_LOGGER_LUA = """\
-- speed_logger.lua — part of rime-speed.
-- Logs one privacy-safe record per commit for typing-speed stats.
-- Stores NO committed text: only counts, code length, schema id, timestamp.
-- Registered as a lua_processor; func always returns kNoop (never affects input).
--
-- NOTE: the data directory must already exist (the rime-speed installer creates
-- it). If it does not, io.open returns nil and records are silently dropped.

local P = {}

local kNoop = 2  -- librime ProcessResult: kRejected=0, kAccepted=1, kNoop=2

local _log_path
local function log_file_path()
  if not _log_path then
    local home = os.getenv("HOME") or ""
    _log_path = home .. "/Library/Application Support/rime-speed/commits.jsonl"
  end
  return _log_path
end

-- Decode a UTF-8 string into codepoints. No dependency on the utf8 library
-- (keeps compatibility with LuaJIT / Lua 5.1 builds of librime-lua).
local function utf8_codepoints(s)
  local cps, i, n = {}, 1, #s
  while i <= n do
    local b = s:byte(i)
    local cp, size
    if b < 0x80 then cp, size = b, 1
    elseif b < 0xE0 then cp, size = b % 0x20, 2
    elseif b < 0xF0 then cp, size = b % 0x10, 3
    else cp, size = b % 0x08, 4 end
    for j = 1, size - 1 do
      local cb = s:byte(i + j)
      if not cb then break end
      cp = cp * 0x40 + (cb % 0x40)
    end
    cps[#cps + 1] = cp
    i = i + size
  end
  return cps
end

local function is_han(cp)
  return (cp >= 0x4E00 and cp <= 0x9FFF)     -- CJK Unified
      or (cp >= 0x3400 and cp <= 0x4DBF)     -- Ext A
      or (cp >= 0x20000 and cp <= 0x2A6DF)   -- Ext B
      or (cp >= 0x2A700 and cp <= 0x2EBEF)   -- Ext C-F
      or (cp >= 0x30000 and cp <= 0x3134F)   -- Ext G
      or (cp >= 0xF900 and cp <= 0xFAFF)     -- Compatibility
end

-- Returns total, han, lat, dig, oth counts.
local function classify(text)
  local total, han, lat, dig, oth = 0, 0, 0, 0, 0
  for _, cp in ipairs(utf8_codepoints(text)) do
    total = total + 1
    if is_han(cp) then han = han + 1
    elseif (cp >= 0x41 and cp <= 0x5A) or (cp >= 0x61 and cp <= 0x7A) then lat = lat + 1
    elseif (cp >= 0x30 and cp <= 0x39) then dig = dig + 1
    else oth = oth + 1 end
  end
  return total, han, lat, dig, oth
end

-- Escape a string for safe inclusion inside a JSON double-quoted value.
local function json_escape(s)
  return (s:gsub('[\\\\"]', '\\\\%0'))
end

local function write_record(env, text, code)
  if not text or text == "" then return end
  local total, han, lat, dig, oth = classify(text)
  if total == 0 then return end
  local k = code and #code or 0
  local schema = ""
  if env.engine and env.engine.schema then
    schema = env.engine.schema.schema_id or ""
  end
  local line = string.format(
    '{"t":%d,"c":%d,"han":%d,"lat":%d,"dig":%d,"oth":%d,"k":%d,"s":"%s"}\\n',
    os.time(), total, han, lat, dig, oth, k, json_escape(schema))
  local f = io.open(log_file_path(), "a")
  if f then
    pcall(f.write, f, line)
    f:close()
  end
end

function P.init(env)
  local ctx = env.engine.context
  env.last_input = ""
  -- Cache the most recent non-empty input so we still know the code length
  -- even if ctx.input is already cleared by the time commit fires.
  env.update_conn = ctx.update_notifier:connect(function(c)
    pcall(function()
      if c.input and c.input ~= "" then env.last_input = c.input end
    end)
  end)
  env.commit_conn = ctx.commit_notifier:connect(function(c)
    -- pcall: a logging failure must never break typing.
    pcall(function()
      local text = c:get_commit_text()
      local code = (c.input and c.input ~= "" and c.input) or env.last_input
      write_record(env, text, code)
    end)
    env.last_input = ""
  end)
end

function P.func(key, env)
  return kNoop
end

function P.fini(env)
  if env.commit_conn then env.commit_conn:disconnect() end
  if env.update_conn then env.update_conn:disconnect() end
end

return P
"""


class PatchError(Exception):
    pass


PATCH_BEGIN = "  # >>> rime-speed >>>"
PATCH_LINE = '  "engine/processors/@before 0": lua_processor@*speed_logger'
PATCH_END = "  # <<< rime-speed <<<"
PATCH_BLOCK = "\n".join([PATCH_BEGIN, PATCH_LINE, PATCH_END])


def merge_processor_patch(text: str) -> str:
    if PATCH_BEGIN in text:
        return text  # idempotent
    # Reject an inline `patch: {...}` mapping we cannot safely edit as text.
    if re.search(r"^patch:[ \t]*\S", text, re.M):
        raise PatchError("existing inline `patch:` mapping; add the processor manually")

    lines = text.splitlines()
    out = []
    inserted = False
    for ln in lines:
        out.append(ln)
        if not inserted and re.match(r"^patch:[ \t]*$", ln):
            out.append(PATCH_BLOCK)
            inserted = True
    if not inserted:
        if out and out[-1].strip() != "":
            out.append("")
        out.append("patch:")
        out.append(PATCH_BLOCK)
    return "\n".join(out) + "\n"


def remove_processor_patch(text: str) -> str:
    if PATCH_BEGIN not in text:
        return text
    out = []
    skip = False
    for ln in text.splitlines():
        if ln == PATCH_BEGIN:
            skip = True
            continue
        if ln == PATCH_END:
            skip = False
            continue
        if not skip:
            out.append(ln)
    result = "\n".join(out)
    return result.rstrip("\n") + ("\n" if result.strip() else "")


def _load(args) -> List[Commit]:
    path = args.log if getattr(args, "log", None) else log_path()
    commits = read_log(path)
    if getattr(args, "from_ts", None) is not None or getattr(args, "to_ts", None) is not None:
        lo = args.from_ts if args.from_ts is not None else 0
        hi = args.to_ts if args.to_ts is not None else 2**62
        commits = filter_range(commits, lo, hi)
    elif getattr(args, "day", None):
        lo, hi = day_bounds(args.day)
        commits = filter_range(commits, lo, hi)
    return commits


def cmd_today(args) -> int:
    today = datetime.date.fromtimestamp(time.time()).isoformat()
    lo, hi = day_bounds(today)
    commits = filter_range(read_log(args.log if args.log else log_path()), lo, hi)
    print(format_today(summarize(commits), by_schema(commits)))
    return 0


def cmd_report(args) -> int:
    commits = _load(args)
    label = args.day if args.day else "区间"
    print(format_report(label, summarize(commits), by_schema(commits), by_hour(commits)))
    return 0


def cmd_export(args) -> int:
    import csv
    commits = _load(args)
    # CSV is currently the only export format; --csv is accepted for explicitness / forward-compat.
    w = csv.writer(sys.stdout)
    w.writerow(["t", "c", "han", "lat", "dig", "oth", "k", "s"])
    for c in commits:
        w.writerow([c.t, c.c, c.han, c.lat, c.dig, c.oth, c.k, c.s])
    return 0


def _add_log_args(p):
    p.add_argument("--log", default=None, help="path to commits.jsonl")
    p.add_argument("--day", default=None, help="YYYY-MM-DD (local)")
    p.add_argument("--from-ts", dest="from_ts", type=int, default=None)
    p.add_argument("--to-ts", dest="to_ts", type=int, default=None)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(prog="rime-speed", description="Chinese typing-speed stats for Rime")
    sub = parser.add_subparsers(dest="cmd")

    p_today = sub.add_parser("today", help="today's stats")
    p_today.add_argument("--log", default=None)
    p_today.set_defaults(func=cmd_today)

    p_report = sub.add_parser("report", help="stats for a day or timestamp range")
    _add_log_args(p_report)
    p_report.set_defaults(func=cmd_report)

    p_export = sub.add_parser("export", help="export raw records")
    _add_log_args(p_export)
    p_export.add_argument("--csv", action="store_true", help="输出 CSV（当前唯一格式，默认即为 CSV）")
    p_export.set_defaults(func=cmd_export)

    args = parser.parse_args(argv)
    if not getattr(args, "cmd", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
