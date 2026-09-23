"""Abnahme der stabilen Bereiche gegen die 30 Urteile vom 22.09. und die vier WLC-Clips vom 23.09.

Spec: docs/superpowers/specs/2026-09-23-autocut-broll-bereichsauswahl-design.md, Abschnitt „Tests".

Die 30 Urteile messen „gewollt vs. ungewollt" (Absicht), dieser Mechanismus misst „ruhig genug zum Schneiden".
Übertragbar ist nur die Fehlalarm-Richtung: in Material, das der User als unbrauchbar bezeichnet hat, darf kein
Bereich behauptet werden. Die Tests lesen die Schwellen aus defaults.yaml — jede Änderung an ruhig_max_px oder
bewegung_max muss hier wieder antreten.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from niro_autocut import telemetrie as T
from niro_autocut.charge import load_config

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CFG = load_config(Path("/nirgendwo"))["telemetrie"]


def _urteile() -> list[dict]:
    return json.loads((FIXTURES / "bereiche-urteile.json").read_text(encoding="utf-8"))


def _beispiel(nr: str) -> dict:
    return next(e for e in _urteile() if e["nr"] == nr)


def _kandidaten_mit(e: dict, cfg: dict) -> list[tuple[float, float]]:
    """Stabile Bereiche des Clips, auf das 5-s-Beispiel geschnitten; zu kurze Schnitte zählen nicht."""
    min_s = float(cfg["stabil_min_s"])
    out = []
    for a, z, _wk, _bw in T.stabile_bereiche(e["telemetrie"], cfg):
        x, y = max(a, e["von_s"]), min(z, e["bis_s"])
        if y - x >= min_s - 1e-6:
            out.append((round(x, 2), round(y, 2)))
    return out


def _kandidaten(e: dict) -> list[tuple[float, float]]:
    return _kandidaten_mit(e, CFG)


def test_fixture_traegt_die_dreissig_urteile():
    alle = _urteile()
    assert len(alle) == 30
    assert sum(1 for e in alle if e["urteil"] == "ungewollt") == 24
    assert sum(1 for e in alle if e["urteil"].startswith("gewollt")) == 6


def test_abnahme_kein_kandidat_im_komplett_ungewollten_beispiel():
    """Hartes Kriterium 1: R2#12 hat der User ausdrücklich „komplett ungewollt" genannt."""
    e = _beispiel("R2#12")
    assert e["anmerkung"] == "komplett ungewollt"
    assert _kandidaten(e) == []


def test_abnahme_hoechstens_zwei_kandidaten_in_ungewolltem_material():
    """Hartes Kriterium 2: höchstens 2 der 24 „ungewollt"-Beispiele dürfen einen Kandidaten bekommen."""
    treffer = [e["nr"] for e in _urteile() if e["urteil"] == "ungewollt" and _kandidaten(e)]
    assert len(treffer) <= 2, f"zu viele Kandidaten in „ungewollt“-Material: {treffer}"
    # R2#10 ist durch die Anmerkung gedeckt; R1#2 stammt aus Runde 1, die ohne Anmerkungen lief, und ist offen
    assert treffer == ["R1#2", "R2#10"]


def test_abnahme_r2_10_trifft_die_vom_user_genannte_stelle():
    e = _beispiel("R2#10")
    assert e["anmerkung"] == "brauchbar am Anfang und ganz kurz am Ende"
    assert _kandidaten(e) == [(2.5, 5.0)]          # genau der Anfang des Beispiels


def test_abnahme_bewegungsdeckel_haelt_den_glatten_schnellen_schwenk_draussen():
    """R2#9: wackeln 0,03–0,18 (ruhig), bewegung bis 5,3 — ohne Deckel käme hier ein Kandidat."""
    e = _beispiel("R2#9")
    assert _kandidaten(e) == []
    assert _kandidaten_mit(e, {**CFG, "bewegung_max": 99.0}) != []


@pytest.mark.parametrize("clip", ["FX3_8636", "FX3_8641", "FX3_8660", "FX3_8663"])
def test_abnahme_wlc_bereiche_des_users_liegen_in_kandidaten(clip):
    """Die vier Clips aus dem Review vom 23.09.: jeder genannte Bereich muss in einem Kandidaten liegen."""
    e = next(x for x in json.loads((FIXTURES / "bereiche-wlc.json").read_text(encoding="utf-8")) if x["clip"] == clip)
    br = T.stabile_bereiche(e["telemetrie"], CFG)
    for a, z in e["bereiche_user"]:
        assert any(x - 1e-6 <= a and z <= y + 1e-6 for x, y, _wk, _bw in br), \
            f"{clip}: {a}–{z} s liegt in keinem Kandidaten {br}"


def test_abnahme_wlc_kandidaten_unveraendert():
    """Gegen gemessene Werte, damit eine Schwellenänderung sichtbar wird statt still durchzugehen."""
    erwartet = {"FX3_8636": [[0.0, 11.52]], "FX3_8641": [[0.0, 4.8]], "FX3_8660": [[0.0, 11.0], [12.0, 18.72]],
                "FX3_8663": [[8.0, 15.0], [22.0, 27.0], [32.0, 34.0], [35.0, 40.0], [42.0, 47.0], [54.0, 59.0],
                             [63.0, 71.0], [72.0, 77.0]]}
    for e in json.loads((FIXTURES / "bereiche-wlc.json").read_text(encoding="utf-8")):
        grenzen = [[a, z] for a, z, _wk, _bw in T.stabile_bereiche(e["telemetrie"], CFG)]
        assert grenzen == erwartet[e["clip"]], e["clip"]
