"""Replay-Kommentare lesen und aufbereiten (Spec 2026-09-16 Abschnitt 2.4): aus Resolve-Markern (Merkmal
„FrameIO") oder aus der Chrome-Lesung, Clips an der Stelle, Veränderung seit dem Upload, neu/bekannt, fremde
Autoren, Bericht ``kommentare.md``. Ohne Resolve.
"""
from __future__ import annotations

import math
import unicodedata

from .charge import AutoCutError


def _frame(key) -> int:
    return int(round(float(key)))


def _nummerieren(kommentare: list[dict]) -> list[dict]:
    kommentare.sort(key=lambda k: (k["frame"], k["text"]))
    for i, k in enumerate(kommentare, start=1):
        k["nr"] = i
    return kommentare


def aus_markern(marker: dict, merkmal: dict | None, vorher: dict | None = None) -> list[dict]:
    """``read_timeline()["markers"]`` (Frame → Info) → Kommentare, sortiert nach Frame.

    Mit ``merkmal`` (z. B. {"color": "FrameIO"}) zählen nur passende Marker. Marker, die unverändert schon im
    Upload-Schnappschuss (``vorher``) lagen, zählen nie — AutoCut-Beat-Marker ebenso wie übernommene Replay-Marker
    einer Kopie."""
    vorher = {str(_frame(k)): v for k, v in (vorher or {}).items()}
    out = []
    for k, m in (marker or {}).items():
        if not isinstance(m, dict):
            continue
        f = _frame(k)
        if merkmal and any(m.get(feld) != wert for feld, wert in merkmal.items()):
            continue
        if vorher.get(str(f)) == m:
            continue
        out.append({"frame": f, "dauer_frames": max(1, int(m.get("duration") or 1)),
                    "text": str(m.get("note") or m.get("name") or "").strip(), "autor": None, "antworten": [],
                    "zeichnung": None, "quelle": "api"})
    return _nummerieren(out)


def _zahl(wert) -> bool:
    """Endliche Zahl — JSON erlaubt in Python NaN/Infinity, die sich nicht in Frames umrechnen lassen."""
    return isinstance(wert, (int, float)) and math.isfinite(wert)


def aus_json(daten: dict, fps: float) -> list[dict]:
    """Chrome-Lesung {"quelle": "chrome", "kommentare": [{"von_s", "bis_s", "autor", "text", "antworten",
    "zeichnung"}]} → Kommentare; Sekunden → Frames kaufmännisch gerundet."""
    if not isinstance(daten, dict) or daten.get("quelle") != "chrome" or not isinstance(daten.get("kommentare"), list):
        raise AutoCutError('JSON der Chrome-Lesung braucht {"quelle": "chrome", "kommentare": [...]}.')
    out = []
    for i, k in enumerate(daten["kommentare"], start=1):
        if not isinstance(k, dict) or not _zahl(k.get("von_s")) or not isinstance(k.get("text"), str):
            raise AutoCutError(f"Kommentar {i}: von_s (endliche Zahl) und text (Text) sind Pflicht.")
        if not isinstance(k.get("antworten") or [], list):
            raise AutoCutError(f"Kommentar {i}: antworten muss eine Liste sein (oder fehlen).")
        von = float(k["von_s"])
        bis = k.get("bis_s")
        dauer = max(1, int((float(bis) - von) * fps + 0.5)) if _zahl(bis) and bis > von else 1
        out.append({"frame": int(von * fps + 0.5), "dauer_frames": dauer, "text": k["text"].strip(),
                    "autor": k.get("autor") or None, "antworten": [str(a) for a in (k.get("antworten") or [])],
                    "zeichnung": bool(k["zeichnung"]) if "zeichnung" in k else None, "quelle": "chrome"})
    return _nummerieren(out)


def clips_an(snap: dict, frame: int) -> list[dict]:
    """Items, die das Frame abdecken (auch inaktive): Quell-Frame = quell_in + (frame − start) × tempo/100."""
    out = []
    for spur in sorted(snap.get("spuren") or {}):
        for r in snap["spuren"][spur]:
            if r["start"] <= frame < r["start"] + r["dauer"]:
                tempo = (r.get("tempo") or 100.0) / 100.0
                qf = None if r.get("quell_in") is None else int(r["quell_in"] + round((frame - r["start"]) * tempo))
                out.append({"spur": spur, "name": r.get("name"), "datei": r.get("datei"), "quell_frame": qf,
                            "aktiv": r.get("aktiv", True)})
    return out


def _signatur(snap: dict) -> dict[str, set]:
    return {spur: {(r.get("datei"), r["start"], r["dauer"], r.get("quell_in"), r.get("aktiv", True)) for r in rows}
            for spur, rows in (snap.get("spuren") or {}).items()}


def vergleiche(alt: dict, neu: dict) -> list[str]:
    """Unterschiede je Spur (Datei, Start, Dauer, Quell-In, aktiv) als Textzeilen; leer = gleicher Stand."""
    a, n = _signatur(alt), _signatur(neu)
    zeilen = []
    for spur in sorted(set(a) | set(n)):
        weg, dazu = a.get(spur, set()) - n.get(spur, set()), n.get(spur, set()) - a.get(spur, set())
        if weg or dazu:
            zeilen.append(f"{spur}: {len(weg)} Item(s) geändert/entfernt, {len(dazu)} neu/geändert")
    return zeilen


def frame_im_stand(clips: list[dict], snap: dict) -> int | None:
    """Stelle eines Kommentars im aktuellen Stand über Datei + Quell-Frame; None, wenn nicht eindeutig."""
    kandidaten = set()
    for c in clips:
        if c.get("quell_frame") is None or not c.get("datei"):
            continue
        for r in (snap.get("spuren") or {}).get(c["spur"], []):
            if r.get("datei") != c["datei"] or r.get("quell_in") is None:
                continue
            tempo = (r.get("tempo") or 100.0) / 100.0
            if r["quell_in"] <= c["quell_frame"] < r["quell_in"] + r["dauer"] * tempo:
                kandidaten.add(r["start"] + int(round((c["quell_frame"] - r["quell_in"]) / tempo)))
    return kandidaten.pop() if len(kandidaten) == 1 else None


def _schluessel(k: dict) -> str:
    text = " ".join(unicodedata.normalize("NFC", k.get("text") or "").split())
    return f"{k['frame']}|{text}"


def markiere_neu(kommentare: list[dict], vorher: dict | None, zeit: str) -> int:
    """``neu`` und ``erstmals_gelesen_am`` gegen die bisherige kommentare.json (Schlüssel Frame + Text)."""
    bekannt = {str(k.get("schluessel")): k.get("erstmals_gelesen_am") for k in ((vorher or {}).get("kommentare") or [])}
    n = 0
    for k in kommentare:
        k["schluessel"] = _schluessel(k)
        if k["schluessel"] in bekannt:
            k["neu"], k["erstmals_gelesen_am"] = False, bekannt[k["schluessel"]]
        else:
            k["neu"], k["erstmals_gelesen_am"] = True, zeit
            n += 1
    return n


def markiere_fremde(kommentare: list[dict], eigene: list[str]) -> int:
    """``fremd`` = Autor bekannt und beginnt mit keinem der eigenen Anzeigenamen (ohne Liste: nie fremd)."""
    n = 0
    for k in kommentare:
        autor = k.get("autor")
        k["fremd"] = bool(autor) and bool(eigene) and not any(str(autor).startswith(e) for e in eigene)
        n += int(k["fremd"])
    return n


def _zelle(wert) -> str:
    return str(wert if wert is not None else "–").replace("|", "\\|").replace("\n", " ")


def _ja(wert) -> str:
    return "–" if wert is None else ("ja" if wert else "nein")


def kommentare_md(doc: dict) -> str:
    """Bericht kommentare.md: Kopf + Tabelle Nr | Neu | TC | Autor | Kommentar | Zeichnung | Clips an der Stelle."""
    kopf = [f"# Replay-Kommentare: {doc['titel']}", "",
            f"- Timeline: {doc['timeline']} (Projekt {doc.get('projekt') or '–'})",
            f"- Hochgeladen: {doc.get('hochgeladen_am') or '–'} · Replay-Ordner: {doc.get('replay_ordner') or '–'}",
            f"- Gelesen: {doc['gelesen_am']} über {doc['lese_weg']} · {doc['anzahl']} Kommentare, {doc['neu']} neu, "
            f"{doc['fremd']} von fremden Autoren",
            f"- Seit Upload verändert: {_ja(doc.get('veraendert_seit_upload'))} · seit Bau von Hand geändert: "
            f"{_ja(doc.get('seit_bau_veraendert'))}"]
    kopf += [f"  - {z}" for z in doc.get("aenderungen") or []]
    zeilen = ["", "| Nr | Neu | TC | Autor | Kommentar | Zeichnung | Clips an der Stelle |",
              "|---|---|---|---|---|---|---|"]
    for k in doc["kommentare"]:
        clips = "; ".join(f"{c['spur']} {c.get('name') or '–'} @{'–' if c.get('quell_frame') is None else c['quell_frame']}"
                          for c in k.get("clips") or []) or "–"
        zeilen.append(f"| {k['nr']} | {'ja' if k.get('neu') else '–'} | {k.get('tc') or '–'} | {_zelle(k.get('autor'))} | "
                      f"{_zelle(k.get('text'))} | {_ja(k.get('zeichnung'))} | {_zelle(clips)} |")
    return "\n".join(kopf + zeilen) + "\n"
