# Protokoll — Craiss Logistik / 4 Ads / 2026-08 Dein erster Tag

## 2026-08-26 — Hook- & CTA-Animation (Video 01)

**Gemacht:**
- Neuen Motion-Client `craiss` angelegt (CI von craiss.com abgeleitet):
  Craiss-Rot `#CD202C` (Logo-Fill/Buttons), Anthrazit `#3D3D3D`,
  Font **Laski Slab** (Light/Regular/Bold/Black, Original-Webfonts der Website),
  Logo als Original-SVG → `tools/motion/public/clients/craiss/`.
- Komposition `Craiss-ErsterTag` (+ `-Preview` mit Footage/Blur-Simulation)
  in `tools/motion/src/clients/craiss/projects/erster-tag/`:
  - **Hook** 0,24–3,6 s: „DEIN ERSTER TAG" (Laski Slab Black) + roter Chip
    „BEI UNS", oben im Himmel-Bereich, Ausblendung endet vor dem Schnitt bei 3,72 s.
  - **CTA** ab 24,32 s (3 Frames nach dem Schnitt auf den Drohnen-Endshot bei 24,2 s):
    Logo-Karte (rot auf weiß), „WERDE TEIL DER / GENERATION LOGISTIK",
    Button „JETZT BEWERBEN", `craiss.com/karriere` — alles steht nach ~1,1 s.
- Video vom NAS nach `Material/Video/` kopiert; Wort-SRT nach `Material/Transcription/`.
- H.264-Proxy in `Material/Video/proxy/` erstellt — das 10-bit-HEVC aus Resolve
  liefert im Remotion-Frame-Extraktor (Render/Stills) falsche Frames beim Seeken;
  Studio-Preview war korrekt. Footage-Vergleich nutzt deshalb den Proxy.

**Geliefert:**
- `Ergebnisse/Renders/01_ErsterTag_HookCTA_Preview_v1.mp4` (1080×1920, H.264,
  Overlay über Footage inkl. simuliertem End-Blur — nur zur Abnahme, kein Liefermaterial).
- `Ergebnisse/Renders/01_ErsterTag_HookCTA_v1.mov` — **Final**, ProRes 4444
  mit Alpha (yuva444p12le), 2160×3840, 25 fps, 749 Frames. Nach Davids Go
  gerendert. `flicker-check.sh`: 3 Kandidaten (Frames 9/86/611), alle in
  Fade-Rampen; Alpha-Verlauf pro Frame nachgemessen — monoton, Ausblendung
  endet auf exakt 0, kein Rest-Alpha, Frame 100 komplett transparent.

**Entscheidungen:**
- Hook-Copy „Dein erster Tag / bei uns" nach Videotitel; Zwei-Gewicht-Motiv
  wie Website (GENERATION/LOGISTIK).
- CTA-URL `craiss.com/karriere` (301→200 geprüft).
- Safe Zone: CTA-Block hochgesetzt, damit URL-Zeile über der unteren
  IG/TikTok-UI-Zone bleibt. Face Zone: In Hook- und CTA-Fenstern sind keine
  Gesichter im Bild (Schnitte 0–3,72 s nur LKW, ab 24,2 s nur Landschaft) —
  per Stills gegen jeden betroffenen Shot geprüft.

**Offen:**
- Videos 02–04 der Charge noch unbearbeitet.

**Render-Hinweis:** `remotion render` bricht auf diesem Mac sporadisch sofort
mit „Visited …/index.html but got no response" ab — einfach erneut starten
(Erfolg meist im 1.–2. Wiederholungsversuch), immer mit explizitem freiem
`--port` und `--public-dir=public-craiss`.

## 2026-09-01 — Migration ins Studio-Hauptsystem

**Gemacht:** Charge vom Zweit-MacBook übernommen und unter
`projects/Craiss/4 Ads/` eingegliedert — liegt jetzt neben der Charge
„2026-08 Dreh" (O-Ton-Pläne/Schnittanweisungen zu denselben 5 Videos).
Inhalte unverändert.
