#!/bin/bash
set -e
cd "$(dirname "$0")"
source .venv/bin/activate
streamlit run app.py
