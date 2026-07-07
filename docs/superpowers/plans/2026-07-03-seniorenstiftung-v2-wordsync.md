# Seniorenstiftung Overlays v2 — Wort-Sync + Warm-Premium (Plan)

**Ziel:** Sprech-synchrone, weichere, veredelte Animationen; Content-Pass mit wort-genauen Timings (freigegeben 2026-07-03 inkl. 2 Wording-Fixes).

**Datenquelle:** `Video inputs/Seniorenstiftung/transcripts/words-index.json` (Wort-Timestamps, ElevenLabs). Timings sind in die `scenes.ts` GEBAKT (kein Runtime-Parsing).

## Änderungen

1. **constants.ts** — weichere Springs: `WARM_SPRING {damping:16, stiffness:150}` ersetzt PUNCH als Standard-Enter; `GLOW_TEAL`-Konstante.
2. **Icons.tsx (NEU)** — 14 Stroke-Icons: herz, haende, team, sprechblase, check, buch, uhr, kalender, glanz, puls, stufen, schild, tropfen, teller. `<ChipIcon name size color strokeWidth>`.
3. **ChipRow v2** — Props: `chips: {label, icon?, delayFrames}[]` (per-Chip wort-synchron statt uniform stagger). Icon im Teal-Punkt-Badge.
4. **HighlightPop v2** — `emphasisDelayFrames?`: Emphasis-Wort pulst (scale 1→1.12→1) + weicher Teal-Glow (text-shadow) exakt beim Aussprechen; weicherer Enter (WARM_SPRING), längerer Fade.
5. **CTASlide v2** — Schimmer-Sweep über Headline (animierte Gradient-Maske), Logo-Reveal mit Glow, 6 dezente aufsteigende Teal-Bokeh-Partikel (deterministisch per Index).
6. **SceneRenderer v2** — Scene-Union: highlight bekommt `emphasisAtSec?` (absolut), chips bekommt `chips: {label, icon?, atSec}[]`; Renderer rechnet in Frames relativ zum Szenenstart um.
7. **scenes.ts × 5** — komplette Neuablage mit den freigegebenen wort-synchronen Momenten (Tabelle im Chat 2026-07-03; Wording-Fixes: PK-Hook = voller Satz „Manche Arbeit fällt erst auf, wenn sie fehlt", AG-Hook = „Einen guten Arbeitgeber spürt man jeden Tag" @3,9–6,7).
8. **previewFootage** — 720p-Proxys (h264+AAC) nach `public/seniorenstiftung/proxy/*.mp4`; Schema-Prop `previewFootage: boolean` (default false); Composition rendert `<OffthreadVideo>` hinter dem Overlay NUR wenn `previewFootage && !getRemotionEnvironment().isRendering` → nie im Export.

## Verifikation
- `npx tsc --noEmit` sauber
- Stills an exakten Wort-Frames + ffmpeg-Composite über echte Videoframes (Emphasis-Puls-Moment, Chip-Pops, CTA)
- Face-Zone unverändert (CONTENT_BOTTOM bleibt 0.42)
- Re-Render aller 5 ProRes-4444-Overlays

Kein Git-Repo → keine Commits. Inline-Ausführung (eng gekoppelte Änderung).
