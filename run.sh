#!/usr/bin/env bash
#
# run.sh — PromotionBench simulation runner
#
# Usage:
#   ./run.sh                     # Full 9-phase simulation (neutral Riley)
#   ./run.sh --resume            # Resume from last checkpoint
#   ./run.sh --variant ruthless  # Run with ruthless Riley
#   ./run.sh --phases 1,2,3      # Run specific phases only
#   ./run.sh --fresh             # Ignore checkpoint, start clean
#   ./run.sh --resume-id <id>    # Resume a specific run
#
# The simulation checkpoints after every successful phase.
# If it crashes, just run:  ./run.sh --resume
# and it picks up from where it left off — zero wasted API calls.
#

set -euo pipefail

# ── Resolve project root (where this script lives) ─────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Colors ──────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }

# ── Check Python venv ───────────────────────────────────────────
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON="$VENV_DIR/bin/python"

if [[ ! -f "$PYTHON" ]]; then
    error "Virtual environment not found at $VENV_DIR"
    error "Create it with:  uv venv && uv pip install -e '.[dev]'"
    exit 1
fi

ok "Python: $($PYTHON --version 2>&1)"

# ── Check .env for API key ──────────────────────────────────────
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    # shellcheck disable=SC1091
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

if [[ -z "${ELEMENT_API_KEY:-}" ]]; then
    error "ELEMENT_API_KEY is not set."
    error "Set it in .env or export it before running."
    error "Get a key: https://console.dx.walmart.com/elementgenai/llm_gateway"
    exit 1
fi

ok "API key: ${ELEMENT_API_KEY:0:20}..."

# ── Ensure output directories exist ────────────────────────────
mkdir -p checkpoints transcripts docs/data

# ── Run the simulation ──────────────────────────────────────────
info "Starting PromotionBench simulation..."
info "Args: $*"
echo ""

# Timestamp for log filename
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
LOGFILE="simulation_${TIMESTAMP}.log"

# Run with all passed arguments, tee to log and console
"$PYTHON" run_simulation.py "$@" 2>&1 | tee "$LOGFILE"
EXIT_CODE=${PIPESTATUS[0]}

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
    ok "Simulation finished (exit code 0)"
    ok "Log: $LOGFILE"
    ok "Dashboard: docs/data/results.json"
    ok "Transcripts: transcripts/"

    # Show checkpoint status
    if [[ -d checkpoints ]] && ls checkpoints/*.checkpoint.json &>/dev/null; then
        warn "Checkpoint file still present (partial run?):"
        ls -la checkpoints/*.checkpoint.json 2>/dev/null
    fi
else
    warn "Simulation exited with code $EXIT_CODE"
    warn "A phase likely failed. Resume with:"
    echo ""
    echo "    ./run.sh --resume"
    echo ""

    # Show which checkpoint is available
    if [[ -d checkpoints ]] && ls checkpoints/*.checkpoint.json &>/dev/null; then
        info "Available checkpoints:"
        for f in checkpoints/*.checkpoint.json; do
            PHASES=$("$PYTHON" -c "
import json, sys
with open('$f') as fh:
    d = json.load(fh)
print(f\"  {d['run_id']}: phases {d['completed_phases']} (saved {d['last_saved']})\")
" 2>/dev/null || echo "  (could not read $f)")
            echo "$PHASES"
        done
    fi
fi

exit $EXIT_CODE
