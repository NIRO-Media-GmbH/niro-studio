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

    def fake_clip(charge, c, client, cfg, prompt, force):
        n_rep = 1 if c["datei"] == "FX3_2.MP4" else 0
        return {**c, "abschnitte": [{**a, **_GOOD_ITEM, "setup_hash": "0" * 16} for a in c["abschnitte"]],
                "nachlauf": {"usage": dict(_USAGE), "reparaturen": n_rep}, "_cache": False}

    monkeypatch.setattr(S, "index_sections_clip", fake_clip)
    out = S.index_sections(ch, {"clips": [rec, rec_b]}, _CFG2, parallel=1)
    assert out["anzahl"] == 2 and out["fehler"] == [] and out["reparaturen"] == 1
    written = json.loads((ch.autocut / "broll_index.json").read_text())
    assert written["nachlauf"]["reparaturen"] == 1
