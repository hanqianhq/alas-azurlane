# 设备 IO：截图 / 注入 / 坐标（本 Skill 最容易翻车的地方）

## 截图：只用 nemu_ipc，禁用 adb screencap

- `adb exec-out screencap -p` 在 MuMu 12 上抓到的是错误 display（安卓桌面/锁屏），**不可信**
- 正确方式：ALAS Device 层的 `d.screenshot()`（nemu_ipc），用 `scripts/al.py shot` 或 `_alas_ui.py`
- 产物 `_alas_shot.png`，实际分辨率 1280×720

### 过期帧陷阱（重要！）

**调度器活着时**，自己的脚本再开一个 nemu_ipc 客户端，拿到的可能是**过期帧**（画面停在很久以前）。症状：截图显示某个页面，实际游戏早不在那了，对着截图点按钮全部"无效"。

验证方法（`al.py alive`）：连拍两帧算像素差：
- `diff > 0.5` → LIVE，可信
- `diff ≈ 0` → **STALE，必须先停调度器**（或重启模拟器）再操作

经验法则：**任何"点击无效"的排查，第一步先 alive 验帧**。

## 注入通道优先级

1. **MaaTouch**（与调度器同款）：`d.click_maatouch(x, y)`，需要 Device 初始化（在 `D:\AzurLaneAutoScript` 目录下跑）
2. **adb input tap**：备用；注意 daemon 每次调用可能已死，先 `adb connect`
3. `d.click(button)` 不接受裸坐标（要 Button 资产对象），裸坐标用 `click_maatouch`
4. uiautomator2 通道慢且不比 MaaTouch 可靠，不优先

**BACK 键是万能后手**：`input keyevent 4` 不受锁屏/部分 UI 限制，能关公告、退弹窗、解挂机锁屏。

## 坐标：严禁目测换算

**Read 工具显示的截图是缩放过的，缩放比例还不固定**——目测坐标换算连续翻车过一整个下午。

铁律：**所有按钮坐标用 cv2 像素定位**（`al.py locate <color> [x0 x1 y0 y1]`）：

```bash
# 例：在右下 25% 区域找橙色「出击」按钮
python al.py locate orange 0.75 1.0 0.55 0.85
# 输出: bbox: (1127, 434, 1261, 539) center: (1194, 486)
```

已知坐标参考（1280×720）：
- 主页面「出击」橙按钮：(1194, 486)
- 主页面「编队」：(1065, 505) 附近
- 主页面左侧奖励入口：(15, 233)
- 船坞退役页「退役设置」齿轮：(38, 519)
- 登录页进游戏：屏幕中心 (640, 360)
- ALAS 资产按钮：查 `log` 里 `Click (x, y) @ BUTTON_NAME` 的历史记录，直接复用

## MuMu 挂机锁屏（最大坑）

现象：截图变成大时钟+日期+电量画面；所有 tap 注入被吞（截图/BACK 正常）。
本质：Android keyguard（闲置超时锁屏）。
- 解除：`input keyevent 4`
- 永久禁用：`settings put global stay_on_while_plugged_in 7` + `screen_off_timeout 600000`
- 模拟器重启后要复查

## 诊断流程（点不动时的标准排查链）

1. `al.py alive` → 帧是 STALE？→ 停调度器重来
2. 画面是锁屏？→ `al.py back`
3. 坐标是目测的？→ `al.py locate` 像素重定位
4. 换通道试：maatouch → adb tap → BACK 键
5. 都不行 → `MuMuManager control -v 1 restart` 重启模拟器（60s），一招解决所有玄学
