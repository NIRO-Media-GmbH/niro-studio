"""Artlist-Abgleich für SFX: jede Datei im Artlist-SFX-Katalog suchen, bei längeren
Dateien zusätzlich im Musik-Katalog (dann ist es ein Song und gehört nicht in die SFX-Library).

search-api.artlist.io/v2/graphql: sfxList(term, page, sortBy, categoryIds) liefert
Name, Künstler, Pack, Dauer und Artlist-Kategorien (sonCategories: name + parentName).
Artlist-SFX-Dateien heißen "Künstler - [Pack - ]Name.wav"; umbenannte (2025 NEW SFX)
nur "Name.wav" → Treffer dann nur "ähnlich" (Kategorien ja, Quelle/Link nein).

    venv/bin/python artlist.py
"""
import json
import re
import time
import unicodedata
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from config import DATA

API = "https://search-api.artlist.io/v2/graphql"
SFX_QUERY = ('query S($term: String!, $page: Float!) { sfxList(categoryIds: "", page: $page, sortBy: STAFF_PICKS, term: $term) '
             '{ songs { songId songName artistName albumName durationTime nameForURL sonCategories { id name parentName } } } }')
SONG_QUERY = ("query L($term: String) { songList(page: 1, songSortType: STAFF_PICKS, take: 30, vocalType: VOCAL_AND_INSTRUMENTS, "
              "searchTerm: $term) { songs { songId songName artistName durationTime } } }")
KOPF = {"Content-Type": "application/json", "Origin": "https://artlist.io", "Referer": "https://artlist.io/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0 Safari/537.36"}


def normal(s):
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", s or "").lower())


def anfrage(query, variablen):
    body = json.dumps({"query": query, "variables": variablen}).encode()
    for versuch in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(API, data=body, method="POST", headers=KOPF), timeout=30) as r:
                d = json.load(r)
            if d.get("errors"):
                raise RuntimeError(d["errors"][0]["message"])
            return d["data"]
        except Exception as e:
            letzter = e
            time.sleep(2 + 3 * versuch)
    raise RuntimeError(f"Artlist-Anfrage fehlgeschlagen: {letzter}")


def sfx_suche(term):
    return (anfrage(SFX_QUERY, {"term": term, "page": 1}).get("sfxList") or {}).get("songs") or []


def song_suche(term):
    return (anfrage(SONG_QUERY, {"term": term}).get("songList") or {}).get("songs") or []


def bewerte_sfx(e, s):
    """'treffer': Künstler + Name passen (Dauer ±1,5 s); 'aehnlich': nur Name + Dauer; sonst None."""
    stamm = normal(e["stamm"])
    voll = normal(s["artistName"] + s["songName"])
    name = normal(s["songName"])
    kurz = normal(s["songName"].split(" - ")[-1])
    diff = abs((s.get("durationTime") or 0) - e["best"]["dur"])
    if diff > 1.5 and not (e["best"]["dur"] > 30 and diff <= 3):
        return None
    if stamm == voll or (normal(s["artistName"]) and stamm.startswith(normal(s["artistName"])) and stamm.endswith(name)):
        return "treffer"
    if stamm in (name, kurz) and len(stamm) >= 6:
        return "aehnlich"
    return None


def ist_song(e):
    teile = [t.strip() for t in e["stamm"].split(" - ")]
    if len(teile) < 2 or e["best"]["dur"] < 30:
        return None
    for s in song_suche(f"{teile[1]} {teile[0]}"):
        name = normal(s["songName"])
        if normal(s["artistName"]) == normal(teile[0]) and name in (normal(" - ".join(teile[1:])), normal(teile[1])) \
                and abs((s.get("durationTime") or 0) - e["best"]["dur"]) <= 3:
            return s
    return None


def main():
    inventar = json.load(open(DATA / "inventar.json"))
    pfad = DATA / "artlist_treffer.json"
    treffer = json.load(open(pfad)) if pfad.exists() else {}
    offen = [e for e in inventar if e["key"] not in treffer and e["quelle"] not in ("Envato Elements", "YouTube-Download", "KI-generiert (03_SFX/AI SFX)")]
    print(f"{len(offen)} SFX zu suchen ({len(treffer)} im Cache)")

    def pruefe(e):
        teile = [t.strip() for t in e["stamm"].split(" - ")]
        begriffe = [" ".join(teile)]
        if len(teile) >= 3:
            begriffe.append(" ".join(teile[1:]))
        if len(teile) >= 2:
            begriffe.append(teile[-1])
        ergebnis = {"status": "kein", "sfx": None}
        try:
            for b in dict.fromkeys(begriffe):
                kandidaten = sfx_suche(b)
                time.sleep(0.3)
                bewertet = [(bewerte_sfx(e, s), s) for s in kandidaten]
                bester = next((s for st, s in bewertet if st == "treffer"), None)
                if bester:
                    ergebnis = {"status": "treffer", "sfx": bester}
                    break
                aehnlich = next((s for st, s in bewertet if st == "aehnlich"), None)
                if aehnlich and ergebnis["status"] == "kein":
                    ergebnis = {"status": "aehnlich", "sfx": aehnlich}
            if ergebnis["status"] != "treffer":
                song = ist_song(e)
                time.sleep(0.3)
                if song:
                    ergebnis = {"status": "song", "sfx": None, "song": song}
        except RuntimeError as fehler:
            print("  !", e["stamm"], fehler)
            return e, None
        return e, ergebnis

    with ThreadPoolExecutor(2) as ex:  # zwei parallele Anfragen, dazwischen Pausen: schonend für die API
        for i, (e, ergebnis) in enumerate(ex.map(pruefe, offen), 1):
            if ergebnis:
                treffer[e["key"]] = ergebnis
            if i % 50 == 0:
                json.dump(treffer, open(pfad, "w"), ensure_ascii=False, indent=1)
                print(f"  {i}/{len(offen)}", flush=True)
    json.dump(treffer, open(pfad, "w"), ensure_ascii=False, indent=1)
    zaehl = {}
    for t in treffer.values():
        zaehl[t["status"]] = zaehl.get(t["status"], 0) + 1
    print("Ergebnis:", zaehl)


if __name__ == "__main__":
    main()
