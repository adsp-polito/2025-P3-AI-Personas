#!/bin/sh

set -eu

VENV_DIR="${ADSP_VENV_DIR:-/opt/venv}"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"

is_truthy() {
  case "${1:-}" in
    1|true|TRUE|True|yes|YES|on|ON)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

ensure_venv() {
  if [ ! -x "$PYTHON_BIN" ]; then
    python -m venv "$VENV_DIR"
  fi
}

needs_requirements_install() {
  "$PYTHON_BIN" - <<'PY'
import importlib.util

required = ("fastapi", "sentence_transformers", "streamlit")
missing = [name for name in required if importlib.util.find_spec(name) is None]
print("yes" if missing else "no")
PY
}

ensure_requirements() {
  if [ "$(needs_requirements_install)" = "yes" ]; then
    echo "Installing Python requirements into $VENV_DIR"
    "$PIP_BIN" install --upgrade pip
    "$PIP_BIN" install -r requirements.txt
  fi
}

torch_install_state() {
  "$PYTHON_BIN" - <<'PY'
import importlib.util
import os

want_cuda = os.environ.get("ADSP_TORCH_EXPECT_CUDA", "true").strip().lower() in {"1", "true", "yes", "on"}
spec = importlib.util.find_spec("torch")
if spec is None:
    print("missing")
    raise SystemExit

import torch

has_cuda_build = bool(getattr(torch.version, "cuda", None))
if want_cuda and not has_cuda_build:
    print("needs_cuda")
else:
    print("ok")
PY
}

ensure_torch_runtime() {
  if ! is_truthy "${ADSP_TORCH_INSTALL_ENABLED:-true}"; then
    return 0
  fi

  torch_state="$(torch_install_state)"
  if is_truthy "${ADSP_TORCH_FORCE_REINSTALL:-false}"; then
    torch_state="force"
  fi

  if [ "$torch_state" = "ok" ]; then
    return 0
  fi

  torch_index_url="${ADSP_TORCH_INDEX_URL:-https://download.pytorch.org/whl/cu124}"
  torch_packages="${ADSP_TORCH_PACKAGES:-torch torchvision torchaudio}"

  echo "Installing PyTorch runtime from $torch_index_url"
  echo "PyTorch packages: $torch_packages"

  set -- "$PIP_BIN" install --index-url "$torch_index_url"
  if is_truthy "${ADSP_TORCH_FORCE_REINSTALL:-false}"; then
    set -- "$@" --force-reinstall
  fi
  for package in $torch_packages; do
    set -- "$@" "$package"
  done
  "$@"
}

log_torch_runtime() {
  "$PYTHON_BIN" - <<'PY'
import importlib.util

if importlib.util.find_spec("torch") is None:
    print("PyTorch runtime check: torch is not installed")
    raise SystemExit

import torch

print(
    "PyTorch runtime check: "
    f"version={torch.__version__} "
    f"cuda_build={getattr(torch.version, 'cuda', None)} "
    f"cuda_available={torch.cuda.is_available()}"
)
PY
}

ensure_venv
ensure_requirements
ensure_torch_runtime
log_torch_runtime
