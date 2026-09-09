# AutoCut Pfad-Zuordnung — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AutoCut findet Material, das inzwischen unter einem anderen Präfix liegt (NAS → SSD), ohne dass die
Arbeitsdateien einer Charge umgeschrieben werden.

**Architecture:** Eine reine Funktion `map_path` in `charge.py` (längster Präfix, Ordnergrenze, NFC), konfiguriert über
`path_map` (defaults.yaml + Chargen-config.yaml). Angewendet nur an den Zugriffsstellen: `ResolveSession`
(Media-Pool-Suche, Import, Proxy-Link), `ton.measure_a1_items` (Pegelmessung), `proxy_for`-Aufrufe in zwei Skripten.
Alle Schlüssel bleiben Originalpfade.

**Tech Stack:** Python 3.12 (`tools/autocut/venv`), pytest, Fake-Resolve (`tests/fake_resolve.py`).

Spec: `docs/superpowers/specs/2026-09-09-autocut-pfadzuordnung-design.md`.

## Global Constraints

- Kommandos aus `/Users/jansantos/NIRO Studio/tools/autocut`, Tests `venv/bin/python -m pytest -q` (Stand: 351 passed,
  1 skipped). zsh: Pfade in Anführungszeichen.
- Verhalten ohne `path_map` bleibt exakt gleich (alle bestehenden Tests unverändert grün).
- Arbeitsdateien, Media-Dicts, Cache-Schlüssel, `ton.json`, Berichte: immer Originalpfade.
- Commits auf `main`, Message deutsch (`feat:`/`test:`/`docs:`), Trailer `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
  Nur die genannten Dateien; andere geänderte/untracked Dateien im Arbeitsbaum (z. B. `tools/motion/`) nie mit aufnehmen.

---

### Task 1: `map_path` + Session/Ton-Anwendung + Skripte + Doku

**Files:**
- Modify: `tools/autocut/src/niro_autocut/charge.py` (Funktion `map_path`, Methode `Charge.map_path`)
- Modify: `tools/autocut/defaults.yaml` (`path_map: {}`)
- Modify: `tools/autocut/src/niro_autocut/resolve_api.py` (`ResolveSession.__init__`, `map_path`, `find_media_item`, `import_media`, `link_proxy`)
- Modify: `tools/autocut/src/niro_autocut/ton.py` (`measure_a1_items(..., map_path=None)`, `build_ton`)
- Modify: `tools/autocut/scripts/autocut_build.py`, `autocut_place_broll.py`, `autocut_finalize.py`, `autocut_export_xml.py`, `resolve_probe.py`, `resolve_probe_xml.py`, `resolve_probe_api.py` (Session mit `path_map=ch.config.get("path_map")`; `proxy_for(ch.map_path(...))` in `resolve_probe_xml.py` und `autocut_place_broll.py`)
- Modify: `tools/autocut/WORKFLOW-AutoCut.md`, `tools/autocut/README.md`, `tools/autocut/SETUP.md`
- Test: `tools/autocut/tests/test_charge.py`, `tests/test_resolve_api.py`, `tests/test_ton.py`, `tests/test_resolve_scripts.py`

**Interfaces:**
- Produces: `niro_autocut.charge.map_path(path: str | Path, path_map: dict | None) -> str`; `Charge.map_path(p) -> str`;
  `ResolveSession(resolve, probe=None, path_map=None)` mit `.map_path(p)`; `measure_a1_items(items, fps, cfg_ton, cache, measure=measure_true_peak, map_path=None)`.

- [ ] **Step 1: Failing tests schreiben**

In `tests/test_charge.py` anhängen:
```python
from niro_autocut.charge import map_path


def test_map_path_longest_prefix_and_folder_boundary():
    pm = {"/Volumes/NAS/a": "/Volumes/SSD/a", "/Volumes/NAS/a/tief": "/Volumes/X/tief", "/Volumes/NAS": "/Volumes/Y"}
    assert map_path("/Volumes/NAS/a/tief/clip.mp4", pm) == "/Volumes/X/tief/clip.mp4"
    assert map_path("/Volumes/NAS/a/clip.mp4", pm) == "/Volumes/SSD/a/clip.mp4"
    assert map_path("/Volumes/NAS/ab/clip.mp4", pm) == "/Volumes/Y/ab/clip.mp4"        # „a" passt nicht auf „ab"
    assert map_path("/Volumes/NAS/a", pm) == "/Volumes/SSD/a"                          # exakt der Präfix selbst
    assert map_path("/anders/clip.mp4", pm) == "/anders/clip.mp4"
    assert map_path("/anders/clip.mp4", None) == "/anders/clip.mp4"
    assert map_path("/Volumes/NAS/a/", {"/Volumes/NAS/a/": "/Volumes/SSD/a/"}) == "/Volumes/SSD/a/"   # Schrägstrich am Ende egal


def test_map_path_is_unicode_normalization_agnostic():
    nfd = "/Volumes/NAS/Kliniken GmbH/März/clip.mp4"       # „ä" als a + Kombinationszeichen
    nfc = "/Volumes/NAS/Kliniken GmbH/März"
    assert map_path(nfd, {nfc: "/Volumes/SSD/März"}) == "/Volumes/SSD/März/clip.mp4"


def test_charge_map_path_uses_config(charge_dir):
    (charge_dir / "_intern" / "autocut").mkdir(parents=True, exist_ok=True)
    (charge_dir / "_intern" / "autocut" / "config.yaml").write_text('path_map:\n  "/Volumes/NAS/p": "/Volumes/SSD/p"\n', encoding="utf-8")
    ch = Charge.open(charge_dir)
    assert ch.map_path("/Volumes/NAS/p/x.mp4") == "/Volumes/SSD/p/x.mp4"
    assert ch.map_path("/woanders/x.mp4") == "/woanders/x.mp4"
```
(`Charge` ist in `test_charge.py` bereits importiert; sonst `from niro_autocut.charge import Charge, map_path`.)

In `tests/test_resolve_api.py` anhängen (Fixtures/Imports der Datei nutzen: `FakeProject`, `FakeResolve`, `RA`):
```python
def test_import_media_finds_mapped_item_without_import_and_keeps_original_key():
    p = FakeProject()
    mp = p.GetMediaPool()
    root = mp.GetRootFolder()
    ssd = mp.ImportMedia(["/Volumes/SSD/proj/Interviews/FX3_0001.MP4"])[0]
    mp.calls.clear()
    s = RA.ResolveSession(FakeResolve(p), path_map={"/Volumes/NAS/proj": "/Volumes/SSD/proj"})
    out = s.import_media(["/Volumes/NAS/proj/Interviews/FX3_0001.MP4"], root)
    assert out == {"/Volumes/NAS/proj/Interviews/FX3_0001.MP4": ssd}
    assert not any(c[0] == "ImportMedia" for c in mp.calls)
    assert s.find_media_item("/Volumes/NAS/proj/Interviews/FX3_0001.MP4") is ssd


def test_import_media_imports_mapped_path_when_missing():
    p = FakeProject()
    mp = p.GetMediaPool()
    s = RA.ResolveSession(FakeResolve(p), path_map={"/Volumes/NAS/proj": "/Volumes/SSD/proj"})
    out = s.import_media(["/Volumes/NAS/proj/B/FX3_0002.MP4"], mp.GetRootFolder())
    assert ("ImportMedia", ["/Volumes/SSD/proj/B/FX3_0002.MP4"]) in mp.calls
    assert list(out) == ["/Volumes/NAS/proj/B/FX3_0002.MP4"]
    assert out["/Volumes/NAS/proj/B/FX3_0002.MP4"].GetClipProperty("File Path") == "/Volumes/SSD/proj/B/FX3_0002.MP4"


def test_link_proxy_maps_proxy_path():
    p = FakeProject()
    item = p.GetMediaPool().ImportMedia(["/Volumes/SSD/proj/FX3_0003.MP4"])[0]
    s = RA.ResolveSession(FakeResolve(p), path_map={"/Volumes/NAS/proj": "/Volumes/SSD/proj"})
    assert s.link_proxy(item, "/Volumes/NAS/proj/Proxy/FX3_0003.mov") is True
    assert item.proxy == "/Volumes/SSD/proj/Proxy/FX3_0003.mov"


def test_session_without_path_map_is_unchanged():
    p = FakeProject()
    mp = p.GetMediaPool()
    s = RA.ResolveSession(FakeResolve(p))
    s.import_media(["/Volumes/NAS/proj/FX3_0004.MP4"], mp.GetRootFolder())
    assert ("ImportMedia", ["/Volumes/NAS/proj/FX3_0004.MP4"]) in mp.calls
```

In `tests/test_ton.py` anhängen (Imports der Datei nutzen; `Item` aus `niro_autocut.timeline_model`):
```python
def test_measure_a1_items_measures_mapped_path_but_keys_original():
    from niro_autocut.ton import measure_a1_items
    seen = []

    def fake_measure(path, in_s, dur_s):
        seen.append(path)
        return -12.0

    items = [Item("A1", "/Volumes/NAS/proj/FX3_0001.MP4", 25, 125, 0, 100, True, "1")]
    cache: dict = {}
    cfg = {"ziel_dbtp": -3.0, "max_gain_db": 30.0, "clip_warn_dbtp": -0.5, "silence_dbtp": -60.0}
    out = measure_a1_items(items, 25.0, cfg, cache, fake_measure, map_path=lambda p: p.replace("/Volumes/NAS/", "/Volumes/SSD/"))
    assert seen == ["/Volumes/SSD/proj/FX3_0001.MP4"]
    assert out[0]["clip"] == "/Volumes/NAS/proj/FX3_0001.MP4" and list(cache) == ["/Volumes/NAS/proj/FX3_0001.MP4|25|125"]
```

In `tests/test_resolve_scripts.py` anhängen (nutzt die Fixture `mek` und `build = _load("autocut_build")`):
```python
def test_build_uses_path_map_and_existing_media_items(mek, monkeypatch, tmp_path):
    """config.yaml path_map: die Charge kennt NAS-Pfade, der Media Pool hat die SSD-Items — kein Import nötig."""
    ch = mek["ch"]
    nas_root = str(tmp_path / "nas")
    ssd_root = str(tmp_path / "ssd")
    (ch.autocut / "config.yaml").write_text(f'path_map:\n  "{nas_root}": "{ssd_root}"\n', encoding="utf-8")
    p = FakeProject()
    mp = p.GetMediaPool()
    for src in (mek["fx"], mek["a7"]):
        mp.ImportMedia([src.replace(nas_root, ssd_root)])
    mp.calls.clear()
    monkeypatch.setattr(build.RA, "connect", lambda: FakeResolve(p))
    assert build.main([str(mek["dir"])]) == 0
    assert not any(c[0] == "ImportMedia" for c in mp.calls)
    tl = p.timelines[-1]
    assert tl.GetItemListInTrack("video", 1)
```
Hinweis: `build.main` liest die Config über `Charge.open` neu (die Fixture hat die Charge vor dem Schreiben der
config.yaml geöffnet) — deshalb genügt das Schreiben der Datei vor `build.main`. Wenn `autocut_build.py` das
Fake-Resolve auf anderem Weg injiziert (siehe die bestehenden Build-Tests in derselben Datei), dieselbe Technik
verwenden.

- [ ] **Step 2: Tests laufen lassen — sie müssen fehlschlagen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_charge.py tests/test_resolve_api.py tests/test_ton.py tests/test_resolve_scripts.py`
Expected: FAIL mit `ImportError: cannot import name 'map_path'` / `TypeError: … unexpected keyword argument 'path_map'`.

- [ ] **Step 3: `charge.py` + `defaults.yaml`**

`charge.py` (nach `_deep_merge`, vor `load_config`; `import unicodedata` ergänzen):
```python
def map_path(path: str | Path, path_map: dict | None) -> str:
    """Pfad über die längste passende Präfix-Zuordnung umschreiben (Ordnergrenze, NFC-normalisiert); sonst unverändert.

    Schlüssel = Präfix in den Arbeitsdateien (z. B. NAS), Wert = Präfix, unter dem die Dateien jetzt liegen (z. B. SSD).
    """
    s = unicodedata.normalize("NFC", str(path))
    best: tuple[str, str] | None = None
    for src, dst in (path_map or {}).items():
        a = unicodedata.normalize("NFC", str(src)).rstrip("/")
        if not a:
            continue
        if s == a or s.startswith(a + "/"):
            if best is None or len(a) > len(best[0]):
                best = (a, unicodedata.normalize("NFC", str(dst)).rstrip("/"))
    if best is None:
        return str(path)
    return best[1] + s[len(best[0]):]
```
In `class Charge` nach `assert_writable`:
```python
    def map_path(self, path: str | Path) -> str:
        """Zugriffspfad laut ``path_map`` der Config (Arbeitsdateien behalten die Originalpfade)."""
        return map_path(path, self.config.get("path_map") or {})
```
`defaults.yaml`, vor `resolve:`:
```yaml
path_map: {}                # Präfix in den Arbeitsdateien → Präfix, unter dem das Material jetzt liegt (z. B. NAS → SSD);
                            # je Charge in _intern/autocut/config.yaml setzen; längster Präfix gewinnt, Ordnergrenze
```

- [ ] **Step 4: `resolve_api.py`**

Import ergänzen: `from .charge import AutoCutError, map_path`. Konstruktor: Signatur `def __init__(self, resolve, probe: dict | None = None, path_map: dict | None = None)`, nach `self.warnings = []`: `self.path_map = dict(path_map or {})`. Neue Methode (vor `_walk`):
```python
    def map_path(self, path: str | Path) -> str:
        return map_path(path, self.path_map)
```
`find_media_item`: `return self._path_index().get(_norm(self.map_path(path)))`.
`import_media`: in der ersten Schleife `item = index.get(_norm(self.map_path(p)))`; der Import wird
`imported = self.media_pool.ImportMedia([self.map_path(p) for p in missing]) or []`; in der Zuordnungsschleife
`item = by_path.get(_norm(self.map_path(p)))` und `item = fresh.get(_norm(self.map_path(p)))`; die Fehlermeldung
nennt `self.map_path(p)`. `out[p] = item` bleibt (Original-Schlüssel).
`link_proxy`: nach `if not proxy_path: return False` die Zeile `proxy_path = self.map_path(proxy_path)`.
Docstring-Kopf der Klasse um einen Satz: „``path_map`` (Chargen-Config) ordnet Arbeitsdatei-Pfade dem aktuellen Ablageort zu; Schlüssel bleiben Originalpfade."

- [ ] **Step 5: `ton.py`**

`measure_a1_items(items, fps, cfg_ton, cache, measure=measure_true_peak, map_path=None)`: in der Messung
`src = map_path(it.clip) if map_path else it.clip` und `measure(src, round(in_s, 3), round(dur_s, 3))`. `build_ton`:
`entries = measure_a1_items(items, fps, cfg_ton, cache, measure, map_path=getattr(charge, "map_path", None))`.

- [ ] **Step 6: Skripte**

An jeder `ResolveSession(...)`-Konstruktion mit vorhandener Charge `ch` den Parameter `path_map=ch.config.get("path_map")`
ergänzen: `autocut_build.py:155`, `autocut_finalize.py:40`, `autocut_place_broll.py:312`, `resolve_probe_xml.py:121`,
`resolve_probe_api.py:329`, `autocut_export_xml.py:55`, `resolve_probe.py:177` (Variablennamen der Charge in der
jeweiligen Datei prüfen). `resolve_probe_xml.py:52`: `proxy_for(ch.map_path(fx))` (beide Vorkommen).
`autocut_place_broll.py:136` und `:195`: `proxy_for(ch.map_path(p))` bzw. `proxy_for(ch.map_path(c))` — den Namen der
Charge-Variable in dieser Datei übernehmen.

- [ ] **Step 7: Doku**

`WORKFLOW-AutoCut.md`, Voraussetzungen, NAS-Punkt: nach „… für jeden Interview- und B-Roll-Clip." ergänzen:
„Liegt das Material inzwischen unter einem anderen Präfix (SSD statt NAS), `path_map` in
`<Charge>/_intern/autocut/config.yaml` setzen (`"<alter Präfix>": "<neuer Präfix>"`) — die Arbeitsdateien bleiben
unverändert, AutoCut ordnet nur beim Zugriff zu (Media Pool, Proxy, Pegelmessung)." Fehlerbild-Zeile
`Datei nicht gefunden … Ist das NAS gemountet?` um „oder `path_map` in der Chargen-config.yaml setzen" ergänzen.
Ausgabe-Konvention: `config.yaml`-Zeile um „, `path_map`" ergänzen.
`README.md`, Abschnitt „Werte anpassen": Satz „`path_map` ordnet die Pfade der Arbeitsdateien dem aktuellen
Ablageort zu (NAS → SSD), je Charge in `config.yaml`." `SETUP.md` §6 NAS: gleicher Hinweis in einem Satz.

- [ ] **Step 8: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q`
Expected: 351 + 9 neue = 360 passed, 1 skipped.

- [ ] **Step 9: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/autocut/src/niro_autocut/charge.py tools/autocut/defaults.yaml tools/autocut/src/niro_autocut/resolve_api.py tools/autocut/src/niro_autocut/ton.py tools/autocut/scripts/autocut_build.py tools/autocut/scripts/autocut_place_broll.py tools/autocut/scripts/autocut_finalize.py tools/autocut/scripts/autocut_export_xml.py tools/autocut/scripts/resolve_probe.py tools/autocut/scripts/resolve_probe_xml.py tools/autocut/scripts/resolve_probe_api.py tools/autocut/WORKFLOW-AutoCut.md tools/autocut/README.md tools/autocut/SETUP.md tools/autocut/tests/test_charge.py tools/autocut/tests/test_resolve_api.py tools/autocut/tests/test_ton.py tools/autocut/tests/test_resolve_scripts.py "docs/superpowers/specs/2026-09-09-autocut-pfadzuordnung-design.md" "docs/superpowers/plans/2026-09-09-autocut-pfadzuordnung.md" && git commit -q -m "feat: AutoCut path_map — Material unter neuem Präfix (NAS → SSD) ohne Umschreiben der Arbeitsdateien

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

## Self-Review

- Spec-Abdeckung: Design 1 → Step 3; 2 → Step 4; 3 → Step 5; 4 → Step 6; 5 → Step 7; 6 (config.yaml der MEK-Charge) ist
  Betrieb, kein Repo-Inhalt — der Controller legt sie vor dem Rohschnitt an. Tests der Spec → Step 1.
- Typen: `map_path(path, path_map)` (charge) und `ResolveSession.map_path(p)`/`Charge.map_path(p)` konsistent;
  `measure_a1_items(..., map_path=None)` bekommt ein Callable, `build_ton` reicht `charge.map_path` durch.
