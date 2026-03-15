# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — GSBWIFI Bypass
Desteklenen platformlar: Windows, macOS, Linux

Kullanım:
    pyinstaller GSBWiFi.spec

Ön koşul:
    pip install -r build-requirements.txt
    python packaging/create_icons.py
"""
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# customtkinter tema ve varlık dosyaları
customtkinter_datas = collect_data_files("customtkinter")

a = Analysis(
    ["main.py"],
    pathex=[str(Path(".").resolve())],
    binaries=[],
    datas=customtkinter_datas,
    hiddenimports=[
        "customtkinter",
        # keyring backend'leri — platform'a göre biri kullanılır
        "keyring.backends",
        "keyring.backends.Windows",
        "keyring.backends.OS_X",
        "keyring.backends.SecretService",
        "keyring.backends.kwallet",
        "keyring.backends.fail",
        "keyrings.alt",
        "keyrings.alt.file",
        "keyrings.alt.Gnome",
        "keyrings.alt.Google",
        # tkinter
        "tkinter",
        "tkinter.ttk",
        # requests / urllib3 iç modülleri
        "requests",
        "urllib3",
        "charset_normalizer",
        "certifi",
        "idna",
    ],
    excludes=[
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "IPython",
        "jupyter",
        "notebook",
        "PIL._webp",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ------------------------------------------------------------------
# Platform'a özgü paketleme
# ------------------------------------------------------------------

if sys.platform == "darwin":
    # macOS: .app bundle (dmg için ayrıca hdiutil kullanılır)
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="GSBWiFi",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        icon="assets/icon.icns",
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="GSBWiFi",
    )
    app = BUNDLE(
        coll,
        name="GSBWiFi.app",
        icon="assets/icon.icns",
        bundle_identifier="tr.gov.gsb.wifibypass",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1.0.0",
            "NSRequiresAquaSystemAppearance": False,  # Dark mode desteği
        },
    )
else:
    # Windows / Linux: tek dosya çalıştırılabilir
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="GSBWiFi",
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
        icon="assets/icon.ico" if sys.platform == "win32" else None,
        onefile=True,
    )
