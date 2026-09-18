# NIRO Musik-Library

Sammelt alle Songs aus den Projekten auf dem NAS in
`NIRO NAS/NIRO Productions/01_Projekte/03_Vorlagen und Tools/07_Musik Library/`,
sortiert nach Einsatzzweck, getaggt mit Artlist-Daten. Aufgebaut 16.09.2026.

**Regeln:** Auf dem NAS nur lesen — geschrieben wird ausschließlich unterhalb von
`07_Musik Library`. Nichts löschen oder verschieben. Nur Musik: keine SFX, Stems,
Loops, Musical Logos, Voiceover oder Aufnahmen. Tags nur in die Kopien.

**Von Hand sortieren ist erlaubt:** `build.py` legt Dateien, die in der Library fehlen oder
verschoben wurden, nie neu an und überschreibt keine seit dem Bau geänderten Dateien
(`von_hand` und `mtime` in `data/build_stand.json`). Der Katalog zeigt den tatsächlichen Ordner.

## Ablauf (neue Songs nachziehen)

```bash
cd tools/musik
venv/bin/python inventory.py          # NAS scannen (dauert einige Minuten), Dubletten zusammenführen
venv/bin/python artlist.py            # neue Songs im Artlist-Katalog suchen (Cache: data/artlist_treffer.json)
venv/bin/python artlist_details.py    # Genre, Mood, Instrument, Video Theme, Tempo, BPM
venv/bin/python kategorien.py         # Ordner bestimmen → data/plan.json (Verteilung wird ausgegeben)
venv/bin/python build.py --nur 5      # Probelauf
venv/bin/python build.py              # kopieren + taggen + MD5-Prüfung + _Katalog.csv
```

Envato-Songs und unklare Quellen stehen von Hand in `data/manuell.json`
(Schlüssel = `key` aus `data/inventar.json`).

## Was wohin kommt

- **Ordner:** Recruiting & Ads · Imagefilm & Corporate · Social Reels & Trends ·
  Event & Aftermovie · Emotional & Testimonial · Unklare Quelle.
  Punkte aus Artlist-Mood/-Genre/-Video-Theme/Tempo/BPM plus den NIRO-Projekten,
  in denen der Song lief (`kategorien.py`, Gewichte oben in der Datei).
- **Tags:** WAV bekommt RIFF-INFO (wie Artlist selbst) und zusätzlich einen
  ID3-Chunk; MP3 ID3v2.3; M4A iTunes-Tags. Kommentar = Einsatz, Stimmung, Genre,
  Video-Themes, Instrumente, Tempo/BPM, Quelle + Link, „Verwendet in".
- **Artlist-Schnittstelle:** `search-api.artlist.io/v2/graphql` — `songList`
  (Suche, `take` max. 60) und `songs(ids: [String!]!)` mit `categories` und
  `bpmRate`. Songseiten selbst sperrt Cloudflare für Skripte.
