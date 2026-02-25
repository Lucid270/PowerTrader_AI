#!/usr/bin/env bash
set -euo pipefail

# If running as root, optionally install system packages
if [ "${EUID:-0}" -eq 0 ]; then
  apt update
  apt install -y python3-venv python3-tk build-essential libssl-dev libffi-dev python3-dev || true
fi

# Create and activate virtualenv
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip || true
if [ -f requirements.txt ]; then
  pip install -r requirements.txt || true
fi

# Create a cleaned copy of pt_trainer.py removing any leading shell commands
CLEANED="pt_trainer_cleaned.py"
awk 'BEGIN{found=0} /^[[:space:]]*#!/{found=1} /^[[:space:]]*(import|from|def|class|if|try|with)\b/{found=1} {if(found) print}' pt_trainer.py > "$CLEANED"

echo "Running cleaned trainer: $CLEANED"
python3 "$CLEANED"
