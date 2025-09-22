# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

project_root = os.getcwd()

# Hidden imports (NumPy/SciPy/PyQt6)
hiddenimports = []
for pkg in ("numpy", "scipy", "PyQt6"):
    try:
        hiddenimports += collect_submodules(pkg)
    except Exception:
        pass

# Data files (icons, settings, PyQt6 resources)
datas = []
try:
    datas += collect_data_files('PyQt6', include_py_files=False)
except Exception:
    pass

for res in ["@splash.png", "icon.ico", "icon.png", "settings.ini"]:
    path = os.path.join(project_root, res)
    if os.path.exists(path):
        datas.append((path, "."))

img_cache_dir = os.path.join(project_root, "image_cache")
if os.path.isdir(img_cache_dir):
    datas.append((img_cache_dir, "image_cache"))

a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PySide6'], # PyQt5 paketini hariç tutuyoruz,
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
    name='DijitalMurekkep',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'icon.ico') if os.path.exists(os.path.join(project_root, 'icon.ico')) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DijitalMurekkep'
)


