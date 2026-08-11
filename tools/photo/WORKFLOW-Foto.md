# WORKFLOW: Foto (ARW-RAW-Pipeline)

Trigger: `„Foto: <Kunde>/<Projekt>[/<Charge>]"` — Ende-zu-Ende-Bearbeitung von
RAW-Fotos: Sichtung/Culling → Look → Batch-Entwicklung → Export. David gibt
Feedback in Runden (Übersichts-Grids, Ansagen wie „alle etwas wärmer").
Design-Spec: `docs/superpowers/specs/2026-08-03-foto-raw-pipeline-design.md`.

## Eiserne Regeln

- **Originale (ARW) sind tabu:** nur lesend öffnen, nie verschieben/verändern.
  Arbeits- und Ausgabedateien ausschließlich in `_intern/photo/` und
  `Ergebnisse/Fotos/`.
- **Ein Look pro Kunde**, gespeichert als HALD-CLUT in
  `tools/photo/looks/<kunde>/` mit `NOTES.md`. Look-Änderungen = neue Version
  (`_v4.png` …), nie überschreiben.
- Konsistenz vor Einzelbild-Optimierung: erst der Serien-Look, dann Ausreißer.
- Protokoll-Pflicht der Charge gilt (Protokoll.md).

## Werkzeuge

- RAW-Stufe: `/opt/homebrew/bin/dcraw_emu` (libraw) —
  `dcraw_emu -w -H 2 -q 3 -6 -T -o 1 -g 2.4 12.92 <kopie.arw>` → 16-bit-sRGB-TIFF.
  Immer auf einer Kopie in `_intern/photo/work/` arbeiten (schreibt neben den Input).
- Previews fürs Culling: `exiftool -b -PreviewImage` (schnell, 1616×1080,
  OHNE Orientierung — Rotation aus `exiftool -Orientation -n` der ARW anwenden).
- Look bauen/iterieren: `tools/photo/scripts/look_dev.sh` (Parameter im Kopf),
  auf 2–3 Testbildern; Sichtung per Read, iterieren bis stimmig.
- Look einfrieren: `tools/photo/scripts/make_look_lut.sh` (Parameter angleichen!)
  → HALD-12-PNG nach `tools/photo/looks/<kunde>/`.
- Batch: `tools/photo/scripts/develop_batch.sh <lut> <work> <ausgabe> NR:BILDNR …`
  — macht pro Bild Auto-Gain (Ziel-Luma 0.26, Klemme 0.85–2.1, Exponent 0.65),
  LUT, auflösungsskalierte Clarity (Sigma = lange Kante/73), Vignette (85 %),
  Full-Res- + 2048er-Web-JPEG.
- Schärfe-Ranking (nur innerhalb gleicher Motive vergleichen!):
  Laplacian-StdDev via `magick -morphology Convolve Laplacian:0`.

## Ablauf

1. **Culling:** Previews extrahieren + orientieren, Kontaktbögen (montage,
   Font explizit: `/System/Library/Fonts/Helvetica.ttc`), Schärfe-Ranking;
   Gruppen bilden, pro Winkel max. 1–2 Bilder. 100%-Crops der
   Offenblende-Kandidaten prüfen. Auswahl mit Story-Nummern (01_…) festlegen.
2. **Look:** Referenzbilder aus `Material/Fotos/Referenz/` bzw.
   `<Projekt>/Beispielfotos/` sichten und charakterisieren; look_dev.sh
   iterieren (Härtetests: hellstes + dunkelstes Motiv mitprüfen!); bei Freigabe
   als LUT einfrieren.
3. **Batch:** dcraw_emu über die Auswahl (Kopien!), develop_batch.sh, dann
   Konsistenz-Grid bauen und sichten; Ausreißer einzeln nachziehen.
4. **Export/Abgabe:** EXIF setzen (`exiftool -TagsFromFile <arw>` Basisdaten,
   `-gps:all=`, Copyright NIRO Media), Kontaktabzug der Ergebnisse für David,
   Protokoll.md fortschreiben.

## Bekannte Fallen

- **RawTherapee/darktable (Casks) starten headless nicht** — macOS-Tahoe-
  Quarantäne killt den Prozess (SIGTRAP in libsecinit), Flag ist nicht
  entfernbar (auch nicht unsandboxed). Deshalb libraw. RT wird nutzbar, sobald
  die App einmal regulär per GUI geöffnet/bestätigt wurde.
- **Homebrew-ImageMagick ist Q16-HDRI:** Werte >1.0 werden NICHT geclippt.
  Vor `-hald-clut` zwingend `-clamp` (nach jedem Gain/Highpass) — sonst liegen
  Highlights außerhalb des LUT-Würfels und die Extrapolation erzeugt massive
  Magenta/Cyan-Artefakte in Lichtern (Pilot 2026-08-03 kostete das einen
  kompletten Batch-Durchlauf).
- Großradius-`-unsharp` (Clarity) ist bei 33 MP unbrauchbar langsam (~5 min/Bild) —
  stattdessen Resize-Highpass wie in develop_batch.sh (identische Wirkung, Sekunden).
- ImageMagick `montage`/`-label` braucht explizite `-font`-Angabe.
- IM-fx: keine Variablennamen mit Ziffern oder reservierten Präfixen (w, h, g…) —
  `ka`, `kb` funktionieren.
- Sony-PreviewImage ist unrotiert; Hochformat erst nach Orientation-Anwendung
  beurteilen.
- zsh: Command-Substitution wird gesplittet, `$VAR`-Flaglisten nicht — Flags
  ausschreiben.
