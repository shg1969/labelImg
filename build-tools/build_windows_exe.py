#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 labelImg 打包成可双击运行的 Windows 可执行文件。

用法（在任意目录执行都可以）：

    python build-tools/build_windows_exe.py

脚本会依次完成：

  1. 检查 PyQt5 / lxml 是否可用；缺少 PyInstaller 时自动安装；
  2. 调用 pyrcc5 重新生成 libs/resources.py（保证多语言字符串是最新的）；
  3. 如果 resources/icons/app.ico 不存在，就由 app.png 生成（需要 Pillow，可选）；
  4. 调用 PyInstaller 打包，最后打印 exe 路径。

可选参数：

    --console   保留黑色控制台窗口（排查启动报错时有用，默认不显示控制台）
    --onedir    打包成文件夹而不是单个 exe（启动更快，但不是单文件）
    --no-clean  不清理上一次的 build/ 与 dist/

产物默认位于项目根目录的 dist/ 下。
"""

import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_NAME = 'labelImg'
ENTRY = os.path.join(ROOT, 'labelImg.py')
QRC = os.path.join(ROOT, 'resources.qrc')
RESOURCES_PY = os.path.join(ROOT, 'libs', 'resources.py')
ICON_PNG = os.path.join(ROOT, 'resources', 'icons', 'app.png')
ICON_ICO = os.path.join(ROOT, 'resources', 'icons', 'app.ico')
DIST_DIR = os.path.join(ROOT, 'dist')
BUILD_DIR = os.path.join(ROOT, 'build')
SPEC_FILE = os.path.join(ROOT, APP_NAME + '.spec')

# 需要一起打包进 exe 的运行时数据（脚本内通过 __file__ 相对路径读取）
DATA_DIR = 'data'


def log(message):
    print('[build] %s' % message, flush=True)


def die(message):
    print('[错误] %s' % message, file=sys.stderr, flush=True)
    sys.exit(1)


def run(cmd):
    log('执行: %s' % ' '.join('"%s"' % c if ' ' in c else c for c in cmd))
    return subprocess.call(cmd, cwd=ROOT)


def has_module(module):
    """在独立进程里探测模块，避免污染当前解释器。"""
    return subprocess.call(
        [sys.executable, '-c', 'import %s' % module],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0


def ensure_dependencies():
    for module, package in (('PyQt5', 'pyqt5'), ('lxml', 'lxml')):
        if not has_module(module):
            die('缺少 %s，请先执行: "%s" -m pip install %s'
                % (module, sys.executable, package))

    if not has_module('PyInstaller'):
        log('未检测到 PyInstaller，正在安装...')
        run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pyinstaller'])
        if not has_module('PyInstaller'):
            die('PyInstaller 安装失败，请手动执行: "%s" -m pip install pyinstaller'
                % sys.executable)
        log('PyInstaller 安装完成')


def find_pyrcc():
    """返回调用 pyrcc5 的命令前缀，找不到时返回 None。"""
    if has_module('PyQt5.pyrcc_main'):
        return [sys.executable, '-m', 'PyQt5.pyrcc_main']

    exe_dir = os.path.dirname(sys.executable)
    for name in ('pyrcc5.exe', 'pyrcc5'):
        candidate = os.path.join(exe_dir, 'Scripts', name)
        if os.path.isfile(candidate):
            return [candidate]

    found = shutil.which('pyrcc5')
    return [found] if found else None


def build_resources():
    pyrcc = find_pyrcc()
    if pyrcc is None:
        die('未找到 pyrcc5，请确认 PyQt5 安装完整')
    log('生成 Qt 资源文件 libs/resources.py')
    if run(pyrcc + ['-o', RESOURCES_PY, QRC]) != 0:
        die('pyrcc5 执行失败')
    if not os.path.isfile(RESOURCES_PY):
        die('资源文件未生成: %s' % RESOURCES_PY)


def build_icon():
    """用 app.png 生成多尺寸 app.ico；缺少 Pillow 时返回 None（不影响打包）。"""
    if os.path.isfile(ICON_ICO):
        return ICON_ICO
    try:
        from PIL import Image
    except ImportError:
        log('未安装 Pillow，跳过程序图标生成（不影响打包）')
        return None
    log('由 app.png 生成 resources/icons/app.ico')
    image = Image.open(ICON_PNG)
    image.save(ICON_ICO, sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                                (64, 64), (128, 128), (256, 256)])
    return ICON_ICO


def clean_previous_build():
    for path in (BUILD_DIR, DIST_DIR):
        if os.path.isdir(path):
            log('清理 %s' % path)
            shutil.rmtree(path, ignore_errors=True)
    if os.path.isfile(SPEC_FILE):
        os.remove(SPEC_FILE)


def build(args):
    cmd = [sys.executable, '-m', 'PyInstaller',
           '--noconfirm',
           '--name', APP_NAME,
           '--onedir' if args.onedir else '--onefile',
           '--console' if args.console else '--windowed',
           '--paths', ROOT,
           '--hidden-import', 'lxml.etree',
           # 让 exe 内仍能通过 __file__/data 找到预设类别文件
           '--add-data', '%s%s%s' % (DATA_DIR, os.pathsep, DATA_DIR)]

    if not args.no_clean:
        cmd.append('--clean')

    icon = build_icon()
    if icon:
        cmd += ['--icon', icon]

    cmd.append(ENTRY)

    if run(cmd) != 0:
        die('PyInstaller 打包失败')


def report(args):
    if args.onedir:
        exe = os.path.join(DIST_DIR, APP_NAME, APP_NAME + '.exe')
        if os.path.isfile(exe):
            log('完成！可双击运行: %s' % exe)
            log('（整个 %s 目录需要一起保留）' % os.path.join(DIST_DIR, APP_NAME))
            return
    else:
        exe = os.path.join(DIST_DIR, APP_NAME + '.exe')
        if os.path.isfile(exe):
            log('完成！可双击运行: %s' % exe)
            log('文件大小: %.1f MB' % (os.path.getsize(exe) / 1024.0 / 1024.0))
            return

    log('打包已结束，但未在 dist 下找到预期产物，请检查 %s' % DIST_DIR)


def main():
    parser = argparse.ArgumentParser(
        description='把 labelImg 打包成可双击运行的 Windows 可执行文件')
    parser.add_argument('--console', action='store_true',
                        help='保留控制台窗口（默认不显示，便于排查问题时使用）')
    parser.add_argument('--onedir', action='store_true',
                        help='打包成文件夹而不是单个 exe（启动更快）')
    parser.add_argument('--no-clean', action='store_true',
                        help='不清理上一次的 build/ 与 dist/')
    args = parser.parse_args()

    if not os.path.isfile(ENTRY):
        die('未找到 %s，请把本脚本放在 labelImg 项目的 build-tools 目录下' % ENTRY)

    log('项目根目录: %s' % ROOT)
    log('使用的解释器: %s' % sys.executable)

    ensure_dependencies()
    if not args.no_clean:
        clean_previous_build()
    build_resources()
    build(args)
    report(args)


if __name__ == '__main__':
    main()
