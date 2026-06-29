---
name: remount-after-eject
description: After --eject the Zumo drive stays unmounted; remount before the next flash
metadata: 
  node_type: memory
  type: project
  originSessionId: d9f95e00-b845-4503-8b70-a834485cf8a7
---

`scripts/flash_robot.py` requires the Zumo's `MicroPython` drive to be already mounted, and it reports "No Zumo drive mounted" if not. After a flash with `--eject` (the standing preference, see [[restart-resets-baseline]]), the drive is unmounted and does NOT auto-remount even while the robot stays physically connected.

**Before each subsequent flash in a session, remount it first:**
`udisksctl mount -b /dev/sda` (mounts to `/run/media/john/MicroPython`).

Diagnose presence with `lsblk -o NAME,LABEL,FSTYPE,MOUNTPOINT` — the device shows as `sda` / label `MicroPython` / vfat / ~15M with an empty MOUNTPOINT when unmounted. The device letter is usually `/dev/sda`; confirm via `/dev/disk/by-label/MicroPython`.
