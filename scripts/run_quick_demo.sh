#!/usr/bin/env bash
set -euo pipefail
python -m irp_demo.cli compare --config configs/demo.yaml --time-limit 30
