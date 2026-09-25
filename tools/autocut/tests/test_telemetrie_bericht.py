"""telemetrie_bericht.py — Markdown-Bericht: Kopf, Verteilung je Kamera, unruhigste Clips, Fehler,
Vergleich mit dem Index."""
from __future__ import annotations

from niro_autocut import telemetrie_bericht as B
from reihen import reihe

ZOOM_SCHNELL = {"von_s": 2.4, "bis_s": 3.1, "von_mm": 24.0, "bis_mm": 70.0, "tempo_max": 85.2, "tempo_mittel": 60.3,
                "ruck": 0.2, "ruckartig": False, "urteil": "schnell"}
ZOOM_LANGSAM = {"von_s": 5.0, "bis_s": 9.0, "von_mm": 70.0, "bis_mm": 105.0, "tempo_max": 12.0, "tempo_mittel": 10.1,
                "ruck": 0.1, "ruckartig": False, "urteil": "langsam"}
TELE = [
    {"path": "/nas/FX3/FX3_1.MP4", "clip": "FX3_1", "kamera": "FX3", "ordner": "FX3", "quelle": "rtmd",
     "haltung": "gimbal", "bewegungsart": "fahrt", "kb_mm": 35.0, "kb_min": 35.0, "kb_max": 35.0, "zooms": [],
     "perspektive_hoehe": "Augenhöhe", "wackeln": 0.04, "bewegung": 0.5, "ruhige_fenster": [0.0, 1.0],
     "fenster": [[0.0, 0.04, 0.5, "fahrt"], [1.0, 0.04, 0.5, "fahrt"]], "fehler": None, "roll_grad": 0.4},
    {"path": "/nas/A7/a7_1.MP4", "clip": "a7_1", "kamera": "a7IV", "ordner": "A7iv", "quelle": "rtmd",
     "haltung": "hand", "bewegungsart": "schwenk_links", "kb_mm": 71.6, "kb_min": 24.0, "kb_max": 105.0,
     "zooms": [ZOOM_SCHNELL, ZOOM_LANGSAM], "zoomfahrt": True, "perspektive_hoehe": "Aufsicht",
     "wackeln": 0.41, "bewegung": 2.0, "ruhige_fenster": [], "fenster": [[0.0, 0.41, 2.0, "schwenk_links"]],
     "fehler": None, "roll_grad": 2.6},
    {"path": "/nas/Mavic/DJI_1.MOV", "clip": "DJI_1", "kamera": "DJI", "ordner": "Mavic", "quelle": "optisch",
     "haltung": "gimbal", "bewegungsart": "fahrt", "kb_mm": None, "zooms": [], "perspektive_hoehe": None,
     "wackeln": 0.02, "bewegung": 0.3, "ruhige_fenster": [0.0], "fenster": [[0.0, 0.02, 0.3, "fahrt"]],
     "fehler": None, "roll_grad": None},
    {"path": "/nas/FX3/FX3_2.MP4", "clip": "FX3_2", "kamera": "FX3", "ordner": "FX3", "quelle": "keine",
     "haltung": None, "bewegungsart": None, "kb_mm": None, "perspektive_hoehe": None, "wackeln": None,
     "bewegung": None, "ruhige_fenster": [], "fenster": [], "fehler": "Datei nicht gefunden: /nas/FX3/FX3_2.MP4",
     "roll_grad": None},
]
INDEX = {"clips": [
    {"path": "/nas/FX3/FX3_1.MP4", "kamerabewegung": "Gimbal",
     "abschnitte": [{"von_s": 0, "bis_s": 4, "brennweite": "normal", "perspektive_hoehe": "Augenhöhe"}]},
    {"path": "/nas/A7/a7_1.MP4", "kamerabewegung": "Handkamera",
     "abschnitte": [{"von_s": 0, "bis_s": 2, "brennweite": "normal", "perspektive_hoehe": "Aufsicht"},
                    {"von_s": 2, "bis_s": 4, "brennweite": "tele", "perspektive_hoehe": "Augenhöhe"}]},
    {"path": "/nas/Mavic/DJI_1.MOV", "kamerabewegung": "Drohne",
     "abschnitte": [{"von_s": 0, "bis_s": 3, "brennweite": "weit"}]},
]}


def test_bericht_kopf_verteilung_und_unruhigste():
    md = B.bericht_md(TELE, "Kunde A / Projekt B / 2026-09 Dreh")
    assert md.startswith("# Kamera-Telemetrie — Kunde A / Projekt B / 2026-09 Dreh")
    assert "4 Clips" in md and "rtmd 2" in md and "optisch 1" in md and "keine 1" in md and "Fehler 1" in md
    assert "| FX3 |" in md and "| a7IV |" in md and "| DJI |" in md
    assert "## Unruhigste Clips" in md and md.index("a7_1") < md.index("FX3_1")          # nach wackeln absteigend
    assert "0,41" in md and "schief 2,6°" in md
    assert "## Clips ohne Daten oder mit Fehler" in md and "FX3_2" in md and "Datei nicht gefunden" in md
    assert "## Vergleich" not in md


def test_vergleich_index_zaehlt_uebereinstimmung():
    v = B.vergleich_index(TELE, INDEX)
    assert set(v) == {"perspektive_hoehe", "haltung"}                      # keine Brennweite mehr (Spec 2026-09-21)
    # FX3 Augenhöhe = Augenhöhe, a7 A1 Aufsicht = Aufsicht, A2 Aufsicht ≠ Augenhöhe
    assert v["perspektive_hoehe"]["n"] == 3 and v["perspektive_hoehe"]["gleich"] == 2
    assert (v["haltung"]["n"] == 3 and v["haltung"]["kreuz"][("gimbal", "Gimbal")] == 1
            and v["haltung"]["kreuz"][("hand", "Handkamera")] == 1)
    md = B.bericht_md(TELE, "T", INDEX)
    assert "## Vergleich mit dem B-Roll-Index" in md and "Perspektive Höhe: 2 von 3" in md
    assert "Brennweite: " not in md and "| gimbal | Gimbal | 1 |" in md


def test_bericht_ohne_clips():
    md = B.bericht_md([], "Leer")
    assert "0 Clips" in md and "## Unruhigste Clips" in md


def test_bericht_unschaerfste_fenster_nur_mit_schaerfe():
    assert "## Unschärfste Fenster" not in B.bericht_md(TELE, "T")
    mit = [{**TELE[0], "schaerfe_p10": 0.4, "fenster": [[0.0, 0.04, 0.5, "fahrt", 0.35], [1.0, 0.04, 0.5, "fahrt", 0.9]]}]
    md = B.bericht_md(mit, "T")
    assert "## Unschärfste Fenster" in md and md.index("| FX3_1 | FX3 | 0 | 0,35 |") < md.index("| FX3_1 | FX3 | 1 | 0,90 |")


def test_vergleich_index_nutzt_claudes_originalwerte():
    """I2: nach Stufe 2b stehen in brennweite/perspektive_hoehe die Telemetrie-Werte — verglichen wird gegen Claudes
    Originalwerte in ``claude``; fehlen sie (Altbestand) und stammt das Feld laut felder_quelle aus der Telemetrie,
    wird der Abschnitt für dieses Feld übersprungen (kein Selbstvergleich)."""
    index = {"clips": [
        {"path": "/nas/A7/a7_1.MP4", "kamerabewegung": "Handkamera",
         "felder_quelle": {"brennweite": "rtmd", "perspektive_hoehe": "rtmd"},
         "abschnitte": [{"von_s": 0, "bis_s": 2, "brennweite": "tele", "perspektive_hoehe": "Aufsicht",
                         "claude": {"brennweite": "normal", "perspektive_hoehe": "Augenhöhe"}},
                        {"von_s": 2, "bis_s": 4, "brennweite": "tele", "perspektive_hoehe": "Aufsicht"}]}]}
    v = B.vergleich_index(TELE, index)
    assert "brennweite" not in v
    assert v["perspektive_hoehe"]["n"] == 1 and v["perspektive_hoehe"]["kreuz"][("Aufsicht", "Augenhöhe")] == 1


def test_bericht_nennt_kameras_ohne_kalibrierung():
    """M8 (Spec „Kamera unbekannt → Hinweis im Bericht"): rtmd-Kameras, die nicht in px_faktor stehen, laufen mit
    px_faktor 1,0 — der Bericht nennt sie unter dem Kopf; ohne px_faktor-Angabe kein Hinweis (bisherige Aufrufe)."""
    md = B.bericht_md(TELE, "T", px_faktor={"FX3": 0.6})
    zeile = next(z for z in md.splitlines() if "ohne Kalibrierung" in z)
    assert "a7IV (1 Clip)" in zeile and "px_faktor 1,0 angenommen" in zeile
    assert "FX3" not in zeile and "DJI" not in zeile                                  # kalibriert bzw. optisch
    assert md.index(zeile) < md.index("## Verteilung je Kamera")
    assert "ohne Kalibrierung" not in B.bericht_md(TELE, "T")
    assert "ohne Kalibrierung" not in B.bericht_md(TELE, "T", px_faktor={"FX3": 0.6, "a7IV": 0.69})


def test_verteilung_brennweite_in_mm():
    md = B.bericht_md(TELE, "T")
    assert "Brennweite KB mm: Median (Spanne)" in md and "weit/normal/tele" not in md
    zeilen = {z.split("|")[1].strip(): z for z in md.splitlines() if z.startswith("| ")}
    assert "| 35,0 (35–35) |" in zeilen["FX3"] and "| 71,6 (24–105) |" in zeilen["a7IV"] and "| – |" in zeilen["DJI"]


def test_bericht_schnelle_zoomfahrten():
    md = B.bericht_md(TELE, "T")
    assert "## Schnelle Zoomfahrten" in md and "| a7_1 | a7IV | 2,4–3,1 | 24,0 → 70,0 | 85/60 | nein |" in md
    assert "5,0–9,0" not in md                                             # langsame Fahrt steht nicht in der Liste
    assert md.index("## Unruhigste Clips") < md.index("## Schnelle Zoomfahrten") < md.index("## Clips ohne Daten")
    ohne = B.bericht_md([{**TELE[0]}], "T")
    assert "## Schnelle Zoomfahrten" in ohne and ohne.split("## Schnelle Zoomfahrten")[1].splitlines()[2] == "- keine"
    alt = [{k: v for k, v in TELE[1].items() if k != "zooms"}]                # Datensatz von vor der Umstellung
    assert "- keine" in B.bericht_md(alt, "T").split("## Schnelle Zoomfahrten")[1]


def test_bericht_schnelle_zoomfahrten_nennen_den_sprung():
    """Nachtrag Final Review (21.09.2026): die Tabelle zeigt, warum eine Fahrt schnell ist — neben Tempo und ruckartig
    der Sprung (``sprunghaft``: Änderung in 0,12 s ab ``zoom_sprung_proz``) als „14 %", sonst „–" (auch bei Datensätzen
    von vor dem Sprung-Kriterium)."""
    sprung = {**ZOOM_SCHNELL, "von_s": 12.0, "bis_s": 12.3, "von_mm": 50.0, "bis_mm": 57.8, "tempo_max": 72.4,
              "tempo_mittel": 40.1, "sprung_proz": 14.3, "sprunghaft": True}
    ruck = {**ZOOM_SCHNELL, "von_s": 20.0, "bis_s": 22.0, "tempo_max": 20.2, "tempo_mittel": 8.4, "ruckartig": True,
            "sprung_proz": 3.1, "sprunghaft": False}
    md = B.bericht_md([{**TELE[1], "zooms": [ZOOM_SCHNELL, sprung, ruck, ZOOM_LANGSAM]}], "T")
    teil = md.split("## Schnelle Zoomfahrten")[1]
    assert "Sprung (Änderung der Brennweite in 0,12 s ab `telemetrie.zoom_sprung_proz`)" in teil
    assert "| Clip | Kamera | von–bis (s) | mm → mm | Tempo % pro s (Spitze/Mittel) | ruckartig | Sprung in 0,12 s |" in teil
    assert "| a7_1 | a7IV | 2,4–3,1 | 24,0 → 70,0 | 85/60 | nein | – |" in teil          # Datensatz ohne Sprung-Felder
    assert "| a7_1 | a7IV | 12,0–12,3 | 50,0 → 57,8 | 72/40 | nein | 14 % |" in teil
    assert "| a7_1 | a7IV | 20,0–22,0 | 24,0 → 70,0 | 20/8 | ja | – |" in teil


def test_bericht_nennt_ruhige_laeufe_frame_genau():
    tele = [{**TELE[0], "verschiebung": reihe((2.4, 0.0, 0.0), (0.8, 5.0, 0.0), (4.8, 0.0, 0.0)), "dauer_s": 8.0}]
    tcfg = {"ruhig_max_px": 0.15, "bewegung_max": 2.0, "glatt_s": 0.4, "stabil_min_s": 2.0}
    md = B.bericht_md(tele, "T", tcfg=tcfg)
    assert "ruhige Läufe (s)" in md and "0,00–2,24; 3,44–8,00" in md
    assert "ruhige Fenster" not in B.bericht_md(TELE, "T")
