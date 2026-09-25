"""Erzeugt die Fixtures bereiche-urteile.json, bereiche-wlc.json und bereiche-klebl.json (Spec 2026-09-25).

Einmalig von Hand laufen lassen, NICHT im Testlauf: die Clips liegen auf dem NAS (nur lesen), Auswahl und Urteile in
projects/ (NAS-Spiegel, nicht im Repo). Jeder Clip wird mit ``clip_messen()`` und der ausgelieferten Konfiguration
(defaults.yaml) neu gemessen — die Chargen bleiben unberührt. Gelesen wird aus dem HAUPTORDNER des Repos (Worktrees
haben kein projects/), geschrieben wird neben diese Datei.

    tools/autocut/venv/bin/python tools/autocut/tests/fixtures/gen_bereiche_fixture.py

Quellen:
  projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh/_intern/autocut/telemetrie.json  (Pfade)
  projects/WLC/Recruiting/2026-07 Erster Dreh/_intern/autocut/telemetrie.json                                  (Pfade)
  projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schwenks/_intern/{beispiele,urteile}{,2}.json
  projects/Klebl/Recruiting-Videos/2026-09 Dreh Edeka Baustelle 22.09/_intern/autocut/video-*/broll_build.json

Reihe und Fenster der 30 Urteile und der 32 Klebl-Shots werden auf den Bereich ± 3 s beschnitten (``t0_s``; die
Läufe im Bereich bleiben dieselben, solange der Rand über ``stabil_min_s`` liegt), die vier WLC-Clips bleiben
vollständig. Die MEK- und WLC-Aufnahmen lagen beim ersten Messen auf der SSD NIRO-SSD-03 — ohne sie gilt dieselbe
Datei auf dem NAS.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parents[1] / "src"))

from niro_autocut.charge import load_config  # noqa: E402
from niro_autocut.telemetrie import clip_messen  # noqa: E402


def studio_wurzel() -> Path:
    """Hauptordner des Repos. NICHT relativ zu dieser Datei bestimmen: in einem Worktree gibt es kein
    projects/ (CLAUDE.md, „Chargen-Daten nur im Hauptordner des Repos lesen und schreiben"). Die erste
    Zeile von `git worktree list --porcelain` nennt den Hauptordner, auch aus einem Worktree heraus."""
    aus = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=HIER,
                         capture_output=True, text=True, check=True).stdout
    return Path(aus.splitlines()[0].removeprefix("worktree "))


STUDIO = studio_wurzel()
MEK = STUDIO / "projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh/_intern/autocut/telemetrie.json"
WLC = STUDIO / "projects/WLC/Recruiting/2026-07 Erster Dreh/_intern/autocut/telemetrie.json"
KAL = STUDIO / "projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schwenks/_intern"
KLEBL = STUDIO / "projects/Klebl/Recruiting-Videos/2026-09 Dreh Edeka Baustelle 22.09/_intern/autocut"
KLEBL_VIDEOS = ("video-1-tiefbau", "video-2-hoch-und-fertigteilbau")
RAND_S = 3.0
FELDER = ("clip", "dauer_s", "fenster_s", "fenster", "ruhige_fenster", "config_hash", "haltung", "wackeln", "zooms",
          "verschiebung")
CFG = load_config(Path("/nirgendwo"))["telemetrie"]
NAS_KUNDEN = "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/"
UMLEITUNG = {"/Volumes/NIRO-SSD-03/01_Projekt-2xAds1xImagefilm_24.06.26/":
             NAS_KUNDEN + "Marien-Elisabeth-Kliniken Kassel gGmbH/02_Projekte/01_Projekt-2xAds1xImagefilm_24.06.26/",
             "/Volumes/NIRO-SSD-03/WLC Würth Logistik GmbH & CO KG/": NAS_KUNDEN + "WLC Würth Logistik GmbH & CO KG/"}

# Die Bereiche, die der User am 23.09. im Review genannt hat (Protokoll der WLC-Charge)
WLC_BEREICHE = {"FX3_8636": [[4.5, 7.5]], "FX3_8641": [[1.5, 4.0]], "FX3_8660": [[12.5, 15.5]],
                "FX3_8663": [[9.0, 12.0], [63.5, 66.5]]}


def _laden(p: Path) -> dict:
    if not p.is_file():
        raise SystemExit(f"{p} fehlt — Charge vom NAS holen (sh tools/studio_abgleich.sh --charge ...).")
    return {r["clip"]: r for r in json.loads(p.read_text(encoding="utf-8"))}


def _medienpfad(p: str) -> Path:
    if Path(p).exists():
        return Path(p)
    for von, nach in UMLEITUNG.items():
        if p.startswith(von) and Path(nach + p[len(von):]).exists():
            return Path(nach + p[len(von):])
    raise SystemExit(f"{p} nicht erreichbar — NAS gemountet?")


def _messen(p: str) -> dict:
    rec = clip_messen(_medienpfad(p), CFG)
    if rec.get("fehler") or not rec.get("verschiebung"):
        raise SystemExit(f"{p}: Messung ohne Reihe ({rec.get('fehler') or rec.get('quelle')})")
    print(f"  gemessen {Path(p).name}", flush=True)
    return rec


def _schlank(rec: dict, von_s: float | None = None, bis_s: float | None = None) -> dict:
    out = {k: rec.get(k) for k in FELDER}
    if von_s is not None:
        a, z = max(0.0, von_s - RAND_S), bis_s + RAND_S
        out["fenster"] = [f for f in out["fenster"] if a <= f[0] <= z]
        out["ruhige_fenster"] = [t for t in out["ruhige_fenster"] if a <= t <= z]
        v = out["verschiebung"]
        i, j = int(round(a * v["fps"])), int(round(z * v["fps"]))
        out["verschiebung"] = {**v, "t0_s": round(i / v["fps"], 2), "dx": v["dx"][i:j], "dy": v["dy"][i:j]}
    return out


def urteile() -> list[dict]:
    mek = _laden(MEK)
    raus = []
    for runde, suffix in ((1, ""), (2, "2")):
        beispiele = json.loads((KAL / f"beispiele{suffix}.json").read_text(encoding="utf-8"))
        urteil = json.loads((KAL / f"urteile{suffix}.json").read_text(encoding="utf-8"))
        for b in beispiele:
            u = urteil[str(b["nr"])]
            von_s = float(b["quelle_start_s"])
            raus.append({"nr": f"R{runde}#{b['nr']}",
                         "urteil": u if isinstance(u, str) else u["urteil"],
                         "anmerkung": "" if isinstance(u, str) else u.get("anmerkung", ""),
                         "von_s": von_s, "bis_s": von_s + 5.0,
                         "telemetrie": _schlank(_messen(mek[b["clip"]]["path"]), von_s, von_s + 5.0)})
    return raus


def wlc() -> list[dict]:
    tel = _laden(WLC)
    return [{"clip": c, "bereiche_user": b, "telemetrie": _schlank(_messen(tel[c]["path"]))}
            for c, b in WLC_BEREICHE.items()]


def klebl() -> list[dict]:
    """Die 32 gebauten B-Roll-Shots des Klebl-Nachtlaufs 24./25.09. (Anlass der Spec), Quellbereich wie gebaut."""
    raus, gemessen = [], {}
    for video in KLEBL_VIDEOS:
        bau = json.loads((KLEBL / video / "broll_build.json").read_text(encoding="utf-8"))
        for p in bau["placed"]:
            if p["clip"] not in gemessen:
                gemessen[p["clip"]] = _messen(p["clip"])
            von_s, bis_s = p["src_in_f"] / p["clip_fps"], p["src_out_f"] / p["clip_fps"]
            raus.append({"video": video, "rec_s": round(p["rec_in_f"] / 25.0, 2), "clip": p["name"],
                         "von_s": round(von_s, 3), "bis_s": round(bis_s, 3), "tempo": int(p["tempo"]),
                         "telemetrie": _schlank(gemessen[p["clip"]], von_s, bis_s)})
    return raus


def _schreiben(p: Path, daten: list[dict]) -> None:
    """JSON mit Einrückung, Zahlenlisten (Reihen, Bereiche) aber je in einer Zeile — sonst eine Zahl je Zeile."""
    text = json.dumps(daten, ensure_ascii=False, indent=1)
    text = re.sub(r"\[\s+([-0-9.,\s]+?)\s+\]", lambda m: "[" + re.sub(r"\s+", "", m.group(1)) + "]", text)
    p.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    for name, erzeugen in (("bereiche-urteile.json", urteile), ("bereiche-wlc.json", wlc),
                           ("bereiche-klebl.json", klebl)):
        print(name, flush=True)
        daten = erzeugen()
        p = HIER / name
        _schreiben(p, daten)
        print(f"{p.name}: {len(daten)} Einträge, {p.stat().st_size // 1024} KB")
