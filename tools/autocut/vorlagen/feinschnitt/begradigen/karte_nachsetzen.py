"""Vorlage (Stand 15.09.2026): Offene Nachbesserung aus nachbesserung.json setzen, sobald Resolve Schreibzugriffe wieder annimmt.

Aufruf (im Hintergrund, nur mit Wissen des Users): tools/autocut/venv/bin/python _intern/begradigen/karte_nachsetzen.py
Alle 30 s ein Versuch, höchstens 30 Versuche (15 min). Nur das eine a7-Stück aus nachbesserung.json ("a7_stueck": start,
vorher, neu) auf V2 der Timeline TIMELINE. Je Versuch: Projekt gegen Freigabe PROJEKT prüfen, Item am Start suchen, aktuelle
Transform-Werte müssen noch den Vorher-Werten entsprechen (sonst von Hand geändert → nichts setzen), SetProperties,
Readback, speichern; bei Erfolg kopf_final.json (v2-Eintrag: neu + Hinweis) und nachbesserung.json (a7_gesetzt, hinweis)
fortschreiben.
Exit-Codes: 0 gesetzt · 1 nach 30 Versuchen weiter abgelehnt · 2 Projekt nicht offen/freigegeben · 3 Stück nicht mehr da ·
4 Transform inzwischen von Hand geändert.
Befund (Resolve 21.1, 15.09.): Resolve lehnte minutenlang jede Item-Schreibaktion ab (SetProperty/SetProperties = False auf
allen Items, auch deaktivierten, ohne Wiedergabe und ohne Spursperre; im Fenster war ein Clip im Source-Viewer/Inspector
geöffnet). Der 5. Versuch (nach ≈ 2 min) ging durch. Während des Laufs meldete der User, die Timeline sei nicht bedienbar
(kurz darauf ging es wieder); parallel waren weitere Scripting-Sessions verbunden, Ursache ungeklärt → bei Bedienproblemen
den Lauf sofort stoppen (pkill -f karte_nachsetzen.py) und nichts als gesetzt melden ohne True + Readback.
Herkunft: Taxodia-Charge, _intern/begradigen/karte_nachsetzen.py
"""
import json
import sys
import time
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402

HIER = Path(__file__).resolve().parent

# ── ANPASSEN je Charge ─────────────────────────────
PROJEKT = "<Resolve-Projekt>"  # in dieser Session freigegebenes Resolve-Projekt (Name exakt wie in Resolve)
TIMELINE = "<Timeline-Name>"  # Feinschnitt-Timeline (wie kopf_angleichen.TIMELINE)
# ── Ende ANPASSEN ──────────────────────────────────

K = ("RotationAngle", "Pitch", "Yaw", "ZoomX", "ZoomY", "Pan", "Tilt")


def main() -> None:
    nb = json.loads((HIER / "nachbesserung.json").read_text())
    neu, vorher = nb["a7_stueck"]["neu"], nb["a7_stueck"]["vorher"]
    stueck = nb["a7_stueck"]["start"]
    for versuch in range(30):
        r = RA.connect(); pm = r.GetProjectManager(); p = pm.GetCurrentProject()
        if p is None or p.GetName() != PROJEKT:
            print("Projekt nicht offen/freigegeben — Abbruch"); sys.exit(2)
        tl = next(t for t in (p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)) if t and t.GetName() == TIMELINE)
        s = tl.GetStartFrame()
        x = next((i for i in tl.GetItemListInTrack("video", 2) if i.GetStart() - s == stueck), None)
        if x is None:
            print(f"a7-Stück {stueck} nicht mehr da (vom User geändert) — nichts gesetzt"); sys.exit(3)
        jetzt = {k: float(x.GetProperty(k)) for k in K}
        if any(abs(jetzt[k] - vorher[k]) > 1e-3 * max(1, abs(vorher[k])) for k in K):
            print("Transform inzwischen von Hand geändert — nichts gesetzt:", jetzt); sys.exit(4)
        if x.SetProperties({k: float(neu[k]) for k in K}):
            rb = {k: float(x.GetProperty(k)) for k in K}
            ok = all(abs(rb[k] - neu[k]) <= 1e-3 * max(1, abs(neu[k])) for k in K)
            print(f"Versuch {versuch + 1}: gesetzt, Readback {ok}, gespeichert {pm.SaveProject()}", rb)
            if ok:
                kf = json.loads((HIER / "kopf_final.json").read_text())
                for e in kf["v2"]:
                    if e["start"] == stueck:
                        e["neu"] = neu; e["nachbesserung"] = f"Kopf {nb['a7_stueck']['hoeher_px_4k']} px höher wegen Grafik-Karte (nachgesetzt)"
                (HIER / "kopf_final.json").write_text(json.dumps(kf, ensure_ascii=False, indent=1), encoding="utf-8")
                nb["a7_gesetzt"] = True; nb["hinweis"] = f"nachgesetzt nach {versuch + 1} Versuchen"
                (HIER / "nachbesserung.json").write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
                sys.exit(0)
        print(f"Versuch {versuch + 1}: Resolve lehnt ab", flush=True)
        time.sleep(30)
    sys.exit(1)


if __name__ == "__main__":
    main()
