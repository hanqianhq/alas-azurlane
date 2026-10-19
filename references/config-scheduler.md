# 配置与调度机制（alas.json）

## 参数类型决定改法

| 类型 | 行为 | 例子 |
|---|---|---|
| `lock` | **每次加载都重置回默认 True**，改了没用 | `Scheduler.Enable`（被 `config.py` 的 `force_enable(["Commission","Research","Reward"])` 强制启用） |
| `datetime` | 可自由改，持久 | `Scheduler.NextRun`（推后/提前任务全靠它） |
| `input` | 可自由改，持久 | `SuccessInterval` / `FailureInterval` |

经验：想"禁用"一个被 force_enable 的任务 → 不是改 Enable，而是把 NextRun 推到远期（如 `2099-01-01`）。

## 间隔参数支持区间字符串（随机化）

`module/config/utils.py` 的 `ensure_time()`：
- 整数 `30` → 固定值（死板，指纹明显）
- `"30-60"` → **正态分布抽样**（采 3 次取均值），比均匀随机更像人类
- 想更"人类"：不对称、非整十的边界，如 `"23-77"`、`"97-243"`

已知坑：**任务失败路径会把 interval 回写成默认值 0/120**（原因未深查）。改完 interval 后如被回写，重改即可。

## 安全修改流程（必须完整走）

1. **停进程**（gui.py 内存配置会回写覆盖文件改动！）：
   ```powershell
   Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Where-Object { $_.CommandLine -match 'alas.py|gui.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
   ```
2. **备份**：`cp config/alas.json "config/alas.json.bak-$(date +%Y%m%d-%H%M%S)"`
3. Edit 修改（先用 Grep 读最新内容——调度器可能在文件里写过 Emotion/NextRun）
4. **JSON 校验 + 打印改动**：
   ```bash
   ./toolkit/python.exe -c "import json; d=json.load(open(r'config\alas.json', encoding='utf-8')); print(d['Main'])"
   ```
5. 重启 gui.py + alas.py（后台任务）
6. 查日志确认无解析错误、任务正常排队

## 任务结构速览

每个任务 = 一个顶层 key（`Commission`/`Research`/`Main`/`Event`/`Dorm`/`Guild`/`Reward`/`Meowfficer`/`Freebies`/`Tactical`…），内含：

```json
"Scheduler": { "Enable", "NextRun", "SuccessInterval", "FailureInterval", "ServerUpdate" }
```

- `ServerUpdate`：到点强制触发的服务器刷新时间（如 Guild `"00:00, 06:00, 12:00, 18:00, 21:00"`）
- 任务实际触发时间 = max(NextRun, 间隔随机值)，由调度器 `Delay task` 写回

## 主线出击（Main 模块）关键参数

```json
"Campaign": { "Name": "10-1", "Mode": "normal", "UseAutoSearch": true, "UseFleetLock": true }
"StopCondition": { "OilLimit": 1000, "MapAchievement": "non_stop", "StageIncrease": false }
"Fleet": { "Fleet1": 1, "Fleet2": 2, "FleetOrder": "fleet1_mob_fleet2_boss" }
"Emotion": { "Mode": "calculate", "Fleet1Control": "prevent_green_face", "Fleet1Recover": "not_in_dormitory" }
```

- **练级模式**：`Name` 设已通关的低章（如 10-1），`StageIncrease: false`（true 会通关后自动跳下一关）
- **推图模式**：`Name` 设当前关卡，`StageIncrease: true` 自动推进
- `OilLimit`：石油低于此值停止出击（防烧穿）
- 心情由 `Emotion` 自动计算与暂停，后宅恢复

## 当前账号状态（2026-10-19）

- 进度：第 10 章科隆班加岛夜战，10-1/10-2 已通，**10-3 未过**
- 第二舰队练度不足（Lv21-52），10-3 全军覆没 ×2 → 策略=10-1 刷级
- 石油 ~21000，钻石 ~90000（充足）
- 退役设置已调好：保护关、同名重复不保留、优先级 R/无/N（SR 不参与退役）
- 船坞 534/538 接近满，用户选择手动清 SR 重复
