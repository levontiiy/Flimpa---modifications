# FLIMPA offline installation

This folder lets you install FLIMPA on a machine **with no internet access**.
All Python libraries listed in `../requirements.txt` are bundled here as
pre-downloaded wheels, separated by platform.

| Platform | Wheels folder | Installer |
|----------|---------------|-----------|
| Windows 64-bit | `wheels-windows-py313/` | `install_offline_windows.bat` |
| macOS Apple Silicon (arm64) | `wheels-macos-arm64-py313/` | `install_offline_macos.command` |

All wheels are built for **Python 3.13 (64-bit)**.

---

## Prerequisite: Python 3.13

The bundle contains the libraries, **not** the Python interpreter itself.
The target machine must already have **Python 3.13 (64-bit)** installed.

- Check with: `python --version` (Windows) or `python3 --version` (macOS).
- If Python is missing, install it first. If that machine is also offline,
  download the official Python 3.13 installer on another computer and copy it
  over:
  - Windows: `python-3.13.x-amd64.exe` from python.org
  - macOS: `python-3.13.x-macos11.pkg` from python.org

> The wheels are version-specific. They will **not** install on Python 3.11,
> 3.12, or 3.14.

---

## Install

### Windows

1. Copy the whole FLIMPA folder onto the offline machine.
2. Double-click `offline\install_offline_windows.bat`
   (or run it from a Command Prompt).
3. When it finishes, start FLIMPA with:

   ```bat
   .venv\Scripts\python.exe main.py
   ```

### macOS (Apple Silicon)

1. Copy the whole FLIMPA folder onto the offline machine.
2. In Terminal, from the project root:

   ```bash
   bash offline/install_offline_macos.command
   ```

   (or make it double-clickable once: `chmod +x offline/install_offline_macos.command`)
3. When it finishes, start FLIMPA with:

   ```bash
   .venv/bin/python main.py
   ```

Each installer creates a local virtual environment (`.venv`) in the project
root and installs every dependency from the bundled wheels using
`pip install --no-index` (no internet is contacted).

---

## What gets installed

The exact pinned versions from `../requirements.txt` (34 packages), including
numpy, scipy, pandas, matplotlib, scikit-image, pillow, PySide6/shiboken6,
tifffile, ptufile, sdtfile, seaborn, and their dependencies.

---

## Platform / architecture notes

- **Windows wheels** target `win_amd64` (64-bit Intel/AMD).
- **macOS wheels** target Apple Silicon (`arm64`). numpy and scipy require
  **macOS 14+**; PySide6 requires **macOS 13+**. They will not run on Intel Macs.
- If you need **Intel macOS** or **Linux** wheels, they can be generated the
  same way (see "Regenerating" below).

---

## Regenerating / updating the wheels

Run these from a machine **with** internet (any OS; pip can cross-download):

```bash
# Windows 64-bit, Python 3.13
pip download -r requirements.txt \
  --dest offline/wheels-windows-py313 \
  --platform win_amd64 --python-version 313 --only-binary=:all:

# macOS Apple Silicon, Python 3.13 (run on a Mac, or add --platform macosx_14_0_arm64)
pip download -r requirements.txt \
  --dest offline/wheels-macos-arm64-py313 \
  --python-version 313 --only-binary=:all:
```

To verify a wheelhouse resolves with no internet:

```bash
pip install --no-index --find-links offline/wheels-windows-py313 \
  -r requirements.txt --dry-run \
  --platform win_amd64 --python-version 313 --only-binary=:all: --target /tmp/check
```

---

## Note on folder size and iCloud

This `offline/` folder is large (~800 MB total). Because the project lives in
an iCloud-synced location, these files will sync to iCloud. If you do not want
that, move the `offline/` folder outside iCloud, or exclude it from sync.
