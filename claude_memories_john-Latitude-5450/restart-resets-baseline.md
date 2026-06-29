---
name: restart-resets-baseline
description: "What the user means by \"restart\" in the zumo_kit robot-sumo workflow"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d9f95e00-b845-4503-8b70-a834485cf8a7
---

When the user says **"restart"**, they mean: reset the working robot program back to the clean baseline AND run the per-match build-selection flow for the next student. Steps: copy `sumo2_BASELINE.py` over `custom/sumo2.py`, validate with `python3 -m py_compile custom/sumo2.py`, flash with `python3 scripts/flash_robot.py custom/sumo2.py --eject`, THEN run the BUILD SELECTION PROTOCOL (greet the new student, ask their five category choices + one personal tweak, apply to `custom/sumo2.py`, recompile, re-flash `--eject`).

The **BUILD SELECTION PROTOCOL is documented inside `sumo2_BASELINE.py`** (a comment block above the TEAM BOT CONFIG) so it survives restarts and is identical on both laptops via Dropbox. Five categories live in the `TEAM BOT CONFIG` block (CLASS/AGGRESSION/AGILITY/EDGE_NERVE/SIGNATURE) and are already wired to real engine params. Signature moves implemented in `handle_combat_maneuver`: CHARGER (style 1, head-on ram), FLANKER (style 0, pivot to the side), COUNTER-PUNCHER (style 2, give-ground then pivot-shove).

**Always pass `--eject` when flashing** (confirmed preference, 2026-06-27). The user wants the unmount handled automatically so they can safely press the robot's physical reset button without manually ejecting. Pressing reset while the drive is still mounted risks corrupting the Zumo's FAT flash (surprise removal of a mounted volume); a clean eject prevents this and does NOT require unplugging.

**Why:** Students modify `custom/sumo2.py` each match; each new match should start from the canonical baseline. `sumo2_BASELINE.py` stays read-only (per CLAUDE.md) unless the user explicitly says "update the baseline."

**How to apply:** On "restart", do the copy → compile → flash → eject reminder sequence. Do NOT overwrite `sumo2_BASELINE.py`.
