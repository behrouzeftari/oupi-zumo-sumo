# Claude Code — saved memories for the Zumo Sumo Kit

This folder is a **backup of Claude Code's persistent memory** for the OUPI Zumo
2040 robot-sumo project. It is here so the memory state can travel with the kit
(via Dropbox) and be restored on another laptop, letting Claude resume with the
same knowledge of how this project works.

These are **notes Claude wrote for itself** — they are not part of the robot
program and have no effect on the robots. Snapshot taken **2026-06-29**.

**This folder holds the memories for one specific laptop** (`john-Latitude-5450`
— hence the folder name). Memory is machine-local and is NOT synced by Dropbox,
so the *other* laptop has its own separate memory store. It should export into
its OWN hostname-named folder (e.g. `claude_memories_<its-hostname>/`) so the two
dumps never overwrite each other in Dropbox.

NOTE: `remount-after-eject.md` hard-codes this laptop's drive node `/dev/sda` —
that may differ on the other laptop; verify with `lsblk` before reusing it.

## What's in here
| File | What it records |
|---|---|
| `MEMORY.md` | The index Claude loads each session — one line per memory. |
| `restart-resets-baseline.md` | What "restart" means: reset `custom/sumo2.py` to the baseline, flash `--eject`, then run the BUILD SELECTION PROTOCOL (greet, 5-category numbered menu, personal tweak). |
| `remount-after-eject.md` | After a `--eject` the Zumo drive stays unmounted; run `udisksctl mount -b /dev/sda` before the next flash. |

(The full per-match build-selection procedure itself lives in
`../sumo2_BASELINE.py`, in the `BUILD SELECTION PROTOCOL` comment block, so it
already travels with the code.)

## How to restore on another machine
Claude's memory for this project lives in a machine-local directory, NOT in
Dropbox, so it must be copied back after cloning/syncing the kit:

1. Make sure the kit sits at the same path used to derive the project slug, i.e.
   `~/Dropbox/Teaching/zumo_kit` (the slug below is built from that path).
2. Create the memory directory if needed and copy these files into it:
   ```
   mkdir -p ~/.claude/projects/-home-<user>-Dropbox-Teaching-zumo-kit/memory
   cp README's-folder/*.md \
      ~/.claude/projects/-home-<user>-Dropbox-Teaching-zumo-kit/memory/
   ```
   Replace `<user>` with the new machine's username (the original was `john`, so
   the original slug was `-home-john-Dropbox-Teaching-zumo-kit`). Do NOT copy
   this `README_CLAUDE_MEMORIES.md` into the memory dir — only the memory `.md`
   files and `MEMORY.md`.
3. If the username/path differs, also fix any absolute paths inside the copied
   files (and update `MEMORY.md` if you rename anything).
4. Start Claude Code in the kit folder; it will pick up `MEMORY.md` and these
   memories automatically.

## Keeping this backup current
This is a point-in-time copy. If Claude's memories change later, re-export by
copying the live memory directory's `*.md` files back into this folder.
