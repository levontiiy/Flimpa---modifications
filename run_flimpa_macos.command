#!/bin/bash
# Start FLIMPA using the local virtual environment (.venv).
cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
  echo
  echo "FLIMPA is not installed yet. Run this first:"
  echo "    bash offline/install_offline_macos.command"
  echo
  read -r -p "Press Enter to close..."
  exit 1
fi

exec ".venv/bin/python" main.py
