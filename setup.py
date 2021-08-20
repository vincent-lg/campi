import distutils
import opcode
import os

from cx_Freeze import setup, Executable

campi = Executable(
    script="src/campi/main.py",
    base="Win32GUI",
    target_name="campi"
)

includefiles = [
        ("src/campi/main.bui", "src/campi/main.bui"),
]
setup(
    name = "campi",
    version = "0.1",
    description = "The Campi Feed Reader.",
    options = {'build_exe': {
            "include_files": includefiles,
            "excludes": ["_gtkagg", "_tkagg", "bsddb", "distutils", "curses",
                    "pywin.debugger", "pywin.debugger.dbgcon",
                    "pywin.dialogs", "tcl", "Tkconstants", "Tkinter"],
            "packages": ["bui.specific.wx4"],
    }},
    executables = [campi]
)
