#!/usr/bin/env bash
set -euo pipefail

cd /workspace

uv venv -c "$UV_PROJECT_ENVIRONMENT"
uv sync
uv pip install --python "$UV_PROJECT_ENVIRONMENT/bin/python" -e .

source "$UV_PROJECT_ENVIRONMENT/bin/activate"

alias_line="alias claude='claude --dangerously-skip-permissions'"
grep -qxF "$alias_line" "$HOME/.bashrc" || \
  echo "$alias_line" >> "$HOME/.bashrc"
