# Bildanalyse-Rubrik — Hochzeits-Showreel (Messe, Premium-Marke „Aeterna“)

Jeder Kontaktbogen zeigt bis zu 6 Zeilen. Jede Zeile = ein Segment aus einem fertig geschnittenen
Hochzeitsfilm: Kennung (z. B. `t2-117`) + Länge, dann 3 Frames bei 20 / 50 / 80 % des Segments.
`t1-…` = Hochzeit Lea & Sebastian (freie Trauung im Zelt, Gut/Schloss, warmer Look).
`t2-…` = Hochzeit Jessica & Dominik (Kirche, Empfang unter Schirmen, Club-Party mit Farblicht).

Das Showreel läuft stumm auf einer Hochzeitsmesse. Zielgruppe: Brautpaare. Marke: elegant, feminin,
echte Emotionen statt gestellter Posen. Bewerte, wie gut der Shot dort wirkt.

## Felder je Segment (alle Pflicht)
- `id`: exakt wie auf dem Bogen
- `kategorie`: genau eine von
  - `location` — Establishing, Drohne, Gebäude, Landschaft, Außenansicht Location
  - `details` — Deko, Ringe, Schuhe, Blumen, Tischdeko, Kerzen, Einladung, Auto-Details, Essen als Detail
  - `getting_ready` — Ankleiden, Styling, Vorbereitung, First Look
  - `trauung` — Zeremonie allgemein: Einzug, Redner/Pfarrer, Paar am Altar, Gäste in der Zeremonie
  - `trauung_moment` — Schlüsselmoment: Ringtausch, Ja-Wort, Kuss nach der Trauung, Auszug mit Konfetti
  - `emotion_gaeste` — Gäste mit Emotion: Tränen, Lachen, Rührung, Umarmungen (ohne Paar im Fokus)
  - `paar` — Brautpaar im Fokus außerhalb Zeremonie: Shooting, Spaziergang, Kuss, Blicke, Auto
  - `gratulation_feier` — Gratulation, Sektempfang, Anstoßen, Gruppenstimmung am Tag
  - `reden_dinner` — Reden, Spiele, Dinner, Buffet, Torte, Tischgespräche
  - `abend_lichter` — Abendstimmung, Lichterketten, Dämmerung, ruhige Abendmomente, Wunderkerzen
  - `party` — Tanzfläche, Eröffnungstanz, DJ, Club-Licht, ausgelassene Feier
  - `unbrauchbar` — Grafik, Titel, Polaroid-Animation, Schwarzblende, Übergangseffekt, nichts erkennbar
- `einstellung`: `totale` | `halbtotale` | `nah` | `detail`
- `paar_im_fokus`: true/false (Braut und/oder Bräutigam ist Hauptmotiv)
- `tageszeit`: `tag` | `abend`
- `wert`: 1–5 Showreel-Wert
  - **5** herausragend: starke echte Emotion oder ikonisches Bild (Kuss im Gegenlicht, Drohne über Location,
    Ringtausch nah, Braut lacht), Motiv klar, schönes Licht, saubere Komposition
  - **4** sehr gut, klar zeigbar
  - **3** solide, Füllmaterial
  - **2** schwach: belanglos, Rückenansicht, verdeckt, unvorteilhaft (Mund voll, Augen zu), unruhig/unklar
  - **1** nicht zeigen
- `flags`: Liste, leer wenn nichts zutrifft:
  - `text_im_bild` (eingeblendeter Titel/Name/Untertitel), `grafik` (Polaroid/Rahmen/Animation),
    `uebergang` (Blende/Lichtblitz/Weißbild/Schwarzbild in einem der Frames), `sw_effekt` (Schwarzweiß/Vintage-Vignette),
    `szenenwechsel` (die 3 Frames zeigen erkennbar verschiedene Szenen/Orte), `unscharf_sichtbar`
    (deutlich unscharf/verwackelt, nur wenn eindeutig), `kind_im_fokus` (Kind ist Hauptmotiv),
    `unvorteilhaft` (Person ungünstig getroffen)
- `motiv`: max. 6 Wörter, z. B. „Ringtausch nah, Kirche“, „Drohne über Gutshof“
- `bester_frame`: 1, 2 oder 3 — welcher der drei Frames den stärksten, am besten zeigbaren Moment zeigt

## Hinweise
- Technische Schärfe wird separat gemessen — nur eindeutige Unschärfe flaggen.
- Zeigen die 3 Frames unterschiedliche Inhalte, bewerte den besten zusammenhängenden Teil, setze aber `szenenwechsel`.
- Sei kalibriert: typische Verteilung etwa 10–15 % Wert 5, 25–30 % Wert 4, 30 % Wert 3, Rest 2/1.
- Party-Shots im Club-Licht nicht pauschal abwerten — gute Party-Momente mit Paar/Emotion sind wichtig.
