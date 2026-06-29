---
name: always-backup-sumo-to-dropbox
description: "Every time sumo2.py changes, also save a backup to the Dropbox/Teaching location"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 796eb6c2-95ee-4ae8-841f-fd9c80ac2042
---

Whenever I modify the Zumo `sumo2.py`, I must ALWAYS also save a backup copy to `/home/john/Dropbox/Teaching/` (the established backup location, e.g. `sumo2_v3_offboard.py`, plus a timestamped archive copy like `sumo2_v3_offboard_<YYYYMMDD-HHMMSS>.py`).

**Why:** John lost earlier work to flash corruption on the bots, so he wants a durable, synced backup of every revision in Dropbox — not just on the (corruption-prone) robot or in the ephemeral scratchpad.

**How to apply:** after every successful edit to the working `sumo2.py`, `cp` it to the Dropbox/Teaching path before/alongside deploying. Don't wait to be asked each time. See [[zumo-sumo-project]] and [[zumo-msc-corruption-hazard]].