#!/usr/bin/env python3
"""List connected Pololu Zumo 2040 robots and their A/B/C letter.

The letter comes from each RP2040's USB serial number, matching the _BOT_IDS
map inside sumo2.py. Edit BOT_IDS below if your robots differ. (You can also
just read the letter off each robot's own display at boot.)
"""
import glob

# serial -> letter  (keep in sync with _BOT_IDS in sumo2.py)
BOT_IDS = {
    "e4621cb30b28292f": "A",
    "e4621cb30b57292f": "B",
    "e4621cb30b3a262f": "C",
}


def main():
    serials = []
    for d in glob.glob("/sys/bus/usb/devices/*/"):
        try:
            if (open(d + "idVendor").read().strip() == "1ffb"
                    and open(d + "idProduct").read().strip() == "2044"):
                serials.append(open(d + "serial").read().strip())
        except OSError:
            pass
    if not serials:
        print("No Zumo 2040 robots detected on USB.")
        return
    print("Connected Zumo 2040 robots:")
    for s in sorted(serials):
        print("  Bot %-3s serial %s" % (BOT_IDS.get(s, "?"), s))


if __name__ == "__main__":
    main()
