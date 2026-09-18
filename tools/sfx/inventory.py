"""SFX-Inventar: Soundeffekte auf dem NAS finden, prüfen, Dubletten zusammenführen.

Nur lesend. Braucht data/nas_scan.tsv (scan.py). Ergebnis: data/inventar.json
(ein Eintrag pro SFX mit bester Fassung und allen Fundstellen) und
data/ausgeschlossen.json (Gründe je Datei).

Nicht aufgenommen (User 16.09.2026): Musik (Musik-Library, Stems, Envato-Musik),
Sprache (Voiceover, Aufnahmen, KI-Stimmen), alles von ElevenLabs, die Adobe
Sound Library (bleibt in 03_SFX). Aufgenommen: Intros/Logos/Jingles, Atmos mit
Stimmengewirr, die AI-SFX aus 03_SFX.

    venv/bin/python inventory.py
"""
import collections
import json
import os
import re
import subprocess
import unicodedata
from concurrent.futures import ThreadPoolExecutor

from config import DATA, FORMAT_RANG, MUSIK_PLAN, NAS_ROOT

ADOBE = re.compile(r"/adobe sound library/", re.I)
ELEVENLABS = re.compile(r"eleven", re.I)
# ElevenLabs-Soundeffekt-Downloads: "11L-<Prompt>-<Zeitstempel>" bzw. "<Prompt 20 Zeichen>_#1-<Zeitstempel>"
ELEVENLABS_SFX = re.compile(r"^11L-|^\w{20}_#\d+-\d{13}$")
STEM = re.compile(r"/stems-zip-|/stems?/|_stem-\d|"
                  r" - (Drums|Percussion|Bass|Synths?|Strings|Keys|Piano|Guitars?|(Lead |Backing )?Vocals|Melody|Pads|Brass|FX)\.\w+$", re.I)
ENVATO = re.compile(r"/([a-z0-9-]+)-(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})-utc/", re.I)
MUSIKORDNER = re.compile(r"/\d*_?Musik/", re.I)
SONSTIGES = re.compile(r"/node_modules/|\.dra/MediaFiles|/DJI Audio Backup/|/05_Rotato - MockUp Tool/", re.I)
SPRACHE = re.compile(
    r"_Eleven_v3_|/[^/]*\bV(oice)? ?O(ver)?\b[^/]*/|/\d+_Voice|/Voice ?over|/Voice/|Voice Over|/07_Samples/|"
    r"_[A-Za-z0-9]{20}\.(wav|mp3)$|/DJI_\d+_\d{8}_\d{6}\.WAV$|/\d+ Mic|-esv2-|enhanced-v2|audio für adobe|Sprecher|"
    r"/04_Exportiert/|/\d{4}(\(\d\))?\.WAV$|Recordings von This is Marketing|/01_Footage/|Ai Fragen|AI Testimonial|"
    r"/ImageVoice/|/AI Generiert/|/\d+_AI Generiert/|/Interview",
    re.I)
AUFNAHME = re.compile(r"/[^/]*\.WAV$")  # Rekorder/Kameras: ".WAV" groß, ohne "Künstler - Titel"


def probe(p):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:format_tags:stream=codec_name,sample_rate,channels,bits_per_sample",
         "-of", "json", p], capture_output=True, text=True, timeout=120)
    d = json.loads(r.stdout or "{}")
    fmt = d.get("format", {})
    st = (d.get("streams") or [{}])[0]
    return {"dur": round(float(fmt.get("duration") or 0), 3), "tags": {k.lower(): v for k, v in (fmt.get("tags") or {}).items()},
            "codec": st.get("codec_name"), "rate": st.get("sample_rate"), "ch": st.get("channels"), "bits": st.get("bits_per_sample")}


def projekt_von(p):
    rel = unicodedata.normalize("NFC", os.path.relpath(p, NAS_ROOT / "01_Projekte"))
    teile = rel.split(os.sep)
    if teile[0] == "01_Kunden" and len(teile) > 3 and teile[2] == "02_Projekte":
        projekt = re.sub(r"^\d+_(Projekt[- ]?)?", "", teile[3]).strip()
        if projekt in ("Sonstiges", "NIRO Content", "Kunden Testimonials", "Werbeanzeigen") and len(teile) > 5:
            projekt += " / " + re.sub(r"^\d+_", "", teile[4]).strip()
        return f"{teile[1].strip()} / {projekt}"
    if teile[0] == "03_Vorlagen und Tools":
        return " / ".join(t for t in teile[:3] if not os.path.splitext(t)[1])
    return " / ".join(t for t in teile[:3] if not os.path.splitext(t)[1]).strip()


def stamm(pfad):
    """Dateiname ohne Endung, ohne Kopie-Zähler ("(1)"), NFC."""
    s = unicodedata.normalize("NFC", os.path.splitext(os.path.basename(pfad))[0])
    return re.sub(r"\s*\((\d+)\)\s*$", "", s).strip()


def normal(s):
    return re.sub(r"[\W_]+", " ", unicodedata.normalize("NFKC", s).lower()).strip()


def quelle_von(k):
    n, tags = k["nfc"], k["tags"]
    kommentar = " ".join(str(tags.get(x, "")) for x in ("comment", "copyright", "description", "synopsis")).lower()
    if "youtube.com" in kommentar or "youtu.be" in kommentar or re.search(r"sound effect \((hd|\d+)\)|sound effect$|y2mate", k["stamm"], re.I):
        return "YouTube-Download"
    if "artlist" in kommentar or re.search(r"SFO-\d|MASTERED", tags.get("title", "")):
        return "Artlist"
    if ENVATO.search(n):
        return "Envato Elements"
    if "/03_SFX/AI SFX/" in n or re.search(r"_AI\d{3}$", k["stamm"]):
        return "KI-generiert (03_SFX/AI SFX)"
    return ""


def main():
    musik = set()
    if MUSIK_PLAN.exists():
        musik = {unicodedata.normalize("NFC", f) for e in json.load(open(MUSIK_PLAN)) for f in e["fundstellen"]}

    raus = collections.Counter()
    ausgeschlossen = []
    kandidaten = []
    for line in open(DATA / "nas_scan.tsv", encoding="utf-8"):
        size, mtime, p = line.rstrip("\n").split("\t", 2)
        n = unicodedata.normalize("NFC", p)
        base = os.path.basename(n)
        grund = None
        if ADOBE.search(n):
            grund = "Adobe Sound Library"
        elif ELEVENLABS.search(n) or ELEVENLABS_SFX.match(os.path.splitext(base)[0]):
            grund = "ElevenLabs"
        elif n in musik:
            grund = "Musik (Musik-Library)"
        elif STEM.search(n) or (ENVATO.search(n) and MUSIKORDNER.search(n)):
            grund = "Musik (Stems/Envato-Musik)"
        elif SONSTIGES.search(n):
            grund = "Aufnahme/Vorlage/Programmdatei"
        elif SPRACHE.search(n) or (AUFNAHME.search(n) and " - " not in base):
            grund = "Sprache/Aufnahme"
        if grund:
            raus[grund] += 1
            ausgeschlossen.append({"path": p, "grund": grund})
        else:
            kandidaten.append({"path": p, "nfc": n, "size": int(size), "mtime": int(mtime)})

    cache_pfad = DATA / "probe_cache.json"
    cache = json.load(open(cache_pfad)) if cache_pfad.exists() else {}
    schluessel = lambda k: f"{k['path']}|{k['size']}|{k['mtime']}"
    offen = [k for k in kandidaten if schluessel(k) not in cache]
    with ThreadPoolExecutor(8) as ex:
        for k, info in zip(offen, ex.map(lambda k: probe(k["path"]), offen)):
            cache[schluessel(k)] = info
    json.dump(cache, open(cache_pfad, "w"), ensure_ascii=False)

    sfx = []
    for k in kandidaten:
        k.update(cache[schluessel(k)])
        k["ext"] = os.path.splitext(k["path"])[1].lower()
        k["stamm"] = stamm(k["path"])
        grund = None
        if "voice-memo-uuid" in k["tags"]:
            grund = "Sprache/Aufnahme"
        elif "adobe systems" in (k["tags"].get("artist", "") + k["tags"].get("copyright", "")).lower():
            grund = "Adobe Sound Library"
        elif k["dur"] <= 0:
            grund = "nicht lesbar"
        if grund:
            raus[grund] += 1
            ausgeschlossen.append({"path": k["path"], "grund": grund})
            continue
        k["quelle"] = quelle_von(k)
        sfx.append(k)

    # Dubletten: gleicher Name + Dauer auf 0,15 s gleich (auch WAV/MP3-Paare desselben SFX)
    nach_name = collections.defaultdict(list)
    for k in sfx:
        nach_name[normal(k["stamm"])].append(k)
    gruppen = {}
    for name, dateien in nach_name.items():
        cluster = []
        for k in sorted(dateien, key=lambda k: k["dur"]):
            if cluster and k["dur"] - cluster[-1][-1]["dur"] <= 0.15:
                cluster[-1].append(k)
            else:
                cluster.append([k])
        for c in cluster:
            gruppen[(name, round(c[0]["dur"], 1))] = c
    inventar = []
    for (name, dauer), fassungen in sorted(gruppen.items()):
        best = max(fassungen, key=lambda k: (FORMAT_RANG.get(k["ext"], 0), k["size"]))
        quelle = next((f["quelle"] for f in fassungen if f["quelle"]), "")
        inventar.append({
            "key": f"{name}|{dauer}", "stamm": best["stamm"], "quelle": quelle,
            "best": {x: best[x] for x in ("path", "ext", "size", "dur", "tags", "codec", "rate", "ch", "bits")},
            "fundstellen": sorted({f["path"] for f in fassungen}),
            "projekte": sorted({projekt_von(f["path"]) for f in fassungen}),
        })
    json.dump(inventar, open(DATA / "inventar.json", "w"), ensure_ascii=False, indent=1)
    json.dump({"zaehler": raus, "dateien": ausgeschlossen}, open(DATA / "ausgeschlossen.json", "w"), ensure_ascii=False, indent=1)
    print("ausgeschlossen:", dict(raus))
    print(f"{len(sfx)} SFX-Dateien -> {len(inventar)} eindeutige SFX ({sum(e['best']['size'] for e in inventar) / 1e9:.2f} GB); "
          f"Quellen: {dict(collections.Counter(e['quelle'] or 'unbekannt' for e in inventar))}")


if __name__ == "__main__":
    main()
