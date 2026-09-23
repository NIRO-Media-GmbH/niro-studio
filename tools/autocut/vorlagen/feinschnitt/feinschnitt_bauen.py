"""Vorlage (Stand 15.09.2026): Feinschnitt als neue Resolve-Timeline bauen (V1–V4, A1–A3, Marker) mit Schwarzframe-Prüfung.

Aufruf: tools/autocut/venv/bin/python _intern/feinschnitt_bauen.py            → Probelauf (Plan, Prüfungen, Schwarzframe-Rechnung)
        tools/autocut/venv/bin/python _intern/feinschnitt_bauen.py --bauen    → Timeline im freigegebenen Projekt PROJEKT bauen + Readback
        danach:  tools/autocut/venv/bin/python tools/autocut/scripts/autocut_readback.py "<Charge>" --timeline "<Name>"  → Bau-Readback (Replay-Runde)

User-Wünsche (15.09.): keine Schwarzframes (alles mit Grafik oder B-Roll gedeckt), Grafiken inkl. Vollbild,
A/B-Perspektiven wechseln, hier und da L-/J-Cuts, Musik (mehrere Tracks, Wechsel pro Thema, nahtlose Übergänge),
Audio-Normalisierung + Voice Isolation, B-Roll stabilisieren und ggf. 50 % Tempo. Grading folgt in eigenem Schritt.

Aufbau (Frames = Timeline-Frames, 25 fps; O-Ton-Positionen wie in der roh-Timeline „AutoCut <video-kurz> JJJJ-MM-TT HHMM (roh)"):
  V1 FX3 (Bild, mit Bildverlängerungen für nahtlose Übergänge, J-/L-Cuts, optional ein Punch-in)
  V2 a7IV durchgehend unter jedem FX3-Stück, nur in den A-Abschnitten aktiv (Perspektivwechsel), sonst deaktiviert
  V3 B-Roll aus der User-Auswahl (nur deren Bereiche; Zeitlupe 50 % bei Händen/Details/Kamerafahrten, nie bei Sprechenden)
  V4 Grafikebene (ProRes 4444 Alpha), je Grafik-Element ein Clip, auf die sichtbaren Frames getrimmt
  A1 FX3-Ton (True Peak −3 dBTP je Clip, Voice Isolation), A2/A3 Musik mit Überblendungen, A4/A5 leer für SFX
Nur neue Objekte: neue Timeline, Importe in den eigenen Bin AutoCut/<video-kurz>. Timeline und Bin des Users werden
wiederhergestellt. Schreibt _intern/autocut/feinschnitt.json.

Eingaben: _intern/autocut/timeline.json (roh-Timeline aus AutoCut), _intern/autocut/probe.json (scripts/resolve_probe.py),
_intern/autocut/broll_auswahl.json (Auswahl-Timeline des Users; darf ohne BROLL fehlen), _intern/autocut/gyroflow.json
(scripts/autocut_gyroflow.py; fehlt die Datei, bleibt jeder Shot beim Stabilize()-Weg), Render der Grafikebene (GRAFIK),
Remotion-Datei mit der TIMELINE der Grafik-Elemente (GRAFIK_TSX), Musik-WAVs aus Material/Musik.
Messungen (ffmpeg, einmal je Render): _intern/grafik/alpha_<Render>.json (Deckkraft je Frame), alpha_<Render>_ymax.txt (Sichtbarkeit).

ANPASSEN-Block füllen (Reihenfolge):
  1. PROJEKT, VIDEO_KURZ, BREITE/HOEHE (timeline.json: project, width, height); ENDE = total_frames der roh-Timeline
     = GESAMT_FRAMES der Grafikebene (der Render muss genau ENDE Frames haben).
  2. V1_AENDERUNGEN + PUNCH_IN aus den O-Ton-Positionen der roh-Timeline (timeline.json → items je beat_nr, nach rec_in_f):
     Pausen bis zum nächsten Satz im Bild halten, J-/L-Cuts per Bild-In/-Out gegen den Ton verschieben.
  3. A_ABSCHNITTE: nur innerhalb von V2-Items der roh-Timeline (a7-Paar vorhanden); nach dem Gesichts-Check ggf. streichen.
  4. BROLL aus broll_auswahl.json (Shot-Nr., Auswahlbereich left_offset_f/dauer_f) mit den Record-Positionen des
     B-Roll-Einsatzes (broll_einsatz.json → plan: shot, rec_in_f); 50 % nur bei 50p-Quellen und nie bei Sprechenden.
  5. GRAFIK + GRAFIK_TSX — V4-Clips und Schwarzframe-Prüfung entstehen daraus (Einträge { id: "…", from: N, dauer: N }
     oder dauer: GESAMT_FRAMES - N, genau in dieser Reihenfolge).
  6. MUSIK_1… + MUSIK_PLAN aus _intern/musik/analyse.json (musik_analyse.py: Takt-Raster, Abschnitte), Sprünge im Track mit
     musik/sprung_berechnen.py; Pegel nach dem Bau mit musik/mischung_pruefen.py messen und hier nachtragen
     (die Timeline übernimmt geänderte Werte erst beim Neubau).
  7. MARKER (Blur/Klärung, Grafik- und Musikwechsel). Probelauf wiederholen, bis keine FEHLER mehr kommen, dann --bauen.
Wird als Modul `fb` geladen (feinschnitt_umbau.py, musik/mischung_pruefen.py, Vorlagen für SFX, Color, Gesichts-Check,
Begradigen): Funktions- und Konstantennamen sowie die Schlüssel des plan()-Dicts nicht umbenennen.
Herkunft: Taxodia-Charge, _intern/feinschnitt_bauen.py
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.timeline_model import Item, MarkerSpec  # noqa: E402
from niro_autocut import telemetrie as TM  # noqa: E402
from niro_autocut import gyroflow as GF  # noqa: E402
from niro_autocut.charge import load_config  # noqa: E402

RA.TRACK_INDEX["A3"] = 3  # dritte Tonspur für Musik-Überblendungen (nur in diesem Skript)

CH = Path(__file__).resolve().parent.parent
AC = CH / "_intern" / "autocut"
MUSIK = CH / "Material" / "Musik"
FPS = 25  # Standard (15.09.): Timeline 25 fps — musik/mischung_pruefen.py und weitere Vorlagen rechnen fest mit 25
TELE = TM.laden(AC)  # _intern/autocut/telemetrie.json (autocut_telemetrie.py); leer = Standard stabilisieren
CFG = load_config(CH)
TCFG = CFG["telemetrie"]

# Gyroflow-OFX (Spec 2026-09-22, Befund 1 — Resolve 21.1, gemessen 22./23.09.2026): ersetzt in 6d Stabilize() für
# B-Roll-Shots, für deren Quelldatei ein Sidecar vorliegt (gyroflow.json, scripts/autocut_gyroflow.py). Tool-Kennung
# und Parametername stammen aus Fusion.GetToolList() bzw. dem Readback von SetInput im offenen Testprojekt —
# keine geratenen Werte.
GYRO_TOOL_ID = "ofx.nl.smslv.gyroflowofx.fisheyestab_v1"  # Fusion.GetToolList(), angezeigt als „Gyroflow"
GYRO_PARAM_PROJEKT = "gyrodata"  # SetInput-Name für den Pfad der .gyroflow-Datei
GYRO_BEI_ZEITLUPE = True  # VideoSpeed wirkt nachweislich (Gegenprobe 23.09.2026, RMSE-Vergleich der Frames)

# ── ANPASSEN je Charge ─────────────────────────────
PROJEKT = "<Resolve-Projekt>"  # Name des in dieser Session freigegebenen Resolve-Projekts (Abgleich vor jedem Schreiben)
VIDEO_KURZ = "<video-kurz>"  # Kurzname wie in der roh-Timeline „AutoCut <video-kurz> … (roh)" → Bin AutoCut/<video-kurz>
BREITE, HOEHE = 3840, 2160  # Timeline-Auflösung in px wie die roh-Timeline (timeline.json width/height; Hochkant z. B. 2160, 3840)
ENDE = 0  # Gesamtlänge in Timeline-Frames = total_frames der roh-Timeline = GESAMT_FRAMES der Grafikebene
GRAFIK = CH / "Ergebnisse" / "Renders" / "<grafikebene>.mov"  # Render der Grafikebene: ProRes 4444 mit Alpha, ab Frame 0, ENDE Frames
GRAFIK_TSX = STUDIO / "tools" / "motion" / "src" / "clients" / "<kunde>" / "projects" / "<projekt>" / "Grafikebene.tsx"  # Remotion-TIMELINE
MUSIK_1 = MUSIK / "<Musik-Track 1>.wav"  # Musik-Tracks als WAV in Material/Musik; Namen für MUSIK_PLAN
MUSIK_2 = MUSIK / "<Musik-Track 2>.wav"
MUSIK_3 = MUSIK / "<Musik-Track 3>.wav"

# --- V1: Bildverlängerungen / J-/L-Cuts (Beat, Index im Beat, Feld "in"/"out", Delta in Frames) -------------------------
# Index = Position unter den V1-Stücken des Beats nach rec_in_f (−1 = letztes). "out" +n: Bild hält n Frames länger (Pause bis
# zum nächsten Satz gedeckt oder J-Cut in den Ton des nächsten Sprechers); "in" ±n verschiebt Record- und Quell-In gemeinsam.
V1_AENDERUNGEN: list[tuple[str, int, str, int]] = [
    # ("6", -1, "out", +22),   # letztes Stück von Beat #6 hält 22 Frames länger (Quelle bis zum nächsten Satz still)
]
# Punch-in (Inspector-Transform) auf dem index-ten V1-Stück (nach rec_in_f) eines Beats; "beat": None = kein Punch-in.
PUNCH_IN = {"beat": None, "index": 0, "props": {"ZoomX": 1.0, "ZoomY": 1.0, "Pan": 0.0}}
# PUNCH_IN = {"beat": "12", "index": 2, "props": {"ZoomX": 1.12, "ZoomY": 1.12, "Pan": -200.0}}

# --- V2: Abschnitte mit a7-Perspektive (A) als (von, bis) in Timeline-Frames, halboffen; sonst FX3 (B) ---------------------
# Jeder Abschnitt muss ganz in einem V2-Item der roh-Timeline liegen. Nach dem Gesichts-Check streichen, wo eine Karte in der
# a7-Framing zu nah ans Gesicht kommt (Messung 15.09.: 16 px bei 1080p unter dem Kinn → Abschnitt gestrichen, dort bleibt FX3).
A_ABSCHNITTE: list[tuple[int, int]] = [
    # (258, 345),
]

# --- V3: B-Roll (Shot aus broll_auswahl.json, Versatz im Shot [Timeline-Frames bei 100 %], Länge, Record-In, Beat,
# 50 %[, stabil]) -- Versatz + genutzte Länge (bei 50 % die halbe Länge) müssen in der Auswahl des Users liegen —
# kürzen ja, nie verlängern.
# 7. Spalte optional: True/False erzwingt Stabilize() bzw. lässt es aus; weggelassen oder None = Vorschlag aus
# telemetrie.json (hand und wackeln > telemetrie.ruhig_max_px → stabilisieren; stativ/gimbal → nicht; ohne Telemetrie →
# stabilisieren). True bei einer _stabilized-Datei (Avata-Export) ist ein Plan-Fehler: Avata nie in Resolve stabilisieren.
# Gyroflow (gyroflow.json) ersetzt beim Bau Stabilize() unabhängig von dieser Spalte, sobald für die Quelldatei ein
# Sidecar vorliegt (Spec 2026-09-22: alle genutzten B-Roll-Shots, nicht nur die mit stabil=True) — siehe die
# GYRO_*-Konstanten oben und den V3-Abschnitt in bauen().
# 8. Spalte optional (Spec 2026-09-21): Zahl = digitaler Zoom des Shots fest (1.0 = keiner); weggelassen = Automatik der
# Brennweitenregel aus telemetrie.json — nie zweimal dieselbe KB-Brennweite direkt hintereinander (Abstand unter
# telemetrie.brennweite_gleich_max), sonst Zoom auf einen der beiden Shots (1,25×, Grenze telemetrie.digitalzoom_max).
# Ein Wert unter 1.0 (Rand würde sichtbar) oder über der Grenze ist ein Plan-Fehler. Schnelle Zooms im genutzten
# Quellbereich meldet der Probelauf als Hinweis. Ein in 3a erzwungener Zoom (PLAN-Spalte 7) muss hier als 8. Spalte
# stehen; den automatischen rechnet 6d aus den eigenen Quellbereichen neu (bei 50 % andere) — er kann von 3a abweichen.
BROLL: list[tuple] = [
    # (10, 27, 54, 345, "4", True),          # Shot 10 ab Frame 27 seiner Auswahl, 54 Frames lang, Record 345, Beat #4, 50 %
    # (11, 0, 40, 400, "5", False, False),   # … und ausdrücklich nicht stabilisieren
    # (12, 0, 40, 440, "5", False, None, 1.0),   # … Stabilisieren nach Vorschlag, aber kein digitaler Zoom
]

# --- Musik (Spur, Datei, Quell-In [Frames], Record-In, Record-Out, Pegel dB, Fade-In, Fade-Out) ---------------------
# Dramaturgie (Muster 15.09.): ein Track je Thema, Wechsel an den Kapitelblenden der Grafikebene, Anhebung zum Titel auf dem
# Downbeat, Höhepunkt auf dem stärksten O-Ton, unter den CTAs zurückgenommen, letztes Item endet mit der Endcard (bis ENDE).
# Übergänge auf Taktgrenzen (musik_analyse.py), ca. 1 s Überblendung: A2/A3 überlappen, Fade-Out des alten Items ≈ Fade-In des neuen.
# Pegel Standard (15.09.): Musik unter Sprache im Median ca. 14 LU leiser als die Sprache, Stellen ohne Sprache (Titel,
# Vollbild-Grafiken, Endcard) ca. −18 LUFS kurzzeit — nach dem Bau mit musik/mischung_pruefen.py nachmessen.
# Sprünge innerhalb eines Tracks beat-genau per Onset-Korrelation (musik/sprung_berechnen.py; Messung 15.09.: exakt 8 Takte,
# Rest-Versatz −10 ms); die Folge-Items desselben Tracks rücken um dieselbe Frame-Differenz mit, damit die überlappenden
# Kopien sample-gleich bleiben.
MUSIK_PLAN: list[tuple] = [
    # ("A2", MUSIK_1, 0, 107, 357, -18.8, 25, 12),
]

# --- Marker (Frame, Farbe, Name, Notiz, Dauer in Frames) ------------------------------------------------------------------
# Rot = blurren, Gelb = mit dem Kunden klären, Lila = Grafik-Element, Grün = Musikwechsel/-sprung gegenhören.
MARKER: list[tuple[int, str, str, str, int]] = [
    # (4337, "Red", "BLUR Monitor C0001", "Name, URL und Lesezeichen auf dem Bildschirm blurren.", 134),
]
# ── Ende ANPASSEN ──────────────────────────────────

# --- Schwarzframe-Prüfung gegen die gemessene Deckkraft der Grafikebene -----------------------------------------------
# Vollbild-Grafiken sind beim Wipe-in/Iris-out 3–10 Frames nicht deckend (Messung 15.09.: 51 Frames ohne Bild darunter).
# Wo V1–V3 leer sind, muss die Grafik deckend sein; Wipe-Ränder werden durch Halten des O-Ton-Bilds (V1/V2) gedeckt.
ALPHA_JSON = AC.parent / "grafik" / f"alpha_{GRAFIK.stem}.json"  # Deckkraft je Frame, einmal je Render gemessen
DECKEND_AB = 250  # Standard (15.09.): kleinster Alpha-Wert im 192×108-Raster (Fläche gemittelt), ab dem ein Frame deckt
YMAX_TXT = AC.parent / "grafik" / f"alpha_{GRAFIK.stem}_ymax.txt"  # Sichtbarkeit je Frame (YMAX des Alpha-Kanals)


def anpassen_pruefen(fuer_bau: bool = False) -> None:
    """Offene Platzhalter im ANPASSEN-Block verständlich melden statt Folgefehlern (IndexError, FileNotFoundError …)."""
    offen = []
    if ENDE <= 0:
        offen.append("ENDE (Gesamtlänge in Timeline-Frames)")
    if "<" in GRAFIK.name or not GRAFIK.exists():
        offen.append(f"GRAFIK (Render der Grafikebene nicht gefunden: {GRAFIK})")
    if "<" in str(GRAFIK_TSX) or not GRAFIK_TSX.exists():
        offen.append(f"GRAFIK_TSX (Remotion-Datei mit TIMELINE nicht gefunden: {GRAFIK_TSX})")
    platzhalter = sorted({Path(e[1]).name for e in MUSIK_PLAN if "<" in Path(e[1]).name})
    if platzhalter:
        offen.append(f"MUSIK_1… (Platzhalter in MUSIK_PLAN: {', '.join(platzhalter)})")
    if fuer_bau:
        offen += [name for name, wert in (("PROJEKT", PROJEKT), ("VIDEO_KURZ", VIDEO_KURZ)) if "<" in wert]
    if offen:
        raise SystemExit("ANPASSEN-Block in feinschnitt_bauen.py füllen: " + "; ".join(offen))


def lade():
    """roh-Timeline (timeline.json) und B-Roll-Auswahl (broll_auswahl.json) lesen; ohne BROLL darf die Auswahl fehlen."""
    tl_pfad, auswahl_pfad = AC / "timeline.json", AC / "broll_auswahl.json"
    if not tl_pfad.exists():
        raise SystemExit(f"{tl_pfad} fehlt — erst den AutoCut-Rohschnitt bauen (schreibt die timeline.json der roh-Timeline).")
    tl = json.loads(tl_pfad.read_text())
    if not auswahl_pfad.exists():
        if BROLL:
            raise SystemExit(f"{auswahl_pfad} fehlt, BROLL ist aber gefüllt — erst die Auswahl-Timeline des Users einlesen.")
        return tl, {}
    shots = {s["nr"]: s for s in json.loads(auswahl_pfad.read_text())["shots"]}
    return tl, shots


def alpha_min() -> list[int]:
    """Kleinster Alpha-Wert je Frame der Grafikebene (192×108, Fläche gemittelt); misst neu, wenn der Render neuer ist."""
    if not ALPHA_JSON.exists() or ALPHA_JSON.stat().st_mtime < GRAFIK.stat().st_mtime:
        print("Messe Deckkraft der Grafikebene (einmal je Render, ca. 2 min) …")
        import numpy as np
        ff = subprocess.run(["ffmpeg", "-v", "error", "-i", str(GRAFIK), "-vf", "alphaextract,scale=192:108:flags=area",
                             "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True)
        a = np.frombuffer(ff.stdout, np.uint8).reshape(-1, 108 * 192)
        ALPHA_JSON.parent.mkdir(parents=True, exist_ok=True)
        ALPHA_JSON.write_text(json.dumps({"datei": GRAFIK.name, "raster": "192x108 area", "alpha_min": a.min(axis=1).tolist(),
                                          "alpha_mean": a.mean(axis=1).round(1).tolist()}))
    werte = json.loads(ALPHA_JSON.read_text())["alpha_min"]
    if len(werte) != ENDE:
        raise SystemExit(f"Grafikebene hat {len(werte)} Frames, Timeline {ENDE} — Render prüfen.")
    return werte


def luecken(spuren: list[list[Item]]) -> list[tuple[int, int]]:
    deck = [False] * ENDE
    for spur in spuren:
        for it in spur:
            for f in range(max(0, it.rec_in_f), min(ENDE, it.rec_out_f)):
                deck[f] = True
    out, s0 = [], None
    for f in range(ENDE + 1):
        frei = f < ENDE and not deck[f]
        if frei and s0 is None:
            s0 = f
        elif not frei and s0 is not None:
            out.append((s0, f))
            s0 = None
    return out


def bild_halten(p: dict, amin: list[int], fehler: list[str]) -> list[str]:
    """Wo V1–V3 leer sind und die Grafik (noch/schon) nicht deckt: O-Ton-Bild davor länger halten bzw. danach früher starten."""
    log = []
    for a, b in luecken([p["V1"], p["V2"], p["V3"]]):
        offen = [f for f in range(a, b) if amin[f] < DECKEND_AB]
        if not offen:
            continue
        vorne = 0
        while a + vorne < b and amin[a + vorne] < DECKEND_AB:
            vorne += 1
        hinten = 0
        while b - 1 - hinten >= a + vorne and b < ENDE and amin[b - 1 - hinten] < DECKEND_AB:
            hinten += 1
        if vorne + hinten < len(offen):
            fehler.append(f"Lücke {tc(a)}–{tc(b)}: Grafik mitten in der Lücke nicht deckend — Grafik-Timing prüfen")
            continue
        for k, feld, grenze, delta in (("vorne", "out", a, vorne), ("hinten", "in", b, hinten)):
            if not delta:
                continue
            for spur in ("V1", "V2", "V3"):
                for i, it in enumerate(p[spur]):
                    if feld == "out" and it.rec_out_f == grenze:
                        neu = replace(it, rec_out_f=it.rec_out_f + delta, src_out_f=it.src_out_f + delta)
                    elif feld == "in" and it.rec_in_f == grenze:
                        neu = replace(it, rec_in_f=it.rec_in_f - delta, src_in_f=it.src_in_f - delta)
                    else:
                        continue
                    if spur == "V3":
                        fehler.append(f"B-Roll bei {tc(grenze)} müsste verlängert werden (verboten) — Grafik-Timing prüfen")
                        continue
                    p[spur][i] = neu
                    log.append(f"{spur} #{it.beat_nr} {'hält' if feld == 'out' else 'startet'} {delta} f "
                               f"{'länger' if feld == 'out' else 'früher'} ({tc(grenze)}, Wipe der Vollbild-Grafik)")
    return log


def v2_voll(p: dict, roh: list[dict], fehler: list[str]) -> list[Item]:
    """a7 durchgehend unter jedem FX3-Stück (Quelle aus dem Roh-Paar), an den A-Abschnitten geteilt: dort aktiv, sonst deaktiviert.
    Das Bild bleibt gleich, der User kann die Wechsel in Resolve per Roll-Edit verschieben (User 15.09.)."""
    roh_v1 = [i for i in roh if i["track"] == "V1"]
    roh_v2 = [i for i in roh if i["track"] == "V2"]
    stuecke: list[Item] = []
    for v in p["V1"]:
        quelle = next((r for r in roh_v1 if r["beat_nr"] == v.beat_nr and r["rec_in_f"] < v.rec_out_f and v.rec_in_f < r["rec_out_f"]), None)
        a7 = next((r for r in roh_v2 if quelle and (r["rec_in_f"], r["rec_out_f"]) == (quelle["rec_in_f"], quelle["rec_out_f"])), None)
        if a7 is None:
            continue  # Stück ohne a7-Paar in der roh-Timeline (z. B. CTA nur mit FX3)
        grenzen = {v.rec_in_f, v.rec_out_f}
        for s in p["V2"]:
            if v.rec_in_f < s.rec_out_f and s.rec_in_f < v.rec_out_f:
                grenzen |= {max(v.rec_in_f, s.rec_in_f), min(v.rec_out_f, s.rec_out_f)}
        g = sorted(grenzen)
        for a, b in zip(g, g[1:]):
            src = a7["src_in_f"] + a - a7["rec_in_f"]
            if src < 0:
                fehler.append(f"a7 #{v.beat_nr} bei {tc(a)}: Quellframe {src} < 0")
            aktiv = any(s.rec_in_f <= a and b <= s.rec_out_f for s in p["V2"])
            stuecke.append(Item("V2", a7["clip"], src, src + b - a, a, b, aktiv, v.beat_nr, "oton", True))
    ist = sorted((i.rec_in_f, i.rec_out_f, i.src_in_f, i.clip) for i in stuecke if i.enabled)
    soll = sorted((i.rec_in_f, i.rec_out_f, i.src_in_f, i.clip) for i in p["V2"])
    if ist != soll:
        fehler.append("V2 durchgehend: aktive Stücke weichen von den A-Abschnitten ab (Bild würde sich ändern)")
    return stuecke


def grafik_elemente() -> list[tuple[str, int, int]]:
    """(id, von, bis) aller Einträge der Remotion-TIMELINE (GRAFIK_TSX)."""
    text = GRAFIK_TSX.read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r'\{\s*id:\s*"([^"]+)",\s*from:\s*(\d+),\s*dauer:\s*(\d+|GESAMT_FRAMES\s*-\s*\d+)', text):
        von = int(m.group(2))
        dauer = ENDE - int(m.group(3).split("-")[1]) if "GESAMT_FRAMES" in m.group(3) else int(m.group(3))
        out.append((m.group(1), von, von + dauer))
    return out


def grafik_sichtbar() -> list[bool]:
    """Je Frame: irgendein Pixel der Grafikebene hat Alpha > 0 (signalstats YMAX auf dem Alpha-Kanal, volle Auflösung)."""
    if not YMAX_TXT.exists() or YMAX_TXT.stat().st_mtime < GRAFIK.stat().st_mtime:
        print("Messe Sichtbarkeit der Grafikebene (einmal je Render, ca. 3 min) …")
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(GRAFIK), "-vf",
                        f"alphaextract,format=gray,signalstats,metadata=print:key=lavfi.signalstats.YMAX:file={YMAX_TXT}",
                        "-f", "null", "-"], check=True)
    werte = [float(z.split("=")[1]) for z in YMAX_TXT.read_text().splitlines() if "YMAX=" in z]
    if len(werte) != ENDE:
        raise SystemExit(f"Sichtbarkeitsmessung hat {len(werte)} Frames statt {ENDE}.")
    return [w > 0 for w in werte]


def v4_stuecke(fehler: list[str]) -> list[Item]:
    """Grafikebene ohne tote Bereiche: je Grafik-Element ein Clip, auf die sichtbaren Frames getrimmt (User 15.09.)."""
    sichtbar = grafik_sichtbar()
    elemente = sorted(grafik_elemente(), key=lambda e: e[1])
    gruppen: list[list] = []
    for eid, von, bis in elemente:  # nur echte Überschneidungen zusammenlegen, aneinanderstoßende Elemente bleiben getrennt
        if gruppen and von < gruppen[-1][2]:
            gruppen[-1] = [gruppen[-1][0] + "+" + eid, gruppen[-1][1], max(gruppen[-1][2], bis)]
        else:
            gruppen.append([eid, von, bis])
    stuecke = []
    for eid, von, bis in gruppen:
        frames = [f for f in range(von, min(bis, ENDE)) if sichtbar[f]]
        if frames:
            a, b = frames[0], frames[-1] + 1
            stuecke.append(Item("V4", str(GRAFIK), a, b, a, b, True, eid, "grafik", True))
    in_elementen = {f for it in stuecke for f in range(it.rec_in_f, it.rec_out_f)}
    ausserhalb = [f for f in range(ENDE) if sichtbar[f] and f not in in_elementen]
    if ausserhalb:
        fehler.append(f"Grafik sichtbar außerhalb der Elemente: {len(ausserhalb)} Frames, erster {tc(ausserhalb[0])}")
    return stuecke


def plan(tl: dict, shots: dict) -> tuple[dict, list[str]]:
    anpassen_pruefen()
    fehler: list[str] = []
    items = tl["items"]
    # A1 unverändert
    a1 = [Item("A1", i["clip"], i["src_in_f"], i["src_in_f"] + i["rec_out_f"] - i["rec_in_f"], i["rec_in_f"], i["rec_out_f"],
               True, i["beat_nr"], "oton", False) for i in items if i["track"] == "A1"]
    # V1 mit Änderungen
    v1_raw = [dict(i) for i in items if i["track"] == "V1"]
    je_beat: dict[str, list[dict]] = {}
    for i in v1_raw:
        je_beat.setdefault(i["beat_nr"], []).append(i)
    for beat, idx, feld, delta in V1_AENDERUNGEN:
        stuecke = sorted(je_beat.get(beat, []), key=lambda x: x["rec_in_f"])
        if not -len(stuecke) <= idx < len(stuecke):
            fehler.append(f"V1_AENDERUNGEN: Beat #{beat} hat {len(stuecke)} V1-Stücke — Index {idx} gibt es nicht")
            continue
        it = stuecke[idx]
        if feld == "out":
            it["rec_out_f"] += delta
        else:
            it["rec_in_f"] += delta
            it["src_in_f"] += delta
    v1 = [Item("V1", i["clip"], i["src_in_f"], i["src_in_f"] + i["rec_out_f"] - i["rec_in_f"], i["rec_in_f"], i["rec_out_f"],
               True, i["beat_nr"], "oton", True) for i in sorted(v1_raw, key=lambda x: x["rec_in_f"])]
    for a, b in zip(v1, v1[1:]):
        if b.rec_in_f < a.rec_out_f:
            fehler.append(f"V1 überlappt: #{a.beat_nr} bis {a.rec_out_f} / #{b.beat_nr} ab {b.rec_in_f}")
    if PUNCH_IN["beat"] is not None:
        n_punch = sum(1 for i in v1 if i.beat_nr == PUNCH_IN["beat"])
        if not -n_punch <= PUNCH_IN["index"] < n_punch:
            fehler.append(f"PUNCH_IN: Beat #{PUNCH_IN['beat']} hat {n_punch} V1-Stücke — Index {PUNCH_IN['index']} gibt es nicht")
    # V2 A-Abschnitte
    v2_quelle = [i for i in items if i["track"] == "V2"]
    v2 = []
    for a, b in A_ABSCHNITTE:
        it = next((i for i in v2_quelle if i["rec_in_f"] <= a and b <= i["rec_out_f"]), None)
        if it is None:
            fehler.append(f"V2-Abschnitt {a}–{b}: kein a7-Item deckt ihn")
            continue
        s = it["src_in_f"] + a - it["rec_in_f"]
        v2.append(Item("V2", it["clip"], s, s + b - a, a, b, True, it["beat_nr"], "oton", True))
    # V3 B-Roll
    v3, v3_meta, folge = [], [], []  # folge: Eingabe der Brennweitenregel (TM.brennweitenfolge)
    for eintrag in sorted(BROLL, key=lambda x: x[3]):
        nr, off, n, rec, beat, langsam, *rest = eintrag
        stabil_hand = rest[0] if rest else None
        zoom_hand = rest[1] if len(rest) > 1 else None  # 8. Spalte: erzwungener Zoom, None = Automatik
        s = shots.get(nr)
        if s is None:
            fehler.append(f"S{nr:02d}: Shot fehlt in broll_auswahl.json")
            continue
        faktor = s["clip_fps"] / FPS
        if langsam and s["clip_fps"] < 2 * FPS:
            fehler.append(f"S{nr:02d}: 50 % bei {s['clip_fps']:g}-fps-Quelle — Bilder stünden doppelt (Zeitlupe nur ab {2 * FPS} fps)")
        genutzt = n / 2 if langsam else n  # Timeline-Frames bei 100 % aus der Auswahl
        if off < 0 or off + genutzt > s["dauer_f"] + 1e-9:
            fehler.append(f"S{nr:02d}: Versatz {off} + genutzt {genutzt} > Auswahl {s['dauer_f']} — verlängert!")
        src_in = int(round((s["left_offset_f"] + off) * faktor))
        src_out = src_in + int(round(n * faktor))  # angehängt bei 100 %; SetSpeed 50 halbiert den Quellbereich
        quelle_genutzt = int(round(n if langsam else n * faktor))
        tele_rec = TM.finden(TELE, s["datei"])
        bereich = TM.genutzter_quellbereich_s(src_in, n, s["clip_fps"], langsam, FPS)
        vorschlag, grund = TM.stabil_vorschlag(*bereich, tele_rec, TCFG, path=s["datei"])
        stabil = vorschlag if stabil_hand is None else bool(stabil_hand)
        if stabil_hand is not None and stabil != vorschlag:
            grund += " — von Hand überstimmt"
        if stabil and "_stabilized" in Path(str(s["datei"])).name.lower():  # User-Regel 18.09.: Avata nur als _stabilized
            fehler.append(f"S{nr:02d}: Spalte 7 True bei _stabilized-Datei — Avata nie in Resolve stabilisieren")
        v3.append(Item("V3", s["datei"], src_in, src_out, rec, rec + n, True, beat, "broll", True))
        auswahl_50p = [int(round(s["left_offset_f"] * faktor)), int(round((s["left_offset_f"] + s["dauer_f"]) * faktor))]
        v3_meta.append({"shot": nr, "clip": s["clip"], "rec_in_f": rec, "dauer_f": n, "langsam": langsam, "src_in_f": src_in,
                        "quelle_genutzt_50p": quelle_genutzt, "auswahl_50p": auswahl_50p,
                        "stabil": stabil, "stabil_grund": grund,
                        "roll_grad": (tele_rec or {}).get("roll_grad"),
                        "zoom_hinweise": TM.zoom_hinweise(f"S{nr:02d}", tele_rec, *bereich, cfg=TCFG,
                                                          tempo_faktor=0.5 if langsam else 1.0)})
        # Brennweite am Schnitt: Ende des genutzten Quellbereichs (bei 50 % halb so lang) bzw. sein Anfang
        folge.append({"id": f"S{nr:02d}", "rec_in": rec, "rec_out": rec + n, "zoom_erzwungen": zoom_hand,
                      "kb_anfang": TM.kb_am(tele_rec, bereich[0], seite="anfang"),
                      "kb_ende": TM.kb_am(tele_rec, bereich[1], seite="ende")})
    # Brennweitenregel (Spec 2026-09-21): nie zweimal dieselbe KB-Brennweite direkt hintereinander, sonst digitaler Zoom
    for m, f, z in zip(v3_meta, folge, TM.brennweitenfolge(folge, TCFG)):
        m.update(zoom=z["zoom"], zoom_hinweis=z["hinweis"], kb_anfang=f["kb_anfang"], kb_ende=f["kb_ende"])
        if z["fehler"]:
            fehler.append(z["fehler"])
    for a, b in zip(v3, v3[1:]):
        if b.rec_in_f < a.rec_out_f:
            fehler.append(f"V3 überlappt bei {b.rec_in_f}")
    v4 = [Item("V4", str(GRAFIK), 0, ENDE, 0, ENDE, True, "grafik", "grafik", True)]
    musik = [Item(sp, str(d), si, si + ro - ri, ri, ro, True, "musik", "musik", False) for sp, d, si, ri, ro, *_ in MUSIK_PLAN]
    p = {"A1": a1, "V1": v1, "V2": v2, "V3": v3, "V4": v4, "musik": musik, "v3_meta": v3_meta}
    # Schwarzframes: Lücken auf V1–V3 müssen von der Grafik deckend gefüllt sein (gemessen, nicht angenommen)
    amin = alpha_min()
    p["gehalten"] = bild_halten(p, amin, fehler)
    p["luecken"] = luecken([p["V1"], p["V2"], p["V3"]])
    p["schwarz"] = [f for a, b in p["luecken"] for f in range(a, b) if amin[f] < DECKEND_AB]
    if p["schwarz"]:
        fehler.append(f"{len(p['schwarz'])} Frames ohne Bild und ohne deckende Grafik, erster {tc(p['schwarz'][0])}")
    for spur in ("V1", "V2"):
        for a, b in zip(p[spur], p[spur][1:]):
            if b.rec_in_f < a.rec_out_f:
                fehler.append(f"{spur} überlappt nach Bild-Halten bei {tc(b.rec_in_f)}")
    # Resolve-Aufbau für manuelles Feintuning (User 15.09.): a7 durchgehend (nur A-Abschnitte aktiv), Grafik je Element ein Clip
    p["V2_voll"] = v2_voll(p, items, fehler)
    p["V4"] = v4_stuecke(fehler)
    return p, fehler


def tc(f: int) -> str:
    return f"{f // FPS // 60:02d}:{f // FPS % 60:02d}:{f % FPS:02d}"


def bericht(p: dict) -> None:
    aus = [i for i in p["V2_voll"] if not i.enabled]
    print(f"A1 {len(p['A1'])} · V1 {len(p['V1'])} · V2 {len(p['V2_voll'])} ({len(aus)} deaktiviert) · V3 {len(p['V3'])} "
          f"({sum(m['langsam'] for m in p['v3_meta'])} × 50 %) · V4 {len(p['V4'])} Grafik-Clips · Musik {len(p['musik'])}")
    a_frames = sum(i.rec_out_f - i.rec_in_f for i in p["V2"])
    print(f"a7-Perspektive sichtbar: {a_frames / FPS:.1f} s in {len(p['V2'])} Abschnitten; a7 liegt unter {sum(i.rec_out_f - i.rec_in_f for i in p['V2_voll']) / FPS:.1f} s")
    tot = ENDE - sum(i.rec_out_f - i.rec_in_f for i in p["V4"])
    print(f"Grafikebene: {len(p['V4'])} Clips, {tot / FPS:.1f} s tote Bereiche herausgeschnitten")
    for zeile in p["gehalten"]:
        print("  Bild gehalten:", zeile)
    frei = sum(b - a for a, b in p["luecken"])
    print(f"Ohne Bild auf V1–V3: {len(p['luecken'])} Lücken / {frei} Frames — davon ohne deckende Grafik: {len(p['schwarz'])}")
    print(f"Stabilisierung, Brennweite und Zoom ({len(TELE)} Clips in telemetrie.json):")
    for m in p["v3_meta"]:
        roll = m.get("roll_grad")
        schief = f"  schief {abs(roll):.1f}°".replace(".", ",") if roll is not None and abs(roll) > 2.0 else ""
        kb = "KB –" if m.get("kb_anfang") is None else f"KB {m['kb_anfang']:g} → {m['kb_ende']:g} mm".replace(".", ",")
        zoom = f"  Zoom {m['zoom']:g}×".replace(".", ",") if m.get("zoom", 1.0) != 1.0 else ""
        print(f"  S{m['shot']:02d} {'stabilisieren' if m['stabil'] else 'lassen       '}  {m['stabil_grund']}{schief}"
              f"  {kb}{zoom}")
    # ohne telemetrie.json eine Zeile; sonst alte oder mit anderen Schwellen gemessene Datensätze der genutzten Clips
    hinweise = (TM.telemetrie_hinweise([TM.finden(TELE, it.clip) for it in p["V3"]], TCFG) if TELE
                else [TM.OHNE_TELEMETRIE])
    for m in p["v3_meta"]:
        hinweise += m.get("zoom_hinweise", []) + ([m["zoom_hinweis"]] if m.get("zoom_hinweis") else [])
    for h in hinweise:
        print(f"  Hinweis: {h}")


def bauen(p: dict) -> dict:
    anpassen_pruefen(fuer_bau=True)
    probe_pfad = AC / "probe.json"
    if not probe_pfad.exists():
        raise SystemExit(f"{probe_pfad} fehlt — erst die Resolve-Probe der Charge ausführen (tools/autocut/scripts/resolve_probe.py).")
    probe = json.loads(probe_pfad.read_text())
    session = RA.ResolveSession(RA.connect(), probe=probe)
    if session.project_name != PROJEKT:
        raise SystemExit(f"Offenes Projekt '{session.project_name}' ≠ Freigabe '{PROJEKT}' — nichts geschrieben.")
    if not GRAFIK.exists():
        raise SystemExit(f"Grafikebene fehlt: {GRAFIK}")
    r, proj, mp = session.resolve, session.project, session.media_pool
    user_folder = mp.GetCurrentFolder()
    name = f"AutoCut {VIDEO_KURZ} {dt.datetime.now():%Y-%m-%d %H%M} Feinschnitt"
    out: dict = {"projekt": session.project_name, "timeline": name,
                 "bin_vorher": user_folder.GetName() if user_folder else None,
                 "timeline_vorher": session.user_timeline.GetName() if session.user_timeline else None}
    try:
        folder = session.ensure_bin(["AutoCut", VIDEO_KURZ])
        pfade = sorted({it.clip for k in ("A1", "V1", "V2_voll", "V3", "V4", "musik") for it in p[k]})
        media = session.import_media(pfade, folder)
        tl = session.create_timeline(name, float(FPS), BREITE, HOEHE, "01:00:00:00")
        # Alle Tonspuren gleich beim Anlegen (auch SFX): per AddTrack nachträglich angelegte Spuren haben keinen Bus-Ausgang (15.09.)
        RA.TRACK_INDEX.update({"A4": 4, "A5": 5})
        session.ensure_tracks(tl, 4, 5, {"V1": "FX3", "V2": "a7IV", "V3": "B-Roll", "V4": "Grafik", "A1": "FX3 Ton", "A2": "Musik 1",
                                         "A3": "Musik 2", "A4": "SFX 1", "A5": "SFX 2"})
        start = int(tl.GetStartFrame())
        for key in ("V1", "A1", "V2_voll", "V3", "V4"):  # V2 durchgehend, nicht sichtbare a7-Stücke deaktiviert
            session.append_items(tl, p[key], media, start)
        # Musik je Spur getrennt anhängen (A2 und A3 überlappen sich absichtlich)
        for spur in ("A2", "A3"):
            session.append_items(tl, [i for i in p["musik"] if i.track == spur], media, start)
        # --- Nachbearbeitung ---
        by_start = lambda kind, idx: {int(x.GetStart()) - start: x for x in (tl.GetItemListInTrack(kind, idx) or [])}
        v3_items = by_start("video", 3)
        v3_plan = {it.rec_in_f: it for it in p["V3"]}  # Quelldatei je Shot, gleicher Schlüssel wie v3_items
        speed_ok, stab, gyroflow_gesetzt, gyroflow_abweichungen = 0, {}, 0, []
        # Gyroflow-Sidecars (Spec 2026-09-22, scripts/autocut_gyroflow.py). Schlüssel ist GF.norm_pfad — der volle
        # aufgelöste Pfad in NFC, nicht der Clip-Stamm: Kartennummern setzen pro Karte/Dreh neu auf, zwei Quelldateien
        # können denselben Stamm tragen, und macOS liefert Umlaute in Pfaden teils in NFD (wie in gyroflow_bericht.py
        # und broll_auswahl.py). Fehlerhafte oder fehlende Einträge bleiben außen vor.
        # Die Datei ist optional wie telemetrie.json (TM.laden): kaputt/unlesbar darf hier nicht raisen — wir sind
        # schon mitten im Bau (nach append_items), ein Absturz hier liefe nie in die Stabilisierungsschleife unten
        # und ließe jeden V3-Shot ohne Stabilize() und ohne Gyroflow zurück.
        # Wert ist der ganze Datensatz, nicht nur der Sidecar-Pfad: haltung steht dort schon drin (clip_export
        # schreibt sie), und ein zweiter Join über TM.finden würde anders normalisieren — exakter Stringvergleich,
        # dann Rückfall auf Eindeutigkeit des Dateinamens. Der greift bei zwei Karten mit FX3_0001.MP4 ins Leere,
        # und der Shot bekäme still „stativ" (Smoothness 0,2 statt 0,7) — was laut Befund 1 Punkt 5 auch das
        # Sidecar überstimmt: eine Handkamera mit Stativ-Glättung, gemeldet als Erfolg.
        GYRO, gyro_geladen = {}, False
        gf_pfad = AC / "gyroflow.json"
        if gf_pfad.exists():
            try:
                gyro_clips = json.loads(gf_pfad.read_text(encoding="utf-8"))["clips"]
                if not isinstance(gyro_clips, list):
                    raise TypeError(f"'clips' ist {type(gyro_clips).__name__}, keine Liste")
                GYRO = {GF.norm_pfad(c["path"]): c
                        for c in gyro_clips if isinstance(c, dict) and c.get("sidecar") and not c.get("fehler")}
                gyro_geladen = True
            except (json.JSONDecodeError, UnicodeDecodeError, OSError, KeyError, TypeError) as e:
                grund = f"gyroflow.json kaputt/unlesbar ({type(e).__name__}: {e}) — alle Shots bleiben beim Stabilize()-Weg"
                gyroflow_abweichungen.append({"shot": None, "grund": grund})
                print(f"  Gyroflow: {grund}", flush=True)
        for m in p["v3_meta"]:
            x = v3_items[m["rec_in_f"]]
            if m["langsam"]:  # 50p-Quelle bei 50 %: jedes Quellbild genau einmal, daher „Nearest" statt Frame-Blending
                RA._safe(x.SetProperties, None, {"RetimeProcess": r.RETIME_NEAREST})
                # Standard (15.09.): Zeitlupe 50 %, Timeline-Dauer bleibt, der genutzte Quellbereich halbiert sich
                speed_ok += int(bool(RA._safe(x.SetSpeed, False, {"Percentage": 50.0, "RippleTimeline": False})))
        out["speed_gesetzt"] = speed_ok
        # Stabilisieren: Gyroflow ersetzt Stabilize() für B-Roll-Shots mit Sidecar — Spec 2026-09-22 will alle
        # genutzten Shots, nicht nur die mit stabil-Flag (auch ruhige Aufnahmen profitieren von der
        # Rolling-Shutter-Korrektur). Nur ohne nutzbaren Sidecar gilt weiter der bisherige, telemetriebasierte Weg
        # (Analyse über den tatsächlich genutzten Quellbereich).
        for n_, m in enumerate(p["v3_meta"], 1):
            t0, shot = dt.datetime.now(), f"S{m['shot']:02d}"
            x = v3_items[m["rec_in_f"]]
            pfad = v3_plan[m["rec_in_f"]].clip
            eintrag = GYRO.get(GF.norm_pfad(pfad))
            sidecar = (eintrag or {}).get("sidecar")
            # Sidecars liegen bei den Medien und laufen nicht über studio_abgleich.sh — nach einem NAS-Umzug und
            # Relink kann die Datei fehlen. SetInput nähme den toten Pfad klaglos an, das continue unten überspränge
            # Stabilize(), und der Shot wäre auf KEINEM der beiden Wege stabilisiert. Darum hier prüfen.
            if sidecar and not Path(sidecar).is_file():
                gyroflow_abweichungen.append({"shot": m["shot"], "grund": f"Sidecar fehlt: {sidecar}"})
                print(f"  Gyroflow {n_}/{len(p['v3_meta'])} {shot}: Sidecar fehlt ({sidecar}) — "
                      f"zurück auf den Stabilize()-Weg", flush=True)
                sidecar = None
            elif sidecar is None and gyro_geladen:
                # Häufigste echte Ursache: veraltete gyroflow.json — BROLL geändert, --bauen ohne neuen Lauf von
                # autocut_gyroflow.py. Dann nähmen genau die neuen Shots still den alten Weg. Zweite Ursache: der
                # Clip steht in gyroflow.json unter „uebersprungen" (keine Gyrospur, Avata-Export) — dort nachsehen.
                gyroflow_abweichungen.append({"shot": m["shot"], "grund": "kein Sidecar"})
            if sidecar:
                comp = RA._safe(x.AddFusionComp, None)
                werkzeug = RA._safe(comp.AddTool, None, GYRO_TOOL_ID) if comp else None
                if werkzeug is None:
                    gyroflow_abweichungen.append({"shot": m["shot"], "grund": "OFX-Tool nicht verfügbar"})
                    stab[shot] = bool(RA._safe(x.Stabilize, False))          # Rückfall auf den bisherigen Weg
                    print(f"  Gyroflow {n_}/{len(p['v3_meta'])} {shot}: OFX-Tool nicht verfügbar — "
                          f"Stabilize() als Rückfall ({stab[shot]})", flush=True)
                else:
                    # Haltung aus demselben Datensatz, der auch den Sidecar-Pfad liefert (clip_export schreibt sie
                    # aus der Telemetrie, wie preset_fuer); ohne Wert die vorsichtigste Stufe.
                    haltung = eintrag.get("haltung") or GF.HALTUNG_VORSICHTIG
                    # .get() statt harter Klammer: die Charge kann ihre glaettung zwischen Sidecar-Lauf und Bau
                    # geändert haben, und dieser Block darf nicht raisen (siehe Kommentar über GYRO).
                    glaettung = (CFG.get("gyroflow") or {}).get("glaettung") or {}
                    if haltung not in glaettung:
                        gyroflow_abweichungen.append(
                            {"shot": m["shot"], "grund": f"Haltung {haltung!r} fehlt in cfg.gyroflow.glaettung"})
                        haltung = GF.HALTUNG_VORSICHTIG
                    RA._safe(werkzeug.SetInput, False, GYRO_PARAM_PROJEKT, sidecar)
                    # Smoothness/FOV explizit setzen: die OFX-Parameter überschreiben sonst das Sidecar (Befund 1, Punkt 5).
                    RA._safe(werkzeug.SetInput, False, "Smoothness", float(glaettung.get(haltung, 0.2)))
                    RA._safe(werkzeug.SetInput, False, "FOV", 1.0)
                    video_speed = 50.0 if (m["langsam"] and GYRO_BEI_ZEITLUPE) else 100.0
                    RA._safe(werkzeug.SetInput, False, "VideoSpeed", video_speed)
                    # Set-then-Readback wie bei zoom_abweichungen/speed_gesetzt: SetInput meldet auch dann Erfolg,
                    # wenn der Parameter nicht ankam. Der Readback von gyrodata liefert den gesetzten Pfad
                    # zurück (Befund 1, Punkt 2) — gezählt wird nur, was wirklich steht.
                    ist = RA._safe(werkzeug.GetInput, None, GYRO_PARAM_PROJEKT)
                    if isinstance(ist, str) and ist and GF.norm_pfad(ist) == GF.norm_pfad(sidecar):
                        gyroflow_gesetzt += 1
                        stab[shot] = None  # Stabilize() bewusst nicht gerufen — Gyroflow ersetzt es für diesen Shot
                        print(f"  Gyroflow {n_}/{len(p['v3_meta'])} {shot}: Haltung {haltung}, "
                              f"VideoSpeed {video_speed:g} ({(dt.datetime.now() - t0).total_seconds():.1f} s)",
                              flush=True)
                    else:
                        gyroflow_abweichungen.append({"shot": m["shot"], "grund": f"gyrodata nicht gesetzt (ist: {ist!r})"})
                        stab[shot] = bool(RA._safe(x.Stabilize, False))      # Rückfall auf den bisherigen Weg
                        print(f"  Gyroflow {n_}/{len(p['v3_meta'])} {shot}: gyrodata nicht gesetzt — "
                              f"Stabilize() als Rückfall ({stab[shot]})", flush=True)
                continue
            if not m["stabil"]:
                stab[shot] = None
                print(f"  Stabilisierung {n_}/{len(p['v3_meta'])} {shot}: übersprungen ({m['stabil_grund']})", flush=True)
                continue
            stab[shot] = bool(RA._safe(x.Stabilize, False))
            print(f"  Stabilisiert {n_}/{len(p['v3_meta'])} {shot}: {stab[shot]} ({(dt.datetime.now() - t0).total_seconds():.1f} s)", flush=True)
        out["stabilisiert"] = stab
        out["gyroflow_gesetzt"] = gyroflow_gesetzt
        out["gyroflow_abweichungen"] = gyroflow_abweichungen
        # Digitaler Zoom der Brennweitenregel (Spec 2026-09-21): auf die Bildmitte, Pan/Tilt bleiben 0
        zoom_ok = {}
        for m in p["v3_meta"]:
            if m["zoom"] == 1.0:
                continue
            x = v3_items[m["rec_in_f"]]
            gesetzt = [bool(RA._safe(x.SetProperty, False, k, float(m["zoom"]))) for k in ("ZoomX", "ZoomY")]
            zoom_ok[f"S{m['shot']:02d}"] = all(gesetzt)
        out["zoom_gesetzt"] = zoom_ok
        if PUNCH_IN["beat"] is None:
            out["punch_in"] = None  # kein Punch-in geplant
        else:
            v1_items = sorted(tl.GetItemListInTrack("video", 1) or [], key=lambda x: x.GetStart())
            cta = [i for i in p["V1"] if i.beat_nr == PUNCH_IN["beat"]]
            ziel_start = sorted(cta, key=lambda i: i.rec_in_f)[PUNCH_IN["index"]].rec_in_f
            punch = next(x for x in v1_items if int(x.GetStart()) - start == ziel_start)
            out["punch_in"] = bool(RA._safe(punch.SetProperties, False, PUNCH_IN["props"]))
        a1_items = tl.GetItemListInTrack("audio", 1) or []
        # Standard (15.09.): True Peak −3 dBTP je FX3-Clip (unabhängig je Clip)
        opts = {"normalizationMode": "True Peak", "targetLevel": -3.0, "setLevelMode": r.NORMALIZE_AUDIO_SET_LEVEL_INDEPENDENT}
        out["normalisiert"] = bool(tl.NormalizeAudioLevel(a1_items, opts))
        # Standard (15.09.): Voice Isolation auf A1, Stärke 50
        out["voice_isolation"] = bool(tl.SetVoiceIsolationState(1, {"isEnabled": True, "amount": 50}))
        musik_ok = []
        for spur_idx, spur in ((2, "A2"), (3, "A3")):
            spur_items = by_start("audio", spur_idx)
            for sp, d, si, ri, ro, db, fi, fo in MUSIK_PLAN:
                if sp != spur:
                    continue
                x = spur_items[ri]
                v = bool(RA._safe(x.SetProperties, False, {"AudioVolume": db}))
                f = bool(RA._safe(x.SetFades, False, {"FadeIn": fi, "FadeOut": fo}))
                musik_ok.append((sp, ri, v, f))
        out["musik_pegel_fades"] = musik_ok
        session.add_markers(tl, [MarkerSpec(f, n, note, c, d) for f, c, n, note, d in MARKER], start)
    finally:
        session.restore_user_timeline()
        if user_folder is not None:
            mp.SetCurrentFolder(user_folder)
    out["gespeichert"] = session.save_project()
    # --- Readback ---
    tl = session.find_timeline(name)
    start = int(tl.GetStartFrame())
    rb = {}
    for kind, n in (("video", 4), ("audio", 3)):
        for idx in range(1, n + 1):
            rb[f"{kind[0].upper()}{idx}"] = [(int(x.GetStart()) - start, int(x.GetDuration()), int(x.GetLeftOffset())) for x in (tl.GetItemListInTrack(kind, idx) or [])]
    out["spuren"] = {k: len(v) for k, v in rb.items()}
    soll = {k: sorted((i.rec_in_f, i.rec_out_f - i.rec_in_f) for i in p[k]) for k in ("V1", "A1", "V3", "V4")}
    soll["V2"] = sorted((i.rec_in_f, i.rec_out_f - i.rec_in_f) for i in p["V2_voll"])
    out["v2_aktiv_identisch"] = sorted(int(x.GetStart()) - start for x in (tl.GetItemListInTrack("video", 2) or []) if x.GetClipEnabled()) == \
        sorted(i.rec_in_f for i in p["V2_voll"] if i.enabled)
    soll["A2"] = sorted((i.rec_in_f, i.rec_out_f - i.rec_in_f) for i in p["musik"] if i.track == "A2")
    soll["A3"] = sorted((i.rec_in_f, i.rec_out_f - i.rec_in_f) for i in p["musik"] if i.track == "A3")
    out["positionen_identisch"] = {k: sorted((a, d) for a, d, _ in rb[k]) == v for k, v in soll.items()}
    # V3: Tempo und genutzter Quellbereich (Left-Offset in 25er-Einheiten, Quelle 50p)
    v3_rb = []
    for x in sorted(tl.GetItemListInTrack("video", 3) or [], key=lambda y: y.GetStart()):
        sp = RA._safe(x.GetSpeed, {}) or {}
        v3_rb.append({"start": int(x.GetStart()) - start, "dauer": int(x.GetDuration()), "left": int(x.GetLeftOffset()),
                      "src": [RA._safe(x.GetSourceStartFrame, None), RA._safe(x.GetSourceEndFrame, None)], "speed": sp.get("Percentage")})
    out["v3"] = v3_rb
    # Readback Zoom (Spec 2026-09-21): ZoomX je V3-Item gegen den Plan (1.0 = kein digitaler Zoom), gepaart über den
    # Record-In wie in 3a (fehlt ein Item, verrutscht so kein Vergleich) → Liste {shot, soll, ist}
    zoom_ist = {int(x.GetStart()) - start: RA._safe(x.GetProperty, None, "ZoomX")
                for x in (tl.GetItemListInTrack("video", 3) or [])}
    out["zoom_abweichungen"] = TM.zoom_abweichungen(p["v3_meta"], zoom_ist)
    ausserhalb = []
    for m, x in zip(sorted(p["v3_meta"], key=lambda z: z["rec_in_f"]), v3_rb):
        s0, s1 = x["src"]
        if s0 is None or s1 is None:
            continue
        a, b = m["auswahl_50p"]
        if s0 < a - 2 or s1 > b + 2:
            ausserhalb.append({"shot": m["shot"], "src": [s0, s1], "auswahl": [a, b], "speed": x["speed"]})
    out["v3_ausserhalb_auswahl"] = ausserhalb
    out["normalisierung_a1_db"] = [RA._safe(x.GetProperty, None, "AudioVolume") for x in (tl.GetItemListInTrack("audio", 1) or [])]
    out["voice_isolation_state"] = RA._safe(tl.GetVoiceIsolationState, None, 1)
    out["musik_readback"] = [(int(x.GetStart()) - start, RA._safe(x.GetProperty, None, "AudioVolume"), RA._safe(x.GetFades, None))
                             for idx in (2, 3) for x in (tl.GetItemListInTrack("audio", idx) or [])]
    out["marker"] = len(tl.GetMarkers() or {})
    out["timeline_ende"] = int(tl.GetEndFrame()) - start
    cur = proj.GetCurrentTimeline()
    out["aktive_timeline"] = cur.GetName() if cur else None
    out["aktiver_bin"] = mp.GetCurrentFolder().GetName() if mp.GetCurrentFolder() else None
    out["warnungen"] = session.warnings
    return out


if __name__ == "__main__":
    tl_json, shots = lade()
    p, fehler = plan(tl_json, shots)
    bericht(p)
    if fehler:
        print("FEHLER:\n  " + "\n  ".join(fehler))
        sys.exit(1)
    if "--bauen" in sys.argv:
        e = bauen(p)
        (AC / "feinschnitt.json").write_text(json.dumps({**e, "plan_v3": p["v3_meta"]}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        print(json.dumps({k: v for k, v in e.items() if k not in ("v3", "normalisierung_a1_db", "musik_readback")}, ensure_ascii=False, indent=1, default=str))
    else:
        # Gyroflow-Sidecars (Spec 2026-09-22): die im Feinschnitt genutzten B-Roll-Quelldateien für
        # scripts/autocut_gyroflow.py. Nur im Probelauf liegen BROLL (was benutzt wird) und die per broll_auswahl.json
        # aufgelösten shots (welche Datei das ist) zusammen vor. Auflösung wie oben in plan() (shots.get(nr), Zeile 369);
        # tempo50 ist die 6. BROLL-Spalte "50 %" (s. Kommentar über BROLL) — nicht geraten, sondern dort nachgelesen.
        gyro_clips, gesehen = [], set()
        for zeile in BROLL:
            s = shots.get(zeile[0])
            if s is None:
                continue  # fehlender Shot wäre oben schon als FEHLER gemeldet, dieser Zweig liefe dann nicht
            datei = s["datei"]
            if datei in gesehen:
                continue
            gesehen.add(datei)
            gyro_clips.append({"datei": datei, "tempo50": bool(zeile[5])})
        ziel = AC / "gyroflow_clips.json"
        ziel.write_text(json.dumps(gyro_clips, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{len(gyro_clips)} B-Roll-Quelldateien für Gyroflow → {ziel}")
        print('  weiter mit: tools/autocut/venv/bin/python tools/autocut/scripts/autocut_gyroflow.py "<Charge>"')
