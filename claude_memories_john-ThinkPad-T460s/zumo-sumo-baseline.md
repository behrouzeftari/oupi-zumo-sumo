---
name: zumo-sumo-baseline
description: The official student-baseline version of sumo2.py and where it lives
metadata: 
  node_type: memory
  type: project
  originSessionId: 796eb6c2-95ee-4ae8-841f-fd9c80ac2042
---

The **official baseline** version of `sumo2.py` — the one students always start from — is **`/home/john/Dropbox/Teaching/sumo2_BASELINE.py`** (established 2026-06-26, 48221 bytes, checksum 3586952). Timestamped snapshots `sumo2_BASELINE_<ts>.py` sit alongside it.

This baseline = the v3 build after off-board/tilt detection was removed, with: bare-wood arena + line-sensor board-edge ESCAPE, no-disengage combat, roaming search, full-power-on-clear-sighting, forward-driving track, and **passive opponent detection** (hearing the other bot's IR emitters). See [[zumo-sumo-project]].

When making new student-baseline changes, update `sumo2_BASELINE.py` (and keep a timestamped copy). The older `sumo2_v3_offboard.py*` names in the same folder are historical backups, not the canonical baseline. See [[always-backup-sumo-to-dropbox]].

**Shareable kit for a companion laptop / programming other robots:** `/home/john/Dropbox/Teaching/zumo_kit/` — self-contained, contains `sumo2_BASELINE.py`, `bot_image/` (full robot filesystem snapshot incl. the `zumo_2040_robot` library), `custom/` (sumo2.py + main.py + main_menu.py), `scripts/` (`flash_robot.py` = mass-storage write+fsync+verify; `identify_bots.py` = USB-serial→letter), and `README.md` documenting the whole workflow (programming, calibration, the eject-or-corrupt rule, passive detection, bot identity). Syncs to any laptop on the same Dropbox. Update the kit when the baseline changes.