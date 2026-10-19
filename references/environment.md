# 环境与进程

## 路径与端口（本机）

| 项 | 值 |
|---|---|
| ALAS 安装目录 | `D:\AzurLaneAutoScript\`（git 仓库，可 git_over_cdn 更新） |
| 配置文件 | `D:\AzurLaneAutoScript\config\alas.json` |
| 日志 | `D:\AzurLaneAutoScript\log\<日期>_alas.txt`（调度器）、`<日期>_gui.txt`（WebUI） |
| 错误快照 | `D:\AzurLaneAutoScript\log\error\<时间戳>\`（含 log.txt + 现场 png） |
| 内置 Python | `D:\AzurLaneAutoScript\toolkit\python.exe`（所有 ALAS 相关脚本用它跑） |
| ALAS 自带 adb | `D:\AzurLaneAutoScript\toolkit\Lib\site-packages\adbutils\binaries\adb.exe`（v29） |
| MuMu 12 模拟器 | `D:\MuMu\`，管理器 `D:\MuMu\nx_main\MuMuManager.exe` |
| 模拟器 adb 地址 | `127.0.0.1:16416`（实例 index=1，名为「碧蓝航线-1」） |
| WebUI | `http://127.0.0.1:22267`（Electron 壳 AlasApp 在本机秒崩，用 gui.py + 浏览器替代） |
| 诊断脚本 | `D:\AzurLaneAutoScript\_alas_ui.py`（无参数=截图，两参数=点击）；Skill 里的 `scripts/al.py` 是增强版 |

## 进程模型

- `gui.py`：WebUI 后端。**它把配置持有在内存中并会回写**——直接改 config 文件必须先停它
- `alas.py alas`：调度器主循环，按各任务 NextRun 轮转
- 每个任务运行时还有 multiprocessing 子进程
- 查进程：`Get-CimInstance Win32_Process -Filter "Name like 'python%'"`，按 CommandLine 区分
- **后台任务生命周期**：WorkBuddy 会话结束后托管后台任务会停 → 调度器随之停摆（这反而制造了"人类离线"的自然空窗，可接受）

## 启动 / 停止

```powershell
# 停止（全部 python 进程，或按 CommandLine 过滤）
Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Where-Object { $_.CommandLine -match 'alas.py|gui.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

启动：在 WorkBuddy 中用 `run_in_background: true` 分别跑：

```bash
cd /d/AzurLaneAutoScript && ./toolkit/python.exe gui.py
cd /d/AzurLaneAutoScript && ./toolkit/python.exe alas.py alas
```

启动后 ~25s 检查 `log\<日期>_alas.txt` 尾部：应看到 nemu_ipc + MaaTouch 连接成功、到达 `page_main`、无 ERROR。

## 模拟器管理

```bash
"/d/MuMu/nx_main/MuMuManager.exe" info -v 1          # 状态（player_state=start_finished 为就绪）
"/d/MuMu/nx_main/MuMuManager.exe" control -v 1 restart  # 重启实例（~60s），解决一切玄学状态
```

- 重启后 adb 端口可能仍是 16416；`adb connect 127.0.0.1:16416` 重连
- 游戏启动：`adb shell am start -n com.bilibili.azurlane/com.manjuu.azurlane.MainActivity`
- **MuMu 锁屏（挂机 keyguard：大时钟+日期+电量）会吞掉所有触摸注入**。已永久禁用（见下）。若重现：`input keyevent 4`（BACK）可解

## 必须保持的模拟器设置

```bash
adb shell settings put global stay_on_while_plugged_in 7   # 插电永不休屏（关键！防锁屏吞输入）
adb shell settings put system screen_off_timeout 600000    # 兜底 10 分钟
```

模拟器重启后需重查这两项（global stay_on_while_plugged_in 可持久，svc power stayon 不能）。

## adb 稳定性

- adb server 会随调度器进程死亡而消失（每次 Bash 调用开头都要 `adb connect`）
- 沙箱内 daemon 易被回收；输入注入类命令必要时用非沙箱模式
- MuMu 的 adb 与 ALAS 的 adb 版本冲突会互杀 5037：MuMu 的 `D:\MuMu\nx_main\adb.exe` 已被替换为 ALAS 的 v29（备份 `adb.exe.bak`），不要改回去
- `adb screencap` 在 MuMu 12 上抓到的可能不是游戏画面（多显示器坑），**一律用 nemu_ipc 截图**
