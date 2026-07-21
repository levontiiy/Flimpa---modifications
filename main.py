import sys
import os
import importlib.util


# --- Dependency self-check -------------------------------------------------
# Runs BEFORE any third-party import so a missing library produces a clear,
# actionable message instead of a raw ModuleNotFoundError traceback.
# The bundled wheels and offline installers live in the 'offline' folder.
_REQUIRED_LIBRARIES = {
    # import name : pip / distribution name (as in requirements.txt)
    "PySide6": "PySide6",
    "numpy": "numpy",
    "scipy": "scipy",
    "pandas": "pandas",
    "matplotlib": "matplotlib",
    "skimage": "scikit-image",
    "PIL": "pillow",
    "yaml": "PyYAML",
    "seaborn": "seaborn",
    "tifffile": "tifffile",
    "ptufile": "ptufile",
    "sdtfile": "sdtfile",
}


def _project_root():
    return os.path.dirname(os.path.abspath(__file__))


def _venv_python_path():
    root = _project_root()
    if sys.platform.startswith("win"):
        return os.path.join(root, ".venv", "Scripts", "python.exe")
    return os.path.join(root, ".venv", "bin", "python")


def _running_in_project_venv():
    """True only when this process is using the project's .venv site-packages."""
    venv_dir = os.path.realpath(os.path.join(_project_root(), ".venv"))
    if not os.path.isdir(venv_dir):
        return False
    if os.path.realpath(sys.prefix) == venv_dir:
        return True
    exe = os.path.realpath(sys.executable)
    return exe.startswith(venv_dir + os.sep)


def _find_missing_libraries():
    """Return the pip names of any required libraries that are not importable."""
    missing = []
    for module_name, pip_name in _REQUIRED_LIBRARIES.items():
        try:
            found = importlib.util.find_spec(module_name) is not None
        except (ImportError, ValueError, ModuleNotFoundError):
            found = False
        if not found:
            missing.append(pip_name)
    return missing


def _try_reexec_with_venv():
    """Restart with .venv Python when launched via system Python without deps."""
    if os.environ.get("FLIMPA_NO_VENV_REEXEC") == "1":
        return False
    if _running_in_project_venv():
        return False

    venv_py = _venv_python_path()
    if not os.path.isfile(venv_py):
        return False
    if not _find_missing_libraries():
        return False

    env = os.environ.copy()
    env["FLIMPA_NO_VENV_REEXEC"] = "1"
    os.execve(venv_py, [venv_py, os.path.abspath(__file__), *sys.argv[1:]], env)
    return True


def _report_missing_and_exit(missing):
    is_windows = sys.platform.startswith("win")
    py_cmd = ".venv\\Scripts\\python.exe" if is_windows else ".venv/bin/python"
    if is_windows:
        launcher = "run_flimpa_windows.bat"
        installer = "offline\\install_offline_windows.bat"
    else:
        launcher = "run_flimpa_macos.command"
        installer = "bash offline/install_offline_macos.command"
    lines = [
        "",
        "============================================================",
        " FLIMPA cannot start: required Python libraries are missing",
        "============================================================",
        " Missing package(s):",
    ]
    lines += [f"   - {name}" for name in missing]
    lines += [
        "",
        " These libraries are bundled in the 'offline' folder, so no",
        " internet connection is needed. Install them by running:",
        "",
        f"     {installer}",
        "",
        " Then start FLIMPA with the project virtual environment:",
        "",
        f"     {launcher}",
        "",
        " or:",
        "",
        f"     {py_cmd} main.py",
        "",
        " If this machine has internet, you can instead run:",
        "",
        "     pip install -r requirements.txt",
        "",
        " Tip: do not use bare 'python3 main.py' unless that Python is",
        " the same one where FLIMPA was installed (.venv).",
        "============================================================",
        "",
    ]
    sys.stderr.write("\n".join(lines) + "\n")
    sys.exit(1)


if _try_reexec_with_venv():
    sys.exit(0)

_missing_libraries = _find_missing_libraries()
if _missing_libraries:
    _report_missing_and_exit(_missing_libraries)
# ---------------------------------------------------------------------------

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QPixmap
from utils.dark_theme import get_darkModePalette
from utils.mainwindow import MainWindow

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

# Ensure the icon path is correct
base_path = os.path.abspath(os.path.dirname(__file__))
icon_path = os.path.join(base_path, 'icon', 'icon_f.ico')

qt_args = sys.argv.copy()
if sys.platform.startswith("win"):
    qt_args += ['-platform', 'windows:darkmode=2']

app = QApplication(qt_args)
app.setStyle('Fusion')
app.setPalette(get_darkModePalette(app))

# Load the icon and resize it to a smaller size
icon = QIcon(QPixmap(icon_path))
app.setWindowIcon(icon)

window = MainWindow(app)
window.setWindowTitle("FLIMPA (v1.4.2)")
window.setWindowIcon(icon)  # Set the window icon here
window.showMaximized()

app.exec()
