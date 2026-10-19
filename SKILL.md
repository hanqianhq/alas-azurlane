---
name: alas-azurlane
description: 碧蓝航线自动化运维 Skill。当用户要求推进/查看/修复碧蓝航线挂机（ALAS + MuMu 12 模拟器环境）、或提到"碧蓝航线""ALAS""挂机游戏推进""委托/科研/出击/练级"时使用。涵盖：调度器启停、alas.json 安全修改、截图与输入注入的正确姿势、常见故障（锁屏吞输入/过期帧/船坞满/战败循环）处置。其他模拟器手游的 AL 系脚本环境也可参考其方法论。
agent_created: true
---

# 碧蓝航线自动化运维（ALAS + MuMu 12）

在已有环境上运维与推进碧蓝航线自动化：收菜任务（委托/科研/后宅等）与出击任务（主线/练级）。

## 环境一览

- ALAS：`D:\AzurLaneAutoScript\`（自带 toolkit python 与 adb）
- 配置：`config\alas.json`；日志：`log\<日期>_alas.txt`
- 模拟器：MuMu 12，adb `127.0.0.1:16416`，管理器 `D:\MuMu\nx_main\MuMuManager.exe`
- WebUI：`http://127.0.0.1:22267`（用 gui.py + 浏览器，Electron 壳不可用）
- 诊断工具：把本 Skill 的 `scripts/al.py` 复制到 `D:\AzurLaneAutoScript\` 下运行（截图/存活检测/注入/像素定位）

详细路径、进程模型、启动停止命令见 `references/environment.md`。

## 标准工作流

### 1. 查状态（先核对再动手）

```bash
# 进程活着吗
powershell: Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Select CommandLine
# 最近任务流转
tail -30 log/<日期>_alas.txt | grep -E "(Task|Start task|End task|Delay|ERROR)"
```

### 2. 截图看画面（顺序很重要）

```bash
python al.py alive   # 先验帧：STALE 说明调度器占着 nemu_ipc，须先停它
python al.py shot    # 再截图 → _alas_shot.png (1280x720)
```

**铁律**：画面是锁屏/桌面 → `al.py back` 解锁；坐标严禁目测（Read 显示的是缩放图），必须 `al.py locate` 像素定位。详见 `references/device-io.md`。

### 3. 改配置（五步缺一不可）

停进程 → 备份 → Edit（先 Grep 读最新内容）→ JSON 校验 → 重启。gui.py 会用内存配置回写覆盖文件，跳过第一步必被坑。调度器参数类型（lock/datetime/input）、间隔随机化、Main 出击模块详解见 `references/config-scheduler.md`。

### 4. 重启与验证

```bash
cd /d/AzurLaneAutoScript && ./toolkit/python.exe gui.py        # 后台
cd /d/AzurLaneAutoScript && ./toolkit/python.exe alas.py alas  # 后台
# 25s 后 tail 日志：应见 MaaTouch connected + page_main + 无 ERROR
```

## 高频故障速查

| 症状 | 处置 |
|---|---|
| 点击全部无效 | ① alive 验帧（大概率 STALE）② 查锁屏 ③ locate 重定位坐标 ④ 换注入通道 |
| 画面变时钟锁屏 | `al.py back` 解锁；根治：`settings put global stay_on_while_plugged_in 7` |
| 日志 `Game page unknown` | 游戏停在 ALAS 不认识的页面（战败结算等），手动关弹窗回主页面再启动 |
| `Request human takeover` | 人工介入：看 `log/error/<时间戳>/` 快照定位原因 |
| 战败 D 评级快照 | 舰队练度不足，别硬重试，降级刷低章或让用户调装备/编队 |
| 船坞满 + 退役选 0 船 | 游戏内退役设置被保护规则卡住，见 `references/gameplay-ops.md` |

## 用户交互约定

- 让用户手动进游戏操作前，**必须先停调度器**（人机抢输入互卡），完成后由 AI 重启
- 花钻石/退役船等涉及账号资产的操作，先问用户
- 后台任务随 WorkBuddy 会话结束而停——告知用户这是"人类离线空窗"，属正常现象

## 参考文档

- `references/environment.md` — 路径/进程/启停/模拟器管理
- `references/config-scheduler.md` — 参数类型、安全改配置流程、Main 模块、当前账号状态
- `references/device-io.md` — 截图/注入/坐标三大坑与标准排查链
- `references/gameplay-ops.md` — 任务全家桶、练级/推图策略、错误语义、巡检方法
