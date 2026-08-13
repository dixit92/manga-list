# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Manga List application.

Build single-file executable:
    pyinstaller MangaList.spec --clean

Output:
    dist/MangaList.exe  (self-contained, includes data/ directory)
"""

import sys
from pathlib import Path

# Project root
ROOT = Path(SPECPATH).resolve()

block_cipher = None

a = Analysis(
    ['manga_list/__main__.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Include any data files the app needs at runtime
        # The data/ dir is created at runtime, but we ensure parent exists
    ],
    hiddenimports=[
        # PySide6 modules that might be missed by automatic detection
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        # Ensure these are included
        'manga_list.gui.main_window',
        'manga_list.gui.table_model',
        'manga_list.gui.mu_worker',
        'manga_list.gui.detail_panel',
        'manga_list.gui.mu_picker',
        'manga_list.mu_cache',
        'manga_list.mu_client',
        'manga_list.mu_match',
        'manga_list.mu_progress',
        'manga_list.models',
        'manga_list.config',
        'manga_list._version',
        'manga_list.scanner',
        'manga_list.anilist_client',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Reduce size by excluding unnecessary Qt modules
        'PySide6.QtNetwork',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuickWidgets',
        'PySide6.QtSql',
        'PySide6.QtTest',
        'PySide6.QtWebEngine',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebSockets',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DRender',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DExtras',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.QtSerialPort',
        'PySide6.QtBluetooth',
        'PySide6.QtNfc',
        'PySide6.QtPositioning',
        'PySide6.QtLocation',
        'PySide6.QtSensors',
        'PySide6.QtTextToSpeech',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MangaList',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed application (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Icon will be loaded at runtime from the application's built-in icon
    icon=None,
)
