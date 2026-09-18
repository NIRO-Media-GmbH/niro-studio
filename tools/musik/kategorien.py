"""Einsatzzweck-Ordner bestimmen und den Bau-Plan schreiben.

Punkte je Ordner aus Artlist-Mood, -Genre, -Video-Theme, Tempo/BPM und den
NIRO-Projekten, in denen der Song lief. Envato-Titel und unklare Quellen kommen
aus data/manuell.json. Ergebnis: data/plan.json.

    venv/bin/python kategorien.py
"""
import collections
import json
import os
import re
import unicodedata

from config import DATA, FORMAT_RANG, KATEGORIEN, UNKLAR

A, B, C, D, E = KATEGORIEN  # Recruiting & Ads, Imagefilm & Corporate, Social Reels & Trends, Event & Aftermovie, Emotional & Testimonial

MOOD = {
    "Exciting": {A: 1.0, D: 0.6}, "Powerful": {A: 1.0, B: 0.4}, "Angry": {A: 0.8, B: 0.2},
    "Uplifting": {A: 0.3, B: 0.4, D: 0.3, E: 0.1}, "Hopeful": {B: 0.5, E: 0.9},
    "Serious": {B: 0.9, A: 0.3}, "Epic": {B: 1.0, A: 0.4}, "Dramatic": {B: 0.9, E: 0.2},
    "Dark": {B: 0.7, A: 0.3}, "Tense": {B: 0.7, A: 0.3}, "Mysterious": {B: 0.8}, "Scary": {B: 0.8},
    "Groovy": {C: 1.0, D: 0.3, A: 0.2}, "Carefree": {C: 0.6, D: 0.6}, "Happy": {C: 0.6, D: 0.7},
    "Playful": {C: 1.0}, "Funny": {C: 1.2}, "Sexy": {C: 0.8, D: 0.2},
    "Love": {E: 1.2}, "Peaceful": {E: 1.2, B: 0.3}, "Sad": {E: 1.4},
}
GENRE = {
    "Rock": {A: 1.0, D: 0.3}, "Pop": {A: 0.5, D: 0.6, C: 0.3}, "Electronic": {A: 0.6, D: 0.6, B: 0.2},
    "Hip Hop": {C: 0.9, A: 0.5}, "Funk": {C: 1.0, D: 0.3}, "Cinematic": {B: 0.9, E: 0.3}, "Corporate": {B: 1.0, A: 0.3},
    "Ambient": {B: 0.6, E: 0.6}, "Classical": {B: 0.6, E: 0.6}, "Retro": {C: 0.8, D: 0.3},
    "Indie": {E: 0.5, A: 0.4, C: 0.2}, "World": {D: 0.7, C: 0.3}, "Lofi & Chill Beats": {C: 1.0},
    "Jazz": {C: 0.8, E: 0.2}, "Fantasy": {B: 0.8}, "Folk": {E: 0.9}, "Acoustic": {E: 1.0}, "Blues": {C: 0.6},
    "Children": {C: 1.0}, "Lounge": {C: 0.6, E: 0.3}, "Soul & RnB": {C: 0.5, E: 0.5}, "Holiday": {D: 0.6, C: 0.4},
    "Reggae": {D: 0.7, C: 0.3}, "Country": {E: 0.5, D: 0.3}, "Singer-Songwriter": {E: 1.0}, "Latin": {D: 0.8, C: 0.2},
}
THEMA = {
    "Commercial": {A: 0.6}, "Sport & Fitness": {A: 0.6, D: 0.3}, "Industry": {A: 0.4, B: 0.4},
    "Technology": {B: 0.4, A: 0.3}, "Business": {B: 0.6}, "Documentary": {B: 0.4, E: 0.4},
    "Drone Shots": {B: 0.3}, "Landscape": {B: 0.3, E: 0.2}, "Time-Lapse": {B: 0.3}, "Slow Motion": {B: 0.2, E: 0.2},
    "Trailer": {B: 0.6}, "Urban": {A: 0.2, C: 0.3}, "Road Trip": {A: 0.3, D: 0.3}, "Travel": {D: 0.4},
    "Party": {D: 1.0}, "Weddings": {E: 0.8, D: 0.2}, "Vlog": {C: 0.6}, "Fashion": {C: 0.4}, "Food": {C: 0.4},
    "Lifestyle": {C: 0.3, D: 0.2}, "Shorts": {C: 0.6}, "Gaming": {C: 0.5}, "Education": {B: 0.3, C: 0.2},
    "Medical": {E: 0.5, B: 0.2}, "Nature": {E: 0.3, B: 0.2}, "Intros & Logos": {B: 0.2, C: 0.2}, "Science": {B: 0.3},
}
TEMPO = {"High": {A: 0.4, D: 0.4}, "Low": {E: 0.5, B: 0.2}, "Medium": {}}
ARTLIST_VERSION = re.compile(r"instrumental|no (lead|backing) vocals|no leads|short version|alternative|creative cut|stripped|^under", re.I)
# NIRO-Nutzung: Stichworte im Projekt- bzw. Musik-Unterordner
NUTZUNG = [
    (A, re.compile(r"\bads?\b|recruiting|werbeanzeige|funnel|ad dreh|onboarding|quiz", re.I)),
    (B, re.compile(r"imagefilm|\bimage\b|erklärvideo|wartezimmer|gewerbedach|dachreinigung", re.I)),
    (C, re.compile(r"reels?|tiktok|content|social|instagram|youtube|kamera reden", re.I)),
    (D, re.compile(r"aftermovie|sommerfest|workation|messe|showreel|skiausflug|hochzeit", re.I)),
    (E, re.compile(r"testimonial|interview|senioren|selflove|herzen|federleicht", re.I)),
]


# kyrillische Doppelgänger lateinischer Buchstaben (Artlist: "Сrystalline") — sonst findet die Suche nichts
DOPPELGAENGER = str.maketrans("АВЕКМНОРСТХаеорсух", "ABEKMHOPCTXaeopcyx")


def dateiname_sicher(s):
    s = unicodedata.normalize("NFC", s).translate(DOPPELGAENGER)
    s = re.sub(r'[\\/:*?"<>|]', "", s)
    return re.sub(r"\s+", " ", s).strip()


def punkte(meta, fundstellen):
    p = collections.Counter()
    for i, m in enumerate(meta.get("moods", [])):
        for k, w in MOOD.get(m, {}).items():
            p[k] += w * (1.0 if i < 3 else 0.6)
    for i, g in enumerate(meta.get("genres", [])):
        for k, w in GENRE.get(g, {}).items():
            p[k] += w * (1.5 if i == 0 else 1.0)
    for t in meta.get("themen", []):
        for k, w in THEMA.get(t, {}).items():
            p[k] += w * 0.5
    for t in meta.get("tempo", []):
        for k, w in TEMPO.get(t, {}).items():
            p[k] += w
    bpm = meta.get("bpm") or 0
    if bpm >= 120:
        p[A] += 0.3; p[D] += 0.3
    elif 0 < bpm < 90:
        p[B] += 0.2; p[E] += 0.3
    for kat, muster in NUTZUNG:
        projekt_treffer = unterordner_treffer = False
        for f in fundstellen:
            rel = unicodedata.normalize("NFC", f).split("/01_Projekte/", 1)[-1]
            projekt, _, rest = rel.partition("/01_Musik/")
            if rest and muster.search(os.path.dirname(rest)):
                unterordner_treffer = True
            if muster.search(os.path.dirname(projekt)):
                projekt_treffer = True
        p[kat] += 1.5 if unterordner_treffer else (0.8 if projekt_treffer else 0)
    return p


def main():
    inventar = json.load(open(DATA / "inventar.json"))
    treffer = json.load(open(DATA / "artlist_treffer.json"))
    details = json.load(open(DATA / "artlist_details.json"))
    manuell = json.load(open(DATA / "manuell.json")) if (DATA / "manuell.json").exists() else {}

    # gleiche Artlist-ID = gleicher Song (z. B. "Semo - Slam" und "Sémø - Slam"): beste Fassung, Fundstellen vereinen
    nach_id = {}
    for e in inventar:
        t = treffer.get(e["key"], {})
        sid = (t.get("song") or {}).get("songId") if t.get("status") == "treffer" else None
        if sid and sid in nach_id:
            erster = nach_id[sid]
            besser = (FORMAT_RANG.get(e["best"]["ext"], 0), e["best"]["size"]) > (FORMAT_RANG.get(erster["best"]["ext"], 0), erster["best"]["size"])
            if besser:
                erster["best"], erster["key"] = e["best"], e["key"]
            erster["fundstellen"] = sorted(set(erster["fundstellen"]) | set(e["fundstellen"]))
            erster["projekte"] = sorted(set(erster["projekte"]) | set(e["projekte"]))
            e["_doppelt"] = True
        elif sid:
            nach_id[sid] = e

    plan, namen, ausgelassen = [], collections.Counter(), []
    for e in inventar:
        if e.get("_doppelt"):
            continue
        t = treffer.get(e["key"], {})
        s = details.get((t.get("song") or {}).get("songId", ""), {}) if t.get("status") == "treffer" else {}
        m = manuell.get(e["key"], {})
        if e["pruefen"] and not s and not m:
            ausgelassen.append(e["best"]["path"])  # z. B. SFX mit Songnamen im SFX-Ordner
            continue
        tags = e["best"]["tags"]
        eintrag = {
            "key": e["key"], "quelle_pfad": e["best"]["path"], "ext": e["best"]["ext"], "size": e["best"]["size"],
            "dauer": e["best"]["dur"], "fundstellen": e["fundstellen"], "projekte": e["projekte"],
        }
        if s:
            kat = s["kategorien"]
            meta = {
                "quelle": "Artlist", "kuenstler": s["artistName"], "titel": s["songName"], "album": s.get("albumName") or "",
                "genres": kat.get("Genre", []), "moods": kat.get("Mood", []), "instrumente": kat.get("Instrument", []),
                "themen": kat.get("Video Theme", []), "tempo": kat.get("Tempo", []), "bpm": s.get("bpmRate"),
                "url": f"https://artlist.io/royalty-free-music/song/{s['nameForURL']}/{s['songId']}", "id": s["songId"],
            }
        elif m:
            meta = {"genres": [], "moods": [], "instrumente": [], "themen": [], "tempo": [], "bpm": None, "url": "", "id": "", "album": ""}
            meta.update({k: v for k, v in m.items() if k != "kategorie"})
        else:
            # Artlist-Tag oder Artlist-Versionsschema im Namen: Quelle klar, nur nicht mehr im Katalog
            artlist = e["quelle"] == "artlist" or (e["quelle"] == "artlist?" and ARTLIST_VERSION.search(e["version"]))
            # alte Art-list-Downloads tragen Stimmungen/Themen im Genre-Feld
            alt = [x.strip() for x in re.split(r"[,;/]", tags.get("genre", "")) if x.strip()]
            meta = {"quelle": "Artlist" if artlist else "", "kuenstler": tags.get("artist") or e["kuenstler"],
                    "titel": e["titel"] + (f" - {e['version']}" if e["version"] else ""), "album": tags.get("album", ""),
                    "genres": [x for x in alt if x in GENRE], "moods": [x for x in alt if x in MOOD], "instrumente": [],
                    "themen": [x for x in alt if x in THEMA], "tempo": [x for x in alt if x in TEMPO], "bpm": None, "url": "", "id": "",
                    "hinweis": "Nicht mehr im Artlist-Katalog gefunden" if artlist else "Kein Artlist-Treffer, Quelle unklar"}
        eintrag["meta"] = meta

        p = punkte(meta, e["fundstellen"])
        rang = [k for k, _ in p.most_common() if p[k] > 0]
        if m.get("kategorie"):
            eintrag["kategorie"] = m["kategorie"]
        elif meta.get("quelle") in ("Artlist", "Envato Elements") and rang:
            eintrag["kategorie"] = rang[0]
        else:
            eintrag["kategorie"] = UNKLAR
        eintrag["auch"] = [k for k in rang[:3] if k != eintrag["kategorie"]][:2]
        eintrag["punkte"] = {k: round(v, 2) for k, v in p.most_common()}

        if meta.get("quelle") == "Artlist":
            basis = f"{meta['kuenstler']} - {meta['titel']}"
        elif m.get("dateiname"):
            basis = m["dateiname"]
        else:
            basis = re.sub(r"\s*\((\d+)\)$", "", os.path.splitext(os.path.basename(unicodedata.normalize("NFC", e["best"]["path"])))[0])
        basis = dateiname_sicher(basis)
        ziel = f"{eintrag['kategorie']}/{basis}{e['best']['ext']}"
        namen[ziel.lower()] += 1
        if namen[ziel.lower()] > 1:
            ziel = f"{eintrag['kategorie']}/{basis} ({namen[ziel.lower()]}){e['best']['ext']}"
        eintrag["ziel"] = ziel
        plan.append(eintrag)

    json.dump(plan, open(DATA / "plan.json", "w"), ensure_ascii=False, indent=1)
    if ausgelassen:
        print("ausgelassen (kein Musiktreffer):", [os.path.basename(p) for p in ausgelassen])
    verteilung = collections.Counter(x["kategorie"] for x in plan)
    for k in KATEGORIEN + [UNKLAR]:
        groesse = sum(x["size"] for x in plan if x["kategorie"] == k) / 1e9
        print(f"{verteilung[k]:4d}  {groesse:5.1f} GB  {k}")


if __name__ == "__main__":
    main()
