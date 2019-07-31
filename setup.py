import sys, os
from cx_Freeze import setup, Executable

import os.path
PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')


build_exe_options = {"packages": ["kenlm_lm","predictor","vocabtrie","config","kconfig","widgets","mainWindow",
                                  "string","time",'PyQt5.QtGui', 'PyQt5.QtCore', 'PyQt5.QtWidgets', "PyQt5.QtMultimedia", "numpy",
                                  "sys","Pickle","pickle_util", "random", "pathlib", "appdirs", "re",
                                  "os", "kenlm"],
                     "include_files": ["icons", "resources"]}#"pygame",

base = None

if sys.platform == "win32":
    base = "Win32GUI"
    
elif sys.platform == "win64":
    base = "Win64GUI"

setup(name="Row Column Scanner",
      version="1.2.0",
      description = "Python 3, PyQt5, Study Mode, Updated Frame Timer",
      options={"build_exe": build_exe_options},
      executables=[Executable("keyboard.py", base=base,
                                icon="rowcol.ico",
                                shortcutName="Row Column Scanner",
                                shortcutDir="DesktopFolder",)])
