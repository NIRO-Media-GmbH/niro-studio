import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auswahl as A  # noqa: E402


def kand(frame, shot, punkte, art="person", ok=True, **kw):
    k = {"frame": frame, "shot": shot, "punkte": punkte, "art": art, "gesicht_ok": ok, "nahe_schnitt": False}
    k.update(kw)
    return k


def test_bewerte_person_mit_offenen_augen():
    k = A.bewerte({"aesthetik": 0.6, "utility": False, "schaerfe_n": 1.0,
                   "gesichter": [{"box": [0.4, 0.2, 0.6, 0.32], "qualitaet": 0.8, "augen": 0.3, "mund": 0.05}]})
    assert k["art"] == "person" and k["gesicht_ok"] is True
    assert k["punkte"] == round(0.45 * 0.8 + 0.35 * 0.8 + 0.20 * 1.0, 4)


def test_bewerte_abzuege_augen_zu_und_ig_zone():
    k = A.bewerte({"aesthetik": 0.6, "schaerfe_n": 1.0,
                   "gesichter": [{"box": [0.4, 0.6, 0.6, 0.72], "qualitaet": 0.8, "augen": 0.1, "mund": 0.05}]})
    assert k["gesicht_ok"] is False and "Augen zu" in k["gruende"]
    assert k["punkte"] == round(0.45 * 0.8 + 0.35 * 0.8 + 0.20 - 0.5 - 0.3, 4)


def test_bewerte_mund_offen_abzug_gedeckelt():
    k = A.bewerte({"aesthetik": 0.0, "schaerfe_n": 0.0,
                   "gesichter": [{"box": [0.4, 0.2, 0.6, 0.32], "qualitaet": 0.5, "augen": 0.3, "mund": 0.9}]})
    assert k["punkte"] == round(0.45 * 0.5 + 0.35 * 0.5 - 0.2, 4)


def test_bewerte_kleines_gesicht_ist_thema():
    k = A.bewerte({"aesthetik": 0.2, "utility": True, "schaerfe_n": 0.5,
                   "gesichter": [{"box": [0.5, 0.3, 0.52, 0.33], "qualitaet": 0.9, "augen": 0.3, "mund": 0.0}]})
    assert k["art"] == "thema" and k["gesicht_ok"] is False
    assert k["punkte"] == round(0.6 * 0.6 + 0.4 * 0.5 - 0.2, 4)


def test_waehle_person_dann_bestes_dann_thema():
    ks = [kand(10, "a", 0.9), kand(15, "a", 0.88), kand(100, "b", 0.8), kand(200, "c", 0.5, art="thema", ok=False),
          kand(300, "d", 0.95, art="thema", ok=False)]
    assert [k["frame"] for k in A.waehle(ks, fps=25)] == [10, 300, 200]


def test_waehle_lockert_bei_nur_einer_einstellung():
    ks = [kand(0, "a", 0.9), kand(20, "a", 0.85), kand(80, "a", 0.8), kand(160, "a", 0.7)]
    assert [k["frame"] for k in A.waehle(ks, fps=25)] == [0, 80, 160]


def test_waehle_ohne_gute_person_nimmt_bestes_motiv():
    ks = [kand(0, "a", 0.6, ok=False), kand(100, "b", 0.7, art="thema", ok=False)]
    assert [k["frame"] for k in A.waehle(ks, fps=25, anzahl=1)] == [100]


def test_nahe_schnitt_faellt_weg():
    ks = [kand(48, "a", 0.99, nahe_schnitt=True), kand(10, "a", 0.5)]
    assert [k["frame"] for k in A.waehle(ks, fps=25, anzahl=1)] == [10]
    assert A.nahe_schnitt(48, [50]) and not A.nahe_schnitt(47, [50])


def test_fuer_bogen_je_shot_begrenzt_und_vorschlaege_drin():
    ks = [kand(i * 30, "a" if i < 6 else "b", 1 - i * 0.01) for i in range(10)]
    b = A.fuer_bogen(ks, [ks[0], ks[6]], fps=25, n=6, je_shot=2)
    assert [k["frame"] for k in b] == [0, 30, 60, 180, 210, 240]


def test_dateinamen_und_nummern():
    namen = ["08 - Duroc vs. Normal_V4_Thumbnail_1.jpg", "08 - Duroc vs. Normal_V4_Thumbnail_3_4K.jpg",
             "08 - Duroc vs. Normal_V3_Thumbnail_7.jpg", "anderes.jpg"]
    assert A.naechste_nummer(namen, "08 - Duroc vs. Normal", "V4") == 4
    assert A.naechste_nummer([], "0 - Tagesessen", "V2") == 1
    assert A.dateiname("0 - Tagesessen", "V2", 2, vier_k=True) == "0 - Tagesessen_V2_Thumbnail_2_4K.jpg"


def test_hoechste_version_und_shot():
    namen = ["12 - Hackfleisch_V1.mp4", "12 - Hackfleisch_V10.mp4", "12 - Hackfleisch_V4.mp4", "x_V99.mp4"]
    assert A.hoechste_version(namen, "12 - Hackfleisch") == "V10"
    assert A.hoechste_version([], "12 - Hackfleisch") is None
    seg = [{"start": 0, "ende": 50, "id": "V1@0"}, {"start": 50, "ende": 90, "id": "V3@50"}]
    assert A.shot_von(49, seg) == "V1@0" and A.shot_von(50, seg) == "V3@50" and A.shot_von(95, seg) == "?"


def test_rang_normiert():
    assert A.rang_normiert([3.0, 1.0, 2.0]) == [1.0, 0.0, 0.5]
    assert A.rang_normiert([5.0]) == [1.0] and A.rang_normiert([]) == []


def test_versionen_und_nummern_mit_nfd_namen_vom_nas():
    import unicodedata
    video = "18 - Umfrage - Schnitzel und Fleischkäs"
    nfd = lambda s: unicodedata.normalize("NFD", s)  # noqa: E731
    assert A.hoechste_version([nfd(f"{video}_V2.mp4"), nfd(f"{video}_V3.mp4")], video) == "V3"
    assert A.naechste_nummer([nfd(f"{video}_V3_Thumbnail_2_4K.jpg")], video, "V3") == 3


def test_bildfolge_maskiert_prozent_im_ordner():
    import thumbnail as T
    from pathlib import Path
    assert T.bildfolge(Path("/x/02 - Napoli 100%_V3_kandidaten"), "k_%05d.jpg") == "/x/02 - Napoli 100%%_V3_kandidaten/k_%05d.jpg"
