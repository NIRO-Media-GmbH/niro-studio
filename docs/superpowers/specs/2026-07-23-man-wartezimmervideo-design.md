# Design: MAN Wartezimmervideo

**Datum:** 2026-07-23 · **Kunde:** MAN Truck & Bus · **Status:** freigegeben (David, 2026-07-23)

## Auftrag (Kundenmail)

Wartezimmervideo für MAN, zwei Fassungen:

- **Mit Ton:** Musik + Gesprochenes
- **Stumm:** selbsterklärende Szenen und/oder Untertitel

Länge flexibel 1–3 Minuten. Animierte, grafische Elemente ausdrücklich erwünscht.

## Entscheidungen

| Frage | Entscheidung |
|---|---|
| Ausrichtung | Reines Standort-Image (Werkstatt-Qualität, Team, Service). Keine Job-/Recruiting-Botschaften, daher keine m/w/d-CTAs. |
| Konzept | Studio entwickelt Kapitel-Struktur aus Materialsichtung; Freigabe durch David vor Sortierung/Schnittplan. |
| Gesprochenes | O-Töne aus den Interviews der Drehs. Dieselben Aussagen werden in der stummen Fassung zu animierten Untertiteln/Inserts. |
| Deliverable | Cutter-Paket: Konzept, O-Ton-Plan, B-Roll-Auswahl, 2 Schnittplan-PDFs, Animations-Renders. Finalschnitt + Musik beim Cutter. |
| Transkriptions-Umfang | Nur Interviews, aus allen vier Drehs. Erkennung: Interviews sind die jeweils größten Dateien pro Dreh. Keine B-Roll-Transkription. |

## Material

Quelle (bleibt auf dem NAS, wird nicht kopiert):
`/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/MAN Truck and Bus/02_Projekte/`

| Dreh | 03_Medien |
|---|---|
| 01 TikTok-Ads (April 2023) | 215 GB |
| 02 Ad Dreh (2025 Retainer 1:3) | 302 GB |
| 03 Frauen in der Werkstatt | 706 GB |
| 04 Lagerlogistik | 176 GB |

Hinweis: ältere Drehs sind intern unsortiert — Interview-Erkennung über Dateigröße/-dauer, nicht über Ordnernamen.

## Projektstruktur

`projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/` nach Studio-Schema
(Material/, Ergebnisse/, _intern/, Protokoll.md ab Session 1). Ins Studio kommen
nur Arbeits- und Ergebnisdateien (Transkripte, Pläne, Kontaktbögen, Renders).

## Pipeline (3 Phasen, je mit Freigabe-Gate)

### Phase 1 — Interviews erschließen

1. Struktur-Scan aller vier Drehs (ffprobe: Pfad, Größe, Dauer, Auflösung, Audio).
2. Interview-Kandidatenliste (größte Dateien pro Dreh, plausibilisiert über Dauer/Tonspur).
3. **Gate: David bestätigt Kandidatenliste vor Transkription** (Kostenkontrolle).
4. Audio extrahieren → ElevenLabs-Transkription → O-Ton-Plan mit Standort-Image-Fokus
   (Workflow `tools/transcribe/WORKFLOW.md`), Ergebnis in `Ergebnisse/O-Ton-Pläne/`.

### Phase 2 — Konzept

Ein Konzept für beide Fassungen: Kapitel-Struktur (Ziel ~90–120 s), pro Kapitel
O-Ton-Zitate + B-Roll-Bedarf + Grafik-Elemente. Ton-Fassung = Musik + O-Töne;
stumme Fassung = gleiche Struktur, O-Ton-Aussagen als animierte Untertitel, nur
selbsterklärende Szenen. **Gate: Freigabe David (pitchbar an MAN).**

### Phase 3 — Cutter-Paket

- B-Roll-Auswahl ohne Transkription: Thumbnail-Kontaktbögen der Kandidaten-Ordner
  (ffmpeg), konkrete Clips mit Ordner + Timecode, Ergebnis in `Ergebnisse/Sortierung/`.
- 2 Schnittplan-PDFs nach Davids Standard (stumm + Ton, je max. 2 Seiten + Übersicht,
  Quellen dreiteilig; Workflow `tools/transcribe/WORKFLOW-Schnittplan.md`).
- Remotion-Animationen im MAN-Look (`tools/motion/src/clients/man/brand.json` vorhanden):
  Opener, Untertitel-/Insert-Templates, Kapitel-Trenner, Endcard (ohne Job-CTA).
  Renders in `Ergebnisse/Renders/`.

## Nicht im Umfang

- Musikauswahl und -lizenzierung (Cutter)
- Finaler Schnitt beider Fassungen (Cutter, nach Schnittplan)
- Untertitel-Feintiming (ergibt sich aus O-Ton-Timecodes im Schnittplan)

## Risiken

- Größte-Datei-Heuristik kann einzelne Interviews verfehlen (z. B. gesplittete
  Aufnahmen) → Gate in Phase 1 fängt das ab, David kennt die Drehs.
- TikTok-Dreh 2023 ist Hochformat — für 16:9-Wartezimmer nur eingeschränkt nutzbar;
  Entscheidung fällt im Konzept.
