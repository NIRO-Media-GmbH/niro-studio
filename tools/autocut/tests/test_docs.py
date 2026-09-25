"""Task 12 — Doku, Workflow, Trigger: Dateien vorhanden, alle CLI-Einstiege dokumentiert, genau eine Trigger-Zeile."""
from __future__ import annotations

import re

from niro_autocut.charge import TOOL_ROOT

STUDIO_ROOT = TOOL_ROOT.parents[1]          # tools/autocut → tools → NIRO Studio
WORKFLOW = TOOL_ROOT / "WORKFLOW-AutoCut.md"
README = TOOL_ROOT / "README.md"
SETUP = TOOL_ROOT / "SETUP.md"
CLAUDE_MD = STUDIO_ROOT / "CLAUDE.md"
RESOLVE_WORKFLOW = STUDIO_ROOT / "tools" / "resolve" / "WORKFLOW-Resolve.md"
REPLAY_PLAN = STUDIO_ROOT / "docs" / "superpowers" / "plans" / "2026-09-16-autocut-replay.md"
BEREICH_PLAN = STUDIO_ROOT / "docs" / "superpowers" / "plans" / "2026-09-23-autocut-broll-bereichsauswahl.md"
PLACE_PROMPT = TOOL_ROOT / "prompts" / "place-broll.md"
SPEC_BEREICH = STUDIO_ROOT / "docs" / "superpowers" / "specs" / "2026-09-23-autocut-broll-bereichsauswahl-design.md"

# CLI-Einstiege laut Spec Abschnitt 6 (alle mit venv/bin/python, Argument = Chargen-Ordner)
SPEC_SCRIPTS = ["autocut_prepare.py", "autocut_sync.py", "autocut_find_quote.py", "autocut_verify.py",
                "autocut_build.py", "autocut_export_xml.py", "autocut_index_broll.py",
                "autocut_place_broll.py", "autocut_read_timelines.py", "autocut_index_sections.py",
                "autocut_finalize.py", "resolve_probe_xml.py", "resolve_probe_api.py",
                "autocut_replay.py", "autocut_readback.py", "autocut_telemetrie.py"]


def _text(p) -> str:
    assert p.is_file(), f"{p} fehlt"
    return p.read_text(encoding="utf-8")


def _abschnitt(text: str, kopf: str) -> str:
    """Markdown-Abschnitt ab der Überschrift, die mit ``kopf`` beginnt, bis zur nächsten gleich hohen oder höheren."""
    m = re.search(rf"^{re.escape(kopf)}.*$", text, flags=re.M)
    assert m, f"Überschrift „{kopf}“ fehlt"
    ebene = len(kopf) - len(kopf.lstrip("#"))
    ende = re.compile(rf"^#{{1,{ebene}}} ", flags=re.M).search(text, m.end())
    return text[m.start():ende.start() if ende else len(text)]


def _flach(text: str) -> str:
    """Leerraum und Zeilenumbrüche zu je einem Leerzeichen — Suchtexte überstehen das Umbrechen der Doku."""
    return " ".join(text.split())


def _plan_schritt(task: str, nr: int) -> str:
    """Block „- [ ] **Step <nr>:" (auch abgehakt) bis zum nächsten Step (innerhalb des Tasks)."""
    m = re.search(rf"^- \[[ xX]\] \*\*Step {nr}:.*?(?=^- \[[ xX]\] \*\*Step |\Z)", task, flags=re.M | re.S)
    assert m, f"Step {nr} fehlt"
    return m.group(0)


def test_docs_exist_and_are_markdown_without_placeholders():
    for p in (WORKFLOW, README, SETUP):
        text = _text(p)
        assert text.startswith("# "), f"{p.name}: Markdown-Überschrift fehlt"
        assert "TODO" not in text and "TBD" not in text, f"{p.name}: Platzhalter im Text"


def test_workflow_covers_spec_scripts_stages_and_rules():
    text = _text(WORKFLOW)
    for s in SPEC_SCRIPTS:
        assert s in text, f"WORKFLOW-AutoCut.md nennt {s} nicht"
    for needle in ("„AutoCut: <Kunde>/<Projekt>[/<Charge>]\"", "prompts/cutlist.md", "prompts/place-broll.md",
                   "--limit 5", "Protokoll", "NAS", "Stufe 1", "Stufe 2", "Stufe 3", "Stufe 4", "Fehler"):
        assert needle in text, f"WORKFLOW-AutoCut.md: „{needle}“ fehlt"


def test_every_existing_script_is_documented():
    """Kein undokumentierter CLI-Einstieg: jedes scripts/*.py steht im Workflow, README oder SETUP."""
    docs = _text(WORKFLOW) + _text(README) + _text(SETUP)
    for p in sorted((TOOL_ROOT / "scripts").glob("*.py")):
        assert p.name in docs, f"{p.name} ist in keiner Doku erwähnt (WORKFLOW/README/SETUP ergänzen)"


def test_setup_names_venv_pth_env_and_resolve():
    text = _text(SETUP)
    for needle in ("python3.12 -m venv venv", "niro_transcribe.pth", "setup_env.py", "ANTHROPIC_API_KEY",
                   "Resolve", "pytest"):
        assert needle in text, f"SETUP.md: „{needle}“ fehlt"


def test_claude_md_has_exactly_one_autocut_trigger_after_foto():
    lines = _text(CLAUDE_MD).splitlines()
    hits = [i for i, l in enumerate(lines) if l.startswith("| „AutoCut:")]
    assert len(hits) == 1, "CLAUDE.md muss genau eine AutoCut-Trigger-Zeile enthalten"
    i = hits[0]
    assert lines[i - 1].startswith("| „Foto:"), "AutoCut-Zeile muss direkt nach der Foto-Zeile stehen"
    assert lines[i].count("|") == 4, "Trigger-Zeile braucht drei Spalten"
    assert "`tools/autocut/WORKFLOW-AutoCut.md`" in lines[i]
    assert lines[i].startswith("| „AutoCut: <Kunde>/<Projekt>[/<Charge>]\" |")


def test_resolve_workflow_exists_with_rules_and_flow():
    text = _text(RESOLVE_WORKFLOW)
    for needle in ("„Resolve: <Aufgabe>\"", "get_resolve_status", "run_script", "run_script_unsafe", "search_scripting_api",
                   "Freigabe", "Cloud-Projektbibliothek", "Ergebnisse/Export/", "Claude <Aufgabe>", "GetCurrentTimeline",
                   "Protokoll", "## Fehlerbilder", "resolve_probe_api.py", "nichts geschrieben"):
        assert needle in text, f"WORKFLOW-Resolve.md: „{needle}“ fehlt"


def test_claude_md_has_resolve_trigger_after_autocut_and_rules():
    lines = _text(CLAUDE_MD).splitlines()
    hits = [i for i, l in enumerate(lines) if l.startswith("| „Resolve: <Aufgabe>\"")]
    assert len(hits) == 1, "CLAUDE.md muss genau eine Resolve-Trigger-Zeile enthalten"
    i = hits[0]
    assert lines[i - 1].startswith("| „AutoCut:"), "Resolve-Zeile muss direkt nach der AutoCut-Zeile stehen"
    assert lines[i].count("|") == 4 and "`tools/resolve/WORKFLOW-Resolve.md`" in lines[i]
    text = "\n".join(lines)
    for needle in ("## Resolve-Regeln", "Cloud-Projektbibliothek", "Export/", ".mcp.json", "zehn Funktionen", "bei Abweichung nichts schreiben"):
        assert needle in text, f"CLAUDE.md: „{needle}“ fehlt"


def test_setup_and_workflow_are_on_21_1():
    setup = _text(SETUP)
    for needle in ("21.1", "README.md", "DaVinciResolveScript.pyi", "ResolvePython", "resolve_probe_api.py", "--project"):
        assert needle in setup, f"SETUP.md: „{needle}“ fehlt"
    workflow = _text(WORKFLOW)
    for needle in ("probe_api.json", "--project", "Resolve Studio 21.1"):
        assert needle in workflow, f"WORKFLOW-AutoCut.md: „{needle}“ fehlt"


def test_replay_ist_dokumentiert():
    wf = _text(WORKFLOW)
    for needle in ("## Review in Replay", "autocut_replay.py", "--hochladen", "einsortiert", "kommentare --timeline",
                   "finden --titel", "FrameIO", "Material/Feedback", "autocut_readback.py", "nach OK",
                   "In Projekt verschieben"):
        assert needle in wf, f"WORKFLOW-AutoCut.md: „{needle}“ fehlt"
    readme = _text(README)
    for needle in ("autocut_replay.py", "autocut_readback.py", "replay.py", "wiedergabe.py", "werkzeuge/"):
        assert needle in readme, f"README.md: „{needle}“ fehlt"
    claude = _text(CLAUDE_MD)
    assert "Review in Dropbox Replay" in claude and "Replay-Marker" in claude
    assert "10. **Dropbox Replay:**" in _text(RESOLVE_WORKFLOW)


def test_replay_upload_nach_rohschnitt_nur_mit_stufe1_bedingung():
    """Rest-Review Punkt 1: „Hochladen" bietet den Upload nach dem Rohschnitt nicht bedingungslos an, sondern mit der
    Bedingung aus Stufe 1, Schritt 7 (Begutachtung vor weiteren Stufen, die dann nur auf einer neuen Version laufen)."""
    hochladen = _flach(_abschnitt(_text(WORKFLOW), "### Hochladen"))
    assert "Nach Rohschnitt, Finalisieren und Feinschnitt den Upload anbieten" not in hochladen
    for needle in ("Rohschnitt", "begutachtet werden soll", "neuen Version", "nie ungefragt"):
        assert needle in hochladen, f"„Hochladen“: „{needle}“ fehlt"


def test_replay_kommentare_ein_lese_weg_und_stand_ohne_ueberschreiben():
    """Rest-Review Punkt 3: Kommentare je Video und Runde nur auf einem Weg lesen; den Stand nach der Chrome-Lesung
    mit `--nur-stand` prüfen — kein zweiter `kommentare`-Lauf per API, der kommentare.json/.md überschreibt."""
    replay = _abschnitt(_text(WORKFLOW), "## Review in Replay")
    assert "Je Video und Runde nur auf einem Weg" in _flach(_abschnitt(replay, "### Kommentare holen"))
    umsetzen = _flach(_abschnitt(replay, "### Umsetzen"))
    aufrufe = re.findall(r"kommentare --timeline[^`]*", umsetzen)
    assert aufrufe and all("--nur-stand" in a for a in aufrufe), aufrufe
    assert "--nur-stand" in _text(README)
    assert "ersetzt dann die API-Lesung" in _flach(_abschnitt(_text(WORKFLOW), "## Fehlerbilder"))
    zeile = next(l for l in _text(WORKFLOW).splitlines() if l.startswith("| Replay-Kommentare: `… nicht im offenen Projekt`"))
    assert "--nur-stand" in zeile, zeile                              # Chrome-Weg prüft keinen Stand


def test_replay_bau_readback_zuletzt_vor_dem_upload():
    """Rest-Review Punkt 4: In „Umsetzen" steht der Bau-Readback der neuen Version nach allen Änderungen (nach der
    Kantenprüfung) unmittelbar vor dem Hochladen — nicht direkt nach `SetName`."""
    wf = _text(WORKFLOW)
    umsetzen = _flach(_abschnitt(wf, "### Umsetzen"))
    assert "Nach jedem `SetName` sofort" not in umsetzen
    readback = umsetzen.index("autocut_readback.py")
    assert umsetzen.index("autocut_kanten.py") < readback < umsetzen.index("Hochladen ab Schritt 1")
    assert "nachfragen, ob er die neue Version" in umsetzen          # Handänderungen nie zum Bau-Stand machen
    assert "ohne Readback steht dort `null`" in umsetzen
    assert "letzten eigenen Änderung" in _flach(_abschnitt(wf, "### Bau-Readback"))   # gilt auch für den ersten Upload
    hochladen = _flach(_abschnitt(wf, "### Hochladen"))
    assert "Bau-Readback" in hochladen and "nachfragen" in hochladen   # auch beim ersten Upload (ohne SetName)


def test_replay_vorbedingung_rendern_dokumentiert():
    """Rest-Review Punkt 7: Vorschau-Schritt und Fehlerbilder nennen die Prüfung auf laufendes Rendern."""
    wf = _text(WORKFLOW)
    assert "IsRenderingInProgress" in _flach(_abschnitt(wf, "### Hochladen"))
    assert "| Replay: `Resolve rendert gerade`" in _flach(_abschnitt(wf, "## Fehlerbilder"))


def test_replay_plan_kopie_test_deckt_zusatzmessungen_ab():
    """Rest-Review Punkt 7: Plan Task 1 — die Zusatzmessungen aus Step 9 haben Zusagen in Step 1, Aufräumen in Step 10
    und je eine Zeile im Nachtrag-Muster von Step 11 (Frage = fett gesetzte Überschrift aus Step 9)."""
    plan = _text(REPLAY_PLAN)
    task = plan[plan.index("### Task 1:"):plan.index("### Task 2:")]
    messungen = re.findall(r"^- \*\*(.+?):\*\*", _plan_schritt(task, 9), flags=re.M)
    assert len(messungen) >= 6, messungen
    schritt1 = _flach(_plan_schritt(task, 1))
    assert "Step 9" in schritt1 and "Step 9" in _flach(_plan_schritt(task, 10))
    pflicht = schritt1[schritt1.index("(d)"):schritt1.index("(e)")]     # (a)–(d) sind Pflicht, (e)–(g) optional
    assert "Step 10" in pflicht, "Löschen von T und K braucht eine Pflicht-Zusage"
    muster = _flach(_plan_schritt(task, 11))
    for frage in messungen:
        assert f"| {frage} |" in muster, f"Step 11: Zeile für „{frage}“ fehlt"


def test_workflow_erklaert_die_bereichsauswahl():
    text = _text(WORKFLOW)
    for needle in ("stabile Bereiche", "abschnitte[].maengel", "stabil_quelle", "gerettet",
                   "bewegung_max", "stabil_min_s", "Punkt liegt in Bewegung"):
        assert needle in text, f"WORKFLOW-AutoCut.md: „{needle}“ fehlt"


def test_readme_nennt_die_bereichsauswahl():
    assert "stabile Bereiche" in _text(README)


def test_bereichsauswahl_nennt_die_ungeschnittenen_laeufe():
    """Task 8 (Schluss-Review I3/M1/M9): Stufe 2b speichert die ungeschnittenen Läufe je Clip und schneidet die Stücke
    ohne Mindestlänge; der Prüfer legt Stücke nur innerhalb eines Laufs zusammen; der kompakte Index gibt die Läufe
    je Clip aus."""
    stufe2b = _flach(_abschnitt(_text(WORKFLOW), "## Ablauf Stufe 2b"))
    for needle in ("stabil_quelle.laeufe", "ohne Mindestlänge je Stück"):
        assert needle in stufe2b, f"Stufe 2b: „{needle}“ fehlt"
    stufe3 = _flach(_abschnitt(_text(WORKFLOW), "## Ablauf Stufe 3 —"))
    for needle in ("ungeschnittenen Läufe", "desselben Laufs", "verschiedener Läufe nie", "nur clip-weit"):
        assert needle in stufe3, f"Stufe 3: „{needle}“ fehlt"
    assert "weder `stabil`" not in stufe3 and "`stabil_laeufe` leer aus" in stufe3      # beide stehen da, als []
    readme = _flach(_text(README))
    assert "`stabil` je Abschnitt" in readme and "`stabil_quelle` je Clip" in readme and "laeufe" in readme
    prompt = _flach(_text(PLACE_PROMPT))
    for needle in ("stabil_laeufe", "in EINEM Lauf", "verwendbar oder gerettet"):
        assert needle in prompt, f"place-broll.md: „{needle}“ fehlt"
    assert "die Messung widerspricht —" not in prompt       # passt nur zum Wackler (Schluss-Review M8)


def test_force_in_stufe_2_nennt_den_neuen_nachlauf():
    """Schluss-Review M2: `autocut_index_broll.py --force` schreibt frische Datensätze ohne die Felder aus Stufe 2b —
    der Nachlauf muss danach neu laufen und fragt die API erneut an. Weder der Workflow noch der Plan dürfen dafür
    „keine API-Kosten" versprechen."""
    stufe2 = _flach(_abschnitt(_text(WORKFLOW), "## Ablauf Stufe 2 —"))
    assert "autocut_index_sections.py" in stufe2 and "API" in stufe2
    probe = _flach(_abschnitt(_text(BEREICH_PLAN), "## Nach dem Plan: erste Probe an WLC"))
    assert "keine API-Kosten" not in probe and "--dry-run" in probe


def test_spec_bereichsauswahl_passt_zu_den_ungeschnittenen_laeufen():
    """Fix-Runde 1 zu Task 8: die maßgebliche Spec widerspricht dem umgesetzten Verhalten nicht mehr — sonst brächte ein
    späterer Task, der nach Abschnitt 3 arbeitet, den Filter je Stück zurück. Jede Berichtigung ist datiert, der Kopf
    nennt sie und den User-Entscheid zu Mängeln, die nur clip-weit stehen."""
    spec = _text(SPEC_BEREICH)
    kopf = _flach(spec[:spec.index("## Anlass")])
    for needle in ("Berichtigt 24.09.2026", "stabil_quelle.laeufe", "keine Mindestlänge je Stück", "desselben Laufs",
                   "nur clip-weit"):
        assert needle in kopf, f"Spec-Kopf: „{needle}“ fehlt"
    stufe2b = _flach(_abschnitt(spec, "## 3 —"))
    assert ", Schnitte unter `stabil_min_s` fallen weg." not in stufe2b
    for needle in ("ohne Mindestlänge je Stück", "config_hash, laeufe}", "berichtigt 24.09.2026, Task 8"):
        assert needle in stufe2b, f"Spec Abschnitt 3: „{needle}“ fehlt"
    kompakt = _flach(_abschnitt(spec, "## 4 —"))            # die Prompt-Regel wie in place-broll.md
    assert "darf ein Shot nur innerhalb von `stabil` liegen" not in kompakt
    for needle in ("in EINEM Lauf aus `stabil_laeufe`", "verwendbar oder gerettet",
                   "außer die Charge sperrt „Wackler\"", "berichtigt 24.09.2026, Task 8"):
        assert needle in kompakt, f"Spec Abschnitt 4: „{needle}“ fehlt"
    randfaelle = _flach(_abschnitt(spec, "## Fehler und Randfälle"))
    assert "wenn sie aneinandergrenzen (FX3_8641" not in randfaelle
    assert "zum selben gemessenen Lauf" in randfaelle and "berichtigt 24.09.2026, Task 8" in randfaelle
    probe = _flach(_abschnitt(spec, "## Erste Probe"))
    assert "ohne API-Kosten" not in probe and "--dry-run" in probe and "berichtigt 24.09.2026, Task 8" in probe


def test_doku_erklaert_die_kantenregel():
    """Spec 2026-09-25: Workflow, Prompt und README nennen die frame-genaue Kantenregel."""
    wf = _flach(_text(WORKFLOW))
    for needle in ("kante_s", "glatt_s", "verschiebung", "frame-genau", "Punkt liegt in Bewegung", "gleich lang passend ab"):
        assert needle in wf, f"WORKFLOW-AutoCut.md: „{needle}“ fehlt"
    assert "Schnittkanten in Bewegung** (Hinweis" in wf, "WORKFLOW-AutoCut.md nennt die Kanten nicht als Hinweis"
    for alt in ("bewegung_rand_s", "bewegung_spitze_faktor", "nicht als stabil gemessen"):
        assert alt not in wf, f"WORKFLOW-AutoCut.md nennt noch „{alt}“"
    prompt = _flach(_text(PLACE_PROMPT))
    for needle in ("Punkt liegt in Bewegung", "0,3 s", "frame-genau"):
        assert needle in prompt, f"place-broll.md: „{needle}“ fehlt"
    assert "nicht als stabil gemessen" not in prompt
    assert "Schnittkanten" in _flach(_text(README))
