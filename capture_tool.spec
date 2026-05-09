# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件
用于将 Playwright 抓包工具打包为单个 EXE 文件

打包命令：
    pyinstaller capture_tool.spec

注意：需要在 32 位 Python 环境下执行打包，才能生成 32 位 EXE
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 项目根目录
PROJECT_DIR = os.path.abspath('.')

# 收集 playwright 相关数据文件
playwright_datas = collect_data_files('playwright')
greenlet_datas = collect_data_files('greenlet')

a = Analysis(
    [os.path.join(PROJECT_DIR, 'main.py')],
    pathex=[PROJECT_DIR],
    binaries=[],
    datas=playwright_datas + greenlet_datas,
    hiddenimports=[
        'playwright',
        'playwright.sync_api',
        'greenlet',
        'greenlet._greenlet',
        'typing_extensions',
        'pyee',
        'pyee.base',
        'json',
        'tkinter',
        '_tkinter',
        'unittest',
        'importlib',
        'importlib.abc',
        'importlib.metadata',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PlaywrightCapture',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口（GUI 程序）
    icon=None,      # 可以设置图标路径，如 'icon.ico'
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,  # 由 Python 解释器的位数决定（32位 Python = 32位 EXE）
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PlaywrightCapture',
)
