"""Vorlage (Stand 15.09.2026): Analyse-Frames aus den Proxys ziehen (nur lesen) — zeitgleiche FX3/a7-Paare je Person + B-Roll-Mitten.

Aufruf (im Ordner _intern/color/skripte — alle Analyse-Skripte legen ihre Arbeitsdateien hier ab, frames/ wird ca. 0,5 GB groß;
Python = tools/autocut/venv/bin/python der Studio-Wurzel, von hier aus mit absolutem Pfad aufrufen):
  tools/autocut/venv/bin/python extract.py
Eingaben (_intern/autocut/, AutoCut-Rohschnitt): media.json (clips → proxy.path), sync.json (paare: ref/other/offset_s/ok),
timeline.json (items: track V1 = FX3, V2 = a7, rec_in_f/rec_out_f/src_in_f/beat_nr), broll_auswahl.json (shots: nr, clip,
datei, in_s, out_s). Proxys: Blackmagic Proxy Generator, 1920×1080 (B-Roll: <Ordner des Originals>/Proxy/<Clip>.mov).
Ausgaben: frames/<id>.npy (rohes YUV444 8 Bit, 3×1080×1920, ca. 6 MB je Frame — Paare „<Person>_<n>_FX3/_A7", B-Roll
„BR<nr>_<Clip>"), manifest.json (id, person, beat, rec_frame, FX3/A7: clip, src_frame, proxy, offset_s bzw. broll_nr, clip, t_s …).
Auswahl: je Person bis zu 6 Paare aus V1/V2-Überlappungen ≥ 20 Frames (Mitte der Überlappung), je Beat nur eines, gleichmäßig
verteilt; Sync-Kontrolle a7_frame = fx3_frame + round(offset_s · FPS) (assert). B-Roll: alle Shots der Auswahl (Mitte).
Kette danach: preview.py → lutjpg.py → faces → measure.py → fit.py → sheets.py/compare.py → holdout_extract.py → holdout_eval.py
→ orig_check.py → export_vorschlag.py (Details in den Docstrings). Die Zeile, die jobs und manifest als leere Listen anlegt,
wörtlich so lassen und den Text nirgends davor wiederholen: holdout_extract.py führt alles davor per exec aus.
Herkunft: Taxodia-Session, Scratchpad color/extract.py (Kopie in _intern/color/skripte/extract.py)
"""
import json, os, subprocess, sys
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# ── ANPASSEN je Charge ─────────────────────────────
PAIRS = {  # Person-Kürzel → (FX3-Clip, a7-Clip) mit Endung wie in media.json; Kürzel ohne „BR"-Anfang (Kennung der B-Roll-Frames)
    # "Person A": ("FX3_0001.MP4", "a7MK4_JJJJMMTT_0001.MP4"),
}
FPS = 25  # Bildrate der Interview-Quellen = Timeline in fps (Sync-Kontrolle, Zeitstempel der Frames) — Standard (15.09.)
# ── Ende ANPASSEN ──────────────────────────────────

SP = os.path.dirname(os.path.abspath(__file__))
CHARGE = os.path.dirname(os.path.dirname(os.path.dirname(SP)))  # skripte → color → _intern → Charge
AC = f"{CHARGE}/_intern/autocut"
OUT = f"{SP}/frames"
os.makedirs(OUT, exist_ok=True)

media = json.load(open(f"{AC}/media.json"))
sync = json.load(open(f"{AC}/sync.json"))
tl = json.load(open(f"{AC}/timeline.json"))
broll = json.load(open(f"{AC}/broll_auswahl.json"))

off = {}
for p in sync["paare"]:
    if p["ok"]:
        off[(os.path.basename(p["ref"]), os.path.basename(p["other"]))] = p["offset_s"]

def proxy_of(clip_path):
    return media["clips"][clip_path]["proxy"]["path"]

def grab(path, t, dest):
    if os.path.exists(dest):
        return dest
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", path, "-frames:v", "1", "-an",
           "-f", "rawvideo", "-pix_fmt", "yuv444p", "-"]
    b = subprocess.run(cmd, capture_output=True, check=True).stdout
    a = np.frombuffer(b, np.uint8)
    assert a.size == 1920 * 1080 * 3, (path, t, a.size)
    np.save(dest, a.reshape(3, 1080, 1920))
    return dest

jobs, manifest = [], []
v1 = [i for i in tl["items"] if i["track"] == "V1"]
v2 = [i for i in tl["items"] if i["track"] == "V2"]
for person, (fx3, a7) in PAIRS.items():
    o = off[(fx3, a7)]
    cands = []
    for a in v1:
        if os.path.basename(a["clip"]) != fx3:
            continue
        for b in v2:
            if os.path.basename(b["clip"]) != a7:
                continue
            lo, hi = max(a["rec_in_f"], b["rec_in_f"]), min(a["rec_out_f"], b["rec_out_f"])
            if hi - lo < 20:
                continue
            mid = (lo + hi) // 2
            f_fx3 = a["src_in_f"] + (mid - a["rec_in_f"])
            f_a7 = b["src_in_f"] + (mid - b["rec_in_f"])
            assert f_a7 == f_fx3 + round(o * FPS), (person, f_fx3, f_a7)
            cands.append((mid, f_fx3, f_a7, a["beat_nr"]))
    cands.sort()
    # max. 6, gleichmäßig über die Items verteilt, benachbarte Items desselben Beats nur einmal
    seen, pick = set(), []
    for c in cands:
        if c[3] in seen:
            continue
        seen.add(c[3]); pick.append(c)
    if len(pick) > 6:
        idx = np.linspace(0, len(pick) - 1, 6).round().astype(int)
        pick = [pick[i] for i in idx]
    fx3_path = next(k for k in media["clips"] if os.path.basename(k) == fx3)
    a7_path = next(k for k in media["clips"] if os.path.basename(k) == a7)
    for n, (mid, ff, fa, beat) in enumerate(pick, 1):
        fid = f"{person}_{n}"
        jobs.append((proxy_of(fx3_path), (ff - 0.25) / FPS, f"{OUT}/{fid}_FX3.npy"))
        jobs.append((proxy_of(a7_path), (fa - 0.25) / FPS, f"{OUT}/{fid}_A7.npy"))
        manifest.append({"id": fid, "person": person, "beat": beat, "rec_frame": mid,
                         "FX3": {"clip": fx3, "src_frame": ff, "proxy": proxy_of(fx3_path)},
                         "A7": {"clip": a7, "src_frame": fa, "proxy": proxy_of(a7_path)},
                         "offset_s": o})

# B-Roll: alle Shots der Auswahl (Mitte) klein für die Auswahl der Fit-Shots (preview.py → lutjpg.BR_SEL)
for s in broll["shots"]:
    d = s["datei"]
    px = os.path.join(os.path.dirname(d), "Proxy", os.path.splitext(os.path.basename(d))[0] + ".mov")
    t = (s["in_s"] + s["out_s"]) / 2
    fid = f"BR{s['nr']:02d}_{s['clip']}"
    jobs.append((px, t, f"{OUT}/{fid}.npy"))
    manifest.append({"id": fid, "broll_nr": s["nr"], "clip": s["clip"], "t_s": round(t, 3), "proxy": px,
                     "in_s": s["in_s"], "out_s": s["out_s"]})

with ThreadPoolExecutor(6) as ex:
    list(ex.map(lambda j: grab(*j), jobs))
json.dump(manifest, open(f"{SP}/manifest.json", "w"), ensure_ascii=False, indent=1)
print(len(jobs), "Frames;", sum(1 for m in manifest if "person" in m), "Paare")
for m in manifest:
    if "person" in m:
        print(m["id"], "beat", m["beat"], "FX3", m["FX3"]["src_frame"], "A7", m["A7"]["src_frame"])
