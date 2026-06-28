# Zumo Sumo Kit — working instructions for Claude Code

This folder is the shared OUPI **Pololu Zumo 2040** robot-sumo kit, synced between
two laptops via **Dropbox**. Read `README.md` for full background. Follow these
rules so changes reach both the robot and the other laptop.

## Source of truth
- `sumo2_BASELINE.py` is the canonical default program — the clean starting point
  every new group of students begins from. **It is never modified** (treat it as
  read-only) unless the user explicitly says "update the baseline."
- `custom/sumo2.py` is the **working program** students modify during their match,
  and the file that gets flashed to the robot. All student edits go here.

## The "restart" keyword (IMPORTANT)
When the user says **"restart"**, return the working program to the pristine
default AND run the per-match build-selection flow for the next student:
1. Restore the working program from the baseline:
   `cp sumo2_BASELINE.py custom/sumo2.py`
2. Validate + flash, ejecting automatically:
   `python3 -m py_compile custom/sumo2.py`
   `python3 scripts/flash_robot.py custom/sumo2.py --eject`
   (`--eject` is the standing preference — it unmounts cleanly so the user can
   safely press the robot's physical reset button without unplugging.)
3. Then run the **BUILD SELECTION PROTOCOL** — greet the new student and present
   each category as a **numbered 1/2/3 menu in the chat** so they build by typing
   numbers (one per category, e.g. "3 1 1 1 2"; blank → middle option), plus one
   personal tweak; apply them to `custom/sumo2.py`, recompile, and re-flash
   `--eject`. The full protocol is documented in `sumo2_BASELINE.py` (the `BUILD
   SELECTION PROTOCOL` comment block) so it survives restarts and is identical on
   both laptops.
The next group modifies `custom/sumo2.py` again; `sumo2_BASELINE.py` itself is
never touched. (Edge calibration on the robot can stay; "restart" only resets the
program, not the arena calibration, unless the user says otherwise.)

## After EVERY robot-code change — flash it, or the robot won't update
The robot does NOT update from Dropbox automatically. It only changes when its
program is written to its mounted USB drive and the drive is ejected. So whenever
you edit the robot program:
1. Validate it: `python3 -m py_compile custom/sumo2.py`
2. Flash it to the connected robot (writes + checksum-verifies):
   `python3 scripts/flash_robot.py custom/sumo2.py`
3. Tell the user to **eject** the `MicroPython` drive in Files (or run
   `flash_robot.py custom/sumo2.py --eject`), then reset/power-cycle the robot.

## Critical — do not corrupt the flash
- ALWAYS eject the `MicroPython` drive before unplugging or resetting the robot.
  Skipping the eject is what corrupts the Zumo's flash.
- If a drive shows read-only or throws an I/O error: eject and remount it
  (`udisksctl unmount -b /dev/sdX`, then `mount -b /dev/sdX`) and retry.

## Identity & calibration
- `python3 scripts/identify_bots.py` lists connected robots and their A/B/C letter.
- After flashing + reset, the robot calibrates via button **C**: WOOD sample, then
  BOARD-EDGE sample. Then **A** starts a match.

## Sharing between the two laptops
- Files you save in this folder sync via Dropbox to the other laptop automatically.
- If you ever see a Dropbox **"conflicted copy"** file, both laptops edited at the
  same time — reconcile the two versions before flashing a robot.
- Avoid editing `sumo2_BASELINE.py` on both laptops at once.
