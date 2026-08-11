# Seniorenstiftung Prenzlauer Berg — Recruiting Text-Overlays (Design)

**Datum:** 2026-07-01
**Client (neu):** `seniorenstiftung`
**Umfang:** 5 animierte 9:16-Text-Overlays (ein Overlay je Video), transparent als Alpha-Overlay über bestehendes Talking-Head-Footage.

## Ziel

Selektive, animierte Texteinblendungen ("Eye-Candy") machen 5 Recruiting-Testimonials
interessanter, ohne die sprechende Person zu verdecken. Kein Voll-Untertitel — nur
Highlight-Pops an Betonungs-Momenten + ein gebrandeter CTA-Endslide.

## Marke / CI

- **Primär:** `#0E7EBE` (Teal-Blau, exakte Logo-Farbe von seniorenstiftung.org)
- **Ink/Text:** `#1E2A32` · **Weiß:** `#FFFFFF` · Frosted-Glass-Pills (weiß, ~94% opak, backdrop-blur)
- **Palette-Entscheidung:** Clean Teal (markentreu, kein warmer Zweitakzent)
- **Claim/Signatur:** „Geborgen in guten Händen" — dezent im CTA-Endslide
- **Font:** warm-humanistischer Sans, Vorschlag *Mulish* (Fallback *Inter*) via `@remotion/google-fonts`
- **Logo:** einfarbiges SVG (Teal), inline als React-Komponente eingebettet

## Technische Eckdaten

- Format: `portrait` (1080×1920), 9:16
- `transparent: true` → Render als **ProRes 4444 mit Alpha** (Compositing in DaVinci)
- fps: an Quell-Footage angleichen (per `ffprobe` prüfen; vermutlich 25 oder 30)
- `durationInSeconds`: je Video an Footage-Länge (Transkript-Dauern: siehe unten)
- Erweitert `projectPropsSchema` aus `src/core/schemas.ts`
- `<ReviewOverlay>` in jeder Komposition (conditional auf `review?.showGuides`)
- **Face-Zone-Regel (CLAUDE.md):** ALLE Overlays sitzen unter der Face-Zone, zentriert
  im Reels-Safe-Band. Spring-Overshoots dürfen nicht in die Face-Zone ragen.
- Kein eingebranntes Footage in der Komposition (reines Alpha-Overlay).

## Architektur

```
src/clients/seniorenstiftung/
  brand.json                     # CI-Werte
  logo.svg                       # Quell-Logo (Teal)
  components/
    constants.ts                 # TEAL, INK, WHITE, Springs, SAFE-Ratios
    useExit.ts                   # Exit-Animation-Hook (outAt / EXIT_SPRING)
    Logo.tsx                     # Inline-SVG Logo-Komponente
    HighlightPop.tsx             # Kinetic-Keyword: Glas-Pill, Clip-Path-Reveal,
                                 #   Spring-Pop, animierte Teal-Akzentlinie
    ChipRow.tsx                  # gestaffelte Chips (z.B. Rollen/Werte-Aufzählung)
    CTASlide.tsx                 # Endslide: Headline + „Jetzt bewerben" + Logo + Claim
    index.ts
  projects/
    pflegefachkraft/  { Composition.tsx, scenes.ts }
    pflege-azubis/    { Composition.tsx, scenes.ts }
    kuechenhilfe/     { Composition.tsx, scenes.ts }
    putzfachkraft/    { Composition.tsx, scenes.ts }
    allgemeines/      { Composition.tsx, scenes.ts }
```

- Registrierung der 5 Kompositionen in `src/Root.tsx`.
- Muster orientiert sich an `src/clients/sauber-entsorgen/` (Szenen → `<Sequence>`).

### Komponenten-Verantwortlichkeiten

- **HighlightPop** — eine kurze Kern-Aussage. Props: `text`, optional `emphasis`
  (hervorgehobenes Wort in Teal), `bottomRatio`, `fontSizeRatio`, `outAt`. Enter:
  Spring-Pop + Clip-Path-Reveal von links; Akzentlinie wächst nach Reveal; Exit via `useExit`.
- **ChipRow** — Array von Labels, gestaffelter Pop (stagger frames). Für Aufzählungen
  (Werte, Rollen). Zentriert, Glas-Pills mit Teal-Rand/Punkt.
- **CTASlide** — `headline`, `sub` („Jetzt bewerben" / „Bewirb dich jetzt"), Logo,
  Claim „Geborgen in guten Händen". Vollflächiger, aber transparenter Slide am Ende
  (bzw. untere Bildhälfte), stärkere Präsenz als die Pops.
- **useExit** — kapselt `outAt`/`EXIT_SPRING`-Muster (analog Projekt-Konvention).

### Szenen-Datenmodell (`scenes.ts`)

Diskriminierte Union analog Sauber Entsorgen:
```ts
type Scene =
  | { kind: "highlight"; startSec; durationSec; text; emphasis? }
  | { kind: "chips";     startSec; durationSec; chips: string[]; staggerFrames? }
  | { kind: "cta";       startSec; durationSec; headline; sub }
```
`Composition.tsx` mappt Szenen auf `<Sequence>` (Frame = `startSec * fps`).

## Content & Timing (aus Transkripten/SRT abgeleitet)

Zeiten sind Anhaltspunkte; im Studio feinjustierbar via globalem `timeOffsetSec`.

### Pflegefachkraft (~55,7 s)
- ~2,5 s `highlight` „Mehr als **Aufgaben**"
- ~6–12 s `chips` [Vertrauen · Nähe · Team]
- ~19–25 s `highlight` „Ein Platz mit **Perspektive**"
- ~25–29 s `highlight` „Fort- & Weiterbildung"
- ~37–44 s `chips` [Respekt · Kommunikation · Team]
- ~48–55,7 s `cta` „Werde **Pflegefachkraft**" / „Jetzt bewerben"

### Pflege Azubis (~56,8 s)
- ~3–6 s `highlight` „Wirklich **gebraucht** werden"
- ~21–24 s `highlight` „Schritt für Schritt"
- ~41–47 s `highlight` „Ein **Lächeln** schenken"
- ~47–49 s `highlight` „Haus mit Garten"
- ~50–56,8 s `cta` „Starte deine **Ausbildung**" / „Jetzt bewerben"

### Küchenhilfe (~38,4 s)
- ~13–17 s `highlight` „Willkommen & **gesehen**"
- ~17–24 s `highlight` „Struktur + echter **Sinn**"
- ~29–32 s `highlight` „Offenes Team"
- ~33–38,4 s `cta` „**Küchen- & Servicekraft** werden" / „Bewirb dich jetzt"

### Putzfachkraft (~52,1 s)
- ~0–3 s `highlight` „…erst auf, wenn sie **fehlt**"
- ~21–28 s `chips` [Respekt · Hygiene · Verantwortung]
- ~34–41 s `highlight` „Deine Arbeit **wird gesehen**"
- ~42–52 s `cta` „Werde **Reinigungskraft**" / „Jetzt bewerben"

### Allgemeines (~56,6 s)
- ~2–7 s `highlight` „Nicht Versprechen — **spürbar**"
- ~19–23 s `highlight` „Mehr als ein **Job**"
- ~24–31 s `chips` [Entwicklung · Team · Sinn]
- ~36–40 s `chips` [Pflege · Ausbildung · Küche · Service · Reinigung · Betreuung]
- ~41–45 s `highlight` „**Geborgen**"
- ~45–56,6 s `cta` „Werde **Teil der Seniorenstiftung**" / „Jetzt bewerben"

## Animation / Look ("Eye-Candy", markentreu-ruhig)

- Enter: `spring` Pop (leichter Overshoot, aber Face-Zone-sicher) + Fade
- Text-Reveal: Clip-Path von links (wie `KeywordLowerThird`)
- Akzentlinie: Teal-Gradient wächst nach dem Reveal
- Chips: gestaffelter Scale-In
- Glas-Pills: weiß ~94%, backdrop-blur, weicher Schatten
- Exit: sanftes Fade + Slide vor Szenenende (`EXIT_LEAD`)
- Zurückhaltend & premium — nicht überladen (Marke: warm-institutionell)

## Review-/Delivery-Konform (CLAUDE.md)

- `review.showGuides` default `false`; SafeZone/FaceZone im Studio prüfbar
- Vor Final-Render: `showGuides: false`; Overlay darf nie im Export erscheinen
- FaceZone je Video ggf. an reales Footage anpassen (Person evtl. nicht zentriert)

## Offene Punkte für den Plan

1. Exakte fps & Dauer je Quellvideo per `ffprobe` bestimmen (Composition-Config).
2. FaceZone-Position je Video am realen Footage verifizieren (Scrub-Check).
3. Font final wählen (Mulish vs. Inter) — via Google-Fonts-Verfügbarkeit.
4. Highlight-Wording ist vom Kunden freigegeben (Textkorrekturen der Scribe-Hörfehler
   sind bereits berücksichtigt: „Ausbildung" statt „Ausbilder", „Wohnbereichsleitung").

## YAGNI / bewusst weggelassen

- Keine Name/Rollen-Lower-Thirds (explizit nicht gewünscht)
- Kein Voll-Untertitel/Karaoke
- Kein warmer Zweitakzent, keine Partikel-/Hintergrund-FX
- Kein eingebranntes Footage in der Remotion-Komposition

## Hinweis

Repo ist kein Git-Repository → keine Commits; Spec wird nur als Datei abgelegt.
