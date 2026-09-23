"""Tests für index_sections.py — Frame-Auswahl, Abschnittsbogen, dHash, Schema, Merge/Cache (ohne API)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from niro_autocut import index_sections as S


def _frames(tmp_path: Path, stem="FX3_1", fp12="abcdefabcdef", times=(0.5, 2.0, 4.0, 6.0, 7.5)) -> Path:
    """Bilder mit horizontalem Verlauf (pro Bild anders verschoben) — nötig, damit dHash auf unterschiedlichen
    Bildern auch unterschiedliche Hashes liefert; ein einfarbiges Bild hat keinen Helligkeitsverlauf zwischen
    Nachbarpixeln und würde immer denselben (Null-)Hash ergeben."""
    d = tmp_path / "work" / "frames" / f"{stem}.{fp12}"
    d.mkdir(parents=True)
    for i, t in enumerate(times):
        im = Image.new("RGB", (640, 360))
        row = [((x + i * 37) % 256,) * 3 for x in range(640)]
        im.putdata(row * 360)
        im.save(d / f"{stem}_{int(round(t * 100)):07d}.jpg")
    return d


class _Block:
    def __init__(self, type_: str, text: str | None = None):
        self.type = type_
        self.text = text


class _Usage:
    input_tokens = 500
    output_tokens = 80
    cache_read_input_tokens = 0
    cache_creation_input_tokens = 0


class _Resp:
    def __init__(self, stop_reason: str, text: str | None):
        self.stop_reason = stop_reason
        self.content = [_Block("text", text)] if text is not None else []
        self.usage = _Usage()


class _FakeClient:
    """Stand-in für den Anthropic-Client: ``messages.create(...)`` liefert immer dieselbe feste Antwort."""

    def __init__(self, resp: _Resp):
        self._resp = resp
        self.messages = self

    def create(self, **kwargs):
        return self._resp


class _Ch:
    def __init__(self, root: Path):
        self.work = root / "work"
        self.autocut = root
        self.autocut.mkdir(exist_ok=True)

    def assert_writable(self, p):
        return None

    def write_json(self, name, data):
        p = self.autocut / name
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return p


def test_frames_in_cache_and_pick(tmp_path):
    _frames(tmp_path)
    rec = {"path": "/nas/B-Roll/Flur/FX3_1.MP4", "fingerprint": "abcdefabcdef0000", "datei": "FX3_1.MP4"}
    fr = S.frames_in_cache(_Ch(tmp_path), rec)
    assert [t for _, t in fr] == [0.5, 2.0, 4.0, 6.0, 7.5]
    picked = S.pick_section_frames(fr, 0.0, 8.0, per_section=2)
    assert [t for _, t in picked] == [0.5, 4.0]                 # Anfang+0,5 und Mitte
    assert [t for _, t in S.pick_section_frames(fr, 5.5, 8.0, per_section=2)] == [6.0, 7.5]
    assert len(S.pick_section_frames(fr, 7.0, 8.0, per_section=2)) == 1   # kurzer Abschnitt: eine Kachel


def test_section_sheet_size_and_dhash(tmp_path):
    d = _frames(tmp_path)
    fr = sorted((p, float(p.stem.split("_")[-1]) / 100) for p in d.glob("*.jpg"))
    out = S.section_sheet([fr[:2], fr[2:4]], tmp_path / "sheet_A.jpg", tile_px=480)
    with Image.open(out) as im:
        assert im.size == (2 * 480 + 3 * 8, 2 * 270 + 3 * 8)
    h1, h2 = S.dhash(fr[0][0]), S.dhash(fr[3][0])
    assert len(h1) == 16 and S.hamming(h1, h1) == 0 and S.hamming(h1, h2) > 0


def test_validate_sections_and_needs():
    good = {"abschnitte": [{"nr": 1, "einstellung": "Totale", "perspektive_hoehe": "Augenhöhe", "perspektive_ansicht": "ohne Person",
                            "brennweite": "weit", "bewegungsrichtung": "keine", "hauptmotiv": "Klinikflur"}]}
    assert S.validate_sections(good, 1) == []
    assert S.validate_sections(good, 2) == ["abschnitte: 1 Einträge, Clip hat 2 Abschnitte"]
    bad = {"abschnitte": [{**good["abschnitte"][0], "brennweite": "lang"}]}
    assert any("brennweite" in p for p in S.validate_sections(bad, 1))
    rec = {"abschnitte": [{"von_s": 0, "bis_s": 5, "beschreibung": "", "qualitaet": 4, "verwendbar": True}]}
    assert S.needs_sections(rec) is True
    rec["abschnitte"][0].update(good["abschnitte"][0])
    rec["abschnitte"][0]["setup_hash"] = "0" * 16
    assert S.needs_sections(rec) is False


def test_validate_sections_nr_order():
    item = {"einstellung": "Totale", "perspektive_hoehe": "Augenhöhe", "perspektive_ansicht": "ohne Person",
            "brennweite": "weit", "bewegungsrichtung": "keine", "hauptmotiv": "Klinikflur"}
    vertauscht = {"abschnitte": [{**item, "nr": 2}, {**item, "nr": 1}]}
    assert S.validate_sections(vertauscht, 2) == ["abschnitte: nr muss 1..n in Reihenfolge sein"]
    doppelt = {"abschnitte": [{**item, "nr": 1}, {**item, "nr": 1}]}
    assert S.validate_sections(doppelt, 2) == ["abschnitte: nr muss 1..n in Reihenfolge sein"]


def test_describe_sections_raises_on_max_tokens(tmp_path):
    sheet = tmp_path / "sheet_A.jpg"
    sheet.write_bytes(b"fake-jpeg-bytes")
    client = _FakeClient(_Resp("max_tokens", "{}"))
    cfg = {"model": "claude-opus-5", "effort": "medium", "max_tokens": 2500}
    with pytest.raises(S.AutoCutError, match="abgeschnitten"):
        S.describe_sections(client, sheet, "meta", cfg, "prompt")


def test_describe_sections_raises_on_invalid_json(tmp_path):
    sheet = tmp_path / "sheet_A.jpg"
    sheet.write_bytes(b"fake-jpeg-bytes")
    client = _FakeClient(_Resp("end_turn", "das ist kein JSON"))
    cfg = {"model": "claude-opus-5", "effort": "medium", "max_tokens": 2500}
    with pytest.raises(S.AutoCutError, match="JSON"):
        S.describe_sections(client, sheet, "meta", cfg, "prompt")


def test_index_sections_clip_merges_and_caches(tmp_path):
    _frames(tmp_path)
    ch = _Ch(tmp_path)
    (ch.autocut / "broll_index").mkdir()
    rec = {"path": "/nas/B-Roll/Flur/FX3_1.MP4", "datei": "FX3_1.MP4", "fingerprint": "abcdefabcdef0000", "orientierung": "16:9",
           "abschnitte": [{"von_s": 0, "bis_s": 4, "beschreibung": "Flur", "qualitaet": 4, "verwendbar": True},
                          {"von_s": 4, "bis_s": 8, "beschreibung": "Tür", "qualitaet": 3, "verwendbar": True}]}
    (ch.autocut / "broll_index" / "abcdefabcdef0000.json").write_text(json.dumps(rec), encoding="utf-8")

    def fake_describe(client, sheet, meta_text, cfg, prompt):
        assert "Abschnitt 2" in meta_text and Path(sheet).name.endswith("_A.jpg")
        return {"abschnitte": [{"nr": i, "einstellung": "Halbtotale", "perspektive_hoehe": "Augenhöhe", "perspektive_ansicht": "seitlich",
                                "brennweite": "normal", "bewegungsrichtung": "nach links", "hauptmotiv": "Pflegekraft im Flur"} for i in (1, 2)],
                "_usage": {"input": 900, "output": 120, "cache_read": 0, "cache_write": 0}}
    cfg = {"index": {"model": "claude-opus-5"}, "index_sections": {"tile_px": 480, "per_section": 2, "max_sections": 5, "effort": "medium", "max_tokens": 2500}}
    out = S.index_sections_clip(ch, rec, None, cfg, "prompt", describe=fake_describe)
    assert out["_cache"] is False and out["abschnitte"][1]["einstellung"] == "Halbtotale" and len(out["abschnitte"][0]["setup_hash"]) == 16
    assert out["nachlauf"]["usage"]["input"] == 900
    cached = json.loads((ch.autocut / "broll_index" / "abcdefabcdef0000.json").read_text())
    assert cached["abschnitte"][0]["brennweite"] == "normal" and "_cache" not in cached
    again = S.index_sections_clip(ch, cached, None, cfg, "prompt", describe=fake_describe)
    assert again["_cache"] is True


def test_needs_sections_ignores_abschnitte_beyond_max_sections(tmp_path):
    """Ein Clip mit mehr als max_sections Abschnitten darf nach einem Lauf nicht für immer als offen gelten
    (sonst würde jeder weitere Lauf ihn erneut kostenpflichtig anfragen, ohne je fertig zu werden)."""
    _frames(tmp_path)
    ch = _Ch(tmp_path)
    (ch.autocut / "broll_index").mkdir()
    abschnitte = [{"von_s": i * 2, "bis_s": i * 2 + 2, "beschreibung": f"Teil {i + 1}", "qualitaet": 4, "verwendbar": True}
                  for i in range(6)]
    rec = {"path": "/nas/B-Roll/Flur/FX3_1.MP4", "datei": "FX3_1.MP4", "fingerprint": "abcdefabcdef0000",
           "orientierung": "16:9", "abschnitte": abschnitte}
    (ch.autocut / "broll_index" / "abcdefabcdef0000.json").write_text(json.dumps(rec), encoding="utf-8")

    def fake_describe(client, sheet, meta_text, cfg, prompt):
        return {"abschnitte": [{"nr": i, "einstellung": "Halbtotale", "perspektive_hoehe": "Augenhöhe",
                                "perspektive_ansicht": "seitlich", "brennweite": "normal",
                                "bewegungsrichtung": "keine", "hauptmotiv": "Flur"} for i in range(1, 6)],
                "_usage": {"input": 500, "output": 80, "cache_read": 0, "cache_write": 0}}
    cfg = {"index": {"model": "claude-opus-5"},
           "index_sections": {"tile_px": 480, "per_section": 2, "max_sections": 5, "effort": "medium", "max_tokens": 2500}}
    out = S.index_sections_clip(ch, rec, None, cfg, "prompt", describe=fake_describe)
    assert out["_cache"] is False and len(out["abschnitte"]) == 6
    assert "setup_hash" not in out["abschnitte"][5]      # 6. Abschnitt liegt über max_sections, bleibt unverändert
    assert S.needs_sections(out, 5) is False
    cached = json.loads((ch.autocut / "broll_index" / "abcdefabcdef0000.json").read_text())
    again = S.index_sections_clip(ch, cached, None, cfg, "prompt", describe=fake_describe)
    assert again["_cache"] is True


def test_index_sections_clip_warns_when_no_frame_in_window(tmp_path):
    """Liegt kein Cache-Frame im Abschnittsfenster, wird der nächstgelegene Frame verwendet, aber mit
    Warnung und frame_s protokolliert, statt den Ersatz kommentarlos als Referenzbild zu verwenden."""
    _frames(tmp_path, times=(0.2, 19.8))
    ch = _Ch(tmp_path)
    (ch.autocut / "broll_index").mkdir()
    rec = {"path": "/nas/B-Roll/Flur/FX3_1.MP4", "datei": "FX3_1.MP4", "fingerprint": "abcdefabcdef0000",
           "orientierung": "16:9",
           "abschnitte": [{"von_s": 9, "bis_s": 11, "beschreibung": "Flur", "qualitaet": 4, "verwendbar": True}]}
    (ch.autocut / "broll_index" / "abcdefabcdef0000.json").write_text(json.dumps(rec), encoding="utf-8")

    def fake_describe(client, sheet, meta_text, cfg, prompt):
        return {"abschnitte": [{"nr": 1, "einstellung": "Halbtotale", "perspektive_hoehe": "Augenhöhe",
                                "perspektive_ansicht": "seitlich", "brennweite": "normal",
                                "bewegungsrichtung": "keine", "hauptmotiv": "Flur"}],
                "_usage": {"input": 500, "output": 80, "cache_read": 0, "cache_write": 0}}
    cfg = {"index": {"model": "claude-opus-5"},
           "index_sections": {"tile_px": 480, "per_section": 2, "max_sections": 5, "effort": "medium", "max_tokens": 2500}}
    out = S.index_sections_clip(ch, rec, None, cfg, "prompt", describe=fake_describe)
    assert out["warnungen"] == ["Abschnitt 1: kein Frame im Cache, nächster Frame bei 19.8 s"]
    assert out["abschnitte"][0]["frame_s"] == [0.2, 19.8]


# --- Schema-Reparatur (Live 04.09.2026: 24/14/3 Abbrüche „Antwort verletzt das Schema“ in drei Anläufen) ----------

_GOOD_ITEM = {"einstellung": "Halbtotale", "perspektive_hoehe": "Augenhöhe", "perspektive_ansicht": "seitlich",
              "brennweite": "normal", "bewegungsrichtung": "nach links", "hauptmotiv": "Pflegekraft im Flur"}
_CFG2 = {"index": {"model": "claude-opus-5"},
         "index_sections": {"tile_px": 480, "per_section": 2, "max_sections": 5, "effort": "medium", "max_tokens": 2500}}
_USAGE = {"input": 500, "output": 80, "cache_read": 0, "cache_write": 0}


def _good(n: int) -> list[dict]:
    return [{"nr": i, **_GOOD_ITEM} for i in range(1, n + 1)]


def _rec2(tmp_path: Path) -> tuple[_Ch, dict]:
    """Charge mit Frame-Cache und einem Clip mit zwei Abschnitten im Clip-Cache."""
    _frames(tmp_path)
    ch = _Ch(tmp_path)
    (ch.autocut / "broll_index").mkdir()
    rec = {"path": "/nas/B-Roll/Flur/FX3_1.MP4", "datei": "FX3_1.MP4", "fingerprint": "abcdefabcdef0000", "orientierung": "16:9",
           "abschnitte": [{"von_s": 0, "bis_s": 4, "beschreibung": "Flur", "qualitaet": 4, "verwendbar": True},
                          {"von_s": 4, "bis_s": 8, "beschreibung": "Tür", "qualitaet": 3, "verwendbar": True}]}
    (ch.autocut / "broll_index" / "abcdefabcdef0000.json").write_text(json.dumps(rec), encoding="utf-8")
    return ch, rec


def test_normalize_sections_fixes_enum_case_and_whitespace():
    """„auf Kamera Zu“ und „von Kamera Weg“ kamen live als Schema-Verstoß zurück — nur die Schreibweise wich ab."""
    data = {"abschnitte": [{"nr": 1, "einstellung": " totale", "perspektive_hoehe": "augenhöhe", "perspektive_ansicht": "Ohne Person",
                            "brennweite": "Weit ", "bewegungsrichtung": "auf Kamera Zu", "hauptmotiv": " Klinikflur "}]}
    out = S.normalize_sections(data)
    a = out["abschnitte"][0]
    assert (a["einstellung"], a["perspektive_hoehe"], a["perspektive_ansicht"], a["brennweite"], a["bewegungsrichtung"]) == \
        ("Totale", "Augenhöhe", "ohne Person", "weit", "auf Kamera zu")
    assert a["hauptmotiv"] == "Klinikflur"
    assert S.validate_sections(out, 1) == []
    bad = S.normalize_sections({"abschnitte": [{**a, "brennweite": "lang"}]})
    assert bad["abschnitte"][0]["brennweite"] == "lang"          # Unbekanntes bleibt stehen und fällt in der Prüfung auf
    assert any("brennweite" in p for p in S.validate_sections(bad, 1))
    assert S.normalize_sections({"abschnitte": "kaputt"}) == {"abschnitte": "kaputt"}
    assert S.normalize_sections(["kein", "dict"]) == ["kein", "dict"]


def test_index_sections_clip_repairs_schema_violation_once(tmp_path):
    """Liefert das Modell weniger Einträge als der Clip Abschnitte hat, fragt der Nachlauf genau einmal mit der
    Fehlerliste nach, statt den bezahlten Clip sofort als Fehler zu verbuchen."""
    ch, rec = _rec2(tmp_path)
    calls: list[str] = []

    def fake_describe(client, sheet, meta_text, cfg, prompt):
        calls.append(meta_text)
        return {"abschnitte": _good(1 if len(calls) == 1 else 2), "_usage": dict(_USAGE)}

    out = S.index_sections_clip(ch, rec, None, _CFG2, "prompt", describe=fake_describe)
    assert len(calls) == 2
    assert calls[1].startswith(calls[0])                                    # dieselbe Aufgabe, plus Fehlerliste
    assert "Schema" in calls[1] and "1 Einträge, Clip hat 2 Abschnitte" in calls[1]
    assert out["_cache"] is False and len(out["abschnitte"]) == 2 and out["abschnitte"][1]["einstellung"] == "Halbtotale"
    assert out["nachlauf"]["usage"]["input"] == 1000 and out["nachlauf"]["reparaturen"] == 1   # beide Anfragen gezählt
    cached = json.loads((ch.autocut / "broll_index" / "abcdefabcdef0000.json").read_text())
    assert cached["nachlauf"]["reparaturen"] == 1 and cached["abschnitte"][1]["brennweite"] == "normal"


def test_index_sections_clip_gives_up_after_one_repair(tmp_path):
    ch, rec = _rec2(tmp_path)
    calls: list[str] = []

    def fake_describe(client, sheet, meta_text, cfg, prompt):
        calls.append(meta_text)
        return {"abschnitte": _good(1), "_usage": dict(_USAGE)}

    with pytest.raises(S.AutoCutError, match="verletzt das Schema"):
        S.index_sections_clip(ch, rec, None, _CFG2, "prompt", describe=fake_describe)
    assert len(calls) == 2                                                  # genau eine Nachfrage, kein Dauerbeschuss
    cached = json.loads((ch.autocut / "broll_index" / "abcdefabcdef0000.json").read_text())
    assert "nachlauf" not in cached                                         # nichts Halbes im Cache


def test_index_sections_clip_normalizes_enum_case_without_repair(tmp_path):
    ch, rec = _rec2(tmp_path)
    calls: list[str] = []

    def fake_describe(client, sheet, meta_text, cfg, prompt):
        calls.append(meta_text)
        items = _good(2)
        items[0]["bewegungsrichtung"] = "auf Kamera Zu"
        items[1]["einstellung"] = "halbtotale "
        return {"abschnitte": items, "_usage": dict(_USAGE)}

    out = S.index_sections_clip(ch, rec, None, _CFG2, "prompt", describe=fake_describe)
    assert len(calls) == 1
    assert out["abschnitte"][0]["bewegungsrichtung"] == "auf Kamera zu" and out["abschnitte"][1]["einstellung"] == "Halbtotale"
    assert out["nachlauf"]["reparaturen"] == 0


def test_index_sections_counts_repairs_over_all_clips(tmp_path, monkeypatch):
    ch, rec = _rec2(tmp_path)
    rec_b = {**rec, "path": "/nas/B-Roll/Flur/FX3_2.MP4", "datei": "FX3_2.MP4", "fingerprint": "bbbbbbbbbbbb0000"}
    monkeypatch.setattr(S, "_make_client", lambda cfg: object())
    monkeypatch.setattr(S, "load_system_prompt", lambda: "prompt")

    def fake_clip(charge, c, client, cfg, prompt, force, telemetrie=None):
        n_rep = 1 if c["datei"] == "FX3_2.MP4" else 0
        return {**c, "abschnitte": [{**a, **_GOOD_ITEM, "setup_hash": "0" * 16} for a in c["abschnitte"]],
                "nachlauf": {"usage": dict(_USAGE), "reparaturen": n_rep}, "_cache": False}

    monkeypatch.setattr(S, "index_sections_clip", fake_clip)
    out = S.index_sections(ch, {"clips": [rec, rec_b]}, _CFG2, parallel=1)
    assert out["anzahl"] == 2 and out["fehler"] == [] and out["reparaturen"] == 1
    written = json.loads((ch.autocut / "broll_index.json").read_text())
    assert written["nachlauf"]["reparaturen"] == 1


# --- Telemetrie (Task 8) -----------------------------------------------------------------------------------------

TELE = {"path": "/nas/B-Roll/Flur/FX3_1.MP4", "clip": "FX3_1", "quelle": "rtmd", "kb_mm": 71.6,
        "kb_verlauf": [[0.0, 71.6]], "zooms": [],
        "pitch_grad": -12.0, "perspektive_hoehe": "Aufsicht", "haltung": "gimbal", "wackeln": 0.05, "fehler": None,
        "fenster": [[0.0, 0.05, 1.0, "schwenk_links"], [1.0, 0.05, 1.0, "schwenk_links"], [2.0, 0.05, 1.0, "schwenk_links"],
                    [3.0, 0.05, 1.0, "schwenk_links"], [4.0, 0.02, 0.1, "statisch"], [5.0, 0.02, 0.1, "statisch"],
                    [6.0, 0.02, 0.1, "statisch"]]}
_CFG_T = {"index": {"model": "claude-opus-5"},
          "index_sections": {"tile_px": 480, "per_section": 2, "max_sections": 5, "effort": "medium", "max_tokens": 2500},
          "telemetrie": {"fenster_s": 2.0}}


def test_telemetrie_text_und_anwenden():
    rec = {"abschnitte": [{"von_s": 0, "bis_s": 4, "brennweite": "normal", "perspektive_hoehe": "Augenhöhe"},
                          {"von_s": 4, "bis_s": 8, "brennweite": "tele", "perspektive_hoehe": "Aufsicht"}]}
    text = S.telemetrie_text(TELE, rec["abschnitte"])
    assert "KB 71,6 mm" in text and "= tele" not in text and "Pitch -12° = Aufsicht" in text and "Haltung gimbal" in text
    assert "A1 schwenk_links, A2 statisch" in text and "brennweite und" not in text
    assert S.telemetrie_text(None, rec["abschnitte"]) == "" and S.telemetrie_text({"quelle": "keine"}, []) == ""
    neu, geaendert = S.telemetrie_anwenden(rec, TELE)
    assert geaendert and neu["felder_quelle"] == {"perspektive_hoehe": "rtmd"}
    assert [a["brennweite"] for a in neu["abschnitte"]] == ["normal", "tele"]              # Claudes Klasse bleibt
    assert [a["brennweite_mm"] for a in neu["abschnitte"]] == [71.6, 71.6]
    assert [a["zoom"] for a in neu["abschnitte"]] == ["keiner", "keiner"]
    assert [a["perspektive_hoehe"] for a in neu["abschnitte"]] == ["Aufsicht", "Aufsicht"]
    assert [a["bewegungsart"] for a in neu["abschnitte"]] == ["schwenk_links", "statisch"]
    assert neu["abschnitte"][0]["haltung"] == "gimbal"
    assert S.telemetrie_anwenden(rec, None) == (rec, False)
    wieder, geaendert2 = S.telemetrie_anwenden(neu, TELE)
    assert not geaendert2 and wieder == neu
    ohne_feld = S.telemetrie_anwenden({"abschnitte": [{"von_s": 0, "bis_s": 2}]}, TELE)[0]["abschnitte"][0]
    assert "brennweite" not in ohne_feld and "perspektive_hoehe" not in ohne_feld and ohne_feld["brennweite_mm"] == 71.6


def test_index_sections_clip_wendet_telemetrie_bei_cache_treffer_an(tmp_path):
    ch = _Ch(tmp_path)
    (ch.autocut / "broll_index").mkdir()
    rec = {"path": "/nas/B-Roll/Flur/FX3_1.MP4", "datei": "FX3_1.MP4", "fingerprint": "abcdefabcdef0000",
           "orientierung": "16:9",
           "abschnitte": [{"von_s": 0, "bis_s": 4, "beschreibung": "Flur", "qualitaet": 4, "verwendbar": True,
                           "einstellung": "Halbtotale", "perspektive_hoehe": "Augenhöhe", "perspektive_ansicht": "seitlich",
                           "brennweite": "normal", "bewegungsrichtung": "keine", "hauptmotiv": "Flur",
                           "setup_hash": "0123456789abcdef"}]}
    (ch.autocut / "broll_index" / "abcdefabcdef0000.json").write_text(json.dumps(rec), encoding="utf-8")

    def kein_api(*a, **k):
        raise AssertionError("kein API-Aufruf bei Cache-Treffer")

    out = S.index_sections_clip(ch, rec, None, _CFG_T, "prompt", describe=kein_api, telemetrie=TELE)
    assert out["_cache"] is True and out["abschnitte"][0]["brennweite"] == "normal"         # Claudes Klasse bleibt
    assert out["felder_quelle"] == {"perspektive_hoehe": "rtmd"} and out["abschnitte"][0]["brennweite_mm"] == 71.6
    cached = json.loads((ch.autocut / "broll_index" / "abcdefabcdef0000.json").read_text())
    assert cached["abschnitte"][0]["perspektive_hoehe"] == "Aufsicht" and cached["abschnitte"][0]["zoom"] == "keiner"
    assert cached["abschnitte"][0]["claude"] == {"perspektive_hoehe": "Augenhöhe"}                          # I2
    assert cached["abschnitte"][0]["bewegungsart"] == "schwenk_links"
    ohne = S.index_sections_clip(ch, rec, None, _CFG_T, "prompt", describe=kein_api)
    assert ohne["_cache"] is True and ohne["abschnitte"][0]["brennweite"] == "normal"


def test_index_sections_clip_api_mit_telemetrie(tmp_path):
    _frames(tmp_path)
    ch = _Ch(tmp_path)
    (ch.autocut / "broll_index").mkdir()
    rec = {"path": "/nas/B-Roll/Flur/FX3_1.MP4", "datei": "FX3_1.MP4", "fingerprint": "abcdefabcdef0000",
           "orientierung": "16:9",
           "abschnitte": [{"von_s": 0, "bis_s": 4, "beschreibung": "Flur", "qualitaet": 4, "verwendbar": True}]}

    def fake_describe(client, sheet, meta_text, cfg, prompt):
        assert "Kamera-Telemetrie" in meta_text and "KB 71,6 mm" in meta_text
        return {"abschnitte": [{"nr": 1, "einstellung": "Halbtotale", "perspektive_hoehe": "Augenhöhe",
                                "perspektive_ansicht": "seitlich", "brennweite": "normal", "bewegungsrichtung": "keine",
                                "hauptmotiv": "Flur"}],
                "_usage": {"input": 1, "output": 1, "cache_read": 0, "cache_write": 0}}

    out = S.index_sections_clip(ch, rec, None, _CFG_T, "prompt", describe=fake_describe, telemetrie=TELE)
    a = out["abschnitte"][0]
    assert a["brennweite"] == "normal" and a["perspektive_hoehe"] == "Aufsicht" and a["brennweite_mm"] == 71.6
    assert a["bewegungsart"] == "schwenk_links" and a["haltung"] == "gimbal" and a["zoom"] == "keiner"
    assert a["claude"] == {"perspektive_hoehe": "Augenhöhe"}                                   # I2: Claudes Antwort
    assert out["felder_quelle"] == {"perspektive_hoehe": "rtmd"}
    cached = json.loads((ch.autocut / "broll_index" / "abcdefabcdef0000.json").read_text())
    assert cached["felder_quelle"] == {"perspektive_hoehe": "rtmd"} and "_cache" not in cached


def test_index_sections_zaehlt_telemetrie(tmp_path, monkeypatch):
    ch, rec = _rec2(tmp_path)
    (ch.autocut / "telemetrie.json").write_text(json.dumps([{**TELE, "path": rec["path"]}]), encoding="utf-8")
    monkeypatch.setattr(S, "_make_client", lambda cfg: object())
    monkeypatch.setattr(S, "load_system_prompt", lambda: "prompt")
    gesehen = {}

    def fake_clip(charge, c, client, cfg, prompt, force, telemetrie=None):
        gesehen[c["datei"]] = telemetrie
        return {**c, "abschnitte": [{**a, **_GOOD_ITEM, "setup_hash": "0" * 16} for a in c["abschnitte"]],
                "nachlauf": {"usage": dict(_USAGE), "reparaturen": 0}, "_cache": False}

    monkeypatch.setattr(S, "index_sections_clip", fake_clip)
    out = S.index_sections(ch, {"clips": [rec]}, _CFG2, parallel=1)
    assert out["mit_telemetrie"] == 1 and gesehen[rec["datei"]]["clip"] == "FX3_1"
    assert json.loads((ch.autocut / "broll_index.json").read_text())["nachlauf"]["mit_telemetrie"] == 1


# --- Fix-Runde 1: fenster_s muss bis in die Kontextzeile durchgereicht werden (Task-8-Review) --------------------

_TELE_FENSTER = {"path": "/nas/B-Roll/Flur/FX3_9.MP4", "clip": "FX3_9", "quelle": "rtmd", "kb_mm": 50.0,
                 "pitch_grad": 0.0, "perspektive_hoehe": "Augenhöhe",
                 "haltung": "gimbal", "wackeln": 0.02, "fehler": None,
                 "fenster": [[0.0, 0.02, 0.1, "statisch"], [1.0, 0.02, 0.1, "statisch"],
                             [2.0, 0.05, 1.0, "schwenk_links"], [3.0, 0.05, 1.0, "schwenk_links"],
                             [4.0, 0.05, 1.0, "schwenk_links"], [5.0, 0.05, 1.0, "schwenk_links"]]}


def test_telemetrie_text_nutzt_konfigurierten_fenster_s():
    """Mit fenster_s 2.0 zählen für Abschnitt 2–4 s die Fenster bei 1/2/3 s (2× schwenk_links, 1× statisch =
    Mehrheit schwenk_links); mit fenster_s 6.0 zählen nur die Fenster bei 0/1 s (2× statisch). Ohne die
    Weitergabe von fenster_s würde telemetrie_text immer den Default 2.0 verwenden und der Hinweis an Claude
    widerspräche dem, was telemetrie_anwenden mit demselben fenster_s tatsächlich in bewegungsart schreibt."""
    abschnitte = [{"von_s": 2, "bis_s": 4}]
    assert "A1 schwenk_links" in S.telemetrie_text(_TELE_FENSTER, abschnitte, fenster_s=2.0)
    assert "A1 schwenk_links" in S.telemetrie_text(_TELE_FENSTER, abschnitte)          # Default weiterhin 2.0
    assert "A1 statisch" in S.telemetrie_text(_TELE_FENSTER, abschnitte, fenster_s=6.0)

    rec = {"abschnitte": [{"von_s": 2, "bis_s": 4, "brennweite": "normal", "perspektive_hoehe": "Augenhöhe"}]}
    geschrieben, _ = S.telemetrie_anwenden(rec, _TELE_FENSTER, fenster_s=6.0)
    art = geschrieben["abschnitte"][0]["bewegungsart"]
    assert art == "statisch"
    # Die Kontextzeile mit demselben fenster_s muss denselben Wert zeigen wie telemetrie_anwenden geschrieben hat.
    assert f"A1 {art}" in S.telemetrie_text(_TELE_FENSTER, rec["abschnitte"], fenster_s=6.0)
    assert f"A1 {art}" in S.section_meta_text(rec, _TELE_FENSTER, fenster_s=6.0)


def test_index_sections_clip_meta_text_stimmt_mit_geschriebenem_bewegungsart_ueberein(tmp_path):
    """End-to-End über index_sections_clip: cfg['telemetrie']['fenster_s'] = 6.0 (Charge-Override) muss in der
    Kontextzeile denselben Bewegungsart-Wert zeigen, den telemetrie_anwenden danach in den Abschnitt schreibt."""
    _frames(tmp_path, stem="FX3_9")
    ch = _Ch(tmp_path)
    (ch.autocut / "broll_index").mkdir()
    rec = {"path": "/nas/B-Roll/Flur/FX3_9.MP4", "datei": "FX3_9.MP4", "fingerprint": "abcdefabcdef0000",
           "orientierung": "16:9",
           "abschnitte": [{"von_s": 2, "bis_s": 4, "beschreibung": "Flur", "qualitaet": 4, "verwendbar": True}]}
    cfg = {**_CFG_T, "telemetrie": {"fenster_s": 6.0}}
    gesehen = {}

    def fake_describe(client, sheet, meta_text, cfg2, prompt):
        gesehen["meta_text"] = meta_text
        return {"abschnitte": [{"nr": 1, "einstellung": "Halbtotale", "perspektive_hoehe": "Augenhöhe",
                                "perspektive_ansicht": "seitlich", "brennweite": "normal",
                                "bewegungsrichtung": "keine", "hauptmotiv": "Flur"}],
                "_usage": {"input": 1, "output": 1, "cache_read": 0, "cache_write": 0}}

    out = S.index_sections_clip(ch, rec, None, cfg, "prompt", describe=fake_describe, telemetrie=_TELE_FENSTER)
    art = out["abschnitte"][0]["bewegungsart"]
    assert art == "statisch"
    assert f"A1 {art}" in gesehen["meta_text"]


# --- Final Review (21.09.2026): Claudes Originalwerte (I2), felder_quelle (M3), .part je Schreiber (M5), Zählung (M12) ---

def test_telemetrie_anwenden_sichert_claudes_originalwerte():
    """I2: Claudes Werte der überschriebenen Felder bleiben je Abschnitt in ``claude`` — der Bericht vergleicht dagegen
    statt Telemetrie mit sich selbst. Zweimal anwenden ändert nichts (claude nie mit dem Telemetrie-Wert überschrieben)."""
    rec = {"abschnitte": [{"von_s": 0, "bis_s": 4, "brennweite": "normal", "perspektive_hoehe": "Augenhöhe"},
                          {"von_s": 4, "bis_s": 8, "brennweite": "tele", "perspektive_hoehe": "Aufsicht"}]}
    neu, geaendert = S.telemetrie_anwenden(rec, TELE)
    assert geaendert and [a["claude"] for a in neu["abschnitte"]] == [
        {"perspektive_hoehe": "Augenhöhe"}, {"perspektive_hoehe": "Aufsicht"}]           # nur noch Perspektive
    wieder, geaendert2 = S.telemetrie_anwenden(neu, TELE)
    assert not geaendert2 and wieder == neu
    ohne_pitch, _ = S.telemetrie_anwenden(rec, {**TELE, "pitch_grad": None, "perspektive_hoehe": None})
    assert "claude" not in ohne_pitch["abschnitte"][0]                                   # nichts überschrieben
    assert ohne_pitch["abschnitte"][0]["perspektive_hoehe"] == "Augenhöhe"
    # Altbestand (vor dem Fix angewendet): felder_quelle gesetzt, kein claude → der Telemetrie-Wert ist nicht Claudes
    alt = {"felder_quelle": {"perspektive_hoehe": "rtmd"},
           "abschnitte": [{"von_s": 0, "bis_s": 4, "brennweite": "tele", "perspektive_hoehe": "Aufsicht"}]}
    assert "claude" not in S.telemetrie_anwenden(alt, TELE)[0]["abschnitte"][0]
    assert "claude" not in S.telemetrie_anwenden(rec, None)[0]["abschnitte"][0]


def test_telemetrie_anwenden_felder_quelle_immer_metadaten():
    """M3: Pitch und Brennweite in mm kommen immer aus den Metadaten, auch wenn die Bewegung optisch gemessen wurde."""
    rec = {"abschnitte": [{"von_s": 0, "bis_s": 4, "brennweite": "normal", "perspektive_hoehe": "Augenhöhe"}]}
    neu, _ = S.telemetrie_anwenden(rec, {**TELE, "quelle": "optisch"})
    assert neu["felder_quelle"] == {"perspektive_hoehe": "rtmd"} and neu["abschnitte"][0]["brennweite_mm"] == 71.6


def test_index_sections_clip_api_setzt_claude_aus_der_antwort(tmp_path):
    """I2: im API-Pfad kommt perspektive_hoehe frisch aus der Modellantwort — claude wird daraus neu gesetzt, auch wenn
    der Datensatz schon felder_quelle und ein altes claude trägt (Neulauf mit --force; hier noch mit der Brennweite
    aus der Zeit vor der Umstellung: sie verschwindet aus claude und felder_quelle, Claudes frische Klasse bleibt)."""
    _frames(tmp_path)
    ch = _Ch(tmp_path)
    (ch.autocut / "broll_index").mkdir()
    rec = {"path": "/nas/B-Roll/Flur/FX3_1.MP4", "datei": "FX3_1.MP4", "fingerprint": "abcdefabcdef0000",
           "orientierung": "16:9", "felder_quelle": {"brennweite": "rtmd", "perspektive_hoehe": "rtmd"},
           "abschnitte": [{"von_s": 0, "bis_s": 4, "beschreibung": "Flur", "qualitaet": 4, "verwendbar": True, **_GOOD_ITEM,
                           "brennweite": "tele", "perspektive_hoehe": "Aufsicht", "setup_hash": "0123456789abcdef",
                           "claude": {"brennweite": "weit", "perspektive_hoehe": "Untersicht"}}]}

    def fake_describe(client, sheet, meta_text, cfg, prompt):
        return {"abschnitte": [{"nr": 1, **_GOOD_ITEM}], "_usage": dict(_USAGE)}   # normal / Augenhöhe

    out = S.index_sections_clip(ch, rec, None, _CFG_T, "prompt", force=True, describe=fake_describe, telemetrie=TELE)
    a = out["abschnitte"][0]
    assert a["brennweite"] == "normal" and a["perspektive_hoehe"] == "Aufsicht"
    assert a["claude"] == {"perspektive_hoehe": "Augenhöhe"} and out["felder_quelle"] == {"perspektive_hoehe": "rtmd"}
    cached = json.loads((ch.autocut / "broll_index" / "abcdefabcdef0000.json").read_text())
    assert cached["abschnitte"][0]["claude"] == {"perspektive_hoehe": "Augenhöhe"}
    # Neulauf ohne Telemetrie, felder_quelle noch vom früheren Lauf: Claudes frische Werte bleiben in claude stehen
    ohne = S.index_sections_clip(ch, rec, None, _CFG_T, "prompt", force=True, describe=fake_describe)
    b = ohne["abschnitte"][0]
    assert b["brennweite"] == "normal" and b["claude"] == {"perspektive_hoehe": "Augenhöhe"}


def test_cache_schreiben_eindeutiger_part_name_je_schreiber(tmp_path, monkeypatch):
    """M5: _cache_schreiben läuft jetzt auch bei Cache-Treffern — zwei Schreiber desselben Clips dürfen nicht im selben
    .part kollidieren (pid + Thread-Id wie clip_mit_cache)."""
    import os
    import threading
    ch = _Ch(tmp_path)
    teile: list[str] = []
    echt = os.replace

    def spion(src, dst):
        teile.append(Path(src).name)
        echt(src, dst)

    monkeypatch.setattr(S.os, "replace", spion)
    rec = {"fingerprint": "abcdefabcdef0000", "abschnitte": [], "_cache": True}
    t = threading.Thread(target=S._cache_schreiben, args=(ch, rec))
    t.start()
    t.join()
    S._cache_schreiben(ch, rec)
    assert len(teile) == 2 and teile[0] != teile[1]
    assert all(n.startswith("abcdefabcdef0000.json.") and n.endswith(".part") and str(os.getpid()) in n for n in teile)
    cached = json.loads((ch.autocut / "broll_index" / "abcdefabcdef0000.json").read_text())
    assert "_cache" not in cached


def test_index_sections_zaehlt_nur_telemetrie_mit_daten(tmp_path, monkeypatch):
    """M12: ein Datensatz mit quelle „keine" (keine Datenspur, --ohne-optisch) zählt nicht als Telemetrie."""
    ch, rec = _rec2(tmp_path)
    (ch.autocut / "telemetrie.json").write_text(json.dumps([{"path": rec["path"], "clip": "FX3_1", "quelle": "keine",
                                                             "fehler": None, "fenster": []}]), encoding="utf-8")
    monkeypatch.setattr(S, "_make_client", lambda cfg: object())
    monkeypatch.setattr(S, "load_system_prompt", lambda: "prompt")

    def fake_clip(charge, c, client, cfg, prompt, force, telemetrie=None):
        return {**c, "abschnitte": [{**a, **_GOOD_ITEM, "setup_hash": "0" * 16} for a in c["abschnitte"]],
                "nachlauf": {"usage": dict(_USAGE), "reparaturen": 0}, "_cache": False}

    monkeypatch.setattr(S, "index_sections_clip", fake_clip)
    assert S.index_sections(ch, {"clips": [rec]}, _CFG2, parallel=1)["mit_telemetrie"] == 0


def test_cli_dry_run_zaehlt_nur_telemetrie_mit_daten(charge_dir, capsys):
    """M12: „Telemetrie: N von M" im Skript zählt nur Datensätze mit Daten (quelle nicht None/„keine")."""
    import importlib.util
    skript_pfad = Path(__file__).resolve().parents[1] / "scripts" / "autocut_index_sections.py"
    spec = importlib.util.spec_from_file_location("autocut_index_sections", skript_pfad)
    skript = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(skript)
    ac = charge_dir / "_intern" / "autocut"
    ac.mkdir(parents=True)
    clips = [{"path": f"/nas/B-Roll/FX3_{i}.MP4", "abschnitte": [{"von_s": 0, "bis_s": 4}]} for i in (1, 2)]
    (ac / "broll_index.json").write_text(json.dumps({"clips": clips}), encoding="utf-8")
    (ac / "telemetrie.json").write_text(json.dumps([{**TELE, "path": clips[0]["path"]},
                                                    {"path": clips[1]["path"], "quelle": "keine", "fenster": []}]),
                                        encoding="utf-8")
    assert skript.main([str(charge_dir), "--dry-run"]) == 0
    assert "Telemetrie: 1 von 2 Clips" in capsys.readouterr().out


# --- Zoomfahrten und Brennweite in mm (Spec 2026-09-21, Abschnitt 3) ------------------------------------------------

def test_telemetrie_anwenden_brennweite_mm_und_zoom_je_abschnitt():
    tele = {**TELE, "kb_mm": 50.0, "kb_verlauf": [[0.0, 24.0], [2.0, 24.0], [3.0, 70.0], [8.0, 70.0]],
            "zooms": [{"von_s": 2.0, "bis_s": 3.0, "von_mm": 24.0, "bis_mm": 70.0, "tempo_max": 107.0,
                       "tempo_mittel": 90.0, "ruck": 0.1, "ruckartig": False, "urteil": "schnell"}]}
    rec = {"abschnitte": [{"von_s": 0, "bis_s": 2}, {"von_s": 2, "bis_s": 4}, {"von_s": 4, "bis_s": 8}]}
    neu, _ = S.telemetrie_anwenden(rec, tele)
    # 2–4 s: 2,0 … 2,9 s steigend, 3,0 … 4,0 s = 70 mm → Median 70; der Zoom 2–3 s schneidet nur diesen Abschnitt
    assert [a["brennweite_mm"] for a in neu["abschnitte"]] == [24.0, 70.0, 70.0]
    assert [a["zoom"] for a in neu["abschnitte"]] == ["keiner", "schnell", "keiner"]
    assert "KB 24–70 mm, schneller Zoom" in S.telemetrie_text(tele, rec["abschnitte"])
    alt = {k: v for k, v in TELE.items() if k not in ("kb_verlauf", "zooms")}          # Datensatz von vor der Umstellung
    ohne, _ = S.telemetrie_anwenden(rec, alt)
    assert all("brennweite_mm" not in a and "zoom" not in a for a in ohne["abschnitte"])
    assert "KB 71,6 mm" in S.telemetrie_text(alt, rec["abschnitte"])


def test_telemetrie_anwenden_schreibt_bewegung_spitzen():
    rec = {"fingerprint": "abc", "abschnitte": [{"von_s": 0, "bis_s": 5, "einstellung": "Totale",
                                                 "perspektive_hoehe": "Augenhöhe"}]}
    tele = {"quelle": "rtmd", "perspektive_hoehe": "Augenhöhe", "haltung": "gimbal", "fenster_s": 2.0,
            "fenster": [[0.0, 0.1, 0.5, "fahrt", None],
                        [1.0, 0.1, 3.0, "schwenk_links", None],
                        [2.0, 0.1, 0.4, "fahrt", None]]}
    neu, geaendert = S.telemetrie_anwenden(rec, tele, 2.0)
    assert geaendert is True
    assert neu["abschnitte"][0]["bewegung_spitzen"] == [[1.0, 3.0]]
    # idempotent: zweiter Lauf ändert nichts mehr
    neu2, geaendert2 = S.telemetrie_anwenden(neu, tele, 2.0)
    assert geaendert2 is False and neu2["abschnitte"][0]["bewegung_spitzen"] == [[1.0, 3.0]]


def test_telemetrie_anwenden_ohne_fenster_setzt_kein_feld():
    rec = {"fingerprint": "abc", "abschnitte": [{"von_s": 0, "bis_s": 5, "perspektive_hoehe": "Augenhöhe"}]}
    tele = {"quelle": "rtmd", "perspektive_hoehe": "Augenhöhe", "fenster": [], "fenster_s": 2.0}
    neu, _ = S.telemetrie_anwenden(rec, tele, 2.0)
    assert "bewegung_spitzen" not in neu["abschnitte"][0]
