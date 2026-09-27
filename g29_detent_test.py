"""
G29 Raststufen-Simulator (Windows, PySDL2) – Version 3: Feder im Gerät
-----------------------------------------------------------------------
Das Lenkrad rechnet den Federeffekt selbst (SDL_HAPTIC_SPRING). Python setzt nur
die Federmitte auf die aktuelle Raststufe und verschiebt sie beim Stufenwechsel.
Kein USB-Regelkreis mehr → kein Zittern.

Installation:
    pip install pysdl2 pysdl2-dll

Voraussetzungen:
    - Logitech G HUB installiert, Lenkbereich z.B. 540°, FFB 100 %

Abbruch mit Strg+C.
"""

import sys
import time
import ctypes
import sdl2

# --------- Einstellungen ---------
# Lok-Profile: Stufenzahl, schwere Übergänge, Zwischenstufen (Feldschwächung).
# "heavy": Schlüssel = untere Position, gilt für k <-> k+1 in beide Richtungen; Wert = Kraftfaktor
# "shunt": Anzahl Zwischenstufen (LED-Anzeige: 1..5 = Füllstand, 6+ = alle LEDs pulsieren)
LOCOS = {
    "EP09": {
        "steps": 32,                       # Positionen 0 .. 31
        "heavy": {0: 2.2, 1: 2.2, 18: 2.2, 19: 2.2, 30: 2.2},
        "shunt": 5,
    },
    "ET22": {
        "steps": 49,                       # Positionen 0 .. 48
        "heavy": {0: 2.2, 1: 2.2, 20: 2.2, 21: 2.2, 35: 2.2, 36: 2.2, 47: 2.2},
        "shunt": 6,
    },
    "EP08-07": {
        "steps": 44,                       # Positionen 0 .. 43
        "heavy": {0: 2.2, 1: 2.2, 27: 2.2, 28: 2.2, 42: 2.2},
        "shunt": 5,                        # bitte prüfen
    },
    "ST44": {
        "steps": 16,                       # Positionen 0 .. 14 (Leerlauf + 14 Fahrstufen)
        "heavy": {0: 2.2},                 # nur 0 <-> 1
        "shunt": 0,                        # keine Zwischenstufen
    },
    "SU45": {
        "steps": 15,                       # Positionen 0 .. 14 (Leerlauf + 14 Fahrstufen)
        "heavy": {0: 2.2},                 # nur 0 <-> 1
        "shunt": 0,                        # keine Zwischenstufen
    },    
}
DEFAULT_LOCO = "EP09"
MENU_KEY = "m"        # Taste im Konsolenfenster, die das Lok-Menü öffnet

# werden aus dem aktiven Profil gesetzt (nicht direkt ändern)
STEPS = LOCOS[DEFAULT_LOCO]["steps"]
HEAVY = LOCOS[DEFAULT_LOCO]["heavy"]
SHUNT_MAX = LOCOS[DEFAULT_LOCO]["shunt"]

STIFFNESS = 23000     # Federhärte normal (0..32767). Bewusst Luft lassen für HEAVY-Faktor!
WALL = 15000           # Kraft-Obergrenze der Feder normal (0..32767)
DEADBAND = 0.04       # Anteil einer Stufe, in dem die Feder ganz locker ist (0 = immer zentrieren)
HYSTERESIS = 0.12     # Stufe wechselt erst bei 0.5 + HYSTERESIS Stufen Abstand von der Mitte

WALL_ABS_MAX = 24000  # Obergrenze für schwere Übergänge

INVERT = False        # True, falls das Rad von der Stufe WEG gedrückt wird
RATE_HZ = 200         # Abfragerate der Position (nur für Stufenwechsel relevant)

SEND_KEYS = True      # Tastendruck ans Spiel schicken (False = nur Konsolenausgabe)
KEY_HOLD = 0.03       # Sekunden, die die Taste gedrückt bleibt

# Scancodes Ziffernblock
SC_NUM_PLUS = 0x4E    # Num+
SC_NUM_MINUS = 0x4A   # Num-
SC_NUM_DIV = 0x35     # Num/  (erweiterte Taste, E0-Präfix)
SC_NUM_MUL = 0x37     # Num*
SC_NUM_0 = 0x52
SC_NUM_1 = 0x4F
SC_NUM_2 = 0x50
SC_NUM_3 = 0x51
SC_NUM_4 = 0x4B
SC_NUM_5 = 0x4C
SC_NUM_6 = 0x4D
SC_NUM_7 = 0x47
SC_NUM_8 = 0x48
SC_NUM_9 = 0x49
SC_NUM_DOT = 0x53     # Num .
SC_SPACE = 0x39       # Leertaste
SC_T = 0x14           # Taste T

KEY_NAMES = {
    SC_NUM_PLUS: "Num+", SC_NUM_MINUS: "Num-", SC_NUM_DIV: "Num/", SC_NUM_MUL: "Num*",
    SC_NUM_0: "Num0", SC_NUM_1: "Num1", SC_NUM_2: "Num2", SC_NUM_3: "Num3", SC_NUM_4: "Num4",
    SC_NUM_5: "Num5", SC_NUM_6: "Num6", SC_NUM_7: "Num7", SC_NUM_8: "Num8", SC_NUM_9: "Num9",
    SC_NUM_DOT: "Num.", SC_SPACE: "Leertaste", SC_T: "T",
}

# Knöpfe -> Tasten (SDL-Knopfindex: (Scancode, erweitert?))
BUTTON_KEYS = {
    4:  (SC_NUM_DIV, True),
    5:  (SC_NUM_MUL, False),
    10: (SC_NUM_DOT, False),
    11: (SC_T, False),
    19: (SC_NUM_1, False),
    20: (SC_NUM_7, False),
    21: (SC_NUM_3, False),
    22: (SC_NUM_9, False),
    23: (SC_NUM_4, False),
    24: (SC_SPACE, False),
}

LEDS = True           # LED-Leiste am G29 nutzen (braucht: pip install hidapi)
LED_BLINK = 0.8       # Sekunden pro Blinkphase, wenn Zwischenstufe > 5
LED_RED_MASK = 0x10   # welche LEDs bei Stufe > 5 blinken (Bit 0 = ganz links … Bit 4 = ganz rechts/rot; bei zwei roten: 0x18)
SHUNT_UP_BUTTON = 4   # Knopf, der eine Zwischenstufe hochschaltet (LED dazu)
SHUNT_DOWN_BUTTON = 5 # Knopf, der eine Zwischenstufe runterschaltet (LED weg)

GAME_EXE = "TrainDriver2.exe"   # Tasten nur senden, wenn dieses Programm im Vordergrund ist
TAP_GAP = 0.06        # Mindestabstand zwischen zwei Tastendrücken (Nachholen nach Fokusverlust)
RESYNC_BUTTON = 3     # G29-Knopf für manuellen Resync (SDL-Index; wird beim Drücken in der Konsole angezeigt)
RESYNC_GAP = 0.08     # Abstand der Tastendrücke beim Resync
RESYNC_FORCE = 9000   # Konstantkraft, mit der das Rad beim Resync auf Stufe 0 fährt (0..32767)
RESYNC_MIN_FORCE = 3000  # Mindestkraft kurz vor dem Ziel (gegen Haftreibung)
RESYNC_DIRECTION = 1  # Vorzeichen der Kraft, die das Rad Richtung Stufe 0 bewegt (Forcetest: +8000 -> links)
RESYNC_TIMEOUT = 5.0  # Sekunden, bis der Resync notfalls abgebrochen wird
AUTO_FOCUS = True     # TD2 automatisch in den Vordergrund holen, wenn Tasten anstehen
FOCUS_RETRY = 2.0     # Sekunden zwischen zwei Fokus-Versuchen
FOCUS_SETTLE = 0.3    # Wartezeit nach dem Fokuswechsel, bevor Tasten gesendet werden
# ---------------------------------


# --------- Tastatur-Emulation (Windows SendInput, Scancodes) ---------
INPUT_KEYBOARD = 1
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001
ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", ULONG_PTR)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("pad", ctypes.c_byte * 32)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("u", _INPUTUNION)]


_user32 = ctypes.WinDLL("user32", use_last_error=True) if sys.platform == "win32" else None


def _key_event(scancode, up=False, extended=False):
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.u.ki.wScan = scancode
    inp.u.ki.dwFlags = (KEYEVENTF_SCANCODE | (KEYEVENTF_KEYUP if up else 0)
                        | (KEYEVENTF_EXTENDEDKEY if extended else 0))
    _user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def tap(scancode, extended=False):
    if not SEND_KEYS or _user32 is None:
        return
    _key_event(scancode, up=False, extended=extended)
    time.sleep(KEY_HOLD)
    _key_event(scancode, up=True, extended=extended)


# --------- G29 LED-Leiste (roher HID-Report, wie im Linux-Treiber lg4ff) ---------
G29_VID = 0x046D
G29_PIDS = (0xC24F, 0xC260, 0xC262)   # G29 PS3-Modus, G29 PS4-Modus, G923


class G29Leds:
    def __init__(self):
        self.dev = None
        if not LEDS:
            return
        try:
            import hid
        except ImportError:
            print("LEDs: 'hidapi' fehlt (pip install hidapi) – LEDs aus.")
            return
        for info in hid.enumerate(G29_VID):
            if info["product_id"] in G29_PIDS:
                try:
                    d = hid.device()
                    d.open_path(info["path"])
                    self.dev = d
                    print(f"LEDs: G29 gefunden (PID {info['product_id']:04x})")
                    break
                except OSError:
                    continue
        if self.dev is None:
            print("LEDs: kein G29-HID-Interface offen bekommen – LEDs aus.")

    def set_mask(self, mask):
        if self.dev is None:
            return
        try:
            self.dev.write(bytes([0x00, 0xF8, 0x12, mask & 0x1F, 0x00, 0x00, 0x00, 0x00]))
        except OSError as e:
            print("LEDs: Schreiben fehlgeschlagen:", e)
            self.dev = None

    def show_level(self, level):
        """Zwischenstufe anzeigen: 0..5 = Füllstand, >5 = alle LEDs pulsieren."""
        self.level = level
        self._blink_on = True
        self._blink_t = time.time()
        self.set_mask((1 << max(0, min(5, level))) - 1)

    def tick(self):
        """Regelmäßig aufrufen – übernimmt das Pulsieren bei Stufe > 5."""
        if self.dev is None or getattr(self, "level", 0) <= 5:
            return
        now = time.time()
        if now - self._blink_t >= LED_BLINK:
            self._blink_t = now
            self._blink_on = not self._blink_on
            self.set_mask(0x1F if self._blink_on else (0x1F & ~LED_RED_MASK))   # rote LEDs blinken, Rest bleibt an

    def flash(self, times=2):
        for _ in range(times):
            self.set_mask(0x1F)
            time.sleep(0.12)
            self.set_mask(0x00)
            time.sleep(0.12)

    def close(self):
        if self.dev is not None:
            self.set_mask(0)
            self.dev.close()


# --------- Fokus-Check: läuft TD2 im Vordergrund? ---------
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True) if sys.platform == "win32" else None
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_focus_cache = {"t": 0.0, "ok": False}


def _pid_exe(pid):
    h = _kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return ""
    buf = ctypes.create_unicode_buffer(1024)
    size = ctypes.c_ulong(len(buf))
    name = buf.value if _kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)) else ""
    _kernel32.CloseHandle(h)
    return name.rsplit("\\", 1)[-1].lower()


def game_focused():
    """True, wenn das Vordergrundfenster zu GAME_EXE gehört (Ergebnis 100 ms gecacht)."""
    if _user32 is None:
        return True
    now = time.time()
    if now - _focus_cache["t"] < 0.1:
        return _focus_cache["ok"]
    ok = False
    hwnd = _user32.GetForegroundWindow()
    if hwnd:
        pid = ctypes.c_ulong(0)
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        ok = _pid_exe(pid.value) == GAME_EXE.lower()
    _focus_cache["t"], _focus_cache["ok"] = now, ok
    return ok


# --------- TD2-Fenster finden und nach vorne holen ---------
SC_LALT = 0x38
SW_RESTORE = 9
_WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p) if sys.platform == "win32" else None


def find_game_window():
    """HWND des sichtbaren Hauptfensters von GAME_EXE, sonst None."""
    if _user32 is None:
        return None
    found = []

    def cb(hwnd, _):
        if _user32.IsWindowVisible(hwnd):
            pid = ctypes.c_ulong(0)
            _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if _pid_exe(pid.value) == GAME_EXE.lower():
                found.append(hwnd)
                return False
        return True

    _user32.EnumWindows(_WNDENUMPROC(cb), 0)
    return found[0] if found else None


def bring_game_to_front():
    hwnd = find_game_window()
    if not hwnd:
        return False
    if _user32.IsIconic(hwnd):
        _user32.ShowWindow(hwnd, SW_RESTORE)
    # Trick: kurzer Alt-Druck gibt uns das Recht, den Vordergrund zu wechseln
    _key_event(SC_LALT, up=False)
    _key_event(SC_LALT, up=True)
    _user32.SetForegroundWindow(hwnd)
    _focus_cache["t"] = 0.0   # Cache verwerfen
    return True


try:
    import msvcrt

    def console_key():
        """Gedrückte Taste im Konsolenfenster oder None (blockiert nicht)."""
        if msvcrt.kbhit():
            return msvcrt.getwch()
        return None
except ImportError:
    def console_key():
        return None


def fail(msg):
    err = sdl2.SDL_GetError()
    print(f"FEHLER: {msg} {err.decode() if err else ''}")
    sdl2.SDL_Quit()
    sys.exit(1)


def step_to_raw(step):
    """Stufenindex -> Achsenwert -32768..32767"""
    return int(step / (STEPS - 1) * 65535) - 32768


def raw_to_step_f(raw):
    return (raw + 32768) / 65535 * (STEPS - 1)


def factor_for(boundary):
    return HEAVY.get(boundary, 1.0)


def wall_for(boundary):
    return int(min(WALL * factor_for(boundary), WALL_ABS_MAX))


def stiff_for(boundary):
    return int(min(STIFFNESS * factor_for(boundary), 32767))


def main():
    if sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK | sdl2.SDL_INIT_HAPTIC) != 0:
        fail("SDL_Init")

    joy = None
    for i in range(sdl2.SDL_NumJoysticks()):
        j = sdl2.SDL_JoystickOpen(i)
        if sdl2.SDL_JoystickIsHaptic(j) == 1:
            joy = j
            break
        sdl2.SDL_JoystickClose(j)
    if joy is None:
        fail("Kein Gerät mit Force Feedback gefunden (G HUB installiert?).")
    print("Gerät:", sdl2.SDL_JoystickName(joy).decode())

    hap = sdl2.SDL_HapticOpenFromJoystick(joy)
    if not hap:
        fail("SDL_HapticOpenFromJoystick")

    caps = sdl2.SDL_HapticQuery(hap)
    if not (caps & sdl2.SDL_HAPTIC_SPRING):
        fail("Gerät meldet keinen Spring-Effekt. Ist G HUB aktiv?")

    sdl2.SDL_HapticSetGain(hap, 100)
    sdl2.SDL_HapticSetAutocenter(hap, 0)

    sign = -1 if INVERT else 1

    eff = sdl2.SDL_HapticEffect()
    eff.type = sdl2.SDL_HAPTIC_SPRING
    eff.condition.direction.type = sdl2.SDL_HAPTIC_CARTESIAN
    eff.condition.direction.dir[0] = 1
    eff.condition.length = sdl2.SDL_HAPTIC_INFINITY
    eff.condition.deadband[0] = int(DEADBAND * 65535 / (STEPS - 1))

    def apply(step, side=0):
        """side: +1 = wir drücken nach oben (step->step+1), -1 = nach unten, 0 = unbekannt.
        Der Logitech-Treiber wertet nur EINE Seite aus, daher setzen wir Härte und
        Sättigung symmetrisch auf die Wand der Seite, in die gerade gedrückt wird."""
        eff.condition.center[0] = step_to_raw(step)
        if side > 0 and step < STEPS - 1:
            wall, stiff = wall_for(step), stiff_for(step)
        elif side < 0 and step > 0:
            wall, stiff = wall_for(step - 1), stiff_for(step - 1)
        elif side == 0:
            wall, stiff = WALL, STIFFNESS
        else:  # Endanschlag
            wall, stiff = 32767, 32767
        eff.condition.right_coeff[0] = stiff * sign
        eff.condition.left_coeff[0] = stiff * sign
        eff.condition.right_sat[0] = wall
        eff.condition.left_sat[0] = wall
        sdl2.SDL_HapticUpdateEffect(hap, eid, ctypes.byref(eff))

    def wheel_step_f():
        sdl2.SDL_JoystickUpdate()
        return raw_to_step_f(sdl2.SDL_JoystickGetAxis(joy, 0))

    # Startstufe aus aktueller Position
    current = int(round(wheel_step_f()))
    eff.condition.center[0] = step_to_raw(current)

    eid = sdl2.SDL_HapticNewEffect(hap, ctypes.byref(eff))
    if eid < 0:
        fail("SDL_HapticNewEffect (Spring)")
    apply(current)
    if sdl2.SDL_HapticRunEffect(hap, eid, 1) != 0:
        fail("SDL_HapticRunEffect")

    # Zweiter Effekt: Konstantkraft für den Resync (bewegt das Rad aktiv)
    ceff = sdl2.SDL_HapticEffect()
    ceff.type = sdl2.SDL_HAPTIC_CONSTANT
    ceff.constant.direction.type = sdl2.SDL_HAPTIC_CARTESIAN
    ceff.constant.direction.dir[0] = 1
    ceff.constant.length = sdl2.SDL_HAPTIC_INFINITY
    ceff.constant.level = 0
    ceid = sdl2.SDL_HapticNewEffect(hap, ctypes.byref(ceff))
    if ceid < 0:
        print("Hinweis: kein Constant-Effekt verfügbar, Resync bewegt das Rad nicht:",
              sdl2.SDL_GetError().decode())
    else:
        print(f"Constant-Effekt angelegt (id {ceid}), Spring-Effekt id {eid}")

    # ---------- Testmodus: python g29_detent_test.py forcetest ----------
    if len(sys.argv) > 1 and sys.argv[1].lower() == "forcetest":
        print("\nFORCETEST: Rad loslassen. Erst Kraft -8000 (2 s), dann +8000 (2 s).")
        r = sdl2.SDL_HapticStopEffect(hap, eid)
        print("  StopEffect(spring) ->", r)
        for lvl in (-8000, 8000):
            ceff.constant.level = lvl
            r1 = sdl2.SDL_HapticUpdateEffect(hap, ceid, ctypes.byref(ceff))
            r2 = sdl2.SDL_HapticRunEffect(hap, ceid, 1)
            print(f"  level {lvl:+d}: Update -> {r1}, Run -> {r2}  {sdl2.SDL_GetError().decode()}")
            t0 = time.time()
            while time.time() - t0 < 2.0:
                print(f"    pos {wheel_step_f():5.1f}", end="\r")
                time.sleep(0.1)
            print()
            sdl2.SDL_HapticStopEffect(hap, ceid)
            time.sleep(0.5)
        print("  Variante B: Spring bleibt an, Constant +8000 zusätzlich (2 s)")
        sdl2.SDL_HapticRunEffect(hap, eid, 1)
        ceff.constant.level = 8000
        sdl2.SDL_HapticUpdateEffect(hap, ceid, ctypes.byref(ceff))
        r = sdl2.SDL_HapticRunEffect(hap, ceid, 1)
        print("  Run ->", r)
        t0 = time.time()
        while time.time() - t0 < 2.0:
            print(f"    pos {wheel_step_f():5.1f}", end="\r")
            time.sleep(0.1)
        print()
        sdl2.SDL_HapticStopAll(hap)
        sdl2.SDL_HapticDestroyEffect(hap, eid)
        sdl2.SDL_HapticDestroyEffect(hap, ceid)
        sdl2.SDL_Quit()
        print("FORCETEST fertig.")
        return

    loco_name = DEFAULT_LOCO
    print(f"Lok: {loco_name} – {STEPS} Stufen aktiv (Feder im Gerät). Strg+C zum Beenden.")
    print(f"Menü: Taste '{MENU_KEY.upper()}' in diesem Fenster -> Lok wechseln.")
    print("Tasten:", "Num+ / Num- werden gesendet" if SEND_KEYS else "AUS (nur Anzeige)")
    print(f"Fokus: Tasten gehen nur raus, wenn {GAME_EXE} im Vordergrund ist.")
    print(f"Resync: G29-Knopf {RESYNC_BUTTON} -> Fahrschalter im Spiel auf 0 fahren und auf Radstufe setzen.")
    print("Knöpfe: " + ", ".join(f"{b} -> {KEY_NAMES.get(sc, hex(sc))}" for b, (sc, _) in sorted(BUTTON_KEYS.items())))
    print("Hinweis: Rad und Spiel sollten beim Start auf derselben Stufe stehen (oder Resync drücken).\n")
    print(f"Stufe {current:2d} / {STEPS - 1}")

    leds = G29Leds()
    shunt = 0                 # aktuelle Zwischenstufe laut unserer Zählung
    leds.show_level(shunt)

    game_step = current       # Stufe, auf der TD2 unserer Kenntnis nach steht
    last_tap = 0.0
    focus_warned = False
    last_focus_try = 0.0
    n_buttons = sdl2.SDL_JoystickNumButtons(joy)
    btn_prev = [0] * n_buttons
    side = 0                  # Richtung, in die aktuell von der Mitte weggedrückt wird

    def resync():
        """Rad fährt per Konstantkraft auf Stufe 0, parallel gehen Num- Drücke ans Spiel."""
        nonlocal game_step, last_tap, current, side
        if not game_focused():
            if AUTO_FOCUS and bring_game_to_front():
                time.sleep(FOCUS_SETTLE)
            if not game_focused():
                print("Resync: TD2 ist nicht im Vordergrund – abgebrochen.")
                return

        print("Resync: Rad loslassen – fährt auf Stufe 0, Spiel wird mitgenommen …")

        def set_force(level):
            if ceid >= 0:
                ceff.constant.level = int(max(-32767, min(32767, level)))
                sdl2.SDL_HapticUpdateEffect(hap, ceid, ctypes.byref(ceff))

        sdl2.SDL_HapticStopEffect(hap, eid)          # Feder aus, damit sie nicht gegenhält
        direction = RESYNC_DIRECTION
        if ceid >= 0:
            ceff.constant.level = direction * RESYNC_FORCE
            r1 = sdl2.SDL_HapticUpdateEffect(hap, ceid, ctypes.byref(ceff))
            r2 = sdl2.SDL_HapticRunEffect(hap, ceid, 1)
            if r1 != 0 or r2 != 0:
                print(f"Resync: Constant Update -> {r1}, Run -> {r2}: {sdl2.SDL_GetError().decode()}")

        minus_left = STEPS + 1
        t0 = time.time()
        next_tap = t0
        arrived_at = None
        while True:
            now = time.time()
            if minus_left > 0 and now >= next_tap:
                tap(SC_NUM_MINUS)
                minus_left -= 1
                next_tap = now + RESYNC_GAP
            pos = wheel_step_f()

            # Kraft: voll bei großem Abstand, linear runter bis RESYNC_MIN_FORCE nahe 0
            if pos > 0.35:
                ramp = min(1.0, pos / 3.0)
                level = RESYNC_MIN_FORCE + (RESYNC_FORCE - RESYNC_MIN_FORCE) * ramp
                set_force(direction * level)
                arrived_at = None
            else:
                set_force(0)
                arrived_at = arrived_at or now

            if minus_left == 0 and arrived_at and now - arrived_at > 0.3:
                break
            if now - t0 > RESYNC_TIMEOUT:
                print(f"Resync: Timeout – Rad steht bei {pos:.1f}, Rad ggf. von Hand nach links drehen.")
                break
            time.sleep(0.01)

        set_force(0)
        if ceid >= 0:
            sdl2.SDL_HapticStopEffect(hap, ceid)
        sdl2.SDL_HapticRunEffect(hap, eid, 1)        # Feder wieder an
        leds.flash()
        leds.show_level(shunt)

        current = int(round(wheel_step_f()))
        game_step = 0
        side = 0
        last_tap = time.time()
        apply(current, 0)     # normale Feder wiederherstellen
        if current == 0:
            print("Resync fertig: Rad = Spiel = Stufe 0")
        else:
            print(f"Resync: Spiel auf 0, Rad bei {current} – wird nachgeholt.")

    def switch_loco(name, do_resync):
        nonlocal loco_name, current, game_step, side, shunt
        global STEPS, HEAVY, SHUNT_MAX
        cfg = LOCOS[name]
        STEPS, HEAVY, SHUNT_MAX = cfg["steps"], cfg["heavy"], cfg.get("shunt", 5)
        shunt = 0
        leds.show_level(shunt)
        loco_name = name
        eff.condition.deadband[0] = int(DEADBAND * 65535 / (STEPS - 1))
        current = int(round(wheel_step_f()))
        game_step = current
        side = 0
        apply(current, 0)
        print(f"\nLok gewechselt: {name} – {STEPS} Stufen (0..{STEPS - 1}), "
              f"schwer bei {sorted(HEAVY)}, {SHUNT_MAX} Zwischenstufen")
        if do_resync:
            resync()
        else:
            print(f"Rad steht auf Stufe {current}; Spiel muss dazu passen (sonst Resync-Knopf).")

    def loco_menu():
        names = list(LOCOS)
        print("\n===== Lok wählen =====")
        for i, n in enumerate(names, 1):
            mark = " (aktiv)" if n == loco_name else ""
            print(f"  {i}) {n} – {LOCOS[n]['steps']} Stufen, {LOCOS[n].get('shunt', 5)} Zwischenstufen{mark}")
        print("  0) Abbrechen")
        try:
            choice = input("Auswahl: ").strip()
        except EOFError:
            return
        if not choice.isdigit() or not (1 <= int(choice) <= len(names)):
            print("Abgebrochen.")
            return
        name = names[int(choice) - 1]
        ans = input("Danach Resync auf Stufe 0 ausführen? [J/n]: ").strip().lower()
        switch_loco(name, ans in ("", "j", "ja", "y"))

    dt = 1.0 / RATE_HZ
    try:
        while True:
            k = console_key()
            if k and k.lower() == MENU_KEY:
                loco_menu()
                continue

            step_f = wheel_step_f()
            d = step_f - current

            # Richtungswechsel erkennen -> passende Wand setzen (nur bei Änderung)
            new_side = 1 if d > DEADBAND else (-1 if d < -DEADBAND else side)
            if new_side != side:
                side = new_side
                apply(current, side)

            new = current
            if d > 0.5 + HYSTERESIS and current < STEPS - 1:
                new = current + 1
            elif d < -(0.5 + HYSTERESIS) and current > 0:
                new = current - 1

            if new != current:
                current = new
                side = 0
                apply(current, 0)
                tag = "  [schwer]" if (current in HEAVY or current - 1 in HEAVY) else ""
                print(f"Stufe {current:2d} / {STEPS - 1}{tag}")

            # ---- Spiel an Radstufe angleichen (ein Tastendruck pro TAP_GAP, nur mit Fokus) ----
            if game_step != current:
                if game_focused():
                    focus_warned = False
                    if time.time() - last_tap >= TAP_GAP:
                        if game_step < current:
                            tap(SC_NUM_PLUS)
                            game_step += 1
                            key = "Num+"
                        else:
                            tap(SC_NUM_MINUS)
                            game_step -= 1
                            key = "Num-"
                        last_tap = time.time()
                        print(f"   -> {key}  (Spiel {game_step} / Rad {current})")
                else:
                    if AUTO_FOCUS and time.time() - last_focus_try >= FOCUS_RETRY:
                        last_focus_try = time.time()
                        if bring_game_to_front():
                            print("   TD2 in den Vordergrund geholt")
                            time.sleep(FOCUS_SETTLE)
                            last_tap = time.time()
                        elif not focus_warned:
                            print("   TD2-Fenster nicht gefunden – läuft das Spiel?")
                            focus_warned = True
                    elif not focus_warned and not AUTO_FOCUS:
                        focus_warned = True
                        print(f"   TD2 nicht im Vordergrund – warte (Rad {current}, Spiel {game_step})")

            # ---- Knöpfe: Resync, Tasten, Anzeige der Knopf-Indizes ----
            for b in range(n_buttons):
                st = sdl2.SDL_JoystickGetButton(joy, b)
                if st and not btn_prev[b]:
                    print(f"[Knopf {b} gedrückt]")
                    if b == RESYNC_BUTTON:
                        resync()
                    elif b in BUTTON_KEYS:
                        sc, ext = BUTTON_KEYS[b]
                        if game_focused() or (AUTO_FOCUS and bring_game_to_front()):
                            tap(sc, ext)
                            info = ""
                            if b == SHUNT_UP_BUTTON and shunt < SHUNT_MAX:
                                shunt += 1
                            elif b == SHUNT_DOWN_BUTTON and shunt > 0:
                                shunt -= 1
                            if b in (SHUNT_UP_BUTTON, SHUNT_DOWN_BUTTON):
                                leds.show_level(shunt)
                                info = f"   Zwischenstufe {shunt}/{SHUNT_MAX}"
                            print(f"   -> {KEY_NAMES.get(sc, hex(sc))}{info}")
                btn_prev[b] = st

            leds.tick()
            time.sleep(dt)

    except KeyboardInterrupt:
        print("\nBeende…")
    finally:
        leds.close()
        sdl2.SDL_HapticStopAll(hap)
        sdl2.SDL_HapticDestroyEffect(hap, eid)
        if ceid >= 0:
            sdl2.SDL_HapticDestroyEffect(hap, ceid)
        sdl2.SDL_HapticClose(hap)
        sdl2.SDL_JoystickClose(joy)
        sdl2.SDL_Quit()


if __name__ == "__main__":
    main()