"""Frames aus den Proxys ziehen (nur lesen vom NAS), als rohes YUV444 8 bit (.npy) in den Scratchpad."""
import json, os, subprocess, sys
import numpy as np
from concurrent.futures import ThreadPoolExecutor

CHARGE = "/Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09"
AC = f"{CHARGE}/_intern/autocut"
SP = os.path.dirname(os.path.abspath(__file__))
OUT = f"{SP}/frames"
os.makedirs(OUT, exist_ok=True)

media = json.load(open(f"{AC}/media.json"))
sync = json.load(open(f"{AC}/sync.json"))
tl = json.load(open(f"{AC}/timeline.json"))
broll = json.load(open(f"{AC}/broll_auswahl.json"))

PAIRS = {  # Person-Kürzel: (FX3, a7)
    "Ludwig": ("FX3_0222.MP4", "a7MK4_20260908_0118.MP4"),
    "Flammann": ("FX3_0223.MP4", "a7MK4_20260908_0119.MP4"),
    "Hein": ("FX3_0228.MP4", "a7MK4_20260908_0752.MP4"),
}
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
            assert f_a7 == f_fx3 + round(o * 25), (person, f_fx3, f_a7)
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
        jobs.append((proxy_of(fx3_path), (ff - 0.25) / 25, f"{OUT}/{fid}_FX3.npy"))
        jobs.append((proxy_of(a7_path), (fa - 0.25) / 25, f"{OUT}/{fid}_A7.npy"))
        manifest.append({"id": fid, "person": person, "beat": beat, "rec_frame": mid,
                         "FX3": {"clip": fx3, "src_frame": ff, "proxy": proxy_of(fx3_path)},
                         "A7": {"clip": a7, "src_frame": fa, "proxy": proxy_of(a7_path)},
                         "offset_s": o})

# B-Roll: alle 30 Shots (Mitte) klein für die Auswahl
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
