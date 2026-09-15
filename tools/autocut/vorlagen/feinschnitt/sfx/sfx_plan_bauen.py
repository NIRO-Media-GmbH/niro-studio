"""Vorlage (Stand 15.09.2026): SFX-Plan für die Grafikebene (V4) bauen — nur offline, schreibt nur in _intern/sfx/.

Aufruf: SFX_STEM_CACHE=<tmp> PYTHONDONTWRITEBYTECODE=1 tools/autocut/venv/bin/python _intern/sfx/sfx_plan_bauen.py
User-Wunsch (15.09.): SFX aus dem SFX-Ordner des Users für die Animationen, ein nices Sound-Design, „eher subtil“.

Ablauf
1. Ereignisse: Element-Start aus der Remotion-TIMELINE der Grafikebene (über feinschnitt_bauen.grafik_elemente()) + lokale
   Animations-Frames aus den Komponenten (Konstanten im ANPASSEN-Block mit Quelle). Wipe-in/Iris-out werden gegen die Alpha-Deckkraft
   (feinschnitt_bauen.ALPHA_JSON, alpha_mean je Frame) geprüft (erstes/letztes sichtbares Frame), alle Ereignisse gegen die sichtbaren
   V4-Bereiche.
2. Ausrichtung: Whoosh/Swell → Hüllkurven-Maximum (bei Swells mit hartem Stopp = der Stopp) auf das Ereignis,
   Click/Pop → Attack (−3 dB) auf das Erscheinen. Quell-In auf ganze Frames (1/25 s); Record-Frame so, dass der Anker −0,25 … +0,75
   Frames um das Ereignis landet (Ton eher minimal spät als früh).
3. Pegel: Ziel-Sample-Peak je Platzierung (unter Sprache −30 … −26 dBFS, sprachfreie Vollbild-Momente präsenter);
   Clip-Gain = Ziel − Peak des tatsächlich genutzten Abschnitts inkl. linearer Fades, zusätzlich begrenzt, sodass der SFX-Peak
   in allen Frames mit hörbarer Sprache ≤ −26 dBFS bleibt (Sprachmaske aus dem Sprach-Stem, sfx_mischung_pruefen.sprachmaske;
   Scribe-Wortzeiten nur zur Beschriftung).
4. Spuren: A4 „SFX 1“, Überlappungen auf A5 „SFX 2“; keine Überlappung auf derselben Spur.
Liest inventar.json (name → pfad_nas), feinschnitt_bauen (lade, plan, grafik_elemente, tc, ENDE, ALPHA_JSON), sfx_mischung_pruefen
(stems, sprachmaske; optional SFX_STEM_CACHE), _intern/cache/*.scribe.json (source_file, words: text/start/end/type).
Schreibt sfx_plan.json (Platzierungen) und analyse/sfx_plan_details.json (Ereignis-Frame, Anker, Abweichung, Wörter, Pegel):
  sfx_plan.json — Liste je Platzierung: element, ereignis, rec_frame (Timeline-Frame ab 0, an dem die SFX-Datei beginnt), sfx_name,
  pfad_nas, src_in_s (Quell-In in s, auf ganze Frames), dauer_frames, gain_db (Clip-Gain), fade_in_f, fade_out_f, spur (A4/A5),
  begruendung. Spätere Pegelkorrekturen dürfen Felder ergänzen (15.09.: gain_db_vorher_agent); die Skripte lesen nur die genannten.
  analyse/sfx_plan_details.json — {pruefung: Befunde oder ["ok"], platzierungen: je element, ereignis, typ, ereignis_frame, tc, anker,
  anker_in_datei_s, landet_frame, abweichung_frames, rec_frame, rec_ende, aktiv_frames, peak_abschnitt_vor_gain_dbfs, ziel_peak_dbfs,
  peak_nach_gain_dbfs, gain_db, gain_durch_sprache_begrenzt, sprachframes_im_clip, sfx_peak_in_sprachframes_dbfs,
  woerter_im_aktiven_bereich, spur}.
Dazu von Hand sfx_plan.md: Kurzfassung, Klangfamilie (+ Verworfenes mit Messbefund), Timing, Pegel, Platzierungen, bewusst ohne SFX,
Prüfmischung, Offen. Nach neuem Grafik-Render erneut laufen lassen (Anker kommen aus der TIMELINE), danach sfx_mischung_pruefen.py.
Nachtrag Pegel (15.09., nach dem Einsatz): Mit den ursprünglichen Zielpegeln lagen die SFX momentan bei −33 … −42 LUFS (Sprache
≈ −19 LUFS) und galten als zu leise; angehoben wurde in Resolve auf ≈ −28 LUFS momentan unter Sprache, −24 LUFS sprachfrei, Spitze
≤ −10 dBFS (Richtwert: nicht unter −30 LUFS momentan) — das bricht die −26-dBFS-Grenze. Eigentliche Ursache für „nicht zu hören“ war
eine stumme, nachträglich angelegte Spur (sfx_einsetzen.py). Zielpegel vor dem Planen mit dem User klären.
Herkunft: Taxodia-Charge, _intern/sfx/sfx_plan_bauen.py
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

# ── ANPASSEN je Charge ─────────────────────────────
# Lokale Animations-Frames (relativ zum Element-Start, negativ = relativ zum Element-Ende), je Konstante mit Quelle im Code der
# Grafik-Komponente. Bewährte Anker (15.09.): Vollbild-Wipe bei ~⅔ Deckung (Easing bzw. alpha_mean), Flash in der Mitte des
# Aufblendens, Karte/Bauchbinde im schnellsten Teil des Wipes, Iris zwischen letztem sichtbarem Frame und klarem Bild, Pin/Chip/
# Station ab dem Frame, ab dem sie sichtbar sind, Zoom bei höchster Geschwindigkeit, Titel ggf. auf der Zählzeit der Musik
# (Beat-Raster musik/analyse.json).
# GRUND_WIPE = 1.5  # <Komponente>: clipPath-Wipe lokal 0–7, EASE_OUT → lokal 1 = 50 %, 2 = 78 % Deckung (alpha_mean) → Stopp bei ~64 %

# Klangfamilie: Dateinamen (Feld „name" in inventar.json), gewählt per Messung (analyse/sfx_metriken.json) und Spektrogramm
# (analyse/spektren/), nicht nach Namen. Bewährt „Luft statt Effekt" (15.09.): eine Whoosh-Serie mit Varianten für die Vollbild-
# Wipes, linearer Luft-Swell mit hartem Stopp für Iris-Öffnungen, reine Luft-Swishes für Karten und Bauchbinden, drei leise
# UI-Klicks im Wechsel für Pins und Stationen (kein Maschinen-Doppel), derselbe Blip für gleich gestaltete Elemente, ein weicher
# Shimmer nur als Klammer Titel/Endcard, ein langer glatter Whoosh für Zooms. Verworfen: Booms/Impacts, tonale Chimes und Jingles,
# 8-Bit/Game/Error, Noise-Riser, Dateien mit tieffrequentem Plopp (hoher Crest) oder Tonlinie.
# WIPE = "<Whoosh-Serie> 1.wav"  # Vollbild-Wipes: Swell → harter Stopp, Luft bis 16 kHz; weitere Varianten der Serie im Wechsel

# Platzierungen: (element, ereignis, lokal, typ, sfx, anker, vorlauf_f, max_f, fade_in, fade_out, ziel_peak_dbfs, begründung)
#   element: id aus der Remotion-TIMELINE (= beat_nr der V4-Clips); ereignis, begründung: Text für Plan und Bericht
#   lokal: Frame relativ zum Element-Start (negativ = relativ zum Element-Ende)
#   typ: "wipe"/"shimmer"/"karte" (bei lokal 0 … <3 gegen das erste sichtbare Frame geprüft), "iris" (gegen das letzte sichtbare
#        Frame), sonst frei zur Beschriftung (z. B. "pop", "zoom", "kreis")
#   sfx: Dateiname aus inventar.json (Klangfamilie oben)
#   anker: "peak" (Hüllkurven-Maximum, Swells: harter Stopp) oder "attack" (−3 dB-Punkt)
#   vorlauf_f: behaltene Frames vor dem Anker (bestimmt Quell-In); max_f: Obergrenze der Cliplänge; fade_*: Frames (None = auto)
#   ziel_peak_dbfs: unter Sprache −30 … −26; sprachfrei präsenter (15.09.: Kapitel-Blenden −18, Titel/Endcard −17 … −19)
PLATZIERUNGEN: list[tuple] = [
    # ("<element-id>", "Vollbild Wipe rein", GRUND_WIPE, "wipe", WIPE, "peak", 5, 22, 2, None, -26.0, "Vollbild-Wipe unter O-Ton → Grenze unter Sprache"),
]
# ── Ende ANPASSEN ──────────────────────────────────

# Bewusst nicht vertonen (bewährt 15.09.): Mikro-Ereignisse (Ortsschilder, Kicker/Wortkaskaden, Labels, Pin-Pulse), Bewegungen unter
# dichtem O-Ton (Linienfüllungen, Fortschrittspunkte, Fußzeilen), alle Austritte von Karten/Bauchbinden/Titel/Flashes (Doktrin:
# Abgang schnell und leise); zwei Bewegungen im Abstand weniger Frames bekommen einen gemeinsamen weichen Whoosh statt zwei SFX.
# Kein Riser, wo die Musik schon anhebt oder Sprache darunter liegt.

HIER = Path(__file__).resolve().parent
INTERN = HIER.parent
FPS, SR = 25, 48000
SPF = SR // FPS

spec = importlib.util.spec_from_file_location("smp", HIER / "sfx_mischung_pruefen.py")
smp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smp)
fb = smp.fb  # feinschnitt_bauen (über musik/mischung_pruefen geladen)
ENDE = fb.ENDE  # Timeline-Länge in Frames — aus feinschnitt_bauen.py (dort im ANPASSEN-Block)

GRENZE_SPRACHE = -26.0  # Standard (15.09.): max. SFX-Sample-Peak in Frames mit hörbarer Sprache (Nachtrag Pegel im Docstring)


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
    if not PLATZIERUNGEN:
        raise SystemExit("ANPASSEN-Block ausfüllen: PLATZIERUNGEN ist leer (lokale Frames, Klangfamilie, Platzierungen) — nichts geschrieben.")
    tl, shots = fb.lade()
    p, fehler = fb.plan(tl, shots)
    if fehler:
        raise SystemExit("Feinschnitt-Plan fehlerhaft:\n  " + "\n  ".join(fehler))
    elemente = {eid: (von, bis) for eid, von, bis in fb.grafik_elemente()}
    sichtbar = {it.beat_nr: (it.rec_in_f, it.rec_out_f) for it in p["V4"]}
    alpha = json.loads(fb.ALPHA_JSON.read_text())["alpha_mean"]
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
        # Record-Frame: Ton darf leicht nacheilen, kaum vorauseilen (ITU-R BT.1359) → Landung in [−0,25; +0,75) Frames — Standard (15.09.)
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
