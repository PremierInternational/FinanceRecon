"""
Entry point for the cx_Freeze-packaged executable.

cx_Freeze bundles this file as the .exe entry point — NOT GL_Recon.py.
This script sets up the correct working directory and asset paths, then
launches the Streamlit server in-process via bootstrap.run().
"""

import os
import sys


def get_bundle_dir() -> str:
    """
    Directory where bundled files (GL_Recon.py, assets/, pages/, etc.) live.
    - cx_Freeze: all files are in the same directory as the .exe
    - Plain Python: the directory containing this script
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    bundle_dir = get_bundle_dir()

    # With cx_Freeze the bundle dir IS the exe dir, so it is also writable.
    # Setting cwd here ensures all relative open() calls (config_profiles.json,
    # temp xlsx exports) resolve to the same folder as the exe.
    os.chdir(bundle_dir)

    # Ensure the bundle dir is on sys.path so GL_Recon.py can import utils.py
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)

    # Tcl/Tk runtime paths — required for tkinter filedialog to work from an exe
    tcl_lib = os.path.join(bundle_dir, "tcl", "tcl8.6")
    tk_lib = os.path.join(bundle_dir, "tcl", "tk8.6")
    if os.path.isdir(tcl_lib):
        os.environ["TCL_LIBRARY"] = tcl_lib
        os.environ["TK_LIBRARY"] = tk_lib

    # Suppress protobuf C-extension warning (common with bundled Streamlit)
    os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

    # Suppress Streamlit telemetry prompt
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    app_script = os.path.join(bundle_dir, "GL_Recon.py")

    from streamlit.web import bootstrap

    flag_options = {
        "server.port": 8501,
        "server.headless": True,
        "browser.serverAddress": "localhost",
        "browser.gatherUsageStats": False,
        # Disable the file watcher — source paths inside the bundle are stable
        # but watching them is unnecessary overhead and can cause errors.
        "server.fileWatcherType": "none",
        "global.developmentMode": False,
    }

    bootstrap.run(app_script, "", [], flag_options)


if __name__ == "__main__":
    main()
