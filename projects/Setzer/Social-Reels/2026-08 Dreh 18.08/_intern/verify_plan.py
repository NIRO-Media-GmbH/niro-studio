"""Verifiziert den Cutter-Plan gegen die Transkripte.

Prüft für jede Ablauf-Zeile im Video-Plan:
 (a) das Zitat kommt so im Transkript des genannten Clips vor,
 (b) die genannten In/Out-Sekunden umschließen die Wortzeiten des Zitats,
 (c) der Out-Punkt liegt innerhalb der echten Clip-Länge (ffprobe),
 (d) es wird kein Clip aus "00 Discarded" zitiert.
"""
from __future__ import annotations

import glob
import json
import re
import subprocess
import unicodedata
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
PLAN = PROJECT / "Ergebnisse/O-Ton-Pläne/video-1-fleischkaese-vs-leberkaese.md"
ROH = Path("/Volumes/NIRO-SSD-03/Setzer/03_Dreh 2026.08.18/Rohmaterial iPhone")
FREI = ROH / "01 - Unterschied Fleischkäse vs. Leberkäse"

# Zeile: | 5a | ... | „Zitat" | Person · 01/IMG_4900.MOV · 0,20–5,10 | ...
ROW = re.compile(
    r"^\|\s*(?P<nr>[0-9]+[a-z]?)\s*\|[^|]*\|\s*(?P<ton>[^|]*)\|\s*(?P<quelle>[^|]*)\|"
)
SRC = re.compile(r"(?P<datei>IMG_\d+\.MOV)\s*·\s*(?P<von>[\d,]+)[–-](?P<bis>[\d,]+)")


QUOTES = "„“”‘’\"'"

# Bewusste Verschriftlichungen: links steht im Plan, rechts sagt der O-Ton.
NORMALISIERT = {"24 7": "vierundzwanzig sieben"}


def norm(s: str) -> str:
    # ß zuerst, sonst zerfaellt "außerhalb" in zwei Tokens und die
    # Wortfenster-Suche verschiebt sich.
    s = s.replace("ß", "ss").replace("ẞ", "ss")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
    for plan, oton in NORMALISIERT.items():
        s = s.replace(plan, oton)
    return s


def load_cache() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in glob.glob(str(PROJECT / "_intern/cache/*.scribe.json")):
        d = json.loads(Path(p).read_text())
        out.setdefault(d["source_file"], d)
    return out


def clip_len(name: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(FREI / name)],
        capture_output=True, text=True,
    )
    return float(r.stdout.strip())


def main() -> None:
    cache = load_cache()
    fehler, geprueft = [], 0
    for line in PLAN.read_text().splitlines():
        m = ROW.match(line)
        if not m:
            continue
        ton = m.group("ton").strip().strip(QUOTES).strip()
        s = SRC.search(m.group("quelle"))
        if not s:
            continue
        nr, datei = m.group("nr"), s.group("datei")
        von = float(s.group("von").replace(",", "."))
        bis = float(s.group("bis").replace(",", "."))
        geprueft += 1
        tag = f"#{nr} {datei}"

        if not (FREI / datei).exists():
            fehler.append(f"{tag}: Datei liegt NICHT im freigegebenen Ordner 01")
            continue

        d = cache.get(datei)
        if not d:
            fehler.append(f"{tag}: kein Transkript im Cache")
            continue

        # (a) Zitat wörtlich enthalten?
        if ton and ton != "—":
            if norm(ton) not in norm(d["text"]):
                fehler.append(f"{tag}: Zitat nicht im Transkript -> {ton!r}")
                continue
            # (b) Wortzeiten des Zitats innerhalb In/Out?
            worte = [w for w in d["words"] if norm(w["text"])]
            ziel = norm(ton).split()
            treffer = None
            for i in range(len(worte)):
                if norm(" ".join(w["text"] for w in worte[i:i + len(ziel)])) == " ".join(ziel):
                    treffer = worte[i:i + len(ziel)]
                    break
            if treffer:
                a, b = treffer[0]["start"], treffer[-1]["end"]
                if a < von - 0.02:
                    fehler.append(f"{tag}: In {von} liegt NACH Sprechbeginn {a:.2f}")
                if b > bis + 0.02:
                    fehler.append(f"{tag}: Out {bis} liegt VOR Sprechende {b:.2f}")
            else:
                fehler.append(f"{tag}: Wortfolge nicht am Stück gefunden (Zitat prüfen)")

        # (c) Out innerhalb der echten Clip-Länge?
        L = clip_len(datei)
        if bis > L + 0.01:
            fehler.append(f"{tag}: Out {bis} > Clip-Länge {L:.2f}")

        # (d) Sprecher-Reinheit
        sp = {w.get("speaker") for w in d["words"] if w.get("speaker")}
        if len(sp) > 1:
            fehler.append(f"{tag}: mehrere Sprecher im Clip: {sorted(sp)}")

    print(f"{geprueft} Ablauf-Zeilen mit Quelle geprüft.")
    if fehler:
        print(f"\n{len(fehler)} BEFUND(E):")
        for f in fehler:
            print("  -", f)
    else:
        print("Alles sauber: Zitate wörtlich, Timecodes umschließen die Sprache, "
              "keine Out-Punkte hinter Clip-Ende, keine Discarded-Quellen, "
              "je Clip genau ein Sprecher.")


if __name__ == "__main__":
    main()
