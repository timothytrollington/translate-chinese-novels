#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
VENV_DIR="${PROJECT_ROOT}/venv"

if [[ -d "${VENV_DIR}" ]]; then
  echo "Virtual environment already exists at ${VENV_DIR}" >&2
else
  python3 -m venv "${VENV_DIR}"
  echo "Created virtual environment at ${VENV_DIR}" >&2
fi

source "${VENV_DIR}/bin/activate"

pip install --upgrade pip
pip install -r "${PROJECT_ROOT}/requirements.txt"

echo "Virtual environment is ready. To activate it later, run:"
echo "source ${VENV_DIR}/bin/activate"
