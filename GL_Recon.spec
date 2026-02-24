# GL_Recon.spec
# -*- mode: python ; coding: utf-8 -*-
#
# Build with:
#   pyinstaller GL_Recon.spec --clean --noconfirm
#
# Output: dist/GL_Recon/GL_Recon.exe  (plus supporting files in the same folder)

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_all

block_cipher = None

# ── Collect Streamlit's bundled web assets (HTML / JS / CSS frontend) ──────
# Without this the browser loads a blank page.
streamlit_datas, streamlit_binaries, streamlit_hiddenimports = collect_all("streamlit")

# ── Collect pyarrow (Streamlit's Arrow-based dataframe serialisation) ───────
pyarrow_datas, pyarrow_binaries, pyarrow_hiddenimports = collect_all("pyarrow")

# ── Collect Tcl/Tk runtime for tkinter filedialog ───────────────────────────
import tkinter as _tk
_tk_dir  = os.path.dirname(_tk.__file__)
_tcl_dir = os.path.join(sys.prefix, "tcl")   # contains tcl8.6/ and tk8.6/ subdirs

tk_datas = [(_tk_dir, "tkinter")]
if os.path.isdir(_tcl_dir):
    tk_datas.append((_tcl_dir, "tcl"))

# ── Your application's own files ────────────────────────────────────────────
app_datas = [
    ("GL_Recon.py",  "."),
    ("utils.py",     "."),
    ("pages",        "pages"),
    ("assets",       "assets"),
]

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=streamlit_binaries + pyarrow_binaries,
    datas=(
        app_datas
        + tk_datas
        + streamlit_datas
        + pyarrow_datas
        + collect_data_files("pandas")
        + collect_data_files("altair")
        + collect_data_files("openpyxl")
        + collect_data_files("tzdata")
    ),
    hiddenimports=(
        streamlit_hiddenimports
        + pyarrow_hiddenimports
        + [
            # Streamlit internals
            "streamlit",
            "streamlit.web.bootstrap",
            "streamlit.web.server",
            "streamlit.web.server.server",
            "streamlit.runtime",
            "streamlit.runtime.scriptrunner",
            "streamlit.runtime.scriptrunner.magic_funcs",
            "streamlit.runtime.caching",
            "streamlit.runtime.legacy_caching",
            "streamlit.runtime.state",
            "streamlit.components.v1",
            "streamlit.elements",
            # Tornado (Streamlit's HTTP server)
            "tornado",
            "tornado.web",
            "tornado.ioloop",
            "tornado.iostream",
            "tornado.httpserver",
            "tornado.websocket",
            # Data / Excel stack
            "pandas",
            "pandas._libs.tslibs.np_datetime",
            "pandas._libs.tslibs.nattype",
            "pandas._libs.tslibs.timedeltas",
            "pandas._libs.tslibs.timestamps",
            "pandas._libs.tslibs.offsets",
            "pandas._libs.skiplist",
            "numpy",
            "numpy.core._dtype_ctypes",
            "openpyxl",
            "openpyxl.cell._writer",
            "openpyxl.styles",
            "openpyxl.utils",
            "openpyxl.workbook",
            "openpyxl.worksheet",
            "et_xmlfile",
            "xlrd",
            # Tkinter
            "tkinter",
            "tkinter.filedialog",
            "_tkinter",
            # Other commonly missed modules
            "importlib.metadata",
            "importlib.resources",
            "pkg_resources",
            "google.protobuf",
            "click",
            "toml",
            "requests",
            "urllib3",
            "certifi",
            "dateutil",
            "dateutil.parser",
            "pytz",
            "tzdata",
            "six",
            "altair",
            "altair.vegalite",
        ]
    ),
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "scipy",
        "IPython",
        "jupyter",
        "notebook",
        "pytest",
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
    name="GL_Recon",
    debug=False,
    strip=False,
    upx=False,          # UPX can corrupt DLLs; leave off
    console=True,       # Keep True during development so error output is visible.
                        # Change to False for a silent production build.
    icon=None,          # Replace with path to a .ico file if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="GL_Recon",    # Output folder: dist/GL_Recon/
)
