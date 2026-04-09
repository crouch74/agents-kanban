#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r apps/api/requirements-dev.txt
npm install

