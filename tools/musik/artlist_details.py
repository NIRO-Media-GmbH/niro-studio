"""Artlist-Details: Genre, Mood, Instrument, Video Theme, Tempo und BPM je gefundenem Song.

Liest data/artlist_treffer.json, fragt search-api.artlist.io in 50er-Paketen ab
(songs(ids) mit categories und bpmRate) und schreibt data/artlist_details.json.

    venv/bin/python artlist_details.py
"""
import json
import time
import urllib.request

from artlist import API
from config import DATA

QUERY = ("query Songs($ids: [String!]!) { songs(ids: $ids) { songId songName artistName albumName durationTime "
         "nameForURL bpmRate numberOfStems categories { name parentName } } }")


def hole(ids):
    body = json.dumps({"query": QUERY, "variables": {"ids": ids}}).encode()
    req = urllib.request.Request(API, data=body, method="POST", headers={
        "Content-Type": "application/json", "Origin": "https://artlist.io", "Referer": "https://artlist.io/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0 Safari/537.36"})
    for versuch in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                daten = json.load(r)
            if daten.get("errors"):
                raise RuntimeError(daten["errors"][0]["message"])
            return daten["data"]["songs"]
        except Exception as e:
            letzter = e
            time.sleep(3 + 5 * versuch)
    raise RuntimeError(f"Artlist-Details fehlgeschlagen: {letzter}")


def main():
    treffer = json.load(open(DATA / "artlist_treffer.json"))
    pfad = DATA / "artlist_details.json"
    details = json.load(open(pfad)) if pfad.exists() else {}
    ids = sorted({t["song"]["songId"] for t in treffer.values() if t["song"]} - set(details))
    print(f"{len(ids)} Songs abzufragen ({len(details)} im Cache)")
    for i in range(0, len(ids), 50):
        for s in hole(ids[i:i + 50]):
            gruppen = {}
            for c in s.pop("categories") or []:
                gruppen.setdefault(c["parentName"], []).append(c["name"])
            s["kategorien"] = gruppen
            details[s["songId"]] = s
        time.sleep(0.5)
    json.dump(details, open(pfad, "w"), ensure_ascii=False, indent=1)
    fehlend = [i for i in ids if i not in details]
    print(f"{len(details)} Songs mit Details, {len(fehlend)} ohne Antwort: {fehlend[:10]}")


if __name__ == "__main__":
    main()
