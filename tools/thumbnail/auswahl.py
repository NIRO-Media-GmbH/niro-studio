"""Thumbnail-Auswahl (reine Logik, ohne Datei- oder Resolve-Zugriff): Punktzahl je Kandidat, drei Vorschläge aus
verschiedenen Einstellungen, Kandidaten für den Kontaktbogen, Dateinamen und fortlaufende Nummern.
Spec: docs/superpowers/specs/2026-09-21-thumbnail-design.md (Abschnitt „Auswahl“)."""
from __future__ import annotations

import re
import unicodedata

GESICHT_MIN_HOEHE = 0.05   # Gesichtsbox ab 5 % der Bildhöhe → Personen-Motiv
QUALITAET_MIN = 0.4        # faceCaptureQuality für die Empfehlung _1
AUGEN_OFFEN = 0.20         # Lidöffnung (Höhe/Breite der Augen-Landmarks) ab hier offen
MUND_OFFEN = 0.20          # Innenlippen Höhe/Breite ab hier „spricht“
MITTE_MAX_Y = 0.55         # Gesichtsmitte tiefer als 55 % der Bildhöhe → IG-Zone
RAND = 0.01                # Box näher als 1 % am Bildrand → angeschnitten
ABSTAND_S = 1.5            # Vorschläge mindestens so weit auseinander (gelockert: doppelt, gleiche Einstellung erlaubt)
SCHNITT_ABSTAND = 2        # Frames vor/nach einem Schnitt fallen weg


def rang_normiert(werte: list[float]) -> list[float]:
    """Rang je Wert als 0–1 (größter = 1), gleiche Werte gleicher Rang."""
    if len(werte) <= 1:
        return [1.0] * len(werte)
    sortiert = sorted(werte)
    return [sortiert.index(w) / (len(werte) - 1) for w in werte]


def hauptgesicht(gesichter: list[dict]) -> dict | None:
    """Größtes Gesicht nach Boxhöhe."""
    return max(gesichter, key=lambda g: g["box"][3] - g["box"][1]) if gesichter else None


def bewerte(k: dict) -> dict:
    """Setzt art („person“/„thema“), gesicht_ok, punkte und gruende. Ästhetik −1…1 geht als (x+1)/2 ein."""
    aest = (float(k.get("aesthetik") or 0.0) + 1) / 2
    s = float(k.get("schaerfe_n") or 0.0)
    g = hauptgesicht(k.get("gesichter") or [])
    gruende: list[str] = []
    if g and g["box"][3] - g["box"][1] >= GESICHT_MIN_HOEHE:
        q = float(g.get("qualitaet") or 0.0)
        p = 0.45 * q + 0.35 * aest + 0.20 * s
        augen_zu = g.get("augen") is not None and g["augen"] < AUGEN_OFFEN
        if augen_zu:
            p -= 0.5
            gruende.append("Augen zu")
        if g.get("mund") is not None and g["mund"] > MUND_OFFEN:
            abzug = min(0.2, g["mund"] - MUND_OFFEN)
            p -= abzug
            gruende.append(f"Mund offen −{abzug:.2f}")
        x0, y0, x1, y1 = g["box"]
        if x0 < RAND or x1 > 1 - RAND or y0 < RAND or y1 > 1 - RAND or (y0 + y1) / 2 > MITTE_MAX_Y:
            p -= 0.3
            gruende.append("Gesicht am Rand oder zu tief")
        k.update(art="person", gesicht_ok=q >= QUALITAET_MIN and not augen_zu)
    else:
        p = 0.6 * aest + 0.4 * s
        if k.get("utility"):
            p -= 0.2
            gruende.append("Utility-Bild")
        k.update(art="thema", gesicht_ok=False)
    k["punkte"] = round(p, 4)
    k["gruende"] = gruende
    return k


def _passt(k: dict, gewaehlt: list[dict], fps: float, streng: bool) -> bool:
    for g in gewaehlt:
        if streng and k["shot"] == g["shot"]:
            return False
        if abs(k["frame"] - g["frame"]) < ABSTAND_S * fps * (1 if streng else 2):
            return False
    return True


def waehle(kandidaten: list[dict], fps: float, anzahl: int = 3) -> list[dict]:
    """_1 beste Person mit gesicht_ok (sonst bestes Motiv), _2 nächstbestes, _3 bestes Thema (sonst nächstbestes), weitere
    nach Punkten. Erst streng (andere Einstellung, ≥ 1,5 s), dann gelockert (≥ 3 s, gleiche Einstellung erlaubt)."""
    sortiert = sorted((k for k in kandidaten if not k.get("nahe_schnitt")), key=lambda k: -k["punkte"])
    filter_je_rolle = {"person": [lambda k: k["art"] == "person" and k["gesicht_ok"], lambda k: True],
                       "thema": [lambda k: k["art"] == "thema", lambda k: True],
                       "beste": [lambda k: True]}
    rollen = ["person", "beste", "thema"] + ["beste"] * max(0, anzahl - 3)
    gewaehlt: list[dict] = []
    for rolle in rollen[:anzahl]:
        wahl = None
        for f in filter_je_rolle[rolle]:
            for streng in (True, False):
                wahl = next((k for k in sortiert if k not in gewaehlt and f(k) and _passt(k, gewaehlt, fps, streng)), None)
                if wahl:
                    break
            if wahl:
                break
        if wahl:
            gewaehlt.append(wahl)
    return gewaehlt


def fuer_bogen(kandidaten: list[dict], vorschlaege: list[dict], fps: float, n: int = 12, je_shot: int = 2) -> list[dict]:
    """Vorschläge plus die besten weiteren Kandidaten (je Einstellung begrenzt, ≥ 1 s auseinander), nach Punkten sortiert.
    Bei wenigen Einstellungen steigt die Grenze je Einstellung, damit der Bogen voll wird."""
    shots = {k["shot"] for k in kandidaten} or {"?"}
    je_shot = max(je_shot, -(-n // len(shots)))
    liste = list(vorschlaege)
    zaehler: dict[str, int] = {}
    for v in vorschlaege:
        zaehler[v["shot"]] = zaehler.get(v["shot"], 0) + 1
    for k in sorted((k for k in kandidaten if not k.get("nahe_schnitt")), key=lambda k: -k["punkte"]):
        if len(liste) >= n:
            break
        if k in liste or zaehler.get(k["shot"], 0) >= je_shot or any(abs(k["frame"] - x["frame"]) < fps for x in liste):
            continue
        liste.append(k)
        zaehler[k["shot"]] = zaehler.get(k["shot"], 0) + 1
    return sorted(liste, key=lambda k: -k["punkte"])


def nahe_schnitt(frame: int, schnitte: list[int], abstand: int = SCHNITT_ABSTAND) -> bool:
    """Frame liegt höchstens `abstand` Frames vor oder nach einem Schnitt (Schnitt = erster Frame der neuen Einstellung)."""
    return any(abs(frame - s) <= abstand for s in schnitte)


def shot_von(frame: int, segmente: list[dict]) -> str:
    return next((s["id"] for s in segmente if s["start"] <= frame < s["ende"]), "?")


def dateiname(video: str, version: str, nummer: int, vier_k: bool = False) -> str:
    return f"{video}_{version}_Thumbnail_{nummer}{'_4K' if vier_k else ''}.jpg"


def _nfc(s: str) -> str:
    """Dateinamen vom NAS (SMB) kommen zerlegt (NFD, „a“ + Trema); Titel aus JSON/Chat sind NFC (W&L 21.09.2026)."""
    return unicodedata.normalize("NFC", s)


def naechste_nummer(namen: list[str], video: str, version: str) -> int:
    muster = re.compile(re.escape(_nfc(f"{video}_{version}_Thumbnail_")) + r"(\d+)(?:_4K)?\.jpg$")
    return max((int(m.group(1)) for n in namen if (m := muster.match(_nfc(n)))), default=0) + 1


def hoechste_version(namen: list[str], video: str) -> str | None:
    muster = re.compile(re.escape(_nfc(video)) + r"_V(\d+)\.mp4$")
    nummern = [int(m.group(1)) for n in namen if (m := muster.match(_nfc(n)))]
    return f"V{max(nummern)}" if nummern else None
