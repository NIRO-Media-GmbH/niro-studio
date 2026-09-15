#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_sync_plan.py — sync-plan-Generator für das MAN-Wartezimmervideo 16:9-Master.

Liest timeline.json (12 Blöcke, 11 Lücken, 134,0 s) und erzeugt den kompletten
Element-Plan als sync-plan.json. Basis: Animations-Konzept-16x9.md v2.2,
überstimmt durch DAVIDS UMBAU-ENTSCHEIDUNGEN 2026-07-24 (Review 1) und
DAVIDS REVIEW 2 vom 2026-07-24 (nachts, verbindlich).

--- Review 1 (bleibt gültig) ---
  1. Plaketten zeigen NUR VORNAMEN (erstes Wort von person), Rolle bleibt.
  2. Plakette liegt KOMPLETT auf der Grafikfläche (kein Pixel über dem Video).
  3. Löwe blickt IMMER zur Bildmitte (rechts platziert = nach links blickend).
  4. Alle Rot-Wipes und Akzent-Wische ersatzlos raus — nur Fade/Slide.
  5. Typ 'balken-puls' ersatzlos raus — Kantenbalken IMMER konstant rot.
  6. Pro Kapitel steht DAUERHAFT eine Headline; darunter wechseln
     Takeaways + Plaketten.
  8. KEIN Seitenwechsel/Travel: Fenster fest RECHTS (x=1164, y=28, 576×1024).
     In den zwei sprechfreien Lücken: SPOTLIGHT-MOMENT.

--- Review 2 (2026-07-24 nachts) — im GENERATOR umgesetzt ---
  Nr. 2  Typ 'typo-akzent' ERSATZLOS raus (Erzeugung + Füller-Logik).
         Ebenso 'zeilen-shift' — er ist Textbewegung und verletzt
         „Keinerlei Positions-Sprünge an Texten". Einziger Füller-Typ ist
         'licht-akzent' (moduliert NUR Licht-Opazität, bewegt nichts).
         Fenster > 5 s ohne Licht-Trägerfenster werden NUR geloggt
         (Feld beatCheck.offeneFenster) — die dauerhafte Headline steht.
  Nr. 3  Takeaway-Timing = Blockdauer: start = block.start + 0,4;
         Ausblendung startet am Blockende. Lesezeit-Kappung entfällt,
         Sohn-Story-Sonderregel (Block 11 spät/kurz) entfällt.
         Ausnahme Lara (Block 9): Text ist spätestens 101,0 s unsichtbar.
  Nr. 5  Rollen-Schema fest per Vorname (ROLLEN) statt Ableitung aus der
         timeline.json; Standortfilter bleibt als Sicherheitsnetz.
  Nr. 6  Kein Morph mehr: alte Plakette/Takeaway fährt VOLLSTÄNDIG aus,
         danach Pause (Ziel 1,0 s, Minimum 0,8 s), erst dann die neue.
         Reicht die Blocklücke nicht, wird die ALTE früher ausgefahren —
         nie überlappen. Ergebnis pro Wechsel: Feld pauseVorher.
  Nr. 7  Endcard: 134,0–134,6 s 'fenster-aus' (Fenster verschwindet KOMPLETT),
         ab 135,0 s Fullscreen-Hero, 140,0–142,0 s Ausklang in Dunkelfläche;
         freezeBis = 134,6 (Video-Layer endet mit dem Fenster).
         Loop-Naht: Frame 0 startet aus derselben Dunkelfläche, Fenster
         blendet 0,0–0,5 s ein (loop.frame0.fensterEin).
  Nr. 8  Neue Takeaway-Texte wörtlich (TAKEAWAYS).
  Nr. 9  Branding-Beat (Text + Logo in Spotlight 1) DEAKTIVIERT — beide
         Spotlights sind text- UND logofrei. 'branding' bleibt nur als
         Stub mit aktiv=false stehen (Composition-Kompatibilität).
  Nr. 10 Werkzeug-Silhouetten-Regen in den Spotlights: Parameter unter
         spotlights[].werkzeugRegen (rein deskriptiv für die Composition).

Composition-seitig (NICHT hier): Nr. 1 Löwe links vollständig, Nr. 4 Logo
links oben x=64, Nr. 11 weicher Fensterschatten, Nr. 12 luftigere Spacings.

Nur Stdlib. Lauffähig mit tools/transcribe/venv/bin/python (oder jedem Python 3).

Ausgabe:
  1. tools/motion/src/clients/man/projects/wartezimmervideo/sync-plan.json
  2. Kopie neben timeline.json (dieses Verzeichnis)
"""

import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TIMELINE = os.path.join(HERE, "timeline.json")
OUT_MOTION = os.path.join(
    HERE, "..", "..", "..", "..", "..", "..",
    "tools", "motion", "src", "clients", "man", "projects", "wartezimmervideo",
    "sync-plan.json",
)
OUT_LOCAL = os.path.join(HERE, "sync-plan.json")

FPS = 25
MASTER_DAUER = 175.0          # 4375 Frames (V3: Video 164,96 s + Endcard; Abbinder liegt IM Finale)
MASTER_FRAMES = 4375
VIDEO_FRAMES = 4124           # echte Framezahl wz-v2-haupt-1080.mov

# --- Umbau-Konstanten (David 2026-07-24, Fenster neu in Review 3 Nr. 4) ---
# Vorher 576×1024 bei y=28: oben/unten blieben nur 28 px, der weiche Schatten
# (Blur 220 / y-Versatz 60) reichte 170 px über die Unterkante und wurde an der
# Canvas-Kante hart abgeschnitten. Jetzt 540×960 (9:16 exakt, 540·16 = 960·9),
# vertikal zentriert bei y = (1080−960)/2 = 60 ⇒ rundum 60 px Luft.
FENSTER = {"x": 1200, "y": 60, "breite": 540, "hoehe": 960}  # fest RECHTS
FENSTER_RAND_RECHTS = 1920 - FENSTER["x"] - FENSTER["breite"]  # = 180 px
FENSTER_RAND_OBEN = FENSTER["y"]                                # = 60 px
FENSTER_RAND_UNTEN = 1080 - FENSTER["y"] - FENSTER["hoehe"]     # = 60 px

SPOTLIGHT_1 = (9.5, 22.3)     # sprechfreie Lücke 1
REST_SPOTLIGHT = (75.5, 89.9)  # Rest von Ex-Lücke 7 nach Quer-1-Ende (v9)
BRANDING = (13.0, 17.0)       # NUR noch Stub-Zeitfenster (Review 2 Nr. 9: aus)

# --- Quer-Strecken (v9 2026-07-29) ---
QUER_1 = (64.56, 76.56)       # Quer-Strecke 1 (Frames 1614–1913), fix aus V2
QUER_2 = (133.52, 164.92)     # Finale (Frames 3338–4122), bleibt offen
QUER_VORLAUF = 0.16           # Grafik-Elemente enden >= 4 Frames vor der Blende
BLENDE_DAUER = 0.6            # Öffnen/Schließen je 15 Frames
SCHWARZ_AB = 163.92           # Schwarzblende im Material (Bild + Ton)

# --- Endcard / Loop (v9: CTA-Endcard Recruiting) ---
ENDCARD_HERO = 165.0          # CTA-Endcard aus dem Schwarz
ENDCARD_AUSKLANG = 173.0      # 8 s Standzeit (QR-Scan), dann Ausklang
LOOP_FENSTER_EIN = 0.5        # Frame 0: Fenster blendet aus der Dunkelfläche ein

# --- Standard-Abbinder (v10 2026-08-07, MAN-Mail 3: CI Film-Ending) ---
# MAN-CI: "Jeder Film endet mit dem Erscheinen des MAN Logos und der
# Überblendung zum schwarzen Hintergrund"; Logo ändert nie Position/Größe.
# Platz dafür hat der Kunde in der V3-Quer-Datei selbst geschaffen:
# Schwertransporter raus, letzter Shot endet 160,2 s mit HARTEM Cut auf
# Schwarz (gemessen YAVG 511→64 zwischen F4006 und F4008; Material danach
# schwarz bis 164,92). Umsetzung im Master: Logo erscheint über der letzten
# Fahrszene, ein Remotion-Dimmer übernimmt die CI-Überblendung zu Schwarz
# und verdeckt den Material-Cut, das weiße Logo steht auf Schwarz und
# blendet synchron mit der Ton-Ausblende des Haupt-Materials aus.
# Endcard (165,0) und Loop-Naht bleiben unverändert.
ABBINDER_LOGO_EIN = (157.52, 158.72)    # F3938–3968: Logo über der Fahrszene
ABBINDER_DIMM = (158.92, 160.2)         # F3973–4005: Überblendung zu Schwarz
ABBINDER_SCHWARZ_VOLL = 160.2           # ab hier weißes Logo auf Schwarz
ABBINDER_LOGO_AUS = (163.92, 164.92)    # F4098–4123: synchron zur Ton-Ausblende
ABBINDER_LOGO_BREITE = 700              # Design-px (1920er Bühne), zentriert

LARA_SPERRE = 101.0           # Guardrail 1: 101,0–103,8 s nie als Text
MIKRO_LUECKE_MAX = 3.0        # größere Lücken = Kapitel-Trenner (Enter nach Spotlight)
BEAT_FENSTER = 5.0            # Zielwert: nie länger als 5 s ohne Content-Event

# --- Takt-Regeln Plaketten/Takeaways (Review 2 Nr. 6) ---
PAUSE_ZIEL = 1.0              # angestrebte Pause zwischen Aus-Ende und Ein-Start
PAUSE_MIN = 0.8               # harte Untergrenze — nie unterschreiten
MIN_STAND = 1.2               # angestrebte Mindest-Standzeit (voll sichtbar)

# --- Takt-Regeln Headline-Wechsel (Review 2 Nr. 2, v4) ---
# Eigene, kürzere Pause: die Bühne soll beim Kapitelwechsel nicht sekundenlang
# kopflos dastehen, zwei Headlines dürfen sich aber NIE überlagern.
HEAD_EIN_DAUER = 0.6
HEAD_AUS_DAUER = 0.6
HEAD_PAUSE_ZIEL = 0.5
HEAD_PAUSE_MIN = 0.4
HEAD_MIN_STAND = 2.0

PLAK_EIN_DAUER = 0.6
PLAK_AUS_DAUER = 0.5
TW_EIN_VERZUG = 0.4           # Review 2 Nr. 3: Einblendung 0,4 s nach Blockstart
TW_EIN_DAUER = 0.5            # revealDauer
TW_AUS_DAUER = 0.4            # = 10 Frames Exit-Fade in der Composition

# Guardrail 3: keine Standortnamen in Rollen-Texten (Sicherheitsnetz, bleibt).
STANDORTNAMEN = (
    "Karlsruhe", "Schweinfurt", "Mannheim", "Stuttgart", "Heilbronn",
    "Freiburg", "Ulm", "Pforzheim", "Würzburg", "Nürnberg", "München",
)

# --- Rollen-Schema (Review 2 Nr. 5, aus den Transkripten recherchiert) ---
# Einheitlich, ohne Standortnamen, „Azubi" nur wenn Azubi. Schlüssel = Vorname.
ROLLEN = {
    "Julia":     "Nutzfahrzeugmechatronikerin",       # „ich bin Nutzfahrzeugmechatronikerin"
    "Marcel":    "Nutzfahrzeugmechatroniker",         # „Geselle" seit 2017; David 2026-07-25: nur Mechatroniker
    "Markus":    "Betriebsleiter Servicebetrieb",     # Betriebsleiter seit 1997
    "Alexander": "Teilelager & Teileverkauf",
    "Tobi":      "Nutzfahrzeugmechatroniker",         # sagt selbst „Mechaniker"; David 2026-07-25: offiziell Mechatroniker
    "Nico":      "Teilelager & Teileverkauf",
    "Louis":     "Azubi Nutzfahrzeugmechatronik",     # 2. Lehrjahr
    "Lara":      "Azubi Nutzfahrzeugmechatronik",
    "Hannes":    "Azubi Nutzfahrzeugmechatronik",     # „NFZ-Bereich", 2. Lehrjahr
    "Mark":      "Betriebsleiter Servicebetrieb",     # Ciattei: „Betriebsleiter vom Servicebetrieb"
}

# --- Kapitel-Headlines (David 2026-07-24, WÖRTLICH; **wort** = Rot) ---
# Stehen DAUERHAFT im Zeitfenster, Wechsel per Slide+Fade (keine Wipes).
HEADLINES = [
    {"kapitel": 1, "start": 0.4, "ende": 9.8,
     "kartentext": "QUALITÄT OHNE **KOMPROMISSE**",
     "zeilen": ["QUALITÄT OHNE", "**KOMPROMISSE**"]},
    {"kapitel": 2, "start": 21.8, "ende": 64.4,
     "kartentext": "EIN STARKES **TEAM**",
     "zeilen": ["EIN STARKES **TEAM**"]},
    {"kapitel": 3, "start": 89.9, "ende": 107.0,
     "kartentext": "FASZINATION **NUTZFAHRZEUGE**",
     "zeilen": ["FASZINATION", "**NUTZFAHRZEUGE**"]},
    {"kapitel": 4, "start": 107.3, "ende": 133.36,
     "kartentext": "MIT **HERZ** DABEI",
     "zeilen": ["MIT **HERZ** DABEI"]},
]

# --- Takeaways (Review 2 Nr. 8, kartentext WÖRTLICH; **wort** = Rot) ---
# groessePx: Review 2 Nr. 12 — kleiner als bisher (64), Zweizeiler noch etwas
# kleiner, damit „FASZINATION NUTZFAHRZEUG" + Zweizeiler nicht überladen wirkt.
TAKEAWAYS = {
    1:  {"kartentext": "**100 %** — VON ANFANG AN",
         "zeilen": ["**100 %** — VON ANFANG AN"]},
    2:  {"kartentext": "**FAMILIÄRES** UMFELD",
         "zeilen": ["**FAMILIÄRES** UMFELD"]},
    3:  {"kartentext": "JEDEN TAG **BESSER** WERDEN",
         "zeilen": ["JEDEN TAG **BESSER** WERDEN"]},
    4:  {"kartentext": "**TEAMGEIST** — AUCH NACH FEIERABEND",
         "zeilen": ["**TEAMGEIST** —", "AUCH NACH FEIERABEND"]},
    5:  {"kartentext": "AUF **AUGENHÖHE**. FLACHE HIERARCHIESTUFEN.",
         "zeilen": ["AUF **AUGENHÖHE**.", "FLACHE HIERARCHIESTUFEN."]},
    6:  {"kartentext": "**ZUSAMMENHALT**, DER TRÄGT",
         "zeilen": ["**ZUSAMMENHALT**, DER TRÄGT"]},
    7:  {"kartentext": "ARBEIT, DIE **WACHSEN** LÄSST",
         "zeilen": ["ARBEIT, DIE **WACHSEN** LÄSST"]},
    8:  {"kartentext": "**LKW-LIEBE** VON KLEIN AUF",
         "zeilen": ["**LKW-LIEBE** VON KLEIN AUF"]},
    9:  {"kartentext": "MIT **VATERS** LKW GROSS GEWORDEN",
         "zeilen": ["MIT **VATERS** LKW", "GROSS GEWORDEN"]},
    10: {"kartentext": "GROSSE FAHRZEUGE. **GROSSES BEWEGEN**.",
         "zeilen": ["GROSSE FAHRZEUGE.", "**GROSSES BEWEGEN**."]},
    11: {"kartentext": "MEIN SOHN WEISS: »DEN HAB ICH **REPARIERT**.«",
         "zeilen": ["MEIN SOHN WEISS:", "»DEN HAB ICH **REPARIERT**.«"]},
    12: {"kartentext": "NICHT VON DER STANGE. ECHTE **SPEZIALKRÄFTE**.",
         "zeilen": ["NICHT VON DER STANGE.", "ECHTE **SPEZIALKRÄFTE**."]},
}

# --- Takeaway-Schriftgrad (Review 3 Nr. 1) ---------------------------------
# Vorher drei Stufen (56 einzeilig / 52 zweizeilig / 48 im „engen" Fall) — die
# gemessene Versalhöhe sprang dadurch je Frame zwischen 38 und 42 px, der Satz
# wirkte unruhig. Jetzt: EIN fester Grad für alle 12 Takeaways. Nur wenn eine
# Zeile breiter als die Spalte würde, schaltet der Generator auf die EINE
# definierte Ausnahmestufe herunter — kein stufenloses Auto-Fit.
TW_GROESSE = 54               # fester Grad für ALLE Takeaways
TW_GROESSE_AUSNAHME = 46      # EINZIGE Ausnahmestufe
TW_SPALTE_PX = 964            # Spalte 64–1064 (1000) minus Balken 8 + Gap 28
TW_LETTER_SPACING = 1.0       # entspricht letterSpacing: 1 in der Composition
FONT_COND_BOLD = os.path.join(
    HERE, "..", "..", "..", "..", "..", "..",
    "tools", "motion", "public", "fonts", "man", "MAN_Global-BoldCondensed.ttf",
)


def text_breite_fabrik():
    """Liefert eine Messfunktion breite(text, px) für MAN Global Bold Condensed
    — oder None, wenn fontTools/die TTF nicht verfügbar sind.

    fontTools ist eine OPTIONALE Abhängigkeit: fehlt sie, läuft der Generator
    unverändert stdlib-only durch, vergibt TW_GROESSE und protokolliert, dass
    die Breitenprüfung nicht laufen konnte.
    """
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return None
    try:
        font = TTFont(os.path.normpath(FONT_COND_BOLD), fontNumber=0, lazy=True)
    except Exception:
        return None
    upm = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]

    def breite(text, px):
        summe = 0
        for ch in text:
            glyph = cmap.get(ord(ch)) or cmap.get(ord(" "))
            summe += hmtx[glyph][0]
        return summe / upm * px + TW_LETTER_SPACING * len(text)

    return breite


def takeaway_groesse(zeilen, block, messen, log, warnungen):
    """Review 3 Nr. 1: TW_GROESSE, Ausnahmestufe nur bei echtem Überlauf."""
    if messen is None:
        return TW_GROESSE, None
    texte = [z.replace("**", "") for z in zeilen]
    breit = max(messen(t, TW_GROESSE) for t in texte)
    if breit <= TW_SPALTE_PX:
        return TW_GROESSE, round(breit, 1)
    klein = max(messen(t, TW_GROESSE_AUSNAHME) for t in texte)
    log.append("Takeaway %d: %.1f px > %d px Spaltenbreite -> Ausnahmestufe "
               "%d px (dann %.1f px)"
               % (block, breit, TW_SPALTE_PX, TW_GROESSE_AUSNAHME, klein))
    if klein > TW_SPALTE_PX:
        warnungen.append("WARNUNG: Takeaway %d passt auch in der Ausnahmestufe "
                         "%d px nicht in die Spalte (%.1f > %d px) — Text kürzen"
                         % (block, TW_GROESSE_AUSNAHME, klein, TW_SPALTE_PX))
    return TW_GROESSE_AUSNAHME, round(klein, 1)


def f(sec):
    """Sekunden -> Frame (25 fps)."""
    return int(round(sec * FPS))


def r1(x):
    return round(x, 2)


def vorname(person):
    """David 2026-07-24 (1): Plakette zeigt nur den Vornamen = erstes Wort."""
    return person.split()[0]


def standort_filter(rolle):
    """Guardrail 3: Standortnamen generisch entfernen (ganze Wörter)."""
    for ort in STANDORTNAMEN:
        rolle = re.sub(r"\s*\b%s\b" % re.escape(ort), "", rolle)
    return re.sub(r"\s{2,}", " ", rolle).strip(" ,;-–—")


def rolle_fuer(block, warnungen):
    """Review 2 Nr. 5: festes Rollen-Schema per Vorname.
    Fallback (unbekannter Vorname): alte Ableitung aus timeline.json + Warnung.
    Standortfilter läuft in BEIDEN Fällen als Sicherheitsnetz."""
    vn = vorname(block["person"])
    if vn in ROLLEN:
        return standort_filter(ROLLEN[vn])
    w = ("WARNUNG: Vorname %r nicht im Rollen-Schema (Review 2 Nr. 5) — "
         "Rolle aus timeline.json abgeleitet, bitte Schema ergänzen" % vn)
    warnungen.append(w)
    return standort_filter(re.sub(r"\s*\([^)]*\)", "", block["rolle"]).strip())


def zeichen_ohne_markup(text):
    return len(text.replace("**", ""))


def takte_pausen(elemente, label, log, warnungen, modus="kuerzen",
                 pause_ziel=PAUSE_ZIEL, pause_min=PAUSE_MIN,
                 min_stand=MIN_STAND):
    """Review 2 Nr. 6 — sequenzieller Takt statt Morph.

    elemente: Liste (zeitlich sortiert) von dicts mit
              einStart, einDauer, ausStart, ausDauer.
    Regel:    Ein-Start der NEUEN minus Aus-Ende der ALTEN >= pause_min,
              Ziel pause_ziel — nie zwei Elemente gleichzeitig sichtbar.

    modus="kuerzen"     Die ALTE fährt früher aus (ausStart wird vorgezogen).
                        Richtig für Plaketten und Headlines: dort ist das Ende
                        nicht an eine Aussage gebunden.
    modus="verzoegern"  Das NEUE Element startet später (einStart wird
                        geschoben), das Aus-Ende der alten bleibt UNANGETASTET.
                        Pflicht für Takeaways (Review 2 Nr. 3: „Ausblendung
                        erst am Blockende", keine Lesezeit-Kappung). Nur wenn
                        selbst maximales Verzögern die Pause nicht herstellt,
                        wird ersatzweise gekürzt — mit Eintrag in `warnungen`.
    Schreibt pauseVorher (Sekunden, None beim ersten Element), gekuerzt und
    (im Verzögerungs-Modus) verzoegert.
    """
    def kuerze(a, b, pause):
        voll_ab = a["einStart"] + a["einDauer"]          # voll sichtbar ab
        ziel = b["einStart"] - pause_ziel - a["ausDauer"]
        grenze = b["einStart"] - pause_min - a["ausDauer"]  # spätester Aus-Start
        neu = ziel
        if neu - voll_ab < min_stand:
            neu = min(voll_ab + min_stand, grenze)
        log.append("%s %s: Ausblendung %.2f -> %.2f s vorgezogen "
                   "(Pause vorher %.2f s, jetzt %.2f s)"
                   % (label, a.get("id", "?"), a["ausStart"], neu,
                      pause, b["einStart"] - (neu + a["ausDauer"])))
        if neu - voll_ab < min_stand - 1e-9:
            log.append("%s %s: Standzeit nur %.2f s (< %.2f s Ziel) — "
                       "Blockabstand gibt nicht mehr her"
                       % (label, a.get("id", "?"), max(0.0, neu - voll_ab), min_stand))
        a["ausStart"] = r1(neu)
        a["gekuerzt"] = True

    for i in range(len(elemente) - 1):
        a, b = elemente[i], elemente[i + 1]
        aus_ende = a["ausStart"] + a["ausDauer"]
        pause = b["einStart"] - aus_ende
        if pause >= pause_min - 1e-9:
            continue
        if modus == "kuerzen":
            kuerze(a, b, pause)
            continue

        # --- modus "verzoegern": Aus-Ende der ALTEN ist unantastbar ---
        min_ein = aus_ende + pause_min
        ziel_ein = aus_ende + pause_ziel
        # Das NEUE muss nach dem Schieben noch min_stand voll stehen.
        spaetestens = b["ausStart"] - b["einDauer"] - min_stand
        neu_ein = min(ziel_ein, spaetestens)
        if neu_ein < min_ein:
            neu_ein = min_ein
        if neu_ein + b["einDauer"] >= b["ausStart"] - 1e-9:
            # Selbst das Minimum passt nicht mehr in den eigenen Block ->
            # nur hier (Blockabstand < Pause) doch kürzen, laut protokolliert.
            warnungen.append("WARNUNG: %s %s — Blockabstand zu klein für die "
                             "Pause (%.2f s); Ausblendung von %s wird "
                             "ausnahmsweise vorgezogen"
                             % (label, b.get("id", "?"), pause, a.get("id", "?")))
            kuerze(a, b, pause)
            continue
        log.append("%s %s: Einblendung %.2f -> %.2f s verzögert "
                   "(Pause vorher %.2f s, jetzt %.2f s) — Aus-Ende von %s "
                   "bleibt bei %.2f s (Review 2 Nr. 3)"
                   % (label, b.get("id", "?"), b["einStart"], neu_ein,
                      pause, neu_ein - aus_ende, a.get("id", "?"), aus_ende))
        b["einStart"] = r1(neu_ein)
        b["verzoegert"] = True

    pausen = []
    for i, e in enumerate(elemente):
        if i == 0:
            e["pauseVorher"] = None
            continue
        a = elemente[i - 1]
        p = r1(e["einStart"] - (a["ausStart"] + a["ausDauer"]))
        e["pauseVorher"] = p
        pausen.append(p)
        if p < pause_min - 1e-9:
            warnungen.append("WARNUNG: %s %s — Pause vor Einblendung nur %.2f s "
                             "(< %.2f s)" % (label, e.get("id", "?"), p, pause_min))
        if p < 0:
            warnungen.append("WARNUNG: %s %s — ÜBERLAPPUNG (%.2f s)"
                             % (label, e.get("id", "?"), p))
    return pausen


UT_MAX_ZEICHEN = 32           # pro Zeile, max 2 Zeilen
UT_MIN_STAND = 1.2


def untertitel_segmente(bloecke, log):
    """Untertitel für die stumme Fassung: Wortlaut aus timeline.json,
    Timing proportional über die Scribe-Wörter des Blocks verteilt."""
    with open(os.path.join(HERE, "transcript.scribe.json"), encoding="utf-8") as fh:
        scribe = json.load(fh)["words"]
    segmente = []
    for b in bloecke:
        woerter = [w for w in scribe
                   if b["start"] - 0.3 <= w["start"] <= b["ende"] + 0.3]
        text = b["text"]
        # Grob an Satzzeichen teilen, dann auf <= 2 Zeilen à 32 Zeichen packen
        import re
        teile = [s.strip() for s in re.split(r"(?<=[.!?…])\s+", text) if s.strip()]
        chunks = []
        for satz in teile:
            wl = satz.split()
            akt = []
            for w in wl:
                kandidat = " ".join(akt + [w])
                if len(kandidat) > 2 * UT_MAX_ZEICHEN and akt:
                    chunks.append(" ".join(akt)); akt = [w]
                else:
                    akt.append(w)
            if akt:
                chunks.append(" ".join(akt))
        gesamt = sum(len(c.split()) for c in chunks)
        cursor = 0
        for c in chunks:
            n = len(c.split())
            if woerter and gesamt:
                i0 = min(int(cursor / gesamt * len(woerter)), len(woerter) - 1)
                i1 = min(int((cursor + n) / gesamt * len(woerter)), len(woerter)) - 1
                s0 = woerter[i0]["start"]; s1 = woerter[max(i0, i1)]["end"]
            else:  # Fallback: proportional über die Blockdauer
                s0 = b["start"] + cursor / max(1, gesamt) * (b["ende"] - b["start"])
                s1 = b["start"] + (cursor + n) / max(1, gesamt) * (b["ende"] - b["start"])
            cursor += n
            # Zeilenumbruch: möglichst mittig, nie > 32 Zeichen
            wl = c.split(); zeilen = [c]
            if len(c) > UT_MAX_ZEICHEN:
                best = min(range(1, len(wl)),
                           key=lambda i: abs(len(" ".join(wl[:i])) - len(c) / 2))
                zeilen = [" ".join(wl[:best]), " ".join(wl[best:])]
            segmente.append({"block": b["idx"], "person": b["person"],
                             "text": c, "zeilen": zeilen,
                             "start": r1(s0), "ende": r1(max(s1, s0 + UT_MIN_STAND))})

    # --- I-1: Quer-Blenden-Kappung (generisch für alle Blenden) ---
    # Jedes Segment, das eine Quer-Deadline (q_start - QUER_VORLAUF) überschreitet,
    # während sein start davor liegt, wird auf die Deadline gekürzt.
    # Kappung schlägt Mindeststand; Segmente mit resultierender Dauer < 0.5 s werden entfernt.
    quer_deadlines = [r1(q - QUER_VORLAUF) for q in (QUER_1[0], QUER_2[0])]
    zu_entfernen = []
    for s in segmente:
        for deadline in quer_deadlines:
            if s["start"] < deadline - 1e-9 < s["ende"] - 1e-9:
                if s["ende"] > deadline + 1e-9:
                    log("UT-Kappung: Block %d '%s' ende %.2f -> %.2f s (Quer-Deadline %.2f)"
                        % (s["block"], s["text"][:20], s["ende"], deadline, deadline))
                    s["ende"] = deadline
                    if s["ende"] - s["start"] < 0.5:
                        log("UT-Entfernt: Block %d '%s' (Dauer %.2f s < 0.5 s nach Kappung)"
                            % (s["block"], s["text"][:20], s["ende"] - s["start"]))
                        zu_entfernen.append(s)
    for s in zu_entfernen:
        segmente.remove(s)

    # --- I-2: Sequenzielle Abdichtung pro Block (strukturell) ---
    # Segmente je Block nach start sortieren; wenn Segment n+1 vor ende[n]+0.08 startet,
    # start[n+1] auf ende[n]+0.08 setzen. Wird dabei start >= ende, ende verlängern.
    # Nie über nächsten Blockstart - 0.1 s und nie über eine Quer-Deadline.
    bloecke_map = {b["idx"]: b for b in bloecke}
    # Sortierte Blockliste für Nachfolger-Lookup
    block_idxs_sorted = sorted(bloecke_map.keys())

    def _block_ende_limit(block_idx):
        """Maximales Ende für Segmente dieses Blocks: vor dem nächsten Blockstart (- 0.1 s)."""
        pos = block_idxs_sorted.index(block_idx)
        if pos + 1 < len(block_idxs_sorted):
            next_idx = block_idxs_sorted[pos + 1]
            next_start = bloecke_map[next_idx]["start"]
            return r1(min(next_start - 0.1, bloecke_map[block_idx]["ende"] + 1.5))
        return r1(bloecke_map[block_idx]["ende"] + 1.5)

    # Gruppieren nach block
    from collections import defaultdict
    block_segs = defaultdict(list)
    for s in segmente:
        block_segs[s["block"]].append(s)

    for block_idx, segs in block_segs.items():
        segs.sort(key=lambda s: s["start"])
        blimit = _block_ende_limit(block_idx)

        def _deadline_cap(start, ende, _blimit=blimit):
            """Begrenzt ende auf die nächste aktive Quer-Deadline ab start."""
            for dl in quer_deadlines:
                if start < dl - 1e-9:
                    ende = min(ende, dl)
                    break
            return min(ende, _blimit)

        def _ensure_min_stand(seg, _blimit=blimit):
            """Verlängert seg["ende"] auf start+UT_MIN_STAND wenn nötig (begrenzt durch Deadlines)."""
            min_ende = r1(seg["start"] + UT_MIN_STAND)
            if seg["ende"] < min_ende - 1e-9:
                seg["ende"] = _deadline_cap(seg["start"], min_ende)

        # Zuerst UT_MIN_STAND für alle Segmente sicherstellen (inkl. letztes)
        for seg in segs:
            _ensure_min_stand(seg)

        # Dann sequenzielle Abdichtung
        for i in range(len(segs) - 1):
            cur = segs[i]
            nxt = segs[i + 1]
            min_nxt_start = r1(cur["ende"] + 0.08)
            if nxt["start"] < min_nxt_start - 1e-9:
                nxt["start"] = min_nxt_start
            if nxt["start"] >= nxt["ende"] - 1e-9:
                # nxt hat keinen Platz mehr: verlängere ende auf start + UT_MIN_STAND
                new_ende = _deadline_cap(nxt["start"], r1(nxt["start"] + UT_MIN_STAND))
                if new_ende <= nxt["start"] + 1e-9:
                    # Immer noch kein Platz (Deadline zu eng): kürze das FRÜHERE Segment
                    cur["ende"] = r1(nxt["start"] - 0.08)
                    nxt["start"] = r1(cur["ende"] + 0.08)
                    new_ende = _deadline_cap(nxt["start"], r1(nxt["start"] + UT_MIN_STAND))
                nxt["ende"] = new_ende
            else:
                # nxt hat seinen start bekommen — sicherstellen dass es UT_MIN_STAND lang ist
                _ensure_min_stand(nxt)

    # Dritter Pass: Segmente die noch unter UT_MIN_STAND liegen:
    # (a) Versuche start zurückzuziehen (begrenzt durch Vorgänger-ende+0.08).
    # (b) Wenn das nicht reicht, merge mit dem Vorgänger (letztes Segment
    #     zu kurz → in vorletztes Segment aufnehmen, Text anhängen).
    for block_idx, segs in block_segs.items():
        segs.sort(key=lambda s: s["start"])
        i = 0
        while i < len(segs):
            seg = segs[i]
            dauer = seg["ende"] - seg["start"]
            if dauer >= UT_MIN_STAND - 1e-9:
                i += 1
                continue
            # Versuche start zurückzuziehen
            needed_start = r1(seg["ende"] - UT_MIN_STAND)
            min_start = r1(segs[i - 1]["ende"] + 0.08) if i > 0 else seg["start"] - 2.0
            if needed_start >= min_start - 1e-9:
                seg["start"] = needed_start
                i += 1
                continue
            # Zurückziehen nicht möglich: merge mit Vorgänger wenn vorhanden
            if i > 0:
                prev = segs[i - 1]
                merged_text = prev["text"] + " " + seg["text"]
                merged_zeilen = [merged_text]
                if len(merged_text) > UT_MAX_ZEICHEN:
                    wl = merged_text.split()
                    best = min(range(1, len(wl)),
                               key=lambda j: abs(len(" ".join(wl[:j])) - len(merged_text) / 2))
                    merged_zeilen = [" ".join(wl[:best]), " ".join(wl[best:])]
                prev["text"] = merged_text
                prev["zeilen"] = merged_zeilen
                prev["ende"] = seg["ende"]
                log("UT-Merge: Block %d '%s' + '%s' → ein Segment (%.2f–%.2f s, Mindeststand nicht erreichbar)"
                    % (block_idx, prev["text"][:15], seg["text"][:15], prev["start"], prev["ende"]))
                segs.pop(i)
                # Segment auch aus segmente-Liste entfernen
                if seg in segmente:
                    segmente.remove(seg)
                # i bleibt gleich (nächstes Element rückt nach)
            else:
                i += 1  # kann nicht mergen, akzeptieren

    # Globaler Assert: innerhalb jedes Blocks gilt start[i+1] >= ende[i] + 0.06
    for block_idx, segs in block_segs.items():
        segs.sort(key=lambda s: s["start"])
        for i in range(len(segs) - 1):
            a, b_seg = segs[i], segs[i + 1]
            assert b_seg["start"] >= a["ende"] + 0.06 - 1e-9, (
                "UT-Sequenz-Verletzung Block %d: %r ende=%.2f, %r start=%.2f"
                % (block_idx, a["text"][:15], a["ende"], b_seg["text"][:15], b_seg["start"])
            )

    # frameVon/frameBis nach allen Anpassungen neu berechnen
    for s in segmente:
        s["frameVon"] = f(s["start"]); s["frameBis"] = f(s["ende"])
    log("Untertitel: %d Segmente" % len(segmente))
    return segmente


def main():
    with open(TIMELINE, "r", encoding="utf-8") as fh:
        timeline = json.load(fh)

    bloecke = {b["idx"]: b for b in timeline["bloecke"]}
    luecken = {l["nach_block"]: l for l in timeline["luecken"]}

    log = []
    warnungen = []

    # ------------------------------------------------------------------
    # Fenster: FEST rechts, kein Travel/Seitenwechsel (David 8).
    # Neu (Review 2 Nr. 7+11): Ausblendung ab 134,0 s, Einblendung im Loop
    # ab Frame 0; Schatten weich/großflächig (Composition).
    # ------------------------------------------------------------------
    fenster = {
        "x": FENSTER["x"], "y": FENSTER["y"],
        "breite": FENSTER["breite"], "hoehe": FENSTER["hoehe"],
        "randRechts": FENSTER_RAND_RECHTS,
        "seite": "rechts",
        "einblendung": {"start": 0.0, "dauer": LOOP_FENSTER_EIN,
                        "hinweis": "Loop-Naht: Fenster kommt aus der Dunkelfläche "
                                   "(Review 2 Nr. 7)"},
        "ausblendung": None,  # durch Quer-Blende ersetzt (v9 2026-07-29; Task 4 entfernt die Verwender)
        "randOben": FENSTER_RAND_OBEN,
        "randUnten": FENSTER_RAND_UNTEN,
        # Review 3 Nr. 4: Reichweite = blur/2 + |y| muss in den 60 px Rand
        # oben UND unten passen, sonst bricht der Schatten an der Canvas-Kante
        # ab. Stufe 1: 35 + 6 = 41 nach unten, 35 − 6 = 29 nach oben.
        # Stufe 2: 60 ohne Versatz ⇒ exakt bündig, rundum weicher Abfall.
        "schatten": {"art": "weich, großflächig, zweistufig, rundum auslaufend",
                     "stufe1": {"blur": 70, "y": 6, "deckkraft": 0.34},
                     "stufe2": {"blur": 120, "y": 0, "deckkraft": 0.2},
                     "reichweiteOben": 60, "reichweiteUnten": 60,
                     "hinweis": "Review 2 Nr. 11: harter Schatten raus; "
                                "Review 3 Nr. 4: Reichweite an den 60-px-Rand "
                                "angepasst, kein Abriss oben/unten mehr"},
        "hinweis": "FEST — kein Seitenwechsel/Travel (David 2026-07-24, Nr. 8). "
                   "Grafikfläche dauerhaft links, Radius 0.",
    }
    fenster_seiten = [{"von": 0.0, "bis": QUER_2[0], "seite": "rechts"}]

    # Löwe: v9 — rechtsblickend, zwei Auftritte (Spotlights), Endcard dunkel links.
    loewe = {
        "blick": "rechts",
        "auftritte": [
            {"id": "auftritt-1", "start": SPOTLIGHT_1[0], "ende": SPOTLIGHT_1[1],
             "seite": "links"},
            {"id": "auftritt-2", "start": REST_SPOTLIGHT[0], "ende": REST_SPOTLIGHT[1],
             "seite": "links"},
        ],
        "endcard": {"variante": "dunkel", "seite": "links"},
    }

    # ------------------------------------------------------------------
    # Plaketten (Review 2 Nr. 6): sauberes Aus -> Pause -> Ein, kein Morph.
    # ------------------------------------------------------------------
    plak_roh = []
    for idx in sorted(bloecke):
        b = bloecke[idx]
        prev_l = luecken.get(idx - 1)      # Lücke VOR diesem Block
        eigene_l = luecken.get(idx)        # Lücke NACH diesem Block

        if idx == 1:
            ein_art = "kaltstart"
        elif prev_l is not None and prev_l["dauer"] > MIKRO_LUECKE_MAX:
            ein_art = "enter-nach-spotlight"
        else:
            ein_art = "enter"              # Review 2 Nr. 6: Morph ersetzt

        plak_roh.append({
            "id": "plakette-%d" % idx,
            "block": idx,
            "einStart": r1(b["start"]),
            "einDauer": PLAK_EIN_DAUER,
            "einArt": ein_art,
            "ausStart": r1(b["ende"]),
            "ausDauer": PLAK_AUS_DAUER,
            "gekuerzt": False,
        })

    # letzte Plakette muss vor der Quer-2-Blende draußen sein
    letzte = plak_roh[-1]
    deadline_plak = r1(QUER_2[0] - QUER_VORLAUF)  # 133.36
    if letzte["ausStart"] + letzte["ausDauer"] > deadline_plak:
        letzte["ausStart"] = r1(deadline_plak - letzte["ausDauer"])
        log.append("Plakette %d: Ausblendung auf %.2f s gezogen "
                   "(muss vor Quer-2-Blende %.2f s draußen sein)"
                   % (letzte["block"], letzte["ausStart"], deadline_plak))

    plak_pausen = takte_pausen(plak_roh, "Plakette", log, warnungen)

    plaketten = []
    for e in plak_roh:
        b = bloecke[e["block"]]
        plaketten.append({
            "block": e["block"],
            "person": vorname(b["person"]),   # David 1: NUR Vorname anzeigen
            "personVoll": b["person"],        # Referenz, wird NICHT gerendert
            "rolle": rolle_fuer(b, warnungen),
            "seite": "links",                 # David 2: komplett auf der Grafikfläche
            "eintritt": {"start": e["einStart"], "dauer": e["einDauer"],
                         "art": e["einArt"]},
            "austritt": {"start": e["ausStart"], "dauer": e["ausDauer"]},
            "pauseVorher": e["pauseVorher"],
            "vorgezogen": e["gekuerzt"],
            "standzeit": r1(e["ausStart"] - (e["einStart"] + e["einDauer"])),
            "frameVon": f(e["einStart"]),
            "frameBis": f(e["ausStart"] + e["ausDauer"]),
            "ciattei": "Ciattei" in b["person"],
        })

    plaketten_regeln = {
        "anzeige": "nur Vorname (erstes Wort von person) + Rolle (David 2026-07-24, Nr. 1)",
        "lage": "komplett auf der Grafikfläche — kein Pixel über dem Video (Nr. 2)",
        "takt": "Review 2 Nr. 6: alte Plakette fährt VOLLSTÄNDIG aus, dann Pause "
                "(Ziel %.1f s, Minimum %.1f s), erst dann fährt die neue ein. "
                "Nie zwei Plaketten gleichzeitig sichtbar. pauseVorher = "
                "gemessene Pause vor dieser Einblendung."
                % (PAUSE_ZIEL, PAUSE_MIN),
        "rollenSchema": "fest per Vorname (Review 2 Nr. 5), Standortfilter als "
                        "Sicherheitsnetz",
    }

    # Review 2 Nr. 6: Morphs gibt es nicht mehr — Feld bleibt leer (Alt-Kompat.)
    morphs = []

    # ------------------------------------------------------------------
    # Takeaways (Review 2 Nr. 3 + 6 + 8):
    # Standzeit = Blockdauer (Ein 0,4 s nach Blockstart, Aus am Blockende),
    # danach derselbe Pausen-Takt wie bei den Plaketten.
    # ------------------------------------------------------------------
    tw_roh = []
    for idx in sorted(bloecke):
        b = bloecke[idx]
        hinweise = []
        ein_start = b["start"] + TW_EIN_VERZUG
        aus_start = b["ende"]                       # Ausblendung startet am Blockende

        if idx == 9:
            # Guardrail 1 (bleibt): Lara 101,0–103,8 s nie als Text ->
            # Text muss um 101,0 s vollständig unsichtbar sein.
            grenze = LARA_SPERRE - TW_AUS_DAUER
            if aus_start > grenze:
                aus_start = grenze
                hinweise.append("Guardrail 1: Lara-Sperre — Text ist um %.1f s "
                                "vollständig ausgeblendet, nichts vom "
                                "Bewerbungs-Satz" % LARA_SPERRE)
        if idx == 12:
            hinweise.append("Guardrail 7: Ciattei nur in abtrennbarer Sequence (ohneCiattei)")

        tw_roh.append({
            "id": "takeaway-%d" % idx,
            "block": idx,
            "einStart": r1(ein_start),
            "einDauer": TW_EIN_DAUER,
            "ausStart": r1(aus_start),
            "ausDauer": TW_AUS_DAUER,
            "gekuerzt": False,
            "verzoegert": False,
            "blockEnde": r1(b["ende"]),
            "hinweise": hinweise,
        })

    letzte_tw = tw_roh[-1]
    deadline_tw = r1(QUER_2[0] - QUER_VORLAUF)  # 133.36
    if letzte_tw["ausStart"] + letzte_tw["ausDauer"] > deadline_tw:
        letzte_tw["ausStart"] = r1(deadline_tw - letzte_tw["ausDauer"])
        log.append("Takeaway %d: Ausblendung auf %.2f s gezogen "
                   "(muss vor Quer-2-Blende %.2f s draußen sein)"
                   % (letzte_tw["block"], letzte_tw["ausStart"], deadline_tw))

    # Review 2 Nr. 3 (v4): Takeaways werden NIE gekürzt — reicht der Abstand
    # zum nächsten Block nicht, startet das NEUE Takeaway später. Das Aus-Ende
    # bleibt am Blockende (Ausnahmen: Lara-Sperre, letzter Block vor 134,0 s).
    tw_pausen = takte_pausen(tw_roh, "Takeaway", log, warnungen,
                             modus="verzoegern")

    # Guardrail (v4): Blockende-Deckung explizit prüfen, damit eine spätere
    # Timeline-Änderung nicht still wieder in die Kappung zurückfällt.
    for e in tw_roh:
        idx = e["block"]
        soll = e["blockEnde"]
        if idx == 9 or idx == tw_roh[-1]["block"]:
            continue          # Lara-Sperre / Endcard-Kante: bewusst früher
        if e["ausStart"] < soll - 1e-9:
            warnungen.append("WARNUNG: Takeaway %d — Ausblendung startet %.2f s "
                             "VOR dem Blockende (%.2f statt %.2f) — Review 2 "
                             "Nr. 3 verletzt"
                             % (idx, soll - e["ausStart"], e["ausStart"], soll))

    messen = text_breite_fabrik()
    if messen is None:
        log.append("HINWEIS: fontTools/TTF nicht verfügbar — Takeaway-"
                   "Breitenprüfung (Review 3 Nr. 1) übersprungen, alle "
                   "Takeaways bekommen %d px" % TW_GROESSE)

    takeaways = []
    tw_breiten = {}
    for e in tw_roh:
        idx = e["block"]
        b = bloecke[idx]
        tw = TAKEAWAYS[idx]
        aus_ende = r1(e["ausStart"] + e["ausDauer"])
        groesse, breit = takeaway_groesse(tw["zeilen"], idx, messen, log, warnungen)
        tw_breiten[idx] = breit
        takeaways.append({
            "block": idx,
            "person": b["person"],
            "kartentext": tw["kartentext"],
            "zeilen": tw["zeilen"],
            "seite": "links",           # Grafikfläche, unter der Headline
            "groessePx": groesse,
            "start": e["einStart"],
            # endeTon/endeStumm = Moment, in dem der Text VOLLSTÄNDIG weg ist
            # (die Composition fadet die letzten TW_AUS_DAUER Sekunden aus).
            "endeTon": aus_ende,
            "endeStumm": aus_ende,
            "austritt": {"start": e["ausStart"], "dauer": e["ausDauer"]},
            "pauseVorher": e["pauseVorher"],
            "vorgezogen": e["gekuerzt"],
            "verzoegert": e["verzoegert"],
            "blockEnde": e["blockEnde"],
            "deckungBlockende": r1(e["ausStart"] - e["blockEnde"]),
            "standzeit": r1(e["ausStart"] - (e["einStart"] + e["einDauer"])),
            "blockdauer": r1(b["ende"] - b["start"]),
            "revealDauer": TW_EIN_DAUER,
            "zeichen": zeichen_ohne_markup(tw["kartentext"]),
            "frameVon": f(e["einStart"]),
            "frameBisTon": f(aus_ende),
            "frameBisStumm": f(aus_ende),
            "ciattei": idx == 12,
            "hinweise": e["hinweise"],
        })

    takeaway_regeln = {
        "timing": "Review 2 Nr. 3: Einblendung block.start + %.1f s, Ausblendung "
                  "startet am Blockende — Takeaway steht, solange die Aussage "
                  "läuft. Keine Lesezeit-Kappung mehr." % TW_EIN_VERZUG,
        "takt": "Pause Ziel %.1f s / Minimum %.1f s zwischen Aus-Ende und "
                "nächstem Ein-Start (Review 2 Nr. 6). Anders als bei den "
                "Plaketten wird die Pause NICHT durch Kürzen des alten "
                "Takeaways erzeugt, sondern durch Verzögern des neuen — das "
                "Aus-Ende bleibt am Blockende (Review 2 Nr. 3)."
                % (PAUSE_ZIEL, PAUSE_MIN),
        "groesse": "Review 3 Nr. 1: EIN fester Grad %d px für ALLE Takeaways "
                   "(vorher 56/52/48 — die Versalhöhe sprang zwischen 38 und "
                   "42 px). Genau EINE Ausnahmestufe %d px, und nur wenn eine "
                   "Zeile in MAN Global Bold Condensed breiter als %d px würde. "
                   "Kein stufenloses Auto-Fit in der Composition."
                   % (TW_GROESSE, TW_GROESSE_AUSNAHME, TW_SPALTE_PX),
        "breitenMessung": {
            "spaltePx": TW_SPALTE_PX,
            "gemessen": "fontTools" if messen is not None else "übersprungen",
            "zeilenbreitePx": tw_breiten,
            "ausnahmestufe": [t["block"] for t in takeaways
                              if t["groessePx"] == TW_GROESSE_AUSNAHME],
        },
        "stumm": "endeStumm == endeTon (Blockdauer gilt in beiden Fassungen)",
    }

    # ------------------------------------------------------------------
    # Quer-Blenden-Kappung (v9 2026-07-29): vor jeder Öffnung ist die Fläche
    # textfrei — Takeaways und Plaketten enden >= QUER_VORLAUF vor der Blende.
    # ------------------------------------------------------------------
    for grenze in (QUER_1[0], QUER_2[0]):
        deadline = r1(grenze - QUER_VORLAUF)   # 64.4 bzw. 133.36
        for tw in takeaways:
            for key in ("endeTon", "endeStumm"):
                if tw[key] > deadline and tw["start"] < grenze:
                    tw[key] = deadline
            if tw["austritt"]["start"] + tw["austritt"]["dauer"] > deadline \
               and tw["start"] < grenze:
                tw["austritt"]["start"] = r1(deadline - tw["austritt"]["dauer"])
                tw["frameBisTon"] = f(deadline)
                tw["frameBisStumm"] = f(deadline)
        for p in plaketten:
            ende_p = p["austritt"]["start"] + p["austritt"]["dauer"]
            if ende_p > deadline and p["eintritt"]["start"] < grenze:
                p["austritt"]["start"] = r1(deadline - p["austritt"]["dauer"])
                p["frameBis"] = f(deadline)

    # CTA-Umbau 2026-07-29: das Video ist jetzt Recruiting — Laras Satz darf
    # als TEXT erscheinen. Takeaway 9 bleibt wie abgenommen (endeTon 101.0),
    # nur die stumme Fassung deckt den Block voll.
    for tw in takeaways:
        if tw["block"] == 9:
            tw["endeStumm"] = r1(bloecke[9]["ende"] + TW_AUS_DAUER)   # 103.80 + 0.4 = 104.2
            tw["frameBisStumm"] = f(tw["endeStumm"])

    # ------------------------------------------------------------------
    # Kapitel-Headlines (David 6+9): stehen DAUERHAFT, Wechsel reiner Fade.
    # Review 2 Nr. 2 (v4): Headline-Wechsel werden wie Plaketten sequenziert —
    # die alte Headline ist VOLLSTÄNDIG ausgeblendet, bevor die neue startet.
    # Vorher überlappten K3 (Aus-Ende 107,60) und K4 (Start 107,30) um 0,30 s,
    # und beide standen — frei im Bild, ohne Spotlight — übereinander.
    # ------------------------------------------------------------------
    head_roh = []
    for h in HEADLINES:
        head_roh.append({
            "id": "headline-%d" % h["kapitel"],
            "kapitel": h["kapitel"],
            "einStart": r1(h["start"]),
            "einDauer": HEAD_EIN_DAUER,
            "ausStart": r1(h["ende"]),
            "ausDauer": HEAD_AUS_DAUER,
            "gekuerzt": False,
            "quelle": h,
        })
    head_pausen = takte_pausen(head_roh, "Headline", log, warnungen,
                               modus="kuerzen",
                               pause_ziel=HEAD_PAUSE_ZIEL,
                               pause_min=HEAD_PAUSE_MIN,
                               min_stand=HEAD_MIN_STAND)

    # Quer-Blenden-Kappung für Headlines (Final-Review-Befund 2026-07-29):
    # Eine Headline, die in eine Quer-Blenden-Deadline hineinragt, muss
    # KOMPLETT unsichtbar sein, bevor die Blende öffnet. Deadline =
    # grenze − QUER_VORLAUF. Analoges Vorgehen wie bei Plaketten/Takeaways.
    for grenze in (QUER_1[0], QUER_2[0]):
        deadline = r1(grenze - QUER_VORLAUF)
        for e in head_roh:
            if e["einStart"] < grenze and e["ausStart"] + e["ausDauer"] > deadline + 1e-9:
                neu_aus = r1(deadline - HEAD_AUS_DAUER)
                log.append(
                    "Headline K%d: Ausblendung %.2f → %.2f s vorgezogen "
                    "(muss vor Quer-Blende %.2f s KOMPLETT draußen sein; "
                    "Deadline=%.2f, HEAD_AUS_DAUER=%.2f) [vorgezogen]"
                    % (e["kapitel"], e["ausStart"], neu_aus, grenze,
                       deadline, HEAD_AUS_DAUER)
                )
                e["ausStart"] = neu_aus
                e["gekuerzt"] = True

    # Eine Headline darf nie enden, solange ein Takeaway ihres Kapitels läuft
    # (die Composition liest die Zeilenzahl der Headline für Takeaway-Position
    # und -Grad aus kapitelKopf169(tw.start) — der Bezug muss stehen).
    for e in head_roh:
        for tw in takeaways:
            if e["einStart"] <= tw["start"] <= e["quelle"]["ende"] \
               and tw["start"] > e["ausStart"] + 1e-9:
                warnungen.append("WARNUNG: Headline K%d endet %.2f s, "
                                 "Takeaway %d startet aber erst %.2f s"
                                 % (e["kapitel"], e["ausStart"],
                                    tw["block"], tw["start"]))

    headlines = []
    for e in head_roh:
        h = e["quelle"]
        headlines.append({
            "id": e["id"],
            "typ": "headline",
            "kapitel": h["kapitel"],
            "kartentext": h["kartentext"],
            "zeilen": h["zeilen"],
            "seite": "links",
            "groessePx": 92,            # Cond Bold ~92 px
            "start": e["einStart"], "ende": e["ausStart"],
            "endeGeplant": r1(h["ende"]),
            "einDauer": e["einDauer"], "exitDauer": e["ausDauer"],
            "wechsel": "fade",          # David 4: keine Wipes — und ab v4
                                        # auch kein Slide (Review 2 Nr. 2)
            "vorgezogen": e["gekuerzt"],
            "pauseVorher": e["pauseVorher"],
            "frameVon": f(e["einStart"]),
            "frameBis": f(e["ausStart"] + e["ausDauer"]),
            "hinweis": "steht dauerhaft im Kapitel; darunter wechseln "
                       "Takeaways + Plaketten. KEINE Positions-Akzente und "
                       "KEIN X-Versatz mehr (Review 2 Nr. 2); Wechsel "
                       "sequenziell — nie zwei Headlines gleichzeitig",
        })

    # ------------------------------------------------------------------
    # Branding-Beat — DEAKTIVIERT (Review 2 Nr. 9).
    # Bleibt als Stub, damit die Composition bis zu ihrem Umbau nicht bricht.
    # ------------------------------------------------------------------
    branding = {
        "aktiv": False,
        "start": BRANDING[0], "ende": BRANDING[1],
        "frameVon": f(BRANDING[0]), "frameBis": f(BRANDING[1]),
        "eyebrow": "",
        "kartentext": "",
        "zeilen": [],
        "logo": "keins",
        "seite": "links",
        "hinweis": "Review 2 Nr. 9: »WILLKOMMEN BEI IHREM MAN SERVICE« UND das "
                   "Logo in Spotlight 1 ERSATZLOS entfernt — beide Spotlights "
                   "sind vollständig text- UND logofrei. Feld nur noch Stub für "
                   "die Composition (aktiv=false -> NICHT rendern).",
    }

    # ------------------------------------------------------------------
    # Spotlight-Momente (David 8) — die zwei sprechfreien Lücken.
    # Review 2: text- und logofrei (Nr. 9), Werkzeug-Silhouetten-Regen (Nr. 10),
    # Löwe links vollständig sichtbar (Nr. 1).
    # ------------------------------------------------------------------
    werkzeug_regen = {
        "aktiv": True,
        "formen": ["schraubenschluessel", "sechskant-mutter", "zahnrad",
                   "schraube", "ringschluessel", "maulschluessel"],
        "anzahl": 9,
        "opazitaet": [0.12, 0.18],
        "fallzeitSek": [14.0, 26.0],       # sehr langsam von oben herabfallend
        "groessePx": [70, 180],
        "rotationGradProSek": [-4.0, 4.0],
        "blurPx": 1.5,
        "zone": "Grafikfläche rechts (x 820–1920); über dem zentrierten Fenster max. 40 % der Opazität",
        "hinweis": "Review 2 Nr. 10: sehr dezent, nie ablenkend; weich ein-/"
                   "ausblenden mit der Spotlight-Hüllkurve",
    }
    spotlights = [
        {
            "id": "spotlight-1", "typ": "spotlight",
            "start": SPOTLIGHT_1[0], "ende": SPOTLIGHT_1[1],
            "frameVon": f(SPOTLIGHT_1[0]), "frameBis": f(SPOTLIGHT_1[1]),
            "textfrei": True, "logofrei": True,
            "beats": [],
            "werkzeugRegen": werkzeug_regen,
            "hinweis": "sprechfreie Lücke 1 (9,5–22,3); Headline-K1-Exit 9,8, "
                       "K2-Enter 21,8 überlappen weich. Review 2 Nr. 9: KEIN "
                       "Branding-Text, KEIN Logo. Löwe: linke Seite mit Kopf "
                       "vollständig sichtbar (Nr. 1)",
        },
        {
            "id": "rest-spotlight", "typ": "spotlight",
            "start": REST_SPOTLIGHT[0], "ende": REST_SPOTLIGHT[1],
            "frameVon": f(REST_SPOTLIGHT[0]), "frameBis": f(REST_SPOTLIGHT[1]),
            "textfrei": True, "logofrei": True, "beats": [],
            "werkzeugRegen": werkzeug_regen,
            "hinweis": "Rest der Ex-Lücke 7 nach der Quer-Strecke: Enter-Rampe "
                       "75,5–76,4 liegt UNSICHTBAR unter dem Vollbild, damit "
                       "die Blende bei 76,56 auf die zentrierte Position "
                       "schließt. Löwe links, Werkzeuge rechts.",
        },
    ]

    # ------------------------------------------------------------------
    # Dichte-Stufen als Amplituden-Hüllkurve (Ambient-Ebene)
    # Erster und letzter Punkt identisch -> loopfähig (Frame 3549 ≙ Frame 0);
    # beide Enden liegen jetzt in der Dunkelfläche (Review 2 Nr. 7).
    # ------------------------------------------------------------------
    dichte = [
        {"t": 0.0,   "amp": 0.3, "phase": "loop-start aus der Dunkelfläche"},
        {"t": 2.0,   "amp": 0.4, "phase": "kaltstart"},
        {"t": 9.5,   "amp": 0.8, "phase": "spotlight-1"},
        {"t": 22.3,  "amp": 0.6, "phase": "team-strecke"},
        {"t": QUER_1[0], "amp": 0.9, "phase": "quer-1-vollbild"},
        {"t": REST_SPOTLIGHT[0], "amp": 0.8, "phase": "rest-spotlight"},
        {"t": 89.9,  "amp": 0.55, "phase": "faszination"},
        {"t": 107.5, "amp": 0.25, "phase": "sohn-story-ruhigste-phase"},
        {"t": 118.6, "amp": 0.5, "phase": "ciattei-stolz"},
        {"t": QUER_2[0], "amp": 0.35, "phase": "quer-2-finale"},
        {"t": 164.92, "amp": 0.3, "phase": "schwarzblende"},
        {"t": ENDCARD_HERO, "amp": 0.45, "phase": "fullscreen-hero"},
        {"t": ENDCARD_AUSKLANG, "amp": 0.3, "phase": "ausklang in die Dunkelflaeche"},
        {"t": MASTER_DAUER, "amp": 0.3, "phase": "loop-ende (= Frame 0)"},
    ]

    # ------------------------------------------------------------------
    # Endcard-Sequenz (v9 2026-07-29: CTA-Recruiting-Endcard)
    # ------------------------------------------------------------------
    endcard = [
        {"typ": "blende-auf", "start": QUER_2[0], "ende": QUER_2[0] + BLENDE_DAUER,
         "frame": f(QUER_2[0]),
         "hinweis": "Quer-2 öffnet sich über %.1f s zum Vollbild (133,52–134,12 s). "
                    "Danach läuft das Video im Vollbild bis zur Schwarzblende."
                    % BLENDE_DAUER},
        {"typ": "schwarz", "start": SCHWARZ_AB, "ende": SCHWARZ_AB + 1.0,
         "frame": f(SCHWARZ_AB),
         "hinweis": "Ton-Ausblende im Haupt-Material ab %.2f s. Das V3-Quer-"
                    "Bild ist bereits ab 160,2 s schwarz (Abbinder-Dimmer); "
                    "das Abbinder-Logo blendet synchron mit dem Ton aus. "
                    "Dauer ca. 1 s bis ENDCARD_HERO." % SCHWARZ_AB},
        {"typ": "hero", "start": ENDCARD_HERO, "ende": ENDCARD_AUSKLANG,
         "frame": f(ENDCARD_HERO),
         "fullscreen": True,
         "kartentext": "GROSSES BEWEGEN **MIT MAN**",
         "zeilen": ["GROSSES BEWEGEN", "**MIT MAN**"],
         "cta": "JETZT BEWERBEN",
         "qr": {"asset": "qr-jobs-man-eu.png", "url": "JOBS.MAN.EU", "groesse": 480},
         "loewe": {"variante": "dunkel", "seite": "links"},
         "hinweis": "CTA-Recruiting-Endcard: 8 s Standzeit für QR-Scan. "
                    "Löwe rechtsblickend, dunkel, links. m/w/d-Pflicht (David-Regel 2026-07-15). "
                    "zeilen: expliziter Zweizeiler (Testframe-Kalibrierung 2026-07-29)."},
        {"typ": "ausklang", "start": ENDCARD_AUSKLANG, "ende": MASTER_DAUER,
         "frame": f(ENDCARD_AUSKLANG),
         "hinweis": "Hero klingt in die DUNKELFLÄCHE aus (Logo/Claim/Löwe weg). "
                    "Bei %.1f s steht exakt derselbe Zustand wie bei Frame 0 — "
                    "Loop-Naht." % MASTER_DAUER},
    ]
    # v10: Abbinder chronologisch zwischen blende-auf und schwarz einsortieren.
    endcard.insert(1, {
        "typ": "abbinder",
        "start": ABBINDER_LOGO_EIN[0], "ende": ENDCARD_HERO,
        "frame": f(ABBINDER_LOGO_EIN[0]),
        "logo": {"einStart": ABBINDER_LOGO_EIN[0],
                 "einEnde": ABBINDER_LOGO_EIN[1],
                 "ausStart": ABBINDER_LOGO_AUS[0],
                 "ausEnde": ABBINDER_LOGO_AUS[1],
                 "breite": ABBINDER_LOGO_BREITE,
                 "asset": "clients/man/logo-weiss.png"},
        "dimm": {"einStart": ABBINDER_DIMM[0], "einEnde": ABBINDER_DIMM[1]},
        "schwarzVoll": ABBINDER_SCHWARZ_VOLL,
        "hinweis": "Standard-Abbinder (MAN-CI Film-Ending, Kundenmail "
                   "2026-08-07): weißes MAN-Logo erscheint zentriert über "
                   "der letzten Fahrszene (Position/Größe konstant), der "
                   "Dimmer übernimmt die CI-Überblendung zu Schwarz und "
                   "verdeckt den harten V3-Material-Cut bei 160,2 s; Logo "
                   "steht 3,7 s auf Schwarz und blendet synchron zur "
                   "Ton-Ausblende (163,92–164,92) aus. Endcard ab 165,0 "
                   "unverändert."})
    loop = {
        "frame0": {
            "zustand": "Dunkelfläche (identisch mit %.1f s)" % MASTER_DAUER,
            "fensterEin": {"start": 0.0, "dauer": LOOP_FENSTER_EIN},
            "logo": "zone-a, blendet mit dem Fenster ein (0,2–0,8 s)",
            "ambientPhase": 0.0,
            "hinweis": "Block 1 startet bei 0,1 s; Headline K1 ab 0,4 s, "
                       "Takeaway 1 ab 0,5 s",
        },
        "frame%d" % (MASTER_FRAMES - 1): {
            "zustand": "Dunkelfläche — kein Fenster, kein Rahmen, kein Logo",
            "ambientPhase": "== 0 (ganze Loop-Perioden)",
        },
        "naht": "Review 2 Nr. 7: Endcard klingt in eine dunkle Fläche aus, "
                "Frame 0 startet aus derselben Dunkelfläche mit %.1f s "
                "Fenster-Fade-in — die Schleife bleibt nahtlos."
                % LOOP_FENSTER_EIN,
    }

    # ------------------------------------------------------------------
    # Quer-Strecken (v9 2026-07-29): 9:16-Vollbild-Momente im 16:9-Master.
    # ------------------------------------------------------------------
    quer_strecken = [
        {
            "id": "quer-1",
            "start": QUER_1[0], "ende": QUER_1[1],
            "frameVon": f(QUER_1[0]), "frameBis": f(QUER_1[1]),
            "oeffnungDauer": BLENDE_DAUER,
            "schliessen": {
                "start": r1(QUER_1[1] - BLENDE_DAUER),
                "dauer": BLENDE_DAUER,
                "ziel": "zentriert",
            },
            "bleibtOffen": False,
            "schwarzAb": None,
            "hinweis": "Quer-Strecke 1: Fenster öffnet Vollbild, schließt wieder "
                       "auf zentrierte Position. Grafik-Fläche vorher textfrei "
                       "(Deadline 64,40 s). Enter-Rampe für rest-spotlight "
                       "75,5–76,4 liegt unsichtbar unter dem Vollbild.",
        },
        {
            "id": "quer-2",
            "start": QUER_2[0], "ende": QUER_2[1],
            "frameVon": f(QUER_2[0]), "frameBis": f(QUER_2[1]),
            "oeffnungDauer": BLENDE_DAUER,
            "schliessen": None,
            "bleibtOffen": True,
            "schwarzAb": SCHWARZ_AB,
            "hinweis": "Quer-Strecke 2 (Finale, V3-Datei): bleibt offen — kein "
                       "Schließen. V3 schneidet bei 160,2 s hart auf Schwarz "
                       "(Abbinder-Dimmer verdeckt den Cut); Ton-Ausblende im "
                       "Haupt-Material bei %.2f s. Ab %.1f s CTA-Endcard."
                       % (SCHWARZ_AB, ENDCARD_HERO),
        },
    ]

    # ------------------------------------------------------------------
    # 5-s-Beat-Prüfung über 0–175 s — für BEIDE Varianten (mit/ohne Ciattei).
    # Review 2 Nr. 2: EINZIGER Füller-Typ ist 'licht-akzent' (Licht-Opazität,
    # bewegt nichts). 'typo-akzent' und 'zeilen-shift' sind ersatzlos raus.
    # Fenster ohne Licht-Trägerfenster werden NUR dokumentiert (offeneFenster) —
    # die dauerhafte Headline steht, die Fläche ist nie leer.
    # ------------------------------------------------------------------
    events = []  # (zeit, label, nur_ciattei)

    def ev(t, label, nur_ciattei=False):
        if 0.0 <= t <= MASTER_DAUER:
            events.append((round(t, 2), label, nur_ciattei))

    ev(0.0, "loop-start")
    for p in plaketten:
        ev(p["eintritt"]["start"], "plakette-%d-ein" % p["block"], p["ciattei"])
        ev(p["austritt"]["start"], "plakette-%d-aus" % p["block"], p["ciattei"])
    for t in takeaways:
        ev(t["start"], "takeaway-%d-reveal" % t["block"], t["ciattei"])
        ev(t["austritt"]["start"], "takeaway-%d-exit" % t["block"], t["ciattei"])
    for h in headlines:
        ev(h["start"], h["id"] + "-ein")
        ev(h["ende"], h["id"] + "-exit")
    for sp in spotlights:
        ev(sp["start"], sp["id"] + "-start")
        ev(sp["ende"], sp["id"] + "-ende")
        for bt in sp["beats"]:
            ev(bt["start"], sp["id"] + "-" + bt["typ"])
            if "ende" in bt:
                ev(bt["ende"], sp["id"] + "-" + bt["typ"] + "-ende")
    for e_ev in endcard:
        ev(e_ev["start"], "endcard-" + e_ev["typ"])
    # v10: Abbinder-Momente als Content-Events — größtes statisches Fenster
    # ist die Logo-Standzeit auf Schwarz 160,2–163,92 = 3,72 s.
    ev(ABBINDER_LOGO_EIN[0], "abbinder-logo-ein")
    ev(ABBINDER_LOGO_EIN[1], "abbinder-logo-voll")
    ev(ABBINDER_DIMM[0], "abbinder-dimm-ein")
    ev(ABBINDER_SCHWARZ_VOLL, "abbinder-schwarz-voll")
    ev(ABBINDER_LOGO_AUS[0], "abbinder-logo-aus")
    # v9: Quer-Blenden-Events + Schwarzblende
    for q in quer_strecken:
        ev(q["start"], q["id"] + "-blende-auf")
        ev(q["ende"], q["id"] + "-blende-zu")
    ev(SCHWARZ_AB, "schwarzblende")
    ev(MASTER_DAUER, "loop-ende")

    def in_quer(t0, t1):
        return any(q[0] - 0.2 <= t0 and t1 <= q[1] + 0.2
                   for q in (QUER_1, QUER_2))
    # Vollbild-Film IST Bewegtbild — Fenster innerhalb der Quer-Strecken
    # fliegen aus der 5-s-Prüfung raus.

    # Einziges Trägerfenster für Füller: laufendes Spotlight (Licht-Opazität).
    licht_fenster = [(sp["start"], sp["ende"]) for sp in spotlights]
    offene_fenster = []

    def beat_typ(t):
        """Subtiler Füller-Typ zur Zeit t — oder None (dann nur dokumentieren)."""
        for a, b in licht_fenster:
            if a + 0.3 < t < b - 0.3:
                return "licht-akzent"
        return None

    zeiten_alle = sorted(set(t for t, _, _ in events))
    zeiten_ohne = sorted(set(t for t, _, nc in events if not nc))

    def max_fenster(zeiten):
        return max(b - a for a, b in zip(zeiten, zeiten[1:]))

    zwischen_beats = []

    def fuelle_beats(zeiten, variante):
        """Füllt Fenster > 5 s mit licht-akzent — NUR wo ein Spotlight läuft.
        Quer-Strecken-Fenster ausgenommen (Vollbild IST Bewegtbild, v9).
        Sonst: dokumentieren (kein Text wird bewegt, Review 2 Nr. 2)."""
        basis = sorted(set(zeiten + [zb["start"] for zb in zwischen_beats]))
        for a, b in zip(basis, basis[1:]):
            delta = b - a
            if in_quer(a, b):
                continue  # Vollbild-Film läuft — keine Beat-Prüfung nötig
            if delta > BEAT_FENSTER + 1e-9:
                n = int(math.ceil(delta / BEAT_FENSTER)) - 1
                gefuellt = 0
                for j in range(1, n + 1):
                    t = round(a + delta * j / (n + 1), 2)
                    typ = beat_typ(t)
                    if typ is None:
                        continue
                    gefuellt += 1
                    zwischen_beats.append({
                        "start": t, "dauer": 0.8, "typ": typ, "frame": f(t),
                        "fuellt": "Fenster %.2f–%.2f s (%.2f s, Variante %s)"
                                  % (a, b, delta, variante),
                    })
                    log.append("Zwischen-Beat %s bei %.2f s eingefügt "
                               "(Fenster %.2f–%.2f s = %.2f s > 5 s, Variante %s)"
                               % (typ, t, a, b, delta, variante))
                if gefuellt < n:
                    eintrag = {
                        "von": r1(a), "bis": r1(b), "dauer": r1(delta),
                        "variante": variante,
                        "grund": "kein Licht-Trägerfenster (kein Spotlight) — "
                                 "Textbewegung als Füller ist seit Review 2 Nr. 2 "
                                 "verboten",
                        "akzeptiert": True,
                        "hinweis": "dauerhafte Kapitel-Headline steht in diesem "
                                   "Fenster — Fläche ist nie leer (David: "
                                   "akzeptabel)",
                    }
                    if eintrag not in offene_fenster:
                        offene_fenster.append(eintrag)
                        log.append("OFFENES FENSTER (akzeptiert): %.2f–%.2f s "
                                   "(%.2f s, Variante %s) ohne Content-Event — "
                                   "kein Spotlight, also KEIN Füller; Headline steht"
                                   % (a, b, delta, variante))

    max_vorher_alle = max_fenster(zeiten_alle)
    max_vorher_ohne = max_fenster(zeiten_ohne)
    fuelle_beats(zeiten_alle, "mit-ciattei")
    fuelle_beats(zeiten_ohne, "ohne-ciattei")
    zwischen_beats.sort(key=lambda zb: zb["start"])

    beat_zeiten = [zb["start"] for zb in zwischen_beats]
    max_nachher_alle = max_fenster(sorted(set(zeiten_alle + beat_zeiten)))
    max_nachher_ohne = max_fenster(sorted(set(zeiten_ohne + beat_zeiten)))
    # „bestanden" = keine echten Warnungen (Takt/Überlappung/Rollen).
    # Offene 5-s-Fenster sind seit Review 2 Nr. 2 ausdrücklich akzeptiert.
    bestanden = not warnungen
    beat_check = {
        "regel": "Zielwert: kein Fenster > 5,0 s ohne Content-Event (Basis "
                 "Fassung 'ton'; geprüft mit UND ohne Ciattei-Elemente). "
                 "Füller ist seit Review 2 Nr. 2 AUSSCHLIESSLICH 'licht-akzent' "
                 "(Licht-Opazität, bewegt nichts) — 'typo-akzent' und "
                 "'zeilen-shift' sind ersatzlos entfernt. Fenster ohne Spotlight "
                 "werden NICHT gefüllt, sondern in offeneFenster dokumentiert.",
        "geprueft": "0,0–%.1f s (Quer-Strecken ausgenommen: Vollbild IST "
                    "Bewegtbild)" % MASTER_DAUER,
        "contentEvents": len(zeiten_alle),
        "contentEventsOhneCiattei": len(zeiten_ohne),
        "maxFensterVorher": r1(max_vorher_alle),
        "maxFensterVorherOhneCiattei": r1(max_vorher_ohne),
        "eingefuegteBeats": len(zwischen_beats),
        "beatTypen": sorted(set(zb["typ"] for zb in zwischen_beats)),
        "maxFensterNachher": r1(max_nachher_alle),
        "maxFensterNachherOhneCiattei": r1(max_nachher_ohne),
        "offeneFenster": offene_fenster,
        "warnungen": warnungen,
        "bestanden": bestanden,
        "log": log,
    }

    def minmax(werte):
        return ({"min": min(werte), "max": max(werte)} if werte
                else {"min": None, "max": None})

    takt_check = {
        "regel": "Review 2 Nr. 6: zwischen Ausblende-Ende der alten und "
                 "Einblende-Start der neuen mindestens %.1f s (Ziel %.1f s); "
                 "nie zwei gleichzeitig sichtbar. Headlines mit eigenem, "
                 "kürzerem Takt (min %.1f s / Ziel %.1f s), aber derselben "
                 "Nicht-Überlappungs-Regel (Review 2 Nr. 2, v4)."
                 % (PAUSE_MIN, PAUSE_ZIEL, HEAD_PAUSE_MIN, HEAD_PAUSE_ZIEL),
        "plaketten": minmax(plak_pausen),
        "takeaways": minmax(tw_pausen),
        "headlines": minmax(head_pausen),
        "plakettenVorgezogen": [p["block"] for p in plaketten if p["vorgezogen"]],
        "takeawaysVorgezogen": [t["block"] for t in takeaways if t["vorgezogen"]],
        "takeawaysVerzoegert": [t["block"] for t in takeaways if t["verzoegert"]],
        "headlinesVorgezogen": [h["kapitel"] for h in headlines if h["vorgezogen"]],
        "takeawayDeckungBlockende": {
            "regel": "Review 2 Nr. 3: Ausblendung startet am Blockende "
                     "(Δ = 0,00). Ausnahmen: Block 9 (Lara-Sperre 101,0 s) "
                     "und der letzte Block (Quer-2-Kappung 133,36 s).",
            "delta": {t["block"]: t["deckungBlockende"] for t in takeaways},
        },
    }

    plan = {
        "meta": {
            "projekt": "MAN Wartezimmervideo — 16:9-Master",
            "quelle": "timeline.json (12 Blöcke, 11 Lücken, 134,0 s)",
            "konzept": "Animations-Konzept-16x9.md v2.2, überstimmt durch Davids "
                       "Umbau-Entscheidungen 2026-07-24 und REVIEW 2 "
                       "(2026-07-24 nachts, 12 Punkte)",
            "review2": [
                "Nr. 2 typo-akzent + zeilen-shift ersatzlos raus (keine Text-Bewegung); "
                "v4: Headline-Wechsel ohne X-Versatz UND sequenziell (K3 endet "
                "vor K4, keine Doppel-Headline mehr)",
                "Nr. 3 Takeaway steht die ganze Blockdauer (Ein +0,4 s, Aus am "
                "Blockende); v4: Pausen entstehen durch Verzögern des NEUEN "
                "Takeaways, nie durch Kürzen des alten",
                "Nr. 5 festes Rollen-Schema per Vorname",
                "Nr. 6 Plaketten/Takeaways sequenziell mit Pause >= 0,8 s (Ziel 1,0 s)",
                "Nr. 7 (überholt in v9): Endcard jetzt 165,0–173,0 aus der Schwarzblende, "
                "Ausklang bis 175,0",
                "Nr. 8 neue Takeaway-Texte",
                "Nr. 9 Spotlights text- UND logofrei (Branding-Beat deaktiviert)",
                "Nr. 10 Werkzeug-Silhouetten-Regen in den Spotlights",
                "Nr. 12 Takeaways kleiner (56/52 px)",
                "v9 2026-07-29: Quer-Strecken + CTA-Endcard + Löwe rechtsblickend + Untertitel",
                "v10 2026-08-07: Quer-Datei V3 (Kunden-Schnitt: mehr TGE, weniger "
                "Winter/E-Truck, Schwertransporter raus, hartes Schwarz ab 160,2) "
                "+ Standard-Abbinder (MAN-CI Film-Ending) im Finale vor der "
                "Endcard — Master bleibt 175,0 s",
            ],
            "fps": FPS,
            "masterDauer": MASTER_DAUER,
            "masterFrames": MASTER_FRAMES,
            "videoFrames": VIDEO_FRAMES,
            "querStrecken": [{"id": q["id"], "start": q["start"], "ende": q["ende"]}
                             for q in quer_strecken],
            "fassungen": ["ton", "stumm"],
            "loopHinweis": "LOOP-NAHT: Die Endcard klingt %.1f–%.1f s in eine "
                           "dunkle Fläche aus (kein Fenster, kein Rahmen, kein Logo). "
                           "Frame 0 startet aus exakt derselben Dunkelfläche; das "
                           "Fenster blendet 0,0–%.1f s ein. Frame %d ≙ Frame 0 — "
                           "die Schleife läuft ohne sichtbaren Sprung."
                           % (ENDCARD_AUSKLANG, MASTER_DAUER, LOOP_FENSTER_EIN,
                              MASTER_FRAMES - 1),
            "hinweis": "Zeiten in Sekunden (Video-Zeit), frame* = 25-fps-Frames. "
                       "endeTon/endeStumm = Moment, in dem der Text vollständig "
                       "unsichtbar ist (Exit-Fade eingerechnet). "
                       "travels/wische/kapitelMarken/bridge/morphs sind LEER "
                       "(nur Alt-Kompatibilität) — neue Wahrheit: fenster, "
                       "querStrecken, headlines, spotlights, loewe, endcard, untertitel. "
                       "branding.aktiv=false -> NICHT rendern (Review 2 Nr. 9). "
                       "fenster.ausblendung=null: durch Quer-Blende ersetzt (v9).",
        },
        "fenster": fenster,
        "fensterSeiten": fenster_seiten,
        "querStrecken": quer_strecken,
        "travels": [],        # Alt-Kompatibilität, LEER (David 8: kein Travel)
        "loewe": loewe,
        "plakettenRegeln": plaketten_regeln,
        "plaketten": plaketten,
        "morphs": morphs,     # Alt-Kompatibilität, LEER (Review 2 Nr. 6)
        "takeawayRegeln": takeaway_regeln,
        "takeaways": takeaways,
        "headlines": headlines,
        "spotlights": spotlights,
        "branding": branding,
        "kapitelMarken": [],  # Alt-Kompatibilität, LEER (ersetzt durch headlines)
        "bridge": [],         # Alt-Kompatibilität, LEER (ersetzt durch spotlight-2)
        "wische": [],         # Alt-Kompatibilität, LEER (David 4: keine Wische)
        "dichte": dichte,
        "endcard": endcard,
        "loop": loop,
        "zwischenBeats": zwischen_beats,
        "beatCheck": beat_check,
        "taktCheck": takt_check,
    }
    plan["untertitel"] = untertitel_segmente(
        [bloecke[i] for i in sorted(bloecke)], log.append
    )

    eintraege = (1 + len(fenster_seiten) + len(plaketten) + len(morphs)
                 + len(takeaways) + len(headlines) + len(spotlights) + 1
                 + len(dichte) + len(endcard) + 1 + len(zwischen_beats))
    plan["meta"]["eintraege"] = eintraege

    out_motion = os.path.normpath(OUT_MOTION)
    for path in (out_motion, OUT_LOCAL):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(plan, fh, ensure_ascii=False, indent=1)
            fh.write("\n")

    print("sync-plan geschrieben:")
    print("  " + out_motion)
    print("  " + OUT_LOCAL)
    print("Einträge gesamt: %d" % eintraege)
    print("Beat-Prüfung (beide Varianten): vorher max %.2f s (mit) / %.2f s (ohne Ciattei), "
          "%d Zwischen-Beats (%s), nachher max %.2f s (mit) / %.2f s (ohne)"
          % (max_vorher_alle, max_vorher_ohne, len(zwischen_beats),
             ", ".join(beat_check["beatTypen"]) or "keine",
             max_nachher_alle, max_nachher_ohne))
    print("Takt-Prüfung: Plaketten-Pausen min %.2f s / max %.2f s, "
          "Takeaway-Pausen min %.2f s / max %.2f s"
          % (takt_check["plaketten"]["min"], takt_check["plaketten"]["max"],
             takt_check["takeaways"]["min"], takt_check["takeaways"]["max"]))
    print("Vorgezogene Ausblendungen: Plaketten %s, Takeaways %s"
          % (takt_check["plakettenVorgezogen"] or "—",
             takt_check["takeawaysVorgezogen"] or "—"))
    for line in log:
        print("  " + line)
    print("Offene 5-s-Fenster (akzeptiert, nur dokumentiert): %d"
          % len(offene_fenster))
    print("Status: %s" % ("BESTANDEN" if bestanden else "NICHT BESTANDEN"))
    if warnungen:
        for w in warnungen:
            print("  " + w)
    return 0 if bestanden else 1


if __name__ == "__main__":
    sys.exit(main())
