"""Abnahme der stabilen Läufe (frame-genau, Spec 2026-09-25) gegen die 30 Urteile vom 22.09., die vier WLC-Clips vom
23.09. und die 32 Klebl-Shots vom 25.09.

Die Tests lesen die Schwellen aus defaults.yaml — jede Änderung an ruhig_max_px, bewegung_max, glatt_s oder
stabil_min_s muss hier wieder antreten. Exakte Läufe und Mengen sind Änderungsmelder (gemessene Werte), keine Urteile;
bewegung_max ist bis zur Review-Runde Schnittkanten UNKALIBRIERT (2,0).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from niro_autocut import telemetrie as T
from niro_autocut.charge import load_config

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CFG = load_config(Path("/nirgendwo"))["telemetrie"]
KLEBL_IM_LAUF = {"FX3_0232.MP4", "FX3_0235.MP4", "FX3_0241.MP4", "FX3_0244.MP4", "FX3_0257.MP4", "FX3_0261.MP4",
                 "FX3_0265.MP4", "FX3_0274.MP4", "FX3_0282.MP4", "FX3_0648.MP4", "FX3_0662.MP4", "FX3_0668.MP4",
                 "FX3_0671.MP4", "FX3_0673.MP4", "FX3_0677.MP4", "FX3_0678.MP4", "FX3_0680.MP4", "FX3_0690.MP4",
                 "FX3_0699.MP4", "FX3_0701.MP4", "FX3_0713.MP4"}


def _json(name: str) -> list[dict]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _im_lauf(tele: dict, von: float, bis: float) -> bool:
    return any(a - 1e-6 <= von and bis <= z + 1e-6 for a, z, _wk, _bw in T.stabile_bereiche(tele, CFG))


def _kandidaten(e: dict) -> list[tuple[float, float]]:
    """Läufe im 5-s-Beispiel, auf das Beispiel geschnitten; zu kurze Schnitte zählen nicht."""
    out = []
    for a, z, _wk, _bw in T.stabile_bereiche(e["telemetrie"], CFG):
        x, y = max(a, e["von_s"]), min(z, e["bis_s"])
        if y - x >= float(CFG["stabil_min_s"]) - 1e-6:
            out.append((round(x, 2), round(y, 2)))
    return out


def test_fixtures_tragen_reihen_je_frame():
    for name in ("bereiche-urteile.json", "bereiche-wlc.json", "bereiche-klebl.json"):
        for e in _json(name):
            v = e["telemetrie"]["verschiebung"]
            assert v["fps"] == 25.0 and len(v["dx"]) == len(v["dy"]) > 0, (name, e.get("nr") or e["clip"])


def test_fixture_traegt_die_dreissig_urteile():
    alle = _json("bereiche-urteile.json")
    assert len(alle) == 30
    assert sum(1 for e in alle if e["urteil"] == "ungewollt") == 24
    assert sum(1 for e in alle if e["urteil"].startswith("gewollt")) == 6


def test_abnahme_kein_lauf_im_komplett_ungewollten_beispiel():
    """Hartes Kriterium 1: R2#12 hat der User ausdrücklich „komplett ungewollt" genannt."""
    e = next(x for x in _json("bereiche-urteile.json") if x["nr"] == "R2#12")
    assert e["anmerkung"] == "komplett ungewollt"
    assert _kandidaten(e) == []


def test_abnahme_hoechstens_zwei_laeufe_in_ungewolltem_material():
    """Hartes Kriterium 2: höchstens 2 der 24 „ungewollt"-Beispiele dürfen einen Lauf bekommen."""
    treffer = [e["nr"] for e in _json("bereiche-urteile.json") if e["urteil"] == "ungewollt" and _kandidaten(e)]
    assert len(treffer) <= 2, f"zu viele Läufe in „ungewollt“-Material: {treffer}"
    assert treffer == ["R2#14"]                     # Änderungsmelder (bewegung_max 2,0)


def test_abnahme_wlc_laeufe_unveraendert():
    """Gegen gemessene Werte, damit eine Schwellenänderung sichtbar wird statt still durchzugehen."""
    erwartet = {"FX3_8636": [[0.0, 11.52]], "FX3_8641": [[0.0, 4.56]], "FX3_8660": [[7.16, 10.24], [13.76, 18.36]],
                "FX3_8663": [[8.36, 15.92], [35.8, 40.44], [41.64, 45.84], [54.04, 59.0], [62.4, 71.12],
                             [71.72, 78.72]]}
    for e in _json("bereiche-wlc.json"):
        assert [[a, z] for a, z, _wk, _bw in T.stabile_bereiche(e["telemetrie"], CFG)] == erwartet[e["clip"]], e["clip"]


@pytest.mark.parametrize("clip,von,bis", [("FX3_8636", 4.5, 7.5), ("FX3_8641", 1.5, 4.0), ("FX3_8663", 9.0, 12.0),
                                          ("FX3_8663", 63.5, 66.5)])
def test_abnahme_wlc_bereiche_des_users_liegen_in_einem_lauf(clip, von, bis):
    e = next(x for x in _json("bereiche-wlc.json") if x["clip"] == clip)
    assert _im_lauf(e["telemetrie"], von, bis)


@pytest.mark.xfail(strict=True, reason="FX3_8660 beginnt bei 12,5 s im Auslauf eines Schwenks (2,9 px/Frame) — ob "
                                       "das an der Kante reicht, entscheidet die Review-Runde Schnittkanten")
def test_abnahme_wlc_fx3_8660_liegt_in_einem_lauf():
    e = next(x for x in _json("bereiche-wlc.json") if x["clip"] == "FX3_8660")
    assert _im_lauf(e["telemetrie"], 12.5, 15.5)


def test_abnahme_klebl_die_vier_wackler_liegen_in_keinem_lauf():
    """Anlass der Spec: diese vier lagen in Läufen aus 2-s-Fenstern und wackelten doch."""
    shots = {s["clip"]: s for s in _json("bereiche-klebl.json")}
    for clip in ("FX3_0260.MP4", "FX3_0700.MP4", "FX3_0653.MP4", "FX3_0267.MP4"):
        s = shots[clip]
        assert not _im_lauf(s["telemetrie"], s["von_s"], s["bis_s"]), clip


def test_abnahme_klebl_shots_in_einem_lauf_unveraendert():
    shots = _json("bereiche-klebl.json")
    assert len(shots) == 32
    drin = {s["clip"] for s in shots if _im_lauf(s["telemetrie"], s["von_s"], s["bis_s"])}
    assert drin == KLEBL_IM_LAUF                   # Änderungsmelder (bewegung_max 2,0)
