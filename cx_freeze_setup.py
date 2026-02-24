"""
cx_Freeze build script for GL Reconciliation.

Usage:
    python cx_freeze_setup.py build

Output: build/exe.win-amd64-3.x/
"""

import os
import sys

import streamlit
import tkinter
from cx_Freeze import Executable, setup

# ── Streamlit's static web assets (HTML / JS / CSS frontend) ────────────────
# Without these the browser renders a blank page.
_streamlit_dir = os.path.dirname(streamlit.__file__)
_streamlit_static = os.path.join(_streamlit_dir, "static")

# ── Tcl/Tk runtime (required for tkinter filedialog) ────────────────────────
_tk_dir = os.path.dirname(tkinter.__file__)
_tcl_dir = os.path.join(sys.prefix, "tcl")   # contains tcl8.6/ and tk8.6/

# ── Files and folders to copy into the build directory ──────────────────────
include_files = [
    # Application source files (Streamlit loads these by absolute path at runtime)
    ("GL_Recon.py", "GL_Recon.py"),
    ("utils.py",    "utils.py"),
    ("pages",       "pages"),
    ("assets",      "assets"),
    # Streamlit frontend
    (_streamlit_static, "streamlit/static"),
    # Tkinter pure-Python package
    (_tk_dir, "tkinter"),
]

# Add the Tcl/Tk runtime DLLs and scripts if present
if os.path.isdir(_tcl_dir):
    include_files.append((_tcl_dir, "tcl"))

# ── Build options ────────────────────────────────────────────────────────────
build_exe_options = {
    "packages": [
        # Streamlit and its HTTP server
        "streamlit",
        "streamlit.web",
        "streamlit.web.bootstrap",
        "streamlit.web.server",
        "streamlit.web.server.server",
        "streamlit.runtime",
        "streamlit.runtime.scriptrunner",
        "streamlit.runtime.scriptrunner.magic_funcs",
        "streamlit.runtime.caching",
        "streamlit.runtime.state",
        "streamlit.components.v1",
        "tornado",
        "tornado.web",
        "tornado.ioloop",
        "tornado.iostream",
        "tornado.httpserver",
        "tornado.websocket",
        # Data / Excel stack
        "pandas",
        "numpy",
        "openpyxl",
        "openpyxl.cell._writer",
        "openpyxl.styles",
        "pyarrow",
        "altair",
        "et_xmlfile",
        "xlrd",
        # Tkinter
        "tkinter",
        "tkinter.filedialog",
        # Other dependencies
        "click",
        "toml",
        "requests",
        "urllib3",
        "certifi",
        "charset_normalizer",
        "google.protobuf",
        "importlib.metadata",
        "importlib.resources",
        "pkg_resources",
        "dateutil",
        "pytz",
        "tzdata",
        "six",
    ],
    "excludes": [
        "matplotlib",
        "scipy",
        "IPython",
        "jupyter",
        "notebook",
        "pytest",
    ],
    "include_files": include_files,
    "include_msvcr": True,       # bundle the Visual C++ runtime
}

executables = [
    Executable(
        "launcher.py",
        base="Console",          # Change to "Win32GUI" to hide the console window
        target_name="GL_Recon.exe",
        icon=None,               # Replace with a path to a .ico file if you have one
    )
]

setup(
    name="GL Reconciliation",
    version="1.0",
    description="GL Reconciliation Tool",
    options={"build_exe": build_exe_options},
    executables=executables,
)
