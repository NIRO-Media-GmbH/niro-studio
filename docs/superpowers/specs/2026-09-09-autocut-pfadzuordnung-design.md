# AutoCut — Pfad-Zuordnung NAS → SSD (Spec)

Datum: 2026-09-09 · Status: Ansatz vom User freigegeben („Pfad-Zuordnung in AutoCut"), Umsetzung als
Voraussetzung für den neuen MEK-Schnitt im Testprojekt „MCP MEK Test".

## Anlass

Die AutoCut-Arbeitsdateien der MEK-Charge (`media.json`, `sync.json`, `cutlist.json`, `broll_index.json`,
`timeline.json`) tragen die NAS-Pfade vom 04.09. (`/Volumes/NIRO NAS/…/01_Projekt-2xAds1xImagefilm_24.06.26/…`).
Das Material liegt jetzt auf der SSD `NIRO-SSD-03` (`/Volumes/NIRO-SSD-03/01_Projekt-2xAds1xImagefilm_24.06.26/…`,
identischer Unterbaum, alle 28 Interview-Originale + Proxies und alle 463 B-Roll-Clips vorhanden), der Media Pool
des Testprojekts referenziert die SSD-Pfade (901 Clips, 530 mit Proxy). Ohne Zuordnung findet AutoCut die
Media-Pool-Einträge nicht, versucht Importe vom nicht gemounteten NAS und scheitert. Laut CLAUDE.md liegt Rohmaterial
grundsätzlich auf externen SSDs — die Zuordnung ist also der Normalfall, nicht die Ausnahme.

## Entscheidungen

| Frage | Entscheidung |
|---|---|
| Wo steht die Zuordnung? | `path_map` in `tools/autocut/defaults.yaml` (Standard `{}`), je Charge überschrieben in `<Charge>/_intern/autocut/config.yaml` — Schlüssel = Präfix in den Arbeitsdateien, Wert = Präfix, unter dem die Dateien jetzt liegen. |
| Was bleibt Schlüssel? | Alle Arbeitsdateien und Media-Dicts behalten die Originalpfade (NAS). Zugeordnet wird nur beim Zugriff: Media-Pool-Suche/Import, Proxy-Link, Pegelmessung, Proxy-Prüfung. |
| Mehrere Präfixe? | Erlaubt; der längste passende Präfix gewinnt; Vergleich NFC-normalisiert und an Ordnergrenzen (`a` passt auf `a/…`, nicht auf `ab/…`). Kein Treffer → Pfad unverändert. |
| Rückweg SSD → NAS? | Nicht nötig; Resolve liefert beim Readback SSD-Pfade, AutoCut vergleicht Items über Namen/Positionen, nicht über Pfade. |
| Nicht im Umfang | `autocut_prepare.py`, `autocut_sync.py`, `autocut_index_broll.py`, `autocut_index_sections.py` (laufen beim Anlegen einer Charge — dann steht der aktuelle Pfad ohnehin im Index). Folgeaufgabe, falls eine alte Charge komplett neu aufgebaut werden muss. |

## Design

1. **`charge.py`:** Funktion `map_path(path, path_map) -> str` (reine Funktion, s. o.) und Methode
   `Charge.map_path(p)` mit `self.config.get("path_map") or {}`. `defaults.yaml` erhält `path_map: {}`.
2. **`resolve_api.ResolveSession`:** neuer Konstruktor-Parameter `path_map=None`; Methode `map_path(p)`.
   `find_media_item` sucht den zugeordneten Pfad; `import_media` sucht und importiert zugeordnete Pfade, liefert
   das Dict aber mit den **Original**-Schlüsseln (`out[p]`); `link_proxy` ordnet den Proxy-Pfad zu.
3. **`ton.py`:** `measure_a1_items(..., map_path=None)` misst am zugeordneten Pfad; Cache-Schlüssel und
   `ton.json`-Einträge behalten den Originalpfad. `build_ton` reicht `charge.map_path` durch.
4. **Skripte:** `autocut_build.py`, `autocut_place_broll.py`, `autocut_finalize.py`, `autocut_export_xml.py`,
   `resolve_probe.py`, `resolve_probe_xml.py`, `resolve_probe_api.py` übergeben `path_map=ch.config.get("path_map")`
   an die Session. `resolve_probe_xml.py` und `autocut_place_broll.py` rufen `proxy_for(ch.map_path(p))`.
5. **Doku:** `WORKFLOW-AutoCut.md` (Voraussetzung „NAS gemountet" → „oder `path_map` in der Chargen-config.yaml",
   Fehlerbild „Datei nicht gefunden"), `README.md` (Werte anpassen), `SETUP.md` §6 (NAS/SSD).
6. **MEK-Charge:** `_intern/autocut/config.yaml` mit der NAS→SSD-Zuordnung (nicht versioniert, liegt unter `projects/`).

## Tests

- `test_charge.py`: längster Präfix gewinnt; Ordnergrenze (`/a/b` passt nicht auf `/a/bc/x`); kein Treffer →
  unverändert; NFC/NFD-Schreibweise gleichwertig; `Charge.map_path` liest `config["path_map"]`.
- `test_resolve_api.py`: Fake-Pool enthält ein Item unter dem SSD-Pfad; Session mit `path_map` findet es für den
  NAS-Pfad ohne `ImportMedia`-Aufruf, Ergebnis-Schlüssel = NAS-Pfad; fehlender Clip → `ImportMedia` mit dem
  SSD-Pfad; `link_proxy` verknüpft den zugeordneten Proxy-Pfad; ohne `path_map` unverändertes Verhalten.
- `test_ton.py`: `measure` erhält den zugeordneten Pfad, `ton.json`/Cache tragen den Originalpfad.
- `test_resolve_scripts.py`: Build mit `config.yaml` (`path_map`) gegen das Fake: Media Pool vorab mit den
  zugeordneten Items gefüllt → Timeline entsteht, keine `ImportMedia`-Aufrufe.

## Reihenfolge

Code + Tests → `config.yaml` der MEK-Charge → `resolve_probe_xml.py` (21.1-Umgebung) → Rohschnitt → B-Roll-Plan →
Finalisieren.
