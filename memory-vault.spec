# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\asahi\\projects\\memory-vault\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\asahi\\projects\\memory-vault\\credentials/*', 'memory-vault/credentials')],
    hiddenimports=['google.auth.transport.requests'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='memory-vault',
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
    uac_admin=True,
    icon=['C:\\Users\\asahi\\projects\\memory-vault\\ico\\memory-vault.ico'],
)
