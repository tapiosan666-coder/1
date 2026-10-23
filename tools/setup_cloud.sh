#!/usr/bin/env bash
set -euo pipefail

cd /workspace/1
export XDG_CACHE_HOME=/workspace/.cache/find-yourself
export XDG_DATA_HOME=/workspace/.local/share
export XDG_CONFIG_HOME=/workspace/.config
export PIP_CACHE_DIR=/workspace/.cache/pip
mkdir -p "$XDG_CACHE_HOME" "$XDG_DATA_HOME" "$XDG_CONFIG_HOME" /workspace/.venvs builds

case "$(godot --version)" in
  4.6.3.*) ;;
  *) echo 'Godot 4.6.3 Standard is required.' >&2; exit 1 ;;
esac
if [ ! -x /workspace/.venvs/find-yourself/bin/python ]; then
  python3 -m venv /workspace/.venvs/find-yourself
fi
/workspace/.venvs/find-yourself/bin/pip install -r tools/requirements.txt
godot --headless --editor --import --quit
godot --headless --script res://tests/test_game.gd
