# sumo2.py
#
# OUPI Robot Sumo Demo for Pololu Zumo 2040 -- Version 3
#
# Arena setup:
#   SAFE SURFACE = bare / unfinished wood arena
#   EDGE MARKER  = the physical edge of the board (a drop-off, no tape)
#
# Buttons:
#   A = start / stop match
#   B = change difficulty when stopped
#   C = recalibrate edge when stopped
#
# Startup calibration (board-edge detection):
#   1. One sample on the bare wood surface (robot sitting flat).
#   2. One sample with the front sensors out over the board edge (the drop-off).
#   3. Per sensor, the trigger point is the midpoint between the two readings,
#      and the direction (which way means "off the board") is learned
#      automatically, so it works no matter how the bare wood reflects IR.
#
# Combat:
#   Once it is pushing an opponent it stays committed and will not break off on
#   its own -- it keeps driving until the opponent is gone (or it reaches the
#   board edge, which sends it into an escape).
#
# Important:
#   If the program crashes, it should show PROGRAM ERROR on the display.

from zumo_2040_robot import robot
import time
import random
import machine

try:
    from micropython import const
except ImportError:
    def const(x):
        return x


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

VERSION = 3


# ---------------------------------------------------------------------------
# Bot identity (derived from each RP2040's unique hardware serial)
# ---------------------------------------------------------------------------

_SERIAL = machine.unique_id().hex()
_BOT_IDS = {
    "e4621cb30b28292f": "A",
    "e4621cb30b57292f": "B",
    "e4621cb30b3a262f": "C",
}
BOT_ID = _BOT_IDS.get(_SERIAL, _SERIAL[-4:])


# ---------------------------------------------------------------------------
# TEAM BOT CONFIG  (set these from the team's paper design sheet)
# ---------------------------------------------------------------------------
#
# Faculty: copy the five choices off the team's design sheet into the values
# below, then flash this file to that team's robot. Spelling and case do not
# have to be exact -- an unknown value just falls back to the middle option,
# so a typo can never crash a match.
#
# To run the locked House Champion instead, set HOUSE_BOT = True; the team
# values below are then ignored.

HOUSE_BOT = False

TEAM_NAME  = "CHALLENGER"     # shown on the robot's display
TEAM_COLOR = "BLUE"           # RED GREEN BLUE YELLOW PURPLE WHITE

CLASS      = "STUDENT"        # ROOKIE  STUDENT  PROFESSOR  (raw speed tier)
AGGRESSION = "BALANCED"       # CAUTIOUS BALANCED RECKLESS  (how hard it commits)
AGILITY    = "NIMBLE"         # SLUGGISH NIMBLE  TWITCHY    (turn sharpness)
EDGE_NERVE = "NORMAL"         # CAREFUL  NORMAL  DAREDEVIL  (edge risk-taking)
SIGNATURE  = "CHARGER"        # CHARGER  FLANKER COUNTER    (favourite move)


# ---------------------------------------------------------------------------
# Hardware
# ---------------------------------------------------------------------------

motors = robot.Motors()
proximity_sensors = robot.ProximitySensors()
# Extend IR detection range so the bots spot each other from farther away.
# Brighter pulse levels added on top of the library defaults; the top level is
# near the PWM ceiling for 56 kHz (~17.8 us period) for maximum reflection range.
proximity_sensors.brightness_levels = [313, 1000, 2063, 3500, 5375, 7563, 11000, 15000, 17500]
line_sensors = robot.LineSensors()
encoders = robot.Encoders()

button_a = robot.ButtonA()
button_b = robot.ButtonB()
button_c = robot.ButtonC()

display = robot.Display()
rgb_leds = robot.RGBLEDs()
rgb_leds.set_brightness(4)

try:
    buzzer = robot.Buzzer()
except Exception:
    buzzer = None


# ---------------------------------------------------------------------------
# Basic constants
# ---------------------------------------------------------------------------

MAX_MOTOR_SPEED = const(6000)

# Change this to -1 if a simple forward command makes the robot drive backward.
MOTOR_DIRECTION = const(1)

# Proximity readings usually range from 0 to about 6.
SENSOR_THRESHOLD = const(1)
CENTER_BALANCE_MARGIN = const(1)
# A "clear sighting" -- this many counts on any proximity sensor -- latches the
# match to full power (overriding the slow-start ramp).
CLEAR_SIGHT_COUNT = const(2)

# Passive opponent detection: with our own IR emitters off, the proximity sensors
# still pick up the OTHER robot's 56 kHz emitters, which reach far beyond a
# reflection. This lets two bots facing each other across the ring detect one
# another (the reflection alone is far too weak at that range). Counts are out of
# PASSIVE_SAMPLES per scan. Set PASSIVE_DETECT = False to disable.
PASSIVE_DETECT = True
PASSIVE_SAMPLES = const(24)     # sensor reads per passive scan (~3 ms)
PASSIVE_SEEN = const(4)         # total lows that count as "opponent out there"
PASSIVE_CLEAR = const(9)        # total lows that count as a clear sighting (full power)
# FRONT_ATTACK_THRESHOLD is set from AGGRESSION in the team-config section.

# Lost-opponent timing.
LOST_OPPONENT_MS = const(1100)

# Escape timing.
BACKUP_MS = const(300)
TURN_AWAY_MS = const(600)

# Escape speeds.
ESCAPE_BACKUP_SPEED = const(2600)
ESCAPE_TURN_SPEED = const(3000)

# Forward drive after turning away from edge. A longer push moves the robot well
# clear of the boundary instead of lingering right next to it.
ESCAPE_FORWARD_MS = const(700)
ESCAPE_FORWARD_SPEED = const(2600)

# Search roaming: scan in place to look around, then roll forward into open
# space, so the robot keeps moving toward the middle instead of camping next to
# an edge. Edge detection still preempts the forward roll and turns us inward.
SEARCH_SCAN_MS = const(900)
SEARCH_ADVANCE_MS = const(600)
SEARCH_SPIN_PCT = const(65)               # scan-spin speed as % of search speed (slower = surer detection)

# Display update rate.
DISPLAY_UPDATE_MS = const(120)

# STEER_GAIN (steering while attacking) is set from AGILITY in the team-config
# section.

# Stalemate detection (time-based + slip-proof; encoder stall is a fast path).
# Time in ATTACK is the primary trigger because it fires whether the treads
# stall OR keep slipping. Encoders only tell us if the treads stopped turning,
# which does not happen when they slip on a smooth surface.
STALEMATE_MIN_MS = const(1200)            # Min time in ATTACK before breaking off
STALEMATE_MAX_MS = const(2000)            # Max time (randomized per engagement)
STALEMATE_ENCODER_THRESHOLD = const(6)    # Tread movement below this = stalled
STALEMATE_CHECK_MS = const(200)           # Encoder sampling interval
STALL_TRIGGER_COUNT = const(3)            # Consecutive stalled samples = break off early

# Match intensity ramp -- robots start slow and build to full speed.
RAMP_DURATION_MS = const(20000)          # Time to reach full intensity
RAMP_START_PCT = const(40)               # Starting speed as % of full

# Combat maneuver phase durations.
MANEUVER_BACKUP_MS = const(150)           # Brief reverse
MANEUVER_TURN_MS = const(250)             # Angled turn
MANEUVER_BURST_MS = const(300)            # Forward burst

# RGB colors.
RGB_OFF = (0, 0, 0)
RGB_RED = (255, 0, 0)
RGB_GREEN = (0, 255, 0)
RGB_BLUE = (0, 0, 255)
RGB_YELLOW = (255, 64, 0)
RGB_PURPLE = (160, 0, 255)
RGB_WHITE = (255, 255, 255)


# ---------------------------------------------------------------------------
# Difficulty levels
# ---------------------------------------------------------------------------

# name, search_speed, track_speed, attack_speed
DIFFICULTIES = [
    ("ROOKIE",    1800, 1500, 2600),
    ("STUDENT",   3000, 2400, 4000),
    ("PROFESSOR", 4200, 3200, 5000),
]

# ---------------------------------------------------------------------------
# Apply team config -> engine parameters
# ---------------------------------------------------------------------------
#
# Each named choice on the design sheet maps to safe numbers the engine already
# understands, so a paper sheet fully defines a robot's behaviour. Every option
# stays inside ranges that have been bench-tested, so no combination crashes.

# Locked House Champion. Editing these changes the champion for everyone, so
# leave them alone unless that is what you intend.
if HOUSE_BOT:
    TEAM_NAME  = "HOUSE BOT"
    TEAM_COLOR = "WHITE"
    CLASS      = "STUDENT"
    AGGRESSION = "BALANCED"
    AGILITY    = "NIMBLE"
    EDGE_NERVE = "NORMAL"
    SIGNATURE  = "CHARGER"

# CLASS -> base speed tier.
_CLASS_INDEX = {"ROOKIE": 0, "STUDENT": 1, "PROFESSOR": 2}
difficulty_index = _CLASS_INDEX.get(CLASS.upper(), 1)

# AGGRESSION -> (attack-speed %, front strength needed to commit to ATTACK).
# A lower threshold means the robot commits to a charge sooner.
_AGGRO = {"CAUTIOUS": (85, 3), "BALANCED": (100, 2), "RECKLESS": (120, 1)}
AGGRO_PCT, FRONT_ATTACK_THRESHOLD = _AGGRO.get(AGGRESSION.upper(), (100, 2))

# AGILITY -> (steering gain, turn-speed %).
_AGILITY = {"SLUGGISH": (400, 85), "NIMBLE": (650, 100), "TWITCHY": (950, 115)}
STEER_GAIN, TURN_PCT = _AGILITY.get(AGILITY.upper(), (650, 100))

# EDGE_NERVE -> edge confirmations before escaping. Fewer = bails out earlier
# (safe but passive); more = holds its ground near the line (pushes harder but
# can drive itself out).
_NERVE = {"CAREFUL": 2, "NORMAL": 3, "DAREDEVIL": 5}
EDGE_CONFIRM_COUNT = _NERVE.get(EDGE_NERVE.upper(), 3)

# SIGNATURE -> favoured combat maneuver when breaking a stalemate
# (0 sidestep, 1 spin-charge, 2 asymmetric push).
_SIG = {"CHARGER": 1, "FLANKER": 0, "COUNTER": 2,
        "COUNTER-PUNCHER": 2, "COUNTERPUNCHER": 2}
SIGNATURE_STYLE = _SIG.get(SIGNATURE.upper(), 1)

# TEAM_COLOR -> idle identity LEDs.
_COLORS = {
    "RED": RGB_RED, "GREEN": RGB_GREEN, "BLUE": RGB_BLUE,
    "YELLOW": RGB_YELLOW, "PURPLE": RGB_PURPLE, "WHITE": RGB_WHITE,
}
TEAM_RGB = _COLORS.get(TEAM_COLOR.upper(), RGB_WHITE)


# ---------------------------------------------------------------------------
# State constants
# ---------------------------------------------------------------------------

STATE_READY = "READY"
STATE_SEARCH = "SEARCH"
STATE_TRACK = "TRACK"
STATE_ATTACK = "ATTACK"
STATE_ESCAPE = "ESCAPE"
STATE_COMBAT_MANEUVER = "COMBAT"
STATE_STOPPED = "STOPPED"


# ---------------------------------------------------------------------------
# Runtime state
# ---------------------------------------------------------------------------

running = False
state = STATE_READY

last_seen_dir = 1       # -1 = left, 1 = right
search_dir = 1
last_seen_ms = 0
last_display_ms = 0

# Search roaming phase state.
search_phase_start_ms = 0
search_advancing = False

escape_start_ms = 0
escape_turn_dir = 1

# Match intensity ramp state.
match_start_ms = 0
full_intensity_signaled = False
full_power = False        # latched True once an opponent is clearly sighted

# Stalemate detection state.
attack_start_ms = 0
stalemate_timeout_ms = 1500
last_encoder_check_ms = 0
last_encoder_left = 0
last_encoder_right = 0
stuck_count = 0
last_attack_move = 0       # Tread movement on the most recent sample (display)

# Combat maneuver state.
maneuver_start_ms = 0
maneuver_turn_dir = 1
maneuver_style = 0

current_line = [0, 0, 0, 0, 0]
current_prox = {
    "left": 0,
    "front_left": 0,
    "front_right": 0,
    "right": 0,
}


# ---------------------------------------------------------------------------
# Edge detection settings
# ---------------------------------------------------------------------------

# Per-sensor edge calibration, overwritten during calibration.
#   EDGE_THRESH = midpoint reading between the wood surface and the off-board
#                 drop-off for each sensor.
#   EDGE_DIR    = +1 if the off-board reading is higher than the wood reading
#                 for that sensor, otherwise -1. This lets the same code work
#                 regardless of how the bare wood happens to reflect IR.
EDGE_THRESH = [512, 512, 512, 512, 512]
EDGE_DIR = [1, 1, 1, 1, 1]

# Deadband past the midpoint before a sensor counts as "over the edge".
EDGE_MARGIN = const(60)

# Minimum useful difference between wood and off-board readings.
MIN_EDGE_DELTA = const(80)

# EDGE_CONFIRM_COUNT (consecutive detections before ESCAPE) is set from
# EDGE_NERVE in the team-config section above.

# Edge calibration is saved here so we only calibrate once per table.
CALIB_FILE = "edge_calib.txt"

edge_counter_left = 0
edge_counter_center = 0
edge_counter_right = 0


# ---------------------------------------------------------------------------
# Time and math helpers
# ---------------------------------------------------------------------------

def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


def now_ms():
    return time.ticks_ms()


def ms_since(t):
    return time.ticks_diff(now_ms(), t)


def intensity_pct():
    """Return current match intensity as a percentage (RAMP_START_PCT..100).

    Normally speed ramps up over the first part of the match, but the moment an
    opponent is clearly sighted (full_power) we jump straight to 100%.
    """
    global full_intensity_signaled
    if full_power:
        if not full_intensity_signaled:
            full_intensity_signaled = True
            play_tone("t220 l32 o5 c e g > c e")
        return 100
    if match_start_ms == 0:
        return 100
    elapsed = ms_since(match_start_ms)
    if elapsed >= RAMP_DURATION_MS:
        if not full_intensity_signaled:
            full_intensity_signaled = True
            play_tone("t220 l32 o5 c e g > c e")
        return 100
    return RAMP_START_PCT + (100 - RAMP_START_PCT) * elapsed // RAMP_DURATION_MS


def get_difficulty():
    # Apply the team's aggression/agility multipliers to the base speed tier.
    name, search_speed, track_speed, attack_speed = DIFFICULTIES[difficulty_index]
    search_speed = search_speed * TURN_PCT // 100
    track_speed = track_speed * TURN_PCT // 100
    attack_speed = attack_speed * AGGRO_PCT // 100
    # Apply match intensity ramp.
    pct = intensity_pct()
    search_speed = search_speed * pct // 100
    track_speed = track_speed * pct // 100
    attack_speed = attack_speed * pct // 100
    return (name, search_speed, track_speed, attack_speed)


# ---------------------------------------------------------------------------
# Motor helpers
# ---------------------------------------------------------------------------

def stop_motors():
    motors.set_speeds(0, 0)


def drive(left, right):
    left = clamp(left, -MAX_MOTOR_SPEED, MAX_MOTOR_SPEED)
    right = clamp(right, -MAX_MOTOR_SPEED, MAX_MOTOR_SPEED)

    motors.set_speeds(
        MOTOR_DIRECTION * left,
        MOTOR_DIRECTION * right
    )


# ---------------------------------------------------------------------------
# LED and sound helpers
# ---------------------------------------------------------------------------

def set_all_leds(color):
    for i in range(6):
        rgb_leds.set(i, color)
    rgb_leds.show()


def set_front_leds(left, center, right):
    rgb_leds.set(5, left)
    rgb_leds.set(4, center)
    rgb_leds.set(3, right)
    rgb_leds.show()


def play_tone(sequence):
    if buzzer is None:
        return

    try:
        buzzer.play_in_background(sequence)
    except Exception:
        pass


def chirp_start():
    play_tone("t180 l16 o5 c e g")


def chirp_target():
    play_tone("t220 l32 o6 c")


def chirp_edge():
    play_tone("t140 l16 o4 c r c")


def chirp_stop():
    play_tone("t140 l16 o4 g e c")


def chirp_attack():
    play_tone("t200 l32 o3 c d e f g")


def chirp_stalemate():
    play_tone("t160 l16 o3 c r c r c")


def chirp_maneuver():
    play_tone("t240 l32 o4 c e g > c")


def chirp_victory():
    play_tone("t180 l16 o5 c e g > c2")


# ---------------------------------------------------------------------------
# LED animation engine
# ---------------------------------------------------------------------------

def update_leds():
    t = now_ms()

    if not running:
        # Breathing glow in team color.
        period = 2000
        phase = t % period
        if phase > period // 2:
            phase = period - phase
        b = phase * 255 // (period // 2)
        tr, tg, tb = TEAM_RGB
        color = (tr * b // 255, tg * b // 255, tb * b // 255)
        for i in range(6):
            rgb_leds.set(i, color)
        rgb_leds.show()
        return

    if state in (STATE_SEARCH, STATE_TRACK, STATE_ESCAPE):
        # Normal operation -- quiet team-color LEDs, no animation.
        for i in range(6):
            rgb_leds.set(i, TEAM_RGB)
        rgb_leds.show()

    elif state == STATE_ATTACK:
        # Anger ramp: green -> orange -> red as stalemate builds.
        time_ratio = 0
        if attack_start_ms > 0 and stalemate_timeout_ms > 0:
            time_ratio = min(ms_since(attack_start_ms) * 120 // stalemate_timeout_ms, 120)
        stuck_anger = min(stuck_count * 40, 120)
        anger = max(time_ratio, stuck_anger)

        hue = 120 - anger  # 120=green, 60=yellow, 0=red
        pulse_period = max(150, 400 - anger * 2)
        phase = t % pulse_period
        if phase > pulse_period // 2:
            phase = pulse_period - phase
        brightness = 80 + phase * 175 // (pulse_period // 2)

        for i in (3, 4, 5):
            rgb_leds.set_hsv(i, [hue, 255, brightness])
        for i in (0, 1, 2):
            rgb_leds.set_hsv(i, [hue, 255, brightness // 4])
        rgb_leds.show()

    elif state == STATE_COMBAT_MANEUVER:
        # Rapid purple/white strobe.
        if (t // 60) % 2:
            for i in range(6):
                rgb_leds.set(i, RGB_PURPLE)
        else:
            for i in range(6):
                rgb_leds.set(i, RGB_WHITE)
        rgb_leds.show()



# ---------------------------------------------------------------------------
# Button helpers
# ---------------------------------------------------------------------------

def clear_button_events(duration_ms=700):
    start = time.ticks_ms()

    while time.ticks_diff(time.ticks_ms(), start) < duration_ms:
        button_a.check()
        button_b.check()
        button_c.check()
        time.sleep_ms(20)


def wait_for_button_c_press():
    while button_c.check() != True:
        time.sleep_ms(20)

    while button_c.check() != False:
        time.sleep_ms(20)


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def show_message(line1="", line2="", line3="", line4=""):
    display.fill(0)

    if line1:
        display.text(line1, 0, 0)
    if line2:
        display.text(line2, 0, 16)
    if line3:
        display.text(line3, 0, 32)
    if line4:
        display.text(line4, 0, 48)

    display.show()


def show_line_values(title, values):
    display.fill(0)
    display.text(title, 0, 0)

    display.text("S0:{}".format(values[0]), 0, 14)
    display.text("S1:{}".format(values[1]), 64, 14)

    display.text("S2:{}".format(values[2]), 0, 28)
    display.text("S3:{}".format(values[3]), 64, 28)

    display.text("S4:{}".format(values[4]), 0, 48)

    display.show()


def show_threshold_values(thresholds):
    display.fill(0)
    display.text("THRESHOLDS", 0, 0)

    display.text("T0:{}".format(thresholds[0]), 0, 14)
    display.text("T1:{}".format(thresholds[1]), 64, 14)

    display.text("T2:{}".format(thresholds[2]), 0, 28)
    display.text("T3:{}".format(thresholds[3]), 64, 28)

    display.text("T4:{}".format(thresholds[4]), 0, 48)

    display.show()


def update_display(force=False):
    global last_display_ms

    t = now_ms()
    if not force and time.ticks_diff(t, last_display_ms) < DISPLAY_UPDATE_MS:
        return

    last_display_ms = t

    name, search_speed, track_speed, attack_speed = get_difficulty()

    display.fill(0)
    display.text(TEAM_NAME[:10], 0, 0)
    display.text(BOT_ID, 72, 0)
    display.text(name[:4], 96, 0)

    if running:
        pct = intensity_pct()
        if pct < 100:
            display.text("{} {}%".format(state, pct), 0, 14)
        else:
            display.text(state, 0, 14)
        display.text("A stop", 76, 14)

        p = current_prox
        prox_text = "{} {} {} {} *{}".format(
            p["left"],
            p["front_left"],
            p["front_right"],
            p["right"],
            p["pl"] + p["pf"] + p["pr"]
        )
        display.text("P:" + prox_text, 0, 30)

        if state == STATE_ATTACK:
            if stuck_count >= STALL_TRIGGER_COUNT:
                mood = "STUCK!!"
            elif stuck_count >= 1:
                mood = "PUSHING! S:{}".format(stuck_count)
            else:
                mood = "CHARGE!"
            display.text(mood, 0, 46)
        elif state == STATE_COMBAT_MANEUVER:
            moves = ("SIDESTEP!", "HAH!", "TAKE THIS!")
            display.text(moves[maneuver_style % 3], 0, 46)
        else:
            line_text = "{} {} {} {} {}".format(
                current_line[0],
                current_line[1],
                current_line[2],
                current_line[3],
                current_line[4]
            )
            display.text("L:" + line_text[:15], 0, 46)
    else:
        display.text("A start", 0, 16)
        display.text("B difficulty", 0, 32)
        display.text("C recalib", 0, 48)

    display.show()


# ---------------------------------------------------------------------------
# Sensor sampling
# ---------------------------------------------------------------------------

def average_line_samples(samples=60, delay_ms=15):
    total = [0, 0, 0, 0, 0]

    for _ in range(samples):
        readings = line_sensors.read()

        for i in range(5):
            total[i] += readings[i]

        time.sleep_ms(delay_ms)

    return [total[i] // samples for i in range(5)]


def read_line():
    global current_line

    current_line = line_sensors.read()[:]
    return current_line


def read_passive_opponent():
    """With our own IR emitters OFF, count how often each proximity sensor sees
    external 56 kHz IR -- i.e. the OTHER robot's proximity emitters. That signal
    carries far beyond reflection range, so two bots facing each other across the
    ring detect one another even when a reflection would be far too weak.
    Returns (left, front, right) low-counts out of PASSIVE_SAMPLES.
    """
    ps = proximity_sensors
    ps.ir_pulses.off()
    ps._prepare_to_read()
    l = 0
    f = 0
    r = 0
    for _ in range(PASSIVE_SAMPLES):
        if not ps.left_sensor.value():
            l += 1
        if not ps.front_sensor.value():
            f += 1
        if not ps.right_sensor.value():
            r += 1
        time.sleep_us(120)
    return l, f, r


def read_proximity():
    global current_prox

    proximity_sensors.read()

    left = proximity_sensors.left_counts_with_left_leds()
    front_left = proximity_sensors.front_counts_with_left_leds()
    front_right = proximity_sensors.front_counts_with_right_leds()
    right = proximity_sensors.right_counts_with_right_leds()

    if PASSIVE_DETECT:
        pl, pf, pr = read_passive_opponent()
    else:
        pl = pf = pr = 0

    current_prox = {
        "left": left,
        "front_left": front_left,
        "front_right": front_right,
        "right": right,
        "pl": pl,
        "pf": pf,
        "pr": pr,
    }

    return current_prox


# ---------------------------------------------------------------------------
# Edge calibration
# ---------------------------------------------------------------------------

def save_calibration():
    # Persist the edge calibration (5 thresholds + 5 directions) so the next
    # power-up can skip calibration.
    try:
        with open(CALIB_FILE, "w") as f:
            f.write(",".join(str(v) for v in EDGE_THRESH))
            f.write(";")
            f.write(",".join(str(v) for v in EDGE_DIR))
    except Exception:
        pass


def load_calibration():
    # Load saved edge calibration. Returns True if a valid set was loaded.
    global EDGE_THRESH
    global EDGE_DIR
    try:
        with open(CALIB_FILE, "r") as f:
            raw = f.read().strip()
        parts = raw.split(";")
        thresh = [int(p) for p in parts[0].split(",")]
        dirs = [int(p) for p in parts[1].split(",")]
        if len(thresh) != 5 or len(dirs) != 5:
            return False
        EDGE_THRESH = thresh
        EDGE_DIR = dirs
        return True
    except Exception:
        return False


def calibrate_edge_threshold():
    """
    Two-step calibration for a bare-wood arena whose boundary is the board edge.

    Step 1: Sample the bare wood surface (robot sitting flat).
    Step 2: Sample with the front sensors out over the board edge (the drop-off).

    Per sensor, the trigger point is the midpoint of the two readings and the
    "off-board" direction is learned from their sign, so polarity never matters.
    """

    global EDGE_THRESH
    global EDGE_DIR
    global edge_counter_left
    global edge_counter_center
    global edge_counter_right

    stop_motors()
    set_all_leds(RGB_BLUE)

    clear_button_events(500)

    # Step 1: Bare wood surface sample (robot flat on the board).

    show_message(
        "WOOD SAMPLE",
        "Place robot on",
        "BARE WOOD flat",
        "Press C"
    )

    wait_for_button_c_press()

    show_message(
        "Sampling WOOD",
        "Do not move",
        "robot...",
        ""
    )

    surf_values = average_line_samples(samples=60, delay_ms=15)

    show_line_values("WOOD", surf_values)
    time.sleep_ms(1200)

    clear_button_events(400)

    # Step 2: Off-board sample (front sensors out over the board edge).

    show_message(
        "EDGE SAMPLE",
        "Hold FRONT over",
        "the BOARD EDGE",
        "Press C"
    )

    wait_for_button_c_press()

    show_message(
        "Sampling EDGE",
        "Hold steady",
        "over the drop...",
        ""
    )

    off_values = average_line_samples(samples=60, delay_ms=15)

    show_line_values("EDGE", off_values)
    time.sleep_ms(1200)

    # Step 3: Per-sensor midpoint threshold + learned off-board direction.

    thresh = []
    dirs = []
    weak_contrast = False

    for i in range(5):
        delta = off_values[i] - surf_values[i]

        if abs(delta) < MIN_EDGE_DELTA:
            weak_contrast = True

        thresh.append((surf_values[i] + off_values[i]) // 2)
        dirs.append(1 if delta >= 0 else -1)

    EDGE_THRESH = thresh
    EDGE_DIR = dirs

    edge_counter_left = 0
    edge_counter_center = 0
    edge_counter_right = 0

    save_calibration()

    show_threshold_values(EDGE_THRESH)
    time.sleep_ms(1600)

    # Step 4: Show calibration result.

    if weak_contrast:
        set_all_leds(RGB_RED)

        show_message(
            "LOW CONTRAST",
            "Wood/edge too",
            "similar - check",
            "placement"
        )

        time.sleep_ms(2500)

    else:
        set_all_leds(RGB_GREEN)

        show_message(
            "CAL OK",
            "Edge thresholds",
            "set",
            "Ready"
        )

        time.sleep_ms(1500)

    set_all_leds(RGB_OFF)
    clear_button_events(500)


# ---------------------------------------------------------------------------
# Edge detection
# ---------------------------------------------------------------------------

def edge_status(line):
    """
    Board-edge detection for a bare-wood arena.

    Each sensor is compared against its calibrated midpoint. A sensor counts as
    "over the edge" when its reading has moved past the midpoint, by at least
    EDGE_MARGIN, in the learned off-board direction (EDGE_DIR). This works no
    matter whether the drop-off reads higher or lower than the wood.

    Sensors are grouped into zones:
        left   = sensors 0, 1
        center = sensor 2
        right  = sensors 3, 4

    A zone triggers if any sensor in it is over the edge.
    EDGE_CONFIRM_COUNT consecutive triggers confirms an edge.
    """

    global edge_counter_left
    global edge_counter_center
    global edge_counter_right

    # Signed distance past the midpoint in the off-board direction, per sensor.
    d0 = (line[0] - EDGE_THRESH[0]) * EDGE_DIR[0]
    d1 = (line[1] - EDGE_THRESH[1]) * EDGE_DIR[1]
    d2 = (line[2] - EDGE_THRESH[2]) * EDGE_DIR[2]
    d3 = (line[3] - EDGE_THRESH[3]) * EDGE_DIR[3]
    d4 = (line[4] - EDGE_THRESH[4]) * EDGE_DIR[4]

    raw_left = d0 > EDGE_MARGIN or d1 > EDGE_MARGIN
    raw_center = d2 > EDGE_MARGIN
    raw_right = d3 > EDGE_MARGIN or d4 > EDGE_MARGIN

    if raw_left:
        edge_counter_left += 1
    else:
        edge_counter_left = 0

    if raw_center:
        edge_counter_center += 1
    else:
        edge_counter_center = 0

    if raw_right:
        edge_counter_right += 1
    else:
        edge_counter_right = 0

    left_edge = edge_counter_left >= EDGE_CONFIRM_COUNT
    center_edge = edge_counter_center >= EDGE_CONFIRM_COUNT
    right_edge = edge_counter_right >= EDGE_CONFIRM_COUNT

    any_edge = left_edge or center_edge or right_edge

    return any_edge, left_edge, center_edge, right_edge


def reset_edge_counters():
    global edge_counter_left
    global edge_counter_center
    global edge_counter_right

    edge_counter_left = 0
    edge_counter_center = 0
    edge_counter_right = 0


# ---------------------------------------------------------------------------
# Edge debug screen
# ---------------------------------------------------------------------------

def debug_edge_detection_screen():
    """
    Diagnostic screen showing live line readings and edge detection status.

    Shows L / C / R for detected edge zones, or SAFE if none.
    Press A to exit.
    """

    stop_motors()
    clear_button_events(500)
    reset_edge_counters()

    while True:
        line = line_sensors.read()
        any_edge, left_edge, center_edge, right_edge = edge_status(line)

        display.fill(0)
        display.text("EDGE DEBUG", 0, 0)

        display.text("{} {} {}".format(
            line[0], line[1], line[2]
        ), 0, 14)

        display.text("{} {}".format(
            line[3], line[4]
        ), 0, 28)

        status = ""

        if left_edge:
            status += "L"

        if center_edge:
            status += "C"

        if right_edge:
            status += "R"

        if not status:
            status = "SAFE"

        display.text(status, 0, 46)
        display.show()

        if button_a.check() == True:
            while button_a.check() != False:
                time.sleep_ms(20)
            break

        time.sleep_ms(50)

    clear_button_events(500)


# ---------------------------------------------------------------------------
# Proximity interpretation
# ---------------------------------------------------------------------------

def passive_total(p):
    return p["pl"] + p["pf"] + p["pr"]


def passive_scaled(v):
    # Map a passive low-count (0..PASSIVE_SAMPLES) onto the active 0..9 scale so
    # it can be compared with reflection counts for bearing / steering.
    return v * 9 // PASSIVE_SAMPLES


def prox_object_seen(p):
    if (p["left"] >= SENSOR_THRESHOLD or
            p["front_left"] >= SENSOR_THRESHOLD or
            p["front_right"] >= SENSOR_THRESHOLD or
            p["right"] >= SENSOR_THRESHOLD):
        return True
    # Passive: we hear the opponent's own emitters even with no usable reflection.
    return passive_total(p) >= PASSIVE_SEEN


def prox_clear_sighting(p):
    # Close reflection on any sensor, or a strong passive read of the opponent's
    # emitters across the ring -- either latches the match to full power.
    if max(p["left"], p["front_left"], p["front_right"], p["right"]) >= CLEAR_SIGHT_COUNT:
        return True
    return passive_total(p) >= PASSIVE_CLEAR


def prox_front_strength(p):
    # Active (reflection) front strength only -- used to commit to a contact push.
    return p["front_left"] + p["front_right"]


def prox_left_score(p):
    return max(p["left"], p["front_left"], passive_scaled(p["pl"]))


def prox_right_score(p):
    return max(p["right"], p["front_right"], passive_scaled(p["pr"]))


def prox_is_centered(p):
    left_score = prox_left_score(p)
    right_score = prox_right_score(p)
    return abs(left_score - right_score) <= CENTER_BALANCE_MARGIN


def prox_direction(p):
    left_score = prox_left_score(p)
    right_score = prox_right_score(p)

    if left_score > right_score:
        return -1
    elif right_score > left_score:
        return 1
    else:
        return last_seen_dir


# ---------------------------------------------------------------------------
# Match startup
# ---------------------------------------------------------------------------

def countdown():
    stop_motors()

    for n in (3, 2, 1):
        display.fill(0)
        display.text("Match starts", 0, 8)
        display.text(str(n), 56, 32)
        display.show()

        set_all_leds(RGB_YELLOW)
        play_tone("t180 l16 o5 c")

        time.sleep_ms(500)

    display.fill(0)
    display.text("GO!", 48, 28)
    display.show()

    set_all_leds(RGB_GREEN)
    chirp_start()

    time.sleep_ms(350)
    set_all_leds(RGB_OFF)


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------

def start_escape(left_edge, center_edge, right_edge):
    global state
    global escape_start_ms
    global escape_turn_dir
    global attack_start_ms
    global stuck_count
    global search_phase_start_ms
    global search_advancing

    state = STATE_ESCAPE
    escape_start_ms = now_ms()
    attack_start_ms = 0
    stuck_count = 0

    # After clearing the edge, resume searching with an in-place scan first
    # (rather than immediately rolling forward back toward the boundary).
    search_advancing = False
    search_phase_start_ms = now_ms()

    if left_edge and not right_edge:
        escape_turn_dir = 1
    elif right_edge and not left_edge:
        escape_turn_dir = -1
    else:
        escape_turn_dir = -last_seen_dir



def handle_search(p):
    global state
    global last_seen_ms
    global last_seen_dir
    global search_dir
    global search_phase_start_ms
    global search_advancing

    name, search_speed, track_speed, attack_speed = get_difficulty()

    if prox_object_seen(p):
        last_seen_ms = now_ms()
        last_seen_dir = prox_direction(p)
        state = STATE_TRACK
        chirp_target()
        return

    # Roam instead of camping: scan in place (a deliberate, slower spin so the
    # narrow IR cone reliably catches a target), then roll forward into open
    # space, then scan again (reversing scan direction each cycle). The main-loop
    # edge check still preempts the forward roll and turns us back inward.
    spin_speed = search_speed * SEARCH_SPIN_PCT // 100

    if search_advancing:
        if ms_since(search_phase_start_ms) >= SEARCH_ADVANCE_MS:
            search_advancing = False
            search_phase_start_ms = now_ms()
            search_dir = -search_dir
            drive(spin_speed * search_dir, -spin_speed * search_dir)
        else:
            drive(search_speed, search_speed)
    else:
        if ms_since(search_phase_start_ms) >= SEARCH_SCAN_MS:
            search_advancing = True
            search_phase_start_ms = now_ms()
            drive(search_speed, search_speed)
        else:
            drive(spin_speed * search_dir, -spin_speed * search_dir)


def handle_track(p):
    global state
    global last_seen_ms
    global last_seen_dir

    name, search_speed, track_speed, attack_speed = get_difficulty()

    if not prox_object_seen(p):
        if ms_since(last_seen_ms) > LOST_OPPONENT_MS:
            state = STATE_SEARCH
        else:
            drive(track_speed * last_seen_dir, -track_speed * last_seen_dir)
        return

    last_seen_ms = now_ms()
    direction = prox_direction(p)
    last_seen_dir = direction

    front = prox_front_strength(p)

    # Commit to the charge as soon as the opponent is solidly in front -- ATTACK
    # steers as it drives, so it no longer needs to be perfectly centered first.
    if front >= FRONT_ATTACK_THRESHOLD:
        state = STATE_ATTACK
        return

    # Close the distance: if the opponent is in front of us, charge forward while
    # steering to keep it centered; if it is off to a side, pivot toward it to
    # bring it into the front sensor. This makes the robots actually drive into
    # each other instead of just rotating in place near one another.
    left_score = prox_left_score(p)
    right_score = prox_right_score(p)
    error = right_score - left_score

    # "Facing" the opponent if a reflection lands on the front sensor OR we hear
    # its emitters dead ahead -- in either case drive forward and steer; only
    # pivot when the opponent is purely off to one side.
    if front >= 1 or p["pf"] >= PASSIVE_SEEN:
        steer = error * (STEER_GAIN // 2)
        drive(track_speed + steer, track_speed - steer)
    else:
        drive(track_speed * direction, -track_speed * direction)


def handle_attack(p):
    global state
    global last_seen_ms
    global last_seen_dir
    global attack_start_ms
    global last_encoder_check_ms
    global last_encoder_left
    global last_encoder_right
    global stuck_count
    global last_attack_move

    name, search_speed, track_speed, attack_speed = get_difficulty()

    # Detect entry to ATTACK state (attack_start_ms reset to 0 on exit).
    if attack_start_ms == 0:
        attack_start_ms = now_ms()
        last_encoder_check_ms = now_ms()
        left_enc, right_enc = encoders.get_counts()
        last_encoder_left = left_enc
        last_encoder_right = right_enc
        stuck_count = 0
        chirp_attack()

    # Opponent tracking.
    if prox_object_seen(p):
        last_seen_ms = now_ms()
        last_seen_dir = prox_direction(p)
    elif ms_since(last_seen_ms) > LOST_OPPONENT_MS:
        # If we were in a real fight, celebrate.
        if ms_since(attack_start_ms) > 800:
            chirp_victory()
        attack_start_ms = 0
        state = STATE_SEARCH
        return

    # Sample the treads every STALEMATE_CHECK_MS. This is a diagnostic plus a
    # fast path: if the treads have actually stalled (not turning) we can break
    # off early. On a slippery surface the treads keep spinning even while the
    # robot is pinned, so this alone is NOT reliable -- the time backstop below
    # is what guarantees we break a slip-stalemate.
    if ms_since(last_encoder_check_ms) >= STALEMATE_CHECK_MS:
        left_enc, right_enc = encoders.get_counts()

        left_delta = abs(left_enc - last_encoder_left)
        right_delta = abs(right_enc - last_encoder_right)
        last_attack_move = left_delta + right_delta

        last_encoder_left = left_enc
        last_encoder_right = right_enc
        last_encoder_check_ms = now_ms()

        if last_attack_move < STALEMATE_ENCODER_THRESHOLD:
            stuck_count += 1
            if stuck_count == 1:
                chirp_stalemate()
        else:
            stuck_count = 0

    # Stay committed: while the opponent is still in front of us we keep pushing
    # and never break off on our own. (stuck_count above still drives the
    # "anger" LEDs and the display, but it no longer makes us disengage.) The
    # only ways out of ATTACK now are losing the opponent or reaching the board
    # edge -- not a self-inflicted maneuver.

    # Normal attack driving with steering correction.
    left_score = prox_left_score(p)
    right_score = prox_right_score(p)

    error = right_score - left_score

    left_speed = attack_speed + error * STEER_GAIN
    right_speed = attack_speed - error * STEER_GAIN

    drive(left_speed, right_speed)


def handle_escape():
    global state

    elapsed = ms_since(escape_start_ms)

    if elapsed < BACKUP_MS:
        drive(-ESCAPE_BACKUP_SPEED, -ESCAPE_BACKUP_SPEED)
        return

    if elapsed < BACKUP_MS + TURN_AWAY_MS:
        drive(ESCAPE_TURN_SPEED * escape_turn_dir,
              -ESCAPE_TURN_SPEED * escape_turn_dir)
        return

    if elapsed < BACKUP_MS + TURN_AWAY_MS + ESCAPE_FORWARD_MS:
        drive(ESCAPE_FORWARD_SPEED, ESCAPE_FORWARD_SPEED)
        return

    reset_edge_counters()
    state = STATE_SEARCH


def start_combat_maneuver():
    global state
    global maneuver_start_ms
    global maneuver_turn_dir
    global maneuver_style
    global attack_start_ms
    global stuck_count
    global stalemate_timeout_ms

    state = STATE_COMBAT_MANEUVER
    maneuver_start_ms = now_ms()
    attack_start_ms = 0
    stuck_count = 0

    # Randomize direction; bias style toward the team's signature move so each
    # bot fights with a recognizable personality (still random ~1 time in 4).
    maneuver_turn_dir = 1 if random.getrandbits(1) else -1
    if SIGNATURE_STYLE is not None and random.getrandbits(2):
        maneuver_style = SIGNATURE_STYLE
    else:
        maneuver_style = random.randint(0, 2)

    # Re-randomize timeout for the next stalemate detection.
    stalemate_timeout_ms = random.randint(STALEMATE_MIN_MS, STALEMATE_MAX_MS)

    chirp_maneuver()


def handle_combat_maneuver():
    global state

    name, search_speed, track_speed, attack_speed = get_difficulty()
    elapsed = ms_since(maneuver_start_ms)

    backup_speed = attack_speed * 80 // 100
    turn_speed = attack_speed * 90 // 100
    burst_speed = attack_speed * 110 // 100

    if maneuver_style == 0:
        # Style 0: Sidestep -- backup, turn, angled burst forward.
        if elapsed < MANEUVER_BACKUP_MS:
            drive(-backup_speed, -backup_speed)
            return
        elif elapsed < MANEUVER_BACKUP_MS + MANEUVER_TURN_MS:
            drive(turn_speed * maneuver_turn_dir,
                  -turn_speed * maneuver_turn_dir)
            return
        elif elapsed < MANEUVER_BACKUP_MS + MANEUVER_TURN_MS + MANEUVER_BURST_MS:
            if maneuver_turn_dir > 0:
                drive(burst_speed, burst_speed * 60 // 100)
            else:
                drive(burst_speed * 60 // 100, burst_speed)
            return

    elif maneuver_style == 1:
        # Style 1: Spin-away -- longer turn, then straight charge.
        spin_ms = MANEUVER_TURN_MS + 100
        if elapsed < spin_ms:
            drive(turn_speed * maneuver_turn_dir,
                  -turn_speed * maneuver_turn_dir)
            return
        elif elapsed < spin_ms + MANEUVER_BURST_MS:
            drive(burst_speed, burst_speed)
            return

    elif maneuver_style == 2:
        # Style 2: Asymmetric push -- one wheel fast, other slow.
        asym_ms = MANEUVER_BURST_MS + 100
        if elapsed < asym_ms:
            if maneuver_turn_dir > 0:
                drive(burst_speed, attack_speed * 30 // 100)
            else:
                drive(attack_speed * 30 // 100, burst_speed)
            return

    # Maneuver complete -- re-acquire opponent.
    reset_edge_counters()
    state = STATE_SEARCH


# ---------------------------------------------------------------------------
# Button actions
# ---------------------------------------------------------------------------

def toggle_running():
    global running
    global state
    global search_dir
    global last_seen_ms
    global attack_start_ms
    global stuck_count
    global stalemate_timeout_ms
    global match_start_ms
    global full_intensity_signaled
    global full_power
    global search_phase_start_ms
    global search_advancing

    if running:
        running = False
        state = STATE_STOPPED
        attack_start_ms = 0
        stuck_count = 0

        stop_motors()
        chirp_stop()

        update_display(True)
        clear_button_events(300)
        return

    reset_edge_counters()

    search_advancing = False
    search_phase_start_ms = now_ms()

    # Seed RNG from hardware timer for symmetry breaking between robots.
    random.seed(time.ticks_us())
    stalemate_timeout_ms = random.randint(STALEMATE_MIN_MS, STALEMATE_MAX_MS)

    countdown()

    running = True
    state = STATE_SEARCH
    attack_start_ms = 0
    stuck_count = 0
    match_start_ms = now_ms()
    full_intensity_signaled = False
    full_power = False

    search_dir = -search_dir
    last_seen_ms = now_ms()

    update_display(True)
    clear_button_events(300)


def cycle_difficulty():
    global difficulty_index

    if running:
        return

    difficulty_index = (difficulty_index + 1) % len(DIFFICULTIES)

    name, search_speed, track_speed, attack_speed = get_difficulty()

    display.fill(0)
    display.text("Difficulty", 0, 0)
    display.text(name, 0, 20)
    display.text("A start", 0, 48)
    display.show()

    play_tone("t200 l16 o5 c")

    time.sleep_ms(600)
    clear_button_events(300)


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main():
    global state
    global running
    global full_power

    running = False
    state = STATE_READY

    stop_motors()
    set_all_leds(RGB_OFF)

    clear_button_events(700)

    # Version splash with the team name and bot identity.
    show_message(
        "OUPI SUMO v2",
        TEAM_NAME,
        "HOUSE BOT" if HOUSE_BOT else "challenger",
        "Bot {}".format(BOT_ID)
    )

    time.sleep_ms(2000)

    # Calibrate once per table: reuse saved thresholds if we have them, so match
    # turnaround stays fast. Press C any time (when stopped) to recalibrate.
    if load_calibration():
        set_all_leds(RGB_GREEN)
        show_message("CALIB LOADED", "from last time", "C = recalibrate", "")
        time.sleep_ms(1500)
    else:
        calibrate_edge_threshold()

    clear_button_events(700)

    while True:
        # Read sensors every loop.
        p = read_proximity()
        line = read_line()

        any_edge, left_edge, center_edge, right_edge = edge_status(line)

        # Button A: start / stop.
        if button_a.check() == True:
            while button_a.check() != False:
                time.sleep_ms(20)

            toggle_running()

        # Button B: difficulty, only when stopped.
        if button_b.check() == True:
            while button_b.check() != False:
                time.sleep_ms(20)

            if not running:
                cycle_difficulty()

        # Button C: recalibrate, only when stopped.
        if button_c.check() == True:
            while button_c.check() != False:
                time.sleep_ms(20)

            if not running:
                calibrate_edge_threshold()
                clear_button_events(500)

        if not running:
            stop_motors()
            update_leds()
            update_display()
            time.sleep_ms(20)
            continue

        # The moment we clearly see an opponent, commit to full power.
        if not full_power and prox_clear_sighting(p):
            full_power = True

        # Edge detection (board boundary) has priority over the combat states.
        if state != STATE_ESCAPE and any_edge:
            start_escape(left_edge, center_edge, right_edge)

        if state == STATE_SEARCH:
            handle_search(p)

        elif state == STATE_TRACK:
            handle_track(p)

        elif state == STATE_ATTACK:
            handle_attack(p)

        elif state == STATE_ESCAPE:
            handle_escape()

        elif state == STATE_COMBAT_MANEUVER:
            handle_combat_maneuver()

        else:
            state = STATE_SEARCH

        update_leds()
        update_display()
        time.sleep_ms(10)


# ---------------------------------------------------------------------------
# Safe program wrapper
# ---------------------------------------------------------------------------

try:
    main()

except Exception as e:
    stop_motors()
    set_all_leds(RGB_RED)

    display.fill(0)
    display.text("PROGRAM ERROR", 0, 0)
    display.text(type(e).__name__[:16], 0, 18)
    display.text(str(e)[:16], 0, 36)
    display.show()

    raise

finally:
    stop_motors()
