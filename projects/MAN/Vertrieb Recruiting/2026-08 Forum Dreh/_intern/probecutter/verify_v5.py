"""Verifikation der V5-Gesamtvideo-Zeilen gegen _intern/utterances.json.

Prüft pro geplanter Schnittplan-Zeile: Existiert das Zitat (Anfangs- und
End-Fragment) im angegebenen Quellclip innerhalb des Timecode-Fensters
(± Toleranz)? Quelle der Wahrheit: utterances.json (FX3 = Ton-Kamera).

Aufruf: python3 verify_v5.py   (aus _intern/probecutter/)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CHARGE = Path(__file__).resolve().parents[2]
UTT = CHARGE / "_intern" / "utterances.json"

TOL = 8.0  # Sekunden Toleranz um das Fenster (Plan-Timecodes sind mm:ss-gerundet)


def norm(s: str) -> str:
    s = s.lower()
    s = s.replace("victoria", "viktoria")  # ASR schreibt mal so, mal so
    s = re.sub(r"[^a-zäöüß0-9 ]", " ", s)
    s = re.sub(r"\b(äh|ähm|eh|ehm|hm)\b", " ", s)  # ASR-Füller ignorieren
    return re.sub(r"\s+", " ", s).strip()


def mmss(t: str) -> float:
    m, s = t.split(":")
    return int(m) * 60 + int(s)


# Zeilen des V5-Plans: (nr, datei, von, bis, start_fragment, end_fragment)
ROWS = [
    ("1 Hook", "FX3_0547.MP4", "03:57", "04:36",
     "Man sitzt mit sechsundzwanzig vor 'nem Kunden",
     "große Verantwortung, die man da trägt"),
    ("2a Vorstellung Roman", "FX3_0546.MP4", "00:31", "00:38",
     "mein Name ist Roman Retsch",
     "Region Allgäu und Bodensee"),
    ("2b Vorstellung Victoria", "FX3_0543.MP4", "01:03", "01:06",
     "Ich bin die Victoria Wader",
     "Truckverkäuferin bei der MAN"),
    ("2c Vorstellung Esther", "FX3_0545.MP4", "01:11", "01:22",
     "Mein Name ist Esther Ludewig",
     "bei der Firma MAN"),
    ("3 Schönste Produkte", "FX3_0546.MP4", "04:25", "04:38",
     "die schönsten Busse",
     "rundes Gesamtpaket"),
    ("4 Palette", "FX3_0544.MP4", "16:29", "16:35",
     "Wenn du bei der MAN als Verkäuferin anfängst",
     "Busse verkaufen"),
    ("5 Feuerwehr", "FX3_0546.MP4", "02:13", "02:42",
     "Am liebsten natürlich Feuerwehrfahrzeuge",
     "Lieblingsterrain"),
    ("6 Tagesablauf", "FX3_0543.MP4", "16:25", "17:20",
     "der typische Tagesablauf",
     "Beratungstermine an"),
    ("7 Büro vs Kunde", "FX3_0544.MP4", "10:00", "10:45",
     "meistens im Büro",
     "zu den Kunden hin"),
    ("8 Beziehungs-Zyklus", "FX3_0546.MP4", "10:05", "11:40",
     "eine Kommune kommt nicht",
     "halben Jahr"),
    ("9 Beißt keiner", "FX3_0544.MP4", "04:39", "05:59",
     "freuen sich die Kunden",
     "beißt keiner"),
    ("10 Lösungen", "FX3_0545.MP4", "21:31", "22:06",
     "kein Produkt mehr",
     "Beratungsleistung"),
    ("11 Teamsport", "FX3_0545.MP4", "07:15", "08:17",
     "Einzelkämpfer",
     "teilst du deine Erfolge"),
    ("12 Vicky", "FX3_0543.MP4", "12:03", "12:34",
     "mittlerweile ist es bei mir",
     "die verkauft LKWs"),
    ("13 Marke", "FX3_0545.MP4", "14:22", "15:04",
     "brennen für die Marke",
     "Lösung für"),
    ("14 Trainee-Programm", "FX3_0545.MP4", "02:45", "03:16",
     "klassisches Trainee-Programm",
     "wenn du's selber machst"),
    ("15 Tag 1", "FX3_0547.MP4", "00:41", "01:04",
     "am ersten Tag war ich",
     "Verkäufer im Büro"),
    ("16 Für jeden", "FX3_0545.MP4", "03:33", "04:00",
     "generell für jeden",
     "erfolgreich zu sein"),
    ("17 Milchsammler", "FX3_0547.MP4", "06:14", "06:50",
     "Auslieferung von einem Milchsammler",
     "am Ende des Tages"),
    ("18a Mut Victoria", "FX3_0544.MP4", "21:15", "21:33",
     "Sei mutig",
     "bleib dran"),
    ("18b Mut Esther", "FX3_0545.MP4", "24:02", "24:24",
     "einfach mal mutig sein",
     "ausprobieren"),
    ("19 CTA Löwen", "FX3_0546.MP4", "24:06", "24:17",
     "Team der Löwen",
     "freuen uns richtig auf dich"),
]


def main() -> None:
    data = json.loads(UTT.read_text(encoding="utf-8"))
    by_name = {d["name"]: d for d in data}
    fails = 0
    for nr, datei, von, bis, frag_a, frag_b in ROWS:
        clip = by_name.get(datei)
        if clip is None:
            print(f"FAIL {nr}: Datei {datei} nicht in utterances.json")
            fails += 1
            continue
        lo, hi = mmss(von) - TOL, mmss(bis) + TOL
        window = " ".join(
            u["text"] for u in clip["utterances"]
            if u["bis_s"] >= lo and u["von_s"] <= hi
        )
        w = norm(window)
        ok_a, ok_b = norm(frag_a) in w, norm(frag_b) in w
        if ok_a and ok_b:
            print(f"OK   {nr}  ({datei} {von}–{bis})")
        else:
            fails += 1
            print(f"FAIL {nr}  ({datei} {von}–{bis})  "
                  f"Anfang={'OK' if ok_a else 'FEHLT'} Ende={'OK' if ok_b else 'FEHLT'}")
            print(f"     Fenster: …{w[:220]}…")
    print(f"\n{len(ROWS) - fails}/{len(ROWS)} Zeilen verifiziert.")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
