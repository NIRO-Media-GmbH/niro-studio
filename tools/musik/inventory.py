"""Inventar: Songs auf dem NAS finden, prüfen, Dubletten zusammenführen.

Nur lesend. Ergebnis: data/inventar.json (ein Eintrag pro Song/Version mit
bester Fassung und allen Fundstellen) plus data/ausgeschlossen.json.

    venv/bin/python inventory.py              # NAS neu scannen
    venv/bin/python inventory.py --scan-tsv X # vorhandenen Scan (Größe\tmtime\t./Pfad) nutzen
"""
import argparse
import collections
import json
import os
import re
import subprocess
import unicodedata
from concurrent.futures import ThreadPoolExecutor

from config import AUDIO_EXT, DATA, FORMAT_RANG, NAS_ROOT

# --- Pfade, die sicher keine Musik enthalten -------------------------------
SFX_ORDNER = re.compile(
    r"/03_Vorlagen und Tools/03_SFX/|/Sound Effects Davinci/|/node_modules/|/Plugins/|"
    r"/DJI Audio Backup/|Recordings von This is Marketing|\.dra/MediaFiles|/05_Rotato - MockUp Tool/|"
    r"/\d*_?Sound ?Effe[ck]te?/|/Sound Effects/|/SFX/|/AI SFX/|/SFXs neu/|/SoundFX/",
    re.I)
SPRACHE = re.compile(
    r"_Eleven_v3_|ElevenLabs_|/[^/]*\bV(oice)? ?O(ver)?\b[^/]*/|/\d+_Voice|/Voice ?over|/Voice Over/|"
    r"/07_Samples/|_[A-Za-z0-9]{20}\.(wav|mp3)$|/DJI_\d+_\d{8}_\d{6}\.WAV$|/\d+ Mic|"
    r"-esv2-|enhanced-v2|audio für adobe|Voice Over|Sprecher|/04_Exportiert/|/\d{4}(\(\d\))?\.WAV$",
    re.I)
# Rekorder/Kameras schreiben ".WAV" groß; Artlist-Downloads heißen "Künstler - Titel.wav"
AUFNAHME = re.compile(r"/[^/ ]*[^/]*\.WAV$")
STEM = re.compile(r"/stems-zip-|/stems?/|_stem-\d|"
                  r" - (Drums|Percussion|Bass|Synths?|Strings|Keys|Piano|Guitars?|(Lead |Backing )?Vocals|Melody|Pads|Brass|FX)\.\w+$", re.I)
ENVATO = re.compile(r"/([a-z0-9-]+)-(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})-utc/", re.I)
ENVATO_NEBEN = re.compile(r"/loops?/|_loop|/shorts/|_short-|\((extra-)?short|\(medium|\(extended|\(loop\)|\(short\)| short\.", re.I)
VERSION = re.compile(
    r"^(instrumental|no (lead|backing) vocals|no leads|alternative|short|extended|slowed|remake|creative cut|"
    r"clean|edit|radio|acoustic|piano|vocal|stripped|remix|.* remix|under)", re.I)
SFX_ANBIETER = re.compile(
    r"^(Artlist (Original|Studios|Foley|Musical Logos)|BOOM Library|SoundBits|Unrealsfx|Epic Stock Media|"
    r"Airborne Sound|Foley Walkers|Carlos Santa Rita|Vadi Sound|Martin Scaglia|Slava Pogorelsky|Eytan Krief|"
    r"Chroma SFX|Cinemear|SoundCrib|JBoB|Just Sound Effects|DB studios|Fusehive|Gain Walkers|Soundholder|"
    r"Lukas Tvrdon|Fly Sound|Stuart Duffield|Articulated Sounds|Ni Sound|Sampletraxx|Front Row SFX|2496 SFX|"
    r"Mat Eric Hart|Soundkrampf|Marcello Del Monaco|Taris Studios|Yael Heim|Flaviu Ciocan|SilenceOther Sounds|"
    r"Ambisonic Spaces|Céline Woodburn|Cinematic Sound Design|Glitchedtones|Ivo Vicic|Periscope Post|"
    r"Rob Kubicki|Travsonic|Udi Zisser|Alberto Sueri|Barney Oram|Callum Donaldson|Cristian Lucchetta|"
    r"Cyberwave Orchestra|DeanKR|Mechanical Wave|MAD ROBOT|Selkor Studio|Soundtrack Creation|TeaSound)", re.I)


def scan():
    rows = []
    for dirpath, dirnames, filenames in os.walk(NAS_ROOT):
        # eigene Libraries nie mitscannen
        dirnames[:] = [d for d in dirnames if not d.startswith((".", "#")) and d not in ("07_Musik Library", "08_SFX Library")]
        for fn in filenames:
            if fn.startswith("._") or os.path.splitext(fn)[1].lower() not in AUDIO_EXT:
                continue
            p = os.path.join(dirpath, fn)
            try:
                st = os.stat(p)
            except OSError:
                continue
            rows.append((st.st_size, int(st.st_mtime), p))
    return rows


def lese_tsv(pfad):
    rows = []
    for line in open(pfad, encoding="utf-8"):
        size, mtime, rel = line.rstrip("\n").split("\t", 2)
        rows.append((int(size), int(mtime), str(NAS_ROOT) + rel[1:]))
    return rows


def probe(p):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:format_tags:stream=codec_name,sample_rate,channels,bits_per_sample",
         "-of", "json", p], capture_output=True, text=True, timeout=120)
    d = json.loads(r.stdout or "{}")
    fmt = d.get("format", {})
    tags = {k.lower(): v for k, v in (fmt.get("tags") or {}).items()}
    st = (d.get("streams") or [{}])[0]
    return {"dur": round(float(fmt.get("duration") or 0), 2), "tags": tags,
            "codec": st.get("codec_name"), "rate": st.get("sample_rate"),
            "ch": st.get("channels"), "bits": st.get("bits_per_sample")}


def projekt_von(p):
    rel = unicodedata.normalize("NFC", os.path.relpath(p, NAS_ROOT / "01_Projekte"))
    teile = rel.split(os.sep)
    if teile[0] == "01_Kunden" and len(teile) > 3 and teile[2] == "02_Projekte":
        projekt = re.sub(r"^\d+_(Projekt[- ]?)?", "", teile[3]).strip()
        # Sammelordner wie "04_Sonstiges" oder "02_Kunden Testimonials": eine Ebene tiefer benennen
        if projekt in ("Sonstiges", "NIRO Content", "Kunden Testimonials", "Werbeanzeigen") and len(teile) > 5:
            projekt += " / " + re.sub(r"^\d+_", "", teile[4]).strip()
        return f"{teile[1].strip()} / {projekt}"
    if teile[0] == "01_Kunden":
        return f"{teile[1].strip()} / {teile[2] if len(teile) > 3 else ''}".rstrip(" /")
    return " / ".join(t for t in teile[:3] if not os.path.splitext(t)[1]).strip()


def normal(s):
    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def zerlege(o):
    """Künstler/Titel/Version aus dem Dateinamen (Artlist-Schema)."""
    stem = unicodedata.normalize("NFC", os.path.splitext(os.path.basename(o["path"]))[0])
    stem = re.sub(r"\s*\((\d+|256)\)\s*$", "", stem)
    stem = re.sub(r"(version) e$", r"\1", stem, flags=re.I)
    teile = [t.strip() for t in stem.split(" - ")]
    m = ENVATO.search(o["path"])
    if m:
        titel = re.sub(r"_main-", " ", stem)
        return {"quelle": "envato", "slug": m.group(1), "kuenstler": "", "titel": titel.strip(), "version": ""}
    if len(teile) >= 2:
        return {"quelle": "artlist?", "kuenstler": teile[0], "titel": teile[1], "version": " - ".join(teile[2:])}
    return {"quelle": "unbekannt", "kuenstler": "", "titel": stem, "version": ""}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan-tsv")
    args = ap.parse_args()
    DATA.mkdir(exist_ok=True)

    rows = lese_tsv(args.scan_tsv) if args.scan_tsv else scan()
    print(f"{len(rows)} Audiodateien auf dem NAS")

    raus = collections.Counter()
    kandidaten = []
    for size, mtime, p in rows:
        n = unicodedata.normalize("NFC", p)  # macOS/SMB liefert Umlaute zerlegt (NFD)
        base = os.path.basename(n)
        if SFX_ANBIETER.match(base) or re.search(r"sound ?effect", base, re.I):
            raus["SFX (Anbieter/Name)"] += 1
        elif SPRACHE.search(n) or (AUFNAHME.search(n) and " - " not in base):
            raus["Sprache/Aufnahme"] += 1
        elif SFX_ORDNER.search(n):
            # falsch abgelegte Songs ("Künstler - Titel[ - Version].wav") nur mit Artlist-Musiktreffer behalten
            if " - " in base and "/05_Rotato" not in n:
                kandidaten.append({"path": p, "size": size, "mtime": mtime, "aus_sfx_ordner": True})
            else:
                raus["SFX-Ordner"] += 1
        elif STEM.search(n):
            raus["Stems"] += 1
        elif ENVATO.search(n) and ENVATO_NEBEN.search(n):
            raus["Envato Loops/Kurzfassungen"] += 1
        else:
            kandidaten.append({"path": p, "size": size, "mtime": mtime})

    cache_pfad = DATA / "probe_cache.json"
    cache = json.load(open(cache_pfad)) if cache_pfad.exists() else {}
    offen = [k for k in kandidaten if f"{k['path']}|{k['size']}|{k['mtime']}" not in cache]
    with ThreadPoolExecutor(8) as ex:
        for k, info in zip(offen, ex.map(lambda k: probe(k["path"]), offen)):
            cache[f"{k['path']}|{k['size']}|{k['mtime']}"] = info
    json.dump(cache, open(cache_pfad, "w"), ensure_ascii=False)

    songs, ausgeschlossen = [], []
    for k in kandidaten:
        k.update(cache[f"{k['path']}|{k['size']}|{k['mtime']}"])
        k["ext"] = os.path.splitext(k["path"])[1].lower()
        titel_tag = k["tags"].get("title", "")
        grund = None
        if re.search(r"SFO-\d|MASTERED", titel_tag):
            grund = "Artlist-SFX (Tag)"
        elif "voice-memo-uuid" in k["tags"]:
            grund = "Sprachmemo"
        elif k["dur"] < 25:
            grund = "kürzer als 25 s"
        elif k.get("aus_sfx_ordner") and k["dur"] < 60:
            grund = "SFX-Ordner, kürzer als 60 s"
        if grund:
            raus[grund] += 1
            ausgeschlossen.append({"path": k["path"], "grund": grund, "dur": k["dur"]})
            continue
        k.update(zerlege(k))
        cr = (k["tags"].get("copyright", "") + k["tags"].get("comment", "")).lower()
        if "artlist" in cr or "art-list" in cr:
            k["quelle"] = "artlist"
        # Artlist-SFX-Muster "Anbieter - Pack - Name": nur mit Musik-Treffer behalten
        k["pruefen"] = bool(k["version"]) and not VERSION.match(k["version"]) and k["quelle"] != "artlist"
        if k["quelle"] == "unbekannt" or k.get("aus_sfx_ordner"):
            k["pruefen"] = True
        songs.append(k)

    gruppen = collections.defaultdict(list)
    for s in songs:
        if s["quelle"] == "envato":
            schluessel = "envato::" + normal(s["slug"] + " " + s["titel"])
        else:
            schluessel = normal(" - ".join(x for x in (s["kuenstler"], s["titel"], s["version"]) if x))
        gruppen[schluessel].append(s)

    inventar = []
    for schluessel, fassungen in sorted(gruppen.items()):
        best = max(fassungen, key=lambda s: (FORMAT_RANG.get(s["ext"], 0), s["size"]))
        inventar.append({
            "key": schluessel,
            "quelle": best["quelle"], "slug": best.get("slug", ""),
            "kuenstler": best["kuenstler"], "titel": best["titel"], "version": best["version"],
            "pruefen": all(f["pruefen"] for f in fassungen),
            "best": {x: best[x] for x in ("path", "ext", "size", "dur", "tags", "codec", "rate", "ch", "bits")},
            "fundstellen": sorted({f["path"] for f in fassungen}),
            "projekte": sorted({projekt_von(f["path"]) for f in fassungen}),
        })
    json.dump(inventar, open(DATA / "inventar.json", "w"), ensure_ascii=False, indent=1)
    json.dump({"zaehler": raus, "kurz": ausgeschlossen}, open(DATA / "ausgeschlossen.json", "w"), ensure_ascii=False, indent=1)

    q = collections.Counter(e["quelle"] for e in inventar)
    print("ausgeschlossen:", dict(raus))
    print(f"{len(inventar)} Songs/Versionen ({sum(e['best']['size'] for e in inventar) / 1e9:.1f} GB), "
          f"davon {sum(e['pruefen'] for e in inventar)} zu prüfen; Quellen: {dict(q)}")


if __name__ == "__main__":
    main()
