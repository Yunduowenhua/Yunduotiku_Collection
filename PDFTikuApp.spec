# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

rapidocr_datas = collect_data_files('rapidocr_onnxruntime')
rapidocr_hidden = collect_submodules('rapidocr_onnxruntime')

a = Analysis(
    ['src\\main.py'],
    pathex=['E:\\My_PythonProject（Yunduo）\\Proj_tiku_V1_goal（GM2）'],
    binaries=[],
    datas=rapidocr_datas,
    hiddenimports=['rapidocr_onnxruntime', 'cv2', 'fitz'] + rapidocr_hidden,
    excludes=['PyQt5', 'PyQt6', 'PySide2'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PDFTikuApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PDFTikuApp',
)
