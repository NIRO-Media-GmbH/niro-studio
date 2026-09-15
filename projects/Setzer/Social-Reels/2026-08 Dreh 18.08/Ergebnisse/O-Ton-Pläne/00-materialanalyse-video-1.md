# Materialanalyse Video 1 — Fleischkäse vs. Leberkäse (intern, nicht im PDF)

Stand: 24.08.2026 · Quelle: alle 20 Clips aus `01 - Unterschied Fleischkäse vs.
Leberkäse` + 12 thematisch passende Clips aus `00 Discarded` transkribiert
(ElevenLabs Scribe), Timecodes wortgenau aus `_intern/utterances.json` /
`_intern/cache/*.scribe.json`.

## Ausgangslage

Kein Konzept, kein Script — der Plan ist rein aus dem Material rekonstruiert.
Das Material trägt aber eine erkennbare, saubere Reel-Dramaturgie:
Frage → Nachfrage → Antwort → Twist → Erklärung + Produkt → CTA.
Jeder Beat wurde 2–5× wiederholt (klassisches Social-Setup ohne Script).

## Technik (aus den Datei-Metadaten, geprüft)

- **Zwei iPhones**, nicht eines:
  - Cam A = **iPhone 14 Pro** (iOS 26.6) → `IMG_48xx`, 2816×1584, **23,976 fps**,
    AAC ~100 kbit/s. Trägt alle Sprech-Takes.
  - Cam B = **iPhone 15 Pro** (iOS 27.0) → `IMG_69xx`, **25 fps**,
    AAC ~190 kbit/s. Zweiter Winkel + B-Roll. `IMG_6932` ist **3840×2160**
    (einziger 4K-Clip → meiste Reframe-Reserve).
- **Gemischte Framerate 23,976 / 25 fps** → Timeline-Basis festlegen und
  Cam-B-Clips konformen, sonst Ruckler an den Schnitten.
- Alle Clips sind **hochkant 9:16** (Rotation-Flag −90°, displayed 1584×2816).
- **Ton generell leise**: Peaks −15 bis −19 dBFS, Mittel ca. −37 dB.
  Vor der Abgabe auf Social-Norm ziehen (−14 LUFS int., True Peak −1 dBTP).
- **DJI-Mic-Sender sichtbar** am Kittel (links auf Brusthöhe) — in mehreren
  Takes deutlich im Bild. Ist Stilmittel-tauglich, aber bewusst entscheiden.
- **Drehdatum laut Metadaten: 19.08.2026** (13:18–13:40 UTC = 15:18–15:40 MESZ).
  Der SSD-Ordner heißt `03_Dreh 2026.08.18` — Ordnername oder Erwartung prüfen.
- `IMG_6929`, `IMG_6929 2`, `IMG_6929 3` sind **byte-identisch** (gleiche MD5,
  d11f0ca7…) — Doppel-Kopien, nur eine Datei verwenden.

## Person

Eine Person spricht, in allen Takes dieselbe: **Nico Setzer**.
Beleg: Kittel-Stick „Nico S…" unter dem Wappen „METZGER MEISTER BETRIEBSWIRT ·
SEIT 2023 · Setzer"; Rücken-Print „Setzer · www.landmetzgerei.de".
Website bestätigt: `Nico Setzer`, Funktion dort wörtlich **„Metzgermeister und
Master Professional of Business Management"**
(landmetzgerei.de/ueber-uns/ansprechpartner/).
→ Der Kittel sagt „Betriebswirt", die Website sagt es nicht. Für Bauchbinden
die Website-Fassung nehmen oder kurz: „Metzgermeister".

## Drehorte (drei, in dieser Reihenfolge gedreht)

| Ort | Clips | Bild |
|---|---|---|
| Produktion | 4874–4883, 6929 | Edelstahltisch, Fleischkäse-Laib auf Blech, Kutter im Hintergrund |
| Verkaufsraum / Theke | 4884–4887 | Kreidetafel „…mit's RICHTIG schmeckt!", Kilomarkt-Plakat |
| 24/7 Shop | 4888–4903, 6932 | pink beleuchtetes SB-Regal, Kasse, Selbstscan |

Die drei Orte ergeben eine motivierte Reise (Herstellung → Theke → Verkauf).
Das trägt den Schnitt und ist der Grund für die empfohlene Beat-Reihenfolge.

## Beat-Matrix (alle Takes je Aussage, freigegeben + discarded)

| Beat | Aussage | Takes freigegeben | Takes discarded | Bewertung |
|---|---|---|---|---|
| 1 Hook | „Gibt's eigentlich einen Unterschied…" / „Wisst ihr eigentlich, was der Unterschied … ist?" | 4875, 4877, 4878, 4879, **6929** | 4874, 4876 | 6929 = einziger Take mit Bewegung + Produkt-Hero, Cam B |
| 2 Nachfrage | „Ist in einem Leberkäse eigentlich wirklich Leber drin?" | **4883** | 4880, 4881, 4882 | 4883 klarster, ohne Versprecher |
| 3 Antwort | „Im Original bayerischen Leberkäs ist natürlich keine Leber drin" | **4884** | 4885, 4886 | 4884 ohne Vorspann „Kurze Antwort:" → tighter |
| 4 Twist | „(Aber) jetzt wird's interessant. Sobald man Bayern verlässt…" | **4888**, 4889, 4890, 4891, 4892 | 4887 | 4888 = nur der Teaser (1,4 s), keine Bayern-Dopplung zu Beat 5 |
| 5 Erklärung + Produkt | Leitsätze → „Deswegen heißt er bei uns Fleischkäse" → Region → 24/7 | **4900**, 4898 | 4894, 4895, 4896, 4899 | 4900 sauber durch; 4898 hängt bei 4,78–5,48 durch (0,52 s Stille + „äh") |
| 6 CTA | „Fleischkäse oder Leberkäse? Schreibt's in die Kommentare" | 4902, **4903** | — | beide mit Turn-around-Reveal; 4903 kürzer und offener formuliert |
| B-Roll | — | 6932 (24/7 Shop, Griff ins Regal), 6933 (drei gebackene Laibe im Blech) | — | die einzigen zwei B-Roll-Clips des Videos |

## Discarded-Ordner gegengeprüft — Sortierung stimmt

Kein übersehener besserer Take. Begründungen:
- `4894` endet mit „Nee, Scheiße" (Abbruch).
- `4895` **sachlich falsch**: „muss außerhalb Bayern jeder **Fleischkäse** Leber
  enthalten" — Verwechslung Fleischkäse/Leberkäs. Zu Recht raus.
- `4896` inhaltlich richtig („muss jeder Leberkäs außerhalb Bayern Leber
  enthalten"), aber 4900 liefert denselben Satz im Fluss mit dem Rest.
- `4899` bricht nach „Laut dem deutschen Fleischergesetz" ab — und dieses
  Gesetz existiert nicht (s. u.). Doppelt zu Recht raus.
- `4887` kombiniert Twist + Regel in einem Take, hat aber „Bayern ver-, Bayern
  verlässt". Bleibt als Struktur-Alternative im Plan vermerkt.
- `4885/4886` = Beat 3 mit Vorspann „(Ganz) kurze Antwort:" — legitim,
  nur eben länger.

## Inhaltliche Risiken (extern geprüft, Quellen unten)

### 1. „muss außerhalb von Bayern Leber drin sein" — verkürzt, „muss" ist falsch

Leitsätze für Fleisch und Fleischerzeugnisse (Neufassung 14.04.2022, geändert
07.11.2024), Nr. 2.4.2.2.2, wörtlich:

> „Leberkäse enthält in Bayern in der Regel keine Leber, **außerhalb Bayerns
> kann derart hergestellter Leberkäse als Bayerischer Leberkäs(e) bezeichnet
> werden**"

Das ist eine **Bezeichnungs-, keine Gebietsregel**: Ein Metzger in
Baden-Württemberg *darf* leberfreien Leberkäs verkaufen — er muss ihn dann
„Bayerischer Leberkäs(e)" nennen. Außerdem sind die Leitsätze nach § 15 LFGB
**nicht rechtsverbindlich** (objektiviertes Sachverständigengutachten über die
Verkehrsauffassung), es gibt also kein „muss". Ein „Deutsches Fleischergesetz"
**existiert nicht** (es gibt das Fleischgesetz — das regelt nur die
Klassifizierung von Schlachtkörpern).

Nicos Schlussfolgerung „**Deswegen heißt er bei uns Fleischkäse**" ist dagegen
sachlich einwandfrei — Fleischkäse ist nach denselben Leitsätzen die saubere,
leberfreie Bezeichnung.

→ Entscheidung bei David/Nico: so lassen (schnelles Social-Format, Kern
stimmt) oder eine Zeile nachdrehen. Nachdreh-Vorschlag im Cutter-Plan.

### 2. „24/7 Märkte" ≠ Website-Wording

Die Website sagt durchgehend **„24/7 Shops"** (Navigation + H1
„Unsere 24/7 Shops in Ihrer Umgebung", Slug `/24-7-shops/`), Einzelseiten
„24/7-Shop <Ort>". **Null Treffer** für „24/7 Markt/Märkte" auf allen
355 Seiten. Nico sagt in **beiden** Erklär-Takes „Märkte" — es gibt keinen
sauberen Take.
→ O-Ton so lassen, aber alles, was NIRO schreibt (Untertitel, Endcard,
Caption), sagt „24/7 Shops". Kein Untertitel-Wortlaut „Märkte".
(David-Regel 2026-08-01: nur Website-belegte Angaben in Kundeninhalten.)

### 3. Preis auf der SB-Schale lesbar

Auf dem Etikett der hochgehaltenen Packung steht **2,05 €** (in 4892 bei ~3,0 s
und in 4900 gegen Ende gut lesbar). Preise ändern sich, stehen nicht auf der
Website → im Reel entweder klein genug halten, weich blurren oder eine
Einstellung ohne lesbares Etikett wählen.

### 4. „bestes Fleisch aus der Region"

O-Ton, also unkritisch. Aber **nicht** als NIRO-Untertitel wiederholen: Die
Website formuliert „Qualität aus der Region" bzw. „aus unserer Region
Hohenlohe", nie „bestes Fleisch aus der Region".

## Belegte Extras (falls ein Trust-Insert gewünscht ist)

Website-belegt und für dieses Video thematisch passend:
- `Fleischkäse fein` — DLG-prämiert **2026 und 2024** (landmetzgerei.de/ueber-uns/)
- `Fleischkäse grob` — **7 × GOLD** bei internationalen Wettbewerben
  (landmetzgerei.de/bestnoten-bei-internationalen-wettbewerben/)
- 10 × „24/7 Shop", zusätzlich 13 × „Genussboxen" (eigener Eigenname)
- Instagram `@landmetzgerei_setzer`. **TikTok-Handle gibt es nicht** — im Footer
  liegt zwar ein TikTok-Icon, aber ohne Link.
- Firmierung: `Landmetzgerei Setzer GmbH`, Birkichstraße 2, 74549
  **Wolpertshausen** (der Footer der Website schreibt fälschlich
  „Wolperthausen" — nicht übernehmen).

## Offen für David

1. **Ton-Kamera bestätigen**: Welches iPhone hat den DJI-Empfänger? Beide
   Spuren sind brauchbar, aber die Regel ist erfragen, nicht raten.
2. Faktenlage (Risiko 1) — so lassen oder nachdrehen?
3. Reihenfolge Hook: dynamisch (6929, Cam B) oder statisch (4877, Cam A)?
4. Untertitel-Stil / CI für Setzer liegt noch nicht vor (kein `brand.json`).
5. Drehdatum 18. oder 19.08.?
