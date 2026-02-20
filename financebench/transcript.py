"""Transcript extraction from Concordia simulation logs.

Handles three log formats:
  1. SimulationLog object (return_structured_log=True)
  2. List of dicts (legacy format)
  3. Raw string fallback
"""

from __future__ import annotations

# Max characters to send to the scoring judge.
MAX_TRANSCRIPT_CHARS = 12000


def extract_transcript(raw_log) -> str:
    """Extract readable transcript from a Concordia log.

    This is the primary entry point.  Delegates to format-
    specific helpers based on the log type.
    """
    if hasattr(raw_log, "entries"):
        return _extract_from_simulation_log(raw_log, MAX_TRANSCRIPT_CHARS)

    if isinstance(raw_log, list):
        return _extract_from_dict_log(raw_log, MAX_TRANSCRIPT_CHARS)

    text = raw_log if isinstance(raw_log, str) else str(raw_log)
    return _salvage_dialogue(text)[:MAX_TRANSCRIPT_CHARS]


# ── Format-specific helpers ─────────────────────────────────────

def _extract_from_simulation_log(sim_log, max_chars: int) -> str:
    """Extract dialogue from a Concordia SimulationLog."""
    lines: list[str] = []
    for entry in sim_log.entries:
        summary = getattr(entry, "summary", "")
        if summary and _is_dialogue(summary):
            lines.append(summary.strip())

        data = getattr(entry, "deduplicated_data", {})
        if not data:
            continue

        try:
            reconstructed = sim_log.reconstruct_value(data)
        except Exception:
            reconstructed = data

        if isinstance(reconstructed, dict):
            for key in ("action", "resolve"):
                val = reconstructed.get(key)
                if isinstance(val, str) and val.strip() and _is_dialogue(val):
                    lines.append(val.strip())
                elif isinstance(val, dict):
                    for v in val.values():
                        if (
                            isinstance(v, str)
                            and v.strip()
                            and _is_dialogue(v)
                        ):
                            lines.append(v.strip())

    if lines:
        deduped = [lines[0]]
        for line in lines[1:]:
            if line != deduped[-1]:
                deduped.append(line)
        return "\n\n".join(deduped)[:max_chars]

    # Fallback: use get_summary()
    try:
        summary = sim_log.get_summary()
        if isinstance(summary, dict):
            parts = [f"{k}: {v}" for k, v in summary.items()]
            return "\n".join(parts)[:max_chars]
        return str(summary)[:max_chars]
    except Exception:
        return str(sim_log)[:max_chars]


def _extract_from_dict_log(log_list: list, max_chars: int) -> str:
    """Extract dialogue from a lis log."""
    lines: list[str] = []
    for entry in log_list:
        if not isinstance(entry, dict):
            continue
        resolve = entry.get("resolve", {})
        if isinstance(resolve, dict):
            for val in resolve.values():
                if (
                    isinstance(val, str)
                    and val.strip()
                    and _is_dialogue(val)
                ):
                    lines.append(val.strip())
        action = entry.get("action", "")
        if isinstance(action, str) and action.strip() and _is_dialogue(action):
            lines.append(action.strip())
    if lines:
        return "\n\n".join(lines)[:max_chars]
    return str(log_list)[:max_chars]


def _is_dialogue(text: str) -> bool:
    """Return True if text looks like actual dialogue, not setup."""
    setup_markers = (
        "The instructions for how to play",
        "This is a social science experiment",
        "tabletop roleplaying game",
        "What kind of person is",
        "What situation is",
        "What would a person like",
        "[observation]",
    )
    return not any(marker in text for marker in setup_markers)


def _salvage_dialogue(text: str) -> str:
    """Extract dialogue lines from raw string dump."""
    lines: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if " -- " in line or line.startswith("Event:"):
            lines.append(line)
        elif line.startswith("Terminate?"):
            lines.append(line)
    return "\n\n".join(lines) if lines else text[:8000]
