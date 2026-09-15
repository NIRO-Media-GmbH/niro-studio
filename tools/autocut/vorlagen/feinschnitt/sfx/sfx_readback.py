"""Vorlage (Stand 15.09.2026): Readback der eingesetzten SFX gegen sfx_plan.json — nur lesen, nichts in Resolve schreiben.

Aufruf: tools/autocut/venv/bin/python _intern/sfx/sfx_readback.py
Liest sfx_plan.json, sfx_einsatz.json (versatz verschobener Grafik-Clips, falls vorhanden) und die Timeline TIMELINE aus
sfx_einsetzen.py im Projekt feinschnitt_bauen.PROJEKT (Abbruch bei anderem Projekt oder fehlender Timeline).
Prüft je Platzierung (Schlüssel Spur + Start = rec_frame + versatz des Elements): vorhanden, Dauer = dauer_frames,
Left-Offset = round(src_in_s · 25), AudioVolume = gain_db (± TOLERANZ_DB), Clipname = sfx_name. Dazu:
  - je A4/A5-Clip, ob er wirklich mit einem V4-Clip verknüpft ist (GetLinkedItems) — ohne Link sind erwartbar, wenn mehrere SFX eines
    Elements auf derselben Spur liegen (Resolve: je Link-Gruppe ein Clip pro Spur, Messung 15.09.)
  - Spurstatus A4/A5: Name, aktiviert, gesperrt (GetIsTrackEnabled ist nur auf der aktiven Timeline aussagekräftig), Anzahl Tonspuren,
    Timeline-Ende. Die Bus-Zuweisung ist per API nicht lesbar → ob die Spuren klingen, zeigt nur sfx_ton_render.py.
Pegel, die der User oder ein späteres Skript geändert hat, erscheinen als Abweichung (gewollt: Plan nachziehen oder bestätigen).
Schreibt sfx_readback.json: projekt, timeline, aktive_timeline, sfx_in_timeline, plan, abweichungen [fehlt | Ist/Soll], ohne_grafik_link,
spuren, audio_spuren, ende.
Herkunft: Taxodia-Charge, Session-Scratchpad sfx_readback.py (+ Link-Prüfung aus nachbesserung2.py, Spurstatus aus sfx_technik.py)
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402

# ── ANPASSEN je Charge ─────────────────────────────
# (keine eigenen Werte: Projekt aus feinschnitt_bauen.PROJEKT, Timeline aus sfx_einsetzen.TIMELINE)
# ── Ende ANPASSEN ──────────────────────────────────

sys.dont_write_bytecode = True
HIER = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("se", HIER / "sfx_einsetzen.py")
se = importlib.util.module_from_spec(spec)
spec.loader.exec_module(se)
fb = se.fb
TOLERANZ_DB = 0.11  # Standard (15.09.): erlaubte Abweichung AudioVolume ↔ gain_db (Readback auf 0,1 dB gerundet)


def main() -> None:
    plan = json.loads((HIER / "sfx_plan.json").read_text())
    platz = plan["platzierungen"] if isinstance(plan, dict) else plan
    einsatz = HIER / "sfx_einsatz.json"
    versatz = json.loads(einsatz.read_text()).get("versatz", {}) if einsatz.exists() else {}
    r = RA.connect()
    p = r.GetProjectManager().GetCurrentProject()
    if p is None or p.GetName() != fb.PROJEKT:
        raise SystemExit(f"Offenes Projekt '{p.GetName() if p else None}' ≠ Freigabe '{fb.PROJEKT}' — nichts gelesen.")
    tl = next((t for t in (p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)) if t and t.GetName() == se.TIMELINE), None)
    if tl is None:
        raise SystemExit(f"Timeline '{se.TIMELINE}' nicht gefunden (sfx_einsetzen.py, ANPASSEN-Block).")
    s = tl.GetStartFrame()
    v4 = {x.GetUniqueId() for x in (tl.GetItemListInTrack("video", 4) or [])}
    ist, ohne_link = {}, []
    for idx, spur in ((4, "A4"), (5, "A5")):
        for x in tl.GetItemListInTrack("audio", idx) or []:
            links = x.GetLinkedItems() or []
            ist[(spur, x.GetStart() - s)] = (x.GetDuration(), round(x.GetLeftOffset()), round(float(x.GetProperty("AudioVolume")), 1),
                                             Path(x.GetName()).name, len(links))
            if not any(l.GetUniqueId() in v4 for l in links):
                ohne_link.append(f"{spur} @{x.GetStart() - s} {x.GetName()}")
    fehler = []
    for e in platz:
        k = (e["spur"], e["rec_frame"] + int(versatz.get(e["element"], 0)))
        if k not in ist:
            fehler.append(("fehlt", k))
            continue
        d, left, vol, name, links = ist[k]
        if d != e["dauer_frames"] or left != round(e["src_in_s"] * 25) or abs(vol - e["gain_db"]) > TOLERANZ_DB or name != e["sfx_name"]:
            fehler.append((k, (d, left, vol, name), (e["dauer_frames"], round(e["src_in_s"] * 25), e["gain_db"], e["sfx_name"])))
    aktiv = p.GetCurrentTimeline()
    spuren = {f"A{i}": {"name": tl.GetTrackName("audio", i), "aktiviert": tl.GetIsTrackEnabled("audio", i),
                        "gesperrt": tl.GetIsTrackLocked("audio", i)} for i in (4, 5) if i <= int(tl.GetTrackCount("audio"))}
    out = {"projekt": p.GetName(), "timeline": se.TIMELINE, "aktive_timeline": aktiv.GetName() if aktiv else None,
           "sfx_in_timeline": len(ist), "plan": len(platz), "abweichungen": fehler,
           "ohne_grafik_link": ohne_link, "spuren": spuren, "audio_spuren": tl.GetTrackCount("audio"), "ende": tl.GetEndFrame() - s}
    (HIER / "sfx_readback.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("SFX im Timeline:", len(ist), "| Plan:", len(platz), "| Abweichungen:", len(fehler), fehler[:5],
          "| mit Grafik verknüpft:", len(ist) - len(ohne_link), "von", len(ist))
    print("Spuren:", spuren, "| Audio-Spuren:", tl.GetTrackCount("audio"), "| Ende:", tl.GetEndFrame() - s,
          "| aktiv:", out["aktive_timeline"], "(Spur-aktiviert nur für die aktive Timeline verlässlich)")


if __name__ == "__main__":
    main()
