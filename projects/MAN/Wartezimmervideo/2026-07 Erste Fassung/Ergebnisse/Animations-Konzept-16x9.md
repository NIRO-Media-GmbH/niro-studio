# Animations-Konzept — 16:9-Master (MAN Wartezimmervideo) · v2

**Stand:** 2026-07-24 · **Status:** v2 nach Davids Design-Feedback (MAN-Web-Look, durchgängige Animation, Takeaways statt Voll-Zitate)
**Basis:** Verbindliche Timeline `_intern/final-16x9/timeline.json` (12 Blöcke, 11 Lücken, 134,0 s)
**Fixierte Entscheidungen (David):** Passepartout-Prinzip · Endcard angehängt · Lara-Audio bleibt (Text-Sperre ab 101,0 s) · Jonathan bewusst draußen · **NEU 2026-07-24 abends:** sehr nah am originalen MAN-Web-Style · nie länger als 5 s statisch · ALLE Aussagen als kurze Einblendung — nie 1:1 der volle Satz, sondern Zusammenfassung des Inhalts.

## 1 · Prinzip

Davids fertiger 9:16-Schnitt läuft per `OffthreadVideo` in Remotion; Remotion
rendert das komplette 16:9-Master. Die Bühne ist datengetrieben aus
`timeline.json` + `sync-plan.json`.

**Neu in v2 — zwei Grundsätze aus Davids Feedback:**
1. **Design = MAN-Web** (man.eu, verifiziert per Browser-Sichtung 2026-07-24;
   Assets von David in `Material/`: komplette MAN-Global-Familie inkl. Thin,
   Logos weiß/schwarz, Löwen-Silhouette `löwe-halb.jpg`).
2. **Durchgängige Animation:** Kein Zustand steht länger als 5 s. Die Garantie
   kommt aus dem System (§4), nicht aus handgesetzten Einzel-Events.

## 2 · Design-Sprache MAN-Web (Tokens)

Beobachtet auf man.eu (Homepage, Produkt-Cards, Hero, 404):

| Token | Wert |
|---|---|
| Anthrazit (Basisfläche dunkel) | #2E3A46 (Panels), Abstufung #222C36 (tiefer) |
| Hellgrau (Basisfläche hell) | #F5F6F7 — nur für Endcard-/Trenner-Akzente, sparsam |
| MAN-Rot (NUR Akzent) | #E30045 — Balken, Unterstriche, CTA-Flächen, nie großflächig als Hintergrund |
| Typo Headline | MAN Global **Bold Condensed, IMMER VERSALIEN**, eng gesetzt — weiß auf dunkel, Anthrazit auf hell |
| Typo Sekundär | MAN Global Regular/Light (Davids Lieferung enthält auch Thin/Light für feine Größen) |
| Kanten | **Alles scharfkantig — border-radius 0** (Website hat keinerlei Rundungen; der bisherige Radius 20 und brand.json-Radius 12 gelten für dieses Projekt nicht) |
| Signature-Elemente | Rote **vertikale Balken** vor Listenzeilen · roter **Tab-Unterstrich** (aktiv) · **Slider-Striche** (roter aktiver Strich, graue inaktive) · **überlappende Panels** (Anthrazit-Block schiebt sich versetzt über/unter Foto) · **Löwe** als großes, angeschnittenes Artwork |
| Buttons/Chips | Scharfkantige Rot-Fläche, weiße Bold-Versalien mit Letterspacing (für uns: nur als Stil-Referenz für Chips — keine CTAs im Video) |

Die Bühne wird damit: **Anthrazit-Grund** (nicht mehr Bordeaux #12000A),
weiße Condensed-Versalien, rote Präzisions-Akzente, harte Kanten,
Panel-Versatz-Layouts wie auf der Website, Löwe als wiederkehrendes
Grafik-Motiv (angeschnitten von der Kante, Ton-in-Ton Anthrazit oder Rot).

## 3 · Geometrie (Design-Auflösung 1920×1080)

- **Fenster:** 576×1024 (exakt 9:16), y=28, **scharfkantig (Radius 0)**,
  `overflow: hidden`. Positionen: links x=132, rechts x=1212.
  Kanten-Behandlung statt Rundkontur: **roter Vertikal-Balken 8 px** an der
  fensterabgewandten... an der Innenkante (zur Grafikfläche zeigend, wie die
  MAN-Listen-Balken), plus ein um +20/+20 versetztes **Anthrazit-Panel**
  (#222C36) hinter dem Fenster — das Überlapp-Pattern der Website.
- **Grafikspalte:** Fenster links → x=784–1856; Fenster rechts → x=64–1136.
- **Zonen:** A Logo y=64–208 · B Inhalt y=260–900. **Keine Zone C mehr:**
  Kapitel-Tabs und Fortschritts-/Aussagen-Striche sind auf Davids Wunsch
  (2026-07-24) komplett gestrichen — keine permanente Orientierungsleiste.
- **Logo:** IMMER die Bilddatei (`MANlogoWeiss.png` aus Davids Lieferung),
  **nie gesetzter Schriftzug**. Zone A: 240 px breit.
- **Sprecher-Plakette:** scharfkantiger Anthrazit-Chip (#222C36, 92 %) an der
  Fensterkante (28 px Überlapp), y=824, H=120: **roter Vertikal-Balken 8 px
  links**, Name MAN Global Cond Bold 44 VERSALIEN Weiß, Rolle MAN Global
  Regular 34 Weiß. Bei Fenster rechts gespiegelt.
- **Takeaway-Zeilen** (Zone B): 1–2 Zeilen MAN Global Cond Bold VERSALIEN
  ~76 px Weiß, Schlüsselwort in Rot, mit rotem Vertikal-Balken links —
  exakt das Listen-Pattern der Website in groß.

## 4 · Motion-System — „nie länger als 5 s still"

Die 5-s-Garantie kommt aus zwei **immer aktiven Ebenen** (die frühere
Echtzeit-Leiste ist mit den Tabs gestrichen):

1. **Ambient-Ebene:** langsame Bewegung im Hintergrund — eine feine rote
   Linie, die pro Kapitel einmal durch die Fläche wandert, dezente
   Helligkeits-Modulation des Versatz-Panels. Ganze Loop-Perioden über die
   Master-Dauer (Root-Ebene, §8). **Kein Löwen-Wasserzeichen:** der Löwe
   ist kein Ambient-Element (Ton-in-Ton war nicht erkennbar — David),
   sondern tritt nur in den Marken-Momenten auf, dann groß und eindeutig
   (§6, Guardrail 12); dort darf er langsam driften (Parallax).
2. **Content-Ebene:** Takeaway pro Block (alle ~6–12 s ein Wechsel),
   Plaketten-Morphs in den Mikro-Lücken, Kapitel-Wipes, Fenster-Travels.
   Zusätzliche Beat-Regel: liegen zwischen zwei Content-Events mehr als 5 s,
   füllt der sync-plan-Generator einen **Zwischen-Beat** ein (Zeilen-Shift
   des Takeaways, Löwen-Akzent, Balken-Puls) — maschinell geprüft über die
   vollen 142 s, kein Fenster > 5 s ohne sichtbare Veränderung.

Weiter gültig: Travels/Wipes/Voll-Exits nur in Lücken; Plaketten-Morphs am
Lückenstart (Naht 9→10: 0,2-s-Überlapp-Ausnahme); SMOOTH-Springs
(damping 20, stiffness 100, overshootClamping), Einstiege +12–24 px,
kein Bounce, kein Scale auf Typo; Akzent-Wisch `min(0,6 s, Lückendauer)`.
Die frühere „Ruhe-Dramaturgie" (18 s textfrei, Sohn-Story ganz still) ist
durch Davids 5-s-Vorgabe ersetzt — die Sohn-Story wird weiterhin am
ruhigsten inszeniert (nur Ambient + späte, kurze Takeaway-Zeile), aber
nie eingefroren.

## 5 · Takeaway-System (ersetzt die wörtlichen Zitat-Momente)

**Davids Vorgabe:** Jede Aussage wird einmal kurz eingeblendet (Stumm-Läufe
im Wartezimmer!), aber **nie der volle Satz 1:1 — immer eine Zusammenfassung
des Inhalts.** Wortsynchroner Aufbau entfällt (der setzte Wörtlichkeit
voraus); stattdessen Zeilen-Reveal beim Blockstart, Standzeit nach
Lesezeit-Regel `min(Blockdauer − 0,5 s, max(3,5 s, Zeichen/12))`.

Vorschlagsliste (zur Abnahme durch David, lebt in sync-plan.json als
`kartentext`):

| # | Person | Takeaway (VERSALIEN im Render) |
|---|---|---|
| 1 | Julia | Qualität heißt hier: **100 %** — von Anfang an |
| 2 | Marcel | Arbeitsklima wie in einer **kleinen Familie** |
| 3 | Markus | Offene **Fehlerkultur**, ständige Verbesserung |
| 4 | Alexander | **Teambuilding** auch nach Feierabend |
| 5 | Tobi | Jeder wird **gleich behandelt** — keine Hierarchien |
| 6 | Julia | Ein **super Team** trägt alles |
| 7 | Nico | Arbeit, an der man **wächst** |
| 8 | Louis | **LKW-Liebe** seit der Kindheit |
| 9 | Lara | Mit LKWs **groß geworden** *(Sperre: nichts vom Bewerbungs-Satz)* |
| 10 | Hannes | **Große Maschinen**, großer Eindruck |
| 11 | Marcel | Der Stolz, sagen zu können: **„Den habe ich repariert."** |
| 12 | Ciattei | Nicht von der Stange — hier arbeiten **Spezialkräfte** |

(Bei #11/#12 sind kurze Original-Fragmente in Anführungszeichen ok, aber
nie der komplette Satz.) Rot markierte Schlüsselwörter = Rot im Render.

## 6 · Ablauf-Gerüst (Zeiten = Video-Zeit; Detail-Beats generiert der sync-plan)

Die Struktur aus v1 bleibt — Seitenwechsel-Choreografie, Bridge, Endcard —
im neuen Look:

- **0,0–9,3 · Kaltstart Julia:** Fenster links, Takeaway 1, Plakette,
  Logo (Bilddatei) in Zone A.
- **9,5–22,3 · Lücke 1:** Takeaway-Exit → Travel 1 (11,2–12,5) → auf der
  freien Fläche Branding-Moment im Web-Hero-Stil: Löwe angeschnitten,
  Logo-Bild groß + „WILLKOMMEN BEI IHREM **MAN SERVICE**" (~5 s) →
  Kapitel-Wipe (scharfe Rot-Fläche, kein Skew — Website kennt keine
  Schrägen) bei 17,2 (**Musik: Downbeat Akt 2**) deckt die kurze
  Kapitel-Marke „EIN STARKES TEAM" auf (steht bis zur Mikro-Lücke 29,2).
- **22,3–64,5 · Team-Strecke:** Fenster rechts; pro Block Takeaway + Morph.
- **64,6–89,9 · Bridge:** Travel 2 zurück (65,3–66,6). **Kein zweites
  Panel** (Regel: nur EIN vertikaler Screen) — die Bridge spielt direkt auf
  der Bühnenfläche: Takeaway-Reprise („EIN **SUPER TEAM**") → Riser
  73,5–76,0 → **Musik-Hit bei 76,0** (Annahme Hero-Shot — nach Eingang der
  Videodatei prüfen) mit großem gestapelten Kapiteltitel „FASZINATION
  **NUTZFAHRZEUG**" frei auf der Fläche, Löwe zieht dazu als großes
  angeschnittenes Artwork von der Kante herein; danach Ambient-Phase mit
  wandernder roter Linie und Löwen-Parallax — nie > 5 s ohne Veränderung.
- **89,9–133,6 · Faszination + Stolz:** Fenster links; Jugend-Blöcke mit
  Takeaways 8–10 (kurz, Lesezeit-Regel); Sohn-Story ruhigste Phase (nur
  Ambient, Takeaway 11 spät und kurz); Ciattei mit Takeaway 12
  („Betriebsleiter Servicebetrieb" ohne Standort).
- **134,0–142,0 · Endcard:** Freeze → Fenster dimmt; Logo-Bild + „IHR MAN
  SERVICE-TEAM" (kein CTA) im Hero-Stil mit Löwe; Rückbau in den
  Loop-Zustand (Logo zurück auf Zone A) — Frame 3550 ≙ Frame 0.

## 7 · Musik-Spec (unverändert; Artlist/Envato)

Akt 1 Organic/Folk 0–17,2 · Akt 2 Funk-Groove 17,2–76,0 · Akt 3 Cinematic
76,0–Ende. Eine Serie/ein Artist, gleiche Tonart, instrumental, Outro-Pad
unter der Endcard.

## 8 · Stumme Fassung & Technik

- **Stumme Fassung:** Durch das Takeaway-System tragen beide Fassungen
  denselben Text-Layer — die stumme Fassung ist ein Render-Flag, das nur
  Standzeiten verlängert (`max(4 s, Zeichen/12)`, Karten dürfen die volle
  Blockdauer stehen) und in der Sohn-Story eine zweite Zeile erlaubt.
  Kein separates Karten-Set mehr nötig.
- **Technik wie v1 (verifiziert):** `ManWz169Master` in der bestehenden
  Composition.tsx; OffthreadVideo in `<Sequence durationInFrames={3350}>` +
  `<Freeze frame={3349}>`-Layer für 134,0–136,0; Ambient auf Root-Ebene
  (Sequences sind frame-relativ), Stufen über Amplituden-Hüllkurven;
  sync-plan-Generator clampt alle Dauern gegen die Lücken und prüft die
  5-s-Beat-Garantie maschinell; Ciattei-Elemente als abtrennbare Sequence
  (`ohneCiattei`); Face-Zone pro Fensterseite gemappt (links
  `{left:0.07,right:0.37,top:0.10,bottom:0.50}`, rechts gespiegelt);
  Render ProRes 422 HQ + H.264-Preview, Flags ausschreiben (zsh).
- **Fonts/Assets:** Davids Lieferung aus `Material/` (MAN Global inkl.
  Thin/Light/Medium, Logos, `löwe-halb.jpg`) nach
  `tools/motion/public/fonts/man/` bzw. `public/clients/man/` übernehmen;
  Löwe als freigestelltes Silhouetten-Asset aufbereiten (aktuell JPG
  schwarz auf weiß → PNG mit Alpha).

## 9 · Guardrails (verbindlich)

1. Lara 101,0–103,8 s nie als Text.
2. Ciattei-Plakette: fester Wortlaut „Betriebsleiter Servicebetrieb"
   (Sonderfall im sync-plan — Ableitung würde „Karlsruhe" durchschleifen).
3. Rollen-Ableitung: ohne Klammerzusätze und ohne Standortnamen.
4. Keine Job-/Recruiting-Elemente, Endcard ohne CTA.
5. Personen-Namen immer vollständig auf den Plaketten.
6. **Takeaways = Zusammenfassungen, nie der volle Original-Satz**
   (Davids Vorgabe v2 — ersetzt die frühere Wortgleichheits-Regel);
   Liste aus §5 vor dem Render von David abnehmen lassen.
7. Ciattei-Elemente nur in abtrennbarer Sequence (MAN-Freigabe 2023 offen).
8. MAN-Web-Look verbindlich: Radius 0, Rot nur als Akzent, Versalien für
   alle Groß-Typo.
9. **Logo immer als Bilddatei** (`MANlogoWeiss.png`), nie als gesetzter
   Schriftzug (David, 2026-07-24).
10. **Höchstens EIN vertikaler Screen** zu jedem Zeitpunkt — das
    Video-Fenster (darf sich verschieben); keine zweiten 9:16-Panels,
    keine Geisterrahmen (David, 2026-07-24).
11. Keine permanenten Kapitel-Tabs oder Fortschritts-/Aussagen-Striche
    (David, 2026-07-24) — Kapiteltitel nur als kurze Marken-Momente in den
    zwei großen Lücken.
12. **Löwe immer klar erkennbar oder gar nicht** (David, 2026-07-24):
    Original-Silhouette aus `löwe-halb.jpg` (freigestellt: Rot #E30045
    oder Weiß auf Anthrazit), groß und von der Bildkante angeschnitten —
    nur in Branding-Moment, Kapitel-Momenten der Bridge und Endcard.
    Nie als schwaches Ton-in-Ton-Wasserzeichen, nie in den Sprech-Blöcken.

## 10 · Offen / nächste Schritte

1. **David: Look-Freigabe v2** (Mockups) + Takeaway-Liste §5 abnehmen.
2. **David liefert die fertige 9:16-Videodatei** (1080×1920, konstante
   Framerate — Ziel 25p, sonst Master anpassen —, 48 kHz, bevorzugt
   ProRes 422). Nach `tools/motion/public/clients/man/wz/` (staticFile),
   ffprobe-Check vor dem ersten Testframe.
3. Bild-Check Bridge (Hero-Shot bei 76,0?) → Musik-Wechsel 2 final.
4. Umsetzung: Assets übernehmen → `ManWz169Master` + sync-plan-Generator
   (inkl. 5-s-Beat-Prüfung) → Testframes (Face-Zone-Review) → Render Ton.
5. Musik-Suche auf Akt-Zeiten (17,2 / 76,0) mappen.
6. Stumme Fassung als Render-Flag nach Freigabe des Ton-Masters.
