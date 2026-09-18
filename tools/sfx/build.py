"""SFX-Library bauen: SFX laut data/plan.json kopieren, nur die Kopien taggen, prüfen, Katalog schreiben.

Auf dem NAS wird ausschließlich unterhalb von LIBRARY geschrieben; Quellen nur lesend.
WAV: neuer LIST/INFO- + id3-Chunk (riff.py aus tools/musik), data-Chunk bitgleich per MD5.
MP3/M4A: Kopie + mutagen, MD5 der Audiopakete. Andere Formate (AAC, AIFF …): 1:1-Kopie, Datei-MD5.

    venv/bin/python build.py --nur 10   # Probelauf
    venv/bin/python build.py            # alles (Fertiges wird übersprungen)
"""
import argparse
import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from mutagen.id3 import COMM, ID3, TALB, TCON, TCOP, TIT1, TIT2, TPE1, TXXX, WOAS, ID3NoHeaderError
from mutagen.mp4 import MP4

from config import DATA, KATEGORIEN, LIBRARY, UNKLAR

sys.path.append(str(Path(__file__).resolve().parent.parent / "musik"))  # riff.py teilen (angehängt: eigene config gewinnt)
import riff  # noqa: E402

LOCK = threading.Lock()
LIZENZ = {"Artlist": "Licensed for video by Artlist.io", "Envato Elements": "Envato Elements license"}
LIESMICH = """NIRO SFX-Library
================
Soundeffekte aus den NIRO-Projekten und Vorlagen auf dem NAS - als Kopien. Die Originale
bleiben unverändert. Aufgebaut am 16.09.2026. Nicht enthalten: Musik (siehe 07_Musik Library),
Sprache/Voiceover, ElevenLabs und die Adobe Sound Library (liegt weiter in 03_SFX).

Ordner nach Sound-Typ: Whoosh & Transitions, Impacts & Hits, Riser & Build-ups, Drones &
Flächen, Glitch & Digital, UI/Clicks & Pops, Film Burn/Vinyl & Analog, Intros/Logos &
Jingles, Foley & Alltag, Menschen & Crowd, Natur/Wasser & Wetter, Fahrzeuge & Maschinen,
Feuer/Explosionen & Waffen, Ambience & Orte, Horror & Spannung, Cartoon & Game.

Unklare Quelle: YouTube-Downloads, Freesound, Pixabay-artige Dateien und SFX ohne Herkunft -
vor dem Einsatz in Kundenvideos die Lizenz klären!

Suchen und filtern: _Katalog.csv (Excel/Numbers) mit Name, Anbieter, Pack, Quelle, Dauer,
Artlist-Kategorien, "Passt auch zu", "Verwendet in", Link und Originalpfad.
Tags in den Dateien: Titel, Anbieter, Pack, Genre (Sound Effect + Ordner), Kommentar, Stichworte.
Die Einordnung ist automatisch (Dateiname, Vorlagen-Ordner, Artlist-Kategorien).

Aktualisieren: NIRO Studio -> tools/sfx/README.md
"""


def unbekannt(wert):
    return not wert or str(wert).strip().lower() in ("unknown", "none")


def kommentar(e):
    m = e["meta"]
    teile = [f"Kategorie: {e['typ'] if e['kategorie'] == UNKLAR else e['kategorie']}" + (f" (passt auch: {', '.join(e['auch'])})" if e["auch"] else "")]
    if m["artlist_kategorien"]:
        teile.append(f"Artlist-Kategorien: {', '.join(m['artlist_kategorien'])}")
    teile.append(f"Quelle: {m['quelle'] or 'unklar'}" + (f" {m['url']}" if m["url"] else ""))
    if m["hinweis"]:
        teile.append(m["hinweis"])
    teile.append(f"Verwendet in: {'; '.join(e['projekte'])}")
    return " | ".join(teile)


def felder(e, alt):
    m = e["meta"]
    return {
        "titel": m["name"] if m["quelle"] == "Artlist" else (alt.get("titel") if not unbekannt(alt.get("titel")) else m["name"]),
        "anbieter": m["anbieter"] or ("" if unbekannt(alt.get("kuenstler")) else alt["kuenstler"]),
        "pack": m["pack"] or ("" if unbekannt(alt.get("album")) else alt["album"]),
        "copyright": alt["copyright"] if not unbekannt(alt.get("copyright")) else LIZENZ.get(m["quelle"], ""),
        "kommentar": kommentar(e) + ("" if unbekannt(alt.get("kommentar")) else f" | Alter Kommentar: {alt['kommentar']}"),
        "stichworte": "; ".join(m["artlist_kategorien"] + m["stichworte"]),
        "genre": ["Sound Effect", e["typ"]],
        "quelle": m["quelle"],
    }


def id3_setzen(tags, e, f):
    m = e["meta"]
    for rahmen, wert in ((TIT2, f["titel"]), (TPE1, f["anbieter"]), (TALB, f["pack"]), (TCOP, f["copyright"]), (TIT1, e["kategorie"])):
        if wert:
            tags.setall(rahmen.__name__, [rahmen(encoding=3, text=wert)])
    tags.setall("TCON", [TCON(encoding=3, text=f["genre"])])
    tags.setall("COMM", [COMM(encoding=3, lang="deu", desc="", text=f["kommentar"])])
    if m["url"]:
        tags.setall("WOAS", [WOAS(url=m["url"])])
    for desc, wert in (("SFX_KATEGORIE", e["typ"]), ("ARTLIST_KATEGORIEN", "; ".join(m["artlist_kategorien"])),
                       ("VERWENDET_IN", "; ".join(e["projekte"])), ("QUELLE", f["quelle"]), ("ARTLIST_ID", m["id"])):
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

    wav_ok = False
    if e["ext"] == ".wav":
        try:
            with open(quelle, "rb") as q:
                info = riff.lies_info(q)
            wav_ok = True
        except ValueError:  # z. B. RF64 oder defekter Kopf: unverändert kopieren
            wav_ok = False
    if wav_ok:
        alt = {"titel": info.get("INAM"), "kuenstler": info.get("IART"), "album": info.get("IPRD"),
               "copyright": info.get("ICOP"), "kommentar": info.get("ICMT")}
        f = felder(e, alt)
        id3 = ID3()
        id3_setzen(id3, e, f)
        puffer = io.BytesIO()
        id3.save(puffer, v2_version=3, padding=lambda _: 0)
        info_neu = {"INAM": f["titel"], "IART": f["anbieter"], "IPRD": f["pack"], "IGNR": ", ".join(f["genre"]),
                    "ISBJ": e["kategorie"], "ICMT": f["kommentar"], "IKEY": f["stichworte"], "ICOP": f["copyright"],
                    "ICRD": info.get("ICRD", ""), "ISRC": f["quelle"]}
        try:
            md5_quelle = riff.schreibe(quelle, teil, info_neu, puffer.getvalue())
            md5_ziel = riff.data_md5(teil)
        except OSError as fehler:  # nur abgeschnittene Quelldatei (Header länger als Datei): unverändert kopieren
            if "Quelle zu kurz" not in str(fehler):
                raise
            wav_ok = False
            e["_unveraendert"] = "Quelldatei abgeschnitten (unvollständiger Download) – 1:1-Kopie ohne neue Tags"
    if not wav_ok and e["ext"] == ".wav":
        shutil.copyfile(quelle, teil)
        md5_quelle, md5_ziel = datei_md5(quelle), datei_md5(teil)
    elif not wav_ok:
        shutil.copyfile(quelle, teil)
        container = container_von(quelle)
        if e["ext"] in (".mp3", ".m4a") and container != {".mp3": "mp3", ".m4a": "mov"}[e["ext"]]:
            # falsche Endung (z. B. y2mate: MP4/AAC als .mp3): keine Tags davorschreiben, 1:1 kopieren
            e["_unveraendert"] = f"Datei ist {container} mit {e['ext']}-Endung – 1:1-Kopie ohne neue Tags"
            md5_quelle, md5_ziel = datei_md5(quelle), datei_md5(teil)
        elif e["ext"] == ".mp3":
            try:
                tags = ID3(teil)
            except ID3NoHeaderError:
                tags = ID3()
            gib = lambda k: str(tags[k].text[0]) if k in tags and tags[k].text else ""
            alt = {"titel": gib("TIT2"), "kuenstler": gib("TPE1"), "album": gib("TALB"), "copyright": gib("TCOP"),
                   "kommentar": " ".join(str(c.text[0]) for c in tags.getall("COMM") if c.text)}
            id3_setzen(tags, e, felder(e, alt))
            tags.save(teil, v2_version=3)
            md5_quelle, md5_ziel = audio_md5(quelle), audio_md5(str(teil))
        elif e["ext"] == ".m4a":
            mp4 = MP4(teil)
            if mp4.tags is None:
                mp4.add_tags()
            t = mp4.tags
            gib = lambda k: str(t[k][0]) if k in t and t[k] else ""
            f = felder(e, {"titel": gib("\xa9nam"), "kuenstler": gib("\xa9ART"), "album": gib("\xa9alb"),
                           "copyright": gib("cprt"), "kommentar": gib("\xa9cmt")})
            for k, w in (("\xa9nam", f["titel"]), ("\xa9ART", f["anbieter"]), ("\xa9alb", f["pack"]), ("\xa9gen", ", ".join(f["genre"])),
                         ("\xa9cmt", f["kommentar"]), ("\xa9grp", e["kategorie"]), ("cprt", f["copyright"])):
                if w:
                    t[k] = [w]
            mp4.save()
            md5_quelle, md5_ziel = audio_md5(quelle), audio_md5(str(teil))
        else:
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
    erg = {"ziel": str(ziel.relative_to(LIBRARY)), "md5": md5_ziel, "bytes": ziel.stat().st_size, "mtime": int(ziel.stat().st_mtime)}
    if e.get("_unveraendert"):
        erg["unveraendert"] = e["_unveraendert"]
    return erg


def plan_hash(e):
    relevant = {k: e[k] for k in ("ziel", "kategorie", "typ", "auch", "projekte", "meta")}
    return hashlib.md5(json.dumps(relevant, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def katalog(plan, stand):
    reihenfolge = KATEGORIEN + [UNKLAR]
    with open(LIBRARY / "_Katalog.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["Ordner", "Datei", "Name", "Anbieter", "Pack", "Quelle", "Dauer (s)", "Sound-Typ", "Passt auch zu",
                    "Artlist-Kategorien", "Verwendet in", "Link", "Hinweis", "Original auf dem NAS"])
        for e in sorted(plan, key=lambda e: (reihenfolge.index(e["kategorie"]), e["ziel"].lower())):
            s = stand.get(e["key"])
            if not s or s.get("von_hand") in ("entfernt", "fehlt"):
                continue
            m = e["meta"]
            w.writerow([s["ziel"].split("/")[0], os.path.basename(s["ziel"]), m["name"], m["anbieter"], m["pack"], m["quelle"] or "unklar",
                        f"{e['dauer']:.1f}".replace(".", ","), e["typ"], ", ".join(e["auch"]), ", ".join(m["artlist_kategorien"]),
                        "; ".join(e["projekte"]), m["url"], " | ".join(x for x in (m["hinweis"], s.get("unveraendert", "")) if x),
                        str(e["quelle_pfad"]).replace("/Volumes/NIRO NAS/", "NIRO NAS/")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nur", type=int)
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
    print(f"{len(offen)} SFX zu bauen, {len(plan) - len(offen)} fertig/übersprungen")
    fehler = {}
    with ThreadPoolExecutor(args.worker) as ex:
        zukunft = {ex.submit(baue, e): e for e in offen}
        for i, z in enumerate(as_completed(zukunft), 1):
            e = zukunft[z]
            try:
                erg = z.result()
                erg["plan_hash"] = e["plan_hash"]
                with LOCK:
                    stand[e["key"]] = erg
                    if i % 50 == 0:
                        json.dump(stand, open(stand_pfad, "w"), ensure_ascii=False, indent=1)
                        print(f"  {i}/{len(offen)}", flush=True)
            except Exception as err:
                fehler[e["key"]] = f"{type(err).__name__}: {err}"
                print(f"  ! {os.path.basename(e['quelle_pfad'])}: {err}", flush=True)
    json.dump(stand, open(stand_pfad, "w"), ensure_ascii=False, indent=1)
    json.dump(fehler, open(DATA / "build_fehler.json", "w"), ensure_ascii=False, indent=1)
    katalog(plan, stand)
    (LIBRARY / "_intern").mkdir(exist_ok=True)
    shutil.copyfile(DATA / "plan.json", LIBRARY / "_intern" / "plan.json")
    (LIBRARY / "_LIESMICH.txt").write_text(LIESMICH, encoding="utf-8")
    print(f"fertig: {len(stand)} SFX, Fehler: {len(fehler)}")


if __name__ == "__main__":
    main()
