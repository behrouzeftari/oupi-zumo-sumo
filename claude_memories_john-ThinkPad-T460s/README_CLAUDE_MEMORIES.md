# Claude Code — saved memories for the Zumo Sumo Kit

This folder is a **backup of Claude Code's persistent memory** for the OUPI Zumo
2040 robot-sumo project. It is here so the memory state can travel with the kit
(via Dropbox) and be restored on another laptop, letting Claude resume with the
same knowledge of how this project works.

These are **notes Claude wrote for itself** — they are not part of the robot
program and have no effect on the robots. Snapshot taken **2026-06-29**.

**This folder holds the memories for one specific laptop.**

| | |
|---|---|
| **Hostname** | `john-ThinkPad-T460s` (hence the folder name) |
| **Username** | `john` |
| **Original memory dir** | `/home/john/.claude/projects/-media-john/memory/` |
| **Project slug** | `-media-john` |

The slug `-media-john` comes from the fact that this laptop's Claude session ran
with the working directory `/media/john` (where the robots mount). That is a
**different slug** from the other laptop (`john-Latitude-5450`), whose Claude ran
inside the kit folder and therefore used the slug
`-home-john-Dropbox-Teaching-zumo-kit`. Each laptop formed its **own** memories;
the two sets are different files and do not overwrite each other (except both
have a `MEMORY.md` index — see restore notes).

**Drive nodes:** these memories do NOT hard-code any machine-specific drive node.
They only mention `/dev/sdX`, `/dev/sdc`, and `/dev/ttyACM0` as *generic examples*
of the dynamic robot drives / sysfs mapping (the robot mounts shuffle every
session, so they are identified by USB serial, not drive letter). `lsblk` on this
machine shows the system disk is `/dev/sda` (476 GB), but nothing here depends on
that — no fix needed.

## What's in here
| File | What it records |
|---|---|
| `MEMORY.md` | The index Claude loads each session — one line per memory. |
| `zumo-sumo-project.md` | Project overview: Pololu Zumo 2040 + MicroPython, the A/B/C bot serial map, bare-wood/board-edge arena, that IMU tilt detection was tried and removed, and the tuning knobs. |
| `zumo-sumo-baseline.md` | The official baseline is `sumo2_BASELINE.py`; the shareable kit lives at `Dropbox/Teaching/zumo_kit/`. |
| `zumo-restart-keyword.md` | "restart" = reset `custom/sumo2.py` to the baseline + reflash the robot, for the next student group. |
| `always-backup-sumo-to-dropbox.md` | Every change to `sumo2.py` is also backed up to `Dropbox/Teaching/`. |
| `zumo-msc-corruption-hazard.md` | Eject-or-corrupt rule, read-only/I-O recovery, Bot A's flaky flash, identify-bots-by-serial. |

(The full per-match build-selection procedure itself lives in
`../sumo2_BASELINE.py`, in the `BUILD SELECTION PROTOCOL` comment block, so it
already travels with the code.)

## How to restore on another machine
Claude's memory for this project lives in a machine-local directory, NOT in
Dropbox, so it must be copied back after syncing/cloning the kit:

1. Determine the target machine's project slug — it is derived from the working
   directory you start Claude Code in. If you start Claude in the kit folder
   (`~/Dropbox/Teaching/zumo_kit`), the slug will look like
   `-home-<user>-Dropbox-Teaching-zumo-kit`.
2. Create that memory directory and copy these memory files into it:
   ```
   mkdir -p ~/.claude/projects/<target-slug>/memory
   cp <this-folder>/*.md ~/.claude/projects/<target-slug>/memory/
   ```
   Do NOT copy this `README_CLAUDE_MEMORIES.md` into the memory dir — only the
   memory `.md` files and `MEMORY.md`.
3. **Merge, don't clobber, `MEMORY.md`.** If the target machine already has its
   own memories (e.g. the other laptop's set, or a previous restore), its
   `MEMORY.md` index is different from this one. Combine the bullet lines from
   both `MEMORY.md` files into one index rather than overwriting, so no memory is
   orphaned.
4. If the username/path differs, fix any absolute paths inside the copied files
   (they assume user `john`).
5. Start Claude Code; it will pick up `MEMORY.md` and these memories
   automatically.

## Keeping this backup current
This is a point-in-time copy (2026-06-29). If Claude's memories change later,
re-export by copying the live memory directory's `*.md` files
(`/home/john/.claude/projects/-media-john/memory/*.md`) back into this folder.
