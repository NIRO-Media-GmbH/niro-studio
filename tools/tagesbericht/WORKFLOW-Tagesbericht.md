# Funktion „Tagesbericht" — Haupt-Check beider Studio-Macs

Trigger im Chat: „Tagesbericht" (heute) · „Tagesbericht: gestern" · „Tagesbericht: <JJJJ-MM-TT>".
Spec: `docs/superpowers/specs/2026-09-17-tagesbericht-design.md` · Sammler: `tools/tagesbericht/README.md`.

Der Bericht fasst zusammen, was an einem Tag auf beiden Macs gemacht wurde, welche Werkzeug-Änderungen entstanden sind,
was davon auf `main` gehört, wo es hakte und was offen bleibt. **Er empfiehlt nur.** Geschrieben wird ausschließlich
unter `berichte/`; keine Commits, Merges, Pushes, keine Änderungen an Chargen oder Werkzeug. Merges führt Claude nur in
einer eigenen Session auf ausdrücklichen Auftrag aus.

## Ablauf

1. **Tag bestimmen:** heute, gestern oder das Datum aus dem Trigger. Im Hauptordner des Repos arbeiten (erste Zeile von
   `git worktree list`).
2. **Sammeln und abgleichen:**

   ```bash
   git fetch -q
   python3 tools/tagesbericht/sammler.py --tag <JJJJ-MM-TT>
   ```

   Der Sammler schreibt den Tagesstand dieses Macs und spiegelt `berichte/` (holt die Datei des anderen Macs). Schlägt
   `git fetch` fehl, nur melden. Fehlt das NAS (Meldung „NAS nicht verbunden"), steht das im Bericht unter „Stand".
3. **Lesen:** alle `berichte/<Tag>/*.md` außer `Tagesbericht.md` (eine Datei je Mac); den jüngsten früheren
   `berichte/<Tag'>/Tagesbericht.md` für den Übertrag; bei Bedarf `berichte/<Tag>/<Mac>.patch` (Inhalt unversionierter
   Änderungen des jeweiligen Macs), Protokolle und Specs. Bekannte Macs = alle `<Mac>.md`-Namen unter `berichte/*/`;
   fehlt ein Mac für den Tag, seinen jüngsten vorhandenen Tag nennen.
4. **`berichte/<Tag>/Tagesbericht.md` schreiben** nach der Vorlage unten. Existiert schon einer, wird er ersetzt; die
   Zeile unter dem Titel nennt dann „ersetzt Fassung von <HH:MM>".
5. **Abgleichen und melden:** `sh tools/studio_abgleich.sh --berichte`; im Chat die Kurzfassung (eine Bildschirmseite:
   Stand, Empfehlungen, Probleme, Offen) und der Pfad der Datei.

## Vorlage `Tagesbericht.md`

    # Tagesbericht <TT.MM.JJJJ>
    Erstellt <JJJJ-MM-TT HH:MM> auf <Mac> · Quellen: <Mac1>.md (Stand HH:MM), <Mac2>.md (Stand HH:MM) · Vorbericht: <Datum oder „keiner“>

    ## Stand
    Je Mac: Zeit des Sammler-Laufs, Sitzungen, Commits. Fehlt ein Mac: „<Mac>: kein Tagesstand für <Tag>, letzter <Datum>“ ganz oben.

    ## Gemacht
    Je Mac, gruppiert nach Chargen und Werkzeug; ein bis zwei Sätze je Sitzung mit Quelle (Sitzungs-Kennung + Zeit oder Commit).
    Die Sammelzeile des Tagesstands („… — in N Chargen“) bleibt eine Zeile.

    ## Neue Funktionen und Werkzeug-Änderungen
    Je Werkzeug (autocut, motion, transcribe, resolve, photo, musik, sfx, studio): auf main gekommen · auf Branches · unversioniert (mit Mac).

    ## Empfehlung für main
    Nummeriert; je Punkt Was, Warum, Befehl, Mac. Nichts wird ausgeführt.
    - ungepushte Branch-Commits → Merge- oder Fast-Forward-Befehl
    - unversionierte Änderungen → Einschätzung „fertig / halbfertig / Wegwerf“ (Quelle: Schlussberichte, Patch) und Vorschlag Commit oder Verwerfen
    - überholte Branches (0 vor, viele hinter) → Löschbefehl
    - Punkte des anderen Macs als Auftrag „auf <Mac>: …“

    ## Probleme und Auffälligkeiten
    Gehäufte Tool-Fehler, abgebrochene Sitzungen, Sitzungen ohne Schlussbericht, offene Fragen aus Schlussberichten, Hinweise des Sammlers.

    ## Offen und Übertrag
    Offene Punkte des Tages; Punkte des Vorberichts mit Alter („seit 3 Tagen“); Erledigtes einmal als erledigt nennen, dann weg.

    ## Chargen-Stand
    Berührte Chargen, Lieferungen (neue Dateien unter Ergebnisse/), fehlende Protokoll-Einträge.

## Regeln

- Jede Aussage nennt Mac und Sitzung (Kennung, Zeit) oder Commit (Hash). Unsicheres steht als „vermutlich …".
- Nichts aus dem Gedächtnis ergänzen, was nicht in den Quellen des Tages steht; Tagesstände verdichten, nicht wiederholen.
- Deutsch, Stil der Protokolle. Kurzfassung im Chat höchstens eine Bildschirmseite.
- Keine Commits, Merges, Pushes, keine Änderungen außerhalb von `berichte/` — auch nicht „nur schnell" für einen
  offensichtlichen Punkt. Der User entscheidet und beauftragt in einer eigenen Session.
