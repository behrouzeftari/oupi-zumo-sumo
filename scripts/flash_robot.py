#!/usr/bin/env python3
"""Flash sumo2.py onto a Pololu Zumo 2040 via its USB mass-storage drive, with
fsync + checksum verification.

Usage:
    python3 flash_robot.py [SOURCE.py] [--eject]

SOURCE defaults to ../sumo2_BASELINE.py (the kit baseline). Every mounted Zumo
drive (a folder named MicroPython* under /media/<you>) is targeted.

IMPORTANT: after flashing, EJECT the drive (the eject button in your file
manager, or rerun with --eject) BEFORE unplugging or resetting the robot.
Skipping the eject is what corrupts the Zumo's flash. The script also runs
`sync`, but a clean eject is what commits the FAT safely.
"""
import os, sys, glob, getpass, subprocess


def zumo_mounts():
    user = getpass.getuser()
    pats = [f"/media/{user}/MicroPython*",
            f"/run/media/{user}/MicroPython*",
            "/media/MicroPython*"]
    found = []
    for p in pats:
        found += glob.glob(p)
    return sorted({m for m in found if os.path.isdir(m)})


def flash(src, mount):
    data = open(src, "rb").read()
    want = (len(data), sum(data))
    dst = os.path.join(mount, "sumo2.py")
    # best-effort backup of whatever is there now
    try:
        open(os.path.join(mount, "sumo2_prev.py"), "wb").write(open(dst, "rb").read())
    except OSError:
        pass
    with open(dst, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    rb = open(dst, "rb").read()
    ok = (len(rb), sum(rb)) == want
    print("  %-32s wrote %d B, cksum %d -> %s"
          % (mount, want[0], want[1], "VERIFIED" if ok else "MISMATCH!!!"))
    return ok


def main():
    args = sys.argv[1:]
    eject = "--eject" in args
    args = [a for a in args if a != "--eject"]
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.abspath(args[0] if args else os.path.join(here, "..", "sumo2_BASELINE.py"))
    if not os.path.exists(src):
        sys.exit("source not found: " + src)

    mounts = zumo_mounts()
    if not mounts:
        sys.exit("No Zumo drive mounted (looked for /media/<you>/MicroPython*).")

    print("Source: %s (%d bytes)" % (src, os.path.getsize(src)))
    ok = True
    for m in mounts:
        try:
            ok &= flash(src, m)
        except OSError as e:
            print("  %-32s FAILED (%s)" % (m, e))
            print("     -> if read-only / I/O error: eject+remount the drive and retry.")
            ok = False
    subprocess.run(["sync"])

    if eject:
        for m in mounts:
            dev = subprocess.run(["findmnt", "-no", "SOURCE", m],
                                 capture_output=True, text=True).stdout.strip()
            if dev:
                subprocess.run(["udisksctl", "unmount", "-b", dev])
                print("  ejected", dev)
    else:
        print("\nNOTE: eject the drive(s) in your file manager before unplugging or")
        print("      resetting the robot (or rerun with --eject). Skipping the eject")
        print("      can corrupt the Zumo's flash.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
