# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# kiwipiepy, kiwipiepy_model 데이터 파일 자동 수집
kiwi_datas = collect_data_files("kiwipiepy") + collect_data_files("kiwipiepy_model")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        # tokenizer CSV
        ("src/tokenizations/ko_dictionary.csv",   "src/tokenizations"),
        ("src/tokenizations/ko_preanalyzed.csv",  "src/tokenizations"),
        # Rust 확장 모듈
        ("_core.pyi", "."),
        # 프론트엔드 빌드 결과물
        ("../frontend/dist/desktop", "frontend/dist/desktop"),
        # kiwipiepy 모델
        *kiwi_datas,
    ],
    hiddenimports=[
        "kiwipiepy_model",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="KKORI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon="../assets/icon.jpg",
)