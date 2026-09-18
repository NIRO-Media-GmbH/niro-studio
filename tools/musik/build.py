"""Library bauen: Songs laut data/plan.json kopieren, nur die Kopien taggen, prüfen, Katalog schreiben.

Auf dem NAS wird ausschließlich unterhalb von LIBRARY geschrieben. Quellen werden
nur lesend geöffnet. WAV: neuer LIST/INFO- + id3-Chunk, data-Chunk bitgleich
(MD5 der Kopie wird neu eingelesen und mit der Quelle verglichen). MP3/M4A:
Kopie + mutagen, Prüfung über MD5 der Audiopakete (ffmpeg -f md5). AAC ohne
Container (kein Tag-Format) wird 1:1 kopiert und per Datei-MD5 geprüft.

    venv/bin/python build.py --nur 5     # Probelauf mit 5 Songs
    venv/bin/python build.py             # alles (bereits Fertiges wird übersprungen)
"""
import argparse
import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from mutagen.id3 import COMM, ID3, TALB, TBPM, TCON, TCOP, TIT1, TIT2, TPE1, TXXX, WOAS, ID3NoHeaderError
from mutagen.mp4 import MP4

import riff
from config import DATA, KATEGORIEN, LIBRARY, UNKLAR

LOCK = threading.Lock()
LIESMICH = """NIRO Musik-Library
==================
Alle Songs, die in NIRO-Projekten auf dem NAS lagen - als Kopien. Die Originale in den
Projektordnern bleiben unverändert. Aufgebaut am 16.09.2026.

Ordner nach Einsatzzweck:
- Recruiting & Ads          treibend, energiegeladen, selbstbewusst
- Imagefilm & Corporate     cinematic, inspirierend, seriös, episch
- Social Reels & Trends     groovy, verspielt, Hip-Hop/Funk/Lo-Fi
- Event & Aftermovie        Party-Pop, fröhlich, sommerlich
- Emotional & Testimonial   ruhig, gefühlvoll, Piano/Akustik
- Unklare Quelle            NICHT über Artlist/Envato lizenziert oder Herkunft unbekannt
                            (u. a. YouTube-Downloads, Epidemic Sound) - vor dem Einsatz in
                            Kundenvideos die Lizenz klären!

Suchen und filtern: _Katalog.csv (Excel/Numbers) mit Stimmung, Genre, BPM, Video-Themes,
Instrumenten, "Passt auch zu", "Verwendet in" (Kunde/Projekt), Artlist-Link und Originalpfad.

Tags in den Dateien: Titel, Künstler, Album, Genre, BPM, Kommentar (alle Infos),
Stichworte; WAV zusätzlich mit ID3-Chunk. Die Einordnung ist automatisch (Artlist-Stimmung,
-Genre und -Video-Themes plus die Projekte, in denen der Song lief) - im Zweifel die
Spalte "Passt auch zu" beachten.

Aktualisieren (neue Songs): NIRO Studio -> tools/musik/README.md
"""


def unbekannt(wert):
    return not wert or str(wert).strip().lower() in ("unknown", "none")


def liste(werte):
    return ", ".join(werte or [])


def kommentar(e):
    m = e["meta"]
    teile = [f"Einsatz: {e['kategorie']}" + (f" (passt auch: {', '.join(e['auch'])})" if e["auch"] else "")]
    if m.get("moods"):
        teile.append(f"Stimmung: {liste(m['moods'])}")
    if m.get("genres"):
        teile.append(f"Genre: {liste(m['genres'])}")
    if m.get("themen"):
        teile.append(f"Video-Themes: {liste(m['themen'])}")
    if m.get("instrumente"):
        teile.append(f"Instrumente: {liste(m['instrumente'])}")
    tempo = liste(m.get("tempo")) + (f" {m['bpm']} BPM" if m.get("bpm") else "")
    if tempo.strip():
        teile.append(f"Tempo: {tempo.strip()}")
    quelle = m.get("quelle") or "unklar"
    teile.append(f"Quelle: {quelle}" + (f" {m['url']}" if m.get("url") else ""))
    if m.get("hinweis"):
        teile.append(m["hinweis"])
    teile.append(f"Verwendet in: {'; '.join(e['projekte'])}")
    return " | ".join(teile)


def felder(e, alt):
    """Tag-Werte: Artlist-/Envato-Daten, sonst vorhandene Tags, sonst Dateiname."""
    m = e["meta"]
    lizenz = {"Artlist": "Licensed for video by Artlist.io", "Envato Elements": "Envato Elements license"}.get(m.get("quelle"), "")
    f = {
        "titel": m.get("titel") or ("" if unbekannt(alt.get("titel")) else alt["titel"]),
        "kuenstler": m.get("kuenstler") or ("" if unbekannt(alt.get("kuenstler")) else alt["kuenstler"]),
        "album": m.get("album") or ("" if unbekannt(alt.get("album")) else alt["album"]),
        "genre": liste(m.get("genres")) or ("" if unbekannt(alt.get("genre")) else alt["genre"]),
        "copyright": alt.get("copyright") if not unbekannt(alt.get("copyright")) else lizenz,
        "jahr": alt.get("jahr", ""),
        "kommentar": kommentar(e) + ("" if unbekannt(alt.get("kommentar")) else f" | Alter Kommentar: {alt['kommentar']}"),
        "stichworte": "; ".join((m.get("moods") or []) + (m.get("themen") or []) + (m.get("instrumente") or [])),
        "bpm": str(m["bpm"]) if m.get("bpm") else "",
        "quelle": m.get("quelle") or "",
    }
    return f


def id3_setzen(tags, e, f):
    m = e["meta"]
    for rahmen, wert in ((TIT2, f["titel"]), (TPE1, f["kuenstler"]), (TALB, f["album"]), (TCOP, f["copyright"]),
                         (TIT1, e["kategorie"]), (TBPM, f["bpm"])):
        if wert:
            tags.setall(rahmen.__name__, [rahmen(encoding=3, text=wert)])
    if m.get("genres"):
        tags.setall("TCON", [TCON(encoding=3, text=m["genres"])])
    elif f["genre"]:
        tags.setall("TCON", [TCON(encoding=3, text=f["genre"])])
    tags.setall("COMM", [COMM(encoding=3, lang="deu", desc="", text=f["kommentar"])])
    if m.get("url"):
        tags.setall("WOAS", [WOAS(url=m["url"])])
    for desc, wert in (("MOOD", "; ".join(m.get("moods") or [])), ("VIDEO_THEMES", "; ".join(m.get("themen") or [])),
                       ("INSTRUMENTS", "; ".join(m.get("instrumente") or [])), ("EINSATZ", e["kategorie"]),
                       ("VERWENDET_IN", "; ".join(e["projekte"])), ("QUELLE", f["quelle"]), ("ARTLIST_ID", m.get("id") or "")):
        if wert:
            tags.setall(f"TXXX:{desc}", [TXXX(encoding=3, desc=desc, text=wert)])


def container_von(pfad):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=format_name", "-of", "default=nw=1:nk=1", pfad],
                       capture_output=True, text=True, timeout=120)
    return r.stdout.strip().split(",")[0]


def audio_md5(pfad):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", pfad, "-map", "0:a", "-c", "copy", "-f", "md5", "-"],
                       capture_output=True, text=True, timeout=600)
    if r.returncode:
        raise RuntimeError(f"ffmpeg md5: {r.stderr.strip()[:200]}")
    return r.stdout.strip()


def datei_md5(pfad):
    h = hashlib.md5()
    with open(pfad, "rb") as f:
        for block in iter(lambda: f.read(riff.PUFFER), b""):
            h.update(block)
    return h.hexdigest()


def baue(e):
    try:
        return _baue(e)
    except Exception:
        ziel = LIBRARY / e["ziel"]
        rest = ziel.with_name("." + ziel.name + ".teil")
        if rest.exists():
            rest.unlink()  # nur die eigene angefangene Teildatei
        raise


def _baue(e):
    quelle = e["quelle_pfad"]
    ziel = LIBRARY / e["ziel"]
    assert str(ziel).startswith(str(LIBRARY) + "/"), ziel  # nie außerhalb der Library schreiben
    ziel.parent.mkdir(parents=True, exist_ok=True)
    teil = ziel.with_name("." + ziel.name + ".teil")  # Punktdatei: von Syncthing ignoriert

    if e["ext"] == ".wav":
        with open(quelle, "rb") as q:
            info = riff.lies_info(q)
        alt = {"titel": info.get("INAM"), "kuenstler": info.get("IART"), "album": info.get("IPRD"), "genre": info.get("IGNR"),
               "copyright": info.get("ICOP"), "kommentar": info.get("ICMT"), "jahr": info.get("ICRD", "")}
        f = felder(e, alt)
        id3 = ID3()
        id3_setzen(id3, e, f)
        puffer = io.BytesIO()
        id3.save(puffer, v2_version=3, padding=lambda _: 0)
        info_neu = {"INAM": f["titel"], "IART": f["kuenstler"], "IPRD": f["album"], "IGNR": f["genre"], "ISBJ": e["kategorie"],
                    "ICMT": f["kommentar"], "IKEY": f["stichworte"], "ICOP": f["copyright"], "ICRD": f["jahr"], "ISRC": f["quelle"]}
        md5_quelle = riff.schreibe(quelle, teil, info_neu, puffer.getvalue())
        md5_ziel = riff.data_md5(teil)
    else:
        shutil.copyfile(quelle, teil)
        alt = {}
        container = container_von(quelle)
        if e["ext"] in (".mp3", ".m4a") and container != {".mp3": "mp3", ".m4a": "mov"}[e["ext"]]:
            raise RuntimeError(f"Datei ist {container} mit {e['ext']}-Endung – nicht taggen, von Hand prüfen")
        if e["ext"] == ".mp3":
            try:
                tags = ID3(teil)
            except ID3NoHeaderError:
                tags = ID3()
            gib = lambda k: str(tags[k].text[0]) if k in tags and tags[k].text else ""
            alt = {"titel": gib("TIT2"), "kuenstler": gib("TPE1"), "album": gib("TALB"), "genre": gib("TCON"),
                   "copyright": gib("TCOP"), "kommentar": " ".join(str(c.text[0]) for c in tags.getall("COMM") if c.text)}
            f = felder(e, alt)
            id3_setzen(tags, e, f)
            tags.save(teil, v2_version=3)
        elif e["ext"] == ".m4a":
            mp4 = MP4(teil)
            t = mp4.tags if mp4.tags is not None else (mp4.add_tags() or mp4.tags)
            gib = lambda k: str(t[k][0]) if k in t and t[k] else ""
            alt = {"titel": gib("\xa9nam"), "kuenstler": gib("\xa9ART"), "album": gib("\xa9alb"), "genre": gib("\xa9gen"),
                   "copyright": gib("cprt"), "kommentar": gib("\xa9cmt")}
            f = felder(e, alt)
            for k, w in (("\xa9nam", f["titel"]), ("\xa9ART", f["kuenstler"]), ("\xa9alb", f["album"]), ("\xa9gen", f["genre"]),
                         ("\xa9cmt", f["kommentar"]), ("\xa9grp", e["kategorie"]), ("cprt", f["copyright"])):
                if w:
                    t[k] = [w]
            if f["bpm"]:
                t["tmpo"] = [int(float(f["bpm"]))]
            mp4.save()
        if e["ext"] in (".mp3", ".m4a"):
            md5_quelle, md5_ziel = audio_md5(quelle), audio_md5(str(teil))
        else:  # z. B. AAC ohne Container: kein Tag-Format, 1:1-Kopie
            md5_quelle, md5_ziel = datei_md5(quelle), datei_md5(teil)

    if md5_quelle != md5_ziel:
        raise RuntimeError(f"Audiodaten weichen ab ({md5_quelle} ≠ {md5_ziel})")
    for versuch in range(6):  # SMB: frisch geschriebene Dateien sind kurz gesperrt (EIO/EBUSY)
        try:
            os.replace(teil, ziel)
            break
        except OSError:
            if versuch == 5:
                raise
            time.sleep(2 + 3 * versuch)
    return {"ziel": str(ziel.relative_to(LIBRARY)), "md5": md5_ziel, "bytes": ziel.stat().st_size, "mtime": int(ziel.stat().st_mtime)}


def plan_hash(e):
    relevant = {k: e[k] for k in ("ziel", "kategorie", "auch", "projekte", "meta")}  # Wahl zwischen gleichen Kopien egal
    return hashlib.md5(json.dumps(relevant, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def katalog(plan, stand):
    pfad = LIBRARY / "_Katalog.csv"
    with open(pfad, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["Ordner", "Datei", "Künstler", "Titel", "Album", "Quelle", "Dauer", "BPM", "Tempo", "Genre", "Stimmung",
                    "Video-Themes", "Instrumente", "Passt auch zu", "Verwendet in", "Link", "Original auf dem NAS"])
        for e in sorted(plan, key=lambda e: (KATEGORIEN + [UNKLAR]).index(e["kategorie"]) if e["kategorie"] in KATEGORIEN + [UNKLAR] else 99):
            s = stand.get(e["key"])
            if not s or s.get("von_hand") in ("entfernt", "fehlt"):
                continue
            m = e["meta"]
            dauer = f"{int(e['dauer'] // 60)}:{int(round(e['dauer'] % 60)):02d}"
            w.writerow([s["ziel"].split("/")[0], os.path.basename(s["ziel"]), m.get("kuenstler", ""), m.get("titel", ""), m.get("album", ""),
                        m.get("quelle") or "unklar", dauer, m.get("bpm") or "", liste(m.get("tempo")), liste(m.get("genres")),
                        liste(m.get("moods")), liste(m.get("themen")), liste(m.get("instrumente")), ", ".join(e["auch"]),
                        "; ".join(e["projekte"]), m.get("url", ""),
                        str(e["quelle_pfad"]).replace("/Volumes/NIRO NAS/", "NIRO NAS/")])
    return pfad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nur", type=int, help="nur die ersten N offenen Songs (Probelauf)")
    ap.add_argument("--worker", type=int, default=4)
    args = ap.parse_args()

    plan = json.load(open(DATA / "plan.json"))
    stand_pfad = DATA / "build_stand.json"
    stand = json.load(open(stand_pfad)) if stand_pfad.exists() else {}
    for e in plan:
        e["plan_hash"] = plan_hash(e)
    offen, von_hand = [], []
    for e in plan:
        s = stand.get(e["key"])
        if not s:
            offen.append(e)  # neu
        elif s.get("von_hand") or not (LIBRARY / s["ziel"]).exists():
            von_hand.append(e)  # von Hand entfernt/verschoben: nie neu anlegen (User sortiert die Library)
            if not s.get("von_hand"):
                s["von_hand"] = "fehlt"
        elif s.get("plan_hash") != e["plan_hash"] and s.get("mtime") == int((LIBRARY / s["ziel"]).stat().st_mtime):
            offen.append(e)  # Plan geändert und Datei seit dem Bau unberührt
    if von_hand:
        print(f"{len(von_hand)} von Hand entfernt/verschoben – bleiben so")
    if args.nur:
        offen = offen[:args.nur]
    print(f"{len(offen)} Songs zu bauen, {len(plan) - len(offen)} fertig/übersprungen")

    fehler = {}
    with ThreadPoolExecutor(args.worker) as ex:
        zukunft = {ex.submit(baue, e): e for e in offen}
        for i, z in enumerate(as_completed(zukunft), 1):
            e = zukunft[z]
            try:
                erg = z.result()
                erg["plan_hash"] = e["plan_hash"]
                with LOCK:
                    alt = stand.get(e["key"])
                    if alt and alt["ziel"] != erg["ziel"] and (LIBRARY / alt["ziel"]).exists():
                        (LIBRARY / alt["ziel"]).unlink()  # eigene, jetzt umbenannte/umsortierte Kopie
                    stand[e["key"]] = erg
                    if i % 20 == 0:
                        json.dump(stand, open(stand_pfad, "w"), ensure_ascii=False, indent=1)
                        print(f"  {i}/{len(offen)}", flush=True)
            except Exception as err:
                fehler[e["key"]] = f"{type(err).__name__}: {err}"
                print(f"  ! {os.path.basename(e['quelle_pfad'])}: {err}", flush=True)
    json.dump(stand, open(stand_pfad, "w"), ensure_ascii=False, indent=1)
    json.dump(fehler, open(DATA / "build_fehler.json", "w"), ensure_ascii=False, indent=1)
    print(f"Katalog: {katalog(plan, stand)}")
    (LIBRARY / "_intern").mkdir(exist_ok=True)
    for name in ("plan.json", "manuell.json"):
        shutil.copyfile(DATA / name, LIBRARY / "_intern" / name)
    (LIBRARY / "_LIESMICH.txt").write_text(LIESMICH, encoding="utf-8")
    print(f"fertig: {len(stand)} Songs, Fehler: {len(fehler)}")


if __name__ == "__main__":
    main()
