# PyInstaller spec for the Windows build.  Run via packaging\windows\build.ps1
# Produces dist\LookHop\LookHop.exe (one-folder build: starts fast, fewer
# antivirus false positives than one-file builds).
import re
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
from PyInstaller.utils.win32.versioninfo import (FixedFileInfo, StringFileInfo, StringStruct,
                                                 StringTable, VarFileInfo, VarStruct, VSVersionInfo)

ROOT = Path(SPECPATH).resolve().parents[1]
VERSION = re.search(r'__version__ = "([^"]+)"', (ROOT / "lookhop" / "__init__.py").read_text()).group(1)
MODEL = ROOT / "models" / "face_landmarker.task"
if not MODEL.exists():
    raise SystemExit(f"Missing {MODEL} - run build.ps1, it downloads the model first.")

# MediaPipe's Tasks API loads a native library + data files at runtime.
datas = collect_data_files("mediapipe") + [(str(MODEL), "models")]
binaries = collect_dynamic_libs("mediapipe")

a = Analysis(
    [str(ROOT / "lookhop" / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=["pystray._win32", "PIL._tkinter_finder"],
    # (matplotlib must stay: mediapipe imports it at load time)
    excludes=["IPython", "pytest", "tensorflow", "jax", "torch"],
    noarchive=False,
)
# Not needed: OpenCV's video-file codecs (the webcam uses DirectShow/MSMF) and
# Pillow's AVIF plugin. Saves ~45 MB.
_DROP = ("opencv_videoio_ffmpeg", "_avif")
a.binaries = [b for b in a.binaries if not any(d in Path(b[0]).name for d in _DROP)]
pyz = PYZ(a.pure)

nums = tuple(int(x) for x in (VERSION.split(".") + ["0", "0", "0"])[:4])
version_info = VSVersionInfo(
    ffi=FixedFileInfo(filevers=nums, prodvers=nums),
    kids=[
        StringFileInfo([StringTable("040904B0", [
            StringStruct("ProductName", "LookHop"),
            StringStruct("FileDescription", "LookHop - the cursor follows your eyes"),
            StringStruct("FileVersion", VERSION),
            StringStruct("ProductVersion", VERSION),
            StringStruct("OriginalFilename", "LookHop.exe"),
            StringStruct("LegalCopyright", "MIT License"),
        ])]),
        VarFileInfo([VarStruct("Translation", [1033, 1200])]),
    ],
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LookHop",
    icon=str(ROOT / "assets" / "lookhop.ico"),
    version=version_info,
    console=False,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="LookHop", upx=False)
