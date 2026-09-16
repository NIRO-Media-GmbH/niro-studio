"""Markdown-Bericht der Kantenprüfung: ``Ergebnisse/Rohschnitt/<video>-kanten.md`` (Spec 2026-09-16, Abschnitt 6)."""
from __future__ import annotations

from .kanten import ARTEN

EINHEIT = {"Schwarzbild": "Mittel", "Schnipsel": "Diff", "Knackser": "×", "Tonloch": "dBFS",
           "Wort angeschnitten": "dB zur Wortspitze"}


def _kz(k: dict | None) -> str:
    if not k or not k.get("n"):
        return "—"
    return f"n {k['n']}, Median {k['median']}, p95 {k['p95']}, Max {k['max']}"


def _kontext_text(x: dict) -> str:
    teile = []
    if x["art"] == "Knackser":
        teile.append(f"Spitze {x.get('spitze')} bei {x.get('versatz_ms')} ms, Kanal {x.get('kanal')}")
    elif x["art"] == "Wort angeschnitten":
        teile.append(f"„{x.get('wort')}“ an der {x.get('seite')}-Kante ({x.get('kante_dbfs')} dBFS), "
                     f"{x.get('spur')} {x.get('clip')}")
    elif x["art"] == "Schnipsel":
        teile.append("an Schnitt" if x.get("an_schnitt") else "ohne Schnitt")
    k = x.get("kontext") or {}
    for key, label in (("bild_schnitt", "Bild-Schnitt"), ("ton_schnitt", "Ton-Schnitt")):
        if k.get(key):
            teile.append(f"{label} {k[key]['abstand']:+d} F")
    items = ", ".join(f"{i['spur']} {i['name']}" for i in (k.get("items") or [])[:4])
    if items:
        teile.append(items)
    return "; ".join(teile).replace("|", "/")


def bericht(erg: dict) -> str:
    ex, sn, um, z = erg["export"], erg["schnappschuss"], erg["umfang"], erg["zaehlung"]
    n = len(erg["befunde"])
    export_zeile = ("- Export: — (`--ohne-export`: nur Wortkanten am Quellton geprüft)" if ex is None else
                    f"- Export: `{ex['datei']}` ({ex['frames']} Frames @ {ex['fps']} fps, {ex['breite']}×{ex['hoehe']}, "
                    f"Ton {'ja' if ex['ton'] else 'nein'})")
    zeilen = [f"# Kantenprüfung — {erg['timeline']}", "", export_zeile,
              f"- Schnappschuss: {sn['quelle']} ({sn['gelesen_am']}, Projekt „{sn['projekt']}“)",
              f"- Umfang: {um['bild_schnitte']} Bild-Schnitte, {um['ton_schnitte']} Ton-Schnitte, "
              f"{um['mit_transkript']} Tonclips mit Transkript, {um['ohne_transkript']} ohne, "
              f"{um.get('ohne_quelle', 0)} ohne erreichbaren Rohclip",
              "", "## Ergebnis", ""]
    if n == 0:
        zeilen.append("**Keine Befunde.**")
    else:
        zeilen.append(f"**{n} {'Befund' if n == 1 else 'Befunde'}** — "
                      + ", ".join(f"{a}: {z[a]}" for a in ARTEN if z.get(a)))
    zeilen.append("")
    if erg.get("hinweise"):
        zeilen += [f"Grafik-Übergänge (nicht als Befund gezählt): {len(erg['hinweise'])} — "
                   + ", ".join(h["timecode"] for h in erg["hinweise"][:40]), ""]
    if um.get("ohne_liste"):
        zeilen += ["Tonclips ohne Transkript (keine Wortprüfung): " + ", ".join(um["ohne_liste"][:12]), ""]
    if um.get("ohne_quelle_liste"):
        zeilen += ["Rohclip nicht erreichbar (keine Wortprüfung, NAS/path_map prüfen): "
                   + ", ".join(um["ohne_quelle_liste"][:12]), ""]
    if n:
        zeilen += ["Befunde sind Verdachtsfälle — erst das Schnittbild ansehen, dann handeln.", "",
                   "| Nr | Art | Timecode | Frames | Wert | Kontext | Bild |", "|---|---|---|---|---|---|---|"]
        for x in erg["befunde"]:
            bild = f"`{x['bild']}`" if x.get("bild") else "—"
            zeilen.append(f"| {x['nr']} | {x['art']} | {x['timecode']} | {x['frames']} | "
                          f"{x['wert']} {EINHEIT[x['art']]} | {_kontext_text(x)} | {bild} |")
        zeilen.append("")
    v = erg.get("verteilung") or {}
    zeilen += ["## Messwerte (Kalibrierung)", ""]
    if "diff" in v:
        zeilen.append(f"- Bild-Diff an Schnitten: {_kz(v['diff'].get('an_schnitten'))} · übrige Frames: "
                      f"{_kz(v['diff'].get('uebrige'))}")
    if "knack_verhaeltnis" in v:
        zeilen.append(f"- Knack-Verhältnis an Ton-Schnitten: {_kz(v['knack_verhaeltnis'])}")
    p = erg.get("parameter") or {}
    zeilen += ["", "Parameter: " + ", ".join(f"{k} {p[k]}" for k in sorted(p)), ""]
    zeilen += [f"- Warnung: {w}" for w in erg.get("warnungen") or []]
    return "\n".join(zeilen).rstrip() + "\n"
