# NIRO AutoCut — Stufe 4: Schnitt-Profil aus der Cloud-Bibliothek (Entwurf für 04.09.)

> Entwurf vom 03.09. abends. Wird am 04.09. mit dem User finalisiert, sobald die
> Liste der Cloud-Projektnamen vorliegt. Baut auf `resolve_api.read_timeline`
> und `scripts/autocut_read_timelines.py` aus dem Hauptplan auf.

> **Hinweis 09.09.2026:** `LoadCloudProject` verstößt gegen die Cloud-Regel des Users (Cloud-Projektbibliothek
> tabu, siehe `tools/resolve/WORKFLOW-Resolve.md`). Stufe 4 läuft nur mit ausdrücklicher Freigabe je Projekt
> oder mit Timelines, die der User selbst im geöffneten Projekt bereitstellt.

**Ziel:** Aus den fertigen Schnitten des Users (Blackmagic-Cloud-Projekte +
MP4s) ein dauerhaftes Schnitt-Profil ableiten: messbare Kennzahlen je Videotyp
und Regeln in Prosa mit Beispielen, das AutoCut in Stufe 3 (B-Roll) und Stufe 1
(Pausen/Handles) mitlädt. Dazu die Korrektur-Schleife.

## Ablage

```
tools/autocut/profile/
├── archiv/<projekt>/<timeline>.otio      Export je Timeline (dauerhaft, unabhängig von der Cloud)
├── archiv/<projekt>/<timeline>.json      read_timeline-Struktur (Items je Spur, Marker, Settings)
├── archiv/<projekt>/projekt.json         Name, UniqueId, Datum, Timelines, MP4-Abgleich
├── kennzahlen.json                        Statistik je Timeline + Aggregate je Typ
├── <typ>.yaml                             Werte, die defaults.yaml/broll überschreiben (z. B. recruiting-9x16.yaml)
├── <typ>.md                               Regeln in Prosa + Beispiele (Aussage → Bildfolge)
└── default.md / default.yaml              Startprofil (bleibt Fallback)
```

## Schritte

1. **Projektliste** vom User (Namen wie im Cloud-Tab). AutoCut kann Cloud-Projekte
   nicht auflisten (API bietet nur `LoadCloudProject` per Name).
2. **Lesen** (`scripts/autocut_profile_read.py --projekte liste.txt`): für jeden Namen
   `pm.LoadCloudProject({CLOUD_SETTING_PROJECT_NAME: name})` — nur, wenn der User
   gerade nicht schneidet (wechselt das aktive Projekt); pro Timeline
   `read_timeline` → JSON + `Export(EXPORT_OTIO)`; danach das ursprüngliche Projekt
   wieder laden. Nichts speichern, nichts ändern.
3. **Finale Timeline erkennen:** Namensmuster (`_V\d+`, „final", „Master"),
   höchste Versionsnummer, und Abgleich mit MP4-Dauern aus `04_Exportiert/`
   bzw. `05_Finale Videos/` (Dauer ±2 s) → `projekt.json` markiert `final`.
   Sync-Hilfstimelines (V1 FX3/V2 a7, ein Interview) werden als `sync`
   erkannt und liefern die Sync-Konvention, nicht den Stil.
4. **Kennzahlen** (`profile.py`): pro finaler Timeline — Format (Auflösung,
   Hoch/Quer), Länge, Zahl der O-Ton-Clips, Sprecher-Vorlauf vor erster B-Roll
   je Sprecher-Erstauftritt, B-Roll-Längen (Median, P10/P90), Abdeckungsgrad
   der O-Töne, Lücken zwischen O-Tönen, Rückkehr zum Sprecher vor Beat-Ende,
   Anteil Schnitte auf Sprechpausen (mit Transkript, falls die Charge im
   Studio liegt), Hook-Länge, Endcard-Länge, Musik-Spur ja/nein. Aggregation
   je Typ (Recruiting-Ad 9:16, Imagefilm 16:9, Reel).
5. **Regeln** (Claude in der Session, `prompts/profile-rules.md`): Kennzahlen +
   3–5 Beispiel-Timelines (kompakt: Aussage → Bildfolge mit Dauern) →
   `<typ>.md` (Prosa, Beispiele) und `<typ>.yaml` (Zahlen). User liest gegen,
   streicht, ergänzt.
6. **Korrektur-Schleife** (`scripts/autocut_diff_timeline.py <Charge>`): liest
   die vom User bearbeitete AutoCut-Timeline (per Name aus `build.json`),
   vergleicht mit `timeline.json`/`broll_plan.json` (verschoben, gelöscht,
   ersetzt, verlängert/gekürzt), schreibt `Ergebnisse/Rohschnitt/<video>-diff.md`
   und Regelvorschläge; Übernahme ins Profil nur nach Freigabe.

## Offene Fragen an den User (04.09.)

- Welche Cloud-Projekte zählen? Alle, oder eine Auswahl der „typischen" Schnitte
  je Videotyp (5–10 pro Typ reichen für belastbare Kennzahlen)?
- Sind die MP4s nach `04_Exportiert/`-Konvention benannt (Versionsnummer), damit
  die finale Timeline sicher zugeordnet werden kann?
- Gibt es Timelines, die bewusst NICHT als Vorbild gelten (Probecutter,
  Experimente)?
