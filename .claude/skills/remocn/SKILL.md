---
name: remocn
description: >
  Remocn-Komponenten für Remotion im NIRO-Studio — Copy-Paste-Bausteine (Text-Reveals, Signature-Transitions,
  Shader-Hintergründe, Odometer, Handschrift, Konfetti, Charts) aus der Registry remocn.dev. Nutzen, wenn eine
  Animation, Szene oder Komposition in tools/motion gebaut oder aufgewertet wird, wenn ein Text-Reveal, eine
  Transition, ein Hintergrund oder ein Effekt gebraucht wird, oder wenn ein Motion-Graphic „geiler" werden soll —
  auch ohne dass Remocn genannt wird.
---

# Remocn im NIRO-Studio

Remocn ist eine MIT-lizenzierte Komponentenbibliothek für Remotion (~240 Komponenten, wächst). Der Code wird in
unser Projekt kopiert — wir besitzen ihn. Basis dieser Datei ist Remocns eigener Agent-Skill, angepasst an unser
Setup (Stand 19.09.2026).

## Unser Setup (weicht von der Remocn-Doku ab)

| Remocn-Doku sagt | Bei uns |
|---|---|
| `npx shadcn@latest add @remocn/<name>` | **`cd tools/motion && npm run remocn:add -- <name> [<name> …]`** — die shadcn-CLI beschädigt String-Literale in Remotion-Code (dedupliziert Tokens: `split("\n")` → `split("")`, `"50% 50%"` → `"50%"`), deshalb unser Script `scripts/remocn-add.ts` (byte-genau, löst `registryDependencies` und npm-Pakete auf). `--force` überschreibt, `--list` zeigt Installiertes. |
| `components/remocn/` | `tools/motion/src/components/remocn/<name>.tsx`, Libs unter `src/lib/remocn/`; Import `@/components/remocn/<name>` (Alias `@/` → `src/`, in tsconfig und remotion.config.ts) |
| Canvas 1280×720 | Unsere Formate aus `projectPropsSchema` (1920×1080, 1080×1920 …). Größen relativ setzen (`width * 0.05`), nicht die Defaults der Komponenten übernehmen. |
| Schrift `var(--font-geist-sans)` | Am Root der Komposition setzen: `style={{ "--font-geist-sans": '"Meutas", sans-serif' } as React.CSSProperties}` → alle Remocn-Textkomponenten laufen in der Kundenschrift. `handwrite`/`inline-word-roll` haben ein `fontFamily`-Prop; `number-wheel`/`rolling-number` nutzen JetBrains Mono (tabular). |
| WebGL-Shader | `remotion.config.ts` setzt `Config.setChromiumOpenGlRenderer("angle")` — ohne GL-Backend bleiben Shader-Flächen schwarz. Im Studio laufen sie nativ. |

**Lokale Patches:** `tools/motion/src/components/remocn/_NIRO-PATCHES.md` listet, was wir an Komponenten geändert
haben (z. B. `marker-highlight`: transparenter Root, Folgetext über dem Marker). Nach `--force` dort nachlesen und
wieder anwenden.

**Alpha-Overlays (ProRes 4444 für Resolve):** Shader- und Backdrop-Komponenten sind opak — nur in Vollbild-Szenen
oder hinter `!transparent` einsetzen. Text-Reveals, Marker, Handschrift, Konfetti, Transitions sind alpha-tauglich.
Vor dem Einsatz jeder Komponente auf `background:` am Root prüfen (Alpha-Falle, siehe WORKFLOW-Motion.md).

**Lebender Nachweis:** Komposition `NiroDemo-RemocnShowcase` (`src/clients/niro-demo/projects/remocn-showcase/`) —
Shader-Mesh + Soft-Blur-In → Whip-Pan → God-Rays + Number-Wheel → Grain-Dissolve → Mask-Reveal + Marker →
Zoom-Blur → Handwrite + Ink-Underline + Confetti. Im Studio anschauen, bevor man Komponenten neu erfindet.

## Katalog: liegt auf remocn.dev, nicht hier

Der Katalog ändert sich; eine Kopie veraltet still. Immer live lesen:

```
https://remocn.dev/llms-components.txt
```

Eine Tabelle je Kategorie, jede Komponente mit `Use for` / `Avoid for`, Länge in Frames (`Length`), `Vibe`, Tier,
Abhängigkeiten und Doku-Link. Scannen, Shortlist bilden, dann nur die Seiten der Shortlist holen:

```
https://remocn.dev/docs/typography/blur-out-up.md
https://remocn.dev/docs/transitions/whip-pan.md
```

Ohne Netz: sagen und stoppen — keine Props, Defaults oder Dauern aus dem Gedächtnis erfinden. Ein falscher
Prop-Name bricht den Build, eine erfundene Dauer schneidet die Animation still ab. Die installierten Dateien
selbst sind natürlich lesbar (`Props`-Interface am Dateianfang).

## Zwei Tiers mit verschiedenen APIs

- **Animation-Tier** (`remocn`) — Text-Animationen, Transitions, Hintergründe, UI-Simulationen, Kompositionen.
  Frame-getrieben. Gemeinsame Props: `speed` (Zeitmultiplikator), bei Text `fontSize`, `color`, `fontWeight`,
  `className` am Root.
- **UI-Primitives** (`remocn-ui`) — timeline-getriebene shadcn-artige Primitives (Button, Dialog, Select …).
  State-Props (`state`, `style`, `variant`, `theme`), **kein `speed`**. Brauchen `@remocn/remocn-ui`.

Die Spalte `Tier` im Index sagt, welches man vor sich hat.

### Muster Animation-Tier

- Benanntes `Props`-Interface je Komponente (z. B. `BlurOutUpProps`).
- Transitions sind Kleinbuchstaben-Factories (`whipPan(props)`), die eine `TransitionPresentation` liefern —
  an `TransitionSeries.Transition` per `presentation`, Timing per `linearTiming` / `springTiming`.
  Nicht alles unter „Transitions" ist eine Presentation: `slide-swap` und `spring-settle` sind Szenen-Sequencer
  mit `scenes`-Array, die die ganze Timeline besitzen — die Doku-Seite sagt, was man hat.
- Viele Text-Komponenten füllen ihren Container (`position:absolute; inset:0`, zentriert) — wer Zahl **und**
  Label stapeln will, gibt jeder Komponente eine eigene, absolut positionierte Box (siehe Showcase, Szene 2).
- `marker-highlight`: Leerzeichen um das Highlight gehören in `before`/`after` (`"Einmal gebaut, "`).

## Timing

- **`Length` ist die Eigenbewegung, nicht der ganze Beat.** Bei Transitions ist es der Wert für
  `linearTiming`/`springTiming`; sonst der Frame, an dem die Animation fertig ist. Als Untergrenze der `Sequence`
  nehmen und Haltezeit draufrechnen. `state-driven` = keine eigene Dauer; `sustained` = umhüllt eine Szene und
  dauert genau so lange wie sie.
- **`Vibe` passend zur Marke wählen** (`tech`/`premium`/`data`/`clean`/`playful`/`social`/`paper`). `paper` ist das
  Stop-Motion-Set (quantisierte ~10 Posen/s, Handschrift, Tinte) — untereinander mischen, nicht mit den glatten
  Tiers.
- Für die Rhythmus- und Easing-Regeln gilt weiter unsere `tools/motion/docs/motion-doctrine.md`.

## Design-Defaults — kein KI-Einheitsbrei

Eigene Zutaten (Text, Szenen-Chrome, Karten — nicht die fertigen Komponenten) bleiben zurückhaltend: normale
Laufweite, Groß-/Kleinschreibung statt VERSALIEN, einfarbiger Text, dezente 1-px-Elevation — keine dekorative
Sperrung, keine Gradient-Textfüllungen, keine Glow-Schatten. Komponenten, deren Wesen der Effekt ist
(`tracking-in`, Social-Card-Gradienten), nicht entkernen.

```
https://remocn.dev/docs/craft/design-defaults.md
https://remocn.dev/docs/craft/motion-principles.md
https://remocn.dev/docs/craft/anti-patterns.md
```

## Remocn-Fallen

- Terminal-Scroll ist eine Stufenfunktion (`translateY`), nie gefedert.
- `overflow: hidden` auf Split-Layouts, sonst bricht Inhalt bei Breiten-Animationen.
- Cursor-Blinken deterministisch: `Math.floor(frame / 15) % 2 === 0`.
- Statische Dateien nach `public/`, laden per `staticFile()`.
- Social-Cards rendern offline (`avatarUrl=""` → Gradient-Fallback).
- Google-Fonts-Imports (`@remotion/google-fonts/...`) in einzelnen Komponenten laden beim Render aus dem Netz.

Allgemeine Remotion-Regeln (kein `Math.random()`, kein `setInterval`, `transform` statt `top/left`, Fonts vor dem
Render laden) stehen im Skill `remotion-best-practices`.

## Ein Video komponieren

Keine Komponenten-Halde, eine Geschichte. Bei „bau ein Produktvideo / Changelog / Intro":

1. **Strategie** — Template, aus Komponenten komponieren oder neue Komponente bauen: `references/anatomy.md` §1.
2. **Beats** — Produktdemo ist Hook → Positionierung → Produkt-Reveal → Features → Beweis → CTA: `anatomy.md` §2.
3. **Rezept** — `references/archetypes/index.md` routet zu Bauplänen je Archetyp (product-demo, changelog,
   feature-announcement, oss-showcase, cli-tool-demo, testimonial-reel, year-in-review, pricing-reveal, logo-bumper):
   Inhaltsvertrag, Dauer-Varianten, Beat→Komponente, `<TransitionSeries>`-Skelett.
4. **Komponente je Beat** aus `llms-components.txt`, Vibe zur Marke, Sequence nach Timing budgetieren.
5. **Qualitätsmaß** — ein Akzent, kinetischer Text in Satzschreibung, echte Inhalte, keine Glow-Halos, keine
   Feature-Aufzählung: `anatomy.md` §3.

Für Kundenarbeit gilt zusätzlich der Hausablauf: `tools/motion/WORKFLOW-Motion.md` (CI zuerst, Pre-Delivery-Review,
Renders ins Projekt, Protokoll).

## Referenz

Gebündelt (ändert sich nicht je Komponente):

- `references/anatomy.md` — ganzes Video komponieren: Strategie, Produktdemo-Beats, Gut-vs-Schrott-Maßstab.
- `references/archetypes/index.md` — Router zu den Archetyp-Rezepten.

Live von remocn.dev:

- `https://remocn.dev/llms-components.txt` — Komponenten-Index. Immer hier anfangen.
- `https://remocn.dev/docs/<section>/<name>.md` — volle Referenz einer Komponente.
- `https://remocn.dev/docs/craft/…` — Design-Defaults, Motion-Prinzipien, Anti-Patterns.
- `https://remocn.dev/llms.txt` — Index der gesamten Doku.

Lizenz: MIT (`LICENSE` in diesem Ordner, Copyright Remocn).
