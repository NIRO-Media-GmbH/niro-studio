from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import pytest

from niro_review import ablage
from niro_review.ablage import ReviewFehler


def test_nfc_normalisiert():
    nfd = unicodedata.normalize("NFD", "Förch")
    assert ablage.nfc(nfd) == "Förch" and ablage.nfc(nfd) != nfd


def test_wurzeln_aus_umgebung(wurzeln):
    assert ablage.repo_wurzel() == wurzeln["repo"]
    assert ablage.review_wurzel() == wurzeln["review"]
    assert ablage.cache_wurzel() == wurzeln["cache"]
    assert ablage.nas_verbunden() is True


def test_review_root_direkt(wurzeln, monkeypatch, tmp_path):
    monkeypatch.setenv("NIRO_REVIEW_ROOT", str(tmp_path / "anders" / "review"))
    assert ablage.review_wurzel() == tmp_path / "anders" / "review"
    assert ablage.nas_verbunden() is False  # Elternordner fehlt


def test_ziel_relativ_mit_und_ohne_projects(wurzeln):
    z = ablage.ziel_aufloesen("projects/Dold/Recruiting/2026-07 Dreh 27-28.07")
    assert (z.kunde, z.projekt, z.charge) == ("Dold", "Recruiting", "projects/Dold/Recruiting/2026-07 Dreh 27-28.07")
    z2 = ablage.ziel_aufloesen("Dold/Recruiting/2026-07 Dreh 27-28.07/")
    assert z2 == z


def test_ziel_absolut_und_nfd(wurzeln):
    nfd = unicodedata.normalize("NFD", "Förch")
    charge = wurzeln["repo"] / "projects" / nfd / "Recruiting" / "2026-06 Dreh"
    charge.mkdir(parents=True)
    z = ablage.ziel_aufloesen(str(charge))
    assert z.kunde == "Förch" and z.charge == "projects/Förch/Recruiting/2026-06 Dreh"


def test_ziel_kunde_projekt(wurzeln):
    z = ablage.ziel_aufloesen("Dold/Recruiting")
    assert (z.kunde, z.projekt, z.charge) == ("Dold", "Recruiting", None)


def test_ziel_fehler(wurzeln, tmp_path):
    with pytest.raises(ReviewFehler):
        ablage.ziel_aufloesen("Dold")
    with pytest.raises(ReviewFehler):
        ablage.ziel_aufloesen(str(tmp_path / "woanders" / "a" / "b" / "c"))


def test_finde_kind_nfd(tmp_path):
    nfd = unicodedata.normalize("NFD", "Förch")
    (tmp_path / nfd).mkdir()
    gefunden = ablage.finde_kind(tmp_path, "Förch")
    assert gefunden.is_dir() and gefunden.name == nfd
    assert ablage.finde_kind(tmp_path, "Neu") == tmp_path / "Neu"


def test_json_atomar(tmp_path):
    p = tmp_path / "a" / "b.json"
    ablage.json_schreiben(p, {"x": "ä"})
    assert json.loads(p.read_text(encoding="utf-8")) == {"x": "ä"}
    assert ablage.json_lesen(p) == {"x": "ä"}
    assert ablage.json_lesen(tmp_path / "fehlt.json", {}) == {}
    assert not list((tmp_path / "a").glob(".tmp-*"))


def test_sicherer_pfad(tmp_path):
    (tmp_path / "Dold" / "Recruiting").mkdir(parents=True)
    (tmp_path / "Dold" / "Recruiting" / "video.mp4").write_bytes(b"x")
    assert ablage.sicherer_pfad(tmp_path, "Dold/Recruiting/video.mp4") == tmp_path / "Dold" / "Recruiting" / "video.mp4"
    assert ablage.sicherer_pfad(tmp_path, "Dold/../Recruiting") is None
    assert ablage.sicherer_pfad(tmp_path, "/etc/passwd") is None
    assert ablage.sicherer_pfad(tmp_path, "") is None
    assert ablage.sicherer_pfad(tmp_path, "Dold/./x") is None
    assert ablage.sicherer_pfad(tmp_path, "Dold/Neu/fehlt.mp4") == tmp_path / "Dold" / "Neu" / "fehlt.mp4"


def test_name_ok():
    assert ablage.name_ok("Dold 02 Fokus (David)")
    assert not ablage.name_ok("a/b") and not ablage.name_ok("..") and not ablage.name_ok(".versteckt") and not ablage.name_ok("")


def test_zeit_helfer():
    assert len(ablage.jetzt()) == 19 and ablage.jetzt()[10] == "T"
    assert ablage.datum_de("2026-09-18T14:02:11") == "18.09.2026"
    assert len(ablage.heute()) == 10
