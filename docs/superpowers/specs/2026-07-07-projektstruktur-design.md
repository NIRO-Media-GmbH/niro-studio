# Design: Neue Projektstruktur mit Chargen-Ebene

**Datum:** 2026-07-07
**Status:** Vom Nutzer freigegeben

## Ziel

Die Projektordner unter `projects/` übersichtlicher machen: Ergebnisse sofort
sichtbar, ein einheitliches Schema für alle Projekte, Technik-Dateien gebündelt,
sprechende deutsche Ordnernamen — plus eine Chargen-Ebene für mehrere
Video-Chargen pro Kunde/Projekt.

## Zielstruktur

```
projects/<Kunde>/<Projekt>/<Charge>/
├── Material/               was der Nutzer reinlegt
│   ├── Audio/                 Interview-WAVs            (alt: audio/)
│   ├── Konzept/               Konzept-PDF               (alt: script/)
│   └── Video/                 Inputs für Animationen    (alt: motion/inputs/)
├── Ergebnisse/             was fertig ist
│   ├── O-Ton-Pläne/           Interview-Pipeline        (alt: output/)
│   ├── Sortierung/            Zuordnungspläne Footage   (alt: footage/-Pläne)
│   └── Renders/               fertige Animationen       (alt: motion/renders/)
└── _intern/                was die Tools brauchen
    ├── cache/  work/          Pipeline-Zwischenstände
    └── …                      Skripte, Logs, Manifeste, Undo-Logs
```

Regeln:

- **Chargen-Ebene immer**, auch bei nur einer Charge. Jedes Projekt sieht
  identisch aus, kein Umbau beim zweiten Dreh.
- **Chargen-Name:** `JJJJ-MM Beschreibung` (z. B. „2026-07 Erster Dreh") —
  sortiert chronologisch im Finder. Bei Bestandsprojekten wird das Datum aus
  den Dateidaten abgeleitet.
- Unterordner in `Material/` und `Ergebnisse/` nur anlegen, wenn die Funktion
  genutzt wird.
- Beim Chat-Trigger nennt der Nutzer Kunde/Projekt/Charge; bei nur einer
  Charge reicht Kunde/Projekt (Charge wird dann automatisch gefunden).
- Umbenennen einer Charge ist jederzeit erlaubt; nur der Remotion-Symlink in
  `tools/motion/public/projects/` muss danach neu gesetzt werden.

## Migration der Bestandsprojekte

Reines Verschieben (`mv`), nichts wird gelöscht. Chargen-Namen aus Dateidaten
ableiten (Arbeitsname „JJJJ-MM Erster Dreh", vom Nutzer umbenennbar).

| Projekt | alt | neu |
|---|---|---|
| REM/Website-Dienstleistungsfilm | `audio/` | `<Charge>/Material/Audio/` |
| | `output/` | `<Charge>/Ergebnisse/O-Ton-Pläne/` |
| | `cache/`, `work/` | `<Charge>/_intern/` |
| LohiBW/Recruiting | `script/` | `<Charge>/Material/Konzept/` |
| | `zuordnungsplan.md` | `<Charge>/Ergebnisse/Sortierung/` |
| | `cache/`, `work/`, `cls/`, Skripte, Logs, Manifeste, JSONs | `<Charge>/_intern/` |
| REM/Dachbeschichtung | `motion/renders/` | `<Charge>/Ergebnisse/Renders/` |
| Seniorenstiftung/Recruiting | `motion/inputs/` | `<Charge>/Material/Video/` |

Nach der Migration: Remotion-Symlink
`tools/motion/public/projects/seniorenstiftung-recruiting` auf den neuen Pfad
(`…/<Charge>/Material/Video`) neu setzen.

## Anpassungen in Doku und Code

- **CLAUDE.md:** Projektstruktur-Block und Pfad-Konvention auf
  `projects/<Kunde>/<Projekt>/<Charge>/` umstellen.
- **tools/transcribe/WORKFLOW.md:** `audio/` → `Material/Audio/`, `script/` →
  `Material/Konzept/`, `output/` → `Ergebnisse/O-Ton-Pläne/`, `cache/` →
  `_intern/cache/`.
- **tools/transcribe/WORKFLOW-Footage.md:** `footage/` →
  `Ergebnisse/Sortierung/` (Pläne) bzw. `_intern/` (Manifeste, Undo-Logs).
- **tools/motion/WORKFLOW-Motion.md:** `motion/inputs/` → `Material/Video/`,
  `motion/renders/` → `Ergebnisse/Renders/`, Symlink-Beispiel anpassen.
- **tools/transcribe/src/niro_transcribe/project.py:** hartkodierte Pfade
  `audio/`, `cache/`, `output/` → `Material/Audio/`, `_intern/cache/`,
  `Ergebnisse/O-Ton-Pläne/`.
- **tools/transcribe/src/niro_transcribe/footage/pipeline.py:** analog prüfen
  und anpassen.
- **Tests** in `tools/transcribe/tests/` mitziehen; Testlauf als Verifikation.
- **Memory-Notizen** (niro-studio.md u. a.) aktualisieren.

## Risiko / Absicherung

Alles lokal und reversibel (Verschieben, git). Verifikation: Test-Suite von
`tools/transcribe` läuft grün; Symlink aufgelöst prüfbar; Stichprobe im Finder.
