# -*- mode: python ; coding: utf-8 -*-

import pkg_resources
import sys

template_dir = pkg_resources.resource_filename('settings_doc', 'templates')

a = Analysis(
    ['ktoolbox/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        (template_dir + '/*', 'settings_doc/templates'),
    ],
    hiddenimports=['winloop._noop'] if sys.platform == 'win32' else [],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ktoolbox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
