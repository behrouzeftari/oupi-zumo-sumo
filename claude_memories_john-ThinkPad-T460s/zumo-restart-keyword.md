---
name: zumo-restart-keyword
description: "What \"restart\" means in the Zumo sumo class workflow — revert to baseline + reflash"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 796eb6c2-95ee-4ae8-841f-fd9c80ac2042
---

In the OUPI Zumo sumo class, students modify the working program (`custom/sumo2.py`) during each match. When John says the word **"restart"**, it means: return the robot and the working program to the pristine **baseline** so the next group starts from default.

**Why:** each new group of students must begin from the same clean default program, not from the previous group's modifications.

**How to apply** (when "restart" is said in this robot context):
1. `cp sumo2_BASELINE.py custom/sumo2.py` — restore the working program to default.
2. `python3 scripts/flash_robot.py sumo2_BASELINE.py` — reflash the connected robot to default.
3. Tell the user to eject the `MicroPython` drive and reset the robot.

`sumo2_BASELINE.py` is never modified (it's the canonical default). This rule is also written into the shared kit's `CLAUDE.md` so the companion laptop's Claude follows it too. See [[zumo-sumo-baseline]] and [[zumo-sumo-project]].