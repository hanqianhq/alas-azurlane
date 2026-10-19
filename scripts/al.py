# -*- coding: utf-8 -*-
"""al.py — 碧蓝航线 (ALAS + MuMu) 诊断工具
在 D:\\AzurLaneAutoScript 目录下运行。

用法:
  python al.py shot                 截图到 _alas_shot.png (nemu_ipc 通道)
  python al.py alive                连拍两帧算差值, 判断截图帧是否实时 (LIVE/STALE)
  python al.py click X Y            MaaTouch 注入点击 (与调度器同通道)
  python al.py tap X Y              adb input tap 注入
  python al.py back                 发送 BACK 键 (可解挂机锁屏)
  python al.py locate <color>       在截图里像素定位按钮, 输出 bbox 与中心点
      color: orange(橙黄) | blue(亮蓝) | white(纯白) | red(红)
      可选区域参数: locate orange 0.75 1.0 0.8 1.0   (x0 x1 y0 y1, 比例)
"""
import sys, os, time
sys.path.insert(0, '.')
import cv2
import numpy as np

SHOT = '_alas_shot.png'

MASKS = {
    'orange': lambda b, g, r: (r > 200) & (g > 130) & (g < 215) & (b < 110),
    'blue':   lambda b, g, r: (b > 200) & (r < 120) & (g > 100) & (g < 210),
    'white':  lambda b, g, r: (r > 230) & (g > 230) & (b > 230),
    'red':    lambda b, g, r: (r > 190) & (g < 90) & (b < 90),
}


def get_device():
    from module.config.config import AzurLaneConfig
    from module.device.device import Device
    c = AzurLaneConfig('alas')
    return Device(c)


def cmd_shot():
    d = get_device()
    img = d.screenshot()
    cv2.imwrite(SHOT, img)
    print('SHOT', img.shape)


def cmd_alive():
    d = get_device()
    a = d.screenshot()
    cv2.imwrite('_alas_a.png', a)
    time.sleep(6)
    d = get_device()
    b = d.screenshot()
    diff = np.abs(a.astype(int) - b.astype(int)).mean()
    print('FRAME DIFF: %.3f -> %s' % (diff, 'LIVE' if diff > 0.5 else 'STALE'))


def cmd_click(x, y):
    d = get_device()
    d.click_maatouch(int(x), int(y))
    print('CLICKED %s %s' % (x, y))


def cmd_tap(x, y):
    import subprocess
    adb = r'D:\AzurLaneAutoScript\toolkit\Lib\site-packages\adbutils\binaries\adb.exe'
    subprocess.run([adb, 'connect', '127.0.0.1:16416'], capture_output=True)
    subprocess.run([adb, '-s', '127.0.0.1:16416', 'shell', 'input', 'tap', str(x), str(y)])
    print('TAPPED %s %s' % (x, y))


def cmd_back():
    import subprocess
    adb = r'D:\AzurLaneAutoScript\toolkit\Lib\site-packages\adbutils\binaries\adb.exe'
    subprocess.run([adb, 'connect', '127.0.0.1:16416'], capture_output=True)
    subprocess.run([adb, '-s', '127.0.0.1:16416', 'shell', 'input', 'keyevent', '4'])
    print('BACK sent')


def cmd_locate(color, x0=0.0, x1=1.0, y0=0.0, y1=1.0):
    img = cv2.imread(SHOT)
    if img is None:
        print('no screenshot, run `al.py shot` first')
        return
    h, w = img.shape[:2]
    x0i, x1i, y0i, y1i = int(w * x0), int(w * x1), int(h * y0), int(h * y1)
    region = img[y0i:y1i, x0i:x1i]
    b, g, r = region[:, :, 0].astype(int), region[:, :, 1].astype(int), region[:, :, 2].astype(int)
    mask = MASKS[color](b, g, r)
    ys, xs = np.where(mask)
    if not len(xs):
        print('NOT FOUND (%s in region)' % color)
        return
    bx0, bx1 = xs.min() + x0i, xs.max() + x0i
    by0, by1 = ys.min() + y0i, ys.max() + y0i
    print('bbox: (%d, %d, %d, %d) center: (%d, %d) pixels: %d'
          % (bx0, by0, bx1, by1, (bx0 + bx1) // 2, (by0 + by1) // 2, len(xs)))


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    cmd = args[0]
    if cmd == 'shot':
        cmd_shot()
    elif cmd == 'alive':
        cmd_alive()
    elif cmd == 'click':
        cmd_click(args[1], args[2])
    elif cmd == 'tap':
        cmd_tap(args[1], args[2])
    elif cmd == 'back':
        cmd_back()
    elif cmd == 'locate':
        region = [float(v) for v in args[2:6]] if len(args) >= 6 else [0.0, 1.0, 0.0, 1.0]
        cmd_locate(args[1], *region)
    else:
        print('unknown command:', cmd)
        print(__doc__)


if __name__ == '__main__':
    main()
