-- speed_logger.lua — part of rime-speed.
-- Logs one privacy-safe record per commit for typing-speed stats.
-- Stores NO committed text: only counts, code length, schema id, timestamp.
-- Registered as a lua_processor; func always returns kNoop (never affects input).

local P = {}

local kNoop = 2  -- librime ProcessResult: kRejected=0, kAccepted=1, kNoop=2

local function log_file_path()
  local home = os.getenv("HOME") or ""
  return home .. "/Library/Application Support/rime-speed/commits.jsonl"
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
    '{"t":%d,"c":%d,"han":%d,"lat":%d,"dig":%d,"oth":%d,"k":%d,"s":"%s"}\n',
    os.time(), total, han, lat, dig, oth, k, schema)
  local f = io.open(log_file_path(), "a")
  if f then f:write(line); f:close() end
end

function P.init(env)
  local ctx = env.engine.context
  env.last_input = ""
  -- Cache the most recent non-empty input so we still know the code length
  -- even if ctx.input is already cleared by the time commit fires.
  env.update_conn = ctx.update_notifier:connect(function(c)
    if c.input and c.input ~= "" then env.last_input = c.input end
  end)
  env.commit_conn = ctx.commit_notifier:connect(function(c)
    -- pcall: a logging failure must never break typing.
    pcall(function()
      local text = c:get_commit_text()
      local code = (c.input and c.input ~= "" and c.input) or env.last_input
      write_record(env, text, code)
      env.last_input = ""
    end)
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
