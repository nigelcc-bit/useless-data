#!/usr/bin/env bash
# Run Tier 1 end to end. Commit PREREG/ before the first run on real data.
set -euo pipefail
cd "$(dirname "$0")"
python -m pytest -q
python -m src.data                       # download / validate / cache
python studies/s01_null_models.py --paths "${PATHS:-500}"
python studies/s02_second_sweep.py
python studies/s03_survival.py
python studies/s04_panel.py --secondary
python studies/s99_tier1_summary.py
