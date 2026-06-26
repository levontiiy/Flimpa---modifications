#!/bin/bash
# ============================================================
#  FLIMPA offline installer - macOS Apple Silicon / Python 3.13
#  Installs all dependencies from the bundled wheels in
#  offline/wheels-macos-arm64-py313 with no internet access.
#
#  Double-click in Finder, or run:  bash install_offline_macos.command
# ============================================================
set -e
cd "$(dirname "$0")/.."

WHEELS="offline/wheels-macos-arm64-py313"

# Locate a Python 3.13 interpreter (the bundled wheels are cp313).
PYBIN=""
for c in python3.13 python3 python; do
  if command -v "$c" >/dev/null 2>&1; then
    if "$c" -c 'import sys; sys.exit(0 if sys.version_info[:2]==(3,13) else 1)' 2>/dev/null; then
      PYBIN="$c"
      break
    fi
  fi
done

if [ -z "$PYBIN" ]; then
  echo
  echo "ERROR: Python 3.13 was not found on this machine."
  echo "The bundled wheels are built specifically for Python 3.13."
  echo "Install Python 3.13 (e.g. from python.org), then run this script again."
  echo
  exit 1
fi

echo "Using $($PYBIN --version)"

# Remove any stale .venv (e.g. a leftover symlink/file copied from another
# computer or OS). venv refuses to run if .venv already exists as a file or
# symlink. rm on a symlink removes only the link, not its target.
if [ -e .venv ] || [ -L .venv ]; then
  echo "Removing existing/stale .venv ..."
  rm -rf .venv
fi

echo
echo "Creating virtual environment (.venv) ..."
"$PYBIN" -m venv .venv

echo
echo "Installing FLIMPA dependencies from bundled wheels (offline) ..."
.venv/bin/python -m pip install --no-index --find-links "$WHEELS" -r requirements.txt

echo
echo "============================================================"
echo " Done. To start FLIMPA, run:"
echo "    .venv/bin/python main.py"
echo "============================================================"
