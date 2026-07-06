# Footage-Sortierer — Design (Spec)

Datum: 2026-07-06
Status: bestätigt (Design), operativer Lauf für Projekt „LohiBW Recruiting" ausstehend

## Zweck

Rohmaterial (viele MP4s, mehrere Kameras) automatisch nach einem Konzept-Script
sortieren, in dem pro Szene der **gesprochene Satz** steht. Das Tool ordnet jeden
Clip anhand seines **transkribierten Tons** (nicht Dateiname) einer Script-Szene,
einer Interview-Person oder B-Roll zu und legt eine geordnete Ordnerstruktur an.

**Eiserne Anforderung: kein Footage geht verloren.** Nichts wird je gelöscht;
alles Nicht-Zuordenbare landet sichtbar in `_nicht_zugeordnet/`; das Verschieben
ist geprüft (Prüfsumme) und über ein Log umkehrbar.

## Betriebsmodell (wie NIRO Transcribe)

Läuft über die Claude-App: **Claude ist Orchestrator UND „Brain".** Die
kreativen/semantischen Schritte (Clip → Szene/Person/B-Roll zuordnen, Take- und
Multi-Cam-Erkennung) macht Claude in der Session anhand eines Prompt-Files. Nur
die **mechanischen** Teile sind Code:

1. Audio aus MP4 extrahieren (ffmpeg).
2. Transkribieren mit **ElevenLabs Scribe, Diarisation an** — **kein Whisper**
   (bei dieser Menge zu langsam). Ergebnis pro Clip nach Inhalts-Hash gecacht.
3. Verschiebe-Ausführung mit Vorher/Nachher-Prüfung und Undo-Log.

Der einzige externe API-Key bleibt `ELEVENLABS_API_KEY`.

## Eingaben & Ordner-Konvention

Footage liegt auf externer SSD (nicht im Repo, ~300 GB):

```
/Volumes/NIRO-SSD-02/Lohi Backup/01_Footage/
   Kamera-A FX3 1/   (11 Clips, + XML-Sidecar je Clip)
   Kamera-B A7iv/    (11 Clips)
   Kamera-C FX3 2/   (113 Clips)   ← A-Cam, die meisten Takes
```

- Alle Kamera-Unterordner werden **rekursiv** durchsucht (MP4/MOV).
- XML-Sidecars (Sony-Metadaten, u. a. Aufnahmezeit) helfen, Multi-Cam-Clips
  desselben Moments zu gruppieren; **primär** wird aber über Transkript-Inhalt
  zugeordnet.

Konzept-Script: Google-Sheets-Export als PDF
(`Lohnsteuerhilfe Baden-Württemberg - Recruiting-Videos - Google Sheets.pdf`),
Tabelle mit Spalten u. a. `Video-Nr | Videotitel | Szenen-Nr | Sprechtext/Inhalt`.
4 Videos, je Hook A/B/C + Szene 1…N. Claude parst das Script in der Session in
strukturierte Szenen (kein robuster Tabellen-Parser nötig).

Arbeits-/Ausgabe-Aufteilung:
- **Repo** `projects/LohiBW Recruiting/`: `script/` (Kopie des PDF),
  `cache/` (Scribe-JSON pro Clip), `zuordnungsplan.md`, `_verschiebe_log.md`.
- **SSD** `…/Lohi Backup/sortiert/`: die verschobene Zielstruktur (große Dateien
  bleiben auf der SSD). Log/Plan werden dorthin gespiegelt, damit die Sortierung
  selbst-dokumentierend neben dem Material liegt.

## Klassifikation pro Clip

Nach Transkript (Kameramann/Interviewer per Diarisation ausgeschlossen, zählt nie):

1. **Gescripteter Satz** (Priorität) — gesprochener Text matcht ~wörtlich eine
   `Sprechtext/Inhalt`-Zeile, die als echter Sprech-Satz gedreht wurde.
   → `sortiert/<Videotitel>/NN_<Szene>_<Kurztext>/` (NN = Script-Reihenfolge).
2. **Freies Interview** — Script-Zeilen der Form „Frage an eine Mitarbeiterin: …
   Sie erzählt, dass …" sind **frei gesprochen** (Antwort nur paraphrasiert).
   Solche Clips werden **nicht** einer Szene zugeordnet, sondern nach Person:
   → `sortiert/Interviews/<Name>/`, **Name aus dem Transkript**
   (Selbstvorstellung/genannter Name). Kein Name ableitbar → `Interviews/_ohne_Namen/`
   und im Plan zur manuellen Benennung markiert.
   (Cross-File-Personenidentität ist nur sicher, wenn der Name im Clip fällt —
   bekannte Grenze; Zweifelsfälle gehen in den Review-Plan, nicht ins Blaue.)
3. **B-Roll / kein verwertbarer O-Ton** — kein Interviewten-Sprech, nur
   Ambiente/Kameramann, oder „Hook C – bildlicher Einstieg ohne gesprochenen
   Text". → `sortiert/B-Roll/` (alles in einen Ordner).
4. **Sicherheitsnetz** — nicht sicher zuordenbar → `sortiert/_nicht_zugeordnet/`.

### Multi-Cam
Ein gescripteter Satz von mehreren Kameras = mehrere Clips → **alle** in denselben
Szenen-Ordner, darin **nach Kamera getrennt** (`Kamera-A/…`, `Kamera-B/…`), damit
die Winkel-Info beim Verschieben erhalten bleibt.

### Mehrere Sätze in einem Clip
Sollte selten sein. Falls doch: **Primärsatz-Regel** — Clip landet im Ordner des
ersten enthaltenen Satzes; Zuordnungsplan vermerkt die weiteren Sätze mit
von–bis, damit sie beim Schnitt auffindbar sind. Keine Datei wird dupliziert.

### Takes
Mehrere Aufnahmen desselben Satzes (Versprecher/Wiederholungen) = Takes → alle in
denselben Szenen-Ordner (bzw. je Kamera). Reihenfolge/Kennzeichnung im Plan.

## Sicherheits-/Ausführungsmodell — Zwei Phasen

**Phase 1 — Analyse (nur lesen).** Audio extrahieren, Scribe-Transkript je Clip
(gecacht), Claude klassifiziert und ordnet zu. Es wird **keine** Datei bewegt.

**Phase 2 — Zuordnungsplan (Review-Gate).** `zuordnungsplan.md`: pro Video/Szene
die zugeordneten Clips (mit Kamera, Take, von–bis, Match-Sicherheit), plus
Interviews-nach-Person, B-Roll und `_nicht_zugeordnet`. **David prüft/korrigiert
im Chat.** Bis hier wurde nichts verschoben.

**Phase 3 — Geprüftes Verschieben (nur nach „go").** Ein Skript verschiebt exakt
nach Plan:
- Vorher: jede Quelle existiert, Zielordner wird angelegt, Namenskollisionen
  werden erkannt (Clip wird nie überschrieben).
- Verschieben von MP4 **inkl. zugehörigem XML-Sidecar**.
- Nachher: Ziel vorhanden, Größe/Prüfsumme identisch zur Quelle.
- `_verschiebe_log.md`: jede Bewegung (von → nach, Prüfsumme) → **jede Bewegung
  umkehrbar**.
- Bei jedem Fehler: Stopp, nichts Halbfertiges, klare Meldung.

## Sicherheitsgarantien (Zusammenfassung)

- **Nie löschen.** Verschieben, nie `rm`.
- **Vollständigkeit prüfbar:** Anzahl Quell-Clips == Summe aller Ziel-Clips +
  `_nicht_zugeordnet`. Diese Bilanz steht im Plan und im Log.
- **Prüfsumme vor/nach** jedem Move; Abbruch bei Abweichung.
- **Undo** über `_verschiebe_log.md`.
- **Sichtbares Auffangbecken** `_nicht_zugeordnet/` statt stillem Verwerfen.

## Bewusst außerhalb v1

- Kein Schneiden von Clips (Multi-Satz-Clips bleiben ganz, Primärsatz-Regel).
- Keine automatische Personen-Zuordnung ohne im Clip genannten Namen.
- Kein DaVinci/Premiere-Import (EDL/XML-Timeline).

## Konkreter Erst-Lauf

Projekt „LohiBW Recruiting": 135 Clips (11/11/113), ~300 GB, 4 Videos laut Script,
Pfade wie oben. Reihenfolge: Setup prüfen (ffmpeg, ELEVENLABS_API_KEY) → Phase 1 →
Plan → Review → Phase 3.
