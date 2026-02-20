"""Checkpoint / resume for PromotionBench simulations.

After every successful phase the full simulation state is written
to a JSON checkpoint file.  If the process dies (API timeout,
OOM, laptop lid closed, etc.) the next run automatically detects
the checkpoint, restores all accumulated state, and resumes from
the first incomplete phase — zero wasted API calls.

Checkpoint contents:
  - run_id            (unique run identifier)
  - variant           (neutral / ruthless)
  - completed_phases  (list of phase numbers that finished)
  - evaluations       (serialised PhaseEvaluation dicts)
  - memory_summaries  (per-character list of memory strings)
  - simulation_state  (SimulationState.to_dict())
  - run_meta          (timing / config metadata)
  - last_saved        (ISO timestamp of last write)
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from financebench.consequences import SimulationState

logger = logging.getLogger(__name__)

DEFAULT_CHECKPOINT_DIR = Path("checkpoints")


def _checkpoint_path(
    run_id: str,
    directory: Path = DEFAULT_CHECKPOINT_DIR,
) -> Path:
    """Return the checkpoint file path for a given run."""
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{run_id}.checkpoint.json"


def save_checkpoint(
    *,
    run_id: str,
    variant: str,
    completed_phases: list[int],
    evaluations: list[dict[str, Any]],
    memory_summaries: dict[str, list[str]],
    simulation_state: SimulationState,
    run_meta: dict[str, Any],
    directory: Path = DEFAULT_CHECKPOINT_DIR,
) -> Path:
    """Persist the full simulation state to disk.

    Called after every successful phase.  The file is written
    atomically (write-to-tmp then rename) so a crash mid-write
    never corrupts the checkpoint.
    """
    path = _checkpoint_path(run_id, directory)
    payload = {
        "run_id": run_id,
        "variant": variant,
        "completed_phases": sorted(completed_phases),
        "evaluations": evaluations,
        "memory_summaries": memory_summaries,
        "simulation_state": simulation_state.to_dict(),
        "run_meta": run_meta,
        "last_saved": datetime.now().isoformat(),
    }

    # Atomic write: tmp → rename
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    tmp.rename(path)

    logger.info(
        "Checkpoint saved: %s (phases %s)",
        path,
        completed_phases,
    )
    return path


def load_checkpoint(
    run_id: str,
    directory: Path = DEFAULT_CHECKPOINT_DIR,
) -> dict[str, Any] | None:
    """Load a checkpoint if it exists.

    Returns None if no checkpoint found for this run_id.
    """
    path = _checkpoint_path(run_id, directory)
    if not path.exists():
        return None

    with open(path) as f:
        data = json.load(f)

    logger.info(
        "Checkpoint loaded: %s (phases %s, saved %s)",
        path,
        data.get("completed_phases", []),
        data.get("last_saved", "unknown"),
    )
    return data


def find_latest_checkpoint(
    directory: Path = DEFAULT_CHECKPOINT_DIR,
) -> dict[str, Any] | None:
    """Find the most recent checkpoint in the directory.

    Useful when the caller doesn't know the run_id (e.g. `--resume`).
    """
    if not directory.exists():
        return None

    candidates = sorted(
        directory.glob("*.checkpoint.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None

    with open(candidates[0]) as f:
        data = json.load(f)

    logger.info("Latest checkpoint: %s", candidates[0].name)
    return data


def restore_simulation_state(
    checkpoint: dict[str, Any],
) -> SimulationState:
    """Rebuild a SimulationState from a checkpoint dict."""
    return SimulationState.from_dict(
        checkpoint.get("simulation_state", {})
    )


def restore_evaluations(
    checkpoint: dict[str, Any],
) -> list:
    """Rebuild PhaseEvaluation objects from checkpoint dicts."""
    from financebench.scoring import PhaseEvaluation, PhaseScores

    evaluations = []
    for ev_dict in checkpoint.get("evaluations", []):
        scores_data = ev_dict.get("scores", {})
        scores = PhaseScores(
            visibility=scores_data.get("visibility", 0),
            competence=scores_data.get("competence", 0),
            relationships=scores_data.get("relationships", 0),
            leadership=scores_data.get("leadership", 0),
            ethics=scores_data.get("ethics", 100),
        )
        ev = PhaseEvaluation(
            phase=ev_dict["phase"],
            name=ev_dict["name"],
            scores=scores,
            narrative=ev_dict.get("narrative", ""),
            key_decisions=ev_dict.get("key_decisions", []),
        )
        evaluations.append(ev)
    return evaluations


def delete_checkpoint(
    run_id: str,
    directory: Path = DEFAULT_CHECKPOINT_DIR,
) -> bool:
    """Delete a checkpoint file (e.g. after a clean finish)."""
    path = _checkpoint_path(run_id, directory)
    if path.exists():
        path.unlink()
        logger.info("Checkpoint deleted: %s", path)
        return True
    return False
