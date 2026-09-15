"""Feinschnitt Taxodia als neue Resolve-Timeline bauen (15.09.2026).

Aufruf: tools/autocut/venv/bin/python _intern/feinschnitt_bauen.py            → Probelauf (Plan, Prüfungen, Schwarzframe-Rechnung)
        tools/autocut/venv/bin/python _intern/feinschnitt_bauen.py --bauen    → Timeline in „Taxodia 09.26" bauen + Readback

User-Wünsche 15.09.: keine Schwarzframes (alles mit Grafik oder B-Roll gedeckt), mehr Grafiken inkl. Vollbild (Grafikebene v2),
A/B-Perspektiven wechseln, hier und da L-/J-Cuts, Musik (3 Tracks, Wechsel pro Thema, nahtlose Übergänge),
Audio-Normalisierung + Voice Isolation, B-Roll stabilisieren und ggf. 50 % Tempo. Grading folgt in eigenem Schritt.

Aufbau (Frames = Timeline-Frames, 25 fps; O-Ton-Positionen wie „AutoCut video-1-taxodia-weg 2026-09-15 0941 (roh)"):
  V1 FX3 (Bild, mit Bildverlängerungen für nahtlose Übergänge und J-Cut #20→#21, Punch-in im CTA #22)
  V2 a7IV nur in den A-Abschnitten (Perspektivwechsel)
  V3 B-Roll aus der User-Auswahl (nur deren Bereiche; Zeitlupe 50 % bei Händen/Details/Kamerafahrten, nie bei Sprechenden)
  V4 Grafikebene v2 (ProRes 4444 Alpha)
  A1 FX3-Ton (True Peak −3 dBTP je Clip, Voice Isolation), A2/A3 Musik mit Überblendungen
Nur neue Objekte: neue Timeline, Importe in den eigenen Bin AutoCut/video-1-taxodia-weg. Timeline und Bin des Users werden
wiederhergestellt. Schreibt _intern/autocut/feinschnitt.json.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/src")
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.timeline_model import Item, MarkerSpec  # noqa: E402

RA.TRACK_INDEX["A3"] = 3  # dritte Tonspur für Musik-Überblendungen (nur in diesem Skript)

CH = Path(__file__).resolve().parent.parent
AC = CH / "_intern" / "autocut"
PROJEKT = "Taxodia 09.26"
FPS = 25
ENDE = 6845
MUSIK = CH / "Material" / "Musik"
GRAFIK = CH / "Ergebnisse" / "Renders" / "taxodia-grafikebene-v2.mov"
CAMPAGNA = MUSIK / "Campagna - Wherever You Want to Go.wav"
T2050 = MUSIK / "2050 - Interpretation of a Dream.wav"
IKOLIKS = MUSIK / "Ikoliks - New Day - No Backing Vocals.wav"

# --- V1: Bildverlängerungen (Beat, Index im Beat, Feld, Delta) ---------------------------------------------------
V1_AENDERUNGEN = [
    ("6", -1, "out", +22),   # Ludwig hält nach „… jemand zu finden." (Quelle still bis „Deshalb" +1,2 s) → Pause gedeckt
    ("7", 0, "in", -3),      # Hein 3 Frames früher (still nach „angestellt.")
    ("20", 0, "out", +37),   # Flammann hält nach „… fortbilden zu lassen." (Interviewer-„Okay" erst +1 s) → J-Cut in Heins Note
    ("21", 0, "in", +12),    # Heins Bild 12 Frames nach seinem Ton
]
PUNCH_IN = {"beat": "22", "index": 2, "props": {"ZoomX": 1.12, "ZoomY": 1.12, "Pan": -200.0}}

# --- V2: Abschnitte mit a7-Perspektive (A); sonst FX3 (B) ---------------------------------------------------------
# (3768, 3831) gestrichen 15.09.: Karte „Kosten" (bis 3790) lag in der a7-Framing 16 px (1080p) unter Ludwigs Kinn.
A_ABSCHNITTE = [
    (0, 60), (258, 345), (693, 760), (1331, 1424), (2118, 2223), (2319, 2500), (2812, 3005),
    (4050, 4162), (4555, 4700), (5396, 5454), (5500, 5705), (5920, 6007),
]

# --- V3: B-Roll (Shot aus broll_auswahl.json, Versatz im Shot [Timeline-Frames bei 100 %], Länge, Record-In, Beat, 50 %) --
BROLL = [
    (10, 27, 54, 345, "4", True), (11, 8, 32, 399, "4", True), (12, 34, 39, 431, "4", True),
    (26, 20, 88, 760, "6", True),
    (4, 20, 75, 1128, "7", True), (3, 10, 46, 1203, "7", True), (8, 0, 82, 1249, "7", True),
    (13, 30, 44, 1424, "8", True), (14, 0, 69, 1468, "8", True),
    (21, 0, 136, 1982, "9", False),
    (5, 8, 34, 2223, "10", True), (6, 10, 62, 2257, "10", True),
    (1, 10, 40, 2638, "11", True), (7, 20, 78, 2678, "11", True), (2, 14, 56, 2756, "11", True),
    (23, 30, 114, 3108, "12", True),
    (15, 0, 62, 3706, "13", False),
    (27, 12, 51, 3890, "14", True), (22, 12, 49, 4001, "15", True),
    (9, 0, 75, 4162, "15", False), (17, 0, 100, 4237, "16", False), (18, 30, 134, 4337, "16", True),
    (29, 0, 84, 4471, "16", False), (19, 20, 77, 4700, "16", True), (20, 0, 57, 4777, "16", False),
    (30, 0, 50, 4906, "17", False), (16, 0, 119, 4956, "18", False),
    (25, 0, 67, 5208, "19", False), (28, 0, 58, 5275, "19", False), (24, 85, 63, 5333, "19", True),
]

# --- Schwarzframe-Prüfung gegen die gemessene Deckkraft der Grafikebene -----------------------------------------------
# Vollbild-Grafiken sind beim Wipe-in/Iris-out 3–10 Frames nicht deckend (Messung 15.09.: 51 Frames ohne Bild darunter).
# Wo V1–V3 leer sind, muss die Grafik deckend sein; Wipe-Ränder werden durch Halten des O-Ton-Bilds (V1/V2) gedeckt.
ALPHA_JSON = AC.parent / "grafik" / "alpha_v2.json"
DECKEND_AB = 250  # kleinster Alpha-Wert im 192×108-Raster (Fläche gemittelt)
YMAX_TXT = AC.parent / "grafik" / "alpha_v2_ymax.txt"
GRAFIK_TSX = Path("/Users/jansantos/NIRO Studio/tools/motion/src/clients/taxodia/projects/erklaervideo/Grafikebene.tsx")

# --- Musik (Spur, Datei, Quell-In [Frames], Record-In, Record-Out, Pegel dB, Fade-In, Fade-Out) ---------------------
# Campagna (Einstieg + Problem, Einsatz unter #2, Anhebung zum Titel) → 2050 ab Blende „Die Online-Steuerfachschule"
# → Ikoliks ab Blende „Online lernen", Sprung auf den Aufbau (Quelle 103,59 s) zur Blende „Das Ergebnis",
# Höhepunkt auf Heins Note, zurückgenommen unter den CTAs, Ende mit der Endcard. Übergänge auf Taktgrenzen, 1 s Überblendung.
# Pegel nach Offline-Messung 15.09. (musik/mischung_pruefen.py): Musik unter Sprache im Median ~13,5 LU leiser als die Sprache,
# Titel und Endcard ohne Sprache auf ca. −18 LUFS kurzzeit.
# Ikoliks-Sprung beat-genau per Onset-Korrelation: Quelle 87,88 s → 103,48 s = exakt 8 Takte (Rest-Versatz −10 ms);
# die beiden Folge-Items rücken um dieselben 3 Frames mit, damit die überlappenden Kopien sample-gleich bleiben.
MUSIK_PLAN = [
    ("A2", CAMPAGNA, 0, 107, 357, -18.8, 25, 12),
    ("A3", CAMPAGNA, 238, 345, 482, -7.8, 12, 12),
    ("A2", CAMPAGNA, 363, 470, 1690, -22.4, 12, 26),
    ("A3", T2050, 0, 1657, 3857, -24.7, 26, 26),
    ("A2", IKOLIKS, 524, 3831, 5516, -26.2, 26, 12),
    ("A3", IKOLIKS, 2587, 5504, 6019, -23.7, 12, 12),
    ("A2", IKOLIKS, 3090, 6007, 6657, -25.3, 12, 12),
    ("A3", IKOLIKS, 3728, 6645, ENDE, -11.3, 12, 50),
]

MARKER = [
    (4337, "Red", "BLUR Monitor C0255", "Heins echter Kursplan: Name, URL, Lesezeichen, „Dozentin: Heike Becker“ blurren.", 134),
    (3108, "Yellow", "Prüfen: Name auf Laptop (C0261)", "Dozentenprofil „Karin Thomas“ lesbar — mit Taxodia klären oder blurren.", 114),
    (4001, "Yellow", "Prüfen: Name auf Laptop (C0260)", "Dozentenprofil „Karin Thomas“ lesbar — mit Taxodia klären oder blurren.", 49),
    (1664, "Purple", "Grafik: Blende Taxodia", "", 1), (3222, "Purple", "Grafik: Taxodia-Weg", "", 1),
    (552, "Purple", "Grafik: Karte Ilshofen", "", 1), (1862, "Purple", "Grafik: Karte Visselhövede–Ilshofen", "", 1),
    (5504, "Green", "Musik: Sprung auf Aufbau (Ikoliks)", "Gegenhören: Taktgrenze 87,99 s → 103,59 s", 1),
    (1657, "Green", "Musik: Wechsel Campagna → 2050", "Überblendung 1657–1690", 1),
    (3831, "Green", "Musik: Wechsel 2050 → Ikoliks", "Überblendung 3831–3857", 1),
]


def lade():
    tl = json.loads((AC / "timeline.json").read_text())
    shots = {s["nr"]: s for s in json.loads((AC / "broll_auswahl.json").read_text())["shots"]}
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
            continue  # CTA #22 hat keine a7
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
    """(id, von, bis) aller Einträge der Remotion-TIMELINE (Grafikebene.tsx)."""
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
        it = sorted(je_beat[beat], key=lambda x: x["rec_in_f"])[idx]
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
    v3, v3_meta = [], []
    for nr, off, n, rec, beat, langsam in sorted(BROLL, key=lambda x: x[3]):
        s = shots[nr]
        faktor = s["clip_fps"] / FPS
        genutzt = n / 2 if langsam else n  # Timeline-Frames bei 100 % aus der Auswahl
        if off < 0 or off + genutzt > s["dauer_f"] + 1e-9:
            fehler.append(f"S{nr:02d}: Versatz {off} + genutzt {genutzt} > Auswahl {s['dauer_f']} — verlängert!")
        src_in = int(round((s["left_offset_f"] + off) * faktor))
        src_out = src_in + int(round(n * faktor))  # angehängt bei 100 %; SetSpeed 50 halbiert den Quellbereich
        v3.append(Item("V3", s["datei"], src_in, src_out, rec, rec + n, True, beat, "broll", True))
        v3_meta.append({"shot": nr, "clip": s["clip"], "rec_in_f": rec, "dauer_f": n, "langsam": langsam, "src_in_f": src_in,
                        "quelle_genutzt_50p": int(round(n if langsam else n * faktor)),
                        "auswahl_50p": [int(round(s["left_offset_f"] * faktor)), int(round((s["left_offset_f"] + s["dauer_f"]) * faktor))]})
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


def bauen(p: dict) -> dict:
    probe = json.loads((AC / "probe.json").read_text())
    session = RA.ResolveSession(RA.connect(), probe=probe)
    if session.project_name != PROJEKT:
        raise SystemExit(f"Offenes Projekt '{session.project_name}' ≠ Freigabe '{PROJEKT}' — nichts geschrieben.")
    if not GRAFIK.exists():
        raise SystemExit(f"Grafikebene fehlt: {GRAFIK}")
    r, proj, mp = session.resolve, session.project, session.media_pool
    user_folder = mp.GetCurrentFolder()
    name = f"AutoCut video-1-taxodia-weg {dt.datetime.now():%Y-%m-%d %H%M} Feinschnitt"
    out: dict = {"projekt": session.project_name, "timeline": name,
                 "bin_vorher": user_folder.GetName() if user_folder else None,
                 "timeline_vorher": session.user_timeline.GetName() if session.user_timeline else None}
    try:
        folder = session.ensure_bin(["AutoCut", "video-1-taxodia-weg"])
        pfade = sorted({it.clip for k in ("A1", "V1", "V2_voll", "V3", "V4", "musik") for it in p[k]})
        media = session.import_media(pfade, folder)
        tl = session.create_timeline(name, 25.0, 3840, 2160, "01:00:00:00")
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
        speed_ok, stab = 0, {}
        for m in p["v3_meta"]:
            x = v3_items[m["rec_in_f"]]
            if m["langsam"]:  # 50p-Quelle bei 50 %: jedes Quellbild genau einmal, daher „Nearest" statt Frame-Blending
                RA._safe(x.SetProperties, None, {"RetimeProcess": r.RETIME_NEAREST})
                speed_ok += int(bool(RA._safe(x.SetSpeed, False, {"Percentage": 50.0, "RippleTimeline": False})))
        out["speed_gesetzt"] = speed_ok
        # Stabilisieren nach dem Tempo (Analyse über den tatsächlich genutzten Quellbereich)
        for n_, m in enumerate(p["v3_meta"], 1):
            t0, shot = dt.datetime.now(), f"S{m['shot']:02d}"
            stab[shot] = bool(RA._safe(v3_items[m["rec_in_f"]].Stabilize, False))
            print(f"  Stabilisiert {n_}/{len(p['v3_meta'])} {shot}: {stab[shot]} ({(dt.datetime.now() - t0).total_seconds():.1f} s)", flush=True)
        out["stabilisiert"] = stab
        v1_items = sorted(tl.GetItemListInTrack("video", 1) or [], key=lambda x: x.GetStart())
        cta = [i for i in p["V1"] if i.beat_nr == PUNCH_IN["beat"]]
        ziel_start = sorted(cta, key=lambda i: i.rec_in_f)[PUNCH_IN["index"]].rec_in_f
        punch = next(x for x in v1_items if int(x.GetStart()) - start == ziel_start)
        out["punch_in"] = bool(RA._safe(punch.SetProperties, False, PUNCH_IN["props"]))
        a1_items = tl.GetItemListInTrack("audio", 1) or []
        opts = {"normalizationMode": "True Peak", "targetLevel": -3.0, "setLevelMode": r.NORMALIZE_AUDIO_SET_LEVEL_INDEPENDENT}
        out["normalisiert"] = bool(tl.NormalizeAudioLevel(a1_items, opts))
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
