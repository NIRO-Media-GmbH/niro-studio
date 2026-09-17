"""replay_kommentare.py: Kommentare aus Markern und Chrome-JSON, Clips, Stand, neu/bekannt, Markdown."""
from __future__ import annotations

import pytest

from niro_autocut import replay_kommentare as KO
from niro_autocut.charge import AutoCutError

MERKMAL = {"color": "FrameIO"}


def _snap(start=0, quell_in=0, tempo=100.0):
    def item(t):
        return {"name": "FX3_1.MP4", "datei": "/nas/FX3_1.MP4", "start": start, "dauer": 200, "quell_in": quell_in,
                "aktiv": True, "tempo": t}
    return {"fps": 24.0, "start_timecode": "01:00:00:00", "laenge": 240, "spuren": {"V1": [item(tempo)], "A1": [item(None)]}}


def test_aus_markern_nur_frameio_und_nicht_schon_beim_upload():
    marker = {"10": {"color": "Blue", "name": "#1 Hook", "note": "", "duration": 1, "customData": ""},
              "48.0": {"color": "FrameIO", "name": "Marker 1", "note": "Test 1", "duration": 1, "customData": ""},
              "120": {"color": "FrameIO", "name": "Marker 2", "note": "Alt aus Kopie", "duration": 1, "customData": ""}}
    vorher = {"120": {"color": "FrameIO", "name": "Marker 2", "note": "Alt aus Kopie", "duration": 1, "customData": ""}}
    k = KO.aus_markern(marker, MERKMAL, vorher)
    assert [(x["nr"], x["frame"], x["text"], x["quelle"]) for x in k] == [(1, 48, "Test 1", "api")]
    assert len(KO.aus_markern(marker, MERKMAL)) == 2


def test_aus_markern_ohne_merkmal_nimmt_neue_marker():
    marker = {"10": {"color": "Blue", "name": "#1", "note": "", "duration": 1},
              "30": {"color": "Green", "name": "Neu", "note": "Bitte kürzen", "duration": 5}}
    k = KO.aus_markern(marker, {}, {"10": {"color": "Blue", "name": "#1", "note": "", "duration": 1}})
    assert [(x["frame"], x["text"], x["dauer_frames"]) for x in k] == [(30, "Bitte kürzen", 5)]


def test_aus_json_rechnet_frames_und_prueft_schema():
    daten = {"quelle": "chrome", "kommentare": [
        {"von_s": 5.008, "bis_s": 7.0, "autor": "NIRO Productions GmbH Eckartshäuser Straße 32", "text": "B", "zeichnung": False},
        {"von_s": 2.008, "text": "A", "antworten": ["ok"], "zeichnung": True}]}
    k = KO.aus_json(daten, 24.0)
    assert [(x["nr"], x["frame"], x["dauer_frames"], x["text"], x["zeichnung"]) for x in k] == [
        (1, 48, 1, "A", True), (2, 120, 48, "B", False)]
    assert k[0]["antworten"] == ["ok"] and k[1]["autor"].startswith("NIRO") and k[0]["quelle"] == "chrome"
    with pytest.raises(AutoCutError, match="quelle"):
        KO.aus_json({"kommentare": []}, 24.0)
    with pytest.raises(AutoCutError, match="Kommentar 1"):
        KO.aus_json({"quelle": "chrome", "kommentare": [{"text": "ohne Zeit"}]}, 24.0)


@pytest.mark.parametrize("kommentar, meldung", [
    ({"von_s": float("nan"), "text": "A"}, "Kommentar 1"),
    ({"von_s": float("inf"), "text": "A"}, "Kommentar 1"),
    ({"von_s": 1.0, "text": "A", "antworten": "ok"}, "antworten"),
    ({"von_s": 1.0, "text": "A", "antworten": 5}, "antworten")])
def test_aus_json_weist_unendliche_zeiten_und_antworten_ohne_liste_ab(kommentar, meldung):
    """Rest-Review Punkt 2 (Nachtrag): NaN/Infinity in von_s und antworten ohne Liste → AutoCutError (Exit 2) statt
    ValueError/OverflowError/TypeError (Exit 1) oder still zerlegtem Text („ok" → ["o", "k"])."""
    with pytest.raises(AutoCutError, match=meldung):
        KO.aus_json({"quelle": "chrome", "kommentare": [kommentar]}, 24.0)


def test_aus_json_unendliches_bis_s_zaehlt_als_fehlend():
    k = KO.aus_json({"quelle": "chrome", "kommentare": [{"von_s": 2.0, "bis_s": float("inf"), "text": "A"}]}, 24.0)
    assert (k[0]["frame"], k[0]["dauer_frames"]) == (48, 1)


def test_clips_an_mit_tempo():
    snap = _snap(start=10, quell_in=100, tempo=50.0)
    c = KO.clips_an(snap, 30)
    assert c[0] == {"spur": "A1", "name": "FX3_1.MP4", "datei": "/nas/FX3_1.MP4", "quell_frame": 120, "aktiv": True}
    assert c[1]["spur"] == "V1" and c[1]["quell_frame"] == 110
    assert KO.clips_an(snap, 5) == []


def test_vergleiche_und_frame_im_stand():
    alt, neu = _snap(start=0), _snap(start=24)
    assert KO.vergleiche(alt, alt) == []
    assert KO.vergleiche(alt, neu) == ["A1: 1 Item(s) geändert/entfernt, 1 neu/geändert",
                                       "V1: 1 Item(s) geändert/entfernt, 1 neu/geändert"]
    clips = KO.clips_an(alt, 48)
    assert KO.frame_im_stand(clips, neu) == 72
    doppelt = _snap(start=24)
    doppelt["spuren"]["V1"].append(dict(doppelt["spuren"]["V1"][0], start=400))
    assert KO.frame_im_stand(clips, doppelt) is None
    assert KO.frame_im_stand(clips, {"spuren": {}}) is None


def test_markiere_neu_und_fremde():
    k1 = KO.aus_json({"quelle": "chrome", "kommentare": [{"von_s": 2.0, "text": "A", "autor": "NIRO Productions GmbH"}]}, 24.0)
    assert KO.markiere_neu(k1, None, "2026-09-17T10:00:00") == 1 and k1[0]["neu"] is True
    k2 = KO.aus_json({"quelle": "chrome", "kommentare": [
        {"von_s": 2.0, "text": "A", "autor": "NIRO Productions GmbH"}, {"von_s": 3.0, "text": "B", "autor": "Kunde X"}]}, 24.0)
    assert KO.markiere_neu(k2, {"kommentare": k1}, "2026-09-17T11:00:00") == 1
    assert [(x["text"], x["neu"], x["erstmals_gelesen_am"]) for x in k2] == [
        ("A", False, "2026-09-17T10:00:00"), ("B", True, "2026-09-17T11:00:00")]
    assert KO.markiere_fremde(k2, ["NIRO Productions GmbH"]) == 1 and [x["fremd"] for x in k2] == [False, True]
    assert KO.markiere_fremde(k2, []) == 0


def test_kommentare_md():
    k = KO.aus_json({"quelle": "chrome", "kommentare": [{"von_s": 2.0, "text": "Schnitt | später", "zeichnung": True}]}, 24.0)
    k[0]["tc"] = "01:00:02:00"
    k[0]["clips"] = [{"spur": "V1", "name": "FX3_1.MP4", "datei": "/nas/FX3_1.MP4", "quell_frame": 48, "aktiv": True}]
    KO.markiere_neu(k, None, "2026-09-17T10:00:00")
    KO.markiere_fremde(k, ["NIRO"])
    md = KO.kommentare_md({"titel": "T", "timeline": "T", "projekt": "P", "hochgeladen_am": "2026-09-17T09:00:00",
                           "replay_ordner": "Autocut/K/P", "lese_weg": "chrome", "gelesen_am": "2026-09-17T10:00:00",
                           "anzahl": 1, "neu": 1, "fremd": 0, "veraendert_seit_upload": None, "aenderungen": [],
                           "seit_bau_veraendert": None, "kommentare": k})
    assert md.startswith("# Replay-Kommentare: T")
    assert "| 1 | ja | 01:00:02:00 | – | Schnitt \\| später | ja | V1 FX3_1.MP4 @48 |" in md
