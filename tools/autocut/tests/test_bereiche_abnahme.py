"""Abnahme der stabilen Läufe (frame-genau, Spec 2026-09-25) gegen die 30 Urteile vom 22.09., die vier WLC-Clips vom
23.09. und die 32 Klebl-Shots vom 25.09.

Die Tests lesen die Schwellen aus defaults.yaml — jede Änderung an ruhig_max_px, bewegung_max, glatt_s oder
stabil_min_s muss hier wieder antreten. Exakte Läufe und Mengen sind Änderungsmelder (gemessene Werte), keine Urteile;
bewegung_max 3,0 aus der Review-Runde Schnittkanten (25.09.2026).
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
                 "FX3_0265.MP4", "FX3_0274.MP4", "FX3_0282.MP4", "FX3_0648.MP4", "FX3_0662.MP4", "FX3_0666.MP4",
                 "FX3_0668.MP4", "FX3_0671.MP4", "FX3_0673.MP4", "FX3_0674.MP4", "FX3_0677.MP4", "FX3_0678.MP4",
                 "FX3_0680.MP4", "FX3_0690.MP4", "FX3_0699.MP4", "FX3_0701.MP4", "FX3_0705.MP4", "FX3_0710.MP4",
                 "FX3_0713.MP4"}


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
    # R2#10 ist durch die Anmerkung „brauchbar am Anfang“ gedeckt; Änderungsmelder bewegung_max 3,0
    assert treffer == ["R2#10", "R2#14"]


def test_abnahme_wlc_laeufe_unveraendert():
    """Gegen gemessene Werte, damit eine Schwellenänderung sichtbar wird statt still durchzugehen."""
    erwartet = {"FX3_8636": [[0.0, 11.52]], "FX3_8641": [[0.0, 4.56]],
                "FX3_8660": [[1.2, 3.36], [7.12, 10.36], [12.04, 18.36]],
                "FX3_8663": [[8.36, 15.92], [35.8, 40.44], [41.64, 46.64], [54.04, 59.0], [62.4, 71.12],
                             [71.72, 78.72]]}
    for e in _json("bereiche-wlc.json"):
        assert [[a, z] for a, z, _wk, _bw in T.stabile_bereiche(e["telemetrie"], CFG)] == erwartet[e["clip"]], e["clip"]


@pytest.mark.parametrize("clip,von,bis", [("FX3_8636", 4.5, 7.5), ("FX3_8641", 1.5, 4.0), ("FX3_8663", 9.0, 12.0),
                                          ("FX3_8663", 63.5, 66.5), ("FX3_8660", 12.5, 15.5)])
def test_abnahme_wlc_bereiche_des_users_liegen_in_einem_lauf(clip, von, bis):
    e = next(x for x in _json("bereiche-wlc.json") if x["clip"] == clip)
    assert _im_lauf(e["telemetrie"], von, bis)


def test_abnahme_klebl_einschwingen_wie_der_user_es_sieht():
    """Review-Runde Schnittkanten (25.09.2026): der einzige Einsetzer, den der User so nicht schneiden würde, ist FX3_0260
    1,5–3,5 s — „erst ab hier smooth“ bei 2,18 s im Clip. Der Shot liegt in keinem Lauf, hat am In-Punkt einen
    Kantenbefund, und der frame-genaue Lauf beginnt höchstens 0,1 s neben der Stelle des Users."""
    s = next(x for x in _json("bereiche-klebl.json") if x["clip"] == "FX3_0260.MP4")
    assert not _im_lauf(s["telemetrie"], s["von_s"], s["bis_s"])
    befunde = T.kanten_befunde(s["telemetrie"], CFG, s["von_s"], s["bis_s"])
    assert any(k.seite == "in" and k.gemessen for k in befunde)
    starts = [a for a, _z, _wk, _bw in T.stabile_bereiche(s["telemetrie"], CFG) if a >= s["von_s"]]
    assert starts and abs(starts[0] - 2.18) <= 0.1, starts


def test_abnahme_klebl_shots_in_einem_lauf_unveraendert():
    shots = _json("bereiche-klebl.json")
    assert len(shots) == 32
    drin = {s["clip"] for s in shots if _im_lauf(s["telemetrie"], s["von_s"], s["bis_s"])}
    assert drin == KLEBL_IM_LAUF                   # Änderungsmelder (bewegung_max 3,0)


KLEBL_KANTENBEFUNDE = {"FX3_0252.MP4", "FX3_0260.MP4", "FX3_0267.MP4", "FX3_0653.MP4", "FX3_0675.MP4",
                       "FX3_0700.MP4", "a7MK4_20260922_0317.MP4"}


def test_abnahme_klebl_kantenpruefung_unveraendert():
    """Kantenbefunde (Hinweise) der 32 Shots bei bewegung_max 3,0 — Änderungsmelder; der User hat in der
    Review-Runde nur FX3_0260 abgelehnt."""
    fehler = set()
    for s in _json("bereiche-klebl.json"):
        befunde = T.kanten_befunde(s["telemetrie"], CFG, s["von_s"], s["bis_s"], 1.0 / s["tempo"])
        if any(k.seite != "mitte" and k.gemessen for k in befunde):
            fehler.add(s["clip"])
    assert fehler == KLEBL_KANTENBEFUNDE
