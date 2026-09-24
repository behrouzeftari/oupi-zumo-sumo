# OUPI Robot Sumo — Activity Runbook

A complete record of how this activity is set up and run, so it can be picked up
again weeks later. Written 2026-06-27.

---

## 1. What the activity is

Students give a **Pololu Zumo 2040** sumo robot a personality and a team color,
then the robot fights another robot in a ring. Students do everything with the
robot's own buttons and OLED menu: they pick a **Persona** (Bear, Lion, or Wolf)
and a **Color** (Blue, Red, or Green). Students do not use a laptop or Claude
Code, and they do not change any code (see §7).

The robot program is `sumo2.py` (MicroPython). Facilitators and developers
maintain and flash it from a laptop with Git and **Claude Code**; between
students they can reset the robot to the approved baseline with the word
**"restart"**.

---

## 2. Hardware

- **Robots:** Pololu Zumo 2040 (RP2040 MCU), running MicroPython. Up to 3 units.
- Each robot self-identifies as **A / B / C** from its RP2040 USB serial number
  (this drives the letter shown on the robot's display):

  | Letter | USB serial |
  |---|---|
  | A | `e4621cb30b28292f` |
  | B | `e4621cb30b57292f` |
  | C | `e4621cb30b3a262f` |

  This map lives in `_BOT_IDS` inside `sumo2.py` and in `scripts/identify_bots.py`.
- **Bot A's flash is flaky** — it intermittently throws I/O errors and goes
  read-only. Recovery is documented in §9.
- When plugged into a laptop each robot appears as:
  - a **USB mass-storage drive** labeled `MicroPython` (this is how we flash code), and
  - a **serial REPL** at `/dev/ttyACM*` (needs sudo; not used in the normal flow).

## 3. Arena

- **Surface:** bare / unfinished **wood**.
- **Boundary:** the **physical edge of the board** (a drop-off). There is **no
  tape**. The robot detects the edge with its downward line sensors; calibration
  learns the difference between the wood surface and the off-board drop-off.

## 4. Laptop setup (GitHub)

The kit is the public GitHub repo, so each laptop just clones its own copy:

```bash
git clone https://github.com/behrouzeftari/oupi-zumo-sumo
```

(This is the current V1 Persona/Color version. It is a fork of the original
project by John Hassell / OU: https://github.com/jhassell/oupi-zumo-sumo.)

- The clone creates an `oupi-zumo-sumo/` folder; that folder **is** the kit (the
  repo root, not a `Teaching/zumo_kit` subfolder).
- **Start Claude Code from inside that folder** so it picks up the project
  instructions in `CLAUDE.md`.
- The repo is the source of truth. Pull the latest before an event with
  `git pull`; commit and push baseline changes you want the other machines to
  get. Flashing a robot is always a local action over USB, so neither Git nor
  Dropbox pushes code to a robot.

## 5. Files & directory layout (all under `oupi-zumo-sumo/`)

```
oupi-zumo-sumo/
├── CLAUDE.md               # project instructions Claude auto-reads (the workflow rules)
├── README.md               # human setup guide for the kit
├── ACTIVITY_RUNBOOK.md     # THIS file
├── sumo2_BASELINE.py       # the canonical DEFAULT program (never edited by students)
├── sumo2_BASELINE_<ts>.py  # timestamped archive snapshots of the baseline
├── custom/                 # the WORKING copy that gets flashed (same as baseline in V1)
│   ├── sumo2.py            #   (this is what gets flashed; reset to baseline on "restart")
│   ├── main.py             #   auto-runs sumo2.py on power-up
│   └── main_menu.py        #   Pololu splash loader (press C during splash to pick a program)
├── bot_image/              # full snapshot of a working robot's filesystem (recovery image;
│                           #   its sumo2.py is older, so flash custom/sumo2.py after using it)
│   ├── zumo_2040_robot/    #   the Pololu MicroPython library (ships on the robot)
│   ├── sumo2.py, main.py, main_menu.py, and the stock example programs
└── scripts/
    ├── flash_robot.py      # write custom/sumo2.py to the mounted robot drive, fsync+verify
    └── identify_bots.py    # list connected robots + their A/B/C letter (by USB serial)
```

- **Source of truth:** `sumo2_BASELINE.py` is the immutable default. It is only
  changed when the facilitator explicitly says "update the baseline."
- **Working file:** `custom/sumo2.py` is what gets flashed. In V1 it is identical
  to the baseline. Students never edit it.

## 6. What `sumo2.py` does (baseline behavior)

- **Search:** roams (slow scan-spin to reliably detect, then rolls forward) so it
  doesn't camp on the edge.
- **Find opponent:** long-range IR **plus passive detection** — it briefly turns
  its own emitters off and "hears" the other robot's 56 kHz IR, so it senses a
  facing opponent across the ring (the display's prox line ends with `*N` = the
  passive count). Toggle with `PASSIVE_DETECT`.
- **Engage:** the instant it clearly sees an opponent it jumps to **full power**;
  it drives toward the opponent and, once pushing, stays committed.
- **Edge safety:** reaching the board edge triggers an ESCAPE (back up, turn in,
  drive in). There is **no IMU tilt detection** (it was tried and removed).
- **Buttons:** A start/stop · B Settings (Persona / Color, when stopped) ·
  C recalibrate (when stopped). The full menu is in §7.
- **Persona** (Bear / Lion / Wolf) sets the fighting behavior from
  `PERSONA_PRESETS`. **Color** (Blue / Red / Green) changes only the LEDs and
  display. Edge detection and escape are the same for every Persona.
- The `TEAM BOT CONFIG` block holds developer/faculty defaults (`TEAM_NAME`,
  `EDGE_NERVE`, `HOUSE_BOT`); it is not student-facing.

## 7. Mode of operation — the student workflow (V1)

Students use only the robot's buttons and OLED menu. They do not use a laptop
or Claude Code, and they do not change any code.

1. **Power on the robot.** After the splash screen it loads the saved edge
   calibration (or asks for one on a new arena — see step 2).
2. **Main menu:**
   - **A** = Start (3-2-1 countdown, then the match begins)
   - **B** = Settings
   - **C** = Recalibrate (WOOD sample, then BOARD-EDGE sample)
3. **Settings:**
   - **A** = Persona
   - **B** = Color
   - **C** = Back (to the Main menu)
4. **Persona:**
   - **A** = Bear — slow and deliberate while searching; hits hard once engaged
   - **B** = Lion — active and mobile; searches and attacks promptly
   - **C** = Wolf — strong tracking and steering; commits quickly
5. **Color:**
   - **A** = Blue
   - **B** = Red
   - **C** = Green
6. After a Persona or Color pick, the robot returns to Settings. Press **C**
   (Back) to return to the Main menu, then **A** to start the match. Pressing
   **A** during a match stops the robot.
7. Persona and Color are student-facing settings only. They can be changed only
   while the robot is stopped, and they reset to **Lion / Blue** when the robot is
   reset, power-cycled, or reflashed.

**Facilitator, between students (optional):** say **"restart"** in Claude Code
to copy `sumo2_BASELINE.py` → `custom/sumo2.py` and flash it with `--eject`
(see `CLAUDE.md`), or simply press the robot's reset button to return to the
defaults. Always eject the drive before resetting (see §9).

## 8. Key commands (run from inside the cloned `oupi-zumo-sumo/` folder)

```bash
# which robots are connected and their letters
python3 scripts/identify_bots.py

# flash the working program to the mounted robot, verify, and cleanly eject
python3 scripts/flash_robot.py custom/sumo2.py --eject

# flash the clean baseline instead
python3 scripts/flash_robot.py sumo2_BASELINE.py --eject

# validate before flashing
python3 -m py_compile custom/sumo2.py
```

The robot mounts at `/media/<user>/MicroPython` (the trailing folder name and the
underlying `/dev/sdX` letter shuffle between sessions — **identify a robot by its
USB serial, never by the mount name or drive letter**).

## 9. Gotchas & recovery (IMPORTANT)

- **Always EJECT before unplugging or resetting** the robot (file-manager eject
  button, or the script's `--eject`). Skipping the eject corrupts the Zumo's
  flash filesystem. This is the single most important rule.
- **Drive shows 0 bytes / "no media":** the robot is **running a program** (it was
  reset to play). Its filesystem isn't writable while running. To flash again,
  **press reset or replug** the robot so the drive re-enumerates, then flash.
  → Practical tip: flash the build **before** the student resets the robot to play.
- **Read-only or I/O error on the drive:** eject and remount, then retry:
  ```bash
  udisksctl unmount -b /dev/sdX    # run from a cwd OUTSIDE /media
  udisksctl mount   -b /dev/sdX
  ```
- **Bot A (`…28292f`) flaky flash:** if a write fails because *reading the old
  file* errors, eject+remount and **overwrite `sumo2.py` directly without reading
  the old file first** (the fresh write lands on good clusters). If writes keep
  failing, that flash may need reformatting or the unit retired.
- **Eject blocked ("target is busy"):** the file manager (nautilus) is holding the
  drive — close/eject it there; don't kill the file manager.
- **Multiple laptops:** each laptop has its own clone, so coordinate baseline
  edits through Git (commit and push, then `git pull` on the others). The robot
  only updates when flashed; neither Git nor Dropbox pushes code to the robot.

## 10. Example builds from the first run (historical reference)

These are from the first run, which used the earlier laptop-based build workflow
(five build options plus a free-text "personal tweak" applied by Claude Code).
That workflow is **not** used in V1 — students now pick a Persona and Color on
the robot (§7). They illustrate the kinds of personal tweaks that were
implemented as real code at the time:

- **Alfie** (green): PROFESSOR/CAUTIOUS/SLUGGISH/CAREFUL/FLANKER; tweak "slow &
  careful" → lowered `MAX_MOTOR_SPEED`.
- **Wall3:** PROFESSOR/BALANCED/TWITCHY/CAREFUL/COUNTER-PUNCHER; tweak "spin on
  contact before accelerating" → brief spin at ATTACK entry.
- **T-1000:** ROOKIE/RECKLESS/NIMBLE/DAREDEVIL/FLANKER; tweak "high torque" →
  shove at full motor power regardless of class.
- **"I got no idea":** added a **DODGE** state — when charged point-blank, back up
  then dart sideways at max speed.
- **Mean Green:** added a random **flank** bias to ~half its attacks.
- **2 Brain Cells:** added a **victory moonwalk** (glide backward with a shuffle
  after winning a clash).
- **90 degrees:** added a **FLANK90** state — when stuck in a shove, snap a fast
  ~90° turn and loop around to hit from the side.

These were all written into `custom/sumo2.py` per-build and wiped on the next
"restart" — the baseline itself stayed clean.

## 11. Resuming in a few weeks — checklist

1. Plug a robot into the laptop; confirm the `MicroPython` drive mounts.
2. `cd` into the cloned `oupi-zumo-sumo` folder and start **Claude Code** there.
3. Ask Claude *"what does 'restart' do here?"* to confirm it loaded `CLAUDE.md`.
4. `python3 scripts/identify_bots.py` to see which bot is which.
5. (First match on a new arena) calibrate each robot: reset → **C** → WOOD sample
   → BOARD-EDGE sample.
6. Say **"restart"** to flash the approved baseline, then run the student
   workflow (§7).
7. If anything looks corrupt/stuck, see §9.

## 12. Tunables (top of `sumo2.py`)

`PASSIVE_DETECT`, `PASSIVE_SEEN`, `PASSIVE_CLEAR`, `CLEAR_SIGHT_COUNT`,
`SEARCH_SPIN_PCT`, `SEARCH_SCAN_MS`, `SEARCH_ADVANCE_MS`, `LOST_OPPONENT_MS`,
`MAX_MOTOR_SPEED`, the `STALEMATE_*` values, `PERSONA_PRESETS` (Bear/Lion/Wolf
behavior), and the `TEAM BOT CONFIG` block.
