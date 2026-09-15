# Craiss 4 Ads — Untertitel-Look „Mix" (Design)

Stand 2026-09-11, freigegeben im Chat. Ersetzt den schlichten Rail-Look vom
07.09. (einheitliche Leiste knapp unter Bildmitte) für alle 5 Videos.

## Ziel

Dynamischere, abwechslungsreichere Untertitel — ohne die Kundenvorgaben zu
brechen: ruhige Bewegung (kein Hüpfen), nichts in Halshöhe, CI (Laski Slab,
Craiss-Rot `#CD202C`, Craiss-Blau `#002F5F`), „Kein Stress" nicht einblenden.
Die eingebrannten Grafiken (Hook, Chips, Flaggen, CTA) bleiben unverändert.

## Feste Regeln (unverändert)

- Ganze Sinneinheiten, nie Satzteile (David-Regel).
- Keine inhaltliche Dopplung mit eingebrannten Grafiken (David-Regel).
- Untertitel nur in den freien Fenstern zwischen Grafiken (bestehende
  `BLOCKED`-Listen je Video); ein Satz erscheint nur, wenn er vom ersten bis
  zum letzten Wort in einem freien Fenster liegt — sonst entfällt er ganz
  (löst die offenen Satzteil-Reste).
- Gebrochenes Deutsch wörtlich; ASR-Korrekturen wie in `scripts/craiss-captions.ts`.
- Nie ein Wort zeigen, bevor es gesprochen ist.

## Ebenen und Anteile (pro Video, bezogen auf sichtbare Sätze)

| Treatment | Anteil | Aussehen (Basis 1080×1920) |
|---|---|---|
| `rail` Grundzeile | ~60 % | Laski Slab Bold 52 px, weiß, Schatten; Wörter erscheinen am Wortanfang |
| `hero-white` | ~25 % gesamt für alle drei Hero-Varianten | Kernwort Laski Slab Black 130 px weiß, Rest als Grundzeile darüber/darunter |
| `hero-red` | ↑ | Kernwort Black 96 px weiß in rotem Kasten (`#CD202C`, Radius 6) |
| `hero-blue` | ↑ | Kernwort Bold 64 px weiß auf blauem Label (`#002F5F`, Radius 6) |
| `wordbox` | ~10 % | Wörter Black 110 px; roter Kasten blendet weich zum gesprochenen Wort über; Aufzählungs-Variante: Grundzeile + ausgewählte Wörter im Kasten, die einander ersetzen |
| `glass` | max. 1–2 pro Video | Zusätzlich zur Grundzeile: ein Wort Black 200–260 px, Füllung Weiß 40 %, feiner heller Rand, in einer freien Fläche (Himmel/Wand) |

Die drei Hero-Varianten rotieren; zwei aufeinanderfolgende Hero-Sätze nutzen
nie dieselbe Variante.

## Position

Pro Einstellung (Shot), nicht pro Wort:

- `top` — Totale: oberes Drittel im freien Bild (y 18–32 %).
- `side-l` / `side-r` — Halbtotale: seitlich neben der Person, auf der Seite
  gegenüber der Blickrichtung (y 30–55 %).
- `chest` — Nahaufnahme: Brusthöhe; Oberkante ≥ Kinn + 110 px.
- Harte Grenzen: Gesicht und Hals immer frei; Unterkante ≤ 78 % (1500 px,
  Plattform-UI); links/rechts ≥ 54 px Rand.
- Glas-Wort: eigene Zone in der größten freien Fläche des Shots.

## Bewegung

- Remotion `spring` mit `SOFT` (Dämpfung 34, Steifigkeit 75, clamped) nur auf
  Transforms, Deckkraft linear (Flicker-Regel).
- Grundzeile: Wort für Wort, 12 px Anstieg + Einblendung über 5 Frames.
- Hero: landet am Wortanfang, Skalierung 0,94 → 1, max. 24 px Weg.
- Wordbox: Kasten blendet in 6 Frames vom vorigen zum gesprochenen Wort über
  (Überblendung statt Positions-Animation — keine Textmessung im Render nötig).
- Glas: Einblendung 0,4 s, Skalierung 1,02 → 1.
- Ausblenden kürzer als Einblenden (5 Frames), nie während laufender Sprache
  mitten im Wort.

## Daten

Pro Video ein Plan `src/clients/craiss/captions/<id>.plan.json`:

```json
{
  "video": "erster-tag-v3",
  "cues": [
    {
      "id": "cc-02",
      "start": 7.799, "end": 9.429,
      "tokens": [{ "text": "Das", "start": 7.879, "end": 8.059 }],
      "pages": [0],
      "treatment": "hero-white",
      "heroIndex": 2,
      "heroCount": 1,
      "zone": "chest",
      "y": 900,
      "chinY": 720,
      "glass": null
    }
  ]
}
```

- Ein Cue = ein Satz; `tokens` und `pages` (Start-Index jeder bisherigen
  Caption-Seite) stammen aus den bestehenden Caption-Seiten (Scribe-Wortzeiten).
  Angezeigt wird immer die aktuelle Seite des Satzes.
- Von Hand je Cue: `treatment`, `heroIndex`/`heroCount` (Wort oder Wortgruppe,
  innerhalb einer Seite), `boxIndices` (Aufzählungs-Wörter), `zone`, `y`,
  `chinY` (gemessenes Kinn → Prüfung Oberkante ≥ Kinn + 110) und `glass`
  (`{ text, startSec, zone, y }`); geprüft gegen Einzelbilder pro Shot.

## Komponenten

- `src/clients/craiss/CaptionMix.tsx` — Renderer für einen Plan
  (Treatments, Zonen, Bewegung, Sperrfenster-Logik wie `Subtitles.tsx`).
- Vorschau (`projects/vorschau`): neues Prop `subtitleStyle: "neu" | "alt"`,
  Standard `neu`, sobald ein Plan für das Video existiert.
- Die `*-Untertitel`-Kompositionen (Alpha-Render) wechseln erst nach Abnahme
  auf den neuen Look.

## Prüfung vor Abnahme

- Kontaktbogen je Cue (Anfang/Mitte/Ende) mit Face-/Safe-Zone-Guides:
  Hals/Gesicht frei, keine Überschneidung mit eingebrannten Grafiken
  (Grafik-Segmente aus der Differenz animiert − ohne Animation).
- Checkliste `docs/cinematic-captions.md` Abschnitt 10 (keine identischen
  Layouts dreier Gruppen hintereinander, keine Phrase vor dem Sprechen komplett).
- `npx tsc --noEmit`; Studio-Vorschau.

## Ablauf

1. Video 01: Plan + Renderer, Vorschau mit Umschalter alt/neu → Abnahme.
2. Videos 02–05 nach demselben System.
3. Alpha-Renders der Untertitel-Spuren (ProRes 4444, 2160×3840) nach Freigabe.

## Nicht Teil davon

Tiefeneffekt hinter der Person (keine Matte vorhanden), Änderungen an den
eingebrannten Grafiken, Sound-Effekte.
