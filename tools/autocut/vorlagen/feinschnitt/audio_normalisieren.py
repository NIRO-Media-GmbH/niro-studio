"""Vorlage (Stand 15.09.2026): Sprachspur A1 der eigenen Timeline normalisieren (True Peak je Clip) + Voice Isolation.

Aufruf: tools/autocut/venv/bin/python _intern/audio_normalisieren.py              → Probelauf: nur Projekt, Timeline, Zustand von A1 lesen
        tools/autocut/venv/bin/python _intern/audio_normalisieren.py --ausfuehren  → normalisieren, Voice Isolation, Gegenmessung
        (Abweichung vom Original: dort schrieb der Aufruf ohne Flag sofort, --lesen war der Probelauf.)

Ziel:   A1 (Ton der Ton-Kamera, AutoCut-Spurname „FX3 Ton") der roh-Timeline aus _intern/autocut/build.json
        (eigene Timeline dieser Session, per Unique-ID), Projekt PROJEKT.
Regel:  True Peak −3 dBTP je Clip, unabhängig (AutoCut-Feedback 04.09.2026); in Resolve 21.1 per NormalizeAudioLevel
        (Live-Probe 09.09.: trifft ffmpeg auf ±0,1 dB). Voice Isolation auf der Spur A1 (User 15.09.2026); ein schon
        gesetzter Betrag bleibt, sonst VI_STANDARD.
Schutz: Projektname = Freigabe, Modus „True Peak" muss angeboten werden. Lehnt NormalizeAudioLevel auf der nicht aktiven
        Timeline ab, wird sie kurz aktiviert und danach die Timeline des Users zurückgesetzt („timeline_kurz_aktiviert").
Prüfung: AudioVolume je Clip gegen −3 − True Peak (ffmpeg ebur128, Original-Ton im Clipbereich), Voice-Isolation-State;
        Abweichungen über 0,5 dB werden gezählt.
Schreibt _intern/autocut/audio.json.

Nicht auf hochgeladene Timelines anwenden (`_intern/replay/uploads.json`) — dort neue Version bauen.

Herkunft: Taxodia-Charge, _intern/audio_normalisieren.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402

CH = Path(__file__).resolve().parent.parent
AC = CH / "_intern" / "autocut"

# ── ANPASSEN je Charge ─────────────────────────────
PROJEKT = "<Resolve-Projekt>"  # Name des offenen Resolve-Projekts = Schreibfreigabe des Users in dieser Session
ZIEL_DBTP = -3.0  # Ziel True Peak je Clip [dBTP], Modus Independent (AutoCut-Feedback 04.09.2026); Standard (15.09.)
FPS = 25.0  # Timeline-Bildrate [fps] für Left-Offset/Dauer → Sekunden der ffmpeg-Messung; Standard (15.09.)
VI_STANDARD = 50  # Voice-Isolation-Betrag, wenn auf A1 noch keiner gesetzt ist (User 15.09.2026); Standard (15.09.)
# ── Ende ANPASSEN ──────────────────────────────────


def true_peak(datei: str, start_s: float, dauer_s: float) -> float | None:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{start_s:.3f}", "-t", f"{dauer_s:.3f}", "-i", datei,
                        "-map", "0:a:0", "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"True peak:\s*\n\s*Peak:\s*(-?[\d.]+|-inf)\s*dBFS", r.stderr)
    return None if not m or m.group(1) == "-inf" else float(m.group(1))


def main() -> None:
    build = json.loads((AC / "build.json").read_text())
    r = RA.connect()
    pm = r.GetProjectManager()
    proj = pm.GetCurrentProject()
    print(f"Projekt: {proj.GetName()}")
    if proj.GetName() != PROJEKT:
        raise SystemExit(f"Offenes Projekt ≠ Freigabe '{PROJEKT}' — nichts geschrieben.")
    tl = next((proj.GetTimelineByIndex(i) for i in range(1, proj.GetTimelineCount() + 1)
               if proj.GetTimelineByIndex(i).GetUniqueId() == build["timeline_id"]), None)
    if tl is None:
        raise SystemExit("Ziel-Timeline nicht gefunden — nichts geschrieben.")
    print(f"Timeline: {tl.GetName()} (aktiv: {proj.GetCurrentTimeline().GetName()})")
    items = tl.GetItemListInTrack("audio", 1) or []
    modi = list(tl.GetNormalizeAudioModes() or [])
    vi_vorher = tl.GetVoiceIsolationState(1)
    vol_vorher = [it.GetProperty("AudioVolume") for it in items]
    print(f"A1: {len(items)} Clips, Modi {modi}, Voice Isolation vorher {vi_vorher}, AudioVolume vorher {sorted(set(vol_vorher))}")
    if "--ausfuehren" not in sys.argv:
        print("Probelauf — nichts geschrieben. Schreiben mit --ausfuehren.")
        return
    if "True Peak" not in modi:
        raise SystemExit("Modus 'True Peak' fehlt — nichts geschrieben.")
    opts = {"normalizationMode": "True Peak", "targetLevel": ZIEL_DBTP, "setLevelMode": r.NORMALIZE_AUDIO_SET_LEVEL_INDEPENDENT}
    ok_norm = bool(tl.NormalizeAudioLevel(items, opts))
    aktiviert = False
    if not ok_norm:  # Fallback: auf der aktiven Timeline erneut versuchen, danach die Timeline des Users zurück
        user_tl = proj.GetCurrentTimeline()
        proj.SetCurrentTimeline(tl)
        aktiviert = True
        try:
            ok_norm = bool(tl.NormalizeAudioLevel(items, opts))
        finally:
            proj.SetCurrentTimeline(user_tl)
    amount = int((vi_vorher or {}).get("amount") or 0) or VI_STANDARD
    ok_vi = bool(tl.SetVoiceIsolationState(1, {"isEnabled": True, "amount": amount}))
    vi_nachher = tl.GetVoiceIsolationState(1)
    gespeichert = bool(pm.SaveProject())
    zeilen, abw = [], []
    start = int(tl.GetStartFrame())
    for it in items:
        mpi = it.GetMediaPoolItem()
        datei = unicodedata.normalize("NFC", mpi.GetClipProperty("File Path"))
        left, dur = int(it.GetLeftOffset()), int(it.GetDuration())
        tp = true_peak(datei, left / FPS, dur / FPS)
        ist = it.GetProperty("AudioVolume")
        soll = None if tp is None else round(ZIEL_DBTP - tp, 2)
        diff = None if soll is None or ist is None else round(float(ist) - soll, 2)
        zeilen.append({"clip": Path(datei).stem, "rec_in_f": int(it.GetStart()) - start, "dauer_f": dur,
                       "true_peak_dbfs": tp, "soll_gain_db": soll, "ist_audio_volume_db": ist, "diff_db": diff})
        if diff is None or abs(diff) > 0.5:
            abw.append(zeilen[-1])
    cur = proj.GetCurrentTimeline()
    out = {"projekt": proj.GetName(), "timeline": tl.GetName(), "normalize_ok": ok_norm, "timeline_kurz_aktiviert": aktiviert,
           "optionen": {"normalizationMode": "True Peak", "targetLevel": ZIEL_DBTP, "setLevelMode": "INDEPENDENT"},
           "voice_isolation_ok": ok_vi, "voice_isolation_vorher": vi_vorher, "voice_isolation_nachher": vi_nachher,
           "gespeichert": gespeichert, "aktive_timeline": cur.GetName() if cur else None,
           "clips": zeilen, "abweichungen_ueber_0_5_db": len(abw)}
    (AC / "audio.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "clips"}, ensure_ascii=False))
    for z in zeilen:
        print(f"  {z['clip']} @{z['rec_in_f']:>5}  TP {z['true_peak_dbfs']} dBFS  soll {z['soll_gain_db']:+} dB  ist {z['ist_audio_volume_db']}  diff {z['diff_db']}")


if __name__ == "__main__":
    main()
