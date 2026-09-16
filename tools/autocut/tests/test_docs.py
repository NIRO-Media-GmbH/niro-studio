"""Task 12 — Doku, Workflow, Trigger: Dateien vorhanden, alle CLI-Einstiege dokumentiert, genau eine Trigger-Zeile."""
from __future__ import annotations

from niro_autocut.charge import TOOL_ROOT

STUDIO_ROOT = TOOL_ROOT.parents[1]          # tools/autocut → tools → NIRO Studio
WORKFLOW = TOOL_ROOT / "WORKFLOW-AutoCut.md"
README = TOOL_ROOT / "README.md"
SETUP = TOOL_ROOT / "SETUP.md"
CLAUDE_MD = STUDIO_ROOT / "CLAUDE.md"
RESOLVE_WORKFLOW = STUDIO_ROOT / "tools" / "resolve" / "WORKFLOW-Resolve.md"

# CLI-Einstiege laut Spec Abschnitt 6 (alle mit venv/bin/python, Argument = Chargen-Ordner)
SPEC_SCRIPTS = ["autocut_prepare.py", "autocut_sync.py", "autocut_find_quote.py", "autocut_verify.py",
                "autocut_build.py", "autocut_export_xml.py", "autocut_index_broll.py",
                "autocut_place_broll.py", "autocut_read_timelines.py", "autocut_index_sections.py",
                "autocut_finalize.py", "resolve_probe_xml.py", "resolve_probe_api.py",
                "autocut_replay.py", "autocut_readback.py"]


def _text(p) -> str:
    assert p.is_file(), f"{p} fehlt"
    return p.read_text(encoding="utf-8")


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
    for needle in ("## Resolve-Regeln", "Cloud-Projektbibliothek", "Export/", ".mcp.json", "sieben Funktionen", "bei Abweichung nichts schreiben"):
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
