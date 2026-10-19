# 游戏运营：练级 / 收菜 / 故障处置

## 任务全家桶（当前启用）

| 任务 | 作用 | 备注 |
|---|---|---|
| Commission | 委托派船/收菜 | cube 过滤器，4 槽 |
| Research | 科研自动启停 | S9 过滤器 series_9_blueprint_ta152；**队列满会连败崩溃**——用户手动停一个项目腾位后恢复 |
| Reward | 领奖（油/币/经验/任务） | 按资源积累速率触发，间隔不用太短 |
| Tactical | 战术学院 | |
| Dorm / Meowfficer / Guild / Freebies | 后宅/猫窝/公会/福利 | 每日性质，ServerUpdate 驱动 |
| Main | 主线出击 | 详见 config-scheduler.md |
| Restart | 每日重启 | NextRun 对齐 00:00 |

## 10-1 刷级模式（当前策略）

第二舰队（Lv21-52）打不动 10-3，先刷已通关的 10-1 带练：
- `Main.Campaign.Name = "10-1"`，`StageIncrease = false`
- 正常节奏：进场 → 自动索敌 4-5 场战斗 → 每场 1-1.5 分钟 → 掉落拾取 → 油耗 ~30/场
- 心情自动管理（calculate + 后宅恢复），111→103 属正常
- 下一场触发 = SuccessInterval 随机（10-40 分钟）

**推 10-3 的前提**：两支舰队都要能活。等第二队练度上来（或用户手动调装备/编队）再切回 `Name: "10-3"` + `StageIncrease: true`。

## 船坞满与退役（已踩平的坑）

**触发链**：战斗掉落新船 → 船坞满(538/538) → 游戏弹窗 → ALAS 一键退役 → 若选不出船 → `CRITICAL No ship retired / Request human takeover` → 调度器自杀退出。

**退役设置（游戏内，已调好，改动需用户确认）**：
- 唯一舰船退役保护 = 关（开=保护所有单拷贝船，会卡死一键退役）
- 「拥有/没有满星同名舰船时」= 不保留
- 优先级 1=R（蓝）、2=无、3=N（白）；**SR 不参与**（曾误勾 SR，确认框会警告"有精锐以上角色"——看到这个警告立即取消）

**船坞空位不足时**：练级每次掉落都会再触发。解法：钻石扩容（一次+5 位，递增计费）或用户手动退役 SR 重复。

## 错误语义与处置

| 日志错误 | 含义 | 处置 |
|---|---|---|
| `GameTooManyClickError` | 同一按钮连点过多（通常是加载/状态卡住） | 自恢复，重试即可，连续出现才深查 |
| `GameStuckError: Wait too long` | 等待超时（战斗无进展等） | 看错误快照 png：若是「全军覆没 D 评级」→ 练度问题，停 Main |
| `Game page unknown` / `Please switch to a supported page` | 启动时游戏停在 ALAS 不认识的页面（战败结算、登出界面等） | 手动截图 → 关弹窗/BACK → 回主页面 → 重启调度器 |
| `ConnectionAbortedError 10053` | adb 连接被杀 | 重连重启，无碍 |
| `Research: Unable to start a research project after 3 trial` | S9 科研队列满 | 让用户停一个项目腾位 |
| `Request human takeover` | 设计上需要人 | **必须人工介入**，查明原因再恢复 |

**全军覆没特征**：错误快照 png 是 D 评级/DEFEAT 结算页。连续两次 = 舰队打不过该图，不要硬重试（烧油+白费），改策略（降级刷低章/用户调装备）。

## 监控节奏（常规巡检）

```bash
# 最近任务流转
tail -30 log/<日期>_alas.txt | grep -E "(Task|Start task|End task|Delay|ERROR)"
# 错误快照
ls -t log/error/ | head -3
# 各任务 NextRun
./toolkit/python.exe -c "import json; d=json.load(open(r'config\alas.json',encoding='utf-8')); [print(k, d[k]['Scheduler']['NextRun']) for k in d if 'Scheduler' in d.get(k,{}) and d[k]['Scheduler'].get('Enable')]"
```

发现长间隔（>1h）无日志 → 查进程是否还活着、模拟器是否锁屏/掉线。

## 人工介入接口

用户可手动进模拟器操作，但必须**先停调度器**（否则人机抢输入互卡）。交接话术：停进程 → 告知用户随便操作 → 用户完成后重启。
