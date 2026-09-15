#!/usr/bin/env python3
"""
Baut aus Transkript + Belegungstabelle die Untertitelseiten für Remotion.

Regeln (mit David abgestimmt, 2026-08-12):
  - Grundposition ist das Mittelband, wo auch die Keyword-Kästen sitzen.
  - Kasten kürzer als 2 s  -> Untertitel pausiert (Seite entfällt).
  - Kasten ab 2 s          -> Untertitel weicht nach unten aus.
  - Hook-Fenster am Anfang -> kein Untertitel (dort steht schon gelber Text).
  - Seiten brechen nie über eine Kastengrenze; sonst würde eine Seite
    mitten im Lauf ihren Zustand wechseln.

Ausgabe: src/clients/lohi-bw/projects/untertitel/captions.ts
"""

import json
import re
import unicodedata
from pathlib import Path

from PIL import ImageFont

CHARGE = Path(__file__).resolve().parents[1]
INTERN = CHARGE / "_intern"
MOTION = Path(__file__).resolve().parents[5] / "tools" / "motion"
FONT_PATH = MOTION / "public" / "clients" / "lohi-bw" / "fonts" / "OpenSans-ExtraBold.ttf"

# --- Layout (Maße im 4K-Frame 2160x3840) ---
FRAME_W, FRAME_H = 2160, 3840
FONT_SIZE = 104
MAX_LINE_PX = 1740          # innerhalb der 5-%-Seitenränder
MAX_WORDS_PER_PAGE = 4
MAX_PAGE_SEC = 2.6
PAUSE_SPLIT_SEC = 0.45      # Sprechpause, an der eine Seite endet

# --- Ausweich-Logik ---
SUB_BAND = (0.44, 0.58)     # was der Untertitel im Normalfall belegt
LONG_BOX_SEC = 2.0          # ab hier weicht der Untertitel aus statt zu pausieren

# --- Verhörer aus Scribe ---
CORRECTIONS = [
    (r"\bLOIBW\b", "LohiBW"),
    (r"\bLoiBW\b", "LohiBW"),
    (r"\bLouis\s+BW\b", "LohiBW"),
    (r"\bLohi\s+BW\b", "LohiBW"),
]
# Füllwörter. Der Vergleich läuft über norm(), das Umlaute zerlegt
# („äh" -> „ah") — die Einträge müssen deshalb in derselben Form
# vorliegen, sonst greift der Filter nicht.
FILLERS = {"ah", "ahm", "oh", "hm", "ahh"}

# --- Dopplungen zu den bestehenden Animationen ---
# David, 12.08.2026: was der Keyword-Kasten inhaltlich schon sagt, gehört
# nicht noch einmal in den Untertitel. Entfernt wird immer die ganze
# Sinneinheit, nie ein Satzfetzen — sonst bleiben Bruchstücke stehen
# („In welcher Steuerkanzlei wirst du" ohne Fortsetzung).
# Die Phrasen greifen NACH den Verhörer-Korrekturen, also mit „LohiBW".
COVERED_BY_BOX = {
    "Video 1 - Der schnellere Weg nach oben.mp4": [
        # „In welcher Steuerkanzlei wirst du" bleibt stehen: sonst startet
        # die Ad fast zwei Sekunden ohne jeden Text. Der Kasten vollendet
        # die Frage („…wirst du" -> FÜHRUNGSKRAFT? -> OHNE EXAMEN).
        ("FÜHRUNGSKRAFT? + OHNE EXAMEN",
         "Führungskraft, ohne vorher das Steuerberaterexamen zu machen?"),
        ("AUFSTIEGSCHANCEN GUT",
         "Ich finde die Aufstiegschancen bei der LohiBW ausgesprochen gut."),
        ("INTERN AUSGESCHRIEBEN",
         "Bei der LohiBW werden frei werdende Beratungsstellen intern "
         "ausgeschrieben."),
        ("JEDER KANN SICH BEWERBEN",
         "Jeder Mitarbeiter kann sich darauf bewerben."),
        # Der Kasten vollendet den Satz; ohne diesen Schnitt endet der
        # Untertitel auf dem Bruchstück „und hast vom".
        ("EINKOMMEN AB TAG 1",
         "und hast vom ersten Tag an ein Einkommen."),
        ("WEG NACH OBEN OFFEN",
         "aber der Weg nach oben, der steht dir wirklich offen."),
    ],
    "Video 2 - Raus aus dem Fristen-Hamsterrad.mp4": [
        # David 13.08.2026: in den ersten drei Sekunden gar kein Untertitel,
        # der Hook trägt den Einstieg allein.
        ("HOOK-TEXT",
         "Wie viele Abende hast du letztes Jahr im Büro verbracht?"),
        # Dritte Animationsart: dunkle Liste („KEINE BUCHHALTUNG / KEINE
        # LOHNABRECHNUNG / KEINE UMSATZSTEUER") bei 27,2–29,8 s. „Das heißt
        # für dich" bleibt als Anmoderation stehen, danach übernimmt die
        # Liste; weiter geht es erst bei „Das heißt nicht, dass…".
        ("DUNKLE LISTE: KEINE BUCHHALTUNG / LOHNABRECHNUNG / UMSATZSTEUER",
         "keine Buchhaltung, keine Lohnabrechnung, keine Umsatzsteuer."),
        ("SEHR VIELE FRISTEN",
         "In einer Steuerkanzlei gibt's eben sehr, sehr viele Fristen, "
         "die man einhalten muss und"),
        # Von den kurzen Kästen zerschnitten; die Reste („als Frist und
        # dadurch ist das") begännen sichtbar mitten im Satz.
        ("NUR EINE FRIST + SEHR ENTSPANNT",
         "als Frist und dadurch ist das Ganze sehr, sehr entspannt."),
        ("FACHLICH GEFORDERT + ABER PLANBAR",
         "Du wirst fachlich gefordert und der Kalender ist voll, aber planbar."),
    ],
    "Video 3 - Wieder mit Menschen arbeiten.mp4": [
        # Der gelbe Hook-Text untertitelt diese Frage bereits.
        ("HOOK-TEXT",
         "Wann hat sich zuletzt jemand bei dir für deine Arbeit bedankt?"),
        # Zwei Kästen hintereinander im selben Fenster: „ÜBER JAHRE
        # BEGLEITET" und „DIE GANZE FAMILIE" — decken den ganzen Satz ab.
        ("ÜBER JAHRE BEGLEITET + DIE GANZE FAMILIE",
         "Manche Mitglieder begleitet man über Jahre, teilweise sogar "
         "die ganze Familie."),
        # Auch hier vollendet der Kasten den Satz — sonst bliebe
        # „gekümmert hat, können" stehen.
        ("KÖNNEN WIR HELFEN",
         "können wir ihnen helfen."),
        ("DANKBARKEIT & WERTSCHÄTZUNG",
         "Und da kommt auch sehr, sehr viel Dankbarkeit und Wertschätzung "
         "bei uns an."),
        # „dann passt du zu uns." bleibt bewusst stehen — als Pointe
        # unter dem Kasten.
        ("MIT MENSCHEN ARBEITEN",
         "Wenn du gern mit Menschen arbeitest und spüren willst, was deine "
         "Arbeit für eine Wirkung hat,"),
    ],
    "Video 4 - Der Steuerjob, der sich nach deinem Leben richtet.mp4": [
        # Hook-Text trägt die Eingangsfrage. „Geht das?" gehört dazu und
        # fliegt auf Davids Wunsch (13.08.2026) mit raus — der Untertitel
        # setzt erst bei „Wenn der Mitarbeiter…" ein.
        ("HOOK-TEXT",
         "Teilzeit in der Steuerberatung, die auch in ein paar Monaten "
         "noch Teilzeit ist. Geht das?"),
        ("FLEXIBEL AUFGESTELLT",
         "Das sind wir schon flexibel aufgestellt."),
        # Enthielt zugleich die ASR-unsichere Stelle „das echt per".
        ("ECHTE ONLINE-BERATUNG",
         "aber das echt per Onlineberatung."),
    ],
}


def strip_covered(words, name):
    """Sinneinheiten entfernen, die der Keyword-Kasten schon abdeckt."""
    removed = []
    for box_label, phrase in COVERED_BY_BOX.get(name, []):
        target = phrase.split()
        hit = None
        for i in range(len(words) - len(target) + 1):
            if [w["text"] for w in words[i:i + len(target)]] == target:
                hit = i
                break
        if hit is None:
            raise SystemExit(
                f"{name}: Phrase für Kasten „{box_label}\" nicht im Transkript "
                f"gefunden:\n    {phrase}\n"
                f"  (Transkript geändert? Dann COVERED_BY_BOX anpassen.)"
            )
        seg = words[hit:hit + len(target)]
        removed.append((box_label, seg[0]["start"], seg[-1]["end"], phrase))
        del words[hit:hit + len(target)]
        # Der Satz endet jetzt hier — ein hängendes Komma sähe aus wie
        # ein Fehler („Dein Einkommen hängt an deinem Einsatz,").
        if hit > 0 and words[hit - 1]["text"].endswith(","):
            words[hit - 1]["text"] = words[hit - 1]["text"][:-1] + "."
    return words, removed


STOPWORDS = {
    "und", "oder", "aber", "dass", "denn", "auch", "noch", "schon", "sehr",
    "eine", "einen", "einem", "eines", "einer", "nicht", "sich", "dich", "mich",
    "dein", "deine", "deinem", "deinen", "mein", "meine", "wird", "wirst",
    "hast", "habe", "haben", "kann", "kannst", "wenn", "dann", "also", "über",
    "unter", "durch", "gibt", "gibts", "ganz", "ganze", "ganzen", "wieder",
    "immer", "meisten", "vielen", "viele", "mehr", "beim", "beim", "vom",
    "dadurch", "darauf", "damit", "heißt", "eben", "halt", "echt", "wirklich",
    "teilweise", "eigentlich", "ausgesprochen", "wahrscheinlich",
}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


# Scribe zerlegt den Markennamen in zwei Tokens ("Louis" + "BW"),
# deshalb muss die Korrektur über Wortgrenzen hinweg greifen.
BRAND_FIRST = {"louis", "loi", "lohi", "loibw", "louisbw", "lohibw"}


def apply_corrections(words):
    out = []
    for w in words:
        t = w["text"]
        for pat, rep in CORRECTIONS:
            t = re.sub(pat, rep, t)
        if norm(t.strip(".,!?")) in FILLERS:
            continue
        out.append({**w, "text": t})

    merged = []
    i = 0
    while i < len(out):
        w = out[i]
        bare = norm(re.sub(r"[^\w]", "", w["text"]))
        nxt = out[i + 1] if i + 1 < len(out) else None
        nxt_bare = norm(re.sub(r"[^\w]", "", nxt["text"])) if nxt else ""
        if bare in BRAND_FIRST and nxt_bare == "bw":
            tail = re.sub(r"[\w]", "", nxt["text"])       # Satzzeichen retten
            merged.append({**w, "text": "LohiBW" + tail, "end": nxt["end"]})
            i += 2
            continue
        if bare in {"loibw", "louisbw", "lohibw"}:
            tail = re.sub(r"[\w]", "", w["text"])
            merged.append({**w, "text": "LohiBW" + tail})
            i += 1
            continue
        merged.append(w)
        i += 1
    return merged


# Animationen, die `analyze_overlays.py` nicht findet, weil es nur nach
# Gelb sucht. Von Hand erfasst und geprüft (13.08.2026).
EXTRA_ANIMATIONS = {
    "Video 2 - Raus aus dem Fristen-Hamsterrad.mp4": [
        # Gestapelte Liste in dunklen Kästen, y 41,6–48,4 %
        {"startSec": 27.24, "endSec": 29.76, "topFrac": 0.416, "botFrac": 0.484},
    ],
}


def clashing_boxes(boxes, name=None):
    """Alles, was das Untertitelband tatsächlich trifft."""
    lo, hi = SUB_BAND
    all_boxes = list(boxes) + EXTRA_ANIMATIONS.get(name, [])
    return [b for b in all_boxes
            if not (b["botFrac"] < lo or b["topFrac"] > hi)]


def build_pages(words, boxes, hook, font, name=None):
    """Wörter zu Seiten gruppieren, Kastengrenzen respektieren."""
    clash = clashing_boxes(boxes, name)
    edges = sorted({b["startSec"] for b in clash} | {b["endSec"] for b in clash})

    def state_of(w):
        """Ein Wort gehört zum Kasten, sobald es ihn überhaupt berührt.

        Nur so kann eine Seite im Normalzustand garantiert nie in einen
        Kasten hineinragen — ein Wort, das über die Grenze läuft, würde
        die Seite sonst mitziehen.
        """
        for b in clash:
            if w["end"] > b["startSec"] and w["start"] < b["endSec"]:
                dur = b["endSec"] - b["startSec"]
                return "hidden" if dur < LONG_BOX_SEC else "shifted"
        return "normal"

    def in_hook(w):
        """Nur Wörter, die überwiegend im Hook-Fenster liegen.

        Ein blosses Anstossen genügt nicht — sonst reisst das Fenster das
        Nachbarwort mit („Abende" endet 0,02 s nach Hook-Beginn und fiele
        sonst mit weg)."""
        if not hook:
            return False
        lo = max(w["start"], hook["hookStartSec"])
        hi = min(w["end"], hook["hookEndSec"])
        if hi <= lo:
            return False
        return (hi - lo) > (w["end"] - w["start"]) * 0.5

    pages, cur = [], []

    def flush():
        nonlocal cur
        if cur:
            pages.append(cur)
            cur = []

    prev_end = None
    for w in words:
        if cur:
            same_state = state_of(cur[0]) == state_of(w)
            same_hook = in_hook(cur[0]) == in_hook(w)
            too_long = w["end"] - cur[0]["start"] > MAX_PAGE_SEC
            gap = prev_end is not None and (w["start"] - prev_end) > PAUSE_SPLIT_SEC
            ends_sentence = bool(re.search(r"[.!?:]$", cur[-1]["text"]))
            if (len(cur) >= MAX_WORDS_PER_PAGE or too_long or gap
                    or ends_sentence or not same_state or not same_hook):
                flush()
        cur.append(w)
        prev_end = w["end"]
    flush()

    # Zustand je Seite, Waisen noch drin
    tagged = [{"words": pg, "mode": state_of(pg[0]),
               "hook": in_hook(pg[0])} for pg in pages]

    hook_edges = ([hook["hookStartSec"], hook["hookEndSec"]] if hook else [])
    tagged = merge_orphans(tagged, edges, hook_edges, font)
    tagged = smooth_shifts(tagged)

    out = []
    for pg in tagged:
        if pg["mode"] == "hidden" or pg["hook"]:
            continue
        out.append({
            "startSec": round(pg["words"][0]["start"], 3),
            "endSec": round(pg["words"][-1]["end"], 3),
            "mode": pg["mode"],
            "lines": wrap(pg["words"], font),
        })
    return hold_pages(out, clash, hook)


HOLD_MAX_SEC = 1.0


def hold_pages(pages, clash, hook):
    """Seite stehen lassen, bis die nächste kommt.

    Sonst blitzen Wortgruppen, die an einer Kastengrenze abgeschnitten
    wurden, nur ein paar Frames lang auf. Die Standzeit endet immer vor
    dem nächsten Sperrfenster.
    """
    blockers = sorted(
        [b["startSec"] for b in clash]
        + ([hook["hookStartSec"]] if hook else [])
    )
    for i, p in enumerate(pages):
        limit = p["endSec"] + HOLD_MAX_SEC
        if i + 1 < len(pages):
            limit = min(limit, pages[i + 1]["startSec"])

        # Erste Sperrgrenze nach dem Seitenbeginn. Sie kappt auch ein
        # bereits überstehendes Ende — ein Wort darf 20 ms in den Hook
        # ragen, die eingeblendete Seite nicht.
        own = blockers if p["mode"] == "normal" else (
            [hook["hookStartSec"]] if hook else [])
        nxt = [b for b in own if b > p["startSec"]]
        if nxt:
            limit = min(limit, nxt[0])
            p["endSec"] = min(p["endSec"], nxt[0])

        p["endSec"] = round(max(p["endSec"], min(limit, p["endSec"] + HOLD_MAX_SEC)), 3)
    # was auch nach der Standzeit zu kurz bleibt, würde nur aufblitzen
    pages = [p for p in pages if p["endSec"] - p["startSec"] >= MIN_PAGE_SEC]
    return capitalize_after_pause(pages)


PAUSE_BEFORE_CAP_SEC = 1.0


def capitalize_after_pause(pages):
    """Seitenanfang nach einer Pause großschreiben.

    Verdeckt ein Kasten das Satzanfangswort, beginnt die nächste Seite
    sonst klein („klick auf den Button" statt „Klick auf den Button")
    und sieht aus wie ein abgeschnittener Satz.
    """
    prev_end = None
    for p in pages:
        gap = None if prev_end is None else p["startSec"] - prev_end
        first = p["lines"][0][0]
        if (gap is None or gap > PAUSE_BEFORE_CAP_SEC) and first["text"][:1].islower():
            first["text"] = first["text"][0].upper() + first["text"][1:]
        prev_end = p["endSec"]
    return pages


ORPHAN_SEC = 0.7
ORPHAN_WORDS = 2
MERGE_MAX_WORDS = 6
MIN_PAGE_SEC = 0.5      # darunter ist eine Seite nicht lesbar, sie entfällt


MAX_LINES = 2


def merge_orphans(tagged, edges, hook_edges, font):
    """Splitter unter 0,7 s in eine benachbarte Seite gleichen Zustands ziehen.

    Die harte Trennung an Kastengrenzen erzeugt sonst Seiten, die nur
    ein bis zwei Frames lang aufblitzen. Eine Zusammenlegung darf aber
    niemals über eine Kastengrenze reichen — sonst stünde der Untertitel
    doch wieder im Kasten.
    """
    def crosses_edge(a_sec, b_sec):
        return any(a_sec < e < b_sec for e in edges)

    changed = True
    while changed:
        changed = False
        for i, pg in enumerate(tagged):
            dur = pg["words"][-1]["end"] - pg["words"][0]["start"]
            if dur >= ORPHAN_SEC and len(pg["words"]) > ORPHAN_WORDS:
                continue
            for j in (i - 1, i + 1):
                if not (0 <= j < len(tagged)):
                    continue
                nb = tagged[j]
                if nb["mode"] != pg["mode"] or nb["hook"] != pg["hook"]:
                    continue
                if len(nb["words"]) + len(pg["words"]) > MERGE_MAX_WORDS:
                    continue
                lo = min(nb["words"][0]["start"], pg["words"][0]["start"])
                hi = max(nb["words"][-1]["end"], pg["words"][-1]["end"])
                # Nur im Normalzustand ist die Kastengrenze bindend —
                # eine ausweichende Seite steht ohnehin ausserhalb des Bandes
                if pg["mode"] == "normal" and crosses_edge(lo, hi):
                    continue
                # Über das Hook-Fenster darf nie zusammengelegt werden:
                # die entstehende Seite stünde sonst über dem Hook-Text,
                # auch wenn keines ihrer Wörter darin liegt.
                if any(lo < e < hi for e in hook_edges):
                    continue
                if hi - lo > MAX_PAGE_SEC:
                    continue
                cand = (nb["words"] + pg["words"] if j < i
                        else pg["words"] + nb["words"])
                if len(wrap(cand, font)) > MAX_LINES:
                    continue
                nb["words"] = cand
                tagged.pop(i)
                changed = True
                break
            if changed:
                break
    return tagged


SHIFT_GAP_SEC = 1.5


def smooth_shifts(tagged):
    """Kurzes Zurückspringen zwischen zwei Ausweich-Phasen unterdrücken."""
    idx = [i for i, p in enumerate(tagged) if p["mode"] == "shifted"]
    for a, b in zip(idx, idx[1:]):
        if b - a < 2:
            continue
        gap = (tagged[b]["words"][0]["start"]
               - tagged[a]["words"][-1]["end"])
        if gap < SHIFT_GAP_SEC and all(
                tagged[k]["mode"] == "normal" for k in range(a + 1, b)):
            for k in range(a + 1, b):
                tagged[k]["mode"] = "shifted"
    return tagged


def wrap(page_words, font):
    """Auf maximal zwei Zeilen umbrechen, nach gemessener Pixelbreite."""
    lines, cur = [], []
    for w in page_words:
        trial = cur + [w]
        text = " ".join(x["text"] for x in trial)
        if cur and font.getlength(text) > MAX_LINE_PX:
            lines.append(cur)
            cur = [w]
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return [[{"text": w["text"], "startSec": round(w["start"], 3),
              "endSec": round(w["end"], 3)} for w in ln] for ln in lines]


def pick_accents(pages, per_video_limit):
    """Höchstens ein gelbes Wort pro Seite, insgesamt sparsam."""
    cands = []
    for pi, pg in enumerate(pages):
        best = None
        for li, ln in enumerate(pg["lines"]):
            for wi, w in enumerate(ln):
                bare = re.sub(r"[^\wäöüÄÖÜß]", "", w["text"])
                if len(bare) < 7 or norm(bare) in STOPWORDS:
                    continue
                if best is None or len(bare) > best[0]:
                    best = (len(bare), li, wi)
        if best:
            cands.append((best[0], pi, best[1], best[2]))
    cands.sort(reverse=True)
    for _, pi, li, wi in cands[:per_video_limit]:
        pages[pi]["lines"][li][wi]["accent"] = True
    return pages


def shift_windows(pages):
    """Zeitfenster, in denen das Untertitelband unten steht.

    Die Komposition fährt das Band als durchgehende Spur — nur so liest
    sich das Ausweichen als Bewegung und nicht als harter Positionswechsel.
    Aneinandergrenzende Seiten werden zu einem Fenster verschmolzen.
    """
    out = []
    for p in pages:
        if p["mode"] != "shifted":
            continue
        if out and p["startSec"] - out[-1]["endSec"] < 1.5:
            out[-1]["endSec"] = p["endSec"]
        else:
            out.append({"startSec": p["startSec"], "endSec": p["endSec"]})
    return out


def validate(name, pages, boxes, hook):
    """Harte Zusage prüfen: im Mittelband steht nie ein Untertitel,
    solange dort ein Keyword-Kasten liegt — und im Hook auch nicht."""
    problems = []
    clash = clashing_boxes(boxes, name)
    for p in pages:
        if p["mode"] == "normal":
            for b in clash:
                if p["endSec"] > b["startSec"] and p["startSec"] < b["endSec"]:
                    ov = min(p["endSec"], b["endSec"]) - max(p["startSec"], b["startSec"])
                    problems.append(
                        f"Seite {p['startSec']:.2f}–{p['endSec']:.2f}s liegt "
                        f"{ov:.2f}s im Kasten {b['startSec']:.2f}–{b['endSec']:.2f}s"
                    )
        if hook and p["endSec"] > hook["hookStartSec"] and p["startSec"] < hook["hookEndSec"]:
            problems.append(
                f"Seite {p['startSec']:.2f}–{p['endSec']:.2f}s liegt im Hook-Fenster"
            )
    if problems:
        raise SystemExit(f"ÜBERSCHNEIDUNG in {name}:\n  " + "\n  ".join(problems))


def ts_ident(name):
    n = re.match(r"Video (\d)", name).group(1)
    return f"VIDEO_{n}"


def main():
    font = ImageFont.truetype(str(FONT_PATH), FONT_SIZE)
    boxes_by_video = {v["video"]: v["boxes"]
                      for v in json.loads((INTERN / "overlays.json").read_text())}
    hooks = json.loads((INTERN / "hooks.json").read_text())

    blocks, summary = [], []
    for f in sorted((INTERN / "ad_transcripts").glob("*.json")):
        tr = json.loads(f.read_text())
        name = f.stem + ".mp4"
        words = apply_corrections(tr["words"])
        n_before = len(words)
        words, removed = strip_covered(words, name)
        pages = build_pages(words, boxes_by_video[name], hooks.get(name), font, name)
        pages = pick_accents(pages, per_video_limit=6)
        validate(name, pages, boxes_by_video[name], hooks.get(name))

        shifted = sum(1 for p in pages if p["mode"] == "shifted")
        shown = sum(len(ln) for p in pages for ln in p["lines"])
        summary.append((name, n_before, shown, len(pages), shifted, removed))

        blocks.append(
            f"export const {ts_ident(f.stem)}: CaptionPage[] = "
            + json.dumps(pages, indent=2, ensure_ascii=False) + ";\n"
        )
        blocks.append(
            f"export const {ts_ident(f.stem)}_SHIFTS: ShiftWindow[] = "
            + json.dumps(shift_windows(pages), indent=2, ensure_ascii=False) + ";\n"
        )

    header = '''// ============================================================
// LohiBW — Recruiting-Ads, Untertiteldaten
// ERZEUGT von _intern/build_captions.py — nicht von Hand ändern.
// Quelle: ElevenLabs Scribe auf dem fertigen Schnitt + gemessene
// Belegung der bestehenden Keyword-Kästen (overlays.json).
//
// mode "normal"  = Untertitel im Mittelband
// mode "shifted" = weicht einem langen Keyword-Kasten nach unten aus
// Seiten unter kurzen Kästen und im Hook-Fenster fehlen bewusst.
// ============================================================

export type CaptionWord = {
  text: string;
  startSec: number;
  endSec: number;
  accent?: boolean;
};

export type CaptionPage = {
  startSec: number;
  endSec: number;
  mode: "normal" | "shifted";
  lines: CaptionWord[][];
};

/** Fenster, in dem das Untertitelband nach unten ausweicht. */
export type ShiftWindow = { startSec: number; endSec: number };

'''
    target = (MOTION / "src" / "clients" / "lohi-bw" / "projects"
              / "untertitel" / "captions.ts")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(header + "\n".join(blocks), encoding="utf-8")

    print(f"geschrieben: {target.relative_to(MOTION)}\n")
    print(f"{'Video':<52} {'Wörter':>7} {'gezeigt':>8} {'Seiten':>7} {'ausweichend':>12}")
    for name, nw, shown, npg, sh, _ in summary:
        print(f"{name[:52]:<52} {nw:>7} {shown:>8} {npg:>7} {sh:>12}")

    print("\nWegen Dopplung mit dem Kasten entfernt:")
    for name, _, _, _, _, removed in summary:
        if not removed:
            continue
        print(f"  {name[:46]}")
        for box_label, a, b, phrase in removed:
            print(f"    {a:6.2f}–{b:6.2f}s  Kasten „{box_label}\"")
            print(f"                  „{phrase}\"")


if __name__ == "__main__":
    main()
