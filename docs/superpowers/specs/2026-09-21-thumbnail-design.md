# Thumbnail — saubere Standbilder aus fertigen Videos (Spec)

Datum: 2026-09-21 · Status: vom User freigegeben (Chat 21.09.: 3 Vorschläge je Video, JPG 1080×1920 + 4K, Ablage in
`04_Exportiert/<Video>/Thumbnails/`, **nur auf ausdrücklichen Wunsch**, Schreiben in „Setzer Reels Charge 2“ für eigene
Kopien erlaubt).

## Anlass

Zu jedem Reel braucht es ein Thumbnail (Reel-Cover): ein schönes Standbild **ohne Grafiken, Untertitel oder Effekte**,
am besten die Person, sonst das Thema (Produkt, B-Roll). Bisher gibt es dafür keinen Weg: Die Exporte haben Grafik
und Untertitel eingebrannt, die Rohclips sind S-Log3 ohne Grading.

## Ziel und Nicht-Ziel

**Ziel**

- Zehnte Studio-Funktion „Thumbnail: <Kunde>/<Projekt>[/<Charge>]“ — läuft **nur auf ausdrücklichen Wunsch** des
  Users, nie automatisch nach Exporten oder AutoCut-Bauten.
- Je Video **3 Vorschläge** aus verschiedenen Einstellungen, `_1` = Empfehlung (Person), `_3` möglichst das Thema.
- Je Vorschlag zwei JPGs: 1080×1920 (Reel-Cover) und 2160×3840 (`_4K`, zum Weiterbearbeiten).
- Bildquelle mit Grading, Punch-ins, Stabilisierung und B-Roll genau wie im Video, nur ohne Einblendungen.

**Nicht-Ziel (jetzt)**

- Gestaltete Thumbnails mit Text, Logo oder KI-Bearbeitung (dafür gibt es den Higgsfield-Skill).
- Videos ohne saubere Quelle (z. B. in Premiere geschnittene Reels vom Dreh 18.08. bei Setzer).
- Beschnitt auf 4:5 oder 3:4: Die Plattformen schneiden das 9:16-Cover selbst zu.

## Bildquelle

1. **Resolve-Timeline (Standard):** Eigene Kopie der Timeline (`DuplicateTimeline`) in einem eigenen Bin
   „Claude Thumbnail <JJJJ-MM-TT HHMM>“. In der Kopie werden alle Video-Items abgeschaltet (`SetClipEnabled(False)`,
   Readback), die
   - einen Alpha-Kanal haben (`Alpha mode` ≠ None — Remotion-Grafik und -Untertitel),
   - keine Mediendatei haben (Text+, Titel, Generatoren, Einstellungsebenen),
   - einen Composite-Modus ≠ Normal haben (Film Burns, Light Leaks im Modus Screen/Add; Nachtrag 21.09.2026, Wurst & Liebe)
     oder
   - auf einer Spur liegen, deren Name „SAFEZONE“ enthält;
   dazu alle Untertitel-Spuren (`SetTrackEnable`). Dann Quick Export „ProRes 422 HQ“ in Timeline-Auflösung nach
   `<Charge>/_intern/thumbnails/work/`. Danach werden Kopie und Bin gelöscht (nur diese eigenen Objekte), Timeline,
   Playhead und Bin des Users werden zurückgesetzt. Vorher wird wie bei allen Resolve-Schreibvorgängen geprüft: Das offene
   Projekt ist exakt das freigegebene, und der User spielt nicht gerade ab.
   Aus der Kopie kommen auch die **Einstellungen** (Shots): Je Frame ist das oberste aktive Nicht-Overlay-Item
   sichtbar; seine Grenzen sind die Schnitte.
2. **Saubere Videodatei (`--datei`):** z. B. ein Export ohne Grafik von einem Cutter; Schnitte per ffmpeg `scdet`.

## Auswahl

- **Kandidaten:** jeder 5. Frame (0,2 s bei 25p) als JPG 1080×1920; Frames bis 2 Frames vor oder nach einem Schnitt
  fallen weg.
- **Bewertung** (Swift, Apple Vision, `bewerten.swift`):
  - Ästhetik (`CalculateImageAestheticsScoresRequest`: `overallScore`, `isUtility`),
  - je Gesicht Box, `faceCaptureQuality`, Augen offen (Lidabstand aus den Landmarks), Mundöffnung.
  - Dazu in Python die Schärfe (Laplace-Varianz, im Gesicht oder in der Bildmitte), innerhalb des Videos als Rang 0–1
    normiert.
- **Punktzahl:**
  - Person (Gesicht ≥ 8 % der Bildhöhe): 0,45·Gesichtsqualität + 0,35·Ästhetik + 0,20·Schärfe. Abzüge: Augen zu
    (−0,5), Mund weit offen (bis −0,2), Gesicht am Bildrand angeschnitten oder Mitte unter 55 % Bildhöhe (IG-Zone, −0,3).
  - Thema (kein ausreichend großes Gesicht): 0,6·Ästhetik + 0,4·Schärfe, Abzug −0,2 bei `isUtility`.
  - Ästhetik geht als (Score + 1) / 2 ein.
- **Drei Vorschläge aus verschiedenen Einstellungen, mindestens 1,5 s auseinander:**
  - `_1` = beste Person (Gesichtsqualität ≥ 0,4, Augen offen), sonst das beste Motiv überhaupt.
  - `_2` = das nächstbeste Motiv.
  - `_3` = das beste Thema-Motiv, sonst das nächstbeste.
- **Blick von Claude:** Kontaktbogen der 12 besten Kandidaten (je Einstellung höchstens 2), beschriftet mit ID, Zeit
  und Punkten. Claude sieht ihn an und übernimmt die Vorschläge oder wählt per `--wahl <ID,ID,ID>` andere; der Grund
  steht im Protokoll.

## Ablage

- Datei `<Video>_V<n>_Thumbnail_<k>.jpg` (1080×1920) und `<Video>_V<n>_Thumbnail_<k>_4K.jpg` (2160×3840). `V<n>` ist
  die Exportversion, deren Bild die Frames zeigen (Standard: die höchste `<Video>_V<n>.mp4` im Exportordner).
- Die Frames kommen framegenau aus dem 4K-Master. RGB aus BT.709 Limited Range, JPG Qualität 92 mit sRGB-Profil.
- **NAS:** `<Exportordner>/<Video>/Thumbnails/`, für Setzer ist das
  `01_Kunden/Setzer/02_Projekte/04_Dreh 2026.09.11 - Reels/04_Exportiert/<Video>/Thumbnails/`. Kopiert wird mit
  `cp -n`, danach Byte-Vergleich.
- **Studio:** `<Charge>/Ergebnisse/Thumbnails/<Video>/`.
- **Nie überschreiben:** Die Nummer `k` zählt über vorhandene Dateien derselben Version weiter (2. Runde: 4–6).
- **Nachweis:** `<Charge>/_intern/thumbnails/<Video>_V<n>.json` (Kandidaten, Punkte, Wahl, Timecodes) und der
  Kontaktbogen `…/<Video>_V<n>_kandidaten.jpg`. Der Master wird nach der Ablage gelöscht.

## Prüfung

- **Quelle gleich Video:** In Frames ohne Einblendung muss der saubere Render mit dem letzten Export übereinstimmen
  (SSIM bei 1080×1920 ≥ 0,95, wie Lieferung zu Master). Gibt es keine freien Frames, gilt ersatzweise der Median über 12
  Frames ≥ 0,80, und die mittlere Luma weicht um höchstens 3 % ab. Sonst bricht der Lauf ab: Grading oder Ausschnitt
  wurden nicht übernommen.
- **Originale statt Proxys:** Der Detail-Faktor des 4K-Masters muss ≥ 1,15 sein (Laplace-Energie gegen herunter- und
  wieder hochskaliert), sonst Warnung.
- **Readback in Resolve:** Alle Overlay-Items der Kopie sind aus. Kopie und Bin sind gelöscht, die Ansicht des Users steht
  wieder.

## Bausteine

| Datei | Aufgabe |
|---|---|
| `tools/thumbnail/WORKFLOW-Thumbnail.md` | Trigger, Regel „nur auf Wunsch“, Ablauf, Blick auf den Kontaktbogen, Bericht |
| `tools/thumbnail/thumbnail.py` | CLI: `vorschlagen` (Quelle → Kandidaten → Bewertung → Kontaktbogen) und `ablegen` (Wahl → JPGs → NAS/Studio → Nachweis) |
| `tools/thumbnail/resolve_sauber.py` | Resolve-Schritt: Kopie ohne Overlays → Quick Export → aufräumen; liefert Master, Overlay-Bereiche, Einstellungen |
| `tools/thumbnail/bewerten.swift` | Vision-Bewertung aller JPGs eines Ordners → JSON-Zeilen |
| `tools/thumbnail/tests/` | pytest für Punktzahl, Auswahl, Dateinamen und Nummernlogik |

Laufzeit: `tools/autocut/venv/bin/python` (Resolve-Modul, numpy, PIL) und ffmpeg. Die Swift-Datei wird beim ersten
Aufruf nach `tools/thumbnail/bin/` kompiliert (nicht versioniert).
