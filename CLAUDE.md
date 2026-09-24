# Zumo Sumo Kit — working instructions for Claude Code

This folder is the shared OUPI **Pololu Zumo 2040** robot-sumo kit, synced between
two laptops via **Dropbox**. Read `README.md` for full background. Follow these
rules so changes reach both the robot and the other laptop.

## Student workflow vs. development workflow
- **Students** do not use Claude Code, a laptop, or the source code. They set up
  the robot only with its physical buttons and OLED menu:
  - MAIN: **A** Start · **B** Settings · **C** Recalibrate
  - SETTINGS: **A** Persona · **B** Color · **C** Back
  - Persona: **Bear** / **Lion** / **Wolf** (fighting behavior)
  - Color: **Blue** / **Red** / **Green** (LED/display identity only)
  - They start the match with **A** on MAIN, and recalibrate with **C** on MAIN
    when needed. **A** during a match stops the robot.
- **Developers/maintainers** use this repository, Git, Python/MicroPython, and
  Claude Code to change, validate, and flash the program. Everything below is
  for developers.

## Source of truth
- `sumo2_BASELINE.py` is the canonical default program — the approved V1
  (Persona/Color) program every robot should run. **It is never modified**
  (treat it as read-only) unless the user explicitly says "update the baseline."
- `custom/sumo2.py` is the **working copy** that gets flashed to the robot. In V1
  it is identical to the baseline. Developer edits go here first; students never
  edit code.

## The "restart" keyword (IMPORTANT)
When the user says **"restart"**, return the working program to the approved
baseline and flash it, so the next student starts from the default robot:
1. Restore the working program from the baseline:
   `cp sumo2_BASELINE.py custom/sumo2.py`
2. Validate + flash, ejecting automatically:
   `python3 -m py_compile custom/sumo2.py`
   `python3 scripts/flash_robot.py custom/sumo2.py --eject`
   (`--eject` is the standing preference — it unmounts cleanly so the user can
   safely press the robot's physical reset button without unplugging.)
3. The robot is then ready. The student picks Persona and Color with the robot's
   buttons (defaults after reset: Lion, Blue). There is no chat build menu and no
   per-student code change in V1.
(Edge calibration on the robot can stay; "restart" only resets the program, not
the arena calibration, unless the user says otherwise.)

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
