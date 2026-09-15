"""Testcut-Wörter den Interview-Quellclips zuordnen -> Schnittliste (Quelle, In/Out, Versatz) + was innerhalb der Sätze fehlt."""
import json, re, collections
from pathlib import Path
CH = Path("/Users/jansantos/NIRO Studio/projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh")
idx = [r for r in json.load(open(CH/"_intern/transcripts_index.json")) if r.get("kamera_rolle", "ton") == "ton" or r["name"].startswith("FX3")]
def norm(s): return re.sub(r"[^a-zäöüß0-9]", "", s.lower())
FILLER = {"äh", "ähm", "ne", "mhm", "hm", "mmm", "also", "ja", "genau"}
src = {}
for r in idx:
    c = json.load(open(CH/"_intern/cache"/f"{r['fingerprint']}.scribe.json"))
    src[r["name"]] = (r, [(norm(w["text"]), w["start"], w["end"], w["text"]) for w in c["words"] if w["text"].strip() and norm(w["text"])])
gram = collections.defaultdict(list)
for name, (r, ws) in src.items():
    for i in range(len(ws) - 2):
        gram[(ws[i][0], ws[i+1][0], ws[i+2][0])].append((name, i))
cut = [(norm(w["text"]), w["start"], w["end"], w["text"]) for w in json.load(open(CH/"_intern/review-testcut/scribe_testcut.json"))["words"] if w["text"].strip() and norm(w["text"])]
# Kandidaten je Schnittwort: (clip, quellindex) aus allen 3-Grammen, die das Wort enthalten
cand = [collections.Counter() for _ in cut]
for i in range(len(cut) - 2):
    for name, j in gram.get((cut[i][0], cut[i+1][0], cut[i+2][0]), []):
        for k in range(3):
            cand[i+k][(name, j+k)] += 1
assign = []
for i, c in enumerate(cand):
    assign.append(c.most_common(1)[0][0] if c else None)
# Runs mit gleichem Clip und fortlaufendem Index (Lücken im Index = Kürzung)
runs = []
for i, a in enumerate(assign):
    if a is None:
        runs.append({"clip": None, "cut_i": [i]}); continue
    if runs and runs[-1]["clip"] == a[0] and runs[-1]["src_j"][-1] < a[1] <= runs[-1]["src_j"][-1] + 1:
        runs[-1]["cut_i"].append(i); runs[-1]["src_j"].append(a[1])
    else:
        runs.append({"clip": a[0], "cut_i": [i], "src_j": [a[1]]})
# zusammenhängende None-Runs mergen
merged = []
for r in runs:
    if merged and r["clip"] is None and merged[-1]["clip"] is None: merged[-1]["cut_i"] += r["cut_i"]
    else: merged.append(r)
out = []
prev = None
for r in merged:
    a, b = r["cut_i"][0], r["cut_i"][-1]
    text = " ".join(cut[k][3] for k in r["cut_i"])
    if r["clip"] is None:
        line = f"[{cut[a][1]:6.2f}–{cut[b][2]:6.2f}] OHNE QUELLE (VO/Atmo?): {text}"
    else:
        rec, ws = src[r["clip"]]
        ja, jb = r["src_j"][0], r["src_j"][-1]
        person = rec["person"].split("_")[0]
        line = f"[{cut[a][1]:6.2f}–{cut[b][2]:6.2f}] {person:<14} {rec['standort'][-1]} {r['clip']} {ws[ja][1]:7.2f}–{ws[jb][2]:7.2f}  „{text}“"
        if prev and prev["clip"] == r["clip"]:
            pj = prev["src_j"][-1]
            gap = ws[pj+1:ja]
            if gap and 0 < len(gap) < 80:
                line = f"      ↳ im Quellclip dazwischen entfernt ({ws[pj][2]:.2f}–{ws[ja][1]:.2f}): „{' '.join(g[3] for g in gap)}“\n" + line
            elif ja <= pj:
                line = f"      ↳ Rücksprung im Quellclip (Index {pj}→{ja})\n" + line
    out.append(line); prev = r if r["clip"] else prev
txt = "\n".join(out); print(txt)
(CH/"_intern/review-testcut/edl_words.txt").write_text(txt)
json.dump([{"clip": r["clip"], "cut_start": cut[r["cut_i"][0]][1], "cut_end": cut[r["cut_i"][-1]][2],
            "src_start": (src[r["clip"]][1][r["src_j"][0]][1] if r["clip"] else None),
            "src_end": (src[r["clip"]][1][r["src_j"][-1]][2] if r["clip"] else None)} for r in merged],
          open(CH/"_intern/review-testcut/edl_words.json", "w"), ensure_ascii=False, indent=1)
