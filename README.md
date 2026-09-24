# OUPI Robot Sumo — Zumo 2040 Kit

Everything a laptop needs to program a **Pololu Zumo 2040** robot for the OUPI
robot-sumo demo.

This kit is the public GitHub repo at https://github.com/jhassell/oupi-zumo-sumo.
Clone it (or download the ZIP) onto any laptop to set that machine up.

---

## What's in here

| Path | What it is |
|---|---|
| `sumo2_BASELINE.py` | **The official baseline** students always start from. |
| `bot_image/` | A complete snapshot of a working robot's filesystem (the `zumo_2040_robot` library + every program + `main.py`). Use to set up a fresh/blank robot. |
| `custom/` | Just the OUPI-specific files: `sumo2.py` (= baseline), `main.py`, `main_menu.py`. Use to update a robot that already has the Pololu library. |
| `scripts/flash_robot.py` | Copy `sumo2.py` onto mounted Zumo drive(s) with fsync + checksum verify. |
| `scripts/identify_bots.py` | List connected robots and their A/B/C letter (by USB serial). |

The arena-specific `edge_calib.txt` is intentionally **not** included — each robot
should calibrate fresh for its own arena (see Calibration below).

---

## How a robot runs

- On power-up, `main_menu.py` shows a splash and after ~6 s launches `main.py`,
  which does `exec(open("sumo2.py").read())`. Press **C** during the splash to
  pick a different program instead.
- Each robot self-identifies as **A / B / C** from its RP2040 serial (the
  `_BOT_IDS` map in `sumo2.py`); the letter shows on its display.

## What `sumo2.py` does (current baseline behavior)

- **Arena:** bare / unfinished wood; the boundary is the **physical edge of the
  board** (a drop-off, no tape). Edge detection is line-sensor based; on reaching
  the edge the robot backs up, turns inward, and drives back in (ESCAPE).
- **Search:** roams (slow scan-spin to reliably catch a target, then rolls
  forward into open space) instead of camping on the edge.
- **Find each other:** long-range IR plus **passive opponent detection** — with
  its own emitters briefly off, each robot hears the *other* robot's 56 kHz IR,
  which carries far past a reflection (so two bots facing each other across the
  ring detect one another). The prox line on the display ends with `*N` = the
  passive count, for diagnosing range.
- **Engage:** the moment a robot **clearly** sees an opponent it jumps to **full
  power** (overriding the slow-start ramp); it drives toward the opponent and,
  once pushing, **does not disengage** on its own.
- Buttons: **A** start/stop · **B** difficulty (when stopped) · **C** recalibrate
  (when stopped).

Handy tunables near the top of `sumo2.py`: `PASSIVE_DETECT`, `PASSIVE_SEEN`,
`CLEAR_SIGHT_COUNT`, `SEARCH_SPIN_PCT`, `LOST_OPPONENT_MS`, and the team-config
block (`TEAM_NAME`, `CLASS`, `AGGRESSION`, `AGILITY`, `EDGE_NERVE`, `SIGNATURE`).

---

## Programming a robot

A Zumo 2040 shows up as a USB flash drive named **MicroPython** (and a serial
REPL on `/dev/ttyACM*`). We program via the **mass-storage drive**.

### Quick update (robot already has the Pololu library — the usual case)
1. Plug in the robot; it mounts at `/media/<you>/MicroPython`.
2. `python3 scripts/flash_robot.py`  ← writes `sumo2_BASELINE.py`, fsync, verifies.
   (Or just drag `custom/sumo2.py` onto the drive.)
3. **Eject** the drive (see the critical note below), then reset the robot.

### Full setup (fresh/blank robot)
1. Copy the entire contents of `bot_image/` onto the robot's MicroPython drive.
2. Eject, reset.

### ⚠️ CRITICAL — don't corrupt the flash
**Always eject the drive (file-manager eject button) before unplugging or
resetting the robot.** Writing while mounted and yanking it without a clean eject
is what corrupts the Zumo's flash filesystem (we lost work this way). The flash
helper runs `sync` and can `--eject` for you, but a clean eject is the real fix.
If a drive ever shows read-only or throws I/O errors, eject and remount it
(`udisksctl unmount -b /dev/sdX` then `mount -b /dev/sdX`) and retry.

---

## Calibration (do this once per robot, per arena)

Press **C** on the robot (or it runs automatically on first boot with no saved
calibration):
1. **WOOD SAMPLE** — place the robot flat on the bare wood, press C.
2. **BOARD-EDGE SAMPLE** — hold the front sensors out over the board edge (the
   drop-off), press C.

The robot learns the midpoint and which way means "off the board" automatically.
Saved to `edge_calib.txt`; press C anytime (when stopped) to redo it.

---

## Robot identity

`scripts/identify_bots.py` lists connected robots and their letter. Current map:

| Serial | Letter |
|---|---|
| `e4621cb30b28292f` | A |
| `e4621cb30b57292f` | B |
| `e4621cb30b3a262f` | C |

(The same map is `_BOT_IDS` in `sumo2.py`. A robot's letter only affects its
display name; the code is identical on every robot.)

**Known issue:** Bot A (`…28292f`) has a flaky flash — it sometimes throws I/O
errors and goes read-only. Workaround: eject + remount, then overwrite `sumo2.py`
directly (don't try to read the old file first). If it keeps failing, that flash
may need reformatting/reflashing.

---

## Using one or more laptops

The kit is the GitHub repo, so each laptop just clones its own copy with
`git clone https://github.com/jhassell/oupi-zumo-sumo`. The repo is the source of
truth: pull the latest before an event with `git pull`, and commit and push any
baseline changes you want other machines to pick up. Flashing a robot is always a
local action over USB, so neither Git nor Dropbox pushes code to a robot (see
Programming a robot).


---

## Behrouz's Contribution

This repository is a fork of the original OUPI Robot Sumo project by John Hassell / OU.

The idea for introducing student-selectable robot Personas and Colors was proposed by John Hassell. My contribution was to develop and implement the student-facing interface, tune the Persona behaviors, update the baseline implementation, and test the system on the physical robots.

### Student Persona System

Students can choose a robot Persona to give their robot a different behavioral style:

| Persona | Behavior |
|---|---|
| **Bear** | Slow and deliberate; becomes strong and committed when an opponent is detected. |
| **Lion** | Active and mobile; searches, moves, and attacks. |
| **Wolf** | Target-oriented; focuses more strongly on steering toward and pursuing an opponent. |

Students can also select a team color:

- Blue
- Red
- Green

### Robot Menu

```text
MAIN
├── A = Start
├── B = Settings
│   ├── A = Persona
│   │   ├── Bear
│   │   ├── Lion
│   │   └── Wolf
│   └── B = Color
│       ├── Blue
│       ├── Red
│       └── Green
└── C = Recalibrate
```

### Hardware Testing

The updated software was flashed and tested on three physical Pololu Zumo 2040 robots.

### Development Environment

- Windows 11
- WSL2 Ubuntu
- Python / MicroPython
- Git
- Claude Code
- Pololu Zumo 2040
