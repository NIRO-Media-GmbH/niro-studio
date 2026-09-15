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

## 2026-09-07 — CTA-Umbau nach Kundenwunsch (CI-Handbuch)

- CI-Handbuch vom NAS gesichtet (`_intern/ci/170531_CRAISS_CD-Handbuch.pdf`,
  Kopie): offizielles Logo = Wortmarke + rechts „GENERATION/LOGISTIK"
  zweizeilig in **Craiss-Blau #002F5F** (Primärfarbe! S. 21); Farbversion
  nur auf hellem Grund (S. 11). Lockup als `CraissLogoLockup` in lib
  nachgebaut (color/white/black), Proportionen aus S. 13 abgemessen.
- **CTA-Serie umgebaut (Kundenwunsch):** „WERDE TEIL DER" + offizielles
  Logo auf weißer Karte statt Text-Claim „GENERATION LOGISTIK". Gilt für
  den geteilten `Cta` und die `Endcard` (betriffen 01/02/03/05 sowie
  Video-04-Transition/-Endlogo in Studio; Re-Render der anderen Videos
  nach Freigabe).
- **Geliefert:** `Ergebnisse/Renders/01_ErsterTag_HookCTA_v2.mov`
  (Final, neuer CTA — ersetzt v1). flicker-check: 2 Kandidaten
  (F9/F86, bekannte Hook-Rampen); Alpha der neuen CTA-Rampe
  frameweise monoton, Leerbereich exakt 0, letzter Frame steht.
- Offen: Re-Render 02/03/05 mit neuem CTA nach Davids Freigabe.

**Render-Hinweis:** `remotion render` bricht auf diesem Mac sporadisch sofort
mit „Visited …/index.html but got no response" ab — einfach erneut starten
(Erfolg meist im 1.–2. Wiederholungsversuch), immer mit explizitem freiem
`--port` und `--public-dir=public-craiss`.

## 2026-09-07 — v2-Final: Kunden-CTA (CI-Handbuch) 
- Geteilte Bausteine umgestellt: CTA/Endcard = „WERDE TEIL DER" +
  offizielles Logo-Lockup (Wortmarke + GENERATION/LOGISTIK in
  Craiss-Blau #002F5F, CD-Handbuch S. 13/21), nach Davids Größen-Review
  um 20 % vergrößert (Wortmarke 480 px, bleibt in der Safe Zone).
- **Geliefert:** `Ergebnisse/Renders/01_ErsterTag_HookCTA_v2.mov` (ProRes 4444 Alpha, ersetzt v1).
  flicker-check: nur bekannte Ein-/Ausblenderampen, keine Ausfälle.

## 2026-09-07 — Untertitel für V3-Schnitt (nur Untertitel, Hook/CTA unverändert)

**Ausgangslage:** `Material/Video/01_Dein_erster_Tag_bei_uns_V3.mp4` ist kein
Rohmaterial, sondern der bereits fertig komponierte Schnitt (Hook+CTA schon
eingebrannt) — vermutlich von David als Referenz für den nächsten Schritt
dort abgelegt statt in `Ergebnisse/Renders/`. Für Untertitel deshalb direkt
darauf aufgesetzt statt die Hook/CTA-Komposition neu zu bauen.

**Gemacht:**
- H.264-Proxy `Material/Video/proxy/01_Dein_erster_Tag_bei_uns_V3_proxy.mp4`
  erstellt (gleicher Grund wie beim V1-Proxy: 10-bit-HEVC liefert falsche
  Frames beim Seeken).
- Wort-genaues Transkript per ElevenLabs Scribe neu gezogen
  (`_intern/cache/01_Dein_erster_Tag_bei_uns_V3.scribe.json`) — die
  vorhandene SRT hatte ASR-Aussetzer („Arbeitentableten“, „Wachstatt“ statt
  „Werkstatt“). Sprache endet bei 19,24 s, danach nur noch Outro-Musik (die
  SRT-Zeile „Ich mag meine Arbeit“ bei ~23 s existiert im V3-Ton nicht mehr —
  V3 ist offenbar kürzer geschnitten als der SRT-Stand).
- Caption-Seiten generiert (`scripts/craiss-captions.ts`, gleiche
  Gruppierungslogik wie `scripts/sw-captions.ts`): 11 Seiten, 2–5 Wörter,
  automatisch nur außerhalb Hook (0,24–3,6 s) und CTA (ab 24,32 s) sichtbar.
  Erste Zeile „Erster Tag, lerne alles.“ bewusst gedroppt (dopplt den Hook).
- Neue Komposition `Craiss-ErsterTag-Untertitel` (nur Untertitel-Layer über
  dem fertigen V3-Footage, Hook/CTA/Composition-01 unangetastet) +
  `clients/craiss/Subtitles.tsx` (Rail-Stil, Laski Slab Bold, Highlight in
  aufgehelltem Rot `#E5484F` statt Marken-Rot — Markenrot wirkte auf
  dunklem Footage matt).
- **Platzierung:** Kunde hatte sich früher über Elemente im Halsbereich
  beschwert. Kontaktbogen-Check (11 Cues durchgerendert mit Safe-Zone/
  Face-Zone-Guides) zeigt: generisches Safe-Zone-Band (45–57,5 %) liegt in
  den engsten Nahaufnahmen dieses Videos exakt auf Kinn/Kragen. Nach
  Iteration mit David (zu tief → zu hoch → Kompromiss) landet die Leiste
  knapp unter Bildmitte, für alle 11 Cues identisch (Davids Vorgabe:
  einheitliche Höhe wichtiger fürs Social-Media-Bild als jede Einstellung
  einzeln kinnfrei zu bekommen). Bei den zwei engsten Close-ups (8,6 s /
  14,06 s) streift der Text kurz den Kragen — akzeptiert, nie das Gesicht.
- Liegt damit außerhalb der generischen `getSafeZonePixels()`-Vorgabe aus
  `core/format-utils.ts` — bewusste, mit David abgestimmte Abweichung nur
  für diese Untertitel-Buehne, kein Eingriff am globalen Default.

**Geliefert:**
- `Ergebnisse/Renders/01_ErsterTag_HookCTA_Untertitel_v1.mp4` (H.264,
  1080×1920, 25 fps, aus dem V3-Proxy — Bild inkl. Hook/CTA/Untertitel).

**Offen:**
- `Material/Video/01_Dein_erster_Tag_bei_uns_V3.mp4` sollte eigentlich nach
  `Ergebnisse/Renders/` gehören (ist kein Rohmaterial) — nicht verschoben,
  da außerhalb des Auftrags („nur Untertitel“); bei Gelegenheit aufräumen.
- Videos 02–05 der Charge-Serie haben noch keine Untertitel.

## 2026-09-11 — Code-Migration, Untertitel-Vorschau, Kundenfeedback-Check

- Craiss-Code vom Zweit-MacBook übernommen (SSD „NIRO Studio Alte Version
  für Craiss“, dort nur gelesen): `Subtitles.tsx`, `captions/`, 5×
  `CompositionSubtitled.tsx`, lib mit Kunden-CTA/SOFT, Fonts + Logo,
  `scripts/craiss-captions.ts`. Symlinks `public/projects/craiss-*` auf
  `projects/Craiss Logistik/…` umgebogen.
- `Craiss-ErsterTag-Untertitel` (Studio-Ordner Craiss → Untertitel-Final):
  Studio zeigt den V3-Schnitt darunter, Render = nur Untertitel als Alpha
  2160×3840 (`transparent`).
- Exporte ohne Animation vom NAS (`04_Exportiert/Alle Videos ohne Aniamtionen
  für Timing NIRO Studio`) nach `Material/Video/ohne-Animation/` + H.264-Proxy.
  Gleicher Schnitt wie V3 animiert (Schnittliste identisch), aber **751 statt
  743 Frames** — das HookCTA-Overlay v2 hat 749 Frames, endet also 2 Frames
  vor dem Clip (Cutter: Ende prüfen).
- Kundenfeedback-Check: „Ich mag meine Arbeit“ am Ende raus ✓, Abspann
  „Werde Teil der“ + offizielles Logo ✓. Verständlichkeit: am Ton nicht
  zu ändern, Untertitel helfen.
- QC Export: −18,6 LUFS integriert, True Peak −0,4 dBFS, keine Schwarzbilder.

- **Abnahme-Vorschau** `Craiss-Vorschau-01-ErsterTag` (Studio: Craiss →
  Vorschau-Neu): Export ohne Animation + aktuelle Animationen + Untertitel.
  `Craiss-ErsterTag`-Defaults auf den Kunden-Schnitt umgestellt (30,04 s,
  Footage = Export ohne Animation, kein simulierter Blur); Hook/CTA-Zeiten per
  Kontroll-Render gegen den animierten V3 bestätigt. Abspann nutzt jetzt den
  aktuellen Serien-CTA (ruhige SOFT-Bewegung wie 04, Layout gleich).

**Offen:** Untertitel-Render (Alpha) nach Freigabe in der Studio-Vorschau.

## 2026-09-11 — Untertitel-Look „Mix" (Video 01, Vorschau)

- Anlass: Feedback „Untertitel langweilig“ — neuer Look freigegeben im Chat
  (Mix aus Grundzeile, Hero-Wort weiß/rot/blau, Wort-Kasten, Glas-Wort; ruhige
  Bewegung, Position je Einstellung, nie am Hals).
- Spec `tools/motion/docs/superpowers/specs/2026-09-11-craiss-untertitel-mix-design.md`,
  Plan `tools/motion/docs/superpowers/plans/2026-09-11-craiss-untertitel-mix.md`.
- Neu: `src/clients/craiss/captionMix/` (Schema/Prüfregeln, Layout, Timing,
  Plan-Erzeugung, Renderer, 16 Tests via `npx tsx --test`) +
  `scripts/craiss-caption-plan.ts` (erzeugen / `--check`).
- Plan `captions/erster-tag-v3.plan.json` (6 Sätze): Aufzählung BÜRO /
  WERKSTATT / AUTOWÄSCHE (Wort-Kasten), KINDERLEICHT (weiß), JUNG ODER ALT
  (rot), EINGEWIESEN (blau), Glas IMMER im Himmel über dem telefonierenden
  Fahrer. Sätze erscheinen nur vollständig (keine Satzteile mehr).
- Sichtprüfung: Kontaktbogen je Satz mit Face-/Safe-Zone-Guides — Hals und
  Gesichter frei; Glas-Wort um 20 px angehoben (berührte die Mütze).
- Vorschau `Craiss-Vorschau-01-ErsterTag`: Prop `subtitleStyle` neu/alt.

**Offen:** Alpha-Render der Untertitel-Spur. (01 im Chat abgenommen — „ja passt,
mach alle so"; 02–05 am selben Tag nach demselben System umgesetzt.)

## 2026-09-11 — UT-Korrektur nach Durchsicht (Video 01, wirkt für alle)

- „Arbeiten Tablet" → **„Arbeit am Tablet"** (Plan-Token + `craiss-captions.ts`-Fix).
- **Autowäsche doppelt:** In der Aufzählung stand das Wort in der Grundzeile
  und im Kasten. Renderer blendet Aufzählungs-Wörter jetzt aus der Grundzeile
  aus (`pageTokensWithoutBox`, Test) — gilt auch für 03 ARABISCH/POLNISCH.
- **„ja" bei 13,11 nur 2 Frames:** Seitenwechsel wartet jetzt, bis das letzte
  Wort einer Seite 0,4 s stand (`MIN_LAST_WORD_SEC`, Test). Betraf 47 Stellen
  in allen 5 Videos (z. B. 03 „damit er", 04 „glaube ich,").
- `Untertitel-Final`-Kompositionen (Alpha-Render-Ziel) zeigen jetzt ebenfalls
  den neuen Look; der alte nur noch in Vorschau-Neu über `subtitleStyle: alt`.
- Geprüft: 19 Tests grün, tsc sauber, alle 5 Pläne ohne Fehler, Stills 5,0 /
  6,6 / 7,4 / 13,44 / 13,6 s (01), 16,8 s (03), 9,2 s (02 in Untertitel-Final).

## 2026-09-11 — Lieferung: eine Alpha-Datei (Animationen + Untertitel)

- User-Wunsch „für jedes Video nur eine lange Datei" (gilt für 01–05): neuer
  Remotion-Ordner `Craiss → Alpha-Komplett` mit `Craiss-Alpha-01…05` — dieselbe
  Komposition wie Vorschau-Neu (`craissAlphaDefaults`), aber 2160×3840 und
  transparent; der Schnitt darunter erscheint nur im Studio, nie im Render.
- **Geliefert:** `Ergebnisse/Renders/01_ErsterTag_Alpha_Komplett_v1.mov` —
  ProRes 4444 Alpha (yuva444p12le), 2160×3840, 25 fps, 751 Frames. Hook, CTA
  und Untertitel-Mix in einer Datei; ersetzt `…_HookCTA_v2.mov`.
- Prüfung: Alpha-Stills (Ecke transparent), flicker-check (Kandidaten nur an
  Ein-/Ausblendungen und Satzwechseln), Suche nach isolierten Ein-Frame-
  Einbrüchen: 1 (Frame 150) = geplanter Wort-Kasten-Wechsel BÜRO → WERKSTATT,
  per Einzelbild geprüft. Kontaktbogen (alle 3 s, über Grau) geprüft.

- **NAS + Resolve (gilt für 01–05):** Dateien ohne Tonspur (verlustfrei
  umverpackt, bytegleich geprüft) nach NAS `…/01_Projekt-4 Ads/03_Medien/02_Assets/
  07_Animation/<Videoordner>/`. Resolve-Projekt `01_Projekt_4_Ads`: Import in Bin
  `03_GRAPHICS/Claude Alpha Komplett 2026-09-11 1945` (Alpha Straight, 0 Audio-Kanäle),
  in Timeline `01_Dein_erster_Tag_bei_uns_V3` neue oberste Spur **V9 „NIRO Alpha
  Komplett"** ab Timeline-Start, 751 Frames, nur Video; Audio-Spuren/-Clips
  unverändert, Timeline des Users wiederhergestellt.

**Offen:** Alte Overlay-Spur V6 (`01_ErsterTag_HookCTA_v2.mov`) liegt noch drin —
Cutter muss sie deaktivieren, sonst doppelte Grafik; Kunden-Abnahme. Code uncommittet.
