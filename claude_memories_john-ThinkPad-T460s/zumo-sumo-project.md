---
name: zumo-sumo-project
description: The OUPI robot-sumo project — Pololu Zumo 2040 bots running sumo2.py (MicroPython)
metadata: 
  node_type: memory
  type: project
  originSessionId: 796eb6c2-95ee-4ae8-841f-fd9c80ac2042
---

John develops `sumo2.py`, an "OUPI Robot Sumo Demo" for **Pololu Zumo 2040** robots (RP2040, MicroPython). `main.py` auto-runs `sumo2.py` on power-up. Robots appear on the host as BOTH a USB mass-storage vfat drive (`/media/john/MicroPython*`, ~15MB) AND a MicroPython serial REPL (`/dev/ttyACM*`, `1ffb:2044`, root:dialout — needs sudo; john not in dialout group).

Per-robot identity comes from `machine.unique_id().hex()`, mapped to letters in `_BOT_IDS`: A=`e4621cb30b28292f`, B=`e4621cb30b57292f`, C=`e4621cb30b3a262f`.

Current arena (as of 2026-06-26): **bare / unfinished wood**, and the arena boundary is the **physical edge of the board (a drop-off, no tape)**. Boundary detection is **line-sensor based** (`edge_status()` + calibration samples WOOD surface vs the OFF-EDGE drop-off, polarity learned automatically). On reaching the edge the bot runs an ESCAPE (back up, turn inward, drive in).

**Tilt/IMU off-board detection: tried and then REMOVED at John's request.** We re-implemented an IMU accelerometer "off-board halt" (first a single hard-coded angle, then a calibrated front/rear/side per-direction version), but it kept false-halting during legitimate combat (riding up on the opponent), so John had it fully removed. `sumo2.py` no longer imports/uses the IMU at all; off-board protection is purely the line-sensor edge ESCAPE. Don't re-add IMU tilt detection unless John explicitly asks.

Other tuning John has asked for: bot must **not disengage while pushing** an opponent (combat-maneuver break-off removed from `handle_attack`); **roaming search** (scan-in-place then roll forward) so it doesn't camp on the edge; improved opponent finding — extended IR `proximity_sensors.brightness_levels` for longer range, `LOST_OPPONENT_MS` raised, and `handle_track` now drives FORWARD toward the opponent (steer/pivot) instead of only rotating; and **full power on clear sighting** (`full_power` latch overrides the slow-start intensity ramp).

**Passive opponent detection** (key feature): the bots couldn't see each other via reflection even at ~2 ft pointing directly (dark/matte robot reflects almost no IR). Fix = `read_passive_opponent()`: turn our own emitters OFF and count how often each prox sensor sees external 56 kHz IR — i.e. the OTHER bot's emitters, which carry far beyond a reflection. Folded into `prox_object_seen` / `prox_clear_sighting` / left-right scores (keys `pl/pf/pr` in `current_prox`); falls back cleanly to active-only when zero. Toggle `PASSIVE_DETECT`; display shows passive total as `*N` on the prox line for diagnosing range.

Working file lives in the session scratchpad; durable backups in `/home/john/Dropbox/Teaching/` (`sumo2_v3_offboard.py` + timestamped archives — see [[always-backup-sumo-to-dropbox]]). Deploy to both bots by writing to the mounted `/media/john/MicroPython*` drives with fsync+verify, then eject. See [[zumo-msc-corruption-hazard]].