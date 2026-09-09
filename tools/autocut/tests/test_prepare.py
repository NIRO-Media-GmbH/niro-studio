"""Tests für scripts/autocut_prepare.py — Gruppierung, Kamera/Rolle, Proxy-Abbruch, Mischformat, media.json."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from niro_autocut.charge import AutoCutError, Charge
from niro_autocut.media import MediaInfo

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "autocut_prepare.py"
spec = importlib.util.spec_from_file_location("autocut_prepare", SCRIPT)
prep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep)


def _info(path: str, nb: int = 250, fps: float = 25.0, w: int = 3840, h: int = 2160, rot: int = 0) -> MediaInfo:
    return MediaInfo(path=path, duration_s=nb / fps, fps=fps, width=w, height=h, rotation=rot, nb_frames=nb,
                     timecode=None, has_audio=True, sample_rate=48000, channels=2)


def _index(tmp_path: Path, records: list[dict]) -> None:
    (tmp_path / "_intern" / "transcripts_index.json").write_text(json.dumps(records), encoding="utf-8")


def _rec(path: str, rolle: str | None, person: str = "Anna", fp: str = "fp1") -> dict:
    r = {"name": Path(path).name, "path": path, "kategorie": "Interviews", "person": person,
         "fingerprint": fp, "ok": True, "duration_s": 10.0, "n_words": 3}
    if rolle:
        r["kamera_rolle"] = rolle
    return r


def test_kamera_and_rolle_derivation():
    assert prep.kamera_from_name("FX3_9981.MP4") == "FX3"
    assert prep.kamera_from_name("a7MK4_20260702_9966.MP4") == "a7MK4"
    assert prep.kamera_from_name("C0001.MP4") is None
    assert prep.rolle_for({"kamera_rolle": "kontext"}, "FX3") == "kontext"
    assert prep.rolle_for({"name": "x"}, "FX3") == "ton"
    assert prep.rolle_for({"name": "x"}, "a7MK4") == "kontext"
    with pytest.raises(AutoCutError, match="Kamerarolle"):
        prep.rolle_for({"name": "C0001.MP4"}, None)


def test_build_media_groups_pairs_and_format(charge_dir):
    fx = "/nas/Interviews/Anna/FX3_0001.MP4"
    a7 = "/nas/Interviews/Anna/a7MK4_0001.MP4"
    fx2 = "/nas/Interviews/Ben/FX3_0002.MP4"
    _index(charge_dir, [_rec(fx, "ton"), _rec(a7, None, fp="fp2"), _rec(fx2, "ton", person="Ben", fp="fp3")])
    ch = Charge.open(charge_dir)
    infos = {fx: _info(fx, rot=90), a7: _info(a7, w=1920, h=1080, rot=90), fx2: _info(fx2, nb=300, rot=90),
             "/nas/Interviews/Anna/Proxy/FX3_0001.mov": _info("p", w=1920, h=1080, nb=251),
             "/nas/Interviews/Anna/Proxy/a7MK4_0001.mov": _info("p", w=1920, h=1080)}
    proxies = {fx: Path("/nas/Interviews/Anna/Proxy/FX3_0001.mov"), a7: Path("/nas/Interviews/Anna/Proxy/a7MK4_0001.mov")}
    media, warn = prep.build_media(ch, probe=lambda p: infos[str(p)], proxy_finder=lambda p: proxies.get(str(p)))
    assert media["format"] == {"fps": 25.0, "width": 2160, "height": 3840, "orientation": "9:16"}
    assert media["ordner"] == {"Anna": {"ton": [fx], "kontext": [a7]}, "Ben": {"ton": [fx2], "kontext": []}}
    c = media["clips"][a7]
    assert c["kamera"] == "a7MK4" and c["rolle"] == "kontext" and c["ordner"] == "Anna" and c["fingerprint"] == "fp2"
    assert c["proxy_path"].endswith("a7MK4_0001.mov") and c["proxy"]["width"] == 1920
    assert media["clips"][fx]["original"]["nb_frames"] == 250 and media["clips"][fx]["proxy"]["nb_frames"] == 251
    assert media["clips"][fx2]["proxy"] is None and media["clips"][fx2]["proxy_path"] is None
    assert any("kein Proxy" in w for w in warn) and any("Ben" in w and "kein a7" in w for w in warn)
    # Kontext-Kamera mit anderer Auflösung ist nur eine Warnung
    assert any("1080" in w and "Kontext" in w for w in warn)


def test_build_media_aborts_on_proxy_mismatch(charge_dir):
    fx = "/nas/Interviews/Anna/FX3_0001.MP4"
    _index(charge_dir, [_rec(fx, "ton")])
    ch = Charge.open(charge_dir)
    infos = {fx: _info(fx), "/nas/Interviews/Anna/Proxy/FX3_0001.mov": _info("p", nb=260, fps=30.0)}
    with pytest.raises(AutoCutError) as ei:
        prep.build_media(ch, probe=lambda p: infos[str(p)],
                         proxy_finder=lambda p: Path("/nas/Interviews/Anna/Proxy/FX3_0001.mov"))
    msg = str(ei.value)
    assert "Bildrate" in msg and "Frames" in msg and "FX3_0001.MP4" in msg


def test_build_media_aborts_on_mixed_format(charge_dir):
    fx = "/nas/Interviews/Anna/FX3_0001.MP4"
    fx2 = "/nas/Interviews/Ben/FX3_0002.MP4"
    _index(charge_dir, [_rec(fx, "ton"), _rec(fx2, "ton", person="Ben", fp="fp3")])
    ch = Charge.open(charge_dir)
    infos = {fx: _info(fx, rot=90), fx2: _info(fx2)}
    with pytest.raises(AutoCutError, match="Mischformat"):
        prep.build_media(ch, probe=lambda p: infos[str(p)], proxy_finder=lambda p: None)
    infos = {fx: _info(fx), fx2: _info(fx2, fps=50.0)}
    with pytest.raises(AutoCutError, match="50.0 fps"):
        prep.build_media(ch, probe=lambda p: infos[str(p)], proxy_finder=lambda p: None)


def test_build_media_collects_missing_files(charge_dir):
    fx = "/nas/Interviews/Anna/FX3_0001.MP4"
    a7 = "/nas/Interviews/Anna/a7MK4_0001.MP4"
    _index(charge_dir, [_rec(fx, "ton"), _rec(a7, "kontext", fp="fp2")])
    ch = Charge.open(charge_dir)

    def probe(p):
        raise AutoCutError(f"Datei nicht gefunden: {p}\nIst das NAS gemountet?")

    with pytest.raises(AutoCutError) as ei:
        prep.build_media(ch, probe=probe, proxy_finder=lambda p: None)
    assert "FX3_0001.MP4" in str(ei.value) and "a7MK4_0001.MP4" in str(ei.value) and "nicht geschrieben" in str(ei.value)


def test_build_media_requires_ton_clip(charge_dir):
    a7 = "/nas/Interviews/Anna/a7MK4_0001.MP4"
    _index(charge_dir, [_rec(a7, "kontext")])
    ch = Charge.open(charge_dir)
    with pytest.raises(AutoCutError, match="ton"):
        prep.build_media(ch, probe=lambda p: _info(str(p)), proxy_finder=lambda p: None)


PLAN_MD = ("# Test\n\nFormat 16:9, Ziel ~60 s\n\n| # | Szene | O-Ton | Quelle | Bild | Sound | Caption | Kommentar |\n"
           "|---|---|---|---|---|---|---|---|\n| 1 | Start | „Hallo“ | Anna (FX3_0001, 00:01) | Gesicht | Raumton | | ~3 s |\n")
_ORIG_BUILD = prep.build_media


def _write_plan(charge_dir: Path) -> None:
    (charge_dir / "Ergebnisse" / "O-Ton-Pläne" / "video-1-test.md").write_text(PLAN_MD, encoding="utf-8")


def _build_with_fakes(ch):
    return _ORIG_BUILD(ch, probe=lambda p: _info(str(p), rot=90), proxy_finder=lambda p: None)


def test_main_writes_media_json_and_warns_on_plan_format(charge_dir, monkeypatch, capsys):
    fx = "/nas/Interviews/Anna/FX3_0001.MP4"
    _index(charge_dir, [_rec(fx, "ton")])
    _write_plan(charge_dir)
    monkeypatch.setattr(prep, "build_media", _build_with_fakes)   # kein ffprobe, kein NAS
    rc = prep.main([str(charge_dir)])
    out = capsys.readouterr().out
    assert rc == 0
    data = json.loads((charge_dir / "_intern" / "autocut" / "media.json").read_text(encoding="utf-8"))
    assert data["format"]["orientation"] == "9:16" and fx in data["clips"]
    assert "Plan nennt 16:9" in out and "Geschrieben" in out


def test_main_returns_1_on_abort(charge_dir, capsys):
    _index(charge_dir, [_rec("/nas/Interviews/Anna/FX3_0001.MP4", "ton")])
    _write_plan(charge_dir)
    rc = prep.main([str(charge_dir)])   # echtes ffprobe → Datei fehlt → Abbruch
    err = capsys.readouterr().err
    assert rc == 1 and "FEHLER" in err and "nicht geschrieben" in err
    assert not (charge_dir / "_intern" / "autocut" / "media.json").exists()


def test_main_returns_1_without_plan_table(charge_dir, capsys):
    _index(charge_dir, [_rec("/nas/Interviews/Anna/FX3_0001.MP4", "ton")])
    rc = prep.main([str(charge_dir)])   # Fixture-Plan hat keine Ablauf-Tabelle
    assert rc == 1 and "Ablauf-Tabelle" in capsys.readouterr().err
