#!/usr/bin/env bash
# Run Tier 1 end to end. PREREG/ was frozen at commit 1ff80ed.
# Requires: pip install -e ".[bear-trap]" from the repo root, and
# data/clean/ndx_1985_2026.csv + spx_1950_2026.csv (primary loads fail without them).
set -euo pipefail
cd "$(dirname "$0")"
STUDY="$(pwd)"
REPO="$(cd ../.. && pwd)"
export PYTHONPATH="${REPO}:${STUDY}${PYTHONPATH:+:${PYTHONPATH}}"

python -m pytest -q "${STUDY}/tests"
python -m bear_trap.data                       # validates clean files; fails if missing
python analyses/s01_null_models.py --paths "${PATHS:-500}"
python analyses/s02_second_sweep.py
python analyses/s03_survival.py
python analyses/s04_panel.py --secondary
python analyses/s99_tier1_summary.py
