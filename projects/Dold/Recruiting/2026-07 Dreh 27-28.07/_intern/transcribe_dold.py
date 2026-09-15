"""Interviews Dold Holzwerke (Dreh 27./28.07.2026) transkribieren.

Ton-Kamera = FX3 (David, 2026-08-13). a7MK4 = Kontext-Kamera (Raum-Mikro,
hört den Interviewer besser) — nie als Tonquelle für Zitate/Timecodes.

Aufruf:  venv/bin/python "<Charge>/_intern/transcribe_dold.py" [--nur-ton]
"""
from __future__ import annotations

import json
import os
import sys
import unicodedata
from pathlib import Path

TOOL = Path("/Users/sergio/NIRO Studio/tools/transcribe")
sys.path.insert(0, str(TOOL / "src"))

from niro_transcribe.cache import TranscriptCache  # noqa: E402
from niro_transcribe.footage.discover import Clip  # noqa: E402
from niro_transcribe.footage.transcribe_clips import clip_fingerprint, transcribe_clip  # noqa: E402

CHARGE = Path(__file__).resolve().parent.parent
INTERN = CHARGE / "_intern"
NAS = Path(
    "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/Dold Holzwerke GmbH/"
    "02_Projekte/04_Projekt-27-28.07.26/03_Medien/01_Footage/Sortiert/Interviews"
)

# Ordner -> (Person, Rolle laut Ordner/Sheet, Bereich)
PERSONEN = {
    "Interview_Abduhamed_Biokraftwerk": ("Abduhamed", "Bioenergie", "Biokraftwerk"),
    "Interview_Ahmet_Biokraftwerk": ("Ahmet", "Bioenergie", "Biokraftwerk"),
    "Interview_Bernd_Produktionsleiter": ("Bernd Faller", "Produktionsleiter", "MHP"),
    "Interview_David_Hobelwerk": ("David Ruch", "Anlagenführer Hobelwerk", "Hobelwerk"),
    "Interview_Dominik_Betriebselektriker": ("Dominik", "Betriebselektriker", "Elektro"),
    "Interview_Georg_Betriebselektriker Abteilungsleiter": (
        "Georg Faller", "Abteilungsleiter Betriebselektrik", "Elektro"),
    "Interview_Gnaju_Schleiferei": ("Gnaju", "Schleiferei", "Schleifraum"),
    "Interview_Kai_Einteiler Rundholzplatz": ("Kai", "Einteiler Rundholzplatz", "RHP"),
    "Interview_Kevin_Biokraftwerk": ("Kevin", "Bioenergie", "Biokraftwerk"),
    "Interview_Lars_Produktionsleitung": ("Lars Loyal", "Produktionsleitung", "MHP"),
    "Interview_Nikolaus_Geschäftsführer": ("Nikolaus Faller", "Geschäftsführer", "Alle Werke"),
    "Interview_Sebastion_Industriemeister": ("Sebastian Tost", "Industriemeister", "Trocknung"),
    "Interview_Thomas_Baggerfahrer": ("Thomas Frey", "Baggerfahrer", "RHP"),
}


def kamera_rolle(name: str) -> str:
    return "ton" if name.startswith("FX3") else "kontext"


def api_key_lesen() -> str:
    for zeile in (TOOL / ".env").read_text(encoding="utf-8").splitlines():
        zeile = zeile.strip()
        if zeile.startswith("ELEVENLABS_API_KEY="):
            return zeile.split("=", 1)[1].strip().strip("'\"")
    raise SystemExit("ELEVENLABS_API_KEY fehlt in tools/transcribe/.env")


def main() -> None:
    nur_ton = "--nur-ton" in sys.argv
    api_key = os.environ.get("ELEVENLABS_API_KEY") or api_key_lesen()
    cache = TranscriptCache(INTERN / "cache")
    work = INTERN / "work"

    index_path = INTERN / "transcripts_index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    erledigt = {r["name"] for r in index if r.get("ok")}

    aufgaben = []
    for ordner_pfad in sorted(NAS.iterdir()):
        # macOS liefert Ordnernamen teils NFD-zerlegt ("Gescha¨ftsfu¨hrer") — normalisieren,
        # sonst greift der PERSONEN-Lookup nicht und der Ordner faellt still raus.
        ordner = unicodedata.normalize("NFC", ordner_pfad.name)
        if not ordner_pfad.is_dir() or ordner not in PERSONEN:
            continue
        for video in sorted(ordner_pfad.glob("*.MP4")):
            rolle = kamera_rolle(video.name)
            if nur_ton and rolle != "ton":
                continue
            aufgaben.append((ordner, video, rolle))

    for i, (ordner, video, rolle) in enumerate(aufgaben, 1):
        name = f"{ordner}/{video.name}"
        if name in erledigt:
            print(f"[{i}/{len(aufgaben)}] übersprungen (Cache): {name}", flush=True)
            continue
        person, funktion, bereich = PERSONEN[ordner]
        print(f"[{i}/{len(aufgaben)}] {name} ({rolle})", flush=True)
        rec = {
            "name": name, "ordner": ordner, "datei": video.name,
            "kamera_rolle": rolle, "person": person, "funktion": funktion,
            "standort": bereich, "kategorie": "interview",
            "fingerprint": clip_fingerprint(video),
        }
        try:
            t = transcribe_clip(
                Clip(path=video, camera=video.name.split("_")[0], sidecar=None),
                cache=cache, api_key=api_key, work_dir=work, diarize=True,
            )
            rec.update(ok=True, n_words=len(t.words), duration_s=round(t.duration(), 1))
            wav = work / f"{video.stem}.wav"
            wav.unlink(missing_ok=True)
        except Exception as exc:  # noqa: BLE001
            rec.update(ok=False, n_words=0, fehler=f"{type(exc).__name__}: {exc}")
            print(f"    FEHLER: {rec['fehler']}", flush=True)
        index = [r for r in index if r["name"] != name] + [rec]
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    ok = sum(1 for r in index if r.get("ok"))
    print(f"\nFertig: {ok}/{len(index)} Clips transkribiert.")


if __name__ == "__main__":
    main()
