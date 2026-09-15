"""Stufe D: Katalog (Segmente + Bildanalyse) → Sequenzplan 5:00 (8 Tagesbögen) + Reserve.

Aufruf:  sequence_plan.py                    → Plan komplett neu
         sequence_plan.py --swap tausch.json → bestehende plan.json behalten, nur die genannten Slots neu besetzen
Tausch-Datei: [{"block": 5, "slot": 13, "kategorien": [...], "exclude": [ids], "avoid_near": [ids],
               "nur_abend": true, "grund": "..."}]
Ausgabe: <ANALYSE>/katalog.json, <ANALYSE>/plan.json, <SCR>/plan_sheets/block_#.png

Stand 11.09. (User): 80 % Lea & Sebastian (t1), 20 % Jessica & Dominik (t2); 13 Slots je Block (~2,9 s/Shot).
"""
import glob
import json
import os
import sys
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw, ImageFont

CHARGE = "/Users/jansantos/NIRO Studio/projects/AeternaWeddings/Messe-Showreel/2026-09 Hochzeitsmesse"
ANALYSE = f"{CHARGE}/_intern/showreel-analyse"
SCR = "/private/tmp/claude-501/-Users-jansantos-NIRO-Studio/8134ca39-169a-4a0c-8512-9571e81da50f/scratchpad"
TOTAL = 7500
SWAP = sys.argv[sys.argv.index("--swap") + 1] if "--swap" in sys.argv else None

# Slot-Vorlage: (Name, erlaubte Kategorien in Präferenz, Frames) — 13 Slots = 937 Frames je Block
TEMPLATE = [
    ("Location/Drohne", ["location"], 88),
    ("Details", ["details", "getting_ready"], 70),
    ("Getting Ready", ["getting_ready", "details"], 70),
    ("Trauung", ["trauung", "trauung_moment"], 75),
    ("Emotion Gäste", ["emotion_gaeste", "gratulation_feier"], 70),
    ("Trauung-Moment", ["trauung_moment", "trauung"], 75),
    ("Paar", ["paar"], 88),
    ("Gratulation/Feier", ["gratulation_feier", "emotion_gaeste", "reden_dinner"], 70),
    ("Paar", ["paar"], 75),
    ("Feier/Reden/Dinner", ["reden_dinner", "gratulation_feier", "details"], 70),
    ("Abend/Lichter", ["party", "abend_lichter", "reden_dinner"], 91),  # User 11.09.: mehr Party im Abendteil
    ("Party", ["party"], 57),
    ("Party/Tanz", ["party"], 38),  # kurzer, schneller Blockschluss – Lea-Party-Shots sind kurz geschnitten
]
assert sum(t[2] for t in TEMPLATE) == 937
NAMES = [t[0] for t in TEMPLATE]
EVENING_START = NAMES.index("Abend/Lichter")
FIRST_PAAR = NAMES.index("Paar")
PAAR_FOCUS_SLOTS = {i for i, n in enumerate(NAMES) if n in ("Paar", "Party/Tanz")}
BLOCKS = 8
# t2-Slots (1-basiert), auf kürzere Positionen gelegt → ~80 % Lea nach Zeit und Anzahl:
# ungerade Blöcke Details · zweiter Paar-Slot · Party, gerade Blöcke Location · Party (nie zwei t2 hintereinander)
T2_SLOTS = {1: {2, 9, 12}, 0: {1, 12}}
ODD = ["t2" if s in T2_SLOTS[1] else "t1" for s in range(1, len(TEMPLATE) + 1)]
EVEN = ["t2" if s in T2_SLOTS[0] else "t1" for s in range(1, len(TEMPLATE) + 1)]
T2_MAX = 22  # Obergrenze t2-Shots tagsüber (User 11.09.: mehr Party → Lea-Anteil darf auf ~70 % sinken)
# Tagesphasen: Ersatz-Kategorien ab Stufe 2 nur aus der eigenen Phase, ab Stufe 6 auch aus Nachbarphasen
PHASES = [["location", "details", "getting_ready"],                         # Morgen (Slots 1–3)
          ["trauung", "trauung_moment", "emotion_gaeste"],                  # Trauung (Slots 4–6)
          ["paar", "gratulation_feier", "reden_dinner", "emotion_gaeste"],  # Paar & Feier (Slots 7–10)
          ["abend_lichter", "party", "reden_dinner"]]                       # Abend (Slots 11–13)
PHASE_OF = [0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3]
assert len(PHASE_OF) == len(TEMPLATE)
BLOCK_ORDER = [1, 8, 2, 7, 3, 6, 4, 5]  # beste Shots gleichmäßig über den Loop verteilen
HARD_FLAGS = {"text_im_bild", "grafik", "uebergang", "sw_effekt", "unscharf_sichtbar"}
EXCLUDE = {  # manuelle Sperren nach Sichtung der Prüfbögen
    "t2-155": "Autokennzeichen lesbar",
    "t2-078": "Autokennzeichen evtl. lesbar (Kolonne)",
    "t2-082": "Autokennzeichen evtl. lesbar (Auto-Detail)",
    "t2-081": "parkende Autos, Kennzeichen in 4K evtl. lesbar",
    "t1-250": "Überblendung/Doppelbelichtung im Fenster",
    "t1-003": "Überblendung in Getting-Ready-Montage (verwischtes Doppelbild)",
    "t1-313": "Anfangs-/Endbild verschiedene Personen → vermutlich Schnitt im Fenster",
}
COLORS = {"location": "Teal", "details": "Beige", "getting_ready": "Apricot", "trauung": "Yellow",
          "trauung_moment": "Orange", "emotion_gaeste": "Pink", "paar": "Violet", "gratulation_feier": "Lime",
          "reden_dinner": "Olive", "abend_lichter": "Navy", "party": "Purple"}
SCENE_SEC = 12                                   # derselbe Moment: ±12 s Quellzeit
SCENE_LIMIT = {"t1": 3, "t2": 2}                 # max. Shots je Moment im ganzen Loop
KEYWORD_CAPS = {"eröffnungstanz": 8, "tort": 2}  # Motiv-Deckel (aus Bildanalyse-Text), je max. 1 pro Block

segments = {s["id"]: s for s in json.load(open(f"{ANALYSE}/segments.json"))}
if os.path.exists(f"{ANALYSE}/segments_override.json"):  # zurückgeholte kurze Party-Shots (Strobo ≠ weiche Blende)
    for s in json.load(open(f"{ANALYSE}/segments_override.json")):
        segments[s["id"]] = s
if os.path.exists(f"{ANALYSE}/segments_sub.json"):  # Montage-Segmente mit weichen Blenden, in Einstellungen zerlegt
    for s in json.load(open(f"{ANALYSE}/segments_sub.json")):
        segments[s["id"]] = s
        if s["parent"] in segments:
            segments[s["parent"]] = {**segments[s["parent"]], "tech_flags": ["zerlegt"]}
vision = {}
for p in sorted(glob.glob(f"{SCR}/vision/results_*.json") + glob.glob(f"{SCR}/vision_sub/results_*.json")
                + glob.glob(f"{SCR}/vision_party/results_*.json")):
    for v in json.load(open(p)):
        vision[v["id"]] = v
# User-Löschungen in v2 (11.09.): nie wieder verwenden, gleiche Momente/sehr ähnliche Bilder abwerten
USER_DELETED = set()  # alle Lösch-Runden des Users (v2, v4, v5 …) – nur die konkreten Shots, nicht die Szenen
for _f in sorted(glob.glob(f"{ANALYSE}/v*_user_*.json")):
    USER_DELETED |= set(json.load(open(_f))["deleted_ids"])
DELETED_REF = [e for e in json.load(open(f"{ANALYSE}/plan_v2_80-20.json"))["showreel"]
               if e["id"] in USER_DELETED] if USER_DELETED else []
missing = [i for i, s in segments.items() if not s["tech_flags"] and i not in vision]
print("Segmente:", len(segments), "| mit Bildanalyse:", len(vision), "| Analyse fehlt:", len(missing), missing[:10])

samples = {f: np.load(f"{ANALYSE}/{f}-samples.npy") for f in ("t1", "t2")}
rgb = {f: np.load(f"{ANALYSE}/{f}-rgb.npy") for f in ("t1", "t2")}  # mittleres RGB je Sample
zsmall = {}
for f in ("t1", "t2"):
    sm = np.load(f"{ANALYSE}/{f}-small.npy").astype(np.float32)
    mu, sd = sm.mean(axis=(1, 2), keepdims=True), sm.std(axis=(1, 2), keepdims=True) + 1e-6
    zsmall[f] = ((sm - mu) / sd).reshape(len(sm), -1)

# Katalog + Schärfe-Perzentil je Film×Kategorie
katalog = []
for sid, s in segments.items():
    v = vision.get(sid)
    if s["tech_flags"] or not v or v["kategorie"] == "unbrauchbar" or sid in EXCLUDE or sid in USER_DELETED:
        continue
    if HARD_FLAGS & set(v.get("flags") or []) or v["wert"] <= 2:
        continue
    katalog.append({**s, **{k: v.get(k) for k in ("kategorie", "einstellung", "paar_im_fokus", "tageszeit",
                                                   "wert", "motiv")},
                    "flags": v.get("flags") or [], "bester_frame": v.get("bester_frame", 2)})
groups = {}
for k in katalog:
    groups.setdefault((k["film"], k["kategorie"]), []).append(k)
for g in groups.values():
    vals = sorted(x["sharp_c_med"] for x in g)
    for x in g:
        x["sharp_pct"] = (vals.index(x["sharp_c_med"]) + 0.5) / len(vals)
motion_p95 = {f: float(np.percentile([k["motion_max"] for k in katalog if k["film"] == f], 95)) for f in ("t1", "t2")}
kat_by_id = {k["id"]: k for k in katalog}
for k in katalog:  # User 11.09.: gelöscht wurden nur die konkreten Shots, nicht die Szenen → kein Abzug für Nähe
    k["del_pen"] = 0
json.dump(katalog, open(f"{ANALYSE}/katalog.json", "w"), ensure_ascii=False, indent=1)
print("Katalog:", len(katalog), dict(Counter((k["film"], k["kategorie"]) for k in katalog)))


def base_score(k, slot_idx):
    sc = k["wert"] * 10 + k["sharp_pct"] * 4 - k.get("del_pen", 0)
    if k["motion_max"] > motion_p95[k["film"]]:
        sc -= 4
    if "szenenwechsel" in k["flags"]:
        sc -= 6
    if "kind_im_fokus" in k["flags"] or "unvorteilhaft" in k["flags"]:
        sc -= 5
    if slot_idx in PAAR_FOCUS_SLOTS and k["paar_im_fokus"]:
        sc += 3
    if slot_idx == 0 and k["einstellung"] == "totale":
        sc += 3
    if slot_idx == EVENING_START:
        sc += 4 if k["tageszeit"] == "abend" else -10
    elif slot_idx > EVENING_START and k["tageszeit"] == "tag":
        sc -= 15  # Party-Teil: Tagesbilder nur als allerletzter Ausweg
    if slot_idx < EVENING_START and k["tageszeit"] == "abend" and k["kategorie"] != "paar":
        sc -= 3
    return sc


_win_cache = {}


def best_window(k, length):
    """Bestes Fenster der Länge `length`: scharf, ruhig, nahe am besten Frame; ohne Blende, Farbblitz,
    Kipp-Inhalt oder Überqueren unsicherer Schnitte. None, wenn keins passt."""
    key = (k["id"], length)
    if key in _win_cache:
        return _win_cache[key]
    lo = k["src_start"] + k.get("edge_in", 12)
    hi = k["src_end"] - k.get("edge_out", 12) - length
    focus = k["src_start"] + {1: 0.2, 2: 0.5, 3: 0.8}.get(k.get("bester_frame"), 0.5) * k["frames"]
    if "szenenwechsel" in k["flags"]:
        lo, hi = max(lo, int(focus - 40 - length / 2)), min(hi, int(focus + 40 - length / 2))
    res = None
    if hi >= lo:
        S, Z = samples[k["film"]], zsmall[k["film"]]
        best, best_sc = None, -1e9
        for start in range(lo, hi + 1, 5):
            i0, i1 = int(np.ceil(start / 5)), int((start + length - 1) // 5)
            rows = S[i0:i1 + 1]
            if len(rows) == 0:
                continue
            crossing = [c for c in k.get("internal_cuts", []) if start < c[0] < start + length and not c[2]]
            if any(c[1] < 0.9 for c in crossing):
                continue  # möglicher echter Schnitt → nur Blitz-Fehlschnitte und sehr sichere überqueren
            if rows[:, 1].min() < max(8.0, 0.4 * k["luma_med"]):
                continue  # Blende/Schwarz im Fenster
            cont = (Z[i0:i1 + 1] @ Z[(i0 + i1) // 2]) / Z.shape[1]
            if cont.min() < (0.6 if k["luma_med"] < 50 else 0.45):
                continue  # Inhalt kippt → unerkannte Überblendung/Schnitt (dunkle Szenen strenger: Rauschen)
            w = rgb[k["film"]][i0:i1 + 1]
            chrom = w - w.mean(axis=1, keepdims=True)
            if float(np.abs(chrom - np.median(chrom, axis=0)).max()) > (60 if k["kategorie"] == "party" else 25):
                continue  # Farbblitz/Light-Leak-Übergang (kalibriert: t1-161 = 71, übrige Nicht-Party < 17)
            sc = float(np.median(rows[:, 3])) / (k["sharp_c_med"] + 1e-6) - 0.02 * float(rows[:, 6].max())
            sc -= 0.3 * abs(start + length / 2 - focus) / max(25.0, k["frames"] / 2)
            if sc > best_sc:
                best, best_sc = start, sc
        if best is not None:
            i0, i1 = int(np.ceil(best / 5)), int((best + length - 1) // 5)
            res = {"src_in": int(best), "src_out": int(best + length),
                   "jump_corr": round(float(Z[i0] @ Z[i1] / Z.shape[1]), 2)}
    _win_cache[key] = res
    return res


plan = {b: [None] * len(TEMPLATE) for b in range(1, BLOCKS + 1)}
used = set()
warnings = []


def near(k, other, sec):
    return k["film"] == other["film"] and abs(k["src_start"] - other["src_start"]) < sec * 25


def block_neighbors(b):
    return {b, (b % BLOCKS) + 1, ((b - 2) % BLOCKS) + 1}


def caps_ok(k, b, all_taken):
    if (sum(1 for p in all_taken if near(k, p, SCENE_SEC)) >= SCENE_LIMIT[k["film"]]
            or any(near(k, p, SCENE_SEC) for p in plan[b] if p)):
        return False
    motiv = (k.get("motiv") or "").lower()
    for kw, cap in KEYWORD_CAPS.items():
        if kw in motiv:
            if sum(1 for p in all_taken if kw in (p.get("motiv") or "").lower()) >= cap:
                return False
            if any(kw in (p.get("motiv") or "").lower() for p in plan[b] if p):
                return False
    return True


def pick(b, i, want, cats_override=None, exclude_ids=frozenset(), avoid_near=(), nur_abend=False):
    """Besten Kandidaten für Block b, Slot i (0-basiert) wählen – alle Regeln, schrittweise gelockert."""
    name, cats, _ = TEMPLATE[i]
    cats = cats_override or cats
    pattern = ODD if b % 2 == 1 else EVEN
    prev = plan[b][i - 1] if i > 0 else None
    nxt = plan[b][i + 1] if i + 1 < len(TEMPLATE) else None  # im Tauschmodus schon besetzt
    taken_nearby = [p for bb in block_neighbors(b) for p in plan[bb] if p]
    all_taken = [p for bb in plan for p in plan[bb] if p]
    t2_count = sum(1 for p in all_taken if p["film"] == "t2")
    t2_cap = T2_MAX + 10 if i >= EVENING_START else T2_MAX  # User 11.09.: mehr Party – Abendteil darf Jessica-Party nutzen
    film_pref = pattern[i] if not (pattern[i] == "t2" and t2_count >= t2_cap) else "t1"
    ph = PHASE_OF[i]
    # Lockerung: 0 alle Regeln · 1 ohne Einstellungswechsel · 2 verwandte Kategorien (Tagesphase) ·
    # 3 anderes Paar erlaubt (t2-Deckel, nie zwei t2 hintereinander) · 4 Nachbarblock 5 s · 5 ohne Deckel ·
    # 6 zusätzlich Nachbarphasen (bevor ein Slot leer bleibt)
    for relax in range(7):
        if relax < 2:
            allowed = cats
        elif relax < 6 or i >= EVENING_START:  # Abendteil: nie auf Tagesbilder ausweichen
            allowed = cats + [c for c in PHASES[ph] if c not in cats]
        else:
            allowed = cats + [c for q in (ph - 1, ph, ph + 1) if 0 <= q < len(PHASES)
                              for c in PHASES[q] if c not in cats]
        cands = []
        for k in katalog:
            if k["id"] in used or k["id"] in exclude_ids or k["kategorie"] not in allowed:
                continue
            if nur_abend and k["tageszeit"] != "abend":
                continue
            if any(near(k, a, SCENE_SEC) for a in avoid_near):
                continue
            if k["film"] != film_pref:
                if relax < 3:
                    continue
                if k["film"] == "t2" and (t2_count >= t2_cap or (i < EVENING_START and (
                        (prev and prev["film"] == "t2") or (nxt and nxt["film"] == "t2")
                        or (not nxt and i + 1 < len(TEMPLATE) and pattern[i + 1] == "t2")))):
                    continue  # tagsüber nie zwei Jessica-Shots hintereinander; Party-Folgen im Abendteil erlaubt
            if any(near(k, p, (15 if k["film"] == "t2" else 10) if relax < 4 else 5) for p in taken_nearby):
                continue
            if any(near(k, p, 3) for p in all_taken):
                continue
            if (prev and near(k, prev, SCENE_SEC)) or (nxt and near(k, nxt, SCENE_SEC)):
                continue  # nie zwei Shots desselben Moments direkt hintereinander (auch nicht gelockert)
            if relax < 5 and not caps_ok(k, b, all_taken):
                continue
            if relax < 1 and any(n and k["einstellung"] == n["einstellung"] for n in (prev, nxt)):
                continue
            if any(n and k["kategorie"] == n["kategorie"] and k["kategorie"] not in ("party",) for n in (prev, nxt)) \
                    and relax < 2:
                continue  # gleiche Kategorie direkt daneben erst ab Stufe 2 (Party-Folgen erlaubt)
            win = best_window(k, want) or (best_window(k, want - 12) if relax >= 2 else None)
            if not win and relax >= 2 and (k["kategorie"] == "paar" or i >= EVENING_START):
                # kurze Einstellungen: Paar (Garten-Montage mit weichen Blenden) bis 1,8 s, Abend/Party bis 1,5 s –
                # der Block gleicht die Länge gleichmäßig über die übrigen Shots aus
                floor, cut = (38, 45) if i >= EVENING_START else (45, 30)
                win = best_window(k, max(floor, want - cut))
            if not win and relax >= 4:
                # späte Ausweichstufe: kurze Einstellung ab 1,6 s in jedem Slot, der Block gleicht aus (Material fast erschöpft)
                win = best_window(k, max(40, want - 45))
            if not win:
                continue
            # Doppel-Motiv (derselbe Moment mehrfach im Film): Mittelbild zu ähnlich zu einem gewählten Shot
            zc = zsmall[k["film"]][(win["src_in"] + win["src_out"]) // 10]
            if any(p["film"] == k["film"] and
                   float(zc @ zsmall[p["film"]][(p["src_in"] + p["src_out"]) // 10]) / zc.shape[0] >= 0.8
                   for p in all_taken):
                continue
            cat_pen = cats.index(k["kategorie"]) * 3 if k["kategorie"] in cats else 12
            cands.append((base_score(k, i) - cat_pen, k, win))
        if cands:
            cands.sort(key=lambda x: -x[0])
            _, k, win = cands[0]
            if relax:
                warnings.append(f"Block {b} Slot {i + 1} ({name}): Regeln gelockert (Stufe {relax})")
            return {"block": b, "slot": i + 1, "slot_name": name, "id": k["id"], "film": k["film"],
                    "paar": k["paar"], "kategorie": k["kategorie"], "einstellung": k["einstellung"],
                    "wert": k["wert"], "motiv": k["motiv"], "src_start": k["src_start"], **win,
                    "frames": win["src_out"] - win["src_in"], "farbe": COLORS[k["kategorie"]],
                    "relax": relax, "alternativen": [c[1]["id"] for c in cands[1:4]]}
    return None


def slot_len(b, i):
    return TEMPLATE[i][2] + (1 if (i == FIRST_PAAR and b % 2 == 1) else 0)


swapped = []
if not SWAP:
    # Slot-weise über alle Blöcke (Schlangen-Reihenfolge) statt Block für Block: knappe Kategorien werden fair
    # auf alle 8 Blöcke verteilt, kein Block bleibt am Ende leer
    carry = {bb: 0 for bb in range(1, BLOCKS + 1)}
    for i, (name, cats, _) in enumerate(TEMPLATE):
        for b in (BLOCK_ORDER if i % 2 == 0 else list(reversed(BLOCK_ORDER))):
            want = slot_len(b, i) + carry[b]
            choice = pick(b, i, want)
            if not choice:
                warnings.append(f"Block {b} Slot {i + 1} ({name}): KEIN Kandidat")
                carry[b] = min(25, want)  # nie ganze Slotlängen weiterschieben – sonst passt danach nichts mehr
                continue
            plan[b][i] = choice
            used.add(choice["id"])
            carry[b] = min(25, want - choice["frames"])
else:
    old = json.load(open(f"{ANALYSE}/plan.json"))
    for p in old["showreel"]:
        plan[p["block"]][p["slot"] - 1] = p
        used.add(p["id"])
    spec = json.load(open(SWAP))
    removed = set()
    for s in spec:
        cur = plan[s["block"]][s["slot"] - 1]
        if s.get("trim") and cur:  # Kürzung des Users übernehmen und fixieren (kein Ausgleich an diesem Shot)
            cur.update({"src_in": s["trim"]["src_in"], "src_out": s["trim"]["src_in"] + s["trim"]["frames"],
                        "frames": s["trim"]["frames"], "fix": True})
            continue
        if cur:
            removed.add(cur["id"])
            plan[s["block"]][s["slot"] - 1] = None
    for s in spec:
        if s.get("trim"):
            continue
        b, i = s["block"], s["slot"] - 1
        if s.get("id") or s.get("ids"):
            # manuelle Wahl (Cutter-Entscheidung): erster Kandidat der Rangliste mit gültigem Fenster –
            # nur Fenster-Wächter, keine Auswahlregeln
            choice = None
            for cid in ([s["id"]] if s.get("id") else []) + s.get("ids", []):
                k = kat_by_id.get(cid)
                if not k or cid in used:
                    continue
                want = s.get("laenge", slot_len(b, i))
                win = best_window(k, want) or best_window(k, want - 12)
                if win:
                    choice = {"block": b, "slot": i + 1, "slot_name": TEMPLATE[i][0], "id": k["id"],
                              "film": k["film"], "paar": k["paar"], "kategorie": k["kategorie"],
                              "einstellung": k["einstellung"], "wert": k["wert"], "motiv": k["motiv"],
                              "src_start": k["src_start"], **win, "frames": win["src_out"] - win["src_in"],
                              "farbe": COLORS[k["kategorie"]], "relax": "manuell", "alternativen": []}
                    break
        else:
            avoid = [kat_by_id[x] for x in s.get("avoid_near", []) if x in kat_by_id]
            choice = pick(b, i, slot_len(b, i), s.get("kategorien"),
                          frozenset(removed | set(s.get("exclude", []))), avoid, s.get("nur_abend", False))
        if not choice:
            warnings.append(f"Tausch Block {b} Slot {i + 1}: KEIN Kandidat ({s.get('grund', '')})")
            continue
        choice["tausch_grund"] = s.get("grund", "")
        plan[b][i] = choice
        used.add(choice["id"])
        swapped.append(choice)
        print(f"Tausch Block {b} Slot {i + 1}: → {choice['id']} ({choice['kategorie']}, W{choice['wert']}, "
              f"Stufe {choice['relax']}) {choice['motiv']} | Grund: {choice['tausch_grund']}")

# Blocklängen exakt, Rhythmus erhalten: überlange Shots (> Slot + 1 s) zuerst zurückschneiden, dann in 5-Frame-
# Schritten gleichmäßig ausgleichen – kürzen am relativ längsten, verlängern am relativ kürzesten Shot (Lea bevorzugt);
# vom User fixierte Längen bleiben unangetastet
def _set_len(p, length):
    w = best_window(kat_by_id[p["id"]], length)
    if w:
        p.update(w)
        p["frames"] = w["src_out"] - w["src_in"]
    return bool(w)


for b in range(1, BLOCKS + 1):
    target = sum(slot_len(b, i) for i in range(len(TEMPLATE)))
    free = [p for p in plan[b] if p and not p.get("fix")]
    for p in free:
        over = p["frames"] - slot_len(b, p["slot"] - 1)
        if over > 25:
            _set_len(p, slot_len(b, p["slot"] - 1) + 25)
    diff = target - sum(p["frames"] for p in plan[b] if p)
    for _ in range(400):
        if diff == 0:
            break
        rel = lambda p: p["frames"] - slot_len(b, p["slot"] - 1)
        moved = False
        if diff < 0:
            for p in sorted(free, key=lambda p: (p["film"] == "t1", -rel(p))):  # Jessica-Shots zuerst kürzen
                d = min(5, -diff)
                if _set_len(p, p["frames"] - d):
                    diff += d
                    moved = True
                    break
        else:
            for p in sorted(free, key=lambda p: (p["film"] != "t1", rel(p))):  # Lea-Shots zuerst verlängern
                if rel(p) >= 50:
                    continue
                d = min(5, diff)
                if _set_len(p, p["frames"] + d):
                    diff -= d
                    moved = True
                    break
        if not moved:
            break
    if diff:
        warnings.append(f"Block {b}: {diff} Frames Abweichung")
seq = [p for b in range(1, BLOCKS + 1) for p in plan[b] if p]
total = sum(p["frames"] for p in seq)

# Reserve: je Kategorie die besten ungenutzten Kandidaten (max. 6), Lea bevorzugt
reserve = []
for cat in COLORS:
    pool = sorted((k for k in katalog if k["kategorie"] == cat and k["id"] not in used),
                  key=lambda k: -(base_score(k, 0) + (6 if k["film"] == "t1" else 0)))
    for k in pool:
        if sum(1 for r in reserve if r["kategorie"] == cat) >= 6:
            break
        win = best_window(k, 57 if cat == "party" else 75) or best_window(k, 40)
        if win:
            reserve.append({"id": k["id"], "film": k["film"], "paar": k["paar"], "kategorie": cat,
                            "einstellung": k["einstellung"], "wert": k["wert"], "motiv": k["motiv"], **win,
                            "frames": win["src_out"] - win["src_in"], "farbe": COLORS[cat]})
frames_by_film = Counter()
for p in seq:
    frames_by_film[p["film"]] += p["frames"]
stats = {"shots": len(seq), "frames": total, "sekunden": total / 25,
         "paar": dict(Counter(p["film"] for p in seq)),
         "lea_anteil_zeit_prozent": round(100 * frames_by_film["t1"] / max(1, total), 1),
         "kategorie": dict(Counter(p["kategorie"] for p in seq)),
         "wert": dict(Counter(p["wert"] for p in seq)), "jump_verdacht": [p["id"] for p in seq if p["jump_corr"] < 0.2],
         "getauscht": [f"B{p['block']} S{p['slot']} {p['id']}" for p in swapped],
         "warnungen": warnings, "reserve": len(reserve)}
json.dump({"stats": stats, "showreel": seq, "reserve": reserve}, open(f"{ANALYSE}/plan.json", "w"),
          ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in stats.items() if k != "warnungen"}, ensure_ascii=False))
print("Warnungen:", len(warnings), [w for w in warnings if "Stufe" not in w])

# Plan-Kontaktbögen je Block (Mitte des Fensters)
out = f"{SCR}/plan_sheets"
os.makedirs(out, exist_ok=True)
font = ImageFont.load_default(size=22)
TW, TH, LAB = 480, 270, 30
for b in range(1, BLOCKS + 1):
    sheet = Image.new("RGB", (TW * 5, (TH + LAB) * 3), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    for i, p in enumerate(plan[b]):
        if not p:
            continue
        x, y = (i % 5) * TW, (i // 5) * (TH + LAB)
        n = int(round((p["src_in"] + p["src_out"]) / 2 / 5))
        img = f"{SCR}/frames/{p['film']}/{n:06d}.jpg"
        if os.path.exists(img):
            sheet.paste(Image.open(img).resize((TW, TH)), (x, y + LAB))
        d.text((x + 6, y + 4), f"{i + 1} {p['kategorie'][:12]} {p['id']} W{p['wert']} {p['frames'] / 25:.1f}s",
               fill=(255, 220, 120), font=font)
    sheet.save(f"{out}/block_{b}.png")
print("Plan-Bögen:", out)
