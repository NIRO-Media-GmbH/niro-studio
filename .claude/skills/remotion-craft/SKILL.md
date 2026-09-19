---
name: remotion-craft
description: >
  Handwerks-Wissen für Remotion-Motion-Graphics im NIRO-Studio (tools/motion): Art Direction und Motion-Language,
  Spring-/Easing-Presets, Kinetic Typography, Lower Thirds, Testimonial-Karten, Logo-Animation, Shot-Komposition
  und Safe-Areas, Style-System (Paletten, Glass, Grain), Custom-Transitions, Beat-Sync, Audio-first-Timing,
  3D mit @remotion/three, Ken-Burns-Shimmer, QA am gerenderten File. Nutzen bei jeder Animation-Aufgabe
  („Animation: <Kunde>/<Projekt>"), wenn etwas „billig", „generisch" oder „unruhig" wirkt, oder wenn Kundenfeedback
  in Änderungen übersetzt werden muss. Ergänzt die offiziellen Remotion-Skills (API) und unsere Doktrin (Regeln).
---

# Remotion-Craft (NIRO)

Die offiziellen Remotion-Skills erklären, **wie Remotion funktioniert**. `tools/motion/docs/motion-doctrine.md` legt
**unsere Regeln** fest (Easing, Szenen-Rhythmus, Skalen, Fallen). Dieser Skill liefert das **Handwerk dazwischen**:
gesammelt aus drei MIT-Quellen (Gang-of-Beads/remotion-killer-skill, iart-ai/motion-skills,
haidrrrry/claude-remotion-skill), Texte in `references/` unverändert, Lizenzen in `LIZENZEN.md`.

**Rangfolge bei Widersprüchen:** `WORKFLOW-Motion.md` und `CLAUDE.md` (Pre-Delivery-Review) → `motion-doctrine.md`
→ dieser Skill → Remocn-Skill. Die Referenzen hier sind Werkzeugkasten, nicht Gesetz.

## Was zuerst lesen — nach Aufgabe

| Aufgabe | Lesen (in `references/`) |
|---|---|
| Neues Stück, Look noch offen; „wirkt unruhig/inkonsistent" | `iart/motion-art-direction.md` (Motion-Language-Spec, Personalities) |
| Szene bauen, Text animieren, Stagger, Layout, Karten | `killer/2d-craft.md`, dazu `iart/animation-principles.md` |
| Titel / Headline / Kinetic Typography | `killer/2d-craft.md` §Kinetic typography + `social/motion-patterns.md` §3 |
| Lower Third, Bauchbinde, Namens-Insert | `iart/lower-thirds.md` (+ `--lower-third-component.md`) |
| Zitat, Bewertung, Testimonial, Recruiting-O-Ton als Karte | `iart/testimonial-video.md` (+ `--quote-card.md`) |
| Logo-Reveal, Sting, Endcard, Bumper | `iart/logo-animation.md`, `iart/youtube-intro-outro.md` |
| Farben, Gradienten, Glass, Grain, Banding | `killer/style-system.md`, `iart/color-motion.md` |
| Hintergründe (Mesh, Aurora, Partikel, Loop) | `iart/motion-background.md`; fertige Shader → Skill `remocn` |
| Szenenwechsel, Custom-Presentation, „wirkt wie PowerPoint" | `killer/transitions.md` |
| Bildaufbau, Safe-Areas je Format, Parallax, Kamera | `iart/shot-composition.md`, `iart/video-delivery-specs--safe-areas.md` |
| Musik, Beat, Schnittrhythmus, Voice-over-Timing, Captions | `killer/audio-sync.md`, `iart/beat-sync-editing.md` |
| 3D (@remotion/three), Partikel, Shader-Material | `killer/3d.md` |
| Langsamer Push-in flimmert / ruckelt (Ken Burns) | `killer/2d-craft.md` §Slow push-in (Shimmer vs. Judder) |
| Multi-Resolution, Codecs, Render-Flags | `killer/rendering.md` (unsere Kommandos: WORKFLOW-Motion.md) |
| Abnahme eines Renders | `killer/video-qa.md` (Rubrik unten) |
| Kundenfeedback vage („mehr Pep", „premium") | `iart/client-revisions--feedback-translator.md` |
| Social-Vollbild-Look (Reels, Grade+Grain-Stack, Holds) | `social/design-rules.md` + `social/motion-patterns.md` |

## Die Kurzfassung, die immer gilt

**Motion-Language zuerst, dann animieren.** Vor der ersten Zeile eine Personality festlegen und überall gleich
anwenden — pro Kunde in `brand.json` unter `style.animationSpeed` bzw. als Notiz im Protokoll:

| Personality | Enter (30 fps) | Exit | Easing-Charakter | Overshoot | Liest sich als |
|---|---|---|---|---|---|
| Premium | 11–18 f | ~⅔ Enter | `Easing.bezier(0.22, 1, 0.36, 1)`, Spring damping 20–26 | 0 % | ruhig, edel, Luxus |
| Corporate | 6–12 f | ~⅔ Enter | `Easing.bezier(0.2, 0, 0, 1)`, Spring damping 18–22 | 0–3 % | sauber, seriös (B2B-Standard) |
| Playful | 5–9 f | ~⅔ Enter | `Easing.bezier(0.34, 1.56, 0.64, 1)`, Spring damping 10–14 | 10–20 % | verspielt (Hochzeit, Lifestyle) |
| Energetic | 3–8 f | ~⅔ Enter | ease-out-expo, Spring stiffness ≥ 180 | 15–30 % | Reels, Hype, Sport |

Eine Easing-Familie, eine Zeiteinheit (Vielfache davon), eine Transition-Familie, ein Stagger-Rhythmus
(2–6 f je Element), Haltezeit ≥ 0,3 s nach jedem Beat. Zwei Kurven maximal (rein/raus). Ein Hero je Frame.
Overshoot nie bei seriösen/finanziellen Inhalten.

**Lower Third (30 fps):** Enter 12–18 f gestaffelt (Balken → Name → Rolle, je 3–6 f), Hold 90–150 f (zweimal
lesbar), Exit 8–12 f. Links verankern, nach rechts wachsen. Name ≥ 1,6× Rolle. Nie hart ein-/ausschneiden.
Bei uns zusätzlich: Face Zone und Safe Zone aus `CLAUDE.md` gelten vor allem anderen.

**Testimonial / O-Ton-Karte:** Vertrauen vor Bewegung — in Lesereihenfolge staffeln, Zitat wörtlich, genau
eine Hervorhebung, Autor (Name · Rolle · Firma) ist der Beweis und kommt zuletzt.

**Style:** Tokens statt Inline-Werte (bei uns `brand.json` + `useCI()`). Dunkle Flächen mit Farbstich statt #000,
Text 90–100 % Weiß, Sekundärtext 60–70 %. Grain (`@remotion/noise`, 3–8 %) gegen Banding. Glow ≤ 1 Element je
Frame, Radius ≈ ⅓ Elementgröße, Alpha ≤ 0,6. Glass nur über bewegtem Hintergrund. Blur und große Schatten sind
die teuersten CSS-Effekte — 5-s-Testrender vor dem Vollrender.

**Transitions:** `TransitionSeries` als Standard, 15–25 f narrativ, 8–12 f Social. Jede Sequence 10–20 f
„beruhigten" Inhalt am Rand für die Überblendung. Nur Fade/Slide überall = Slideshow; 2–3 Signature-Moves
abwechseln (Rezepte Punch-Zoom, Whip-Pan, Depth-Push in `killer/transitions.md`; fertige in Remocn).

**Audio-first:** Wenn Sprache das Timing treibt, erst Audio (eine Datei je Szene, Dauer per ffprobe in ein
Manifest), dann Szenen-Längen daraus ableiten; Beats → `frame = Math.round(ms * fps / 1000)`;
`framesPerBeat = fps * 60 / bpm`. BGM 0,10–0,15 unter VO. SFX-Kit ohne Downloads: `npm run sfx`
(→ `public/sfx/`), Hit 2–3 f **vor** dem visuellen Landen.

**QA am gerenderten File, nie an der Studio-Vorschau:** erster und letzter Frame gesetzt · je Szene ≥ 1 Frame
geprüft (Fonts geladen? Safe Area?) · jedes Transition-Fenster gesampelt (kein Blitz, kein leerer Frame) ·
Audio vorhanden, gepegelt, synchron · Determinismus (gleicher Frame zweimal gerendert = identisch) ·
Kontaktbogen: `npx remotion still … --frame=N` an Schlüsselframes, `magick montage`, ansehen, fixen, neu rendern.
Ergänzt die Pflicht-Checkliste aus `tools/motion/CLAUDE.md`, ersetzt sie nicht.

## NIRO-Vorbehalte gegenüber den Quellen

- **Alpha-Overlays** (ProRes 4444 für Resolve, `transparent: true`): kein Grade/Grain/Vignette/Mesh-Stack,
  keine opaken Hintergründe, kein Ken Burns „auf jedes Still". Die 5-Schichten-Regel aus `social/design-rules.md`
  gilt nur für Vollbild-Social-Stücke.
- **Web-Anteile ignorieren:** In den iart-Texten stehen Millisekunden, GSAP/CSS-Keyframes und „Deliver &
  verify (standalone HTML)" — bei uns zählt Frames (`fps` aus `useVideoConfig()`), `interpolate`/`spring`,
  und die Verifikation läuft über Remotion-Stills. Die Design-Aussagen (Hierarchie, Safe-Areas, Rhythmus) gelten.
- **Provider-Aussagen** (TTS, Musik-Gen) sind Beispiele; unsere Kette ist Scribe-JSON → `@remotion/captions`
  (WORKFLOW-Motion.md, Caption-Datenkette).
- **Fonts:** Kundenschriften lokal aus `public/fonts/` bzw. `public/clients/<kunde>/fonts/`, nicht Fontshare/Google
  als Hero-Font — siehe `praktikant-reel` als Muster.
- **Render-Kommandos** nur aus WORKFLOW-Motion.md (`--public-dir=public-<kunde>`, Renders ins Projekt).

## Quellen

- `references/killer/*` — Gang-of-Beads/remotion-killer-skill (8 Skills, Stand 15.09.2026)
- `references/iart/*` — iart-ai motion-design-, tiktok-video-, ad-video-, youtube-video-, freelance-motion-skills
  (Stand 22.06.2026; Datei `<skill>.md` = SKILL.md, `<skill>--<ref>.md` = deren Reference)
- `references/social/*` — haidrrrry/claude-remotion-skill (Stand 12.08.2026)
- Aktualisieren: Repos neu klonen, Dateien ersetzen, Quellzeile oben in der Datei anpassen.
