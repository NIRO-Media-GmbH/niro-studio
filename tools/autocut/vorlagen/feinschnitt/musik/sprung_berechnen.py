"""Vorlage (Stand 15.09.2026): Sprung innerhalb eines Musiktracks beat-genau finden (Onset-Korrelation + Feinabgleich in ms).

Aufruf: tools/autocut/venv/bin/python _intern/musik/sprung_berechnen.py
Situation: ein Musik-Item läuft bis zur Sprungstelle, dort übernimmt ein Folge-Item desselben Tracks mit späterem Quell-In
(z. B. Sprung auf den Aufbau des Songs, damit Höhepunkt und Songende an den richtigen Stellen im Video liegen).
Verfahren (wie in der Session gerechnet):
  1. Onset-Kurve (positiver Spectral Flux: Hann-Fenster 1024 Samples, Hop 5 ms, log-Betragsspektrum, z-normiert) ± FENSTER_S
     um die Auslaufstelle und um jeden Kandidaten-Frame im Suchbereich; Korrelation ohne Versatz → beste Kandidaten mit
     Sprunglänge in Takten.
  2. Feinabgleich für den Kandidaten und seine Nachbar-Frames (± FEIN_FENSTER_S): Versatz ±120 ms in 5-ms-Schritten.
     Empfehlung = Frame mit dem kleinsten Rest-Versatz (Resolve schneidet nur framegenau, 1 Frame = 40 ms).
  3. Pegel 1 s vor der Auslaufstelle gegen 1 s ab dem Einsprung (RMS dBFS) — Hinweis für den Pegel des Folge-Items.
Messung 15.09.: die höchste Korrelation lag bei 7,75 Takten; gewählt wurde der beste Kandidat mit ganzer Taktzahl
(8 Takte, Rest-Versatz −10 ms) — die automatische Kandidatenwahl (FEIN_UM_F = None) bildet das nach.
Eingaben: Musik-WAV aus Material/Musik, Taktlänge aus _intern/musik/analyse.json (musik_analyse.py). Ausgabe nur im Terminal.
Danach: Quell-In des einlaufenden Items in MUSIK_PLAN (feinschnitt_bauen.py) eintragen; alle weiteren Items desselben Tracks
dahinter rücken um dieselbe Frame-Differenz mit, damit überlappende Kopien sample-gleich bleiben. Vor der Abnahme gegenhören.
Herkunft: Taxodia-Charge, Inline-Rechnung der Session 15.09. (kein eigenes Skript in _intern)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.io import wavfile

HIER = Path(__file__).resolve().parent
CH = HIER.parent.parent
MUSIK = CH / "Material" / "Musik"

# ── ANPASSEN je Charge ─────────────────────────────
MUSIK_DATEI = MUSIK / "<Musik-Track>.wav"  # Track mit dem Sprung (WAV in Material/Musik)
AUS_QUELLE_F = None  # Quell-Frame (25 fps) an der Sprungstelle im auslaufenden Item = Quell-In + (Record-Sprung − Record-In)
SUCHE_F = None  # (von, bis) Quell-Frames für den Einsprung, halboffen wie range(), z. B. ±15 Frames um die geplante Stelle
AKTUELL_F = None  # optional: bisher geplanter Quell-In des einlaufenden Items (wird zum Vergleich ausgegeben)
FEIN_UM_F = None  # optional: Kandidat für den Feinabgleich; None = bester Kandidat mit ganzer Taktzahl (± TAKT_TOLERANZ)
TAKT_S = None  # Taktlänge in s; None = "takt_s" des Tracks aus _intern/musik/analyse.json
# ── Ende ANPASSEN ──────────────────────────────────

FPS = 25  # Standard (15.09.): Frames = Timeline-Frames bei 25 fps
HOP_S, WIN = 0.005, 1024  # Standard (15.09.): Onset-Kurve mit 5-ms-Hop und Hann-Fenster über 1024 Samples
FENSTER_S = 4.0  # Standard (15.09.): ± s um Auslaufstelle und Kandidat in der Grobsuche
FEIN_FENSTER_S = 3.0  # Standard (15.09.): ± s im Feinabgleich
VERSATZ_SCHRITTE = 24  # Standard (15.09.): ±24 Hops = ±120 ms Versatzsuche
TOP = 8  # Anzahl gelisteter Kandidaten
TAKT_TOLERANZ = 0.05  # Takte, die ein Sprung von einer ganzen Taktzahl abweichen darf (automatische Kandidatenwahl)


def anpassen_pruefen() -> None:
    offen = []
    if "<" in MUSIK_DATEI.name or not MUSIK_DATEI.exists():
        offen.append(f"MUSIK_DATEI (nicht gefunden: {MUSIK_DATEI})")
    if AUS_QUELLE_F is None:
        offen.append("AUS_QUELLE_F")
    if SUCHE_F is None:
        offen.append("SUCHE_F")
    if offen:
        raise SystemExit("ANPASSEN-Block in musik/sprung_berechnen.py füllen: " + "; ".join(offen))


def taktlaenge() -> float:
    """TAKT_S oder takt_s des Tracks aus analyse.json (musik_analyse.py)."""
    if TAKT_S is not None:
        return float(TAKT_S)
    pfad = HIER / "analyse.json"
    if not pfad.exists():
        raise SystemExit(f"{pfad} fehlt — erst musik_analyse.py ausführen oder TAKT_S setzen.")
    for a in json.loads(pfad.read_text()):
        if a["datei"] == MUSIK_DATEI.name:
            return float(a["takt_s"])
    raise SystemExit(f"{MUSIK_DATEI.name} fehlt in {pfad} — musik_analyse.py neu ausführen oder TAKT_S setzen.")


def lade(pfad: Path) -> tuple[int, np.ndarray]:
    sr, x = wavfile.read(pfad)
    x = x.astype(np.float32) / (2 ** 31 if x.dtype == np.int32 else 2 ** 15 if x.dtype == np.int16 else 1)
    if x.ndim == 2:
        x = x.mean(1)
    return sr, x


def onset(x: np.ndarray, sr: int, t0: float, t1: float) -> np.ndarray:
    """Z-normierte Onset-Kurve (positiver Spectral Flux) von t0 bis t1 Sekunden, ein Wert je Hop."""
    hop = int(sr * HOP_S)
    a = x[int(t0 * sr):int(t1 * sr) + WIN]
    n = (len(a) - WIN) // hop
    fr = np.stack([a[i * hop:i * hop + WIN] * np.hanning(WIN) for i in range(n)])
    s = np.log1p(np.abs(np.fft.rfft(fr, axis=1)))
    fl = np.maximum(np.diff(s, axis=0), 0).sum(1)
    fl = np.concatenate([[0], fl])
    return (fl - fl.mean()) / (fl.std() + 1e-9)


def main() -> None:
    anpassen_pruefen()
    takt_s = taktlaenge()
    sr, x = lade(MUSIK_DATEI)
    aus_s = AUS_QUELLE_F / FPS
    if min(aus_s, SUCHE_F[0] / FPS) - FENSTER_S < 0:
        raise SystemExit(f"Auslaufstelle und Suchbereich müssen mindestens {FENSTER_S} s nach dem Songbeginn liegen.")

    def takte(f: int) -> float:
        return (f - AUS_QUELLE_F) / FPS / takt_s

    # 1) Grobsuche: Korrelation der Onset-Kurven ohne Versatz
    O = onset(x, sr, aus_s - FENSTER_S, aus_s + FENSTER_S)
    res = []
    for f in range(*SUCHE_F):
        I = onset(x, sr, f / FPS - FENSTER_S, f / FPS + FENSTER_S)
        m = min(len(O), len(I))
        res.append((float(np.dot(O[:m], I[:m]) / m), f))
    res.sort(reverse=True)
    print(f"{MUSIK_DATEI.name}: Auslauf bei Quell-Frame {AUS_QUELLE_F} ({aus_s:.2f} s), Takt {takt_s:.4f} s")
    print("beste Quell-Frames (Korrelation, Frame, Sprung in s):")
    for c, f in res[:TOP]:
        print(f"  {c:.3f}  {f}  ({f / FPS:.2f} s, Sprung {(f - AUS_QUELLE_F) / FPS:.3f} s = {takte(f):.3f} Takte)")
    if AKTUELL_F is not None:
        print(f"aktuell {AKTUELL_F}:", [r for r in res if r[1] == AKTUELL_F] or "außerhalb des Suchbereichs")
    # 2) Feinabgleich um den Kandidaten und seine Nachbar-Frames: bester Versatz in ms
    ganz = [(c, f) for c, f in res if round(takte(f)) != 0 and abs(takte(f) - round(takte(f))) <= TAKT_TOLERANZ]
    kandidat = FEIN_UM_F if FEIN_UM_F is not None else (ganz or res)[0][1]
    O = onset(x, sr, aus_s - FEIN_FENSTER_S, aus_s + FEIN_FENSTER_S)
    fein = []
    for f in (kandidat - 1, kandidat, kandidat + 1):
        I = onset(x, sr, f / FPS - FEIN_FENSTER_S, f / FPS + FEIN_FENSTER_S)
        m = min(len(O), len(I))
        lags = range(-VERSATZ_SCHRITTE, VERSATZ_SCHRITTE + 1)
        sc = [(float(np.dot(O[max(0, l):m + min(0, l)], I[max(0, -l):m - max(0, l)]) / m), int(round(l * HOP_S * 1000)))
              for l in lags]
        best = max(sc)
        print(f"Quelle {f}: Korrelation ohne Versatz {sc[VERSATZ_SCHRITTE][0]:.3f}; bestes Alignment bei {best[1]:+d} ms "
              f"(Korr. {best[0]:.3f})")
        fein.append((abs(best[1]), -best[0], f, best[1]))
    _, _, wahl, rest_ms = min(fein)
    print(f"Empfehlung: Quell-In {wahl} ({wahl / FPS:.2f} s) — Sprung {takte(wahl):.3f} Takte, Rest-Versatz {rest_ms:+d} ms; gegenhören")

    # 3) Pegelvergleich: RMS 1 s vor der Auslaufstelle / 1 s ab dem Einsprung
    def rms(t0: float, t1: float) -> float:
        a = x[int(t0 * sr):int(t1 * sr)]
        return float(20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-9))

    ein_s = wahl / FPS
    print(f"Ausgehend {aus_s - 1:.2f}–{aus_s:.2f} s: {rms(aus_s - 1, aus_s):.1f} dB | "
          f"eingehend {ein_s:.2f}–{ein_s + 1:.2f} s: {rms(ein_s, ein_s + 1):.1f} dB")


if __name__ == "__main__":
    main()
