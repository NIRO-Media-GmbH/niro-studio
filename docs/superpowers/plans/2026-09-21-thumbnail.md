# Thumbnail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Zehnte Studio-Funktion „Thumbnail:“ — je Video drei saubere Standbilder (ohne Grafik, Untertitel, Effekte) als
JPG 1080×1920 + 4K, abgelegt in `04_Exportiert/<Video>/Thumbnails/`, nur auf Wunsch des Users.

**Architecture:** `resolve_sauber.py` rendert eine eigene Kopie der Timeline ohne Overlays (Quick Export, danach
aufräumen) und liefert die Einstellungen (Shots). `bewerten.swift` bewertet Kandidaten-Frames mit Apple Vision
(Ästhetik, Gesichtsqualität, Augen, Mund). `auswahl.py` ist reine Logik (Punktzahl, drei Vorschläge, Bogen, Dateinamen).
`thumbnail.py` verbindet alles per ffmpeg (`vorschlagen`, `ablegen`).

**Tech Stack:** Python 3.12 (`tools/autocut/venv`: numpy, PIL, pytest, Resolve-Modul über `niro_autocut.resolve_api`),
ffmpeg/ffprobe, Swift 6 + Vision (macOS 15+; Studio-Mac 26.6), DaVinci Resolve Studio 21.1.

## Global Constraints

- Nur auf ausdrücklichen Wunsch des Users; keine Automatik in anderen Workflows.
- 3 Vorschläge je Video: `_1` = Person (Gesichtsqualität ≥ 0,4, Augen offen), `_2` = nächstbestes, `_3` = Thema; verschiedene Einstellungen, ≥ 1,5 s auseinander.
- Dateien `<Video>_V<n>_Thumbnail_<k>.jpg` (lange Kante 1920) und `<Video>_V<n>_Thumbnail_<k>_4K.jpg` (Quellauflösung), JPG Qualität 92, sRGB-Profil.
- Ablage NAS `<Exportordner>/<Video>/Thumbnails/` + Studio `<Charge>/Ergebnisse/Thumbnails/<Video>/`; nie überschreiben, Nummern zählen weiter.
- Resolve: nur im exakt genannten, offenen Projekt; nur eigene Objekte („Claude Thumbnail …“), danach gelöscht; Timeline, Playhead, Bin, Seite des Users zurück; nicht während der Wiedergabe schreiben.
- Prüfung: freie Frames SSIM-Median ≥ 0,95, sonst (keine freien Frames) Median über 12 Frames ≥ 0,80 und Luma-Abweichung ≤ 3 %; Detail-Faktor ≥ 1,15 sonst Warnung.
- Commits nur auf Wunsch des Users (Session-Regel); die Commit-Schritte unten entfallen bis dahin.

---

### Task 1: Auswahl-Logik

**Files:**
- Create: `tools/thumbnail/auswahl.py`
- Test: `tools/thumbnail/tests/test_auswahl.py`

**Interfaces:**
- Produces: `rang_normiert(werte) -> list[float]`, `hauptgesicht(gesichter) -> dict|None`, `bewerte(k) -> dict` (setzt
  `art`, `gesicht_ok`, `punkte`, `gruende`), `waehle(kandidaten, fps, anzahl=3) -> list[dict]`,
  `fuer_bogen(kandidaten, vorschlaege, fps, n=12, je_shot=2) -> list[dict]`, `nahe_schnitt(frame, schnitte) -> bool`,
  `shot_von(frame, segmente) -> str`, `dateiname(video, version, nummer, vier_k=False) -> str`,
  `naechste_nummer(namen, video, version) -> int`, `hoechste_version(namen, video) -> str|None`, Konstante `GESICHT_MIN_HOEHE`.
  Kandidat = dict mit `frame`, `shot`, `nahe_schnitt`, `aesthetik`, `utility`, `gesichter` (`box` [x0,y0,x1,y1] oben links,
  `qualitaet`, `augen`, `mund`), `schaerfe_n`.

- [ ] **Step 1: Tests schreiben** — `tools/thumbnail/tests/test_auswahl.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auswahl as A  # noqa: E402


def kand(frame, shot, punkte, art="person", ok=True, **kw):
    k = {"frame": frame, "shot": shot, "punkte": punkte, "art": art, "gesicht_ok": ok, "nahe_schnitt": False}
    k.update(kw)
    return k


def test_bewerte_person_mit_offenen_augen():
    k = A.bewerte({"aesthetik": 0.6, "utility": False, "schaerfe_n": 1.0,
                   "gesichter": [{"box": [0.4, 0.2, 0.6, 0.32], "qualitaet": 0.8, "augen": 0.3, "mund": 0.05}]})
    assert k["art"] == "person" and k["gesicht_ok"] is True
    assert k["punkte"] == round(0.45 * 0.8 + 0.35 * 0.8 + 0.20 * 1.0, 4)


def test_bewerte_abzuege_augen_zu_und_ig_zone():
    k = A.bewerte({"aesthetik": 0.6, "schaerfe_n": 1.0,
                   "gesichter": [{"box": [0.4, 0.6, 0.6, 0.72], "qualitaet": 0.8, "augen": 0.1, "mund": 0.05}]})
    assert k["gesicht_ok"] is False and "Augen zu" in k["gruende"]
    assert k["punkte"] == round(0.45 * 0.8 + 0.35 * 0.8 + 0.20 - 0.5 - 0.3, 4)


def test_bewerte_mund_offen_abzug_gedeckelt():
    k = A.bewerte({"aesthetik": 0.0, "schaerfe_n": 0.0,
                   "gesichter": [{"box": [0.4, 0.2, 0.6, 0.32], "qualitaet": 0.5, "augen": 0.3, "mund": 0.9}]})
    assert k["punkte"] == round(0.45 * 0.5 + 0.35 * 0.5 - 0.2, 4)


def test_bewerte_kleines_gesicht_ist_thema():
    k = A.bewerte({"aesthetik": 0.2, "utility": True, "schaerfe_n": 0.5,
                   "gesichter": [{"box": [0.5, 0.3, 0.52, 0.33], "qualitaet": 0.9, "augen": 0.3, "mund": 0.0}]})
    assert k["art"] == "thema" and k["gesicht_ok"] is False
    assert k["punkte"] == round(0.6 * 0.6 + 0.4 * 0.5 - 0.2, 4)


def test_waehle_person_dann_bestes_dann_thema():
    ks = [kand(10, "a", 0.9), kand(15, "a", 0.88), kand(100, "b", 0.8), kand(200, "c", 0.5, art="thema", ok=False),
          kand(300, "d", 0.95, art="thema", ok=False)]
    assert [k["frame"] for k in A.waehle(ks, fps=25)] == [10, 300, 200]


def test_waehle_lockert_bei_nur_einer_einstellung():
    ks = [kand(0, "a", 0.9), kand(20, "a", 0.85), kand(80, "a", 0.8), kand(160, "a", 0.7)]
    assert [k["frame"] for k in A.waehle(ks, fps=25)] == [0, 80, 160]


def test_waehle_ohne_gute_person_nimmt_bestes_motiv():
    ks = [kand(0, "a", 0.6, ok=False), kand(100, "b", 0.7, art="thema", ok=False)]
    assert [k["frame"] for k in A.waehle(ks, fps=25, anzahl=1)] == [100]


def test_nahe_schnitt_faellt_weg():
    ks = [kand(48, "a", 0.99, nahe_schnitt=True), kand(10, "a", 0.5)]
    assert [k["frame"] for k in A.waehle(ks, fps=25, anzahl=1)] == [10]
    assert A.nahe_schnitt(48, [50]) and not A.nahe_schnitt(47, [50])


def test_fuer_bogen_je_shot_begrenzt_und_vorschlaege_drin():
    ks = [kand(i * 30, "a" if i < 6 else "b", 1 - i * 0.01) for i in range(10)]
    b = A.fuer_bogen(ks, [ks[0], ks[6]], fps=25, n=6, je_shot=2)
    assert [k["frame"] for k in b] == [0, 30, 60, 180, 210, 240]


def test_dateinamen_und_nummern():
    namen = ["08 - Duroc vs. Normal_V4_Thumbnail_1.jpg", "08 - Duroc vs. Normal_V4_Thumbnail_3_4K.jpg",
             "08 - Duroc vs. Normal_V3_Thumbnail_7.jpg", "anderes.jpg"]
    assert A.naechste_nummer(namen, "08 - Duroc vs. Normal", "V4") == 4
    assert A.naechste_nummer([], "0 - Tagesessen", "V2") == 1
    assert A.dateiname("0 - Tagesessen", "V2", 2, vier_k=True) == "0 - Tagesessen_V2_Thumbnail_2_4K.jpg"


def test_hoechste_version_und_shot():
    namen = ["12 - Hackfleisch_V1.mp4", "12 - Hackfleisch_V10.mp4", "12 - Hackfleisch_V4.mp4", "x_V99.mp4"]
    assert A.hoechste_version(namen, "12 - Hackfleisch") == "V10"
    assert A.hoechste_version([], "12 - Hackfleisch") is None
    seg = [{"start": 0, "ende": 50, "id": "V1@0"}, {"start": 50, "ende": 90, "id": "V3@50"}]
    assert A.shot_von(49, seg) == "V1@0" and A.shot_von(50, seg) == "V3@50" and A.shot_von(95, seg) == "?"


def test_rang_normiert():
    assert A.rang_normiert([3.0, 1.0, 2.0]) == [1.0, 0.0, 0.5]
    assert A.rang_normiert([5.0]) == [1.0] and A.rang_normiert([]) == []
```

- [ ] **Step 2: Tests laufen lassen, müssen scheitern**

Run: `tools/autocut/venv/bin/python -m pytest tools/thumbnail/tests -q`
Expected: FAIL (`ModuleNotFoundError: No module named 'auswahl'`)

- [ ] **Step 3: `tools/thumbnail/auswahl.py` schreiben**

```python
"""Thumbnail-Auswahl (reine Logik, ohne Datei- oder Resolve-Zugriff): Punktzahl je Kandidat, drei Vorschläge aus
verschiedenen Einstellungen, Kandidaten für den Kontaktbogen, Dateinamen und fortlaufende Nummern.
Spec: docs/superpowers/specs/2026-09-21-thumbnail-design.md (Abschnitt „Auswahl“)."""
from __future__ import annotations

import re

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


def naechste_nummer(namen: list[str], video: str, version: str) -> int:
    muster = re.compile(re.escape(f"{video}_{version}_Thumbnail_") + r"(\d+)(?:_4K)?\.jpg$")
    return max((int(m.group(1)) for n in namen if (m := muster.match(n))), default=0) + 1


def hoechste_version(namen: list[str], video: str) -> str | None:
    muster = re.compile(re.escape(video) + r"_V(\d+)\.mp4$")
    nummern = [int(m.group(1)) for n in namen if (m := muster.match(n))]
    return f"V{max(nummern)}" if nummern else None
```

- [ ] **Step 4: Tests laufen lassen, müssen bestehen**

Run: `tools/autocut/venv/bin/python -m pytest tools/thumbnail/tests -q`
Expected: `12 passed`

- [ ] **Step 5: Commit (nur auf Wunsch)** — `git add tools/thumbnail/auswahl.py tools/thumbnail/tests/test_auswahl.py`

---

### Task 2: Vision-Bewerter

**Files:**
- Create: `tools/thumbnail/bewerten.swift`
- Create: `tools/thumbnail/.gitignore` (`bin/`, `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, wie `tools/autocut/.gitignore`)

**Interfaces:**
- Produces: Binärdatei `tools/thumbnail/bin/bewerten <Ordner>` → je `.jpg` eine JSON-Zeile
  `{"datei", "aesthetik", "utility", "gesichter": [{"box", "qualitaet", "augen", "mund"}]}` oder `{"datei", "fehler"}`.

- [ ] **Step 1: `tools/thumbnail/bewerten.swift` schreiben**

```swift
// Thumbnail-Bewertung (Stand 21.09.2026) per Apple Vision für alle .jpg eines Ordners.
// Build:  swiftc -O tools/thumbnail/bewerten.swift -o tools/thumbnail/bin/bewerten   (erledigt thumbnail.py beim ersten Lauf)
// Aufruf: bewerten <Ordner>  → je .jpg (sortiert) eine JSON-Zeile auf stdout:
//   {"datei": …, "aesthetik": −1…1, "utility": bool,
//    "gesichter": [{"box": [x0, y0, x1, y1], "qualitaet": 0–1, "augen": Lidöffnung, "mund": Mundöffnung}]}
// Box normiert, Ursprung oben links. augen = Mittel beider Augen (Höhe/Breite der Landmark-Punkte), mund = Innenlippen
// Höhe/Breite; fehlende Werte = null. Lesefehler: {"datei": …, "fehler": …}. Vision schreibt Logzeilen auf stderr.
import Foundation
import Vision
import CoreGraphics
import ImageIO

func oeffnung(_ r: VNFaceLandmarkRegion2D?) -> Double? {
    guard let r = r, r.pointCount >= 4 else { return nil }
    let xs = r.normalizedPoints.map { Double($0.x) }, ys = r.normalizedPoints.map { Double($0.y) }
    let w = xs.max()! - xs.min()!, h = ys.max()! - ys.min()!
    return w > 0 ? h / w : nil
}

func zeile(_ d: [String: Any]) {
    if let data = try? JSONSerialization.data(withJSONObject: d), let s = String(data: data, encoding: .utf8) { print(s) }
}

let ordner = URL(fileURLWithPath: CommandLine.arguments[1])
let dateien = ((try? FileManager.default.contentsOfDirectory(atPath: ordner.path)) ?? []).filter { $0.hasSuffix(".jpg") }.sorted()
for f in dateien {
    autoreleasepool {
        guard let src = CGImageSourceCreateWithURL(ordner.appendingPathComponent(f) as CFURL, nil),
              let img = CGImageSourceCreateImageAtIndex(src, 0, nil) else { zeile(["datei": f, "fehler": "lesen"]); return }
        let handler = VNImageRequestHandler(cgImage: img, options: [:])
        let aest = VNCalculateImageAestheticsScoresRequest()
        let marks = VNDetectFaceLandmarksRequest()
        do { try handler.perform([aest, marks]) } catch { zeile(["datei": f, "fehler": "\(error)"]); return }
        let faces = marks.results ?? []
        var qualitaet = [Double](repeating: -1, count: faces.count)
        if !faces.isEmpty {
            let q = VNDetectFaceCaptureQualityRequest()
            q.inputFaceObservations = faces
            if (try? handler.perform([q])) != nil, let res = q.results, res.count == faces.count {
                qualitaet = res.map { Double($0.faceCaptureQuality ?? -1) }
            }
        }
        var gesichter: [[String: Any]] = []
        for (i, o) in faces.enumerated() {
            let b = o.boundingBox
            var g: [String: Any] = ["box": [b.minX, 1 - b.maxY, b.maxX, 1 - b.minY].map { (Double($0) * 10000).rounded() / 10000 }]
            g["qualitaet"] = qualitaet[i] >= 0 ? qualitaet[i] as Any : NSNull()
            if let l = oeffnung(o.landmarks?.leftEye), let r = oeffnung(o.landmarks?.rightEye) { g["augen"] = (l + r) / 2 } else { g["augen"] = NSNull() }
            if let m = oeffnung(o.landmarks?.innerLips) { g["mund"] = m } else { g["mund"] = NSNull() }
            gesichter.append(g)
        }
        var d: [String: Any] = ["datei": f, "gesichter": gesichter, "utility": aest.results?.first?.isUtility ?? false]
        if let a = aest.results?.first { d["aesthetik"] = Double(a.overallScore) } else { d["aesthetik"] = NSNull() }
        zeile(d)
    }
}
```

- [ ] **Step 2: Bauen und an zwei echten Frames prüfen**

Run: `mkdir -p tools/thumbnail/bin && swiftc -O tools/thumbnail/bewerten.swift -o tools/thumbnail/bin/bewerten && tools/thumbnail/bin/bewerten <Ordner mit 2 Setzer-Frames> 2>/dev/null`
Expected: zwei JSON-Zeilen, eine mit Gesicht (`qualitaet` ≈ 0,2–0,5, `augen` und `mund` Zahlen).

- [ ] **Step 3: `tools/thumbnail/.gitignore` anlegen** — gebauter Bewerter und Python-Caches bleiben unversioniert.

---

### Task 3: Resolve-Schritt (saubere Quelle)

**Files:**
- Create: `tools/thumbnail/resolve_sauber.py`

**Interfaces:**
- Consumes: `niro_autocut.resolve_api.connect()`.
- Produces: `sauberer_master(projekt: str, timeline: str, video: str, ziel: Path) -> dict` mit `master` (Pfad), `frames`,
  `fps`, `overlays` (Liste `{spur, start, ende, name}`), `einstellungen` (Liste `{id, spur, clip, start, ende}`), `user`,
  `kopie_geloescht`, `bin_geloescht`, `ansicht_zurueck`; Fehler als `ResolveFehler`.

- [ ] **Step 1: `tools/thumbnail/resolve_sauber.py` schreiben**

```python
"""Thumbnail, Resolve-Schritt: eigene Kopie einer Timeline ohne Overlays → Quick Export „ProRes 422 HQ“ → aufräumen.
Spec: docs/superpowers/specs/2026-09-21-thumbnail-design.md („Bildquelle“). Regeln: tools/resolve/WORKFLOW-Resolve.md.

Nur im offenen, exakt genannten Projekt. Legt Bin „Claude Thumbnail <Datum>“ und Timeline „Claude Thumbnail <Video>
<Datum>“ an, schaltet darin Alpha-Clips, Clips ohne Mediendatei (Titel, Generatoren) und SafeZone-Clips sowie alle
Untertitel-Spuren ab, rendert und löscht Kopie und Bin wieder. Timeline, Playhead, Bin und Seite des Users werden
zurückgesetzt, auch nach einem Fehler. Wartet, solange der User abspielt.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

STUDIO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402


class ResolveFehler(RuntimeError):
    pass


def _projekt(resolve):
    for _ in range(10):
        p = resolve.GetProjectManager().GetCurrentProject()
        if p is not None:
            return p
        time.sleep(1.0)
    raise ResolveFehler("Resolve liefert kein offenes Projekt.")


def _warten_bis_ruhe(proj, max_s: float = 300.0) -> None:
    t0 = time.time()
    while True:
        tl = proj.GetCurrentTimeline()
        if tl is None:
            return
        a = tl.GetCurrentTimecode()
        time.sleep(0.8)
        if tl.GetCurrentTimecode() == a:
            return
        if time.time() - t0 > max_s:
            raise ResolveFehler("Der User spielt seit 5 min ab — nichts geschrieben.")
        print("  Wiedergabe läuft — warte …", file=sys.stderr, flush=True)
        time.sleep(5)


def ist_overlay(item, spurname: str) -> bool:
    """Alpha-Clip (Remotion-Grafik/-Untertitel), Clip ohne Mediendatei (Text+, Titel, Generator) oder SafeZone-Spur."""
    if "SAFEZONE" in (spurname or "").upper():
        return True
    mpi = item.GetMediaPoolItem()
    if mpi is None:
        return True
    return (mpi.GetClipProperty("Alpha mode") or "None") not in ("None", "")


def einstellungen(tl, ausgenommen: set) -> list[dict]:
    """Sichtbare Einstellung je Frame = oberstes aktives Item, das kein Overlay ist → zusammenhängende Segmente."""
    start = int(tl.GetStartFrame())
    n = int(tl.GetEndFrame()) - start
    ebenen = []
    for k in range(int(tl.GetTrackCount("video")), 0, -1):
        for it in tl.GetItemListInTrack("video", k) or []:
            if it.GetUniqueId() in ausgenommen or not it.GetClipEnabled():
                continue
            ebenen.append((k, int(it.GetStart()) - start, int(it.GetEnd()) - start, it.GetName()))
    segmente: list[dict] = []
    for f in range(n):
        e = next((x for x in ebenen if x[1] <= f < x[2]), None)
        sid = f"V{e[0]}@{e[1]}" if e else "leer"
        if segmente and segmente[-1]["id"] == sid and segmente[-1]["ende"] == f:
            segmente[-1]["ende"] = f + 1
        else:
            segmente.append({"id": sid, "spur": f"V{e[0]}" if e else None, "clip": e[3] if e else None, "start": f, "ende": f + 1})
    return segmente


def _zuruecksetzen(proj, tl, tc) -> bool:
    if tl is None:
        return True
    ok = bool(proj.SetCurrentTimeline(tl))
    for _ in range(5):
        time.sleep(0.5)
        if not tc or tl.GetCurrentTimecode() == tc:
            break
        tl.SetCurrentTimecode(tc)
    return ok and (not tc or tl.GetCurrentTimecode() == tc)


def sauberer_master(projekt: str, timeline: str, video: str, ziel: Path) -> dict:
    resolve = RA.connect()
    proj = _projekt(resolve)
    if proj.GetName() != projekt:
        raise ResolveFehler(f"Offenes Projekt „{proj.GetName()}“ ≠ Freigabe „{projekt}“ — nichts geschrieben.")
    quelle = next((proj.GetTimelineByIndex(i) for i in range(1, proj.GetTimelineCount() + 1)
                   if proj.GetTimelineByIndex(i).GetName() == timeline), None)
    if quelle is None:
        raise ResolveFehler(f"Timeline „{timeline}“ fehlt.")
    _warten_bis_ruhe(proj)
    mp = proj.GetMediaPool()
    user_tl = proj.GetCurrentTimeline()
    user_tc = user_tl.GetCurrentTimecode() if user_tl else None
    user_bin = mp.GetCurrentFolder()
    user_seite = resolve.GetCurrentPage()
    anzahl = proj.GetTimelineCount()
    stempel = time.strftime("%Y-%m-%d %H%M")
    out: dict = {"projekt": proj.GetName(), "timeline": timeline,
                 "user": {"timeline": user_tl.GetName() if user_tl else None, "tc": user_tc,
                          "bin": user_bin.GetName() if user_bin else None, "seite": user_seite}}
    bin_ = kopie = None
    try:
        bin_ = mp.AddSubFolder(mp.GetRootFolder(), f"Claude Thumbnail {stempel}")
        if not bin_:
            raise ResolveFehler("Eigener Bin nicht angelegt.")
        mp.SetCurrentFolder(bin_)
        kopie = quelle.DuplicateTimeline(f"Claude Thumbnail {video} {stempel}")
        if not kopie:
            raise ResolveFehler("Kopie der Timeline nicht angelegt.")
        proj.SetCurrentTimeline(kopie)
        time.sleep(1.5)
        start = int(kopie.GetStartFrame())
        overlays, ids, fehler = [], set(), []
        for k in range(1, int(kopie.GetTrackCount("video")) + 1):
            spurname = kopie.GetTrackName("video", k)
            for it in kopie.GetItemListInTrack("video", k) or []:
                if not ist_overlay(it, spurname):
                    continue
                ids.add(it.GetUniqueId())
                overlays.append({"spur": f"V{k}", "start": int(it.GetStart()) - start, "ende": int(it.GetEnd()) - start,
                                 "name": it.GetName()})
                if it.GetClipEnabled():
                    it.SetClipEnabled(False)
                if it.GetClipEnabled():
                    fehler.append(f"V{k} {it.GetName()} @ {int(it.GetStart()) - start}")
        for k in range(1, int(kopie.GetTrackCount("subtitle")) + 1):
            kopie.SetTrackEnable("subtitle", k, False)
        if fehler:
            raise ResolveFehler(f"Overlays ließen sich nicht abschalten: {fehler[:5]}")
        out.update(frames=int(kopie.GetEndFrame()) - start, fps=float(kopie.GetSetting("timelineFrameRate")),
                   overlays=overlays, einstellungen=einstellungen(kopie, ids))
        ziel.mkdir(parents=True, exist_ok=True)
        name = f"{video}_sauber_{stempel.replace(' ', '_')}"
        res = proj.RenderWithQuickExport("ProRes 422 HQ", {"TargetDir": str(ziel), "CustomName": name, "EnableUpload": False})
        out["quick_export"] = res
        if (res or {}).get("JobStatus") != "Render Complete":
            raise ResolveFehler(f"Quick Export nicht fertig: {res}")
        dateien = sorted(ziel.glob(f"{name}*"))
        if len(dateien) != 1:
            raise ResolveFehler(f"Master nicht eindeutig: {dateien}")
        out["master"] = str(dateien[0])
    finally:
        out["ansicht_zurueck"] = _zuruecksetzen(proj, user_tl, user_tc)
        if kopie is not None:
            out["kopie_geloescht"] = bool(mp.DeleteTimelines([kopie]))
        if bin_ is not None:
            out["bin_geloescht"] = bool(mp.DeleteFolders([bin_]))
        if user_bin is not None:
            mp.SetCurrentFolder(user_bin)
        if user_seite and resolve.GetCurrentPage() != user_seite:
            resolve.OpenPage(user_seite)
        out["timelines_danach"] = proj.GetTimelineCount()
    if out["timelines_danach"] != anzahl or not out.get("kopie_geloescht") or not out.get("bin_geloescht"):
        raise ResolveFehler(f"Aufräumen unvollständig: {out}")
    return out
```

- [ ] **Step 2: API-Namen gegen die Stubs prüfen** (`search_scripting_api`: `DuplicateTimeline`, `SetTrackEnable`,
  `DeleteTimelines`, `DeleteFolders`, `GetUniqueId`, `SetClipEnabled`).

- [ ] **Step 3: Live-Test an „0 - Tagesessen_V2“** (Projekt „Setzer Reels Charge 2“, freigegeben 21.09.):

Run: `tools/autocut/venv/bin/python -c "import sys,json; sys.path.insert(0,'tools/thumbnail'); import resolve_sauber as R; from pathlib import Path; print(json.dumps(R.sauberer_master('Setzer Reels Charge 2','0 - Tagesessen_V2','0 - Tagesessen',Path('<scratch>')), ensure_ascii=False, default=str))"`
Expected: `master` existiert (286 Frames, 2160×3840), `overlays` = 3 (V4 ×1, V5 ×2), `einstellungen` = 2 Segmente,
`kopie_geloescht`/`bin_geloescht`/`ansicht_zurueck` = true; Resolve danach per MCP lesen: 104 Timelines, Ansicht wie vorher.

---

### Task 4: CLI `thumbnail.py`

**Files:**
- Create: `tools/thumbnail/thumbnail.py`

**Interfaces:**
- Consumes: `auswahl` (Task 1), `bin/bewerten` (Task 2), `resolve_sauber.sauberer_master` (Task 3).
- Produces: `thumbnail.py vorschlagen …` / `thumbnail.py ablegen …` (Aufruf im Modul-Docstring), Nachweis-JSON
  `<Charge>/_intern/thumbnails/<Video>_V<n>.json` mit `kandidaten`, `vorschlaege`, `pruefung`, `master`, `exportordner`, `abgelegt`.

- [ ] **Step 1: `tools/thumbnail/thumbnail.py` schreiben**

```python
"""Thumbnail — saubere Standbilder aus fertigen Videos (Studio-Funktion „Thumbnail:“, nur auf Wunsch des Users).
Spec docs/superpowers/specs/2026-09-21-thumbnail-design.md · Ablauf tools/thumbnail/WORKFLOW-Thumbnail.md

Aufruf (autocut-venv, im Repo):
  thumbnail.py vorschlagen "<Charge>" --video "<Titel>" --exportordner "<…/04_Exportiert>"
               (--timeline "<Resolve-Timeline>" --projekt "<Resolve-Projekt>" | --datei <saubere Videodatei>) [--version V<n>]
      → sauberer Master, Prüfung gegen den Export, Kandidaten (jeder 5. Frame), Vision-Bewertung,
        Kontaktbogen _intern/thumbnails/<Video>_V<n>_kandidaten.jpg, Nachweis _intern/thumbnails/<Video>_V<n>.json
  thumbnail.py ablegen "<Charge>" --video "<Titel>" [--version V<n>] [--wahl <Frame,Frame,Frame>] [--grund "…"]
      → je Vorschlag JPG (lange Kante 1920) + _4K nach Ergebnisse/Thumbnails/<Video>/ und <Exportordner>/<Video>/Thumbnails/,
        nie überschreiben (Nummern zählen weiter), danach Master und Kandidaten löschen.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms, ImageDraw, ImageFont

HIER = Path(__file__).resolve().parent
STUDIO = HIER.parents[1]
sys.path.insert(0, str(HIER))
import auswahl as A  # noqa: E402

SCHRITT = 5
BEWERTER = HIER / "bin" / "bewerten"
SCHRIFT = "/System/Library/Fonts/Helvetica.ttc"
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


def charge_pfad(charge: str) -> Path:
    p = Path(charge)
    return p if p.is_absolute() else STUDIO / p


def probe(datei: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate,nb_frames", "-of", "json", str(datei)],
                         capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]
    z, n = s["r_frame_rate"].split("/")
    frames = int(s.get("nb_frames") or 0)
    if not frames:
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
                              "stream=nb_read_frames", "-of", "csv=p=0", str(datei)], capture_output=True, text=True, check=True)
        frames = int(out.stdout.strip())
    return {"breite": int(s["width"]), "hoehe": int(s["height"]), "fps": int(z) / int(n), "frames": frames}


def tc(frame: int, fps: float) -> str:
    f = int(round(fps))
    s = frame // f
    return f"00:{s // 60:02d}:{s % 60:02d}:{frame % f:02d}"


def bewerter() -> Path:
    quelle = HIER / "bewerten.swift"
    if not BEWERTER.exists() or BEWERTER.stat().st_mtime < quelle.stat().st_mtime:
        BEWERTER.parent.mkdir(exist_ok=True)
        subprocess.run(["swiftc", "-O", str(quelle), "-o", str(BEWERTER)], check=True)
    return BEWERTER


def lap_var(a: np.ndarray) -> float:
    if a.shape[0] < 5 or a.shape[1] < 5:
        return 0.0
    return float((a[1:-1, 1:-1] * 4 - a[:-2, 1:-1] - a[2:, 1:-1] - a[1:-1, :-2] - a[1:-1, 2:]).var())


def frame_rgb(datei: Path, frame: int, fps: float) -> Image.Image:
    """Genau dieser Frame als RGB (BT.709 → sRGB-Werte). Suche per -ss knapp vor dem Frame (ProRes ist Intra-only)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, (frame - 0.25) / fps):.4f}", "-i", str(datei),
                          "-frames:v", "1", "-vf", "scale=iw:ih:in_color_matrix=bt709,format=rgb24",
                          "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(raw)).convert("RGB")


def kandidaten_extrahieren(master: Path, ziel: Path) -> list[int]:
    """Jeder SCHRITT-te Frame als JPG, lange Kante 1920; Datei k_<i>.jpg ↔ Frame i·SCHRITT."""
    ziel.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(master), "-vf",
                    f"select='not(mod(n\\,{SCHRITT}))',scale='if(gt(iw,ih),1920,-2)':'if(gt(iw,ih),-2,1920)'"
                    ":flags=lanczos:in_color_matrix=bt709:out_color_matrix=bt601:out_range=pc,format=yuvj420p",
                    "-fps_mode", "passthrough", "-q:v", "3", "-start_number", "0", str(ziel / "k_%05d.jpg")], check=True)
    return [int(p.stem[2:]) * SCHRITT for p in sorted(ziel.glob("k_*.jpg"))]


def bewerten_ordner(ordner: Path) -> dict[str, dict]:
    out = subprocess.run([str(bewerter()), str(ordner)], capture_output=True, text=True, check=True).stdout
    return {z["datei"]: z for z in (json.loads(l) for l in out.splitlines() if l.startswith("{"))}


def schaerfe(pfad: Path, gesicht: dict | None) -> float:
    im = Image.open(pfad).convert("L")
    w, h = im.size
    if gesicht:
        x0, y0, x1, y1 = gesicht["box"]
        dx, dy = (x1 - x0) * 0.1, (y1 - y0) * 0.1
        box = (max(0, int((x0 - dx) * w)), max(0, int((y0 - dy) * h)), min(w, int((x1 + dx) * w)), min(h, int((y1 + dy) * h)))
    else:
        box = (int(w * 0.2), int(h * 0.2), int(w * 0.8), int(h * 0.8))
    return lap_var(np.asarray(im.crop(box), dtype=np.float32))


def schnitte_aus_datei(datei: Path, frames: int) -> list[dict]:
    """Einstellungen einer Videodatei per ffmpeg scdet (Schwelle 10)."""
    err = subprocess.run(["ffmpeg", "-nostats", "-i", str(datei), "-vf", "scdet=threshold=10", "-an", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    fps = probe(datei)["fps"]
    starts = sorted({0} | {int(round(float(t) * fps)) for t in re.findall(r"lavfi\.scd\.time:\s*([\d.]+)", err)})
    grenzen = starts + [frames]
    return [{"id": f"S{i}", "spur": None, "clip": None, "start": a, "ende": b} for i, (a, b) in enumerate(zip(grenzen, grenzen[1:])) if b > a]


def _grau(datei: Path, frames: list[int], breite: int = 270, hoehe: int = 480) -> list[np.ndarray]:
    sel = "+".join(f"eq(n\\,{f})" for f in frames)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(datei), "-vf", f"select='{sel}',scale={breite}:{hoehe},format=gray",
                          "-fps_mode", "passthrough", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return [np.frombuffer(raw[i * breite * hoehe:(i + 1) * breite * hoehe], np.uint8) for i in range(len(raw) // (breite * hoehe))]


def ssim_je_frame(sauber: Path, export: Path, frames: list[int]) -> list[float]:
    sel = "+".join(f"eq(n\\,{f})" for f in frames)
    with tempfile.TemporaryDirectory() as tmp:
        stats = Path(tmp) / "ssim.txt"
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(sauber), "-i", str(export), "-lavfi",
                        f"[0:v]select='{sel}',scale=1080:1920:flags=lanczos,format=yuv420p,setpts=N/TB[a];"
                        f"[1:v]select='{sel}',scale=1080:1920:flags=lanczos,format=yuv420p,setpts=N/TB[b];"
                        f"[a][b]ssim=stats_file={stats}", "-f", "null", "-"], check=True)
        return [float(re.search(r"All:([0-9.]+)", z).group(1)) for z in stats.read_text().splitlines() if "All:" in z]


def pruefen(master: Path, export: Path | None, overlays: list[dict] | None, frames: int, fps: float) -> dict:
    """Quelle = Video (Spec „Prüfung“) und Detail-Faktor. Bricht bei Abweichung ab."""
    p: dict = {}
    if export and export.exists():
        ef = probe(export)["frames"]
        if ef != frames:
            raise SystemExit(f"Export {export.name} hat {ef} Frames, die Quelle {frames} — Version/Timeline prüfen.")
        belegt = set()
        for o in overlays or []:
            belegt.update(range(o["start"], o["ende"]))
        frei = [f for f in range(frames) if f not in belegt] if overlays is not None else []
        if frei:
            probe_frames = [frei[int(i * (len(frei) - 1) / 7)] for i in range(8)] if len(frei) >= 8 else frei
            werte = ssim_je_frame(master, export, sorted(set(probe_frames)))
            med = float(np.median(werte))
            p.update(art="freie Frames", frames=sorted(set(probe_frames)), ssim=[round(w, 4) for w in werte], median=round(med, 4))
            if med < 0.95:
                raise SystemExit(f"Saubere Quelle weicht vom Export ab (SSIM-Median {med:.3f} < 0,95 in freien Frames).")
        else:
            probe_frames = [int(i * (frames - 1) / 11) for i in range(12)]
            werte = ssim_je_frame(master, export, probe_frames)
            a, b = _grau(master, probe_frames), _grau(export, probe_frames)
            luma = float(np.mean([abs(x.mean() - y.mean()) / max(y.mean(), 1) for x, y in zip(a, b)]))
            med = float(np.median(werte))
            p.update(art="alle Frames", frames=probe_frames, ssim=[round(w, 4) for w in werte], median=round(med, 4),
                     luma_abweichung=round(luma, 4))
            if med < 0.80 or luma > 0.03:
                raise SystemExit(f"Saubere Quelle weicht vom Export ab (SSIM-Median {med:.3f}, Luma {luma:.1%}).")
    else:
        p["art"] = "kein Export zum Vergleich"
    detail = []
    for f in (int(frames * 0.3), int(frames * 0.5), int(frames * 0.7)):
        g = np.asarray(frame_rgb(master, f, fps).convert("L"), dtype=np.float32)
        h, w = g.shape
        c = g[int(h * 0.1):int(h * 0.5), int(w * 0.25):int(w * 0.75)]
        ci = Image.fromarray(c.astype(np.uint8))
        du = np.asarray(ci.resize((ci.width // 2, ci.height // 2), Image.LANCZOS).resize(ci.size, Image.LANCZOS), dtype=np.float32)
        detail.append(round(lap_var(c) / max(lap_var(du), 1e-6), 2))
    p["detail_faktor"] = detail
    if min(detail) < 1.15:
        p["warnung"] = "Detail-Faktor < 1,15 — womöglich aus Proxys gerendert"
    return p


def kontaktbogen(bogen: list[dict], vorschlaege: list[dict], kand_dir: Path, ziel: Path, titel: str) -> None:
    W, H, spalten, kopf, text_h = 270, 480, 6, 56, 74
    zeilen = -(-len(bogen) // spalten)
    b = Image.new("RGB", (W * spalten, kopf + zeilen * (H + text_h)), (18, 18, 18))
    d = ImageDraw.Draw(b)
    gross, klein = ImageFont.truetype(SCHRIFT, 24), ImageFont.truetype(SCHRIFT, 16)
    d.text((10, 14), f"{titel} — Kandidaten (rot = Vorschlag)", font=gross, fill=(240, 240, 240))
    for i, k in enumerate(bogen):
        x, y = (i % spalten) * W, kopf + (i // spalten) * (H + text_h)
        b.paste(Image.open(kand_dir / f"k_{k['frame'] // SCHRITT:05d}.jpg").resize((W, H), Image.LANCZOS), (x, y))
        nr = next((j + 1 for j, v in enumerate(vorschlaege) if v["frame"] == k["frame"]), None)
        if nr:
            d.rectangle([x + 1, y + 1, x + W - 2, y + H - 2], outline=(227, 6, 19), width=5)
            d.text((x + 10, y + 8), f"_{nr}", font=gross, fill=(227, 6, 19))
        g = A.hauptgesicht(k.get("gesichter") or [])
        q = f"Q {g['qualitaet']:.2f}" if g and g.get("qualitaet") is not None else "Q –"
        d.text((x + 6, y + H + 4), f"#{k['frame']}  {k['tc']}  {k['art']}", font=klein, fill=(235, 235, 235))
        d.text((x + 6, y + H + 24), f"P {k['punkte']:.2f} · Ä {k['aesthetik']:.2f} · {q} · S {k['schaerfe_n']:.2f}", font=klein, fill=(200, 200, 200))
        d.text((x + 6, y + H + 44), ", ".join(k["gruende"])[:40], font=klein, fill=(255, 150, 120))
    ziel.parent.mkdir(parents=True, exist_ok=True)
    b.save(ziel, quality=88)


def vorschlagen(a: argparse.Namespace) -> None:
    charge = charge_pfad(a.charge)
    intern = charge / "_intern" / "thumbnails"
    work = intern / "work"
    video_ordner = Path(a.exportordner) / a.video
    version = a.version or A.hoechste_version([p.name for p in video_ordner.glob("*.mp4")], a.video)
    if not version:
        raise SystemExit(f"Keine Exportversion in {video_ordner} — --version angeben.")
    basis = f"{a.video}_{version}"
    nachweis_pfad = intern / f"{basis}.json"
    if nachweis_pfad.exists():
        alt = json.loads(nachweis_pfad.read_text())
        if not alt.get("abgelegt"):
            raise SystemExit(f"Offene Runde für {basis} (Nachweis ohne Ablage) — erst ablegen oder den Nachweis prüfen.")
        nachweis_pfad.rename(intern / f"{basis}_bis_{time.strftime('%Y-%m-%d_%H%M')}.json")
    t0 = time.time()
    if a.timeline:
        import resolve_sauber as R
        if not a.projekt:
            raise SystemExit("--timeline braucht --projekt (exakter Name des freigegebenen Resolve-Projekts).")
        quelle = R.sauberer_master(a.projekt, a.timeline, a.video, work)
        master, segmente, overlays = Path(quelle["master"]), quelle["einstellungen"], quelle["overlays"]
    else:
        master = Path(a.datei)
        quelle, overlays = {"datei": str(master)}, None
        segmente = schnitte_aus_datei(master, probe(master)["frames"])
    info = probe(master)
    fps, frames = info["fps"], info["frames"]
    pruefung = pruefen(master, video_ordner / f"{basis}.mp4", overlays, frames, fps)
    kand_dir = work / f"{basis}_kandidaten"
    if kand_dir.exists():
        shutil.rmtree(kand_dir)
    nummern = kandidaten_extrahieren(master, kand_dir)
    bew = bewerten_ordner(kand_dir)
    schnitte = sorted({s["start"] for s in segmente if s["start"] > 0})
    kandidaten = []
    for f in nummern:
        datei = f"k_{f // SCHRITT:05d}.jpg"
        b = bew.get(datei) or {"fehler": "fehlt"}
        if "fehler" in b:
            continue
        gross = [g for g in b.get("gesichter", []) if g["box"][3] - g["box"][1] >= A.GESICHT_MIN_HOEHE]
        kandidaten.append({"frame": f, "zeit_s": round(f / fps, 2), "tc": tc(f, fps), "shot": A.shot_von(f, segmente),
                           "nahe_schnitt": A.nahe_schnitt(f, schnitte), "aesthetik": b.get("aesthetik") or 0.0,
                           "utility": bool(b.get("utility")), "gesichter": b.get("gesichter", []),
                           "schaerfe": round(schaerfe(kand_dir / datei, A.hauptgesicht(gross)), 2)})
    for k, n in zip(kandidaten, A.rang_normiert([k["schaerfe"] for k in kandidaten])):
        k["schaerfe_n"] = round(n, 4)
        A.bewerte(k)
    vorschlaege = A.waehle(kandidaten, fps)
    bogen_pfad = intern / f"{basis}_kandidaten.jpg"
    kontaktbogen(A.fuer_bogen(kandidaten, vorschlaege, fps), vorschlaege, kand_dir, bogen_pfad, f"{a.video} {version}")
    nachweis = {"video": a.video, "version": version, "charge": str(a.charge), "exportordner": str(a.exportordner),
                "angelegt": time.strftime("%Y-%m-%d %H:%M"), "quelle": {k: v for k, v in quelle.items() if k != "einstellungen"},
                "master": str(master), "master_eigen": bool(a.timeline), "fps": fps, "frames": frames,
                "aufloesung": [info["breite"], info["hoehe"]], "einstellungen": segmente, "pruefung": pruefung,
                "kandidaten": kandidaten, "vorschlaege": [v["frame"] for v in vorschlaege], "kandidaten_ordner": str(kand_dir),
                "kontaktbogen": str(bogen_pfad), "dauer_s": round(time.time() - t0, 1), "abgelegt": None}
    intern.mkdir(parents=True, exist_ok=True)
    nachweis_pfad.write_text(json.dumps(nachweis, indent=1, ensure_ascii=False, default=str))
    print(json.dumps({"video": a.video, "version": version, "kandidaten": len(kandidaten), "vorschlaege": nachweis["vorschlaege"],
                      "pruefung": pruefung, "kontaktbogen": str(bogen_pfad), "nachweis": str(nachweis_pfad),
                      "dauer_s": nachweis["dauer_s"]}, ensure_ascii=False, default=str))


def speichern(bild: Image.Image, ziel: Path, lange_kante: int | None) -> None:
    if lange_kante and max(bild.size) != lange_kante:
        f = lange_kante / max(bild.size)
        bild = bild.resize((round(bild.width * f), round(bild.height * f)), Image.LANCZOS)
    bild.save(ziel, "JPEG", quality=92, optimize=True, icc_profile=SRGB, subsampling=0)


def ablegen(a: argparse.Namespace) -> None:
    charge = charge_pfad(a.charge)
    intern = charge / "_intern" / "thumbnails"
    kandidaten_json = [p for p in intern.glob(f"{a.video}_V*.json") if "_bis_" not in p.name]
    if a.version:
        nachweis_pfad = intern / f"{a.video}_{a.version}.json"
    elif kandidaten_json:
        nachweis_pfad = max(kandidaten_json, key=lambda p: int(re.search(r"_V(\d+)\.json$", p.name).group(1)))
    else:
        raise SystemExit(f"Kein Nachweis für {a.video} — erst vorschlagen.")
    n = json.loads(nachweis_pfad.read_text())
    if n.get("abgelegt"):
        raise SystemExit(f"{nachweis_pfad.name} ist schon abgelegt — für neue Bilder erst vorschlagen.")
    master = Path(n["master"])
    if not master.exists():
        raise SystemExit(f"Master fehlt: {master}")
    wahl = [int(x) for x in a.wahl.split(",")] if a.wahl else n["vorschlaege"]
    if any(not 0 <= f < n["frames"] for f in wahl):
        raise SystemExit(f"Frame außerhalb 0–{n['frames'] - 1}: {wahl}")
    studio_dir = charge / "Ergebnisse" / "Thumbnails" / a.video
    nas_dir = Path(n["exportordner"]) / a.video / "Thumbnails"
    studio_dir.mkdir(parents=True, exist_ok=True)
    nas_dir.mkdir(parents=True, exist_ok=True)
    vorhanden = [p.name for d in (studio_dir, nas_dir) for p in d.iterdir()]
    start = A.naechste_nummer(vorhanden, a.video, n["version"])
    kand = {k["frame"]: k for k in n["kandidaten"]}
    abgelegt = []
    for i, f in enumerate(wahl):
        bild = frame_rgb(master, f, n["fps"])
        varianten = [(False, 1920)] + ([(True, None)] if max(bild.size) > 1920 else [])
        for vier_k, kante in varianten:
            name = A.dateiname(a.video, n["version"], start + i, vier_k)
            lokal, fern = studio_dir / name, nas_dir / name
            if lokal.exists() or fern.exists():
                raise SystemExit(f"{name} existiert schon — nichts überschrieben.")
            speichern(bild, lokal, kante)
            subprocess.run(["cp", "-n", str(lokal), str(fern)], check=True)
            if subprocess.run(["cmp", "-s", str(lokal), str(fern)]).returncode != 0:
                raise SystemExit(f"NAS-Kopie von {name} weicht ab.")
            with Image.open(lokal) as im:
                abgelegt.append({"datei": name, "frame": f, "tc": tc(f, n["fps"]), "groesse": list(im.size),
                                 "kb": round(lokal.stat().st_size / 1024), "punkte": (kand.get(f) or {}).get("punkte"),
                                 "art": (kand.get(f) or {}).get("art")})
    n["abgelegt"] = {"am": time.strftime("%Y-%m-%d %H:%M"), "wahl": wahl, "grund": a.grund,
                     "studio": str(studio_dir), "nas": str(nas_dir), "dateien": abgelegt}
    if n.get("master_eigen"):
        master.unlink()
    shutil.rmtree(n["kandidaten_ordner"], ignore_errors=True)
    nachweis_pfad.write_text(json.dumps(n, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(n["abgelegt"], ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="befehl", required=True)
    v = sub.add_parser("vorschlagen")
    v.add_argument("charge")
    v.add_argument("--video", required=True)
    v.add_argument("--exportordner", required=True)
    v.add_argument("--timeline")
    v.add_argument("--projekt")
    v.add_argument("--datei")
    v.add_argument("--version")
    ab = sub.add_parser("ablegen")
    ab.add_argument("charge")
    ab.add_argument("--video", required=True)
    ab.add_argument("--version")
    ab.add_argument("--wahl")
    ab.add_argument("--grund")
    a = ap.parse_args()
    if a.befehl == "vorschlagen":
        if bool(a.timeline) == bool(a.datei):
            raise SystemExit("Genau eine Quelle angeben: --timeline (mit --projekt) oder --datei.")
        vorschlagen(a)
    else:
        ablegen(a)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Frame-Genauigkeit prüfen** — `frame_rgb` (Suche per `-ss`) gegen `select=eq(n\,N)` an 3 Frames eines
  Masters vergleichen: Pixel identisch.

- [ ] **Step 3: End-to-End an „0 - Tagesessen_V2“** (Export V2) mit `vorschlagen`, Kontaktbogen ansehen, Schwellen
  (Augen, Mund) an echten Werten kalibrieren, Tests anpassen falls Konstanten sich ändern, dann `ablegen`.

---

### Task 5: Workflow, CLAUDE.md, Setzer-Lauf

**Files:**
- Create: `tools/thumbnail/WORKFLOW-Thumbnail.md`
- Modify: `CLAUDE.md` (Intro „zehn Funktionen“, Projektstruktur `Thumbnails/`, Tabellenzeile, Umgebung)
- Modify: `projects/Setzer/Social-Reels/2026-09 Dreh 11.09/Protokoll.md`

- [ ] **Step 1: `WORKFLOW-Thumbnail.md` schreiben** (Trigger, Regel „nur auf Wunsch“, Voraussetzungen, Ablauf mit
  Befehlen, Blick auf den Kontaktbogen, Bericht, Fehlerbilder).
- [ ] **Step 2: CLAUDE.md ergänzen** (Tabellenzeile + Struktur + Umgebung).
- [ ] **Step 3: Setzer: alle 6 Reels** (0 V2, 08/09/12 V4 aus `…_V3`, 15 V1, 16 V2) vorschlagen → Bögen ansehen →
  ablegen; Resolve danach lesen (Timelines 104, Ansicht wie vorher).
- [ ] **Step 4: Protokoll-Eintrag, `studio_abgleich.sh --charge`, Bericht im Chat.**
