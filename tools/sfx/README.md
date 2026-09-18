# NIRO SFX-Library

Sammelt die Soundeffekte aus den Projekten und Vorlagen auf dem NAS in
`NIRO NAS/NIRO Productions/01_Projekte/03_Vorlagen und Tools/08_SFX Library/`,
sortiert nach Sound-Typ, getaggt mit Artlist-Daten. Aufgebaut 16.09.2026.
Gegenstück zur Musik-Library (`tools/musik`).

**Regeln (User 16.09.2026):** Auf dem NAS nur lesen — geschrieben wird ausschließlich
unterhalb von `08_SFX Library`; nichts löschen oder verschieben. Keine Musik (Musik-Library,
Stems, Envato-Musik), keine Sprache (Voiceover, Aufnahmen, KI-Stimmen), nichts von
ElevenLabs, **ohne Adobe Sound Library** (bleibt in `03_SFX`). Mit drin: Intros/Logos/Jingles,
Atmos mit Stimmengewirr, die AI-SFX aus `03_SFX/AI SFX`. Tags nur in die Kopien.

**Von Hand sortieren ist erlaubt:** `build.py` legt Dateien, die in der Library fehlen oder
verschoben wurden, nie neu an und überschreibt keine seit dem Bau geänderten Dateien
(`von_hand` und `mtime` in `data/build_stand.json`). Der Katalog zeigt den tatsächlichen Ordner.

## Ablauf (neue SFX nachziehen)

```bash
cd tools/sfx
venv/bin/python scan.py          # NAS scannen (einige Minuten; eigene Libraries ausgenommen)
venv/bin/python inventory.py     # Ausschlüsse, ffprobe, Dubletten (Name + Dauer)
venv/bin/python artlist.py       # Artlist-SFX-Katalog (und Song-Gegenprobe) – Cache data/artlist_treffer.json
venv/bin/python kategorien.py    # Ordner + Quelle → data/plan.json; aussortierte Songs → data/songs_gefunden.json
venv/bin/python build.py --nur 10
venv/bin/python build.py         # kopieren + taggen + MD5-Prüfung + _Katalog.csv
venv/bin/python pruefen.py       # Abschlussprüfung (auch: Originale unverändert)
```

Neue Musik-Ordner in `tools/musik` vorher aktualisieren, sonst landen neue Songs als
Kandidaten hier (die Song-Gegenprobe in `artlist.py` fängt Artlist-Songs trotzdem ab).

## Wie sortiert wird

- **Sound-Typ** (`kategorien.py`): Stichworte im Dateinamen (am stärksten), kuratierte
  Vorlagen-Ordner (`2025 NEW SFX`, `Sound Effects Davinci`, Liquid Glass …) und
  Artlist-Kategorien (`sonCategories`, z. B. Transitions/Whooshes → Whoosh & Transitions).
- **Unklare Quelle:** YouTube-Downloads, Freesound (`123456__user__name`), Pixabay-artige
  Namen (`name-12345`) und Projektdateien ganz ohne Herkunft — Lizenz klären.
  Vorlagen ohne dokumentierte Herkunft bleiben in ihrem Typ-Ordner („NIRO-Vorlagen").
- **Artlist-Schnittstelle:** `search-api.artlist.io/v2/graphql` → `sfxList(term, page,
  sortBy: STAFF_PICKS, categoryIds: "")` mit `songs { songId songName artistName albumName
  durationTime nameForURL sonCategories { name parentName } }`; Link
  `https://artlist.io/sfx/track/<nameForURL>/<songId>`. Artlist-SFX-Dateien heißen
  „Anbieter - [Pack - ]Name“.
