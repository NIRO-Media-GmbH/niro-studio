# WORKFLOW: Thumbnail (saubere Standbilder aus fertigen Videos)

Trigger: **„Thumbnail: <Kunde>/<Projekt>[/<Charge>]“**, optional mit einzelnen Videos. **Nur auf ausdrücklichen Wunsch des
Users** (Vorgabe 21.09.2026): nie automatisch nach Exporten, AutoCut-Bauten oder Review-Ablagen. Auch nicht ungefragt
„gleich mitmachen“; höchstens in einer Zeile anbieten, wenn der User nach Covern fragt.

Spec: `docs/superpowers/specs/2026-09-21-thumbnail-design.md` · Plan: `docs/superpowers/plans/2026-09-21-thumbnail.md`

## Was rauskommt

- Je Video **3 Vorschläge** aus verschiedenen Einstellungen: `_1` = Empfehlung (Person), `_2` = nächstbestes Motiv,
  `_3` = möglichst das Thema (Produkt, B-Roll).
- Je Vorschlag zwei JPGs (Qualität 92, sRGB):
  - `<Video>_V<n>_Thumbnail_<k>.jpg` mit langer Kante 1920 (Reel-Cover 1080×1920),
  - `<Video>_V<n>_Thumbnail_<k>_4K.jpg` in Quellauflösung (nur wenn die Quelle größer als 1920 ist).
- `V<n>` ist die **Exportversion**, deren Bild die Frames zeigen.
- Ablage:
  - NAS `<Exportordner>/<Video>/Thumbnails/` (bei Setzer `04_Exportiert/<Video>/Thumbnails/`),
  - Studio `<Charge>/Ergebnisse/Thumbnails/<Video>/`,
  - Nachweis und Kontaktbogen in `<Charge>/_intern/thumbnails/`.
- Kein Eintrag in NIRO Review: Dort liegen Videos, keine Standbilder.

## Voraussetzungen

- Resolve läuft, das Projekt ist offen, und der User hat es **in dieser Session freigegeben**. Die Funktion legt nur eigene
  Objekte an (Bin „Claude Thumbnail …“, Timeline-Kopie) und löscht sie wieder; die Regeln aus
  `tools/resolve/WORKFLOW-Resolve.md` gelten.
- In der Kopie abgeschaltet werden Alpha-Clips (Grafik, Untertitel), Clips ohne Mediendatei (Text+, Titel), die
  SafeZone-Spur und Clips mit Composite-Modus ≠ Normal (Film Burns, Light Leaks im Modus Screen). Liegt ein anderer Effekt
  als eigener Clip ohne Alpha im Modus Normal über dem Bild, fällt er nicht darunter: vorher per Readback prüfen.
- Die Timeline, aus der gerendert wird, muss inhaltlich dem Export `<Video>_V<n>.mp4` entsprechen. Die Prüfung vergleicht
  beide und bricht bei Abweichung ab.
- Werkzeuge: `tools/autocut/venv/bin/python`, ffmpeg, swiftc. Der Vision-Bewerter wird beim ersten Lauf nach
  `tools/thumbnail/bin/` gebaut.

## Ablauf

    PY="tools/autocut/venv/bin/python"; TH="tools/thumbnail/thumbnail.py"
    CHARGE="projects/<Kunde>/<Projekt>/<Charge>"; EXP="<NAS …/04_Exportiert>"

0. `sh tools/studio_abgleich.sh --charge "$CHARGE"`.
1. **Videos, Timelines und Versionen bestimmen.** Den Exportordner und die aktuelle Version je Video liefern
   Chargen-Protokoll und Exportordner.
   - Timeline-Name und Exportversion können auseinanderlaufen, wenn der User in place nachgebessert hat. Beispiel Setzer
     21.09.: Timeline `…_V3` enthält den Export V4.
   - Standard ist die höchste `<Video>_V<n>.mp4`; `--version` nur bei Bedarf.
2. **Vorschlagen**, je Video:

       "$PY" "$TH" vorschlagen "$CHARGE" --video "<Video>" --exportordner "$EXP" --timeline "<Resolve-Timeline>" --projekt "<Resolve-Projekt>"

   Ohne Resolve geht es mit einer sauberen Videodatei ohne Grafik: `--datei <mp4/mov>` statt `--timeline`/`--projekt`;
   die Schnitte kommen dann aus ffmpeg `scdet`.
3. **Kontaktbogen ansehen** (`_intern/thumbnails/<Video>_V<n>_kandidaten.jpg`, rot = Vorschlag, `#` = Frame).
   - Wirkt das Gesicht natürlich? Kein Blinzeln, kein halbes Wort, kein Wegschauen, keine Grimasse.
   - Ist das Bild scharf, und zeigt es die Person mit dem Thema (Produkt, Gericht, Ort)?
   - Das Thema muss offen zu sehen sein: geöffnete Packung statt geschlossener, Gericht ohne Haube.
   - Kein Stock-Material als Cover (Setzer 08: das Duroc-Schwein aus dem Stock-Clip), nur eigenes Drehmaterial.
   - Offene Kundenfragen gelten auch fürs Cover (Wurst & Liebe 21.09.): kein Alkohol im Bild, solange der Kunde das nicht
     freigegeben hat (Bierflasche hinter der Currywurst, Aperol auf dem Tisch), keine Kindergesichter ohne Einwilligung,
     keine fremden Logos (Dienstkleidung, Taschen), keine fremde Marke (Neonlogo der Nachbarstation im Video der anderen Marke).
   - Straßen- und Innenraum-Totalen ohne Menschen bewertet Vision oft hoch (Schärfe), sie wirken als Cover aber leer — ersetzen.
   - Prozess-Bilder wie Fleischwolf oder Maschine unterschätzt Vision (Utility-Abzug); solche Kandidaten gezielt ansehen.
   - Enge Kandidaten groß ansehen (die Kandidaten-JPGs liegen in `work/<Video>_V<n>_kandidaten/k_<Frame/5>.jpg`).
   - Andere Wahl oder Reihenfolge per `--wahl <Frame,Frame,Frame>`, mit Grund.
4. **Ablegen:**

       "$PY" "$TH" ablegen "$CHARGE" --video "<Video>" [--wahl 225,55,130] [--grund "…"]

   Kopiert mit `cp -n` und Byte-Vergleich. Nummern zählen über vorhandene Dateien weiter, eine zweite Runde ergibt `_4…_6`.
   Master und Kandidaten werden danach gelöscht.
5. **Nachkontrolle:** In Resolve per MCP lesen: Timeline-Anzahl wie vorher, keine „Claude Thumbnail“-Bins oder
   -Timelines, Ansicht des Users unverändert.
6. **Bericht im Chat:** je Video die drei Motive in einer Zeile und der NAS-Ordner. Dazu ein Protokoll-Eintrag und
   `studio_abgleich.sh --charge`.

## Auswahl in Kürze

- Kandidat ist jeder 5. Frame; 2 Frames vor und nach einem Schnitt fallen weg.
- Apple Vision bewertet Ästhetik, Gesichtsqualität, Lidöffnung und Mundöffnung; dazu kommt die Schärfe im Gesicht bzw. in
  der Bildmitte.
- Punkte für eine Person: 0,45·Qualität + 0,35·Ästhetik + 0,20·Schärfe. Abzüge gibt es für Augen zu (−0,5),
  Mund offen (bis −0,2) und ein Gesicht am Rand oder unter 55 % der Bildhöhe (−0,3).
- Punkte für ein Thema: 0,6·Ästhetik + 0,4·Schärfe.
- Schwellen stehen in `tools/thumbnail/auswahl.py`, Tests in `tools/thumbnail/tests/`
  (`"$PY" -m pytest tools/thumbnail/tests -q`).
- Die Automatik erkennt nicht, ob das Thema zu sehen ist (z. B. Gericht unter der Haube). Das entscheidet der Blick auf
  den Bogen.

## Fehlerbilder

| Meldung | Abhilfe |
|---|---|
| „Offenes Projekt … ≠ Freigabe …“ | Nichts geschrieben. Den User fragen, welches Projekt gemeint ist; nie ein Projekt laden. |
| „Export … hat N Frames, die Quelle M“ | Timeline und Exportversion passen nicht zusammen: Version klären oder `--version` setzen. |
| „Saubere Quelle weicht vom Export ab“ | Grading, Ausschnitt oder Timeline stimmen nicht. Timeline prüfen; die Kopie hat womöglich nicht alles übernommen. Der Master wird gelöscht. |
| „Overlays ließen sich nicht abschalten“ | Resolve lehnt Schreibzugriffe ab (Clip im Inspector offen, Wiedergabe) und räumt auf. Später erneut versuchen. |
| „Aufräumen unvollständig“ | Per MCP nach „Claude Thumbnail“-Bins und -Timelines suchen und nur diese eigenen Objekte löschen. |
| Warnung Detail-Faktor < 1,15 | Womöglich aus Proxys gerendert. Den Bogen scharf prüfen, im Zweifel die Proxy-Einstellung mit dem User klären. |
| „Offene Runde für …“ | Ein Vorschlag wurde nicht abgelegt. Erst `ablegen` oder den Nachweis prüfen. |
