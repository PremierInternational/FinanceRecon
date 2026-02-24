# Packaging GL Reconciliation as a Standalone Windows Executable

This guide explains how to build a self-contained `GL_Recon.exe` that end users can run
on Windows without installing Python, Streamlit, or any other dependencies.

---

## How it works

Streamlit is a web server. The `.exe` starts a local HTTP server and opens the app in the
user's default browser — just like running `streamlit run GL_Recon.py` normally, except
everything is bundled inside the build folder.

The tool used is **cx_Freeze** (Windows build, must be run on a Windows machine).

---

## Files created for packaging

| File | Purpose |
|------|---------|
| `launcher.py` | Entry point for the exe. Sets up paths and starts Streamlit in-process. |
| `cx_freeze_setup.py` | cx_Freeze build configuration. Run this to produce the exe. |

The existing source files (`GL_Recon.py`, `utils.py`, `pages/`) need no changes.

---

## Prerequisites (build machine only)

These are only needed on the machine that **builds** the exe, not on end-user machines.

```cmd
pip install cx_freeze streamlit pandas openpyxl numpy pyarrow xlrd
```

Verify the key imports work before building:

```cmd
python -c "import streamlit.web.bootstrap; print('OK')"
python -c "import pyarrow; print('OK')"
python -c "import tkinter; print('OK')"
python -c "import cx_Freeze; print('OK')"
```

> **Tip:** Build inside a fresh virtual environment to avoid bundling unused packages.
> ```cmd
> python -m venv build_venv
> build_venv\Scripts\activate
> pip install cx_freeze streamlit pandas openpyxl numpy pyarrow xlrd
> ```

---

## Building the executable

Open a command prompt, navigate to the `FinanceRecon` folder, and run:

```cmd
cd "c:\Users\10118\OneDrive - Premier International\Documents\Product Management\Client Portal\Recon\FinanceRecon"
python cx_freeze_setup.py build
```

cx_Freeze will:
1. Resolve all imported packages
2. Bundle Python, Streamlit, pandas, openpyxl, and all other dependencies
3. Copy your app files, pages, assets, and Streamlit's web frontend
4. Write the output to `build\exe.win-amd64-3.x\` (folder name includes your Python version)

The build takes **5–15 minutes** the first time.

---

## Output structure

```
build\
└── exe.win-amd64-3.x\
    ├── GL_Recon.exe              ← the file users double-click
    ├── lib\                      ← bundled Python packages (do not delete)
    ├── GL_Recon.py               ← app source (Streamlit loads this at runtime)
    ├── utils.py
    ├── pages\
    ├── assets\
    ├── streamlit\static\         ← Streamlit's HTML/JS/CSS frontend
    ├── tcl\                      ← Tcl/Tk runtime for the Save dialog
    └── (runtime files appear here after first run)
         ├── config_profiles.json
         └── temp_reconciliation_results.xlsx
```

Distribute the **entire `build\exe.win-amd64-3.x\` folder** to users — rename it to
`GL_Recon` for clarity. Zip it up or use an installer (see below).

---

## Running the application (end users)

1. Extract / copy the `GL_Recon` folder to any location (Desktop, Documents, etc.)
2. Double-click `GL_Recon.exe`
3. A console window appears briefly, then the default browser opens to `http://localhost:8501`
4. Use the app normally

> **Port conflict:** If port 8501 is already in use, the app will fail to start. Close other
> Streamlit instances first, or change `"server.port"` in `launcher.py` and rebuild.

---

## Saved configuration profiles

`config_profiles.json` is created in the **same folder as `GL_Recon.exe`** the first time
a profile is saved. This means:

- Profiles **persist** between runs ✓
- Moving the entire folder preserves saved profiles ✓
- The file is plain JSON and can be backed up or copied between machines ✓

---

## Troubleshooting common build issues

### Browser opens but shows a blank page
Streamlit's frontend assets were not copied into the build.
**Fix:** Confirm `_streamlit_static` is in `include_files` in `cx_freeze_setup.py` and
that the path `build\...\streamlit\static\index.html` exists after building.

### `ModuleNotFoundError` at runtime
A package was not listed in `packages`.
**Fix:** Add the missing module name to the `packages` list in `cx_freeze_setup.py` and rebuild.

### `ImportError: pyarrow version X is not compatible`
The pyarrow version in your build environment doesn't match what Streamlit expects.
**Fix:** `pip install "pyarrow>=7.0"` and rebuild.

### Save dialog (Download Results) doesn't open
Tcl/Tk runtime files were not found or bundled.
**Fix:** Verify `sys.prefix\tcl` exists in your Python installation:
```cmd
python -c "import sys; print(sys.prefix)"
```
Check that `<prefix>\tcl\tcl8.6\` exists, then rebuild.

### `TypeError: Descriptors cannot not be created directly` (protobuf error)
Already handled in `launcher.py`. If the error still appears, set this before running:
```cmd
set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
GL_Recon.exe
```

### Antivirus flags the exe
Bundled Python executables can trigger false positives. Options:
- Submit the file to your AV vendor for whitelisting
- Sign the executable with a code-signing certificate
- cx_Freeze `--onedir` builds (the default here) are flagged less often than single-file bundlers

### App crashes immediately with no error visible
`launcher.py` has `base="Console"` by default so the console window stays open and shows
the Python traceback. If you changed it to `Win32GUI`, switch it back to `Console` temporarily
to see the error.

---

## Creating an installer (optional)

To give users a proper installer with a Start Menu shortcut, use **Inno Setup** (free):

1. Download Inno Setup from https://jrsoftware.org/isinfo.php
2. Point it at the build output folder
3. Build the installer — produces a single `GL_Recon_Setup.exe`

A minimal Inno Setup script:

```iss
[Setup]
AppName=GL Reconciliation
AppVersion=1.0
DefaultDirName={autopf}\GL Reconciliation
DefaultGroupName=GL Reconciliation
OutputBaseFilename=GL_Recon_Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "build\exe.win-amd64-3.x\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\GL Reconciliation"; Filename: "{app}\GL_Recon.exe"
Name: "{commondesktop}\GL Reconciliation"; Filename: "{app}\GL_Recon.exe"

[Run]
Filename: "{app}\GL_Recon.exe"; Description: "Launch GL Reconciliation"; Flags: nowait postinstall skipifsilent
```

> **Note:** Update the `Source` path to match your actual Python version folder name,
> e.g. `build\exe.win-amd64-3.11\*`

---

## Quick reference

| Task | Command |
|------|---------|
| Build | `python cx_freeze_setup.py build` |
| Test build | `build\exe.win-amd64-3.x\GL_Recon.exe` |
| Rebuild after code changes | `python cx_freeze_setup.py build` |
| Change port | Edit `"server.port"` in `launcher.py`, then rebuild |
| Add an icon | Set `icon="path\\to\\icon.ico"` in `cx_freeze_setup.py` Executable block, then rebuild |
| Hide console window | Change `base="Console"` to `base="Win32GUI"` in `cx_freeze_setup.py`, then rebuild |
