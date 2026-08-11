# MAN Wartezimmervideo — Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cutter-Paket für das MAN-Wartezimmervideo (zwei Fassungen: Ton + stumm) aus 1,4 TB Footage von vier Drehs — Konzept, O-Ton-Auswahl, B-Roll-Auswahl, 2 Schnittplan-PDFs, Remotion-Layout-Renders.

**Architecture:** Eine Transkriptions-Passage über die bestätigten Interviews (transcribe_clip → `utterances.json`, Abweichung vom Spec-Wortlaut „Audio extrahieren": gleiche Deliverables, eine statt zwei Transkriptionen). Utterances speisen O-Ton-Auswahl UND Schnittplan-Zitate. B-Roll ohne Transkription per Thumbnail-Kontaktbögen. Remotion liefert 16:9-Frames mit Alpha, in die der Cutter das 9:16-Footage legt.

**Tech Stack:** `tools/transcribe` (Python-venv, ElevenLabs Scribe, ffmpeg/ffprobe, `render_schnittplan_pdf.py`), `tools/motion` (Remotion, Client `man` mit brand.json).

**Spec:** `docs/superpowers/specs/2026-07-23-man-wartezimmervideo-design.md`

## Global Constraints

- NAS-Quelle ist **read-only**: `/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/MAN Truck and Bus/02_Projekte/` — Originale werden NIE verändert, nichts wird verschoben.
- Chargen-Ordner (alle Arbeits-/Ergebnisdateien): `/Users/jansantos/NIRO Studio/projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/` — im Folgenden `<CHARGE>`.
- Transkribiert werden NUR von David bestätigte Interview-Dateien (Gate in Task 2). Keine B-Roll-Transkription.
- Sämtliches Footage ist 9:16. Ausgabe 16:9 (1920×1080). Kein Job-/Recruiting-Inhalt, keine CTAs (reine Standort-Image-Ausrichtung).
- Schnittplan-Format verbindlich nach `tools/transcribe/WORKFLOW-Schnittplan.md`: max. 2 PDF-Seiten pro Video (< 6.000 Zeichen je MD) + genau 1 Übersichtsseite, Quellen IMMER dreiteilig `<Person> (<Rolle>) · <Ordner>/<Datei> · <von–bis>`, Kommentar-Spalte Pflicht, Zitate wörtlich.
- Remotion-Finalrenders: ProRes 4444 mit Alpha (`--image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444`), vorher Pre-Delivery-Review nach `tools/motion/CLAUDE.md` (Safe Zone; `review.showGuides: false` vor Final-Render).
- Python immer über `tools/transcribe/venv/bin/python`; ElevenLabs-Key aus `tools/transcribe/.env`.
- Nach jeder Session: `<CHARGE>/Protokoll.md` fortschreiben.
- Gates (Arbeit anhalten, David fragen): nach Task 2 (Kandidatenliste), nach Task 5 (Konzept). Bei Unklarheiten zu Personen/Rollen: fragen, nicht raten.

---

### Task 1: Struktur-Scan aller vier Drehs

**Files:**
- Create: `<CHARGE>/_intern/scan_media.py`
- Create (Output): `<CHARGE>/_intern/scan.csv`

**Interfaces:**
- Produces: `scan.csv` mit Spalten `dreh,relpath,size_gb,dur_min,breite,hoehe,audio_kanaele` — Grundlage für Task 2 (Kandidaten) und Task 6 (B-Roll-Ordner).

- [ ] **Step 1: Scan-Script schreiben**

```python
#!/usr/bin/env python3
"""Struktur-Scan MAN-Drehs: ffprobe-Metadaten aller Videodateien -> scan.csv"""
import csv, json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

NAS = Path("/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/MAN Truck and Bus/02_Projekte")
OUT = Path(__file__).parent / "scan.csv"
EXTS = {".mp4", ".mov", ".mxf", ".m4v"}

def probe(p: Path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", str(p)],
            capture_output=True, text=True, timeout=60)
        d = json.loads(r.stdout or "{}")
        dur = float(d.get("format", {}).get("duration", 0))
        v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
        a = [s for s in d.get("streams", []) if s.get("codec_type") == "audio"]
        return {
            "dreh": p.relative_to(NAS).parts[0],
            "relpath": str(p.relative_to(NAS)),
            "size_gb": round(p.stat().st_size / 1e9, 2),
            "dur_min": round(dur / 60, 1),
            "breite": v.get("width", 0), "hoehe": v.get("height", 0),
            "audio_kanaele": sum(int(s.get("channels", 0)) for s in a),
        }
    except Exception as e:
        print(f"WARN {p}: {e}", file=sys.stderr)
        return None

files = [p for p in NAS.rglob("*") if p.suffix.lower() in EXTS
         and not p.name.startswith("._")]
print(f"{len(files)} Videodateien gefunden, probe läuft …")
with ThreadPoolExecutor(max_workers=8) as ex:
    rows = [r for r in ex.map(probe, files) if r]
rows.sort(key=lambda r: (r["dreh"], -r["size_gb"]))
with OUT.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print(f"{len(rows)} Zeilen -> {OUT}")
```

- [ ] **Step 2: Scan laufen lassen**

Run: `"/Users/jansantos/NIRO Studio/tools/transcribe/venv/bin/python" "<CHARGE>/_intern/scan_media.py"`
Expected: `N Videodateien gefunden … N Zeilen -> …/scan.csv` (N > 500 erwartet; WARN-Zeilen einzeln ok). Läuft je nach NAS-Tempo mehrere Minuten — im Hintergrund starten.

- [ ] **Step 3: Plausibilität prüfen**

```bash
"/Users/jansantos/NIRO Studio/tools/transcribe/venv/bin/python" - <<'EOF'
import csv
from collections import defaultdict
agg = defaultdict(lambda: [0, 0.0])
for r in csv.DictReader(open("<CHARGE>/_intern/scan.csv")):
    agg[r["dreh"]][0] += 1
    agg[r["dreh"]][1] += float(r["size_gb"])
for dreh, (n, gb) in sorted(agg.items()):
    print(f"{dreh}: {n} Dateien, {gb:.0f} GB")
EOF
```

Expected: 4 Drehs, Summen ≈ 215/302/706/176 GB (±10 % wegen Nicht-Video-Dateien). Weicht ein Dreh stark ab → Extensions/Fehler prüfen, nicht einfach weitermachen.

### Task 2: Interview-Kandidatenliste + GATE

**Files:**
- Create: `<CHARGE>/_intern/interview-kandidaten.md`

**Interfaces:**
- Consumes: `scan.csv` aus Task 1.
- Produces: `interview-kandidaten.md` — pro Dreh Tabelle `| # | Datei (relpath) | GB | Min | Audio |`, nach Davids Freigabe mit Markierung `[OK]`/`[RAUS]` je Zeile. Nur `[OK]`-Zeilen gehen in Task 3.

- [ ] **Step 1: Kandidaten filtern und Markdown bauen**

Heuristik (Spec): Interviews = größte Dateien pro Dreh. Regel: je Dreh alle Dateien mit `size_gb >= 3` ODER `dur_min >= 8`, UND `audio_kanaele >= 1`; mindestens Top 10 je Dreh nach Größe, damit kein Dreh leer ausgeht. Als Tabellen (eine je Dreh, sortiert nach Größe) nach `_intern/interview-kandidaten.md` schreiben, Kopfzeile mit Heuristik-Beschreibung.

- [ ] **Step 2: GATE — David bestätigen lassen**

Kandidatenliste im Chat zeigen (kompakt: Anzahl + Gesamt-GB je Dreh + Auffälligkeiten wie Dateien ohne Audio). Fragen: (a) Kandidaten streichen/ergänzen? (b) **Welche Kamera trägt den Ton** (B-Cams laufen laut Workflow oft ohne Mikro)? Antworten in `interview-kandidaten.md` einarbeiten (`[OK]`/`[RAUS]` + Notiz Ton-Kamera). NICHT weiterarbeiten ohne Freigabe.

- [ ] **Step 3: Protokoll fortschreiben + Session-Stand sichern**

`<CHARGE>/Protokoll.md`: Datum, Scan-Bilanz (Dateien/GB je Dreh), Kandidaten-Stand, Davids Entscheidungen.

### Task 3: Interviews transkribieren → utterances.json

**Files:**
- Create: `<CHARGE>/_intern/transcribe_man.py` (nach Vorlage `projects/WLC/Recruiting/2026-07 Erster Dreh/_intern/transcribe_wlc.py`)
- Create (Output): `<CHARGE>/_intern/cache/`, `<CHARGE>/_intern/transcripts_index.json`, `<CHARGE>/_intern/utterances.json`

**Interfaces:**
- Consumes: `[OK]`-Dateien aus `interview-kandidaten.md` (absolute NAS-Pfade = `NAS + relpath`).
- Produces: `utterances.json` — einzige Quelle für Zitate + Timecodes + Sprecher in Task 4 und Task 7. Index-Felder je Clip: `standort/kategorie/person` (hier: `dreh` als standort-Feld, kategorie=`interview`, person aus Selbstvorstellung oder `unbekannt`).

- [ ] **Step 1: Vorlage lesen und Runner anpassen**

`projects/WLC/Recruiting/2026-07 Erster Dreh/_intern/transcribe_wlc.py` lesen. Anpassen: Clip-Liste = `[OK]`-relpaths aus `interview-kandidaten.md` (parsen, nicht hart codieren), NAS-Root wie Task 1, Cache/Index nach `<CHARGE>/_intern/`. Nutzt `transcribe_clip` aus `tools/transcribe` (Scribe + Diarisation, gecacht).

- [ ] **Step 2: Probelauf mit EINEM Clip**

Runner mit `--limit 1` (oder Liste auf 1 gekürzt) laufen lassen.
Expected: 1 Eintrag in `transcripts_index.json`, Cache-Datei in `_intern/cache/`, Transkript enthält deutschen Text mit Sprecher-IDs. Erst dann Vollauf.

- [ ] **Step 3: Vollauf**

Alle `[OK]`-Clips transkribieren (im Hintergrund; Kosten fallen hier an — Umfang wurde in Task 2 von David gedeckelt).
Expected: `transcripts_index.json` hat genau so viele Einträge wie `[OK]`-Zeilen.

- [ ] **Step 4: Utterances bauen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/transcribe" && venv/bin/python scripts/build_utterances.py "<CHARGE>"`
Expected: `_intern/utterances.json` entsteht; Stichprobe: Utterances haben `von/bis`-Timecodes und Sprecher-Trennung.

### Task 4: O-Ton-Auswahl Standort-Image

**Files:**
- Create: `<CHARGE>/Ergebnisse/O-Ton-Pläne/00-oton-auswahl-standort-image.md`

**Interfaces:**
- Consumes: `utterances.json`, `transcripts_index.json`.
- Produces: thematisch geclusterte O-Ton-Auswahl; jede Aussage mit wörtlichem Zitat, dreiteiliger Quelle und Timecode. Task 5 referenziert Aussagen über deren laufende Nummer (`O-01`, `O-02`, …).

- [ ] **Step 1: Wer-ist-wer klären**

Selbstvorstellungen in den Utterances suchen (Name/Rolle am Interview-Anfang), Personen-Tabelle `Person | Rolle | Dreh | Datei` bauen. Unklare Personen im Chat mit David klären, nicht raten.

- [ ] **Step 2: Aussagen auswählen und clustern**

Aus `utterances.json` NUR Aussagen der Interviewten (Interviewer/Regie per Diarisation ausschließen). Cluster für Standort-Image: Werkstatt-Qualität/Kompetenz, Team & Menschen, Service/Kundennähe, Technik/Ausstattung, Stolz/Identifikation. Keine Job-/Bewerbungs-Aussagen aufnehmen. Je Cluster 3–6 beste Aussagen, kurz (Wartezimmer-tauglich: einzeln verständlich, ≤ ~12 s), jede als:
`O-NN · "<wörtliches Zitat>" · <Person> (<Rolle>) · <Ordner>/<Datei> · <von–bis>`

- [ ] **Step 3: Verifizieren**

Jede ausgewählte Aussage gegen `utterances.json` prüfen: Zitat wörtlich vorhanden, Timecodes stimmen, im Bereich `[von, bis]` spricht nur diese Person. Abweichung → Aussage korrigieren oder streichen.

- [ ] **Step 4: Datei schreiben + Protokoll**

`00-oton-auswahl-standort-image.md` mit Personen-Tabelle + Clustern schreiben; Protokoll fortschreiben (Anzahl Aussagen je Cluster, Lücken — z. B. Cluster ohne brauchbare O-Töne).

### Task 5: Konzept beider Fassungen + GATE

**Files:**
- Create: `<CHARGE>/Ergebnisse/Konzept.md`
- Create: `<CHARGE>/_intern/script_structured.json`

**Interfaces:**
- Consumes: O-Ton-Nummern aus Task 4, `scan.csv` (welche Ordner/Motive existieren).
- Produces: `Konzept.md` (Kapitel-Struktur, pitchbar an MAN) und `script_structured.json` nach Schnittplan-Workflow-Schema `{"videos":[{"nr","titel","rows":[{"id","typ","text"}]}]}` mit `videos[0] = Ton-Fassung (nr 1)`, `videos[1] = stumme Fassung (nr 2)`; `typ` ∈ interview|visual. Zusätzlich je row Feld `layout` ∈ solo|versetzt|duo und Feld `oton` (O-NN oder null) — Task 7 und Task 8 lesen genau diese Felder.

- [ ] **Step 1: Kapitel-Struktur entwerfen**

Ziel ~90–120 s, 4–6 Kapitel (z. B. Ankommen/Standort → Werkstatt & Technik → Menschen/Team → Service-Versprechen → Abbinder mit Logo — endgültige Kapitel aus dem tatsächlichen Material ableiten). Pro Kapitel in `Konzept.md`: Ziel-Dauer, Kernaussage, O-Töne (O-NN), B-Roll-Bedarf (Motive + Kandidaten-Ordner aus `scan.csv`), Layout-Typ (solo/versetzt/duo), Grafik-Elemente. Beide Fassungen aus EINER Struktur: Ton-Fassung = Musik + O-Töne hörbar; stumme Fassung = gleiche Kapitel, O-Ton-Aussagen als animierte Untertitel-Inserts, nur selbsterklärende Szenen (Szenen, die Gesprochenes zwingend brauchen, bekommen in der stummen Fassung Ersatz-B-Roll oder Insert-Text).

- [ ] **Step 2: script_structured.json ableiten**

Aus `Konzept.md` mechanisch das JSON bauen (Schema oben). `hinweise`-Block aufnehmen: read-only-NAS, 9:16-in-16:9-Layouts, keine Job-CTAs.

- [ ] **Step 3: GATE — Freigabe David**

`Konzept.md` im Chat zusammenfassen (Kapiteltabelle + was die stumme Fassung anders macht). Erst nach Freigabe (ggf. nach MAN-Pitch) weiter mit Task 6–8. Änderungswünsche in Konzept.md UND script_structured.json einpflegen. Protokoll fortschreiben.

### Task 6: B-Roll-Auswahl per Kontaktbögen

**Files:**
- Create (Output): `<CHARGE>/_intern/kontaktboegen/<dreh>/<clipname>.jpg`
- Create: `<CHARGE>/Ergebnisse/Sortierung/broll-auswahl.md`

**Interfaces:**
- Consumes: B-Roll-Bedarf + Kandidaten-Ordner aus `Konzept.md`; Clip-Liste aus `scan.csv` (Nicht-Interview-Dateien der genannten Ordner).
- Produces: `broll-auswahl.md` — je Konzept-Kapitel konkrete Clips `<Ordner>/<Datei> · <Timecode-Bereich> · <Bildbeschreibung>`. Task 7 übernimmt diese Referenzen in die Bild-Spalte.

- [ ] **Step 1: Kontaktbögen rendern**

Für jeden Kandidaten-Clip (aus `scan.csv`, nur Ordner laut Konzept, Interviews ausgenommen):

```bash
ffmpeg -hide_banner -loglevel error -i "<NAS-Pfad>" \
  -vf "fps=1/10,scale=240:-1,tile=6x5" -frames:v 1 \
  "<CHARGE>/_intern/kontaktboegen/<dreh>/<clipname>.jpg"
```

(1 Frame alle 10 s, 30 Kacheln/Bogen = 5 min je Bogen; längere Clips: `-frames:v 2` usw., Suffix `_2.jpg`.) Als Schleifen-Script `_intern/kontaktboegen.sh` ablegen, im Hintergrund laufen lassen.
Expected: je Kandidaten-Clip ≥ 1 JPG; Fehlläufe (0-Byte-JPGs) auflisten und melden.

- [ ] **Step 2: Sichten und zuordnen**

Kontaktbögen als Bilder lesen (Read-Tool), je Konzept-Kapitel die 3–8 besten Clips wählen: verwacklungsarm, selbsterklärend (Pflicht für stumme Fassung), Timecode-Bereich aus Kachelposition (Kachel n ≈ Sekunde n×10). In `broll-auswahl.md` schreiben, gruppiert nach Kapitel, mit 1-Zeilen-Bildbeschreibung je Clip.

- [ ] **Step 3: Abdeckung prüfen + Protokoll**

Jedes Kapitel hat ≥ 3 Clips? Lücken ins Protokoll und in `broll-auswahl.md` als „Offen" — nicht stillschweigend dünn lassen.

### Task 7: Schnittplan-PDF (beide Fassungen)

**Files:**
- Create: `<CHARGE>/Ergebnisse/O-Ton-Pläne/Dossier/video-1-ton-lang.md`, `…/video-2-stumm-lang.md`
- Create: `<CHARGE>/Ergebnisse/O-Ton-Pläne/video-1-ton.md`, `…/video-2-stumm.md`, `…/01-projekt-grundlagen.md`
- Create: `<CHARGE>/_intern/pdf_meta.json`

**Interfaces:**
- Consumes: `script_structured.json` (Kapitel/rows mit `layout` + `oton`), `utterances.json` (Zitate/Timecodes), `broll-auswahl.md` (Bild-Spalte), Render-Namen aus Task 8 (`Interfaces: Produces` dort — Grafik-Zeilen referenzieren exakt diese Dateinamen).
- Produces: eine Cutter-PDF nach Davids Standard.

- [ ] **Step 1: Langfassungen bauen**

Pro Fassung ein detaillierter Plan (Dossier): Szenen-Tabelle über alle Kapitel mit O-Ton wörtlich (aus utterances.json), Quelle dreiteilig, Bild (B-Roll-Clips aus `broll-auswahl.md` + Layout-Typ), Grafik (Remotion-Render-Dateiname), Sound (Ton-Fassung: Musik-Charakter + O-Ton; stumme Fassung: „—"), Caption/Insert-Text, Kommentar.

- [ ] **Step 2: Verifizieren (Pflicht, Reihenfolge aus Workflow)**

(a) Jedes Zitat + Timecode + Sprecher-Reinheit gegen `utterances.json`. (b) Regeln: keine Job-CTAs, stumme Fassung nur selbsterklärende Szenen, Quellen dreiteilig. (c) Cutter-Tauglichkeit: In/Out auffindbar, keine Szene ohne Bild-Quelle, Alpha-Render-Namen existieren in Task-8-Liste.

- [ ] **Step 3: Kompaktfassungen + Übersichtsseite**

`video-1-ton.md` / `video-2-stumm.md` je < 6.000 Zeichen (Budget: max 2 PDF-Seiten), Sektionen: Titel [Fassung] · Ziel & Story (max 3 Sätze inkl. Ziellänge) · Material (erlaubt/verboten) · Ablauf-Tabelle (# | Szene | O-Ton wörtlich | Quelle | Bild | Sound | Caption | Kommentar) · Alternativen · Offen. `01-projekt-grundlagen.md` (1 Seite): NAS-Pfad, Hauptregel („9:16-Footage in 16:9-Frames — Grafik-Renders mit Alpha unterlegen"), Fassungs-Tabelle, Personen-Tabelle aus Task 4, Ton-Kamera-Regel aus Task 2, Offenes.
Check: `wc -c` je Kompakt-MD < 6000.

- [ ] **Step 4: PDF rendern + Seitenbudget prüfen**

`_intern/pdf_meta.json` (titel „MAN Wartezimmervideo", untertitel, stand, warnbox = Hauptregel, kapitel_farben, dateiname), dann:
Run: `cd "/Users/jansantos/NIRO Studio/tools/transcribe" && venv/bin/python scripts/render_schnittplan_pdf.py "<CHARGE>"`
Expected: PDF in `Ergebnisse/O-Ton-Pläne/`; mit pypdf Seiten je Kapitel zählen: Übersicht = 1, je Fassung ≤ 2. Drüber → MD kürzen (nicht Layout quetschen), neu rendern.

### Task 8: Remotion-Layout-System + Renders

**Files:**
- Create: `tools/motion/src/clients/man/projects/wartezimmervideo/` (Kompositionen, via `npm run new:project`)
- Create (Output): `<CHARGE>/Ergebnisse/Renders/*.mov`

**Interfaces:**
- Consumes: `script_structured.json` (Kapitel, `layout`, Insert-Texte/Kapiteltitel, O-Ton-Texte der stummen Fassung aus Task 4).
- Produces: Renders mit festem Namensschema — `frame-solo-<kapitel>.mov`, `frame-versetzt-<kapitel>.mov`, `frame-duo-<kapitel>.mov` (je Kapitel nur der laut Konzept nötige Typ, 30 s loopbar), `opener.mov`, `trenner-<kapitel>.mov`, `insert-O-NN.mov` (ein Untertitel-Insert je O-Ton der stummen Fassung, Dauer = O-Ton-Länge + 2 s), `endcard.mov`. Task 7 referenziert exakt diese Namen.

- [ ] **Step 1: Projekt anlegen + Kompositionen bauen**

`cd tools/motion && npm run new:project` (Kunde `man`, Projekt `wartezimmervideo`). Kompositionen (alle 1920×1080/25fps, `projectPropsSchema` aus `src/core/schemas.ts`, `<ReviewOverlay>` integriert): `FrameSolo` (ein 9:16-Fenster mittig-links, Grafikfläche rechts mit Logo/Farbverlauf/Textbereich), `FrameVersetzt` (Fenster außermittig, asymmetrische Flächen), `FrameDuo` (zwei 9:16-Fenster nebeneinander, schmale Mittel-Grafikspalte), `Opener`, `KapitelTrenner` (Titel-Prop), `UntertitelInsert` (Text-Prop, unteres Drittel), `Endcard` (Logo + Standort-Claim, KEIN Job-CTA). Fenster = transparente Aussparungen (Alpha), MAN-Look aus `brand.json`.

- [ ] **Step 2: Studio-Sichtprüfung**

`npm run studio`, jede Komposition mit `review.showGuides/showSafeZone: true` prüfen: Text in Safe Zone, Fenster-Aussparungen korrekt, Animationen ohne Overshoot aus der Safe Zone. (Face Zone entfällt — Frames enthalten kein Footage, Fenster sind leer.)

- [ ] **Step 3: Final-Renders**

`review.showGuides: false`, dann je Komposition/Kapitel-Variante:

```bash
npx remotion render src/index.ts <CompId> \
  "../../projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/Ergebnisse/Renders/<name>.mov" \
  --image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444
```

Expected: alle Dateien des Namensschemas vorhanden; Stichprobe per ffprobe: `pix_fmt=yuva444p10le` (Alpha da), 1920×1080.

- [ ] **Step 4: Konsistenz-Check gegen Schnittplan**

Jeder in Task 7 referenzierte Render-Name existiert als Datei (Shell-Loop über die MD-Dateien, fehlende melden/fixen).

### Task 9: Übergabe-Paket + Abschluss

**Files:**
- Modify: `<CHARGE>/Protokoll.md`

**Interfaces:**
- Consumes: alle Ergebnisse aus Task 4–8.

- [ ] **Step 1: Vollständigkeit prüfen**

Checkliste gegen Spec-Deliverable: Konzept.md (freigegeben) ✓, 00-oton-auswahl ✓, broll-auswahl.md ✓, Schnittplan-PDF (Übersicht + 2 Fassungen, Seitenbudget) ✓, Renders komplett ✓. Fehlendes nachziehen, nicht wegdokumentieren.

- [ ] **Step 2: Übergabe im Chat + Protokoll**

Bilanz an David: was liegt wo, was der Cutter braucht (PDF + Renders + NAS-Zugriff), offene Punkte (Musikwahl, MAN-Freigaben). Protokoll-Schlusseintrag.
