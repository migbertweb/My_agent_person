#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export QT_QPA_PLATFORM=wayland
python main.py "$@"