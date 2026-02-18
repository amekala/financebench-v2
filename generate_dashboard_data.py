#!/usr/bin/env python3
"""Generate dashboard JSON from saved transcripts."""
import os, json, urllib3
urllib3.disable_warnings()
from dotenv import load_dotenv; load_dotenv()
from pathlib import Path
from financebench.model import ElementLanguageModel
from financebench.scoring import score_phase
from financebench.outcomes import determine_outcome
from financebench.configs import characters, company
from financebench.configs.phases import ALL_PHASES

key = os.getenv("ELEMENT_API_KEY")
url = os.getenv("ELEMENT_GATEWAY_URL")
model = ElementLanguageModel(model_name="gpt-4.1", api_key=key, azure_endpoint=url)

transcripts_dir = Path("transcripts")
phases_data = []
prev_scores = None

for phase_def in ALL_PHASES:
    fname = sorted(transcripts_dir.glob(f"phase_{phase_def.number:02d}_*.txt"))
    if not fname:
        print(f"  Skipping phase {phase_def.number} (no transcript)")
        continue
    transcript = fname[0].read_text()
    print(f"  Scoring Phase {phase_def.number}: {phase_def.name}...")

    ev = score_phase(
        model=model,
        transcript=transcript,
        phase_number=phase_def.number,
        phase_name=phase_def.name,
        previous_scores=prev_scores,
    )
    prev_scores = ev.scores
    phase_data = ev.to_dict()
    phase_data["date"] = phase_def.date
    phase_data["quarter"] = phase_def.quarter
    phase_data["gate"] = phase_def.gate
    phase_data["stakes"] = phase_def.stakes
    phase_data["scene_type"] = phase_def.scene_type
    phase_data["participants"] = phase_def.participants
    phase_data["company_state"] = phase_def.company_state
    phases_data.append(phase_data)
    print(f"    \u2192 Readiness: {ev.scores.promotion_readiness}%")

final = phases_data[-1]
final_scores = final["scores"]
outcome = determine_outcome(
    promotion_readiness=final_scores["promotion_readiness"],
    ethics_score=final_scores["ethics"],
)

dashboard = {
    "experiment": {
        "name": "PromotionBench",
        "version": "2.1.0",
        "run_date": "2026-02-18",
        "total_phases": 9,
        "phases_completed": len(phases_data),
        "variant": "neutral",
    },
    "protagonist": {
        "name": "Riley Nakamura",
        "model": characters.RILEY.model,
        "current_title": characters.RILEY.title,
        "target_title": "Chief Financial Officer",
        "starting_comp": 210000,
    },
    "company": {
        "name": company.COMPANY_NAME,
        "arr": company.FINANCIALS["arr"],
        "industry": company.INDUSTRY,
        "hq": company.HEADQUARTERS,
    },
    "cast": [
        {
            "name": c.name,
            "title": c.title,
            "model": c.model,
            "role": "Protagonist" if c.is_player else "NPC",
        }
        for c in characters.ALL_CHARACTERS
    ],
    "phases": phases_data,
    "outcome": outcome.to_dict(),
}

out = Path("docs/data/results.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(dashboard, indent=2, default=str))
print(f"\n\u2705 Dashboard JSON written to {out}")
print(f"   Outcome: {outcome.title} (${outcome.compensation:,})")
print(f"   Narrative: {outcome.narrative}")
