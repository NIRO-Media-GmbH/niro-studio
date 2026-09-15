# Showreel-Schnitt 5:00 — Vorgehen (abgenommen 2026-09-11)

Quelle: Resolve-Projekt „Messe Showreel“, Timeline 1 (Lea & Sebastian, 323 Shots) + Timeline 2
(Jessica & Dominik, 468 Shots), beide per DetectSceneCuts zerlegt. Ziel: neue Timeline, 5:00,
4K/25p, stumm (keine Musik, freier Schnittrhythmus nach Bildinhalt).

## Entscheidungen (User)
- **Erster Wurf + Tauschen:** 5-min-Timeline + Reserve-Timeline; User setzt rote Marker auf schwache
  Shots, Claude tauscht aus der Reserve (gleiche Kategorie, Regeln bleiben erfüllt)
- **Tagesbogen:** 8 Blöcke à 37,5 s (= 7500 Frames gesamt), jeder Block = Hochzeitstag im Zeitraffer
- **Ohne Musik**, Shots dürfen gekürzt werden

## Phase 1 — Shot-Katalog
1. Ein Decode-Durchlauf je Film (5 fps, 960×540): Schärfe (Laplace-Varianz, gesamt + Mitte),
   Helligkeit, Clipping, Sättigung, Bewegung; Vorschaubilder 640×360
2. Fehlschnitte zusammenführen: Schnitte, bei denen das Bild davor/danach strukturell ähnlich bleibt
   (Blitz/Lichtwechsel), gelten nicht als Schnitt → Segmente
3. Ausschluss: Titel/Text, Polaroid-Grafiken, Schwarz-/Weißbilder, Lichtblitz-Übergänge, S/W-Vignetten-Intro,
   technisch schwach (gemessen, nicht geraten)
4. Bildanalyse je Segment (3 Frames): Kategorie, Einstellungsgröße, Showreel-Wert 1–5 (echte Emotion > Pose),
   Ausschluss-Flags
5. Bestes Fenster je Shot (Randframes weg, schärfste/ruhigste Stelle)

## Phase 2 — Sequenz (Block-Vorlage, 15 Slots = 37,5 s)
| Slot | Kategorie | s |
|---|---|---|
| 1 | Location/Drohne | 3,5 |
| 2 | Details | 2,5 |
| 3 | Getting Ready | 2,5 |
| 4 | Details/Getting Ready | 2 |
| 5 | Trauung | 3 |
| 6 | Emotion (Gäste) | 2,5 |
| 7 | Trauung-Moment (Ringe/Kuss) | 2,5 |
| 8 | Paar | 3,5 |
| 9 | Gratulation/Feier | 2,5 |
| 10 | Paar | 3 |
| 11 | Feier/Reden/Dinner | 2,5 |
| 12 | Abend/Lichter | 2,5 |
| 13 | Party | 1,5 |
| 14 | Party | 1,5 |
| 15 | Party/Tanz | 2 |

Regeln: jeder Shot nur einmal · nie zwei gleiche Kategorien oder Einstellungsgrößen hintereinander ·
Paar wechselt spätestens nach 2 Shots, gesamt ≈ 50/50 · Party ≈ 13 % (+ Abend ≈ 7 %) · Block-Start mit starkem
Bild · keine zwei Shots derselben Szene im selben/benachbarten Block · fehlt einer Kategorie beim Paar
(z. B. Getting Ready), springt das andere Paar ein · Slotlängen ±0,5 s flexibel, Blocksumme fix ·
Loop: Block 8 endet im Abend/Party, Block 1 startet mit Drohne bei Tag.

## Phase 3 — Bau in Resolve (Freigabe: Schreiben erlaubt in „Messe Showreel“)
- Neuer Bin + Timelines „Claude Showreel 5min <Datum Zeit>“ und „Claude Showreel Reserve <Datum Zeit>“
  (3840×2160, 25p, nur Video, harte Schnitte), Block-Marker blau (User-Marker rot = tauschen)
- Readback: Anzahl, Summe 7500 Frames, keine Lücken, Quellbereiche = Plan; Timeline des Users wieder aktiv
- Plan + Katalog als JSON in `_intern/showreel-analyse/`

## Offen/Hinweis
Einverständnis der Paare für öffentliche Messe-Nutzung prüfen (auch erkennbare Gäste/Kinder).
