# Motion-Doktrin — Qualitätsregeln für alle Kompositionen

Toolunabhängige Motion-Design-Lehre, destilliert aus den HyperFrames-Skills
von HeyGen (`heygen-com/hyperframes`, skills: faceless-explainer,
hyperframes-creative, talking-head-recut, embedded-captions u. a.; MIT).
Gilt zusätzlich zu WORKFLOW-Motion.md und der Review-Checkliste in
CLAUDE.md. px-Angaben: 1080×1920 bzw. 1920×1080 wie angegeben.

## 1. Easing-Doktrin

- Standard-Ease: langer Auslauf (power3-artig; CSS
  `cubic-bezier(.2,.7,.2,1)`; Remotion: `spring` mit hoher Dämpfung oder
  `interpolate` + easeOut-Kubik).
- **Kein Bounce/Back/Elastic als Default** — federnde Entrances sind der
  häufigste Amateur-Tell. Overshoot nur, wenn etwas bewusst
  elastisch/taktil sein soll.
- Entrances enden mit `.out`, Exits starten mit `.in`, Moves `.inOut`.
  Exits schneller als Entrances (Faustregel 0,4 s rein / 0,25 s raus,
  Exit ≈ Entry rückwärts bei 60 % Dauer).
- Entrances < 150 ms wirken hektisch; > 700 ms nur für Luxus/cinematisch.
- Tempo = Gewicht: 0,15–0,3 s Energie, 0,3–0,5 s professionell,
  0,5–0,8 s Luxus, 0,8–2,0 s cinematisch.
- Nie mehr als 2 Tweens mit identischer Ease in einer Szene; die
  langsamste Szene eines Videos darf ~3× langsamer sein als die
  schnellste. Nicht jedes Element von `y:30, opacity:0` starten.
- Konstante Fahrt (Pfad, Laufband) = linear (`ease: none`); diskrete
  UI-Zustände = scharfes ease-out.
- Ein Subjekt zwischen zwei Positionen = EIN kontinuierlicher Tween.
  Zwischen-Keyframes nur, wenn der Zuschauer distinkte Beats fühlen soll
  — jedes Segment ändert die Geschwindigkeit und kann ruckeln.

## 2. Szenen-Rhythmus (Anti-PowerPoint)

- Szenenstruktur: Build 0–30 % / Breathe 30–70 % / Resolve 70–100 %.
- **Nichts in den ersten ~25 % der Szene dumpen.** Reveals sequenziell
  über die hintere Hälfte auf den VO-/Musik-Beat legen; erste Animation
  0,1–0,3 s versetzt, nie bei t=0.
- Reveals aufs gesprochene Wort pacen — reale VO-/O-Ton-Dauer schlägt
  Schätzung; mechanisch aus Timings syncen, nie nach Gefühl.
- Kein „Lazy Breathing": kein Slow-Pan/Dauer-Puls in der zweiten
  Szenenhälfte. **Lieber keine Motion als schlechte Motion.** Erlaubte
  Aliveness im Hold: subtiler Low-Amplitude-Jitter.
- Rhythmusbruch alle ~30 s (Gegenrichtung, doppelt großes Wort,
  Caption-Pause, Farbwechsel) — sonst adaptiert das Auge und die
  Betonung stumpft ab.
- „Wow"-Transition max. 1–2 pro Reel, sonst flacht sie ab.
- Jedes animierte Element bekommt ein Motion-Verb (SLAMS, DRAWS, FLOATS,
  SNAPS, …). Kann man das Verb nicht nennen, ist das Element nicht
  designt. Rhythmus vorab benennen (z. B. fast-fast-SLOW-fast-hold).

## 3. Transition-Rezepte (Zahlen als Startwerte)

- **Velocity-matched Cut** (Schnitt am Geschwindigkeits-Peak, Richtung +
  Tempo beidseits gleich ±5 %): Exit `y −150 px, Blur 30 px, 0,33 s,
  ease-in` → Entry `y 150→0, Blur 30→0, 1,0 s, ease-out`.
- **Whip-Pan:** `x ∓400 px, Blur 24 px, 0,3 s, power3`.
- **Zoom-through:** `scale 1→1,2 + Blur, 0,2 s ease-in` →
  `scale 0,75→1, 0,5 s, expo-out`.
- Dauer-Presets: instant 0,15 / snappy 0,2 / smooth 0,4 / dramatic 0,5 /
  gentle 0,6 / luxe 0,7 s.
- Layout-Umbau (Split→Stack etc.): 0,5–0,7 s, ease-inOut.

## 4. Video ≠ Web — Skalentabelle

Web-Reflexe (kleine Schrift, 8-px-Paddings, 3 %-Deko) sind im Video
unsichtbar. Richtwerte:

| Element | 16:9 (1920×1080) | 9:16 (1080×1920) |
|---|---|---|
| Headline/Hook | 64–120 px (In-Feed ≥ 90) | 130–170 px (7–9 % Höhe) |
| Body | 28–42 px (In-Feed ≥ 32) | 65–95 px (3,5–5 % Höhe) |
| Labels/Kicker | 18–24 px | 18–22 px × 1,3 |
| Untertitel-Rail | ~48 px (4,5 % Höhe) | ~86 px (4,5 % Höhe) |

- Deko-Elemente: Opacity 12–25 % (nicht 3–8 wie im Web), Borders 2–4 px,
  Paddings 60–140 px.
- Hero-Text darf 60–80 % der Framebreite spannen; an Kanten ankern statt
  zentriert schweben; min. 2 Fokuspunkte; 3 Ebenen denken
  (BG-Treatment / MG-Content / FG-Akzente).
- **Portrait-Umrechnung:** `portraitPx = landscapePx × 1,3` (4-px-Raster);
  Hero-Titel bis ×1,4, Meta nur ×1,2; line-height NICHT mitskalieren;
  horizontale Paddings schrumpfen auf 24–36 px. 4:5 (1080×1350) =
  Portrait-Bounds × 0,703.
- Tracking: Display −0,015 bis −0,035 em, Body +0,005 bis +0,015 em.
  Hell-auf-dunkel wirkt fetter: Weight eine Stufe runter (350 statt 400),
  line-height +0,05–0,1, letter-spacing +0,01 em. `tabular-nums` bei
  gestapelten/zählenden Zahlen.
- Weight-Kontrast extrem fahren (300 vs 900, nicht 400 vs 700); eine
  Fontfamilie, max. 2 Gewichte; nie zwei ähnliche Sans paaren; nie
  Kursiv als Emphase im Video.
- 3 s Screentime ⇒ Text muss in 2 s lesbar sein.

## 5. Text auf Footage — Luminanz-Gates

- BG-Luma < 60: helle Schrift pur.
- 60–180: Glyph-Scrim 30–40 % (nur textbox-groß, nie framebreit).
- > 180: opake dunkle Schrift + Scrim; Screen-Blend versagt auf hell.
- Kontrast-Eskalation in dieser Reihenfolge: Blend-Mode → Stroke 2–3 px +
  Soft-Shadow → schmale Gradient-Bar → lokales Abdunkeln 10–15 % →
  weiße Pill-Box (auf cinematischem Material verboten).
- **Keine framefüllenden Linear-Gradients auf dunklen BGs** — H.264/
  Social-Encoding bandet sie sichtbar. Radial-Gradient oder Solid + Glow.

## 6. Technik-Fallen (gelten in Remotion 1:1)

- Nie zwei konkurrierende Transform-Animationen auf demselben Element
  (z. B. Entrance-Slide + Ken-Burns-Zoom): auf Wrapper (Entrance) und
  Child (Zoom) splitten oder in einen Tween kombinieren.
- Nur `transform` + `opacity` animieren — nie `width/height/top/left`,
  nie `letter-spacing` oder `filter: blur` am Wort-Entrance (Reflow kann
  Zeilenumbruch springen lassen).
- Einzel-Properties `scale` und `rotate` im Inline-Style immer als String
  setzen (`scale: String(x)`, `rotate: \`${deg}deg\``): React 18 hängt an
  Zahlen „px“ an, der Wert ist ungültig und die Animation fällt ohne
  Fehlermeldung aus (Schmitt 2026-09). `transform: \`scale(${x})\`` ist
  unkritisch.
- Layout-Konstanten (Positionen, Breiten) vorab berechnen, nicht pro
  Frame messen. Wortbreiten-Schätzung: `fontSize × Zeichen × 0,55`
  (kursiv 0,50, Versalien-fett 0,62) — gegen die längste Zeile nach
  Umbruch rechnen.
- Ken Burns dezent: scale 1→1,04 über die Beat-Dauer.
- Audio-reaktive Pulse: Logos ≤ 4–5 % Scale, BG-Flächen 10–30 % — nie
  Equalizer/Waveforms zeigen.
- Quellvideos für frame-genaues Scrubbing (`<OffthreadVideo>`) ggf. mit
  dichten Keyframes re-encoden (`-g`/`-keyint_min` = fps), sonst frieren
  Seeks ein.

## 7. Interview-Overlays: Karten-Pacing (talking-head-Formate)

Wenn ein Interview/Talking-Head mit Grafik-Karten überzogen wird
(Lower-Thirds, Daten-Callouts, Zitate):

- Basistempo nach Videolänge: < 60 s → 6–8 s/Karte; 1–3 min → 8–12 s;
  3–10 min → 12–20 s; 10–30 min → 20–35 s. Dichte-Multiplikator:
  datendicht ×0,7, gemischt ×1,0, eine lange Story ×1,5. Min. 5 Karten.
- Karten > 15 s Standzeit brauchen einen Multi-Step-Reveal — ein
  statischer Einzeiler langweilt ab ~8 s.
- Ein Akzent-Farbindex pro Karte; gleicher Index = gleicher Erzähl-Beat.
  2–3 wiederkehrende Motion-Patterns pro Video, nicht mehr.
- PiP-Karte 16:9: 400×300 unten rechts, Radius 16, weißer Ring,
  Schatten `0 12px 40px rgba(0,0,0,.35)`.

## 8. Musik-Trim

Library-Tracks öffnen oft mit leisem Build, der die ersten Sekunden eines
kurzen Videos verschenkt: Opening gegen spätere 5-s-Abschnitte
gegenhören und ggf. ab der stärkeren, musikalisch sauberen Stelle
trimmen. Kurzer Fade-in, längerer Fade-out. Nach jeder Längenänderung
neu prüfen. (Quellen bleiben Artlist/Envato.)

## 9. Scope-Disziplin

Auftrag exakt halten: „Title-Card" heißt Title-Card — nicht Title-Card +
drei Szenen + Musik. Erweiterungen im Chat anbieten, nicht ungefragt
einbauen.
