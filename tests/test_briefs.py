from niro_transcribe.briefs import load_briefs


def test_load_briefs(tmp_path):
    y = tmp_path / "briefs.yaml"
    y.write_text(
        "global:\n"
        "  wiederverwendung: mehrfach\n"
        "  anzahl_videos: 2\n"
        "videos:\n"
        "  - titel: V1\n"
        "    fokus: Einstieg\n"
        "    person: durchmischen\n"
        "    ziel_laenge_sek: 90\n"
        "  - titel: V2\n"
        "    fokus: Technik\n"
        "    person: Milena\n"
        "    dramaturgie: AIDA\n",
        encoding="utf-8",
    )
    briefs, gconf = load_briefs(y)
    assert gconf.wiederverwendung == "mehrfach"
    assert gconf.anzahl_videos == 2
    assert len(briefs) == 2
    assert briefs[0].titel == "V1" and briefs[0].ziel_laenge_sek == 90
    assert briefs[1].person == "Milena" and briefs[1].dramaturgie == "AIDA"
    assert briefs[1].ziel_laenge_sek is None


def test_load_briefs_defaults_global(tmp_path):
    y = tmp_path / "briefs.yaml"
    y.write_text("videos:\n  - titel: V1\n    fokus: x\n    person: durchmischen\n", encoding="utf-8")
    _, gconf = load_briefs(y)
    assert gconf.wiederverwendung == "exklusiv"
    assert gconf.anzahl_videos is None
