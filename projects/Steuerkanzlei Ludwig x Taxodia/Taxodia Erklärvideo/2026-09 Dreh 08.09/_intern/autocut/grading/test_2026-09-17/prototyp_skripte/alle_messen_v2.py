"""Prototyp: Messung fuer alle V1-V3-Items der Grading-Test-Kopie mit Look C (Kontrast 1,05, Saettigung 1,00).

Je aktivem Einsatz 3 Bilder (20/50/80 %), Wert je Clip = Median aller Bilder, eigener Einsatz-Wert bei > 0,7 Bl. (e) bzw.
> 0,3 Bl. (R/B). Deaktivierte Items bekommen den Clip-Wert. Ergebnis: proto/plan_alle.json + proto/uebersicht_alle.jpg.
"""
import json, subprocess, sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HIER = Path(__file__).resolve().parent
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/vorlagen/feinschnitt/color/skripte")
sys.path.insert(0, str(HIER))
import colorlib as CL  # noqa: E402
import proto_messung as PM  # noqa: E402

LOOK_C = (1.05, 1.00)
PM.render.__defaults__ = (LOOK_C,)
PM.LOOK = LOOK_C
GRENZE = 8.0  # User 17.09.: Blendengrenze aufheben (NR spaeter von Hand)
PM.PROFIL["grenze_e"] = GRENZE
PM.bisekt.__defaults__ = (-GRENZE, GRENZE, 0.01)
FACES_DIR = HIER / "proto" / "faces_alle"
FACES_DIR.mkdir(parents=True, exist_ok=True)
A = 2.4 / 1.961  # Ausgabe Rec.709-A


def quellframe(it, f):
    return int(round(it["src"] + (f - it["start"]) * it["tempo"] / 100 * it["fps"] / 25))


def messe(auftrag):
    pfad, n, fps, jpg_name, boxen = auftrag
    PM.render.__defaults__ = (LOOK_C,)
    PM.PROFIL["grenze_e"] = GRENZE
    PM.bisekt.__defaults__ = (-GRENZE, GRENZE, 0.01)
    x = PM.decode(pfad, n, fps)
    return jpg_name, PM.messe_bild(x, boxen)


def main():
    daten = json.load(open(HIER / "proto" / "kopie_items.json"))
    items = daten["items"]
    je_clip = defaultdict(list)
    for it in items:
        je_clip[it["name"]].append(it)
    auftraege = []  # (pfad, n, fps, jpgname)
    for name, its in je_clip.items():
        mess = [i for i in its if i["aktiv"]] or its
        for it in mess:
            it["mess_frames"] = [quellframe(it, it["start"] + round(q * (it["dauer"] - 1))) for q in (0.2, 0.5, 0.8)]
            for n in it["mess_frames"]:
                auftraege.append((it["pfad"], n, it["fps"], f"{Path(it['pfad']).stem}__{n}"))
    auftraege = list(dict.fromkeys(auftraege))
    print("Bilder:", len(auftraege), flush=True)
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(lambda a: PM.decode(a[0], a[1], a[2]), auftraege))
    print("dekodiert", flush=True)
    for pfad, n, fps, jn in auftraege:
        ziel = FACES_DIR / f"{jn}.jpg"
        if not ziel.exists():
            x = PM.decode(pfad, n, fps)
            Image.fromarray(CL.to_u8(PM.render(x, {"e": 0, "wr": 0, "wb": 0}, (1.0, 1.0)))).save(ziel, quality=90)
    out = subprocess.run([str(PM.FACES), str(FACES_DIR)], capture_output=True, text=True, check=True).stdout
    boxen = {}
    for z in out.strip().splitlines():
        nm, _, rest = z.partition("\t")
        boxen[nm[:-4]] = [tuple(map(float, t.split(","))) for t in filter(None, rest.split(";")) if t != "ERR"]
    print("Gesichter:", sum(1 for v in boxen.values() if v), "von", len(boxen), flush=True)
    with ProcessPoolExecutor(12) as ex:
        ergebnisse = dict(ex.map(messe, [(p, n, f, jn, boxen.get(jn, [])) for p, n, f, jn in auftraege], chunksize=2))
    print("gemessen", flush=True)
    plan, clips = [], {}
    for name, its in je_clip.items():
        mess = [i for i in its if "mess_frames" in i]
        bilder = [ergebnisse[f"{Path(i['pfad']).stem}__{n}"] for i in mess for n in i["mess_frames"]]
        clip = {k: float(np.median([b[k] for b in bilder])) for k in ("e", "wr", "wb")}
        hinweise = sorted({h.split(" (")[0] for b in bilder for h in b["hinweise"]})
        grenze = any(abs(b["e"]) >= GRENZE - 0.001 for b in bilder)
        if grenze:
            hinweise.append("Belichtungsgrenze")
        anker = sorted({f"{b['e_anker']}/{b['wb_anker']}" for b in bilder})
        clips[name] = {"werte": {k: round(v, 3) for k, v in clip.items()}, "hinweise": hinweise, "anker": anker,
                       "bilder": len(bilder)}
        for it in its:
            w, quelle = clip, "clip"
            if "mess_frames" in it and it["aktiv"]:
                eig = {k: float(np.median([ergebnisse[f"{Path(it['pfad']).stem}__{n}"][k] for n in it["mess_frames"]]))
                       for k in ("e", "wr", "wb")}
                if abs(eig["e"] - clip["e"]) > 0.7 or abs(eig["wr"] - clip["wr"]) > 0.3 or abs(eig["wb"] - clip["wb"]) > 0.3:
                    w, quelle = eig, "einsatz"
            off = [(w["e"] + w["wr"]) * PM.STOP, w["e"] * PM.STOP, (w["e"] + w["wb"]) * PM.STOP]
            plan.append({"spur": it["spur"], "start": it["start"], "name": it["name"], "aktiv": it["aktiv"], "quelle": quelle,
                         "werte": {k: round(v, 3) for k, v in w.items()}, "n1": " ".join(f"{o:.4f}" for o in off)})
    json.dump({"look": LOOK_C, "clips": clips, "items": plan}, open(HIER / "proto" / "plan_alle_v2.json", "w"), indent=1, ensure_ascii=False)
    for name, c in sorted(clips.items()):
        print(f"{name:<26} e {c['werte']['e']:+.2f} R {c['werte']['wr']:+.2f} B {c['werte']['wb']:+.2f} | {c['anker']} | {c['hinweise']}")
    print("Einsatz-eigene Werte:", [(p["spur"], p["start"], p["name"]) for p in plan if p["quelle"] == "einsatz"])
    # Uebersicht: je Clip das mittlere Bild des ersten gemessenen Einsatzes, Darstellung wie am Mac
    namen = sorted(clips)
    W, H = 384, 216
    spalten = 5
    bogen = Image.new("RGB", (spalten * W, ((len(namen) + spalten - 1) // spalten) * (H + 40)), (16, 16, 16))
    d = ImageDraw.Draw(bogen)
    for i, name in enumerate(namen):
        it = next(j for j in je_clip[name] if "mess_frames" in j)
        n = it["mess_frames"][1]
        x = PM.decode(it["pfad"], n, it["fps"])
        m = PM.render(x, clips[name]["werte"], LOOK_C)
        img = Image.fromarray(CL.to_u8(np.clip(m, 0, 1) ** (2.4 / 2.2))).resize((W, H), Image.LANCZOS)
        x0, y0 = (i % spalten) * W, (i // spalten) * (H + 40)
        bogen.paste(img, (x0, y0 + 40))
        v = clips[name]["werte"]
        farbe = (255, 200, 60) if clips[name]["hinweise"] else (230, 230, 230)
        d.text((x0 + 4, y0 + 3), f"{Path(name).stem}  e {v['e']:+.2f} R {v['wr']:+.2f} B {v['wb']:+.2f}", fill=farbe, font=CL.font(14))
        if clips[name]["hinweise"]:
            d.text((x0 + 4, y0 + 21), "; ".join(clips[name]["hinweise"])[:60], fill=farbe, font=CL.font(12))
    bogen.save(HIER / "proto" / "uebersicht_alle_v2.jpg", quality=86)
    print("Bogen ok")


if __name__ == "__main__":
    main()
