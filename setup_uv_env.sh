#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${VENV_DIR:-.venv}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"

cd "$PROJECT_ROOT"

install_uv() {
  echo "uv is not installed. Installing uv..."

  if command -v curl >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://astral.sh/uv/install.sh | sh
  else
    echo "Could not install uv automatically because curl/wget is missing."
    echo "Install uv manually from: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
  fi

  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
}

if ! command -v uv >/dev/null 2>&1; then
  install_uv
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv install finished, but uv is still not available on PATH."
  echo "Restart your shell or add ~/.local/bin and ~/.cargo/bin to PATH, then rerun this script."
  exit 1
fi

echo "Using uv: $(uv --version)"
echo "Project root: $PROJECT_ROOT"

if [ ! -f "requirements.txt" ]; then
  echo "Missing requirements.txt"
  exit 1
fi

if [ ! -f "requirements-dev.txt" ]; then
  echo "Missing requirements-dev.txt"
  exit 1
fi

echo "Creating virtual environment at $VENV_DIR with Python $PYTHON_VERSION..."
if ! uv venv "$VENV_DIR" --python "$PYTHON_VERSION"; then
  echo "Python $PYTHON_VERSION was not available locally. Installing it with uv..."
  uv python install "$PYTHON_VERSION"
  uv venv "$VENV_DIR" --python "$PYTHON_VERSION"
fi

echo "Installing runtime and dev dependencies..."
uv pip install --python "$VENV_DIR/bin/python" -r requirements.txt -r requirements-dev.txt

echo ""
echo "Setup complete."
echo ""
echo "Activate environment:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "Run Excel tests:"
echo "  $VENV_DIR/bin/python -m pytest tests/modules/excel"
