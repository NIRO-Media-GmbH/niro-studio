# MAN Wartezimmervideo — Kundenfeedback Runde 1+2 (Design)

**Datum:** 2026-07-29 (v2 — nach zweiter MAN-Mail und Lieferung der V2-Schnittdateien)
**Charge:** `projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/`

MAN hat die erste Fassung gelobt und in zwei Mails nachgesteuert: 13 Wünsche in
Mail 1 (Szenen, Texte, CTA-Endcard, Untertitel-Fassung, Löwe), 2 in Mail 2
(Produktszenen im vollen Querformat; Löwe doch erlaubt, aber nur mit Blick nach
rechts). Davids Schnitt V2 liegt vor und ist verifiziert.

## 1. Quellmaterial V2 — geliefert und geprüft

`Material/V2 Videodateien/`, beide HEVC 10-bit BT.709, 25 fps:

| Datei | Format | Inhalt |
|---|---|---|
| `…_V2 Haupt.mp4` | 2160×3840 (9:16), 4124 F, AAC 48 kHz | Schnitt + Ton; Quer-Strecken schwarz |
| `…_V2 Quer.mp4` | 3840×2160 (16:9), 4123 F, ohne Ton | nur die Quer-Strecken, sonst schwarz |

**Verifiziert (blackdetect/volumedetect/Frame-Sichtung):**

- Quer-Strecke 1: **64,56–76,56 s** (Frames 1614–1913, exakt 12,0 s) — dunkle
  Studio-Produktshots (rote TGX-Front, Interieur, Halle). Passt tonal zur
  dunklen Bühne.
- Quer-Strecke 2 (Finale): **133,52–164,92 s** (Frames 3338–4122, 31,4 s) —
  Fahraufnahmen (Alpenstraße, Busse, E-Trucks, Lenkrad, Abendlicht),
  Schwarzblende 163,92–164,92, Ton blendet mit.
- **Timeline steht.** Strecke 1 liegt vollständig in der alten 25,3-s-Musiklücke
  (64,6–89,9), Strecke 2 hängt hinter Ciattei (Alt-Ende 133,96) an. Kein
  O-Ton-Block verschiebt sich: Nico steht bei 64,4 im Bild (Blockende 64,5),
  Louis bei 91 (Block 89,9–94,3); Gesamtdauer 164,92 = 133,96 − 0,44 + 31,4.
  timeline.json und alle Block-Zeiten bleiben gültig, keine Neu-Transkription.
- **Musik ist eingearbeitet** (Lücken ≈ −17 dB statt Stille). Der frühere
  Offen-Punkt „Musik legt David später drunter" entfällt.
- Haupt blendet 133,52–133,92 ab; in diesem Fenster liegt bereits die
  Quer-Ebene darüber — ohne Wirkung.
- Die 5 Szenentausche aus Mail 1 (unterm Truck raus, Produktszene 2:03) sind
  im V2 drin (Stichproben 11/47/93/126 s).

**Bestätigt (David 2026-07-29):** Quer-Material stammt aus dem MAN-Brandportal,
nativ 4K — das 4K-Master ist damit durchgehend sauber.

## 2. Architektur: zwei Ebenen, eine Blende

Die Komposition bekommt eine zweite Videoebene:

- **Haupt** (9:16): liefert Ton und den Fensterinhalt — wie bisher.
- **Quer** (16:9): liegt bildschirmfüllend UNTER der Grafikbühne, stumm, nur in
  den zwei Strecken gemountet.

**Der Übergang ist eine Blende, kein Schnitt:** Das Passepartout-Fenster wird
zur Maske. Beim Öffnen wächst das Fenster von 540×960 auf 1920×1080; darunter
läuft das Quer-Video bildschirmfest und wird durch die wachsende Öffnung
freigegeben. Der harte Materialwechsel in den Dateien liegt exakt auf dem
Cut-Frame — die Weichheit macht die Maske, deshalb sind Davids fixe Frames kein
Problem, sondern Voraussetzung. An den V2-Dateien ist nichts zu ändern.

Zeiten (25 fps):

| Moment | Zeit | Verhalten |
|---|---|---|
| Öffnung 1 | 64,56 → 65,16 (15 F, easeOut) | Fenster x1200 → Vollbild; roter Kantenbalken wandert mit der linken Kante und blendet aus |
| Vollbild 1 | 65,16 – 75,96 | reine Produktstrecke, keine Grafik, kein Text |
| Schließen 1 | 75,96 → 76,56 (15 F) | Maske schrumpft auf die ZENTRIERTE Fensterposition (x690, Spotlight-Stand); am Cut-Frame 76,56 wechselt der Fensterinhalt aufs Hochformat — unsichtbar, weil im geschlossenen Fenster |
| Rest-Spotlight | 76,56 – 89,9 (13,3 s) | Abdunklung/Glow wie gehabt, Löwe links, Werkzeuge rechts; Fenster gleitet 89,3–89,9 zurück nach rechts zum Louis-Start |
| Öffnung 2 | 133,52 → 134,12 | gleiche Blende, bleibt offen; Finale läuft 31,4 s |
| Schwarz | 163,92 – 164,92 | im Material (Bild + Ton) |
| Endcard | 165,0 – 173,0 | CTA + QR aus dem Schwarz (8 s) |
| Ausklang | 173,0 – 175,0 | in die Dunkelfläche; Loop-Naht Frame 4374 ≙ 0 |

**Master neu: 175,0 s / 4375 Frames** (vorher 142,0/3550). Optionaler
Feinschliff am Testframe: minimaler Scale-Settle (103→100 %) im Quer-Video
während der Öffnung.

Für den Render werden ProRes-Arbeitskopien transkodiert (HEVC 10-bit ist als
OffthreadVideo-Quelle zäh); Maße je Render-Pfad im Umsetzungsplan.

## 3. Texte (Generator `build_sync_plan.py`)

Wortlaut-Änderungen aus Mail 1 (alle Texte entstehen im Generator):

| Element | Zeit | Ist | Soll |
|---|---|---|---|
| Takeaway Block 2 | 22,7 s | `MEHR ALS KOLLEGEN. EINE **FAMILIE**.` | `**FAMILIÄRES** UMFELD` |
| Takeaway Block 5 | 44,7 s | `GLEICHE **AUGENHÖHE**. KEINE HIERARCHIEN.` | `AUF **AUGENHÖHE**. FLACHE HIERARCHIESTUFEN.` |
| Plakette Block 7 | 59,0 s | Rolle `Azubi Teilelager & Teileverkauf` | `Teilelager & Teileverkauf` |
| Headline Kapitel 3 | 89,9 s | `FASZINATION **NUTZFAHRZEUG**` | `FASZINATION **NUTZFAHRZEUGE**` |
| Takeaway Block 10 | 104,3 s | `GROSSE MASCHINEN. GROSSER **EINDRUCK**.` | `GROSSE FAHRZEUGE. **GROSSES BEWEGEN**.` |

„Azubi" fällt nur bei Nico; Louis/Lara/Hannes behalten ihre Rollen.
Breitenprüfung (fontTools, 964 px) für die zwei neuen Takeaways erneut laufen
lassen.

**Neue Anschluss-Regeln wegen der Blenden:**

- Headline K2, Nicos Takeaway und Plakette sind bis **64,4 s komplett
  unsichtbar** (Austritt vorziehen; bisher 64,8/64,9) — die Öffnung startet
  direkt von Nicos letztem Wort.
- Headline K4 und die Ciattei-Elemente sind bis **133,4 s komplett unsichtbar**
  (bisher 133,8) — dann öffnet das Finale.

## 4. Löwe: zurück, mit Blick-Regel

MAN in Mail 2: Der Löwe darf verwendet werden, **muss aber immer nach rechts
schauen.** Die vorhandenen Assets (`loewe-links-*.png`) blicken nach links und
werden gespiegelt (`loewe-rechts-*.png`). Blick nach rechts heißt gestalterisch:
Der Löwe gehört an den LINKEN Bildrand, angeschnitten, damit er ins Bild schaut.

Auftritte (Entscheidung David — nur Musikparts und Endcard, Seiten getauscht):

1. **Spotlight 1** (9,5–22,3): Löwe links am Rand, Werkzeug-Regen rechts
   (Zone spiegelt sich; über dem zentrierten Fenster max. 40 % Deckkraft).
2. **Rest-Spotlight** (76,56–89,9): dito, kürzerer Auftritt (Enter ~77,2,
   Exit ~89,3).
3. **Endcard:** Löwe links angeschnitten, Ton-in-Ton dunkel hinter der
   Textspalte (Kontrastband 8–14 % wie beim bisherigen dunklen Löwen), Blick
   nach rechts führt zu Claim und QR.

In Sprech-Blöcken bleibt die Fläche löwenfrei (Davids Linie „clean").
Der alte Guardrail „Blick zur Bildmitte" ist damit ersetzt durch:
**Blick immer nach rechts ⇒ Platzierung immer links.**

## 5. Endcard: CTA mit QR (Variante A)

135,0→165,0 verschoben, Inhalt wie in Runde 1 entschieden:

- Links: MAN-Logo (Bilddatei), `GROSSES BEWEGEN **MIT MAN**`, roter
  Trennstrich, `JETZT BEWERBEN`.
- Rechts: QR-Code 480 px als weiße Platte, darunter `JOBS.MAN.EU` als Klartext.
- Dahinter links der dunkle Löwe (Abschnitt 4).
- Kein Berufstitel ⇒ m/w/d-Pflicht greift nicht.

QR-Ziel `https://jobs.man.eu/` (offizielle Jobbörse; Karriereseiten-Claim-Pfad
bestätigt das Wording). Erzeugung einmalig als Asset nach
`tools/motion/public/clients/man/wz/`, Fehlerkorrektur M, Quiet Zone 4 Module,
vor Einbau mit echtem Handy gegen die Ziel-URL getestet. Tracking-Parameter von
MAN wären besser — nachfragen, nicht blockierend.

**Ton unter der Endcard:** still — von David bestätigt (2026-07-29): „Endcard
kommt ganz zum Schluss ohne Musik." Kein Audio-Nachschub nötig, die V2-Datei
ist final.

## 6. Stumme Fassung mit Untertiteln

Wie in Runde 1 entschieden: Untertitel klassisch unten im Videofenster
(460 px Textbreite, MAN Global Regular ~30 px, max. 2 Zeilen, ≥1,2 s,
dezenter Verlauf; Stärke am Testframe). Quelle: Wort-Timings aus
`transcript.scribe.json`, Wortlaute aus `timeline.json`, Segmentierung im
Generator. In den Quer-Strecken gibt es keine Sprache, also keine Untertitel.

**Lara-Textsperre entfällt** (CTA macht das Video zum Recruiting-Film; die
Sperre wäre eine Lücke mitten im Satz). `endeStumm` Block 9 zieht auf das
Blockende nach.

**Risiko unverändert:** Headline + Takeaway + Plakette + Untertitel gleichzeitig
— Dichte am Testframe prüfen; falls zu viel, wird die Takeaway-Ebene
ausgedünnt, nicht der Untertitel.

## 7. Lieferung

Je Fassung (Ton/stumm) ProRes 422 HQ in 1920×1080 und 3840×2160 plus
H.264-Preview — acht Dateien, ~14 GB bei 175 s. Falls die stumme Fassung nur
auf dem Wartezimmer-Schirm läuft, reicht dort HD — Davids Entscheidung vor dem
Rendern. 4K-Fenster trifft die 9:16-Quelle jetzt mit 2160×3840 nativ
(Downscale statt Upscale — Gewinn gegenüber Runde 1).

## 8. Offene Punkte

1. QR-Ziel `jobs.man.eu` von MAN bestätigen lassen (Tracking?) — nicht blockierend.
2. Stumme Fassung 4K oder nur HD — David, spätestens vor dem Render.

Erledigt: Quer-Material = MAN-Brandportal nativ 4K; Endcard ohne Musik
(beides David 2026-07-29).

## 9. Reihenfolge

1. ~~V2-Dateien prüfen~~ → erledigt (Abschnitt 1).
2. Umsetzungsplan (writing-plans), dann: ProRes-Arbeitskopien, Generator,
   Komposition (Quer-Ebene + Blende, Löwe gespiegelt, Endcard, Untertitel),
   Master 175 s.
3. Testframes: Öffnung 1 mitten in der Bewegung, Vollbild, Schließen auf
   Spotlight-Stand, Löwe links, Endcard mit QR, Untertitel-Dichte stumm.
4. Look-Review David, erst danach Render.
