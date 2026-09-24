"""Erzeugt die Fixtures bereiche-urteile.json und bereiche-wlc.json aus den Chargen-Daten.

Einmalig von Hand laufen lassen, NICHT im Testlauf: die Quellen liegen in projects/ und damit nicht im Repo
(NAS-Spiegel). Die erzeugten Dateien werden committet — sie sind die Testgrundlage. Gelesen wird aus dem
HAUPTORDNER des Repos (Worktrees haben kein projects/), geschrieben wird neben diese Datei.

    python3 tools/autocut/tests/fixtures/gen_bereiche_fixture.py

Quellen:
  projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh/_intern/autocut/telemetrie.json
  projects/WLC/Recruiting/2026-07 Erster Dreh/_intern/autocut/telemetrie.json
  projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schwenks/_intern/{beispiele,urteile}{,2}.json

Die Fenster-Reihen der 30 Urteile werden auf den Bereich ± 10 s beschnitten (halbiert die Dateigröße;
an allen 30 Beispielen geprüft: identische Kandidaten wie mit der vollen Reihe). Die vier WLC-Clips
bleiben vollständig — dort werden Kandidaten über den ganzen Clip geprüft.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

HIER = Path(__file__).resolve().parent


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
RAND_S = 10.0
FELDER = ("clip", "dauer_s", "fenster_s", "fenster", "ruhige_fenster", "config_hash", "haltung", "wackeln")

# Die Bereiche, die der User am 23.09. im Review genannt hat (Protokoll der WLC-Charge)
WLC_BEREICHE = {"FX3_8636": [[4.5, 7.5]], "FX3_8641": [[1.5, 4.0]], "FX3_8660": [[12.5, 15.5]],
                "FX3_8663": [[9.0, 12.0], [63.5, 66.5]]}


def _laden(p: Path) -> dict:
    if not p.is_file():
        raise SystemExit(f"{p} fehlt — Charge vom NAS holen (sh tools/studio_abgleich.sh --charge ...).")
    return {r["clip"]: r for r in json.loads(p.read_text(encoding="utf-8"))}


def _schlank(rec: dict, von_s: float | None = None, bis_s: float | None = None) -> dict:
    out = {k: rec.get(k) for k in FELDER}
    if von_s is not None:
        a, z = von_s - RAND_S, bis_s + RAND_S
        out["fenster"] = [f for f in out["fenster"] if a <= f[0] <= z]
        out["ruhige_fenster"] = [t for t in out["ruhige_fenster"] if a <= t <= z]
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
                         "telemetrie": _schlank(mek[b["clip"]], von_s, von_s + 5.0)})
    return raus


def wlc() -> list[dict]:
    tel = _laden(WLC)
    return [{"clip": c, "bereiche_user": b, "telemetrie": _schlank(tel[c])} for c, b in WLC_BEREICHE.items()]


if __name__ == "__main__":
    for name, daten in (("bereiche-urteile.json", urteile()), ("bereiche-wlc.json", wlc())):
        p = HIER / name
        p.write_text(json.dumps(daten, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{p.name}: {len(daten)} Einträge, {p.stat().st_size // 1024} KB")
