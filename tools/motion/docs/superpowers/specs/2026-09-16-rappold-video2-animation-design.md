# Rappold Video 2 „Kfz-Mechatroniker" — Animationen „Freie Typo" (Design)

Stand 2026-09-16, Entscheidungen im Chat (Session 16.09.). Grundlage: Schnitt
`Video 2 - Kfz-Mechatroniker - Recruiting_V1.mp4` (NAS `04_Exportiert/…`,
Kopie in `projects/Autohaus Rappold/Recruiting und Imagefilm/2026-09 Dreh 02.09/Material/Video/`),
1080×1920, 25 fps, 57,6 s = 1440 Frames.

## Entscheidungen (User 16.09.)

- **Stil „Freie Typo":** große weiße Versalwörter direkt aufs Bild, blaue
  Akzentwörter, keine Flächen/Kästen. Lesbarkeit über Schatten und lokale,
  textgroße Abdunklung (Luminanz-Gates `docs/motion-doctrine.md` §5).
- **Untertitel mit in derselben Datei** (Lieferformat wie Craiss
  „Alpha-Komplett": eine Alpha-Datei mit allen Grafiken + Untertiteln).
- **Endcard: 5 s deckend an den Schnitt, wie er ist** → Gesamtlänge 62,6 s
  (1565 Frames). Bewusste Ausnahme vom 60-s-Standard.
- **CI bestätigt:** Logo-Blau `#0D69B3`, Anthrazit `#434F4F`, Hellgrau
  `#EBE9E8`, Weiß; Schrift Open Sans (Website-Dateien v29, Schnitte 600/800).

## Feste Regeln

- Inhalte nur Website-belegt oder aus dem freigegebenen Schnittplan
  (Quellen-Tabelle unten). Keine Benefits-Liste (Konzept: „keine
  Knaller-Benefits"), keine Zeitangabe als Grafik, nichts aus der
  Familiengeschichte, keine VW-Logos in der Grafik.
- Untertitel: ganze Sinneinheiten, nie ein Wort vor dem Sprechen, keine
  inhaltliche Dopplung mit Grafiken (David-Regeln); max. 2 Zeilen je Seite.
- Gesicht und Hals frei: Textoberkante ≥ Kinn + 110 px (Kinn je Einstellung aus
  Vision-Gesichtsboxen); Unterkante ≤ 1500 px (78 %, Plattform-UI), Rand
  links/rechts ≥ 54 px — wie das freigegebene Craiss-System.
- Ruhige Bewegung: kein Bounce/Overshoot, nur transform + opacity.
- `(M/W/D)` am Berufstitel in CTA und Endcard.

## Wortlaut-Korrekturen (Scribe-Schnitt vs. Original-Interview + Whisper)

| Stelle | Scribe (Schnitt) | gesetzt | Beleg |
|---|---|---|---|
| 19,3 s | „Ja geil, bin wieder am Arbeitsplatz." | „Ja, geil, wieder am Arbeitsplatz." | FX3_1011 + Whisper |
| 32,6 s | „eine Stunde, jetzt anderthalb." | „eine Stunde bis anderthalb." | FX3_1011 + Whisper |
| 50,1 s | „und man weiß ja auch" | „und dann weiß ich auch" | FX3_1013 + Whisper |

## Typo-System

| Rolle | Schnitt | Größe (Basis 1080) | Farbe |
|---|---|---|---|
| Untertitel-Grundzeile | Open Sans 600, gemischt | 56 px, Zeilenhöhe 1,18, max. 920 px breit | Weiß |
| Untertitel-Hero (Kernwort im Satz) | Open Sans 800, Versal | 120–150 px | Weiß oder Blau |
| Grafik-Kicker | Open Sans 600, Versal, Sperrung 0,18 em | 30 px | Weiß 90 % |
| Grafik-Titel | Open Sans 800, Versal, Sperrung −0,02 em | 96–150 px | Weiß, Akzentwort Blau |
| Blaue Linie (Grafik-Signatur) | Fläche 64×8 px | — | `#0D69B3` |

- Grafiken sind **linksbündig** mit blauer Linie + Kicker (Signatur aus dem
  Logo: Text links, Linie), Untertitel **zentriert** — so bleiben beide Ebenen
  unterscheidbar.
- Schatten auf allem Text: `0 3px 18px rgba(0,0,0,.45), 0 1px 3px rgba(0,0,0,.5)`;
  blaue Glyphen zusätzlich mit weichem dunklem Halo.
- Lokale Abdunklung (radial, textblockgroß, 25–40 %) nur, wo der Hintergrund
  hell ist (gemessene Luma im Textfeld > 150).

## Bewegung

- Grundzeile: Wort für Wort am Wortanfang, 12 px Anstieg + Einblendung 5 Frames.
- Hero: landet am Wortanfang, Skalierung 0,94 → 1 über 7 Frames, `easeOut` kubisch.
- Grafik-Einstieg: Linie zeichnet (scaleX 0 → 1, 8 Frames) → Kicker blendet
  auf → Titelwörter wischen aus einer Maske hoch (translateY 100 % → 0,
  10 Frames, 3 Frames Versatz).
- Ausstieg 6 Frames (Deckkraft + 12 px nach oben), nie mitten im Wort.
- CTA → Endcard: Titel und „JETZT EINTRAGEN" gleiten (inOut, 14 Frames) auf ihre
  Endcard-Positionen, während der Grund einblendet.

## Ablauf (Zeiten = Schnitt V1)

| Zeit | Einstellung / O-Ton | Ebene | Inhalt |
|---|---|---|---|
| 0,08–4,90 | Hannes Nah/Totale: Hook | Untertitel mit Heroes | „…da war man eine **NUMMER**, war man **ERSETZBAR**." · „Hier weiß man, man ist **WICHTIG**." (blau) |
| 4,92–7,48 | Drohne + Fassade (Musik) | Grafik | Kicker „AUTOHAUS RAPPOLD · BLAUFELDEN", Titel **SEIT 1911** |
| 7,80–10,74 | Hannes stellt sich vor | Grafik + UT | **HANNES** / KFZ-MECHATRONIKER; UT nur „Bin seit 2013 hier im Autohaus Rappold." |
| 11,08–14,40 | Christos stellt sich vor | Grafik + UT | **CHRISTOS** / KFZ-MECHATRONIKER; UT nur „Bin seit fünf Jahren beim Autohaus Rappold." |
| 14,4–17,1 | helle Halle (Musik) | Grafik | **WERKSTATT WIE 1995?** → **MODERNER ARBEITSPLATZ.** (Akzent blau) |
| 17,28–41,32 | Hannes/Christos, Halle, Vermessbühne, Geschäftsleitung | Untertitel | Heroes: **VIEL PLATZ** (24,3), **VERSTANDEN** (40,5, blau); Rest Grundzeile |
| 41,36–43,3 | Rad-/Reifen-B-Roll (Sprechpause) | Grafik | Titel **FAMILIENGEFÜHRT**, Unterzeile „RUND 30 MITARBEITENDE" |
| 42,56–46,02 | Hannes: „keine Steine in den Weg" | Grafik + UT | **QUALITÄT** (blau) **VOR QUANTITÄT** ab 43,4 über der Totale |
| 46,90–51,86 | Christos: „mit den Leuten…", Abklatschen | Grafik + UT | **ECHTER TEAMGEIST** ab 50,1 |
| 51,92–57,50 | Hannes-CTA | Grafik + UT | Kicker „OFFENE STELLE", **KFZ-MECHATRONIKER** + „(M/W/D)" ab „Schrauber"; UT „Also wenn du Schrauber bist … komm vorbei,"; **JETZT EINTRAGEN** ab „trag dich ein" (UT dafür raus); UT „Wir freuen uns auf dich." |
| 57,60–62,60 | Endcard (deckend) | Grafik | Grund: letztes Schnittbild eingefroren, weichgezeichnet, abgedunkelt; weißes Logo, KFZ-MECHATRONIKER (M/W/D), JETZT EINTRAGEN, `autohaus-rappold.de/karriere` |

Änderungen gegenüber dem Chat-Entwurf (Folge der Untertitel-Entscheidung):
- Der Hook-Titel „WERKSTATT WIE 1995?" wandert von 0 s an die erste
  Hallen-Einstellung (14,4 s) — im Nah-Hook ist kein Platz für zwei Textebenen,
  und die helle Halle beantwortet die Frage im Bild.
- „ACHSVERMESSUNG" entfällt: der Untertitel sagt „vermessen und eingestellt"
  (inhaltliche Dopplung).
- „FAMILIENGEFÜHRT · RUND 30 MITARBEITENDE" liegt in der Sprechpause nach
  „verstanden." (ab 41,36 s) statt über dem dichten Geschäftsleitungs-Satz.

## Quellen je Grafik

| Grafik | Beleg |
|---|---|
| SEIT 1911 · Blaufelden | `historie` („Im Jahre 1911 …"), Kontakt „Im Riedle 4, 74572 Blaufelden" |
| Namen + Beruf | Schnittplan 14.09. (Vorname reicht) |
| WERKSTATT WIE 1995? | Konzept-Titel Video 2 |
| MODERNER ARBEITSPLATZ | `karriere` → Benefits „Moderner Arbeitsplatz" |
| FAMILIENGEFÜHRT · RUND 30 MITARBEITENDE | `karriere` („familiengeführter VW- und Audi-Partner mit rund 30 Mitarbeitenden") |
| QUALITÄT VOR QUANTITÄT | Schnittplan-Caption #9 (Hannes FX3_1012 10:39,6) |
| ECHTER TEAMGEIST | `karriere` („… Verlässlichkeit und echten Teamgeist") |
| Endcard-URL | `https://www.autohaus-rappold.de/karriere/` existiert; Formular-URL beim Kunden offen → Prop |

## Technik

- Motion-Client `rappold` (`tools/motion/src/clients/rappold/`), Fonts und Logos
  in `public/clients/rappold/`.
- Komposition `Rappold-V2-Mechatroniker-Alpha` (transparent, 1080×1920 Basis,
  25 fps, 1565 Frames) + `…-Vorschau` (mit Schnitt als Hintergrund, Proxy mit
  dichten Keyframes).
- Daten: `daten-generiert.ts` (Wörter + Einstellungen mit Kinnlinie, per
  `scripts/rappold-v2-daten.ts`), `untertitel-plan.ts` (Sätze, Seiten, Heroes)
  und `grafik-plan.ts` (Zeiten, Texte, Positionen) — Zeiten in Frames des Schnitts V1.
- Alpha-Komposition im Format `portrait-4k` (2160×3840, Inhalt auf 1080er-Basis
  uniform skaliert) als ProRes 4444 mit Alpha (wie Craiss), gerendert aus dem
  Bundle `build-rappold` (Spiegel `public-rappold`) nach `Ergebnisse/Renders/`.

## Prüfung vor Abgabe

- Kontaktbogen je Untertitel-Seite und Grafik (Anfang/Mitte/Ende) über dem Schnitt.
- Gesichts-Check automatisch: Vision-Gesichtsboxen (jedes 5. Frame) gegen die
  Alpha-Maske eines Prüfrenders, kritisch < 60 px Abstand bei 1080p.
- Luma-Check der Textfelder (Lesbarkeit), Grenze 1500 px, Ränder 54 px.
- `npx tsc --noEmit`; Guides aus vor dem Final-Render.

## Offen beim Kunden

Endcard-/Formular-URL · „geil" im O-Ton (steht auch im Untertitel) ·
Freigabe „QUALITÄT VOR QUANTITÄT" (Schnittplan-Caption, nicht wörtlich auf der Website).

## Feedback-Runde 1 (16.09.2026, User)

- Namen raus → Vorstellungssätze als Untertitel.
- CTA ohne Person: eigene Karte auf Rappold-Blau nach dem Schnitt, Übergang Anthrazit→Blau-Wisch von unten über Hannes' letzte 16 Frames; Karte: Logo weiß, OFFENE STELLE, KFZ-MECHATRONIKER (M/W/D), JETZT EINTRAGEN, URL (alles weiß).
- Schatten klein (8–10 px), Abdunklung eng an Wort/Zeile statt Block.
- Untertitel-Lage fest je Seite, Wechsel nur auf Schnitten; kein Ausblenden während Sprache.
- Zusätzliche blaue Akzente: „Arbeit", „Geschäftsleitung", „Schrauber" (ExtraBold, nur auf Personen-Einstellungen) + blaue CTA-Karte.
