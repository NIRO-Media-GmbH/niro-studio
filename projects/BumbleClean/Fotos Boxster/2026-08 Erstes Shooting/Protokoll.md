# Protokoll — BumbleClean / Fotos Boxster / 2026-08 Erstes Shooting

## 2026-08-03 — Pilot der neuen Foto-Funktion: Auswahl + Look + Entwicklung

**Gemacht:**
- Erste Nutzung der fünften Studio-Funktion „Foto" (Spec:
  `docs/superpowers/specs/2026-08-03-foto-raw-pipeline-design.md`).
- 36 ARWs (A7 IV, Sigma 24-70 2.8, 2026-08-02) gesichtet: Previews extrahiert,
  Schärfe-Ranking, Kontaktbögen, 100%-Crops der Offenblende-Kandidaten.
- Auswahl: 13 Bilder, jede Perspektive einmal (Story-Reihenfolge 01–13):
  01 2980 Hero Waben-Haube · 02 2969 Front frontal · 03 2979 Front mit Rollup ·
  04 2977 Ganzaufnahme Schriftzug · 05 2985 Seite Felge/Bremssattel ·
  06 2984 Heck-Detail · 07 2986 Heck unter Banner · 08 2990 Heck-Totale ·
  09 2991 Makro „Boxster S" · 10 2994 Cockpit offen · 11 2997 Lenkrad ·
  12 3001 Sitze · 13 3002 Halle gesamt.
  Aussortiert u. a.: 2983 (Fokus daneben), 2981/2987/2989/2992 (schwächere
  Beinahe-Duplikate), 2972–2976/2978 (Serie desselben Winkels).
- Look „Ultraclean Dramatic v3" aus den 3 Beispielfotos abgeleitet, in 3
  Iterationen auf Härtetest-Bildern (2980/2977/2997) kalibriert, als HALD-LUT
  gespeichert: `tools/photo/looks/bumbleclean/ultraclean_v3.png` (+ NOTES.md).
- Batch-Entwicklung aller 13 in voller Auflösung → `Ergebnisse/Fotos/`
  (Full-Res + `web/` 2048 px + `_Uebersicht_01-13.jpg`). Zwei Batch-Läufe
  nötig: Lauf 1 wegen HDRI-LUT-Artefakten verworfen (Q16-HDRI clippt nicht;
  Highlights außerhalb des LUT-Würfels → Magenta/Cyan — Fix: `-clamp` vor
  `-hald-clut`), Lauf 2 sauber; Konsistenz im Grid + Stichproben (02/12/13)
  geprüft. EXIF final: Kamera/Objektiv/Aufnahmedaten aus ARW übernommen,
  Copyright „© 2026 NIRO Media", GPS/Seriennummer entfernt.

**Entscheidungen:**
- RAW-Engine umgestellt: RawTherapee-CLI wird von macOS-Tahoe-Quarantäne beim
  Start gekillt (SIGTRAP libsecinit, Flag headless nicht entfernbar; Reports
  18:41–18:46 Uhr). Stattdessen libraw/dcraw_emu (Homebrew-Formula) +
  ImageMagick-LUT — erfüllt den Spec-Kern (Klartext-Feinsteuerung) sogar
  besser. RT in /Applications bleibt als Upgrade-Pfad (einmal GUI-Öffnen
  schaltet ihn frei). Spec-Abweichung hiermit dokumentiert.
- ARWs liegen (abweichend von der SSD-Konvention) direkt im Projektordner
  `Fotos Boxster/` — bewusst dort belassen (Originale unangetastet), Charge
  `2026-08 Erstes Shooting/` hält nur Arbeit + Ergebnisse.
- Auto-Gain-Angleichung pro Bild (Ziel-Luma 0.26, Klemme 0.85–2.1), damit
  Interieur-Aufnahmen zur Außen-Serie passen.

**Runde 2 (gleicher Tag, nach Davids Feedback „unprofessionell, Auto ungleich
hell"):** Diagnose bestätigt per Messung — Lack-Luminanz schwankte Faktor 6
(0.037–0.221), Ursache: Belichtungsangleich auf Gesamtbild-Mean statt aufs
Auto; zudem Look zu dunkel (Mitten global abgesenkt). Fix: (1) Look v4 —
Mitten neutral, S-Kurve sanfter, Highlight-Stretch, Vignette dezenter,
Grün-Dämpfung stärker; (2) Belichtung ankert jetzt auf definierter
Lack-Region pro Bild (Referenz 2980), Feintrim 05/06/10. Ergebnis: Serie im
Korridor 0.08–0.17 (Rest motivbedingter Glanz), alle 13 neu geliefert, EXIF
neu gesetzt. Looks: v3 archiviert, v4 aktiv (`tools/photo/looks/bumbleclean/`).

**Runde 3 (Davids Feedback „fehlt Punch/Drama"):** Look v5 — Kern ist eine
Luma-selektive Mitteltöne-Senke: Umgebung (Boden/Wände) sinkt deutlich ab,
schwarzer Lack und Reflexe bleiben stehen → Spotlight-Wirkung der Referenzen.
Dazu Vignette 80 %, Clarity 0.24, Schwarzpunkt 2.5 %, Gelb weiter entsättigt.
Getestet als v4-vs-v5-Vergleich an 01/04, dann Batch; 02/03/10 lagen mit
Frontschatten/Leder im Senkenbereich und wurden per Anker-Faktor (1.25/1.15/1.0)
ausgeglichen. Alle 13 neu geliefert, EXIF gesetzt, Übersicht erneuert.

**Offen:**
- Kennzeichen „SHA X 987" auf 08_2990/06_2984 lesbar — falls unerwünscht:
  Winkel streichen oder Photoshop-Retusche (außerhalb Pipeline-Scope).
- Social-Zielformate (4:5/1:1/9:16) noch nicht definiert — Ausgangsmaterial
  2:3 lässt alle Crops zu.
- Leichtes ISO-Rauschen in stark gepushten Interieurs — falls störend: Topaz
  Photo AI als optionale Stufe prüfen.
