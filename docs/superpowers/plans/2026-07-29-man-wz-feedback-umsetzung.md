# MAN Wartezimmervideo — Feedback-Umsetzung (Runde 1+2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Das 16:9-Master auf Davids V2-Schnitt umbauen: Quer-Vollbild-Strecken mit Masken-Blende, Löwe mit Blick-nach-rechts-Regel, CTA-Endcard mit QR, neue Texte, Untertitel-Fassung — Master 175,0 s.

**Architecture:** Zwei Videoebenen (Haupt 9:16 mit Ton im Fenster; Quer 16:9 fullscreen unter einer animierten clip-path-Blende). Alle Zeiten/Texte kommen wie bisher aus `build_sync_plan.py` → `sync-plan.json`; `Composition.tsx` (Sektion 6, `ManWz169Master`) rendert datengetrieben.

**Tech Stack:** Remotion 4 (tools/motion, Comp-ID `man-wz-169-master`), Python 3 stdlib + Pillow/fontTools im transcribe-venv, ffmpeg/ffprobe.

**Spec:** `docs/superpowers/specs/2026-07-29-man-wartezimmervideo-kundenfeedback-design.md`

## Global Constraints

- **zsh splittet Variablen NICHT** — ffmpeg/Remotion-Flags immer ausschreiben, nie `$FLAGS`.
- Python immer `tools/transcribe/venv/bin/python` (relativ zur Studio-Wurzel `/Users/jansantos/NIRO Studio`).
- Composition-ID im CLI ist `man-wz-169-master`, nicht `ManWz169Master`.
- Alle Wortlaute EXAKT aus der Spec übernehmen, `**wort**` = rot.
- Quer-Strecken (Video-Zeit): **64,56–76,56** (Frames 1614–1913) und **133,52–164,92** (Frames 3338–4122). Schwarzblende im Material ab 163,92. Master: **175,0 s / 4375 Frames**, Video-Ebene 4124 Frames.
- Löwe blickt IMMER nach rechts ⇒ steht IMMER links; nur in den zwei Musikparts + Endcard. Kein dauerhafter Löwe mehr in Sprech-Blöcken.
- Kein Berufstitel auf der Endcard (sonst m/w/d-Pflicht).
- Media-Dateien (`.mov`) werden NICHT committet (Repo ignoriert sie; `git status` nach jedem Task prüfen).
- Lara: Untertitel dürfen den Bewerben-Satz jetzt zeigen; Takeaway 9 bleibt unverändert, nur `endeStumm` geht aufs Blockende.

---

### Task 1: ProRes-Arbeitskopien aus den V2-Dateien

**Files:**
- Create: `tools/motion/public/clients/man/wz/wz-v2-haupt-1080.mov` (ProRes 422, 1080×1920, PCM-Ton)
- Create: `tools/motion/public/clients/man/wz/wz-v2-quer-a-2160.mov` (ProRes 422, 3840×2160, 300 F, stumm)
- Create: `tools/motion/public/clients/man/wz/wz-v2-quer-b-2160.mov` (ProRes 422, 3840×2160, 785 F, stumm)

**Interfaces:**
- Consumes: `projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/Material/V2 Videodateien/MAN Wartezimmervideo_V2 Haupt.mp4` + `…_V2 Quer.mp4` (HEVC 10-bit, verifiziert in Spec §1)
- Produces: die drei Dateinamen oben — Task 4 referenziert sie wörtlich per `staticFile()`. Haupt behält die volle Länge (4124 F); die Quer-Clips sind auf die Strecken getrimmt, sodass in der Composition `startFrom=0` gilt.

- [ ] **Step 1: Quellstabilität prüfen** (Dateien fertig kopiert?)

```bash
cd "/Users/jansantos/NIRO Studio/projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/Material/V2 Videodateien"
ls -la "MAN Wartezimmervideo_V2 Haupt.mp4" "MAN Wartezimmervideo_V2 Quer.mp4"
sleep 15
ls -la "MAN Wartezimmervideo_V2 Haupt.mp4" "MAN Wartezimmervideo_V2 Quer.mp4"
```

Expected: Byte-Größen identisch zwischen beiden Aufrufen (338686382 / 210588353).

- [ ] **Step 2: Haupt transkodieren** (volle Länge, 1080×1920 — im 4K-Render ist das Fenster exakt 1080×1920, die Kopie also 1:1)

```bash
cd "/Users/jansantos/NIRO Studio"
ffmpeg -y -i "projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/Material/V2 Videodateien/MAN Wartezimmervideo_V2 Haupt.mp4" -vf "scale=1080:1920:flags=lanczos" -c:v prores_ks -profile:v 2 -pix_fmt yuv422p10le -c:a pcm_s16le -ar 48000 "tools/motion/public/clients/man/wz/wz-v2-haupt-1080.mov"
```

- [ ] **Step 3: Quer-Strecken frame-genau trimmen** (Output-Seeking = frame-exakt; nativ 3840×2160 belassen)

```bash
cd "/Users/jansantos/NIRO Studio"
ffmpeg -y -i "projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/Material/V2 Videodateien/MAN Wartezimmervideo_V2 Quer.mp4" -ss 64.56 -to 76.56 -an -c:v prores_ks -profile:v 2 -pix_fmt yuv422p10le "tools/motion/public/clients/man/wz/wz-v2-quer-a-2160.mov"
ffmpeg -y -i "projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/Material/V2 Videodateien/MAN Wartezimmervideo_V2 Quer.mp4" -ss 133.52 -to 164.92 -an -c:v prores_ks -profile:v 2 -pix_fmt yuv422p10le "tools/motion/public/clients/man/wz/wz-v2-quer-b-2160.mov"
```

- [ ] **Step 4: Verifizieren** (Framezahlen, Ton, kein Schwarzstart)

```bash
cd "/Users/jansantos/NIRO Studio/tools/motion/public/clients/man/wz"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,nb_frames,r_frame_rate -of csv=p=0 wz-v2-haupt-1080.mov
ffprobe -v error -select_streams v:0 -show_entries stream=nb_frames -of csv=p=0 wz-v2-quer-a-2160.mov
ffprobe -v error -select_streams v:0 -show_entries stream=nb_frames -of csv=p=0 wz-v2-quer-b-2160.mov
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate -of csv=p=0 wz-v2-haupt-1080.mov
ffmpeg -v info -ss 0 -to 1 -i wz-v2-quer-a-2160.mov -vf blackdetect=d=0.2:pix_th=0.08 -an -f null - 2>&1 | grep blackdetect; echo "exit=$?"
```

Expected: `1080,1920,4124,25/1` · `300` · `785` · `pcm_s16le,48000` · blackdetect-grep leer (`exit=1`, erster Quer-Frame ist Inhalt, kein Schwarz).

- [ ] **Step 5: Kein Commit** — `git status` zeigt keine der drei `.mov` als trackbar (Media ignoriert). Falls doch: STOPP, `.gitignore` prüfen, nicht committen.

---

### Task 2: Löwen-Assets „Blick rechts" + QR-Asset (mit Decode-Test)

**Files:**
- Create: `tools/motion/public/clients/man/wz/loewe-rechts-dunkel.png`, `loewe-rechts-weiss.png` (Canvas 1200×2400, wie die Links-Varianten)
- Create: `projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/_intern/qr/build_qr.py`
- Create: `projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/_intern/qr/test_qr.py`
- Create: `tools/motion/public/clients/man/wz/qr-jobs-man-eu.png`

**Interfaces:**
- Consumes: vorhandenes `loewe-rechts-rot.png` (Blick-rechts-Vektor aus Phase 1) als Form-Quelle; Farbreferenzen aus `loewe-links-dunkel.png` / `loewe-links-weiss.png`.
- Produces: Dateinamen-Schema `loewe-rechts-{dunkel|rot|weiss}.png` — Task 4 lädt per `loewe-${blick}-${variante}.png`. QR-PNG mit weißer Platte inkl. Quiet Zone; Task 4 platziert es 480×480 (Design-px). Außerdem die gemessene Alpha-BBox der Rechts-PNGs für `LION_VIS_RECHTS` (Task 4, Step 2).

- [ ] **Step 1: Recolor-Skript schreiben und laufen lassen** (Form aus `loewe-rechts-rot.png`, Farben exakt aus den Links-PNGs gesampelt; BBox beider Richtungen ausgeben)

```bash
cd "/Users/jansantos/NIRO Studio" && tools/transcribe/venv/bin/python - <<'PY'
from PIL import Image
import os
WZ = "tools/motion/public/clients/man/wz"
form = Image.open(os.path.join(WZ, "loewe-rechts-rot.png")).convert("RGBA")
def dominante_farbe(pfad):
    im = Image.open(pfad).convert("RGBA")
    px = [p for p in im.getdata() if p[3] > 200]
    n = len(px)
    return tuple(round(sum(c[i] for c in px) / n) for i in range(3))
for name in ("dunkel", "weiss"):
    farbe = dominante_farbe(os.path.join(WZ, f"loewe-links-{name}.png"))
    r, g, b, a = form.split()
    voll = Image.new("RGBA", form.size, farbe + (255,))
    voll.putalpha(a)
    out = os.path.join(WZ, f"loewe-rechts-{name}.png")
    voll.save(out)
    print(name, "farbe", farbe, "size", voll.size)
for f in ("loewe-links-rot.png", "loewe-rechts-rot.png"):
    im = Image.open(os.path.join(WZ, f)).convert("RGBA")
    print(f, "bbox", im.getchannel("A").getbbox(), "size", im.size)
PY
```

Expected: `dunkel farbe (37, 47, 58)` (≈ #252F3A), `weiss farbe (255, 255, 255)`, size beide `(1200, 2400)`. BBox-Zeilen notieren: Links-BBox ≈ `(199, 506, 1094, 1895)`; die Rechts-BBox muss horizontal gespiegelt sein (left ≈ 1200−1094 = 106). **Weicht die Rechts-BBox stark ab (kein Spiegel), Werte trotzdem notieren — Task 4 Step 2 übernimmt die GEMESSENEN Zahlen.**

- [ ] **Step 2: QR-Abhängigkeiten ins venv**

```bash
cd "/Users/jansantos/NIRO Studio" && tools/transcribe/venv/bin/pip install segno opencv-python-headless numpy --quiet && tools/transcribe/venv/bin/python -c "import segno, cv2; print('ok', segno.__version__)"
```

Expected: `ok <version>`.

- [ ] **Step 3: Failing Test schreiben** — `_intern/qr/test_qr.py`

```python
# Prüft das erzeugte QR-Asset: dekodierbar und exakt die Ziel-URL.
import os, sys
import cv2

PNG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "..", "..",
    "tools", "motion", "public", "clients", "man", "wz", "qr-jobs-man-eu.png",
)

def main():
    assert os.path.exists(PNG), f"fehlt: {PNG}"
    img = cv2.imread(PNG)
    daten, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
    assert daten == "https://jobs.man.eu/", f"dekodiert: {daten!r}"
    h, w = img.shape[:2]
    assert min(h, w) >= 1000, f"zu klein fuer 4K-Downscale: {w}x{h}"
    print("QR OK:", daten, f"{w}x{h}")

if __name__ == "__main__":
    main()
```

Hinweis: `_intern/qr/` liegt unter `projects/` (gitignored) — Pfad zur Studio-Wurzel hat FÜNF `..`-Stufen (qr → _intern → Charge → Projekt → Kunde → projects → Wurzel ist eine zu viel; beim Anlegen mit `pwd`-Ausgabe gegenprüfen und die `..`-Kette so anpassen, dass `tools/motion/…` existiert).

- [ ] **Step 4: Test laufen lassen — muss fehlschlagen**

```bash
cd "/Users/jansantos/NIRO Studio/projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/_intern/qr" && "/Users/jansantos/NIRO Studio/tools/transcribe/venv/bin/python" test_qr.py
```

Expected: `AssertionError: fehlt: …qr-jobs-man-eu.png`

- [ ] **Step 5: Generator schreiben** — `_intern/qr/build_qr.py`

```python
# Erzeugt den Endcard-QR: EC-Level M, Quiet Zone 4 Module, dunkle Module
# auf weisser Platte. Skalierung so, dass die PNG-Kante >= 1000 px hat
# (Endcard 480 Design-px -> 960 echte px im 4K-Render, Downscale bleibt scharf).
import os
import segno

ZIEL = "https://jobs.man.eu/"
OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "..", "..",
    "tools", "motion", "public", "clients", "man", "wz", "qr-jobs-man-eu.png",
)

qr = segno.make(ZIEL, error="m")
seite = qr.symbol_size(border=4)[0]          # Module inkl. Quiet Zone
scale = -(-1000 // seite)                    # ceil auf >= 1000 px
qr.save(OUT, kind="png", scale=scale, border=4, dark="#1a1a1a", light="#ffffff")
print("gebaut:", os.path.abspath(OUT), "module", seite, "scale", scale)
```

(dieselbe `..`-Ketten-Prüfung wie in Step 3)

- [ ] **Step 6: Bauen + Test grün**

```bash
cd "/Users/jansantos/NIRO Studio/projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/_intern/qr" && "/Users/jansantos/NIRO Studio/tools/transcribe/venv/bin/python" build_qr.py && "/Users/jansantos/NIRO Studio/tools/transcribe/venv/bin/python" test_qr.py
```

Expected: `QR OK: https://jobs.man.eu/ <n>x<n>` mit n ≥ 1000.

- [ ] **Step 7: Kein Commit** (PNGs = Media, Skripte liegen unter `projects/` = gitignored). `git status` muss sauber bleiben.

---

### Task 3: Generator v9 — `build_sync_plan.py`

**Files:**
- Modify: `projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/_intern/final-16x9/build_sync_plan.py`
- Output: beide `sync-plan.json` (final-16x9 + `tools/motion/src/clients/man/projects/wartezimmervideo/`)

**Interfaces:**
- Consumes: `timeline.json` (12 Blöcke, UNVERÄNDERT), `transcript.scribe.json` (`{"words": [{"text","start","end"}...]}`, 335 Wörter).
- Produces: sync-plan v9 mit neuen Top-Level-Keys, die Task 4 liest:
  - `querStrecken`: Liste von 2 Objekten `{id, start, ende, frameVon, frameBis, oeffnungDauer: 0.6, schliessen: {start, dauer: 0.6, ziel: "zentriert"} | null, bleibtOffen: bool, schwarzAb: 163.92 | null}`
  - `untertitel`: Liste `{block, person, text, zeilen: [str, str?], start, ende, frameVon, frameBis}` — nur Fassung „stumm".
  - `loewe`: ersetzt durch `{blick: "rechts", auftritte: [{id, start, ende, seite: "links"}, …], endcard: {variante: "dunkel", seite: "links"}}`
  - geänderte `meta`: `masterDauer: 175.0`, `masterFrames: 4375`, `videoFrames: 4124`, `querStrecken`-Echo, kein `freezeBis` mehr.
  - `endcard`: Typen `blende-auf` (133,52), `schwarz` (163,92–164,92), `hero` (165,0–173,0, `kartentext: "GROSSES BEWEGEN **MIT MAN**"`, `cta: "JETZT BEWERBEN"`, `qr: {asset: "qr-jobs-man-eu.png", url: "JOBS.MAN.EU", groesse: 480}`), `ausklang` (173,0–175,0).
  - `spotlights`: `spotlight-1` unverändert (9,5–22,3) + `rest-spotlight` `{start: 75.5, ende: 89.9}` (Enter-Rampe liegt unsichtbar unter dem Vollbild; env ≈ 1 bei 76,56); der alte `spotlight-2` (64,6–89,9) entfällt. `werkzeugRegen.zone` = „Grafikfläche rechts".

- [ ] **Step 1: Konstanten ändern** (Zeilen 76–107)

```python
MASTER_DAUER = 175.0          # 4375 Frames (V2: Video 164,96 s + Endcard)
MASTER_FRAMES = 4375
VIDEO_FRAMES = 4124           # echte Framezahl wz-v2-haupt-1080.mov

QUER_1 = (64.56, 76.56)       # Quer-Strecke 1 (Frames 1614–1913), fix aus V2
QUER_2 = (133.52, 164.92)     # Finale (Frames 3338–4122), bleibt offen
QUER_VORLAUF = 0.16           # Grafik-Elemente enden >= 4 Frames vor der Blende
BLENDE_DAUER = 0.6            # Öffnen/Schließen je 15 Frames
SCHWARZ_AB = 163.92           # Schwarzblende im Material (Bild + Ton)

ENDCARD_HERO = 165.0          # CTA-Endcard aus dem Schwarz
ENDCARD_AUSKLANG = 173.0      # 8 s Standzeit (QR-Scan), dann Ausklang
```

`ENDCARD_START`, `FENSTER_AUS_DAUER`, `FENSTER_AUS_ENDE`, `FREEZE_BIS` ersatzlos löschen; alle Verwender folgen in Step 4/5. `SPOTLIGHT_2` (64,6/89,9) → `REST_SPOTLIGHT = (75.5, 89.9)`.

- [ ] **Step 2: Texte** (Zeilen 141–199)

```python
    "Nico":      "Teilelager & Teileverkauf",
```

```python
    {"kapitel": 3, "start": 89.9, "ende": 107.0,
     "kartentext": "FASZINATION **NUTZFAHRZEUGE**",
     "zeilen": ["FASZINATION", "**NUTZFAHRZEUGE**"]},
```

```python
    2:  {"kartentext": "**FAMILIÄRES** UMFELD",
         "zeilen": ["**FAMILIÄRES** UMFELD"]},
    5:  {"kartentext": "AUF **AUGENHÖHE**. FLACHE HIERARCHIESTUFEN.",
         "zeilen": ["AUF **AUGENHÖHE**.", "FLACHE HIERARCHIESTUFEN."]},
    10: {"kartentext": "GROSSE FAHRZEUGE. **GROSSES BEWEGEN**.",
         "zeilen": ["GROSSE FAHRZEUGE.", "**GROSSES BEWEGEN**."]},
```

Headline K2 `ende`: 64.8 → **64.4**. Headline K4: `start` 107.3 bleibt, `ende` 133.8 → **133.36**.

- [ ] **Step 3: Blenden-Kappung für Block 7 und 12** — nach dem Takeaway/Plaketten-Takt (dort, wo `takte_pausen` gelaufen ist) einfügen:

```python
    # --- Quer-Blenden-Anschluss: vor jeder Öffnung ist die Fläche textfrei ---
    for grenze in (QUER_1[0], QUER_2[0]):
        deadline = r1(grenze - QUER_VORLAUF)   # 64.4 bzw. 133.36
        for tw in takeaways:
            for key, aus in (("endeTon", None), ("endeStumm", None)):
                if tw[key] > deadline and tw["start"] < grenze:
                    tw[key] = deadline
            if tw["austritt"]["start"] + tw["austritt"]["dauer"] > deadline \
               and tw["start"] < grenze:
                tw["austritt"]["start"] = r1(deadline - tw["austritt"]["dauer"])
                tw["frameBisTon"] = f(deadline)
                tw["frameBisStumm"] = f(deadline)
        for p in plaketten:
            ende_p = p["austritt"]["start"] + p["austritt"]["dauer"]
            if ende_p > deadline and p["eintritt"]["start"] < grenze:
                p["austritt"]["start"] = r1(deadline - p["austritt"]["dauer"])
                p["frameBis"] = f(deadline)
```

- [ ] **Step 4: Lara-Sperre für Untertitel lockern + `endeStumm`** — die bestehende `LARA_SPERRE`-Logik bleibt für das TAKEAWAY der Ton-Fassung unangetastet; ergänzen:

```python
    # CTA-Umbau 2026-07-29: das Video ist jetzt Recruiting — Laras Satz darf
    # als TEXT erscheinen. Takeaway 9 bleibt wie abgenommen (endeTon 101.0),
    # nur die stumme Fassung deckt den Block voll.
    for tw in takeaways:
        if tw["block"] == 9:
            tw["endeStumm"] = r1(bloecke[8]["ende"] + TW_AUS_DAUER)   # 104.2
            tw["frameBisStumm"] = f(tw["endeStumm"])
```

- [ ] **Step 5: Spotlights/Löwe/Endcard/dichte ersetzen** — `spotlights`-Liste: Eintrag 1 unverändert, Eintrag 2 ersetzen durch:

```python
        {
            "id": "rest-spotlight", "typ": "spotlight",
            "start": REST_SPOTLIGHT[0], "ende": REST_SPOTLIGHT[1],
            "frameVon": f(REST_SPOTLIGHT[0]), "frameBis": f(REST_SPOTLIGHT[1]),
            "textfrei": True, "logofrei": True, "beats": [],
            "werkzeugRegen": werkzeug_regen,
            "hinweis": "Rest der Ex-Lücke 7 nach der Quer-Strecke: Enter-Rampe "
                       "75,5–76,4 liegt UNSICHTBAR unter dem Vollbild, damit "
                       "die Blende bei 76,56 auf die zentrierte Position "
                       "schließt. Löwe links, Werkzeuge rechts.",
        },
```

`werkzeug_regen["zone"] = "Grafikfläche rechts (x 820–1920); über dem zentrierten Fenster max. 40 % der Opazität"`. Flare-Beat entfällt (lag bei 76,0 mitten in der Quer-Strecke).

Neues `loewe`-Objekt, `querStrecken`, `endcard`, `dichte` (Kurvenpunkte auf 175 s, `{"t": 164.92, "amp": 0.3}`, `{"t": MASTER_DAUER, "amp": 0.3}`), `untertitel` (Step 6). Endcard-Einträge exakt nach Interfaces-Block oben; `loop`-Texte auf Frame 4374 umschreiben.

- [ ] **Step 6: Untertitel-Segmentierung** — neue Funktion vor `main()`:

```python
UT_MAX_ZEICHEN = 32           # pro Zeile, max 2 Zeilen
UT_MIN_STAND = 1.2

def untertitel_segmente(bloecke, log):
    """Untertitel für die stumme Fassung: Wortlaut aus timeline.json,
    Timing proportional über die Scribe-Wörter des Blocks verteilt."""
    with open(os.path.join(HERE, "transcript.scribe.json"), encoding="utf-8") as fh:
        scribe = json.load(fh)["words"]
    segmente = []
    for b in bloecke:
        woerter = [w for w in scribe
                   if b["start"] - 0.3 <= w["start"] <= b["ende"] + 0.3]
        text = b["text"]
        # Grob an Satzzeichen teilen, dann auf <= 2 Zeilen à 32 Zeichen packen
        import re
        teile = [s.strip() for s in re.split(r"(?<=[.!?…])\s+", text) if s.strip()]
        chunks = []
        for satz in teile:
            wl = satz.split()
            akt = []
            for w in wl:
                kandidat = " ".join(akt + [w])
                if len(kandidat) > 2 * UT_MAX_ZEICHEN and akt:
                    chunks.append(" ".join(akt)); akt = [w]
                else:
                    akt.append(w)
            if akt:
                chunks.append(" ".join(akt))
        gesamt = sum(len(c.split()) for c in chunks)
        cursor = 0
        for c in chunks:
            n = len(c.split())
            if woerter and gesamt:
                i0 = min(int(cursor / gesamt * len(woerter)), len(woerter) - 1)
                i1 = min(int((cursor + n) / gesamt * len(woerter)), len(woerter)) - 1
                s0 = woerter[i0]["start"]; s1 = woerter[max(i0, i1)]["end"]
            else:  # Fallback: proportional über die Blockdauer
                s0 = b["start"] + cursor / max(1, gesamt) * (b["ende"] - b["start"])
                s1 = b["start"] + (cursor + n) / max(1, gesamt) * (b["ende"] - b["start"])
            cursor += n
            # Zeilenumbruch: möglichst mittig, nie > 32 Zeichen
            wl = c.split(); zeilen = [c]
            if len(c) > UT_MAX_ZEICHEN:
                best = min(range(1, len(wl)),
                           key=lambda i: abs(len(" ".join(wl[:i])) - len(c) / 2))
                zeilen = [" ".join(wl[:best]), " ".join(wl[best:])]
            segmente.append({"block": b["idx"], "person": b["person"],
                             "text": c, "zeilen": zeilen,
                             "start": r1(s0), "ende": r1(max(s1, s0 + UT_MIN_STAND))})
        # Segment-Enden gegen Folgesegment abdichten
    for i, s in enumerate(segmente[:-1]):
        n = segmente[i + 1]
        if s["block"] == n["block"] and s["ende"] > n["start"] - 0.08:
            s["ende"] = r1(n["start"] - 0.08)
    for s in segmente:
        s["frameVon"] = f(s["start"]); s["frameBis"] = f(s["ende"])
    log("Untertitel: %d Segmente" % len(segmente))
    return segmente
```

In `main()` einhängen: `plan["untertitel"] = untertitel_segmente(bloecke, log)`.

- [ ] **Step 7: Beat-Prüfung auf 175 s + Quer-Fenster ausnehmen** — in der Fenster-Auswertung nach dem Sortieren der Events:

```python
    def in_quer(t0, t1):
        return any(q[0] - 0.2 <= t0 and t1 <= q[1] + 0.2 for q in (QUER_1, QUER_2))
    # Vollbild-Film IST Bewegtbild — Fenster innerhalb der Quer-Strecken
    # fliegen aus der 5-s-Prüfung raus.
```

Events ergänzen: `ev(q_start, "quer-blende-auf")`, `ev(q_ende, "quer-blende-zu")` für beide Strecken, `ev(SCHWARZ_AB, "schwarzblende")`; die Fensterliste vor der Warnungs-Schleife mit `in_quer` filtern.

- [ ] **Step 8: Laufen lassen + Asserts**

```bash
cd "/Users/jansantos/NIRO Studio/projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/_intern/final-16x9" && "/Users/jansantos/NIRO Studio/tools/transcribe/venv/bin/python" build_sync_plan.py
```

Expected: `BESTANDEN`, 0 Warnungen, „Untertitel: N Segmente" (N ≈ 25–40).

```bash
cd "/Users/jansantos/NIRO Studio/projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/_intern/final-16x9" && "/Users/jansantos/NIRO Studio/tools/transcribe/venv/bin/python" - <<'PY'
import json
p = json.load(open("sync-plan.json"))
m = p["meta"]
assert (m["masterDauer"], m["masterFrames"], m["videoFrames"]) == (175.0, 4375, 4124)
assert p["takeaways"][1]["kartentext"] == "**FAMILIÄRES** UMFELD"
assert p["takeaways"][4]["kartentext"] == "AUF **AUGENHÖHE**. FLACHE HIERARCHIESTUFEN."
assert p["takeaways"][9]["kartentext"] == "GROSSE FAHRZEUGE. **GROSSES BEWEGEN**."
assert "NUTZFAHRZEUGE" in p["headlines"][2]["kartentext"]
assert p["headlines"][1]["ende"] <= 64.4 and p["takeaways"][6]["endeTon"] <= 64.4
assert p["headlines"][3]["ende"] <= 133.36
assert p["plaketten"][6]["rolle"] == "Teilelager & Teileverkauf"
q = p["querStrecken"]
assert (q[0]["start"], q[0]["ende"], q[1]["start"], q[1]["ende"]) == (64.56, 76.56, 133.52, 164.92)
assert q[0]["schliessen"]["ziel"] == "zentriert" and q[1]["bleibtOffen"]
hero = [e for e in p["endcard"] if e["typ"] == "hero"][0]
assert (hero["start"], hero["ende"]) == (165.0, 173.0)
assert hero["kartentext"] == "GROSSES BEWEGEN **MIT MAN**" and hero["cta"] == "JETZT BEWERBEN"
assert p["loewe"]["blick"] == "rechts" and len(p["loewe"]["auftritte"]) == 2
lara = [u for u in p["untertitel"] if u["block"] == 9]
assert any("bewerben" in u["text"] for u in lara), "Lara-Satz fehlt in den UT"
assert all(u["ende"] - u["start"] >= 1.15 for u in p["untertitel"])
sp = [s["id"] for s in p["spotlights"]]
assert sp == ["spotlight-1", "rest-spotlight"]
print("PLAN-ASSERTS OK —", len(p["untertitel"]), "UT-Segmente")
PY
```

Expected: `PLAN-ASSERTS OK — <N> UT-Segmente`.

- [ ] **Step 9: Commit** (nur falls Generator-Kopie im Repo läge — liegt er nicht; `sync-plan.json` unter `tools/motion/src/...` IST im Repo):

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/motion/src/clients/man/projects/wartezimmervideo/sync-plan.json && git commit -m "feat(man-wz): sync-plan v9 — Quer-Strecken, CTA-Endcard, Löwe rechtsblickend, Untertitel, Master 175s"
```

---

### Task 4: Composition-Umbau `ManWz169Master`

**Files:**
- Modify: `tools/motion/src/clients/man/projects/wartezimmervideo/Composition.tsx` (Typen ab ~800, `Loewe169` :1029, `Spotlight169` :1297, `EndcardHero169` :1445, Master :1551–1922)
- Modify: `tools/motion/src/Root.tsx` (nichts — Dauer kommt aus `manWz169MasterDefaults`)

**Interfaces:**
- Consumes: sync-plan v9 (Task 3), Assets `wz-v2-haupt-1080.mov`, `wz-v2-quer-{a,b}-2160.mov`, `loewe-rechts-*.png`, `qr-jobs-man-eu.png` (Tasks 1–2).
- Produces: Comp `man-wz-169-master` mit 4375 Frames; Props unverändert (`fassung`, `ohneCiattei`).

- [ ] **Step 1: Typen + Defaults.** `SyncPlan169` um `querStrecken`, `untertitel`, neues `loewe`-Objekt erweitern; `EndcardEvent169.typ` um `"blende-auf" | "schwarz"`; `kartentext`/`cta`/`qr` am Hero. `manWz169MasterDefaults.durationInSeconds: 142` → `175`. Alte Keys `freezeBis`/`fenster.ausblendung`-Verwender entfernen.

- [ ] **Step 2: `Loewe169` richtungsfähig machen** — BBox-Konstanten pro Blickrichtung (Zahlen aus Task 2 Step 1 übernehmen, falls dort abweichend gemessen):

```tsx
const LION_VIS_L = { left: 199 / 1200, top: 506 / 2400, w: 895 / 1200, h: 1389 / 2400 };
const LION_VIS_R = { left: 106 / 1200, top: 506 / 2400, w: 895 / 1200, h: 1389 / 2400 };

const Loewe169: React.FC<{
  variante: "dunkel" | "rot" | "weiss";
  blick?: "links" | "rechts";       // MAN 2026-07-29: IMMER "rechts" verwenden
  visX: number; visY: number; visH: number;
  shiftX?: number; opacity?: number; filter?: string;
}> = ({ variante, blick = "rechts", visX, visY, visH, shiftX = 0, opacity = 1, filter }) => {
  const vis = blick === "rechts" ? LION_VIS_R : LION_VIS_L;
  const imgH = visH / vis.h;
  const imgW = imgH * 0.5;
  return (
    <Img
      src={staticFile(`clients/man/wz/loewe-${blick}-${variante}.png`)}
      style={{
        position: "absolute", width: imgW, height: imgH,
        left: visX - imgW * vis.left, top: visY - imgH * vis.top,
        transform: `translateX(${shiftX}px)`, opacity, filter,
      }}
    />
  );
};
```

- [ ] **Step 3: Spotlight — Löwe links, Werkzeuge rechts.** In `Spotlight169` den `<Werkzeuge>`-Block in einen Wrapper rechts setzen und den Löwen spiegeln:

```tsx
      <div style={{ position: "absolute", left: BASE_W - M_WERKZEUG_ZONE_W, top: 0 }}>
        <Werkzeuge
          progress={tLok / dauer}
          opacity={werkzeugOp * env}
          farbe={WHITE}
          zyklen={dauer / 26}
          breite={M_WERKZEUG_ZONE_W}
          hoehe={BASE_H}
        />
      </div>
      {/* Roter Löwe LINKS am Rand, Blick nach rechts (MAN 2026-07-29).
          Silhouette läuft links aus dem Bild (Anschnitt), Kopf zeigt ins Bild.
          Kalibrierung (Deckkraft 0,24, brightness 0,82, blur 3) unverändert. */}
      <Loewe169
        variante="rot"
        blick="rechts"
        visX={-240 + (1 - env) * -200}
        visY={20}
        visH={1180}
        shiftX={-M_SPOT_LOEWE_DRIFT + 2 * M_SPOT_LOEWE_DRIFT * (tLok / dauer)}
        opacity={0.24 * env}
        filter="brightness(0.82) blur(3px)"
      />
```

`M_SPOT_LOEWE_X`/`M_SPOT_LOEWE_WEG` löschen. Sichtkante: `visX=-240` schneidet die linke Rumpfpartie an; Kopf (rechte 55 % der Rechts-Silhouette) bleibt frei — Feinwert am Testframe.

- [ ] **Step 4: Dauerhaften dunklen Löwen entfernen** (Master :1661–1668 + `heroMask` :1618). David: Löwe NUR Musikparts + Endcard. `heroMask` ersatzlos streichen; Frame-0-Zustand ist jetzt reine Anthrazit-Fläche.

- [ ] **Step 5: Blenden-Geometrie + Fenster-Einheit.** Kern des Umbaus — vor dem `return` des Masters:

```tsx
  // --- Quer-Blende: Fensterrechteck ↔ Vollbild (clip-path auf der Quer-Ebene,
  //     Fenster-Einheit fährt dasselbe Rechteck) ---
  type Rect = { x: number; y: number; w: number; h: number };
  const lerpRect = (a: Rect, b: Rect, p: number): Rect => ({
    x: a.x + (b.x - a.x) * p, y: a.y + (b.y - a.y) * p,
    w: a.w + (b.w - a.w) * p, h: a.h + (b.h - a.h) * p,
  });
  const RECT_FULL: Rect = { x: 0, y: 0, w: BASE_W, h: BASE_H };
  let offen = 0;          // 0 = Fenster, 1 = Vollbild
  let querAktiv: (typeof PLAN169.querStrecken)[number] | null = null;
  for (const q of PLAN169.querStrecken) {
    if (t < q.start - 0.02 || t > q.ende + 1e-6) continue;
    querAktiv = q;
    const auf = interpolate(t, [q.start, q.start + q.oeffnungDauer], [0, 1],
      { ...CLAMP, easing: Easing.out(Easing.cubic) });
    const zu = q.schliessen
      ? interpolate(t, [q.schliessen.start, q.schliessen.start + q.schliessen.dauer],
          [1, 0], { ...CLAMP, easing: Easing.inOut(Easing.cubic) })
      : 1;
    offen = Math.min(auf, zu);
  }
  // Basisrechteck: folgt dem Spotlight-Glide (winX); die Blende interpoliert
  // von dort nach Vollbild. Öffnung 1 startet bei winX=1200 (spot=0), das
  // Schließen landet bei winX=690 (rest-spotlight env=1 ab 76,4).
  const RECT_WIN: Rect = { x: winX, y: M_WIN_Y, w: M_WIN_W, h: M_WIN_H };
  const boxRect = lerpRect(RECT_WIN, RECT_FULL, offen);
  // Spotlight-Scale nur im Fensterzustand (Vollbild-Footage nie skalieren)
  const effScale = 1 + (M_SPOT_SCALE - 1) * spot * (1 - offen);
  // Fenster-Hüllkurve NEU: nur noch Loop-Fade-in; die alte 133er-Ausblendung
  // ist durch die Blende ersetzt. Nach Videoende (164,92) trägt die Endcard.
  const winOp = interpolate(t, [fensterEin.start, fensterEin.start + fensterEin.dauer],
    [0, 1], { ...CLAMP, easing: Easing.out(Easing.cubic) });
```

Fenster-Einheit (:1687–1779) umbauen: äußere Div nutzt `boxRect` (`left/top/width/height`), `transform: scale(${effScale})`, Grund/Panel/Kantenbalken unverändert relativ zur Box, aber Panel + Kantenbalken zusätzlich `opacity: 1 - offen` (Vollbild randlos; Balken „wandert mit und blendet aus"). Videoinhalt der Box:

```tsx
              {/* Hochformat (Haupt) — überall außer in den Quer-Strecken */}
              {!querAktiv && (
                <Sequence durationInFrames={videoFrames}>
                  <OffthreadVideo
                    src={videoSrc}
                    muted={stumm}
                    style={{ width: "100%", height: "100%", objectFit: "cover" }}
                  />
                </Sequence>
              )}
              {/* Quer-Ebene: bildschirmfestes 1920×1080-Video, von der Box
                  maskiert — Kompensation hebt die Box-Position auf. */}
              {querAktiv && (
                <div style={{
                  position: "absolute",
                  left: -boxRect.x, top: -boxRect.y,
                  width: BASE_W, height: BASE_H,
                }}>
                  <Sequence
                    from={fr169(querAktiv.start) - /* Sequence-lokale Zeit! */ 0}
                    durationInFrames={fr169(querAktiv.ende) - fr169(querAktiv.start)}
                  >
                    <OffthreadVideo
                      src={staticFile(querAktiv.id === "quer-1"
                        ? "clients/man/wz/wz-v2-quer-a-2160.mov"
                        : "clients/man/wz/wz-v2-quer-b-2160.mov")}
                      muted
                      style={{ width: "100%", height: "100%" }}
                    />
                  </Sequence>
                </div>
              )}
```

WICHTIG (Freeze-Lektion 2026-07-26): Die Quer-`Sequence` liegt bereits in einer Box, die auf Root-Ebene gerendert wird — `from` muss der ABSOLUTE Frame `fr169(querAktiv.start)` sein, es sei denn, ein umgebender `<Sequence>` verschiebt die Zeitachse. Beim Einbau mit einem Kontroll-Still bei F1620 und F3340 verifizieren, dass der Clip bei seinem ERSTEN Frame beginnt (dunkle rote TGX-Front bzw. Alpenstraße, kein Sprung).

Ton: der Haupt-`OffthreadVideo` wird in den Quer-Strecken unmountet — der TON liegt aber im Haupt! Deshalb zusätzlich eine reine Audio-Instanz, die durchläuft:

```tsx
          {/* Ton-Träger: läuft IMMER (auch während der Quer-Strecken), Bild 0 px */}
          {!stumm && (
            <Sequence durationInFrames={videoFrames}>
              <OffthreadVideo src={videoSrc} style={{ width: 1, height: 1, opacity: 0 }} />
            </Sequence>
          )}
```

und der Fenster-`OffthreadVideo` bekommt dann IMMER `muted` (Bildspur), damit der Ton nur einmal spielt.

- [ ] **Step 6: Untertitel-Ebene (stumme Fassung)** — neue Komponente + Einbau in die Video-Box (unter dem Videoinhalt-`</div>`-Ende, innerhalb `overflow: hidden`):

```tsx
const Untertitel169: React.FC<{ u: UntertitelPlan169 }> = ({ u }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const total = Math.max(6, u.frameBis - u.frameVon);
  const ein = interpolate(frame, [0, 5], [0, 1], CLAMP);
  const aus = interpolate(frame, [total - 4, total - 1], [1, 0], CLAMP);
  return (
    <div style={{
      position: "absolute", left: 40, right: 40, bottom: 34,
      textAlign: "center", opacity: ein * aus,
    }}>
      {u.zeilen.map((z, i) => (
        <div key={i} style={{
          fontFamily: FONT_BODY, fontWeight: 400, fontSize: 30,
          lineHeight: 1.25, color: WHITE,
          textShadow: "0 1px 3px rgba(0,0,0,0.9), 0 0 14px rgba(0,0,0,0.6)",
        }}>{z}</div>
      ))}
    </div>
  );
};
```

Einbau (in der Box, nur Fensterzustand — in den Quer-Strecken gibt es keine Sprache):

```tsx
              {stumm && !querAktiv &&
                PLAN169.untertitel.map((u, i) => (
                  <Sequence key={`ut-${i}`} name={`UT ${u.block}`}
                    from={u.frameVon}
                    durationInFrames={Math.max(6, u.frameBis - u.frameVon)}>
                    <Untertitel169 u={u} />
                  </Sequence>
                ))}
```

Dazu ein Verlaufs-Band hinter den UT (im Box-Div, unter den Sequences): `position:absolute; left:0; right:0; bottom:0; height:150px; background: linear-gradient(rgba(11,17,23,0), rgba(11,17,23,0.55))`, `opacity` an `stumm && !querAktiv` gekoppelt. `FONT_BODY` existiert bereits (MAN Global Regular); falls der Bezeichner anders heißt, den vorhandenen Body-Font-Konstantennamen der Datei verwenden.

- [ ] **Step 7: Endcard `EndcardCta169`** — `EndcardHero169` ersetzen (alter Code raus):

```tsx
const M_CTA_X = 160;            // linke Spalte
const M_CTA_LOGO_Y = 250;
const M_CTA_LOGO_W = 300;
const M_CTA_CLAIM_Y = 470;
const M_CTA_CLAIM_PX = 96;
const M_CTA_BAR_Y = 700;
const M_CTA_BAR_W = 320;
const M_CTA_CTA_Y = 748;
const M_QR_GROESSE = 480;
const M_QR_X = 1920 - 180 - M_QR_GROESSE;   // rechte Spalte, Rand 180
const M_QR_Y = (1080 - M_QR_GROESSE) / 2 - 40;

const EndcardCta169: React.FC<{
  kartentext: string; cta: string; qrUrl: string;
  ausklangVon: number; ausklangDauer: number;
}> = ({ kartentext, cta, qrUrl, ausklangVon, ausklangDauer }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const bgIn = interpolate(frame, [0, 10], [0, 1], CLAMP);
  const logoIn = spring({ frame: frame - 6, fps, config: SMOOTH, durationInFrames: 18 });
  const textIn = spring({ frame: frame - 14, fps, config: SMOOTH, durationInFrames: 20 });
  const qrIn = spring({ frame: frame - 22, fps, config: SMOOTH, durationInFrames: 20 });
  const ausVon = Math.round(ausklangVon * fps);
  const ausBis = Math.round((ausklangVon + ausklangDauer) * fps);
  const exit = interpolate(frame, [ausVon, ausBis], [1, 0],
    { ...CLAMP, easing: Easing.inOut(Easing.cubic) });
  return (
    <AbsoluteFill style={{ backgroundColor: ANTHRAZIT, opacity: bgIn }}>
      {/* Dunkler Löwe LINKS hinter der Textspalte, Blick nach rechts → führt
          zu Claim + QR. Ton-in-Ton (Kontrast ≈ 13 %), Text bleibt lesbar. */}
      <Loewe169 variante="dunkel" blick="rechts"
        visX={-160} visY={140} visH={1150} opacity={0.68 * logoIn * exit} />
      <div style={{ opacity: exit }}>
        <div style={{ position: "absolute", left: M_CTA_X, top: M_CTA_LOGO_Y,
          opacity: logoIn, transform: `translateY(${(1 - logoIn) * 18}px)` }}>
          <ManLogo width={M_CTA_LOGO_W} />
        </div>
        <div style={{ position: "absolute", left: M_CTA_X, top: M_CTA_CLAIM_Y,
          width: 1000, opacity: textIn,
          transform: `translateY(${(1 - textIn) * 20}px)`,
          fontFamily: FONT_TITLE, fontWeight: 700, fontSize: M_CTA_CLAIM_PX,
          letterSpacing: 2, lineHeight: 1.08, color: WHITE,
          textTransform: "uppercase" }}>
          <Markup169 text={kartentext} />
        </div>
        <div style={{ position: "absolute", left: M_CTA_X, top: M_CTA_BAR_Y,
          width: M_CTA_BAR_W * textIn, height: 6, background: MAN_RED }} />
        <div style={{ position: "absolute", left: M_CTA_X, top: M_CTA_CTA_Y,
          opacity: textIn, fontFamily: FONT_TITLE, fontWeight: 700,
          fontSize: 54, letterSpacing: 3, color: WHITE,
          textTransform: "uppercase" }}>
          {cta}
        </div>
        <div style={{ position: "absolute", left: M_QR_X, top: M_QR_Y,
          opacity: qrIn, transform: `translateY(${(1 - qrIn) * 16}px)` }}>
          <Img src={staticFile("clients/man/wz/qr-jobs-man-eu.png")}
            style={{ width: M_QR_GROESSE, height: M_QR_GROESSE, display: "block" }} />
          <div style={{ marginTop: 18, textAlign: "center",
            fontFamily: FONT_TITLE, fontWeight: 700, fontSize: 30,
            letterSpacing: 4, color: WHITE }}>{qrUrl}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
```

Einbau im Master (ersetzt den alten Hero-Block :1854–1868): `Sequence from={fr169(165.0)} durationInFrames={fr169(175.0) − fr169(165.0)}`, Props aus dem `hero`-Endcard-Event (`kartentext`, `cta`, `qr.url` → `qrUrl`, `groesse` steckt in `M_QR_GROESSE`), `ausklangVon = 173.0 − 165.0`, `ausklangDauer = 1.6` (Elemente sind bei 174,6 weg, 0,4 s Reserve zur Naht). Das Schwarz aus dem Material (bis 164,92) liegt UNTER der Endcard; `bgIn` blendet Anthrazit in 0,4 s darüber. Loop-Naht: Frame 4374 = reine Anthrazit-Fläche = Frame 0 (Fenster-Fade-in beginnt erst bei F0+).

- [ ] **Step 8: Kleinkram.** `videoSrc` → `wz-v2-haupt-1080.mov`; `videoFrames` liest `meta.videoFrames` (4124); `freezeBisF`-Zeile löschen; `logoOp = winOp * (1 - spot) * (1 - offen)` (Vollbild logofrei); Face-Zone-Overlay zusätzlich `&& offen < 0.5`; alte `fensterAus`-Konstante und alle Verwender entfernen.

- [ ] **Step 9: Typecheck + Kontroll-Stills**

```bash
cd "/Users/jansantos/NIRO Studio/tools/motion" && npx tsc --noEmit
npx remotion still src/index.ts man-wz-169-master /tmp/wzv3-f1620.png --frame=1620
npx remotion still src/index.ts man-wz-169-master /tmp/wzv3-f1700.png --frame=1700
npx remotion still src/index.ts man-wz-169-master /tmp/wzv3-f3340.png --frame=3340
npx remotion still src/index.ts man-wz-169-master /tmp/wzv3-f4250.png --frame=4250
```

Expected: tsc sauber; F1620 = Blende halb offen mit Quer-Inhalt (rote TGX-Front) im wachsenden Rechteck; F1700 = Vollbild randlos; F3340 = Finale-Öffnung (Alpenstraße); F4250 = Endcard mit Logo, Claim, rotem Strich, JETZT BEWERBEN, QR rechts, Löwe links dunkel. Stills als Bild PRÜFEN (Read), nicht nur rendern.

- [ ] **Step 10: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/motion/src/clients/man/projects/wartezimmervideo/Composition.tsx tools/motion/src/Root.tsx && git commit -m "feat(man-wz): V2-Master 175s — Quer-Blende, Löwe rechtsblickend links, CTA-Endcard mit QR, Untertitel stumm"
```

---

### Task 5: Testframe-Satz + Loop-Naht + Review-Gate (David)

**Files:**
- Replace: `projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/Ergebnisse/Testframes-16x9/*.png`
- Modify: `projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/Protokoll.md`

**Interfaces:**
- Consumes: Comp aus Task 4.
- Produces: Freigabe-Grundlage für David; ohne dessen OK startet Task 6 NICHT.

- [ ] **Step 1: Alte Testframes löschen, neuen Satz rendern** (Ton-Fassung, Flags ausschreiben):

| Datei | Frame | Zeigt |
|---|---|---|
| 01-kaltstart.png | 60 | Fenster rechts, Headline K1 |
| 02-spotlight1-loewe-links.png | 350 | roter Löwe links (Blick rechts!), Werkzeuge rechts |
| 03-team-takeaway.png | 600 | „FAMILIÄRES UMFELD" ab F568 sichtbar |
| 04-augenhoehe.png | 1150 | Takeaway 5 neu (Breitenprüfung optisch) |
| 05-blende-auf.png | 1620 | Öffnung 1 halb offen |
| 06-quer-vollbild.png | 1750 | Vollbild randlos, kein Logo |
| 07-blende-zu.png | 1907 | Schließen auf zentrierte Position |
| 08-rest-spotlight.png | 2050 | Fenster mittig, Löwe links, Werkzeuge rechts |
| 09-faszination.png | 2300 | Headline „NUTZFAHRZEUGE", Louis |
| 10-finale-auf.png | 3345 | Öffnung 2 |
| 11-finale.png | 3700 | Finale Vollbild |
| 12-endcard.png | 4250 | CTA + QR + Löwe |
| 13-loop-ende.png | 4374 | reine Anthrazit-Fläche |

- [ ] **Step 2: Stumme Fassung** — 3 Stills mit `--props='{"fassung":"stumm"}'`: F150 (Julia + UT), F2520 (Lara + Bewerben-Satz als UT), F800 (Markus, kürzester Block — Dichte Headline+Takeaway+Plakette+UT).

- [ ] **Step 3: Loop-Naht pixelgenau**

```bash
cd "/Users/jansantos/NIRO Studio/tools/motion" && npx remotion still src/index.ts man-wz-169-master /tmp/wz-f0.png --frame=0 && npx remotion still src/index.ts man-wz-169-master /tmp/wz-f4374.png --frame=4374 && "/Users/jansantos/NIRO Studio/tools/transcribe/venv/bin/python" -c "
from PIL import Image, ImageChops
a = Image.open('/tmp/wz-f0.png').convert('RGB')
b = Image.open('/tmp/wz-f4374.png').convert('RGB')
print('naht-diff bbox:', ImageChops.difference(a, b).getbbox())
"
```

Expected: `naht-diff bbox: None` (Frame 0 zeigt vor dem Fenster-Fade-in dieselbe Fläche). Falls nicht None: Fenster-Einblendung beginnt bei 0,0 — dann F0 gegen die Erwartung prüfen (winOp(0) = 0 ⇒ identisch; Abweichung = Bug).

- [ ] **Step 4: Alle Stills als Bild prüfen** (Read), Befunde notieren. Gezielt: QR-Kontrast auf Anthrazit, Löwen-Anschnitt links (Kopf frei?), UT-Lesbarkeit auf hellem Footage, Takeaway 5 einzeilig vs. Ausnahme 46 px.

- [ ] **Step 5: Protokoll-Eintrag** (Was gemacht / Geliefert / Offen) + Commit der Spec-/Plan-Änderungen, falls angefallen.

- [ ] **Step 6: GATE — Testframes an David, auf Freigabe warten.** Explizit abfragen: (a) Look Blende auf/zu, (b) Löwen-Position links, (c) Endcard-Layout + QR-Handy-Scan vom Bildschirm, (d) UT-Dichte stumm, (e) stumme Fassung HD-only oder 4K?

---

### Task 6 (NACH Freigabe): Finale Renders + Verifikation

**Files:**
- Create: `Ergebnisse/Renders/MAN-Wartezimmervideo-V2-16x9-Master.mov` (+ `-Preview.mp4`, `-4K-Master.mov`, `-4K-Preview.mp4`; stumme Fassung analog mit Suffix `-stumm`, 4K nur falls David ja sagt)
- Modify: `Protokoll.md`

**Interfaces:**
- Consumes: freigegebene Comp; Davids Antworten aus Task 5 Step 6.
- Produces: Lieferpaket V2.

- [ ] **Step 1: Ton-Fassung HD** (Flags ausschreiben, `--frames=0-4374`):

```bash
cd "/Users/jansantos/NIRO Studio/tools/motion" && npx remotion render src/index.ts man-wz-169-master "../../projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/Ergebnisse/Renders/MAN-Wartezimmervideo-V2-16x9-Master.mov" --codec=prores --prores-profile=hq --concurrency=8
```

- [ ] **Step 2: Ton-Fassung 4K** — identisch plus `--scale=2`, Dateiname `…-V2-4K-Master.mov`.
- [ ] **Step 3: Stumme Fassung** — `--props='{"fassung":"stumm"}'`, HD (4K nur nach Davids Antwort).
- [ ] **Step 4: Previews** je Master:

```bash
ffmpeg -y -i "<Master>.mov" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -movflags +faststart "<Master ersetzt Master durch Preview>.mp4"
```

(stumme Fassung ohne `-c:a aac` — sie hat keine Tonspur)

- [ ] **Step 5: Verifikation je Master:** ffprobe 4375 F / 175,0 s / 25 fps; Ton-Fassung hat PCM-Audio, stumme KEINE Audiospur; Stichproben-Stills aus dem RENDER (ffmpeg) bei 64,8 s / 76,4 s / 134 s / 168 s gegen die Testframes; Loop: Frame 0 vs. 4374 aus dem Master extrahieren und diffen (bbox None); Helligkeitsverlauf 163,5–165,5 monoton (kein Blitz).
- [ ] **Step 6: Protokoll + Gedächtnis aktualisieren** (Lieferung, Entscheidungen, Offenes: nur noch QR-Bestätigung MAN). Commit Doku.

---

## Self-Review (erledigt)

- **Spec-Abdeckung:** §1 V2-Quellen → Task 1 · §2 Blende/Zeiten → Task 3 Step 5 + Task 4 Step 5 · §3 Texte/Kappungen → Task 3 Steps 2–4 · §4 Löwe → Tasks 2, 4 Steps 2–4 · §5 Endcard/QR → Tasks 2, 3 Step 5, 4 Step 7 · §6 Untertitel/Lara → Task 3 Steps 4+6, Task 4 Step 6 · §7 Lieferung → Task 6 · §9 Testframes/Gate → Task 5. Keine Lücke.
- **Typkonsistenz:** `querStrecken`-IDs heißen `quer-1`/`quer-2` — Task 3 MUSS diese IDs so vergeben (Task 4 Step 5 mappt `quer-1` → Datei `-a`); `blick`-Prop default „rechts"; `hero.qr.url` = Anzeigetext, `hero.qr.asset` = Dateiname.
- **Bekannte Feinjustagen am Testframe (bewusst offen):** Löwen-`visX` links, UT-Verlaufsstärke, `M_CTA_*`-Feinlayout.
