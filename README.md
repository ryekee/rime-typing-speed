# rime-typing-speed

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![Platform](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)
![for Rime / Squirrel](https://img.shields.io/badge/for-Rime%20%2F%20Squirrel-1f6feb.svg)
![dependencies: 0](https://img.shields.io/badge/dependencies-0-success.svg)

统计基于 Rime（Squirrel）输入法的**汉字上屏速度**（字/分钟，CPM）——衡量的是汉字输出速度，不是键盘敲击速度。

> Measure your real Chinese **output** speed (characters-per-minute) on the [Rime](https://rime.im/) input method. It counts committed characters, not keystrokes. Pure Lua + a zero-dependency Python CLI; no recompiling librime.

## 工作原理

- 一个 librime-lua 处理器 `speed_logger.lua` 监听上屏（commit）事件，每次上屏写一条**不含文字内容**的记录（字数 + 汉字/英文/数字/标点分类计数 + 编码长度 + 方案 id + 时间戳）到
  `~/Library/Application Support/rime-typing-speed/commits.jsonl`（刻意避开会被同步的 `~/Library/Rime/`）。
- 单文件、零依赖的 Python CLI `rspeed` 读取日志，计算活跃/上屏/峰值速度并出报告。

## 安装

需要已启用 librime-lua 的 Squirrel（macOS）。雾凇拼音等带 Lua 脚本的配置即已满足。

```bash
make install      # 把 rspeed / rts 命令软链到 ~/.local/bin
rspeed install    # 写入 Lua、挂载到各启用方案、触发 Squirrel 重新部署
```

之后正常打字即可，日志会自动累积。`rspeed` 是主命令，`rts` 是等价简写。

## 使用

```bash
rspeed today                       # 今日概况（实时）
rspeed report yesterday            # 昨天
rspeed report week                 # 最近 7 天（截止昨天，不含今天）
rspeed report month                # 最近 30 天（截止昨天，不含今天）
rspeed report today                # 今天（详细，含按小时分布）
rspeed report 2026-05-31           # 指定某天
rspeed report --from-ts T --to-ts T   # 自定义时间区间（unix 秒）
rspeed export --csv > out.csv      # 导出明细
rspeed uninstall                   # 卸载（加 --purge 删日志）
```

> `report` 接受位置参数 `today | yesterday | week | month | YYYY-MM-DD`；省略它则回退到 `--day` / `--from-ts/--to-ts`。完整说明见 `rspeed -h` 与 `rspeed report -h`。

## 指标与统计口径

字数口径：统计**所有上屏字符**（汉字、英文、数字、标点，按 Unicode 码点计；汉字数单列）。下面三个速度各回答一个不同的问题，单位都是 **字/分钟**。

**记账规则**：每次上屏的字数，归属到「以这次上屏结束的那段间隔」。一段连续输入 / 会话 / 窗口里的**第一次上屏只贡献时间、不贡献字数**（它之前没有间隔，无从算速度）。
**默认参数**：空闲阈值 `5s`、会话间隔 `5min`、峰值窗口 `60s`。

### 活跃速度（头条）— 你真在打字时有多快

只把相邻两次上屏间隔 **≤ 5 秒**的算作「在打字」：

```
活跃速度 = Σ(间隔≤5s 的上屏字数) / Σ(这些间隔的秒数) × 60
```

间隔 > 5 秒视为停顿，那段时间和字都不计入。剔除了发呆/思考，反映纯手速。

### 上屏速度 — 含思考停顿的真实吞吐

先按「间隔 > 5 分钟」把记录切成若干会话，每个会话：

```
会话字数 = 该会话里「除第一次外」所有上屏的字数
会话时长 = 末次时间戳 − 首次时间戳
上屏速度 = Σ会话字数 / Σ会话时长 × 60
```

包含会话内的阅读/思考停顿，反映「一段时间里实际产出多少字」，通常明显低于活跃速度。

### 峰值速度 — 你能持续的最快手速

一个 60 秒窗口在整段记录上滑动，取最高的一段：

```
某窗口速度 = 窗口内「除首次外」的字数 / 窗口跨度秒数 × 60
峰值速度   = max(所有窗口速度)
```

这是唯一能和「打字测试」结果类比的口径（测试本质就是一段爆发）。

### 输入效率（码长）— 每字敲几键

```
输入效率 = Σ每次上屏的编码长度 / Σ字数        （击键/字）
```

即平均码长。双拼理想约 2；用词组/整句上屏会更低，全拼更高。

> ⚠️ 时间戳为**秒级**：同一秒内多次上屏的间隔为 0，不计入活跃/峰值，因此极快的爆发会被低估（长期会被平均掉）。要让峰值精确对标打字测试，需要毫秒级时间戳。

## 隐私

日志**只记数量、分类计数、编码长度、方案、时间戳，绝不记录你打过的任何文字内容**。数据全部留在本机。

## 局限

- 仅统计经 Rime compose 上屏的字符；纯英文 ASCII 直通模式打的字不计入。
- 时间戳为秒级：手速很快（同一秒内多次上屏）时，活跃速度会偏保守，可视作下限，爆发段以峰值为准。
- 新增输入方案后需重新 `rspeed install` 才会纳入统计。

## 开发

```bash
make dev     # 建 venv 并装 pytest
make test    # 跑测试
```

GPL-3.0-only。
