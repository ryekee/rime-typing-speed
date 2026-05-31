# rime-speed

统计基于 Rime（Squirrel）输入法的**汉字上屏速度**（字/分钟）——衡量的是汉字输出速度，不是键盘敲击速度。

## 工作原理

- 一个 librime-lua 处理器 `speed_logger.lua` 监听上屏事件，每次上屏写一条**不含文字内容**的记录（数量 + 分类计数 + 编码长度 + 方案 id + 时间戳）到
  `~/Library/Application Support/rime-speed/commits.jsonl`（刻意避开 iCloud 同步的 `~/Library/Rime/`）。
- 单文件、零依赖的 Python CLI `rime-speed` 读取日志，计算净/毛/峰值速度并出报告。

## 安装

```bash
make dev        # 开发环境
pipx install .  # 安装 rime-speed 命令
rime-speed install        # 写入 Lua、挂载到各方案、部署
```

## 使用

```bash
rime-speed today                       # 今日统计
rime-speed report --day 2026-05-31     # 指定日期
rime-speed report --from-ts T --to-ts T
rime-speed export --csv > out.csv      # 导出
rime-speed uninstall                   # 卸载（加 --purge 删日志）
```

## 指标说明

- **净速度（头条）**：剔除超过 5 秒的停顿后的真实手速。
- **毛速度**：含思考停顿的整体速度。
- **峰值速度**：最佳 60 秒窗口速度。
- **码字效率**：字/击键。

## 局限

仅统计经 Rime compose 上屏的字符；纯英文 ASCII 直通模式打的字不计入。时间戳为秒级。

GPL-3.0。
