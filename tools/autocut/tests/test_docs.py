"""Task 12 — Doku, Workflow, Trigger: Dateien vorhanden, alle CLI-Einstiege dokumentiert, genau eine Trigger-Zeile."""
from __future__ import annotations

from niro_autocut.charge import TOOL_ROOT

STUDIO_ROOT = TOOL_ROOT.parents[1]          # tools/autocut → tools → NIRO Studio
WORKFLOW = TOOL_ROOT / "WORKFLOW-AutoCut.md"
README = TOOL_ROOT / "README.md"
SETUP = TOOL_ROOT / "SETUP.md"
CLAUDE_MD = STUDIO_ROOT / "CLAUDE.md"

# CLI-Einstiege laut Spec Abschnitt 6 (alle mit venv/bin/python, Argument = Chargen-Ordner)
SPEC_SCRIPTS = ["autocut_prepare.py", "autocut_sync.py", "autocut_find_quote.py", "autocut_verify.py",
                "autocut_build.py", "autocut_export_xml.py", "autocut_index_broll.py",
                "autocut_place_broll.py", "autocut_read_timelines.py", "autocut_index_sections.py",
                "autocut_finalize.py", "resolve_probe_xml.py"]


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
