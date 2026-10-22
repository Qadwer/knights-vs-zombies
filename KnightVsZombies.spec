# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for Knight vs Zombies (Рыцарь против Зомби).
Builds a standalone, single-file Windows executable with embedded assets and icon.
"""

import os

block_cipher = None

datas = []
if os.path.exists('assets'):
    datas.append(('assets', 'assets'))

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'pygame',
        'pydantic',
        'pydantic_settings',
        'pydantic.deprecated.decorator',
        'pydantic_core',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy.tests', 'unittest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='KnightVsZombies',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/app_icon.ico' if os.path.exists('assets/app_icon.ico') else None,
)

