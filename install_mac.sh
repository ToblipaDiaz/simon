#!/bin/bash
set -e
cd "$(dirname "$0")"
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Se creó .env desde .env.example. Edita .env y pega tu OPENAI_API_KEY."
fi
