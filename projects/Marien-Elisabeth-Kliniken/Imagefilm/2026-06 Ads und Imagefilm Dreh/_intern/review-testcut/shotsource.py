"""Jede Einstellung des Testcuts ihrem Quellclip zuordnen (Standort-Nachweis).
Bank: Proxys aller B-Roll-Index-Clips, Mavic, Actioncam, KI-Clips, Interviews (FX3+a7) beider Standorte.
Abgleich: CLAHE-Graustufen 256x144, Multi-Scale-Template-Matching (Ausschnitt/Zoom), 2 Frames je Einstellung."""
import json, os, subprocess, sys, time, glob, re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
import numpy as np, cv2
CH = Path("/Users/jansantos/NIRO Studio/projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh")
W = CH / "_intern/review-testcut"; BANK = W / "bank"; BANK.mkdir(exist_ok=True)
MED = Path("/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/Marien-Elisabeth-Kliniken Kassel gGmbH/02_Projekte/01_Projekt-2xAds1xImagefilm_24.06.26/03_Medien")
BW, BH = 256, 144
def entries():
    E = []
    for c in json.load(open(CH/"_intern/autocut/broll_index.json"))["clips"]:
        src = c["proxy"] if c.get("proxy") and os.path.exists(c["proxy"]) else c["path"]
        E.append(dict(key=f"broll_{c['standort'][-1]}_{c['datei']}", path=src, standort=c["standort"], ordner=c["ordner"], datei=c["datei"], fps=2))
    for s in ("Standort 1", "Standort 2"):
        for d, fps in (("Mavic", 2), ("Actioncam", 1)):
            for p in sorted(glob.glob(str(MED/"01_Footage"/s/d/"Proxy"/"*"))):
                E.append(dict(key=f"{d}_{s[-1]}_{Path(p).stem}", path=p, standort=s, ordner=d, datei=Path(p).stem, fps=fps))
        for p in sorted(glob.glob(str(MED/"01_Footage"/s/"Sortiert"/"Interviews"/"*"/"Proxy"/"*"))):
            person = Path(p).parent.parent.name
            E.append(dict(key=f"iv_{s[-1]}_{Path(p).stem}", path=p, standort=s, ordner="Interview " + person, datei=Path(p).stem, fps=0.5))
    for p in sorted(glob.glob(str(MED/"02_Assets"/"06_AI Generiert"/"*.mp4"))):
        E.append(dict(key=f"KI_{Path(p).stem[:18]}", path=p, standort="KI-generiert", ordner="06_AI Generiert", datei=Path(p).name, fps=4))
    return E
def decode(e):
    out = BANK / f"{e['key']}.npy"
    if out.exists(): return e["key"], True
    cmd = ["ffmpeg", "-v", "error", "-i", e["path"], "-vf", f"fps={e['fps']},scale={BW}:{BH}:flags=area,format=gray", "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8)
    if a.size == 0: return e["key"], False
    a = a.reshape(-1, BH, BW)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(4, 4))
    a = np.stack([clahe.apply(x) for x in a])
    np.save(out, a); return e["key"], True
_BANK = None
def _init(meta):
    global _BANK
    _BANK = [(m, np.load(BANK/f"{m['key']}.npy", mmap_mode="r")) for m in meta]
def match(q):
    t, img = q
    scales = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5)
    tmpls = []
    for s in scales:
        w, h = int(round(BW*s)), int(round(BH*s))
        tmpls.append(cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32))
    per_clip = []
    for m, arr in _BANK:
        best = (-1.0, 0, 1.0)
        for j in range(arr.shape[0]):
            f = np.asarray(arr[j], dtype=np.float32)
            for s, tp in zip(scales, tmpls):
                v = cv2.matchTemplate(f, tp, cv2.TM_CCOEFF_NORMED).max()
                if v > best[0]: best = (float(v), j, s)
        per_clip.append((best[0], m["key"], best[1] / m["fps"], best[2]))
    per_clip.sort(reverse=True)
    return t, per_clip[:3]
if __name__ == "__main__":
    E = entries(); print(len(E), "Bank-Clips"); sys.stdout.flush()
    t0 = time.time()
    with ThreadPoolExecutor(10) as ex:
        res = list(ex.map(decode, E))
    ok = {k for k, v in res if v}; meta = [e for e in E if e["key"] in ok]
    json.dump(meta, open(W/"bank_meta.json", "w"), ensure_ascii=False, indent=1)
    nfr = sum(np.load(BANK/f"{m['key']}.npy", mmap_mode="r").shape[0] for m in meta)
    print(f"Bank fertig: {len(meta)} Clips, {nfr} Frames, {time.time()-t0:.0f}s"); sys.stdout.flush()
    cuts = [0.0] + [float(x) for x in open(W/"scenes.txt").read().split()] + [134.28]
    SRC = CH/"Material/Testcut/MEK Test1.mov"
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(4, 4))
    queries = []
    for a, b in zip(cuts[:-1], cuts[1:]):
        if b - a < 0.2: continue
        for frac in (0.35, 0.7):
            t = a + (b - a) * frac
            fr = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(SRC), "-frames:v", "1", "-vf", f"scale={BW}:{BH}:flags=area,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
            img = clahe.apply(np.frombuffer(fr, np.uint8).reshape(BH, BW))
            queries.append((round(t, 2), img))
    print(len(queries), "Abfrage-Frames"); sys.stdout.flush()
    t1 = time.time(); results = {}
    with Pool(14, initializer=_init, initargs=(meta,)) as pool:
        for t, top in pool.imap_unordered(match, queries):
            results[t] = top
    bym = {m["key"]: m for m in meta}
    rows = []
    for (a, b) in zip(cuts[:-1], cuts[1:]):
        qs = [t for t in results if a <= t < b]
        if not qs: continue
        cand = {}
        for t in qs:
            for sc, key, st, zs in results[t]:
                cand.setdefault(key, []).append((sc, st, zs, t))
        key, vals = max(cand.items(), key=lambda kv: (len(kv[1]), max(v[0] for v in kv[1])))
        m = bym[key]; best = max(vals)
        second = sorted({k: max(v)[0] for k, v in cand.items() if k != key}.items(), key=lambda kv: -kv[1])[:1]
        rows.append(dict(von=a, bis=b, key=key, standort=m["standort"], ordner=m["ordner"], datei=m["datei"], score=round(best[0], 3), quellzeit=round(best[1], 1), zoom=round(1/best[2], 2), treffer=len(vals), zweitbester=(second[0][0], round(second[0][1], 3)) if second else None))
    json.dump(rows, open(W/"shotsource.json", "w"), ensure_ascii=False, indent=1)
    for r in rows:
        print(f"{r['von']:6.2f}–{r['bis']:6.2f}  {r['score']:.3f} ({r['treffer']}/2)  {r['standort']:<11} {r['ordner']:<34} {r['datei']:<26} @{r['quellzeit']:6.1f}s  Zoom {r['zoom']}  | 2.: {r['zweitbester']}")
    print(f"Abgleich {time.time()-t1:.0f}s")
