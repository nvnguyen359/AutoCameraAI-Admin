# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_submodules

sys.path.insert(0, os.path.abspath('.'))

hidden_modules = collect_submodules('app')
hidden_modules.extend([
    'app.main_core',
    'app.api',
    'app.services',
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'uvicorn.lifespan.off',
    'fastapi',
    'starlette',
    'webview',
    'webview.platforms.edgechromium',
    'webview.platforms.mshtml',
    'clr',
    'pystray',
    'PIL',
    'PIL.Image',
])

datas = []
if os.path.exists('client'):
    datas.append(('client', 'client'))
if os.path.exists('loading.html'):
    datas.append(('loading.html', '.'))
if os.path.exists('version.txt'):
    datas.append(('version.txt', '.'))
if os.path.exists('icon.ico'):
    datas.append(('icon.ico', '.'))

icon_file = os.path.abspath('icon.ico') if os.path.exists('icon.ico') else None

a = Analysis(
    ['run_desktop.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_modules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'torchvision', 'torchaudio', 'tensorflow', 'scipy', 'matplotlib', 'sympy', 'sklearn', 'IPython', 'pytest'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AutoCameraAI-Admin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='AutoCameraAI-Admin',
)
