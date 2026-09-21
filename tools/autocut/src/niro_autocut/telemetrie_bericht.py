"""Bericht ``Ergebnisse/Rohschnitt/telemetrie.md``: Kopf, Verteilung je Kamera, unruhigste Clips, Clips ohne Daten,
optional Vergleich mit dem B-Roll-Index (Stufe 2b: Brennweite, Perspektive Höhe; Erst-Index: Kamerabewegung ↔ Haltung)."""
from __future__ import annotations

import datetime as _dt
from collections import Counter
from pathlib import Path

from .telemetrie import BEWEGUNGSARTEN, HALTUNGEN, finden

TOP = 25
SCHIEF_AB_GRAD = 2.0


def _de(x, stellen: int = 2) -> str:
    if x is None:
        return "–"
    return f"{x:.{stellen}f}".replace(".", ",")


def _md(s) -> str:
    return str(s if s is not None else "–").replace("|", "\\|")


def _verteilung(tele: list[dict]) -> list[str]:
    zeilen = ["| Kamera | Clips | Quelle rtmd/optisch/keine | Haltung " + "/".join(HALTUNGEN)
              + " | Bewegungsart " + "/".join(BEWEGUNGSARTEN)
              + " | Brennweite weit/normal/tele | Perspektive Augenhöhe/Aufsicht/Untersicht/Vogel |",
              "|---|---|---|---|---|---|---|"]
    for kam in sorted({r.get("kamera") or "unbekannt" for r in tele}):
        rs = [r for r in tele if (r.get("kamera") or "unbekannt") == kam]
        q = Counter(r.get("quelle") for r in rs)
        h = Counter(r.get("haltung") for r in rs)
        b = Counter(r.get("bewegungsart") for r in rs)
        f = Counter(r.get("brennweitenklasse") for r in rs)
        p = Counter(r.get("perspektive_hoehe") for r in rs)
        zeilen.append(f"| {kam} | {len(rs)} | {q['rtmd']}/{q['optisch']}/{q['keine']} | "
                      + "/".join(str(h[x]) for x in HALTUNGEN) + " | "
                      + "/".join(str(b[x]) for x in BEWEGUNGSARTEN)
                      + f" | {f['weit']}/{f['normal']}/{f['tele']} | "
                      f"{p['Augenhöhe']}/{p['Aufsicht']}/{p['Untersicht']}/{p['Vogelperspektive']} |")
    return zeilen


def _unruhigste(tele: list[dict]) -> list[str]:
    zeilen = ["| Clip | Kamera | Ordner | wackeln | bewegung | Haltung | Bewegungsart | ruhige Fenster (s) | Hinweis |",
              "|---|---|---|---|---|---|---|---|---|"]
    ok = [r for r in tele if r.get("wackeln") is not None]
    for r in sorted(ok, key=lambda r: -float(r["wackeln"]))[:TOP]:
        hinweis = []
        roll = r.get("roll_grad")
        if roll is not None and abs(float(roll)) > SCHIEF_AB_GRAD:
            hinweis.append(f"schief {_de(abs(float(roll)), 1)}°")
        if r.get("zoomfahrt"):
            hinweis.append("Zoomfahrt")
        ruhig = r.get("ruhige_fenster") or []
        zeilen.append(f"| {_md(r.get('clip'))} | {_md(r.get('kamera'))} | {_md(r.get('ordner'))} | {_de(r['wackeln'])} | "
                      f"{_de(r.get('bewegung'))} | {_md(r.get('haltung'))} | {_md(r.get('bewegungsart'))} | "
                      f"{', '.join(f'{t:g}' for t in ruhig[:12]) + (' …' if len(ruhig) > 12 else '') or '–'} | "
                      f"{', '.join(hinweis) or '–'} |")
    return zeilen


def vergleich_index(tele: list[dict], index: dict) -> dict:
    """Übereinstimmung Telemetrie ↔ Claude: je Abschnitt Brennweite und Perspektive Höhe (Stufe 2b),
    je Clip Haltung ↔ Kamerabewegung."""
    out = {k: {"n": 0, "gleich": 0, "kreuz": Counter()} for k in ("brennweite", "perspektive_hoehe", "haltung")}
    for c in index.get("clips") or []:
        r = finden(tele, str(c.get("path", "")))
        if not r or r.get("quelle") in (None, "keine"):
            continue
        if r.get("haltung") and c.get("kamerabewegung"):
            v = out["haltung"]
            v["n"] += 1
            v["kreuz"][(r["haltung"], c["kamerabewegung"])] += 1
            v["gleich"] += int((r["haltung"], c["kamerabewegung"]) in {
                ("hand", "Handkamera"), ("gimbal", "Gimbal"), ("stativ", "statisch"),
                ("stativ", "Schwenk"), ("gimbal", "Fahrt"), ("gimbal", "Drohne")})
        for a in c.get("abschnitte") or []:
            if r.get("brennweitenklasse") and a.get("brennweite"):
                v = out["brennweite"]
                v["n"] += 1
                v["kreuz"][(r["brennweitenklasse"], a["brennweite"])] += 1
                v["gleich"] += int(r["brennweitenklasse"] == a["brennweite"])
            if r.get("perspektive_hoehe") and a.get("perspektive_hoehe"):
                v = out["perspektive_hoehe"]
                v["n"] += 1
                v["kreuz"][(r["perspektive_hoehe"], a["perspektive_hoehe"])] += 1
                v["gleich"] += int(r["perspektive_hoehe"] == a["perspektive_hoehe"])
    return out


def _kreuz(titel: str, v: dict, links: str, rechts: str) -> list[str]:
    if not v["n"]:
        return [f"{titel}: keine vergleichbaren Einträge.", ""]
    z = [f"{titel}: {v['gleich']} von {v['n']} gleich ({100 * v['gleich'] / v['n']:.0f} %).", "",
         f"| {links} | {rechts} | Anzahl |", "|---|---|---|"]
    z += [f"| {a} | {b} | {n} |" for (a, b), n in sorted(v["kreuz"].items(), key=lambda kv: -kv[1])]
    return z + [""]


def bericht_md(tele: list[dict], titel: str, index: dict | None = None) -> str:
    q = Counter(r.get("quelle") for r in tele)
    fehler = [r for r in tele if r.get("fehler") or r.get("quelle") in (None, "keine")]
    zeilen = [f"# Kamera-Telemetrie — {titel}", "",
              f"Stand: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M')} · {len(tele)} Clips "
              f"(rtmd {q['rtmd']}, optisch {q['optisch']}, keine {q['keine']}, "
              f"Fehler {sum(1 for r in tele if r.get('fehler'))}). Werte in px @480 je 25-fps-Frame; "
              f"Quelle ``_intern/autocut/telemetrie.json``.", "",
              "## Verteilung je Kamera", ""]
    zeilen += _verteilung(tele) + ["", f"## Unruhigste Clips (bis {TOP}, nach wackeln)", ""] + _unruhigste(tele) + [""]
    unscharf = [(f[4], r.get("clip"), r.get("kamera"), f[0]) for r in tele
                for f in (r.get("fenster") or []) if len(f) > 4 and f[4] is not None]
    if unscharf:
        zeilen += [f"## Unschärfste Fenster (bis {TOP}, relative Schärfe p10; 1,0 = schärfstes Zehntel des Clips)", "",
                   "| Clip | Kamera | Fenster ab (s) | Schärfe |", "|---|---|---|---|"]
        zeilen += [f"| {_md(c)} | {_md(k)} | {t:g} | {_de(v)} |"
                   for v, c, k, t in sorted(unscharf, key=lambda x: x[0])[:TOP]] + [""]
    zeilen += ["## Clips ohne Daten oder mit Fehler", ""]
    zeilen += [f"- {_md(r.get('clip'))} ({_md(r.get('kamera'))}, {_md(r.get('quelle'))}): "
               f"{_md(r.get('fehler') or 'keine Datenspur, optisch nicht gemessen')}"
               for r in fehler] or ["- keine", ""]
    if index:
        v = vergleich_index(tele, index)
        zeilen += ["", "## Vergleich mit dem B-Roll-Index", ""]
        zeilen += _kreuz("Brennweite", v["brennweite"], "Telemetrie", "Claude (2b)")
        zeilen += _kreuz("Perspektive Höhe", v["perspektive_hoehe"], "Telemetrie", "Claude (2b)")
        zeilen += _kreuz("Haltung", v["haltung"], "Telemetrie", "Claude (Erst-Index kamerabewegung)")
    return "\n".join(zeilen).rstrip() + "\n"
