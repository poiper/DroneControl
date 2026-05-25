#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_PATH="${1:-${WORKSPACE_DIR}/config/wind_pid_test.json}"

exec python3 "${SCRIPT_DIR}/run_pid_trajectory_test.py" "${CONFIG_PATH}"
