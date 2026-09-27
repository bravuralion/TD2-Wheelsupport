# G29 Fahrschalter für Train Driver 2 – Anleitung

Mit diesem kleinen Programm wird dein Logitech G29 Lenkrad zum Fahrschalter für die polnischen E-Loks in Train Driver 2. Das Lenkrad rastet spürbar von Stufe zu Stufe, wichtige Übergänge (z. B. 0 → 1 oder in die Dauerfahrstufen) gehen schwerer, und jede Raststufe wird automatisch als Tastendruck ans Spiel geschickt. Die Knöpfe am Lenkrad übernehmen weitere Funktionen, die LED-Leiste zeigt die Feldschwächung an.

Du musst nichts programmieren. Einmal einrichten, danach reicht ein Doppelklick.

---

## 1. Was du brauchst

- Windows 10 oder 11
- Logitech G29 (G923 sollte auch gehen)
- **Logitech G HUB** installiert und gestartet (die normale Lenkrad-Software von Logitech)
- Train Driver 2
- Einmalig Internet für die Installation

## 2. Python installieren (einmalig)

Das Programm ist in Python geschrieben, deshalb muss Python auf dem PC sein. Das ist kostenlos und in fünf Minuten erledigt.

1. Gehe auf **https://www.python.org/downloads/** und klicke auf den großen gelben Button "Download Python 3.x".
2. Starte die heruntergeladene Datei.
3. **Ganz wichtig:** Setze im ersten Fenster unten den Haken bei **"Add python.exe to PATH"** (oder "Add Python to PATH"). Ohne diesen Haken findet die Startdatei Python später nicht.
4. Klicke auf **"Install Now"** und warte, bis die Installation fertig ist.
5. Fenster schließen. Fertig.

Falls du den Haken vergessen hast: Python deinstallieren (Windows-Einstellungen → Apps), dann noch einmal von Schritt 1 an.

## 3. Programm-Ordner

Lege diese drei Dateien zusammen in einen Ordner, z. B. `C:\G29-TD2\`:

- `Start.bat` – zum Starten doppelklicken
- `g29_detent_test.py` – das eigentliche Programm
- `Anleitung.md` – diese Anleitung

## 4. G HUB einstellen

Öffne G HUB, wähle das G29 und stelle ein:

- **Lenkbereich (Operating Range): 900°** – je größer, desto mehr Platz haben die Stufen
- **Force Feedback / Kraftrückmeldung: 100 %**
- Zentrierfeder (Centering Spring) **aus**, falls vorhanden

G HUB muss beim Spielen im Hintergrund laufen.

## 5. Starten

1. Lenkrad anstecken, G HUB läuft.
2. Train Driver 2 starten und in die Lok einsteigen.
3. **Doppelklick auf `Start.bat`.**

Beim allerersten Start werden automatisch ein paar Zusatzpakete heruntergeladen – das dauert eine Minute und braucht Internet. Danach nicht mehr.

Es öffnet sich ein schwarzes Textfenster. Das bleibt die ganze Zeit offen, du kannst es aber minimieren. Darin siehst du, welche Stufe gerade aktiv ist und welche Tasten gesendet werden.

Wenn du das Rad drehst, sollte es jetzt spürbar einrasten.

## 6. Rad und Spiel abgleichen (Resync)

Das Programm weiß nicht, wo der Fahrschalter in der Lok gerade steht. Deshalb drückst du nach dem Start einmal den **Resync-Knopf** (Knopf 3 am Lenkrad, meist die Dreieck-Taste):

- Das Rad dreht sich von selbst ganz nach links auf Stufe 0. **Rad dabei loslassen!**
- Gleichzeitig wird der Fahrschalter im Spiel auf 0 gefahren.
- Die LED-Leiste blinkt kurz, danach passt alles zusammen.

Immer wenn Rad und Spiel auseinandergelaufen sind (z. B. nach einem Lokwechsel), einfach wieder Resync drücken.

## 7. Lok wechseln

Jede Lok hat eine andere Zahl von Stufen. Zum Wechseln:

1. Klicke in das schwarze Textfenster des Programms.
2. Drücke die Taste **M**.
3. Tippe die Nummer der Lok ein und drücke Enter.
4. Auf die Frage nach dem Resync einfach Enter drücken – das Rad fährt dann auf 0.

Dann wieder zurück ins Spiel.

Vorhandene Loks: **EP09**, **ET22**, **EP08/EP07**, **ST44**. Beim Start ist die EP09 aktiv.

## 8. Knöpfe am Lenkrad

| Knopf | Funktion / Taste |
|------:|------------------|
| Lenkrad drehen | Fahrschalter hoch / runter (Num+ / Num-) |
| 3 | Resync – Rad und Spiel auf Stufe 0 |
| 4 | Feldschwächung eine Stufe hoch (Num /) – LED-Leiste füllt sich |
| 5 | Feldschwächung eine Stufe runter (Num *) – LED geht aus |
| 10 | Num . |
| 11 | T |
| 19 | Num 1 |
| 20 | Num 7 |
| 21 | Num 3 |
| 22 | Num 9 |
| 23 | Num 4 |
| 24 | Leertaste |

Welche Knopfnummer welcher Taste am Rad entspricht, siehst du im Textfenster: Jeder Druck zeigt dort `[Knopf X gedrückt]`.

Die LED-Leiste zeigt die Feldschwächung: eine LED pro Stufe. Beim ET22 (6 Stufen) blinkt bei Stufe 6 zusätzlich die rote LED.

## 9. Gut zu wissen

- Tasten werden **nur ans Spiel geschickt, wenn Train Driver 2 im Vordergrund ist.** Bist du gerade im Browser und drehst am Rad, holt das Programm TD2 automatisch nach vorne und schickt die Tasten dann nach.
- Das Programm muss nicht als Administrator laufen – außer TD2 läuft selbst als Administrator, dann muss `Start.bat` es auch (Rechtsklick → Als Administrator ausführen).
- Beenden: Textfenster schließen oder darin Strg+C drücken.

## 10. Wenn etwas nicht geht

**"Python wurde nicht gefunden"**
Python ist nicht installiert oder der PATH-Haken fehlte. Siehe Schritt 2.

**"Kein Gerät mit Force Feedback gefunden"**
Lenkrad nicht angesteckt oder G HUB läuft nicht. G HUB starten, Rad kurz ab- und wieder anstecken, `Start.bat` neu starten.

**"Gerät meldet keinen Spring-Effekt"**
G HUB läuft nicht, oder ein anderes Programm (z. B. ein Rennspiel) hat das Force Feedback belegt. Andere Programme schließen.

**Das Rad rastet nicht oder nur schwach**
In G HUB Force Feedback auf 100 % prüfen. Wenn es immer noch zu weich ist, kann man in der Datei `g29_detent_test.py` die Werte `WALL` (Widerstand zwischen den Stufen) und `STIFFNESS` (Festigkeit in der Raststufe) erhöhen – Datei mit dem Editor öffnen, Zahl ändern, speichern, Programm neu starten.

**Rad und Spiel stimmen nicht überein**
Resync-Knopf drücken (Knopf 3), Rad dabei loslassen.

**Die Tasten kommen im Spiel nicht an**
Prüfen, ob TD2 wirklich im Vordergrund ist. Läuft TD2 als Administrator, muss `Start.bat` ebenfalls als Administrator gestartet werden.

**LEDs bleiben dunkel**
Im Textfenster steht beim Start, ob die LED-Leiste gefunden wurde. Wenn nicht, ist es meist G HUB, das den Zugriff blockiert. Das Programm funktioniert trotzdem, nur ohne LED-Anzeige.

**Beim ersten Start bricht die Installation ab**
Internetverbindung prüfen und `Start.bat` noch einmal ausführen.

---

## Anhang: Eigene Anpassungen

Alle Einstellungen stehen oben in der Datei `g29_detent_test.py` im Abschnitt "Einstellungen". Du kannst die Datei mit dem Windows-Editor (Notepad) öffnen. Nach dem Speichern das Programm neu starten.

Die wichtigsten Stellen:

- **`LOCOS`** – die Lok-Profile. Neue Lok = neuer Eintrag nach demselben Muster: Stufenzahl (`steps`, gezählt inklusive der 0), schwere Übergänge (`heavy`), Zahl der Zwischenstufen (`shunt`).
- **`BUTTON_KEYS`** – welcher Knopf welche Taste schickt.
- **`RESYNC_BUTTON`** – der Knopf für den Resync.
- **`WALL` / `STIFFNESS`** – wie schwer bzw. wie knackig das Rasten ist.
- **`DEFAULT_LOCO`** – welche Lok beim Start aktiv ist.
