"""SFX-Typ-Ordner bestimmen und den Bau-Plan schreiben.

Punkte je Ordner aus Stichworten im Dateinamen (am stärksten), den kuratierten
Vorlagen-Ordnern (2025 NEW SFX, DaVinci-SFX …) und den Artlist-Kategorien.
Quelle entscheidet über "Unklare Quelle": YouTube-Downloads, Freesound, Pixabay-artige
Namen und Projektdateien ohne jede Herkunft. Songs (Artlist-Musiktreffer) fliegen raus.

    venv/bin/python kategorien.py
"""
import collections
import json
import os
import re
import unicodedata

from config import DATA, KATEGORIEN, UNKLAR

(WHOOSH, IMPACT, RISER, DRONE, GLITCH, UI, ANALOG, INTRO, FOLEY, MENSCH, NATUR, MASCHINE, FEUER, AMBIENCE,
 HORROR, CARTOON) = KATEGORIEN

# Stichworte im Namen: (Ordner, Gewicht, Muster)
STICHWORTE = [
    (WHOOSH, 3, r"whoo?sh|woosh|swoo?sh|swosh|swish|swipe|whip|fly ?by|air move|air puff|zips?\b"),
    (WHOOSH, 1.5, r"transition"),
    (IMPACT, 3, r"impact|\bhits?\b|boom|braam|punch|slam|thud|thump|bass drop|\bdrop\b|stomp|smash|gong|earthquake|bassonator|power down|piou"),
    (RISER, 3, r"riser|\brise\b|rising|build ?up|uplifter|swell|reverse|suckback|tension riser|stutter"),
    (DRONE, 3, r"drone|\bpads?\b|texture|soundscape|scapes?\b"),
    (DRONE, 1.5, r"\bhum\b|atmospher"),
    (GLITCH, 3, r"glitch|digital|\bdata\b|static|interference|distort|electric|sci ?fi|cyber|computer|bitcrush|\bsignal\b|white noise|\btv\b|"
                r"channel surfing|buzz|defect|malfunction|spark|futuris|\bradio\b"),
    (UI, 3, r"\bui\b|click|button|notification|\bpop\b|bleep|beep|blip|\bding\b|chime|message|menu|cursor|select|mouse|keyboard|typing|"
            r"shutter|switch|toggle|error|mistake|confirm|success|access denied|alert|\btext\d|app\b|smartphone|tap\b"),
    (ANALOG, 4, r"film burn|projector|vinyl|record (player|stop|scratch)|scratch|turntable|backspin|\btape\b|cassette|vhs|analog|retro devices"),
    (ANALOG, 2, r"vintage|\banlg\b"),
    (INTRO, 3, r"\bintro\b|\blogo\b|jingle|\bident\b|sting(er)?\b|fanfare|opener|trailer drop|musical|tada|full track|advertise|title reveal|the end\b"),
    (FOLEY, 3, r"\bfoley\b"),
    (FOLEY, 3, r"footsteps?|\bsteps?\b|stepping|sneakers?|\bshoes?\b|\bboots\b|walking|running|\bstones?\b|\brocks?\b|gravel|\bmud\b|\batm\b|"
                 r"\bdoor|cloth|fabric|paper|cutlery|kitchen|\bcup\b|bottle|\bkeys\b|zipper|scissors|pencil|\bpen\b|writing|"
                 r"\bbook\b|\bpage\b|drawer|chair|\bbag\b|\bbox\b|clock|\btick|kettle|shower|knock|creak|latch|asmr|crystals?|\bwood|plastic|"
                 r"rattl|chain|glass|metal(lic)?\b|coins? (drop|count)|cash|money|ratchet|snipping|stitching|pour|liquid"),
    (MENSCH, 3, r"crowd|walla|cheer|applause|laugh|scream|breath|\bkiss|children|\bkids?\b|audience|reaction|\byeah\b|gasp|sigh|giggl|chuckl|smirk|"
                r"woman|female|\bmale\b|\bgirl|\bboy\b|"
                r"cough|choir|vocal|human|chatter|talking|burp|clap(ping)?\b|\bslap"),
    (NATUR, 2, r"\bwater\b|fluid|flow|bubble"),
    (NATUR, 3, r"\brain\b|\bwind\b|thunder|\bstorm\b|ocean|\bsea\b|waves?\b|river|stream|\blake\b|splash|bubble|underwater|\bbirds?\b|"
               r"songbird|forest|nature|leaves|\bsnow\b|\bice\b|animal|\bdog|\bcat\b|horse|insect|cricket|nightingale|blizzard|desert"),
    (MASCHINE, 2, r"machine"),
    (MASCHINE, 3, r"\bcar\b|truck|\blkw\b|\bbus\b|engine|motor|train|bicycle|\bbike\b|biking|cycling|traffic|\bhorn\b|siren|forklift|excavator|drill|\bsaw\b|"
                  r"robot|servo|factory|industrial|industry|workshop|construction|compressor|hydraulic|pneumatic|printer|sewing|conveyor|"
                  r"elevator|aircraft|plane|helicopter|tractor|combine|gate\b|diesel|garage|steam|bmw|opel|vehicle|driving|revving|oximeter"),
    (FEUER, 3, r"\bfire\b|flame|burning|blowtorch|explosion|explode|\bblast\b|\bguns?\b|gunshot|\bshots?\b|rifle|pistol|cannon|sword|blade|"
               r"arrow|\bbomb|grenade|firework|laser|weapon|sizzle"),
    (MENSCH, 2, r"people"),
    (AMBIENCE, 3, r"ambien|\batmo|room tone|office|workplace|\bcity\b|street|restaurant|\bcafe|cafeteria|school|\bbank\b|hospital|emergency room|"
                  r"supermarket|market|harbou?r|warehouse|interior|urban|\bpark\b|village|countryside|area\b"),
    (HORROR, 3, r"horror|creepy|scary|spooky|suspense|eerie|ominous|heartbeat|\bhell\b|monster|ghost|tinnitus|dissonant"),
    (HORROR, 2, r"tension|dramatic"),
    (CARTOON, 3, r"cartoon|funny|comedy|boing|bonk|squeak|\bgame\b|arcade|8 ?bit|coin|\bjump|power ?up|level|pick ?up|minecraft|mario|"
                 r"magic|sparkle|twinkle|anime|ninja|quest|inventory|reward|bouncy|cheerful|positive sound"),
]
STICHWORTE = [(k, w, re.compile(m, re.I)) for k, w, m in STICHWORTE]

# kuratierte Vorlagen-Ordner (Pfadteil → Ordner)
VORLAGEN_ORDNER = [
    (r"/Whoosh/|/Woosh/|Cinematic Whoosh|whoosh-2-", WHOOSH), (r"/Impact/|/hit & impact/|/subwoofer/", IMPACT),
    (r"/Riser/|/riser/", RISER), (r"/Drones/|/drone/", DRONE), (r"/Glitch/", GLITCH),
    (r"/UI/|/Click/|Negative bleeps|/Glass/|/Fluid/", UI), (r"/Film Burn/|film-burn-transition|/DJ Turntable/", ANALOG),
    (r"/Intro/", INTRO), (r"/Positive jingles/", INTRO), (r"ninja-jump", CARTOON), (r"cordless-drill", MASCHINE),
]
VORLAGEN_ORDNER = [(re.compile(m, re.I), k) for m, k in VORLAGEN_ORDNER]

ARTLIST = {
    "Whooshes": {WHOOSH: 2.5}, "Impacts": {IMPACT: 2.5}, "Logos": {INTRO: 2.5},
    "Loops & Phrases": {INTRO: 1.5}, "One Shots": {INTRO: 1.5}, "Vocals": {MENSCH: 1.5},
    "Cartoon": {CARTOON: 2}, "Horror": {HORROR: 2}, "Sci-Fi & Fantasy": {GLITCH: 1, CARTOON: 0.5}, "Technology": {GLITCH: 1.2, UI: 0.8},
    "City": {AMBIENCE: 2}, "Indoor Ambiences": {AMBIENCE: 2}, "Transport Ambience": {AMBIENCE: 1.5, MASCHINE: 0.5},
    "Nature": {NATUR: 2}, "Weather": {NATUR: 2}, "Crowds": {MENSCH: 2},
    "Footsteps": {FOLEY: 2}, "Fashion": {FOLEY: 2}, "Destruction": {FOLEY: 1.5, IMPACT: 0.5},
    "Body Hits & Martial Arts": {IMPACT: 1, FOLEY: 1}, "Voices & Body Sounds": {MENSCH: 2},
    "Animals": {NATUR: 2}, "Elements of Nature": {NATUR: 2}, "Electronics": {UI: 1.5, GLITCH: 0.5}, "Home": {FOLEY: 1.5},
    "Materials": {FOLEY: 1.5}, "Industry & Commercial": {MASCHINE: 1.5, AMBIENCE: 0.3}, "Transport": {MASCHINE: 2},
    "Sports": {MENSCH: 1, FOLEY: 0.5}, "Weapons & Warfare": {FEUER: 2},
}

FREESOUND = re.compile(r"^(\d{4,7}__)?[a-z0-9_.-]+__[\w .-]+$", re.I)
PIXABAY = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*-\d{4,6}$", re.I)
ANBIETER_SCHEMA = re.compile(r"^[^-]+ - .+")


def dateiname_sicher(s):
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r'[\\/:*?"<>|]', "", s)
    return re.sub(r"\s+", " ", s).strip(" .")


def punkte(e, sfx):
    text = " ".join([e["stamm"].replace("_", " ").replace("-", " ")] + ([sfx["songName"], sfx.get("albumName") or ""] if sfx else []))
    p, gruende = collections.Counter(), []
    for kat, w, muster in STICHWORTE:
        if muster.search(text):
            p[kat] += w
            gruende.append(muster.search(text).group(0).lower())
    for muster, kat in VORLAGEN_ORDNER:
        if any(muster.search(unicodedata.normalize("NFC", f)) for f in e["fundstellen"]):
            p[kat] += 1 if "jingles" in muster.pattern else 3.5  # Team-Ordner; "Positive jingles" enthält auch Whooshes
    for c in (sfx or {}).get("sonCategories") or []:
        for kat, w in ARTLIST.get(c["name"].strip(), {}).items():
            p[kat] += w
    if not p:
        p[AMBIENCE if e["best"]["dur"] > 20 else FOLEY] += 0.1  # ohne jedes Signal
    return p, sorted(set(gruende))


def quelle_und_hinweis(e, t):
    stamm, fund = e["stamm"], e["fundstellen"]
    vorlage = any("/03_Vorlagen und Tools/" in unicodedata.normalize("NFC", f) for f in fund)
    if t.get("status") == "treffer":
        return "Artlist", "", False
    if e["quelle"] == "YouTube-Download":
        return "YouTube-Download", "YouTube-Download – nicht lizenziert, Lizenz klären", True
    if FREESOUND.match(stamm):
        return "Freesound", "Freesound.org-Download – Lizenz je Datei (CC0/CC BY/CC BY-NC) prüfen", True
    if PIXABAY.match(stamm):
        return "vermutlich Pixabay", "Dateiname im Pixabay-Schema, Quelle nicht bestätigt", True
    if e["quelle"] in ("Envato Elements", "KI-generiert (03_SFX/AI SFX)"):
        return e["quelle"], "", False
    if e["quelle"] == "Artlist" or t.get("status") == "aehnlich":
        return "vermutlich Artlist", "Artlist-Tag bzw. gleichnamiger Artlist-SFX gefunden, nicht eindeutig", False
    if ANBIETER_SCHEMA.match(stamm):
        return "vermutlich Artlist", "Artlist-Namensschema, im Artlist-Katalog nicht gefunden", False
    if vorlage:
        return "NIRO-Vorlagen", "aus 03_Vorlagen und Tools, Herkunft nicht dokumentiert", False
    return "", "Herkunft unbekannt", True


def main():
    inventar = json.load(open(DATA / "inventar.json"))
    treffer = json.load(open(DATA / "artlist_treffer.json"))
    # Handentscheidungen je Dateiname (klein): {"ausschliessen": Grund} oder {"unklar": true, "hinweis": …}
    manuell = {k.lower(): v for k, v in json.load(open(DATA / "manuell.json")).items()} if (DATA / "manuell.json").exists() else {}
    plan, songs, namen, ausgelassen = [], [], collections.Counter(), []
    for e in inventar:
        m_hand = manuell.get(e["stamm"].lower(), {})
        if m_hand.get("ausschliessen"):
            ausgelassen.append(f"{e['stamm']} ({m_hand['ausschliessen']})")
            continue
        t = treffer.get(e["key"], {})
        if t.get("status") == "song":
            songs.append({"path": e["best"]["path"], "song": t["song"]})
            continue
        sfx = t.get("sfx") if t.get("status") in ("treffer", "aehnlich") else None
        quelle, hinweis, unklar = quelle_und_hinweis(e, t)
        if m_hand.get("unklar"):
            unklar, hinweis = True, m_hand.get("hinweis", hinweis)
        p, stichworte = punkte(e, sfx)
        rang = [k for k, v in p.most_common() if v > 0]
        kategorie = UNKLAR if unklar else rang[0]
        teile = [x.strip() for x in e["stamm"].split(" - ")]
        meta = {
            "quelle": quelle, "hinweis": hinweis,
            "name": (sfx["songName"] if t.get("status") == "treffer" else e["stamm"]),
            "anbieter": (sfx["artistName"] if t.get("status") == "treffer" else (teile[0] if quelle == "vermutlich Artlist" and len(teile) > 1 else "")),
            "pack": (sfx.get("albumName") or "") if t.get("status") == "treffer" else "",
            "artlist_kategorien": [f"{c['parentName']}/{c['name'].strip()}" for c in (sfx or {}).get("sonCategories") or []],
            "stichworte": stichworte,
            "url": f"https://artlist.io/sfx/track/{sfx['nameForURL']}/{sfx['songId']}" if t.get("status") == "treffer" else "",
            "id": sfx["songId"] if t.get("status") == "treffer" else "",
        }
        basis = dateiname_sicher(e["stamm"])
        ziel = f"{kategorie}/{basis}{e['best']['ext']}"
        namen[ziel.lower()] += 1
        if namen[ziel.lower()] > 1:  # gleichnamige, aber verschiedene SFX (z. B. "Cinematic Whoosh")
            ziel = f"{kategorie}/{basis} ({namen[ziel.lower()]}){e['best']['ext']}"
        plan.append({"key": e["key"], "quelle_pfad": e["best"]["path"], "ext": e["best"]["ext"], "size": e["best"]["size"],
                     "dauer": e["best"]["dur"], "fundstellen": e["fundstellen"], "projekte": e["projekte"], "meta": meta,
                     "kategorie": kategorie, "typ": rang[0], "auch": [k for k in rang[:3] if k != kategorie][:2],
                     "punkte": {k: round(v, 2) for k, v in p.most_common()}, "ziel": ziel})

    json.dump(plan, open(DATA / "plan.json", "w"), ensure_ascii=False, indent=1)
    json.dump(songs, open(DATA / "songs_gefunden.json", "w"), ensure_ascii=False, indent=1)
    verteilung = collections.Counter(x["kategorie"] for x in plan)
    for k in KATEGORIEN + [UNKLAR]:
        print(f"{verteilung[k]:4d}  {sum(x['size'] for x in plan if x['kategorie'] == k) / 1e6:7.0f} MB  {k}")
    print(f"{len(plan)} SFX; {len(songs)} Songs aussortiert: {[os.path.basename(s['path']) for s in songs]}")
    print(f"von Hand ausgelassen: {ausgelassen}")


if __name__ == "__main__":
    main()
