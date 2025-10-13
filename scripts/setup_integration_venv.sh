#!/usr/bin/env bash
set -euo pipefail

# Create a reusable Python virtualenv for integration tests
VENV_DIR=".venv-integration"
PYTHON=${PYTHON:-python3}

echo "Creating virtualenv at ${VENV_DIR} using ${PYTHON}"
${PYTHON} -m venv "${VENV_DIR}"
echo "Activating venv and upgrading pip"
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip

echo "Installing test dependencies: pytest, pyzmq, docker"
python -m pip install pytest pyzmq docker

echo "Venv setup complete. Activate with: source ${VENV_DIR}/bin/activate"
