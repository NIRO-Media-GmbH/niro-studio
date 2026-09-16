# NIRO Studio

Master-Werkzeug von NIRO Media: sieben Funktionen, ein Projektsystem, eine Session.

## Projektstruktur

Alle Projektdaten liegen unter `projects/<Kunde>/<Projekt>/<Charge>/`.
Chargen-Name: `JJJJ-MM Beschreibung` (z. B. „2026-07 Erster Dreh") — die
Chargen-Ebene existiert immer, auch bei nur einer Charge.

    projects/<Kunde>/<Projekt>/<Charge>/
    ├── Protokoll.md        Kurzprotokoll pro Session
    ├── Material/           was reinkommt
    │   ├── Audio/             Interview-WAVs
    │   ├── Konzept/           Konzept-PDF
    │   └── Video/             Inputs für Animationen
    ├── Ergebnisse/         was fertig ist
    │   ├── O-Ton-Pläne/       Interview-Pipeline
    │   ├── Sortierung/        Zuordnungspläne Footage
    │   ├── Renders/           fertige Animationen
    │   ├── Export/            Renders aus Resolve (Review-Kopien, Lieferungen)
    │   └── Fotos/             entwickelte RAW-Fotos (+ web/)
    └── _intern/            was die Tools brauchen (cache, work, Logs, Manifeste)

Rohes Drehmaterial bleibt auf externen SSDs; hier liegen nur Arbeits- und
Ergebnisdateien. Unterordner nur anlegen, wenn die Funktion genutzt wird.

**Protokoll-Pflicht:** Bei jeder Arbeit an einer Charge (egal welche Funktion)
`Protokoll.md` im Chargen-Ordner fortschreiben — pro Session ein kurzer
Eintrag: Datum, was gemacht, was geliefert (Dateien), Entscheidungen/Offenes.
Datei bei der ersten Session anlegen.

## Die Funktionen (Trigger)

| Trigger im Chat | Funktion | Anleitung |
|---|---|---|
| „Video-Auswahl: <Kunde>/<Projekt>[/<Charge>]" | Interviews → sortierte O-Ton-Pläne | `tools/transcribe/WORKFLOW.md` |
| „Footage sortieren: <Pfad>" + Konzept | Roh-MP4s nach Konzept-Script sortieren | `tools/transcribe/WORKFLOW-Footage.md` |
| „Schnittplan: <Kunde>/<Projekt>[/<Charge>]" | Roh-Footage → Cutter-Schnittanweisungen (PDF, Lesbarkeit vor Seitenbudget, max. 20 Seiten) | `tools/transcribe/WORKFLOW-Schnittplan.md` |
| „Animation: <Kunde>/<Projekt>[/<Charge>]" | Remotion Motion Graphics | `tools/motion/WORKFLOW-Motion.md` |
| „Foto: <Kunde>/<Projekt>[/<Charge>]" | ARW-RAWs → Culling, Look, fertige Bilder | `tools/photo/WORKFLOW-Foto.md` |
| „AutoCut: <Kunde>/<Projekt>[/<Charge>]" | Schnittplan → Rohschnitt-Timeline in Resolve (roh) → B-Roll aus der Auswahl-Timeline des Users → Feinschnitt (A/B-Wechsel, Grafik, Ton, Musik, SFX, Grading, Begradigen; Vorlagen) · Finalisieren (Pegel, Zeitlupe) · Kantenprüfung am Export · Review in Dropbox Replay (Upload nach OK, Kommentare holen) | `tools/autocut/WORKFLOW-AutoCut.md` |
| „Resolve: <Aufgabe>" | Ad-hoc-Arbeit im offenen Resolve-Projekt über den nativen MCP (lesen, prüfen, rendern, importieren) | `tools/resolve/WORKFLOW-Resolve.md` |

Beim Trigger die jeweilige Workflow-Datei lesen und ihr folgen.
Projektpfad-Konvention überall: `projects/<Kunde>/<Projekt>/<Charge>/` (relativ
zu dieser Studio-Wurzel). Bei nur einer Charge reicht Kunde/Projekt im Trigger —
die Charge wird dann automatisch gefunden.

## Resolve-Regeln (MCP und Skripte)

- **Standard nur lesen.** Schreiben nur in Projekten, die der User in dieser Session
  ausdrücklich freigibt; vor jedem schreibenden Skript den Projektnamen lesen, nennen und
  mit der Freigabe abgleichen — bei Abweichung nichts schreiben, sondern nachfragen.
- **Cloud-Projektbibliothek tabu:** keine Projekte laden, anlegen, löschen, wechseln;
  keine Cloud-Einstellungen. Gearbeitet wird nur im geöffneten Projekt.
- **Auch im freigegebenen Projekt nur anhängen** (neue Bins, Timelines, Marker, Renders);
  gelöscht werden nur eigene Objekte derselben Session; am Ende Timeline und Media-Pool-Bin
  des Users wieder aktivieren.
- **Cloud-Projekte speichern sofort (Live Save):** erst lesen, dann klein schreiben,
  Readback, Bericht mit Projekt- und Timeline-Namen und Zahlen.
- **Nie schreiben, während der User abspielt:** Schreibaufrufe hängen dann oder laufen
  nach einem Abbruch später trotzdem. Arbeitet der User parallel in Resolve, Timeline-Wechsel
  vorher abstimmen; von Hand Geändertes nie überschreiben. Gemessenes API-Verhalten:
  `tools/resolve/WORKFLOW-Resolve.md`.
- **Dropbox Replay:** Upload nur nach OK je Upload; in Replay nur fehlende Ordner unter „Autocut" anlegen und
  eigene Uploads dorthin verschieben — nichts teilen, beantworten, abhaken, löschen, archivieren, umbenennen oder
  kommentieren (ein Kommentar von Claude käme als FrameIO-Marker zurück und würde als User-Kommentar gelesen);
  Replay-Marker (Farbe „FrameIO") nie löschen (löscht die Kommentare in Replay); hochgeladene Timelines nicht
  löschen oder ändern. Ablauf: `tools/autocut/WORKFLOW-AutoCut.md` („Review in Replay").

## Umgebung

- **Python (transcribe):** `tools/transcribe/venv/bin/python`; `.env` mit
  API-Keys liegt in `tools/transcribe/.env`.
- **Remotion (motion):** `cd tools/motion && npm run studio`; Kompositionen
  und `brand.json` pro Kunde in `tools/motion/src/clients/<kunde>/`.
- **Foto (photo):** RAW-Stufe `dcraw_emu` (libraw, Homebrew) + ImageMagick;
  Kunden-Looks als HALD-LUT in `tools/photo/looks/<kunde>/`; RawTherapee liegt
  quarantäne-blockiert in `/Applications` (GUI einmal öffnen würde ihn freischalten).
- **Resolve (MCP):** nativer Server `ResolveMCP` aus dem App-Bundle, registriert in
  `.mcp.json` (Projekt-Scope); braucht laufendes Resolve Studio 21.1 mit „External
  scripting = Local". Werkzeuge `run_script` (Sandbox-Python 3.14, `resolve`/`project`
  vorinjiziert, Rückgabe über `result`), `search_scripting_api`, `get_scripting_docs`;
  Stubs und README lokal unter `/Library/Application Support/Blackmagic Design/DaVinci
  Resolve/Developer/Scripting/`. AutoCut nutzt weiter `tools/autocut/venv/bin/python`.
- **Neues Projekt:** Ordner nach Bedarf anlegen, z. B.
  `mkdir -p "projects/<Kunde>/<Projekt>/<Charge>/Material/Audio"`.
