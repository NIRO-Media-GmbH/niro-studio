"""Artlist-Abgleich (Suche): jeden Song aus dem Inventar im Artlist-Katalog finden.

Nutzt die öffentliche Such-Schnittstelle der Website (search-api.artlist.io),
passt Künstler, Titel, Version und Dauer ab. Ergebnis: data/artlist_treffer.json.
Mood/Instrumente/Video-Themes/BPM holt danach artlist_details.py.

    venv/bin/python artlist.py                  # neue Songs suchen
    venv/bin/python artlist.py --nochmal-kein   # Songs ohne Treffer erneut suchen
    venv/bin/python artlist.py --neu-bewerten   # Status aus gespeicherten Kandidaten neu berechnen
"""
import json
import re
import time
import unicodedata
import urllib.request

from config import DATA

API = "https://search-api.artlist.io/v2/graphql"
FELDER = "songId songName artistName albumName durationTime nameForURL numberOfStems primaryArtists featuredArtists genreCategories { name }"
QUERY = (
    "query SongList($page: Int!, $songSortType: SongSortType!, $take: Int!, $vocalType: VocalType!, $searchTerm: String) {"
    " songList(page: $page, songSortType: $songSortType, take: $take, vocalType: $vocalType, searchTerm: $searchTerm)"
    " { songs { " + FELDER + " versions { " + FELDER + " } } totalResults } }")


def normal(s):
    # Dateinamen verlieren Sonderzeichen ("Flow  Fly" = "Flow & Fly", "Whos That" = "Who's That")
    s = unicodedata.normalize("NFKC", s or "").lower()
    return re.sub(r"[\W_]", "", s)


def suche(begriff, take=30):
    body = json.dumps({"query": QUERY, "variables": {
        "searchTerm": begriff, "take": take, "page": 1,
        "songSortType": "STAFF_PICKS", "vocalType": "VOCAL_AND_INSTRUMENTS"}}).encode()
    req = urllib.request.Request(API, data=body, method="POST", headers={
        "Content-Type": "application/json", "Origin": "https://artlist.io", "Referer": "https://artlist.io/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0 Safari/537.36"})
    for versuch in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                daten = json.load(r)
            songs = daten["data"]["songList"]["songs"]
            flach = []
            for s in songs:
                flach.append(s)
                flach.extend(s.get("versions") or [])
            return flach
        except Exception as e:  # Netz/Rate-Limit: kurz warten, erneut
            letzter = e
            time.sleep(2 + 3 * versuch)
    raise RuntimeError(f"Artlist-Suche fehlgeschlagen für {begriff!r}: {letzter}")


APOSTROPH = {"whos": "who's", "whats": "what's", "cant": "can't", "wont": "won't", "dont": "don't", "im": "I'm",
             "lets": "let's", "its": "it's", "thats": "that's", "youre": "you're", "ive": "I've", "theres": "there's",
             "aint": "ain't", "didnt": "didn't", "isnt": "isn't", "theyre": "they're"}


def mit_apostroph(titel):
    return " ".join(APOSTROPH.get(w.lower(), w) for w in titel.split())


def kuenstler_von(s):
    namen = [s.get("artistName") or ""]
    for feld in ("primaryArtists", "featuredArtists"):
        try:
            namen += [a.get("name", "") for a in json.loads(s.get(feld) or "[]")]
        except (ValueError, AttributeError):
            pass
    return {normal(n) for n in namen if n}


def bewerte(eintrag, s):
    """Punkte: Künstler 4, Titel+Version exakt 6 (nur Titel 4), Dauer bis 3 (Abzug bei Abweichung)."""
    name = s.get("songName") or ""
    basis = name.partition(" - ")[0]
    punkte = 0
    k = normal(eintrag["kuenstler"])
    if k and (k in kuenstler_von(s) or any(k in n or n in k for n in kuenstler_von(s) if len(n) > 3)):
        punkte += 4
    voll = normal(eintrag["titel"] + eintrag["version"])
    titel_ok = voll == normal(name) or normal(eintrag["titel"]) in (normal(basis), normal(name))
    if voll == normal(name):
        punkte += 6
    elif titel_ok:
        punkte += 4
    diff = abs((s.get("durationTime") or 0) - eintrag["best"]["dur"])
    punkte += 3 if diff <= 2.5 else (1 if diff <= 6 else -2)
    return punkte, diff, titel_ok


def status_von(e, rangliste):
    if not rangliste:
        return "kein"
    p, diff, titel_ok = bewerte(e, rangliste[0])
    if p >= 11 or (titel_ok and diff <= 2.5):
        # gleicher Titel + gleiche Dauer genügt: Artlist benennt Künstler um (z. B. Charlie Ryan → Solis)
        return "treffer"
    if p >= 8 and titel_ok:
        return "unsicher"
    return "kein"


def neu_bewerten(inventar, treffer):
    """Status aus den gespeicherten Kandidaten neu berechnen (ohne neue Anfragen)."""
    nach_key = {e["key"]: e for e in inventar}
    for key, t in treffer.items():
        e = nach_key.get(key)
        if not e:
            continue
        rangliste = sorted(t["kandidaten"], key=lambda s: bewerte(e, s)[0], reverse=True)
        t["status"] = status_von(e, rangliste)
        t["song"] = rangliste[0] if t["status"] != "kein" else None


def main():
    inventar = json.load(open(DATA / "inventar.json"))
    pfad = DATA / "artlist_treffer.json"
    treffer = json.load(open(pfad)) if pfad.exists() else {}
    if "--neu-bewerten" in __import__("sys").argv:
        neu_bewerten(inventar, treffer)
        json.dump(treffer, open(pfad, "w"), ensure_ascii=False, indent=1)
        zaehl = {}
        for t in treffer.values():
            zaehl[t["status"]] = zaehl.get(t["status"], 0) + 1
        print("neu bewertet:", zaehl)
        return
    nochmal = "--nochmal-kein" in __import__("sys").argv
    offen = [e for e in inventar if e["quelle"] != "envato"
             and (e["key"] not in treffer or (nochmal and treffer[e["key"]]["status"] != "treffer"))]
    print(f"{len(offen)} Songs zu suchen ({len(treffer)} schon im Cache)")

    for i, e in enumerate(offen, 1):
        begriffe = [f"{e['titel']} {e['kuenstler']}".strip()]
        if e["version"]:
            begriffe.insert(0, f"{e['titel']} {e['version']} {e['kuenstler']}")
        # Die Suche ist satzzeichengenau: Titel aus dem Tag bzw. mit Apostroph ("Whos That" → "Who's That")
        for titel in {(e["best"]["tags"].get("title") or "").split(" - ")[0], mit_apostroph(e["titel"])} - {"", e["titel"]}:
            begriffe.insert(0, f"{titel} {e['kuenstler']}".strip())
        if e["kuenstler"]:
            begriffe += [e["titel"], e["kuenstler"]]
        kandidaten = {}
        for b in begriffe:
            try:
                ergebnisse = suche(b, take=60 if b == e["kuenstler"] else 30)  # API erlaubt max. 60
            except RuntimeError as fehler:
                print("  !", fehler)
                continue
            for s in ergebnisse:
                kandidaten[s["songId"]] = s
            time.sleep(0.35)
            bestes = max(kandidaten.values(), key=lambda s: bewerte(e, s)[0], default=None)
            if bestes and bewerte(e, bestes)[0] >= 11:
                break
        rangliste = sorted(kandidaten.values(), key=lambda s: bewerte(e, s)[0], reverse=True)[:3]
        status = status_von(e, rangliste)
        treffer[e["key"]] = {"status": status, "song": rangliste[0] if status != "kein" else None,
                             "kandidaten": [dict(s, punkte=bewerte(e, s)[0]) for s in rangliste]}
        if i % 25 == 0:
            json.dump(treffer, open(pfad, "w"), ensure_ascii=False, indent=1)
            print(f"  {i}/{len(offen)}")
    json.dump(treffer, open(pfad, "w"), ensure_ascii=False, indent=1)

    zaehl = {}
    for t in treffer.values():
        zaehl[t["status"]] = zaehl.get(t["status"], 0) + 1
    print("Ergebnis:", zaehl)


if __name__ == "__main__":
    main()
