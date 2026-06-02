# rime-typing-speed

统计基于 Rime（Squirrel）输入法的**汉字上屏速度**（字/分钟，CPM）——衡量的是汉字输出速度，不是键盘敲击速度。

> Measure your real Chinese **output** speed (characters-per-minute) on the [Rime](https://rime.im/) input method. It counts committed characters, not keystrokes. Pure Lua + a zero-dependency Python CLI; no recompiling librime.

## 工作原理

- 一个 librime-lua 处理器 `speed_logger.lua` 监听上屏（commit）事件，每次上屏写一条**不含文字内容**的记录（字数 + 汉字/英文/数字/标点分类计数 + 编码长度 + 方案 id + 时间戳）到
  `~/Library/Application Support/rime-typing-speed/commits.jsonl`（刻意避开会被同步的 `~/Library/Rime/`）。
- 单文件、零依赖的 Python CLI `rspeed` 读取日志，计算净/毛/峰值速度并出报告。

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

## 指标说明

- **净速度（头条）**：剔除超过 5 秒的停顿后的真实手速。
- **毛速度**：含思考停顿的整体速度。
- **峰值速度**：最佳 60 秒窗口速度。
- **码字效率**：字/击键。

## 隐私

日志**只记数量、分类计数、编码长度、方案、时间戳，绝不记录你打过的任何文字内容**。数据全部留在本机。

## 局限

- 仅统计经 Rime compose 上屏的字符；纯英文 ASCII 直通模式打的字不计入。
- 时间戳为秒级：手速很快（同一秒内多次上屏）时，净速度会偏保守，可视作下限，爆发段以毛速度/峰值为准。
- 新增输入方案后需重新 `rspeed install` 才会纳入统计。

## 开发

```bash
make dev     # 建 venv 并装 pytest
make test    # 跑测试
```

GPL-3.0-only。
