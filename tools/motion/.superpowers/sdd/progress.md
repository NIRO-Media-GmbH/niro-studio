# Seniorenstiftung Overlays — Progress Ledger

Plan: docs/superpowers/plans/2026-07-01-seniorenstiftung-overlays.md
Note: Repo is NOT git → no commits; verification via tsc + `remotion still`.
De-risked: Mulish font available (@remotion/google-fonts/Mulish); ReviewOverlay props confirmed.

## Status
- Slice A (Tasks 1-4: foundation + shared components + Pflegefachkraft): COMPLETE (tsc clean, 4 stills verified, face-zone safe, CONTENT_BOTTOM=0.42)
- Slice B (Tasks 5-8: Pflege Azubis, Küchenhilfe, Putzfachkraft, Allgemeines): COMPLETE (tsc clean, risky stills verified: long CTA wraps, 6 chips wrap 3x2). WATCH: Allgemeines 6-chip block is tall → verify vs real face in Task 9.
- Task 9 (face-zone scrub + delivery review): COMPLETE. Composited overlays over real frames for all 5: faces sit upper, overlays lower → NO face coverage (incl. Allgemeines 6-chip = b-roll, no face). Delivery: showGuides:false in all 5, 5 comps registered, 5 render scripts present, tsc clean.

## Post-implementation fix
- HighlightPop clipped long phrases (nowrap + clip-path clipped overflow at pill maxWidth). FIXED: added measureText (@remotion/layout-utils) auto-fit — font scales down to fit one line (floor 0.5×). Verified full text on "Willkommen & gesehen", "Wirklich gebraucht werden", "Nicht Versprechen — spürbar", "Deine Arbeit wird gesehen". Root cause was in the plan itself.

## v1 DONE — all 5 overlays built, verified, ProRes-rendered (out/seniorenstiftung/*.mov).

## v2 (word-sync + warm-premium) — IN PROGRESS (Plan: 2026-07-03-seniorenstiftung-v2-wordsync.md)
- DONE: words-index.json, constants (WARM/PULSE/GLOW), Icons.tsx (14), ChipRow v2 (per-chip delayFrames+icons), HighlightPop v2 (emphasis pulse+glow), CTASlide v2 (shimmer+logo-glow+bokeh), SceneRenderer v2 (word-sync Scene union + chips fontSizeRatio passthrough), 5× scenes.ts word-synced, FootagePreview + previewFootage toggle (isRendering-guarded), 720p proxies in public/seniorenstiftung/proxy/. tsc clean. Word-sync verified on stills (pf-205: Nähe mid-pop, Team absent — exact).
- FULL SCRUB DONE (all scenes composited over real footage via draft webm + libvpx alpha decode — note: ffmpeg needs `-c:v libvpx` BEFORE the webm input or alpha decodes black):
  Findings & fixes (all verified fixed on re-scrub):
  1. PF chips 5.1s: block touched resident's chin + covered 2nd shot's face → fontSizeRatio 0.026, durationSec 7.9→6.0 (exit before ~11.3s cut)
  2. KH "Offenes Team" 29.6s: pill sat on speaker's mouth (frontal close-up) → scene REMOVED
  3. AG 6-role chips 36.1s: covered walking server's face → fontSizeRatio 0.024
  4. AZ chips 19.9s: stack covered rear nurse's face → fontSizeRatio 0.026 (also 34.6s chips)
- Preview MP4s (720p, overlay over footage, WITH audio) in out/seniorenstiftung/preview/*.mp4
- DONE: final v2 ProRes renders (all 5, prores yuva444p12le, durations match sources).

## v2 DONE 2026-07-03 — word-synced, warm-premium, full-scrub face-safe, rendered.
