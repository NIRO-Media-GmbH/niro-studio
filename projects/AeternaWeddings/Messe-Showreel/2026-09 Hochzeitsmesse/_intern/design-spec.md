# Design-Spec — Aeterna Messe-Screen (abgenommen 2026-09-11)

## Auftrag
75" LG LCD auf der Hochzeitsmesse, Wiedergabe per USB-Stick im Dauerloop. Links läuft das
Hochzeits-Showreel (noch ungeschnitten, gedreht in 25p, Zielänge 5:00), rechts animierte
Info-Kapitel. Die komplette Datei entsteht in Remotion (User-Entscheidung: kein
Resolve-Compositing).

## Look „Elfenbein“ (Look B)
- Grund `#FCFBF8` · Text `#3B352F` · Gold `#C1A67A` (Linien, Ornamente, Logo) · tieferes Gold
  `#9C8156` für Schreibschrift-Text (Kontrast auf Elfenbein)
- Playfair Display (Headlines) · Red Hat Text (Body) · Great Vibes (Script-Akzent) — alle
  als `@remotion/google-fonts`
- Logo: `projects/AeternaWeddings/CI/Aeterna/aeterna-Logo.svg` (Gold-Wortmarke)

## Layout (Raster 1920×1080, Code rechnet ×2 → 3840×2160)
| Element | Maß (1080er Raster) |
|---|---|
| Showreel-Fenster | 1152×648, x 64, vertikal mittig; leichte Rundung + Gold-Haarlinie als Passepartout |
| Claim unter dem Video | „Euer Tag. Eure Erinnerungen. Für immer spürbar.“ in Great Vibes, tieferes Gold |
| Info-Spalte | x 1280–1856 (576 breit): Logo oben · Kapitel Mitte · QR unten |
| Headlines | 64–72 px Playfair |
| Body | ≈ 42 px Red Hat Text (75": ≈ 3,6 cm, lesbar aus 3–4 m) |
| QR | ≈ 180 px (≈ 15 cm, Scan aus ≈ 1,5 m), Dunkelbraun auf Elfenbein, Quiet Zone ≥ 4 Module, statisch; CTA „Kostenfreies Kennenlernen“ |
| Fortschritt | 8 feine Gold-Segmente |

## Kapitel (8 × 12,5 s = 100-s-Zyklus × 3 = 5:00; skaliert mit der echten Videolänge)
1. **Liebe, die man sieht.** Momente, die man fühlt.
2. **Fotos zeigen, wie es aussah.** Film zeigt, wie es sich angefühlt hat.
3. **Alles aus einer Hand:** Cinematic Film · Social-Reels inklusive · Foto auf Wunsch
4. **48–72 h** Sneak Peek · **24 h** erste Reels · **100 %** pünktliche Lieferung (Count-up)
5. **Was euch nicht passiert:** Keine gestellten Posen · Kein Warten ohne Ende · Keine Überraschungen · Kein Risiko
6. **Aeterna Legacy:** Geführte Interviews mit euch und euren Liebsten
7. **Ein eingespieltes Team. Ein Ansprechpartner.** Deutschlandweit · 2027 noch Termine frei
8. **Messe-Bonus:** Ein Extra-Reel geschenkt – bei Buchung bis 14 Tage nach der Messe

Ausgeschlossen: Preise, Verlosung, Instagram, Team-Fotos, Kundenstimmen, Reue-Statistiken, Ablauf-Kapitel.

## Motion
- Kapitelwechsel: Exit 0,4 s Fade (ease-in) → Entry zeilenweise Masken-Reveal 0,7 s ease-out, Stagger 120 ms, Gold-Linie DRAWS
- Multi-Step-Reveal im Kapitel (Punkte nacheinander, Zahlen zählen) → nie > 5 s Stillstand
- Deko: feine Gold-Ornamente (Zweige/Ringe) als Path-Draw, 15–20 % Deckkraft; langsamer Goldstaub
- Loop-exakt: alle Drifts/Periodik mit ganzzahligen Perioden pro 100-s-Zyklus; letzter → erster Frame nahtlos
- Kein Bounce; LCD → kein Burn-in-Drift nötig

## Technik
- Remotion-Client `aeterna-weddings` (brand.json, Logo nach `public/clients/aeterna-weddings/`)
- `fpsSchema` in `src/core/schemas.ts` um 50 erweitern
- Composition 3840×2160 @ 50 fps nativ (`--scale` skaliert Video nicht hoch)
- Dauer aus der Showreel-Datei (`@remotion/media-parser`), Zyklus = Dauer / 3; Platzhalter 5:00, solange kein Schnitt existiert
- 25p-Video in 50p = exakte Bildverdopplung
- QR per npm-Paket erzeugt (Ziel noch Platzhalter)
- Render: `--codec=h265 --hardware-acceleration=if-possible --video-bitrate=40M`, MP4, Showreel-Ton als AAC; LG-Grenze HEVC 4K60 Main/Main10 @ L5.1 ≤ 60 Mbps (H.264 4K nur 30p!)
- Schlanker `--public-dir`-Spiegel laut WORKFLOW-Motion

## Verifikation
Stills pro Kapitel in 4K · Loop-Naht (letzter vs. erster Frame) · ffprobe (Profil/Level/Bitrate/fps) · QR scannen · früher 30-s-Testclip am echten LG (USB-Start, Repeat-Funktion, Elfenbein-Helligkeit)

## Offen
QR-Ziel, Betrachtungsabstand. Nächster Meilenstein: 4K-Standbild des Layouts.
