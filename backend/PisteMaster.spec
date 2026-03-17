# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PisteMaster backend

Build command:
    pyinstaller PisteMaster.spec --noconfirm --clean

Output:
    dist/pistemaster-backend.exe (Windows)
    dist/pistemaster-backend (Linux/macOS)
"""

import sys
from pathlib import Path

block_cipher = None

backend_dir = Path('.').resolve()

a = Analysis(
    ['run_desktop.py'],
    pathex=[str(backend_dir)],
    binaries=[],
    datas=[
        ('PisteMaster/settings', 'PisteMaster/settings'),
    ],
    hiddenimports=[
        'django',
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'rest_framework',
        'corsheaders',
        'django_filters',
        'backend.apps.fencing_organizer',
        'core',
        'PisteMaster.settings',
        'PisteMaster.settings.base',
        'PisteMaster.settings.development',
        'PisteMaster.settings.production',
        'PisteMaster.settings.desktop',
    ],
    hookspath=['./hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'test',
        'tests',
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
    name='pistemaster-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  
    console=True,  
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='pistemaster-backend',
)