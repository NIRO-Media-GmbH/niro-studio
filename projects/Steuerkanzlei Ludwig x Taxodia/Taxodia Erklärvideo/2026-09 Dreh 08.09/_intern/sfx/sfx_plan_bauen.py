"""SFX-Plan für die Grafikebene des Taxodia-Erklärvideos (15.09.2026) — nur offline, schreibt nur in _intern/sfx/.

Aufruf: SFX_STEM_CACHE=<tmp> PYTHONDONTWRITEBYTECODE=1 tools/autocut/venv/bin/python _intern/sfx/sfx_plan_bauen.py
User-Wunsch: „Im SFX Ordner sind Sound Effekte die du nutzen kannst für die Animationen um ein nices Sound Design zu machen.
Es soll eher subtil sein.“

Ablauf
1. Ereignisse: Element-Start aus Grafikebene.tsx (TIMELINE, über feinschnitt_bauen.grafik_elemente()) + lokale Animations-Frames aus
   vollbild.tsx / grafik-basis.tsx (Konstanten unten mit Quelle). Wipe-in/Iris-out werden gegen alpha_v2.json geprüft
   (erstes/letztes sichtbares Frame), alle Ereignisse gegen die sichtbaren V4-Bereiche.
2. Ausrichtung: Whoosh/Swell → Hüllkurven-Maximum (bei Swells mit hartem Stopp = der Stopp) auf das Ereignis,
   Click/Pop → Attack (−3 dB) auf das Erscheinen. Quell-In auf ganze Frames (1/25 s); Record-Frame so, dass der Anker −0,25 … +0,75
   Frames um das Ereignis landet (Ton eher minimal spät als früh).
3. Pegel: Ziel-Sample-Peak je Platzierung (unter Sprache −30 … −26 dBFS, sprachfreie Vollbild-Momente präsenter);
   Clip-Gain = Ziel − Peak des tatsächlich genutzten Abschnitts inkl. linearer Fades, zusätzlich begrenzt, sodass der SFX-Peak
   in allen Frames mit hörbarer Sprache ≤ −26 dBFS bleibt (Sprachmaske aus dem Sprach-Stem, sfx_mischung_pruefen.sprachmaske;
   Scribe-Wortzeiten nur zur Beschriftung).
4. Spuren: A4 „SFX 1“, Überlappungen auf A5 „SFX 2“; keine Überlappung auf derselben Spur.
Schreibt sfx_plan.json (Platzierungen) und analyse/sfx_plan_details.json (Ereignis-Frame, Anker, Abweichung, Wörter, Pegel).
"""
from __future__ import annotations

import glob
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HIER = Path(__file__).resolve().parent
INTERN = HIER.parent
FPS, SR = 25, 48000
SPF = SR // FPS
ENDE = 6845

spec = importlib.util.spec_from_file_location("smp", HIER / "sfx_mischung_pruefen.py")
smp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smp)
fb = smp.fb  # feinschnitt_bauen (über musik/mischung_pruefen geladen)

GRENZE_SPRACHE = -26.0  # max. SFX-Sample-Peak in Frames mit hörbarer Sprache

# ------------------------------------------------------------------------------------------------------------------
# Lokale Animations-Frames (relativ zum Element-Start), Quelle im Code
# ------------------------------------------------------------------------------------------------------------------
FLASH_AUF = 1.5        # Flash: opacity 0→1 in lokal 0–3 (linear) → Mitte des Aufblendens
GRUND_WIPE = 1.5       # WeisserGrund: clipPath-Wipe lokal 0–7, EASE_OUT → lokal 1 = 50 %, 2 = 78 % Deckung (alpha_mean 126,5/197,9) → Stopp bei ~64 %
KARTE_WIPE = 1.5       # HelleKarte: rein(0, 15) EASE_OUT → lokal 1 = 27 %, 2 = 52 % der Endfläche
TITEL_WIPE = 1.7       # wie HelleKarte; 373,7 = Zählzeit von Campagna (Beat-Raster musik/analyse.json)
ENDCARD_WIPE = 1.5     # Endcard: Wipe lokal 0–8 EASE_OUT → lokal 1 = 44 %, 2 = 73 % (alpha_mean 112,7/185,5)
IRIS_ENDE = -0.5       # Iris: lokal dauer−11 … dauer, EASE_IN → Stopp zwischen letztem sichtbaren Frame und klarem Bild
PIN_ILSHOFEN = 10      # KarteIlshofen: <Pin start={10}>
ZOOM_MITTE = 40        # KarteIlshofen: Zoom lokal 18–62, inOut(cubic) → höchste Geschwindigkeit in der Mitte
KREIS = 626 - 552 + 2  # radiusStart = 626−552, Kreis zeichnet lokal 74–96 EASE_OUT → schnellster Teil am Anfang
PIN_VISSELHOEVEDE = 8  # KarteTaxodia: <Pin start={8}>
PIN_ILSHOFEN_2 = 18    # KarteTaxodia: <Pin start={18}>
CHIP_ONLINE = 56       # KarteTaxodia: chip = setzen(frame, 56), sichtbar ab 56
STATIONEN = {"Einstiegskurs": 10, "Teil I": 3327 - 3222, "Teil II": 3372 - 3222, "Prüfung": 3419 - 3222}
LOGOS = 18             # Endcard: logos = rein(16, 14) + setzen(16) → halb eingeblendet bei lokal ~18
PILL = 52              # Endcard: pill = rein(52, 12) + setzen(52)

# ------------------------------------------------------------------------------------------------------------------
# Klangfamilie (Auswahl per Messung + Spektrogramm, analyse/sfx_metriken.json, analyse/spektren/)
# ------------------------------------------------------------------------------------------------------------------
W2 = "Whoosh {}.wav"                                          # Vollbild-Wipes: 5 Varianten derselben Serie (Swell → harter Stopp, Luft bis 16 kHz)
IRIS_A, IRIS_B = "Woosh_AI004.mp3", "Riser Woosh_AI005.mp3"  # Iris: linearer Luft-Swell mit hartem Stopp
SWISH = ("Ninja Jump 5.wav", "Ninja Jump 1.wav", "Ninja Jump 6.wav")  # Karten: reine Luft-Swishes (Fabric: 50-Hz-Plopp/Crest 19 dB, NJ3: Tonlinie → verworfen)
TOCK, TICK, POP, BLIP = ("Smartphone User Interface Click Single.wav", "Menu Select.wav", "Pop Notification.wav",
                         "Digital Interface Notification.wav")  # leise UI-Klicks für Pins, Stationen, Pillen
SHIMMER = "Shimmer and fast airy whoosh.wav"                  # einziger Shimmer: Titel und Endcard (Klammer)
WEICH = "Whoosh Airy Motion Soft Transition.wav"             # weiches Anschwellen: Kreis, Iris+Bauchbinde Flammann
ZOOM = "Cinematic Whoosh (19).wav"                            # langer, glatter Whoosh: Karten-Zoom

# ------------------------------------------------------------------------------------------------------------------
# Platzierungen: (element, ereignis, lokal, typ, sfx, anker, vorlauf_f, max_f, fade_in, fade_out, ziel_peak_dbfs, begründung)
#   lokal: Frame relativ zum Element-Start (negativ = relativ zum Element-Ende)
#   anker: "peak" (Hüllkurven-Maximum, Swells: harter Stopp) oder "attack" (−3 dB-Punkt)
#   vorlauf_f: behaltene Frames vor dem Anker (bestimmt Quell-In); max_f: Obergrenze der Cliplänge; fade_*: Frames (None = auto)
# ------------------------------------------------------------------------------------------------------------------
PLATZIERUNGEN = [
    # --- Kaltstart ---
    ("flash-fachkraeftemangel", "Flash rein (Aufblenden 3 Frames)", FLASH_AUF, "wipe", W2.format("2-4"), "peak", 7, 22, 2, None, -24.0,
     "Swell mit hartem Stopp auf das Aufblenden; Sprechpause ganz ohne Musik → leisester Wipe"),
    ("flash-quereinsteiger", "Flash rein (Aufblenden 3 Frames)", FLASH_AUF, "wipe", W2.format("2-2"), "peak", 7, 22, 2, None, -20.0,
     "Gegenstück zum ersten Flash (andere Variante der Serie); Sprechpause, leise Musik darunter"),
    # --- Titel (Musik-Anhebung, ohne Sprache) ---
    ("titel", "Titelkarte Wipe + Rise", TITEL_WIPE, "shimmer", SHIMMER, "peak", 11, 36, 2, None, -17.0,
     "weicher Shimmer auf Karten-Wipe und Zählzeit der Musik-Anhebung; Ausklang trägt die Wortkaskade"),
    # --- Ludwig / Karte Ilshofen ---
    ("bauchbinde-ludwig", "Bauchbinde Wipe + Rise", KARTE_WIPE, "karte", SWISH[0], "peak", 2, 9, 1, None, -26.0,
     "kurzer Luft-Swish auf den schnellsten Teil des Karten-Wipes, unter Sprache"),
    ("karte-ilshofen", "Vollbild Wipe rein (weißer Grund)", GRUND_WIPE, "wipe", W2.format("2-3"), "peak", 5, 22, 2, None, -26.0,
     "Vollbild-Wipe unter laufendem O-Ton („circa“) → Grenze unter Sprache"),
    ("karte-ilshofen", "Pin Ilshofen erscheint", PIN_ILSHOFEN, "pop", POP, "attack", 0, 6, 0, None, -26.0,
     "Pop exakt auf das Erscheinen des Pins (setzen 0,92→1,02→1)"),
    ("karte-ilshofen", "Karten-Zoom 1→2,7 (lokal 18–62)", ZOOM_MITTE, "zoom", ZOOM, "peak", 12, 36, 2, None, -26.0,
     "langsamer, glatter Whoosh; Peak auf die höchste Zoom-Geschwindigkeit nach Ludwigs Atempause (578–591)"),
    ("karte-ilshofen", "50-km-Kreis zeichnet sich", KREIS, "kreis", WEICH, "peak", 7, 24, 2, None, -26.0,
     "weiches Anschwellen zum Kreisbeginn (EASE_OUT), Ausklang während sich der Kreis schließt"),
    ("karte-ilshofen", "Iris öffnet in den Take", IRIS_ENDE, "iris", IRIS_A, "peak", 11, 16, 2, 3, -22.0,
     "Luft-Swell mit hartem Stopp auf das Iris-Ende (EASE_IN beschleunigt); Sprechpause 660–699 → präsenter"),
    # --- Hein ---
    ("bauchbinde-hein", "Bauchbinde Wipe + Rise", KARTE_WIPE, "karte", SWISH[1], "peak", 3, 9, 1, None, -26.0,
     "Swish-Variante 2, unter Sprache"),
    # --- Kapitel Taxodia ---
    ("blende-taxodia", "Vollbild Wipe rein (Kapitel „Die Online-Steuerfachschule“)", GRUND_WIPE, "wipe", W2.format("2-1"), "peak", 3, 22, 2, None, -18.0,
     "Kapitel-Blende in der Sprechpause (1664–1696) → präsenter; kurzer Swell, damit das Satzende frei bleibt"),
    ("blende-taxodia", "Iris öffnet + Bauchbinde Flammann 4 Frames später", IRIS_ENDE, "iris", WEICH, "peak", 7, 24, 2, None, -27.0,
     "ein weicher Whoosh für beide Bewegungen: Peak aufs Iris-Ende, Ausklang über dem Bauchbinden-Wipe (1716) → keine Doppelung"),
    ("karte-taxodia", "Vollbild Wipe rein (Karte Visselhövede–Ilshofen)", GRUND_WIPE, "wipe", W2.format("2-5"), "peak", 5, 22, 2, None, -26.0,
     "Vollbild-Wipe über Flammanns „ähm“ → Grenze unter Sprache"),
    ("karte-taxodia", "Pin Visselhövede erscheint", PIN_VISSELHOEVEDE, "pop", POP, "attack", 0, 6, 0, None, -26.0,
     "Pop auf den ersten Pin"),
    ("karte-taxodia", "Pin Ilshofen erscheint", PIN_ILSHOFEN_2, "pop", TICK, "attack", 0, 6, 0, None, -27.0,
     "zweiter Pin mit weicherem Tick statt identischem Pop (kein Maschinen-Doppel)"),
    ("karte-taxodia", "Chip „online“ poppt auf", CHIP_ONLINE, "pop", BLIP, "attack", 0, 8, 0, None, -26.0,
     "leiser digitaler Blip auf die Kernaussage „online“; gleicher Klang wie die URL-Pille der Endcard (gleiches Design)"),
    ("karte-taxodia", "Iris öffnet in den Take", IRIS_ENDE, "iris", IRIS_B, "peak", 11, 15, 2, 3, -24.0,
     "Iris-Variante 2; Satzende 1958, erstes Wort 1980 → fast sprachfrei, Gain an Flammanns „Wir“ begrenzt"),
    # --- Faktenkarten ---
    ("software", "Faktenkarte Wipe + Rise (unten rechts)", KARTE_WIPE, "karte", SWISH[2], "peak", 2, 9, 1, None, -26.0,
     "Swish-Variante 3, unter Sprache"),
    ("bachelor-professional", "Faktenkarte Wipe + Rise", KARTE_WIPE, "karte", SWISH[0], "peak", 2, 9, 1, None, -26.0,
     "Swish-Variante 1, unter Sprache"),
    # --- Taxodia-Weg ---
    ("taxodia-weg", "Vollbild Wipe rein (Der Taxodia-Weg)", GRUND_WIPE, "wipe", W2.format("2-2"), "peak", 5, 22, 2, None, -26.0,
     "Vollbild-Wipe auf „geht“ → Grenze unter Sprache"),
    ("taxodia-weg", "Station 1 Einstiegskurs setzt", STATIONEN["Einstiegskurs"], "pop", TOCK, "attack", 0, 6, 0, None, -26.0,
     "weicher Tock auf den Stationspunkt (setzen)"),
    ("taxodia-weg", "Station 2 Teil I setzt", STATIONEN["Teil I"], "pop", TICK, "attack", 0, 6, 0, None, -26.0,
     "Tick-Variante, damit die vier Stationen nicht identisch klingen"),
    ("taxodia-weg", "Station 3 Teil II setzt", STATIONEN["Teil II"], "pop", TOCK, "attack", 0, 6, 0, None, -26.0,
     "Tock wie Station 1"),
    ("taxodia-weg", "Station 4 Prüfung setzt", STATIONEN["Prüfung"], "pop", POP, "attack", 0, 6, 0, None, -26.0,
     "Ziel der Linie: runder Pop statt Tock als kleiner Abschluss"),
    ("taxodia-weg", "Iris öffnet in den Take", IRIS_ENDE, "iris", IRIS_A, "peak", 11, 16, 2, 3, -28.0,
     "Iris-Swell unter Ludwigs ersten Worten → leiser"),
    # --- Kosten / Kapitel Online ---
    ("kosten", "Faktenkarte Wipe + Rise", KARTE_WIPE, "karte", SWISH[1], "peak", 3, 9, 1, None, -26.0,
     "Swish-Variante 2, unter Sprache"),
    ("blende-online", "Vollbild Wipe rein (Kapitel „Online lernen“)", GRUND_WIPE, "wipe", W2.format("2-4"), "peak", 3, 22, 2, None, -18.0,
     "Kapitel-Blende in der Sprechpause (3831–3862), Musikwechsel 2050 → Ikoliks"),
    ("blende-online", "Iris öffnet in den Take", IRIS_ENDE, "iris", IRIS_B, "peak", 11, 15, 2, 3, -28.0,
     "Iris-Swell unter Heins ersten Worten → leiser"),
    ("monitoring", "Faktenkarte Wipe + Rise", KARTE_WIPE, "karte", SWISH[2], "peak", 2, 9, 1, None, -26.0,
     "Swish-Variante 3, unter Sprache"),
    ("abrechnung", "Faktenkarte Wipe + Rise", KARTE_WIPE, "karte", SWISH[0], "peak", 2, 9, 1, None, -26.0,
     "Swish-Variante 1, unter Sprache"),
    # --- Kapitel Ergebnis / CTAs ---
    ("blende-ergebnis", "Vollbild Wipe rein (Kapitel „Das Ergebnis“)", GRUND_WIPE, "wipe", W2.format("2-3"), "peak", 3, 22, 2, None, -18.0,
     "Kapitel-Blende in der Sprechpause (5446–5485)"),
    ("blende-ergebnis", "Iris öffnet in den Take", IRIS_ENDE, "iris", IRIS_A, "peak", 11, 16, 2, 3, -28.0,
     "Iris-Swell unter Flammanns „haben“ → leiser"),
    ("blende-kanzleien", "Vollbild Wipe rein (CTA „Für Kanzleien“)", GRUND_WIPE, "wipe", W2.format("2-5"), "peak", 3, 22, 2, None, -18.0,
     "CTA-Blende in der Sprechpause (6007–6032)"),
    ("blende-kanzleien", "Iris öffnet in den Take", IRIS_ENDE, "iris", IRIS_B, "peak", 11, 15, 2, 3, -28.0,
     "Iris-Swell unter „appellieren“ → leiser"),
    ("blende-quereinsteiger", "Vollbild Wipe rein (CTA „Für Quereinsteiger“)", GRUND_WIPE, "wipe", W2.format("2-1"), "peak", 3, 22, 2, None, -18.0,
     "CTA-Blende in der Sprechpause (6349–6380)"),
    ("blende-quereinsteiger", "Iris öffnet in den Take", IRIS_ENDE, "iris", IRIS_A, "peak", 11, 16, 2, 3, -28.0,
     "Iris-Swell, Stopp auf Heins „Also“ (6380–6384) → leiser"),
    # --- Endcard ---
    ("endcard", "Endcard Wipe rein", ENDCARD_WIPE, "wipe", W2.format("2-3"), "peak", 3, 22, 2, None, -19.0,
     "letzter Vollbild-Wipe direkt nach Heins „ist.“ (6637); Musik-Finale setzt 6645 ein"),
    ("endcard", "Logos Taxodia + Ludwig erscheinen", LOGOS, "shimmer", SHIMMER, "peak", 10, 36, 2, None, -18.0,
     "zweiter und letzter weicher Shimmer (Klammer zum Titel) auf die Logos, über dem Musik-Finale"),
    ("endcard", "URL-Pille taxodia.de poppt auf", PILL, "pop", BLIP, "attack", 0, 8, 0, None, -18.0,
     "Blip wie beim „online“-Chip (gleiche grüne Pille); sprachfrei, deutlich unter dem Musik-Finale"),
]

# Bewusst nicht vertont (Mikro-Ereignisse / Dichte): Ortsschilder, Kicker/Wortkaskaden, Radius-Label, Bogen der Karte Taxodia
# (Chip schließt ihn ab), Linienfüllung und Fortschrittspunkt des Taxodia-Wegs (dichter O-Ton), Fußzeile, Pin-Pulse,
# alle Austritte der Karten/Bauchbinden (Doktrin: Abgang schnell und leise), Flash-Ausblenden, Bauchbinde Flammann (im Iris-Whoosh).
# Kein Riser: Titel hat die Musik-Anhebung auf der Eins (345), vor der Endcard läuft Heins CTA bis 6637.


def lade_audio(pfad: str) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", pfad, "-map", "0:a:0", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2).astype(np.float64)


def huelle(x: np.ndarray, fenster_s: float = 0.005, hop_s: float = 0.001) -> tuple[np.ndarray, np.ndarray]:
    p = (x ** 2).mean(axis=1)
    n, h = int(fenster_s * SR), int(hop_s * SR)
    cs = np.concatenate([[0.0], np.cumsum(p)])
    st = np.arange(0, max(1, len(p) - n), h)
    return (st + n / 2) / SR, 10 * np.log10((cs[st + n] - cs[st]) / n + 1e-14)


def woerter(p: dict) -> list[tuple[float, float, str]]:
    """Scribe-Wortzeiten der A1-Clips auf Timeline-Frames abgebildet (nur Beschriftung)."""
    cache = {}
    for f in glob.glob(str(INTERN / "cache" / "*.scribe.json")):
        d = json.loads(Path(f).read_text())
        if isinstance(d, dict) and "source_file" in d:
            cache[d["source_file"]] = d
    out = []
    for it in sorted(p["A1"], key=lambda i: i.rec_in_f):
        c = cache.get(Path(it.clip).name)
        if not c:
            continue
        s0, s1 = it.src_in_f / FPS, it.src_out_f / FPS
        for w in c["words"]:
            if w.get("type", "word") == "word" and w["start"] >= s0 - 0.02 and w["end"] <= s1 + 0.02:
                out.append((it.rec_in_f + (w["start"] - s0) * FPS, it.rec_in_f + (w["end"] - s0) * FPS, w["text"]))
    return out


def main() -> None:
    tl, shots = fb.lade()
    p, fehler = fb.plan(tl, shots)
    if fehler:
        raise SystemExit("Feinschnitt-Plan fehlerhaft:\n  " + "\n  ".join(fehler))
    elemente = {eid: (von, bis) for eid, von, bis in fb.grafik_elemente()}
    sichtbar = {it.beat_nr: (it.rec_in_f, it.rec_out_f) for it in p["V4"]}
    alpha = json.loads((INTERN / "grafik" / "alpha_v2.json").read_text())["alpha_mean"]
    inv = {e["name"]: e for e in json.loads((HIER / "inventar.json").read_text())}
    wl = woerter(p)
    sprache, _musik, aktiv_items = smp.stems()
    maske, _ = smp.sprachmaske(sprache, aktiv_items)
    audio: dict[str, np.ndarray] = {}
    pruef: list[str] = []
    details, plan = [], []

    for (eid, ereignis, lokal, typ, name, anker, vorlauf, max_f, fi, fo, ziel, grund) in PLATZIERUNGEN:
        von, bis = elemente[eid]
        e_frame = (bis + lokal) if lokal < 0 else (von + lokal)
        s0, s1 = sichtbar[eid]
        if not (s0 - 1 <= e_frame <= s1):
            pruef.append(f"{eid}/{ereignis}: Ereignis {e_frame} außerhalb des sichtbaren Bereichs {s0}–{s1}")
        # Wipe/Iris gegen die gemessene Deckkraft
        if typ in ("wipe", "shimmer", "karte") and 0 <= lokal < 3:
            erstes = next(f for f in range(von, bis) if alpha[f] > 0)
            if not (erstes - 1 <= e_frame <= erstes + 2):
                pruef.append(f"{eid}: Wipe-Anker {e_frame} passt nicht zum ersten sichtbaren Frame {erstes}")
        if typ == "iris":
            letztes = max(f for f in range(von, min(bis, ENDE)) if alpha[f] > 0)
            if not (letztes - 2 <= e_frame <= letztes + 1):
                pruef.append(f"{eid}: Iris-Anker {e_frame} passt nicht zum letzten sichtbaren Frame {letztes}")
        e = inv[name]
        if name not in audio:
            audio[name] = lade_audio(e["pfad_nas"])
        x = audio[name]
        t, env = huelle(x)
        emax = float(env.max())
        t_a = float(t[int(env.argmax())]) if anker == "peak" else float(t[np.nonzero(env >= emax - 3)[0][0]])
        # Quell-In auf ganze Frames, nie hinter den Anker
        src_in = max(0, math.floor((t_a - vorlauf / FPS) * FPS + 1e-9)) / FPS
        # Record-Frame: Ton darf leicht nacheilen, kaum vorauseilen (ITU-R BT.1359) → Landung in [−0,25; +0,75) Frames
        rec = math.ceil(e_frame - (t_a - src_in) * FPS - 0.25)
        landet = rec + (t_a - src_in) * FPS
        # Länge: bis −45 dB unter Maximum, begrenzt
        i_end = np.nonzero(env > emax - 45)[0][-1]
        t_end = min(float(t[i_end]) + 0.02, len(x) / SR)
        dauer = max(2, int(min(max_f, math.ceil((t_end - src_in) * FPS))))
        seg = x[int(round(src_in * SR)): int(round(src_in * SR)) + dauer * SPF].copy()
        if len(seg) < dauer * SPF:
            seg = np.pad(seg, ((0, dauer * SPF - len(seg)), (0, 0)))
        pegel_an = lambda sek: float(np.interp(sek, t, env)) - emax
        if fi is None:
            fi = 2 if pegel_an(src_in) > -35 else 1
        if fo is None:
            fo = 1 if pegel_an(src_in + dauer / FPS - 0.01) < -40 else min(6, max(2, dauer // 4))
        n = len(seg)
        h = np.ones(n)
        if fi:
            h[: fi * SPF] = np.linspace(0, 1, fi * SPF)
        if fo:
            h[-fo * SPF:] = np.minimum(h[-fo * SPF:], np.linspace(1, 0, fo * SPF))
        seg *= h[:, None]
        pk = 20 * np.log10(np.abs(seg).max() + 1e-12)
        # Anker darf weder im Fade-In noch im Fade-Out liegen
        if fi and (t_a - src_in) < fi / FPS:
            pruef.append(f"{eid}/{ereignis}: Anker liegt im Fade-In")
        if fo and (t_a - src_in) > (dauer - fo) / FPS:
            pruef.append(f"{eid}/{ereignis}: Anker liegt im Fade-Out")
        # Gain: Ziel-Peak, begrenzt durch Sprache (SFX-Peak in Frames mit hörbarer Sprache ≤ −26 dBFS)
        gain_ziel = ziel - pk
        pk_sprache_roh = 0.0
        sprachframes = 0
        for k in range(dauer):
            f = rec + k
            if 0 <= f < ENDE and maske[f]:
                sprachframes += 1
                pk_sprache_roh = max(pk_sprache_roh, float(np.abs(seg[k * SPF:(k + 1) * SPF]).max()))
        gain_grenze = GRENZE_SPRACHE - 20 * np.log10(pk_sprache_roh) if pk_sprache_roh > 0 else float("inf")
        gain = math.floor(min(gain_ziel, gain_grenze) * 10) / 10
        begrenzt = gain_grenze < gain_ziel
        peak_nach = pk + gain
        if begrenzt and ziel - peak_nach > 3:
            pruef.append(f"{eid}/{ereignis}: Sprachgrenze kostet {ziel - peak_nach:.1f} dB (Peak {peak_nach:.1f} statt {ziel})")
        # Wörter im aktiven Bereich (Hüllkurve > −20 dB unter Maximum) — Beschriftung
        tt = np.arange(0, dauer / FPS, 0.001) + src_in
        aktiv_t = tt[np.interp(tt, t, env) - emax > -20]
        a_von = rec + ((aktiv_t[0] - src_in) * FPS if len(aktiv_t) else 0)
        a_bis = rec + ((aktiv_t[-1] - src_in) * FPS if len(aktiv_t) else dauer)
        ueber = [w for w in wl if w[1] > a_von and w[0] < a_bis]
        plan.append({
            "element": eid, "ereignis": ereignis, "rec_frame": rec, "sfx_name": name, "pfad_nas": e["pfad_nas"],
            "src_in_s": round(src_in, 2), "dauer_frames": dauer, "gain_db": gain, "fade_in_f": int(fi), "fade_out_f": int(fo),
            "spur": None, "begruendung": grund,
        })
        details.append({
            "element": eid, "ereignis": ereignis, "typ": typ, "ereignis_frame": e_frame, "tc": fb.tc(int(e_frame)),
            "anker": anker, "anker_in_datei_s": round(t_a, 3), "landet_frame": round(landet, 2),
            "abweichung_frames": round(landet - e_frame, 2), "rec_frame": rec, "rec_ende": rec + dauer,
            "aktiv_frames": [round(float(a_von), 1), round(float(a_bis), 1)], "peak_abschnitt_vor_gain_dbfs": round(pk, 2),
            "ziel_peak_dbfs": ziel, "peak_nach_gain_dbfs": round(peak_nach, 1), "gain_db": gain,
            "gain_durch_sprache_begrenzt": bool(begrenzt), "sprachframes_im_clip": sprachframes,
            "sfx_peak_in_sprachframes_dbfs": round(20 * np.log10(pk_sprache_roh) + gain, 1) if pk_sprache_roh > 0 else None,
            "woerter_im_aktiven_bereich": " ".join(w[2] for w in ueber),
        })

    # Spuren: A4, Überlappungen auf A5
    ende = {"A4": -1, "A5": -1}
    for pl, de in sorted(zip(plan, details), key=lambda z: z[0]["rec_frame"]):
        for spur in ("A4", "A5"):
            if pl["rec_frame"] >= ende[spur]:
                pl["spur"] = de["spur"] = spur
                ende[spur] = pl["rec_frame"] + pl["dauer_frames"]
                break
        else:
            pruef.append(f"{pl['element']}/{pl['ereignis']}: überlappt auf A4 und A5")
    plan.sort(key=lambda z: z["rec_frame"])
    details.sort(key=lambda z: z["rec_frame"])
    for spur in ("A4", "A5"):
        its = [pl for pl in plan if pl["spur"] == spur]
        for a, b in zip(its, its[1:]):
            if b["rec_frame"] < a["rec_frame"] + a["dauer_frames"]:
                pruef.append(f"{spur}: Überlappung {a['element']} / {b['element']}")
    for pl in plan:
        if pl["rec_frame"] < 0 or pl["rec_frame"] + pl["dauer_frames"] > ENDE:
            pruef.append(f"{pl['element']}: außerhalb der Timeline")
    (HIER / "sfx_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    (HIER / "analyse").mkdir(exist_ok=True)
    (HIER / "analyse" / "sfx_plan_details.json").write_text(
        json.dumps({"pruefung": pruef or ["ok"], "platzierungen": details}, ensure_ascii=False, indent=1), encoding="utf-8")
    for pl, de in zip(plan, details):
        print(f"{pl['spur']} {pl['rec_frame']:5d}+{pl['dauer_frames']:2d} {de['tc']} {pl['element'][:21]:21s} {pl['sfx_name'][:30]:30s} "
              f"in {pl['src_in_s']:.2f} g {pl['gain_db']:+5.1f} pk {de['peak_nach_gain_dbfs']:5.1f}{'*' if de['gain_durch_sprache_begrenzt'] else ' '} "
              f"f {pl['fade_in_f']}/{pl['fade_out_f']} Δ{de['abweichung_frames']:+.2f} S{de['sprachframes_im_clip']:2d} "
              f"{de['woerter_im_aktiven_bereich'][:30]}")
    print(f"{len(plan)} Platzierungen, A4 {sum(pl['spur'] == 'A4' for pl in plan)}, A5 {sum(pl['spur'] == 'A5' for pl in plan)}")
    print("Prüfung:", "ok" if not pruef else "\n  " + "\n  ".join(pruef))


if __name__ == "__main__":
    main()
