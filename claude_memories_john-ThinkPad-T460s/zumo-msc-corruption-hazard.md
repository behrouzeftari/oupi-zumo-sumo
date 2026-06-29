---
name: zumo-msc-corruption-hazard
description: "Editing files on the Zumo's mounted USB drive corrupts its flash — use the serial REPL instead"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 796eb6c2-95ee-4ae8-841f-fd9c80ac2042
---

Two Zumo 2040 bots had their `sumo2.py` corrupted on the flash itself (one read `OSError EIO` past the first 4KB cluster even via the robot's own REPL; the other was truncated to 4096B). The likely cause: editing files directly on the mounted USB mass-storage drive (`/media/john/MicroPython*`) and resetting/unplugging without a safe eject, while the RP2040 also had the filesystem mounted — concurrent FAT access corrupts it.

**Why:** the damaged tail data was never committed intact to flash, and it was unrecoverable from both the host mount and the robot REPL.

**How to apply (deploying a file to a bot):** the reliable path for a ~40-47KB file like `sumo2.py` is to write directly to the mounted MSC drive, then `f.flush()`+`os.fsync()`+`sync`, then **read it back and compare length+checksum**, then **cleanly eject** (udisksctl unmount, or the eject button in Files) BEFORE resetting/unplugging the bot. The clean eject + sync is what was missing when the earlier bots got corrupted — writing itself is fine. NOTE: a chunked write over the serial **raw REPL fails with "memory allocation failed"** on a file this size (RP2040 runs out of RAM), so don't use the REPL to push large files. When ejecting, the mount is often held busy by **nautilus** (the Files window) — the user must close/eject it; don't kill their file manager.

**Bot A (`e4621cb30b28292f`) has a failing flash:** its filesystem repeatedly throws `Input/output error` and drops to read-only (`errors=remount-ro`). Workarounds that worked 2026-06-26: clear the ro state with `udisksctl unmount -b /dev/sdX` then `mount -b` (run from a cwd outside `/media/john`), then **overwrite `sumo2.py` directly without reading the old file first** (the EIO was triggered by reading the old file on a bad sector); the fresh write went to good clusters and verified + persisted across a remount. If writes keep failing, Bot A's flash likely needs reformatting/reflashing or the unit is degrading.

**How to apply (reading/recovering a file):** reading a file off a bot over the raw REPL (base64) works and bypasses a stale/remounted-ro MSC view. Reading the serial port needs sudo (john is not in the `dialout` group). Map a bot's MSC node to its serial port via sysfs (e.g. `/dev/sdc` and `/dev/ttyACM0` share the same `usbN/x-y` path). See [[zumo-sumo-project]].