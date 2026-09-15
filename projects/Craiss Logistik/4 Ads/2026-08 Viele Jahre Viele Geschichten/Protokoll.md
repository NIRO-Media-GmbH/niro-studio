# Protokoll — Craiss Logistik / 4 Ads / 2026-08 Viele Jahre Viele Geschichten

## 2026-08-26 — Hook, Flaggen & CTA-Endcard (Video 03)

**Gemacht:**
- Lose Dateien aus `4 Ads/` einsortiert; H.264-Proxy erstellt (Quelle 10-bit-HEVC).
- Komposition `Craiss-VieleJahre` (+ `-Preview`):
  - **Hook** 0,24–2,72 s als Lower-Third (Talking-Head-Opener, Ende auf dem
    Schnitt): „VIELE JAHRE" + Chip „VIELE GESCHICHTEN" (Videotitel).
  - **Flaggen** 7,84–10,64 s synchron zur Kollegen-Aufzählung
    (Wortanfänge aus SRT): Ungarn 7,84 / Tschechien 8,64 / Rumänien 9,28 /
    Litauen 9,76. Inline-SVG in offiziellen Flaggenfarben + Label.
    **Davids Feedback umgesetzt: Staffellauf statt Sammelreihe** — jede
    Flagge fliegt am Wortanfang von rechts ein und beim nächsten Wort nach
    links raus, nichts bleibt stehen („sonst wirkt es, als wären nur diese
    4 Länder akzeptiert"). Alle raus vor dem Schnitt bei 10,68 s.
    PL-Flagge in der lib vorhanden (ungenutzt, für evtl. Gags).
    **v3:** Litauen von 9,76 auf 10,08 verschoben — SRT-Wortgrenze zu früh,
    echter Einsatz laut Wellenform nach Sprechpause (~10,05–10,25).
    **v4:** Litauen hielt nach hinten zu kurz → hält jetzt bis 11,56 über
    den Schnitt bei 10,68 (Close-up) durch „Alles.". Dafür alle Flaggen
    kompakter (160×96) und tiefer (Label exakt auf Safe-Zone-Unterkante),
    weil die alte Größe/Position im Close-up das Kinn überdeckt hätte.
  - **CTA als opake Endcard** ab 40,84 s (Website-Look: weiß, roter
    Akzentbalken, rotes Logo, Anthrazit-Text, Texte/Stack wie Serie):
    Die Sprache läuft bis 40,8 s und der letzte Shot (Büro ab 38,16 s) ist
    ein Talking Head — kein freier Endshot fürs Overlay-Muster der Videos
    01/02. Komposition verlängert das Video deshalb auf **46 s**.
- lib.tsx erweitert: `FlagsRow` (+ Schemas), `Endcard`.

**Kontext:** Video bewusst satirisch/stereotypisch. Begrüßungen am Anfang:
Polnisch/Ungarisch/Rumänisch/Tschechisch (SRT verstümmelt, Timings 0,08–2,36 s).
Polnischer Fluch ~28,5–29,2 s („Entschuldigung." 29,24) — bleibt evtl. im
Schnitt; bewusst KEIN Overlay dazu gebaut (Davids Schnitt-Entscheidung).

**Update CTA:** Nach Abnahme der v4 wollte David die Endcard **transparent**
statt mit weißem Grund (Hintergrund macht er im Schnitt). Der finale CTA ist
deshalb der Standard-Serien-CTA aus Video 01/02 (weiße Schrift mit Schatten,
Logo auf weißer Karte) auf Alpha — die opake `Endcard`-Komponente bleibt
ungenutzt in der lib. Komposition weiterhin 46 s (Video endet bei 40,76 s,
CTA ab 40,84 s auf transparentem Grund).

**Geliefert:**
- `Ergebnisse/Renders/03_VieleJahre_HookFlagsCTA_Preview_v1–v4.mp4` (Abnahme-Previews).
- `Ergebnisse/Renders/03_VieleJahre_HookFlagsCTA_v1.mov` — **Final**, ProRes
  4444 mit Alpha (yuva444p12le), 2160×3840, 25 fps, 1150 Frames (46 s).
  `flicker-check.sh`: 3 Kandidaten (Frames 9/64/1024), alle in Fade-Rampen;
  Alpha frameweise nachgemessen — monoton, Flaggen-Übergaben sauber,
  Leerbereiche (Frames 150/500/1000) exakt 0, letzter Frame steht.

**Offen:**
- Video 04 noch unbearbeitet.

## 2026-09-07 — v2-Final: Kunden-CTA (CI-Handbuch) 
- Geteilte Bausteine umgestellt: CTA/Endcard = „WERDE TEIL DER" +
  offizielles Logo-Lockup (Wortmarke + GENERATION/LOGISTIK in
  Craiss-Blau #002F5F, CD-Handbuch S. 13/21), nach Davids Größen-Review
  um 20 % vergrößert (Wortmarke 480 px, bleibt in der Safe Zone).
- **Geliefert:** `Ergebnisse/Renders/03_VieleJahre_HookFlagsCTA_v2.mov` (ProRes 4444 Alpha, ersetzt v1).
  flicker-check: nur bekannte Ein-/Ausblenderampen, keine Ausfälle.

## 2026-09-07 — Untertitel für V3-Schnitt (Teil der Craiss-01–05-Serie)

Gleiches Vorgehen wie Video 01/02: `Material/Video/
03_Viele_Jahre_Viele_Geschichten_V3.mp4` ist der fertig komponierte Schnitt
(Hook+Flaggen+CTA eingebrannt). H.264-Proxy gebaut, Scribe-Transkript neu
gezogen (ASR-Fehler „Kreis"→Craiss korrigiert), 39 Caption-Seiten generiert,
neue Komposition `Craiss-VieleJahre-Untertitel`.

V3 ist ~5,7 s **länger** als der `craissVieleJahreDefaults`-Stand — Hook/
Flaggen/CTA-Sperrzeiten per Frame-Kontaktbogen neu vermessen: Hook 0–3,0 s,
Flaggen 7,6–11,8 s (deckt sich mit den Root.tsx-Werten), CTA ab 46,3 s
(Schnitt ~46,65 s). Multilinguale Begrüßungen am Anfang (Dzień dobry/Buna
ziua/Zdravím/…) liegen komplett im Hook-Fenster und fallen damit unter den
Untertitel raus — inhaltlich unkritisch, Hook trägt bereits den Videotitel.

Gleiche Untertitel-Höhe/-Stil wie Video 01/02. Keine Kollisionen mit
Zitat-/Flaggen-Grafiken gefunden (Kontaktbogen deckte alle 39 Seiten ab).

**Geliefert:** `Ergebnisse/Renders/03_VieleJahre_HookFlagsCTA_Untertitel_v1.mp4`
(H.264, 1080×1920, 25 fps, aus dem V3-Proxy).

**Offen:** `Material/Video/03_Viele_Jahre_Viele_Geschichten_V3.mp4` gehört
eigentlich nach `Ergebnisse/Renders/` (kein Rohmaterial) — nicht verschoben,
außerhalb des Auftrags.

## 2026-09-11 — Code-Migration, Untertitel-Vorschau, Kundenfeedback-Check

- Craiss-Code vom Zweit-MacBook übernommen (Details im Protokoll 01).
  `Craiss-VieleJahre-Untertitel`: Studio mit V3-Schnitt, Render = Alpha.
- Export ohne Animation vom NAS nach `Material/Video/ohne-Animation/`
  (+ Proxy): identischer Schnitt zu V3 animiert; Grafiken per Differenz
  gemessen (Hook 0,36–2,6 s, Flaggen 7,92–11,52 s, CTA ab 46,76 s).
- Kundenfeedback-Check (Kunde bezog sich auf V2, hier liegt V3):
  „Ich lerne Deutsch sprechen“ raus ✓, Opa Didi drin (32–40 s) ✓, Abspann ✓.
  **Teilweise:** Tomasz — nur ein neuer Satz („Viele Fahrer wundern sich …“),
  die gewünschten emotionalen Passagen über die Fahrer fehlen.
  **Nicht umgesetzt:** Abwechslung — Flaggen-Passage und „Rente“/„optimal“
  laufen auch in 05. Videotitel klärt Jan direkt mit der Kundin.
- QC Export: −15,9 LUFS, **True Peak +1,0 dBFS** (Cutter), keine Schwarzbilder.

- **Abnahme-Vorschau** `Craiss-Vorschau-03-VieleJahre` (Craiss →
  Vorschau-Neu). `Craiss-VieleJahre`-Defaults auf den Kunden-Schnitt
  umgestellt: 51,64 s, CTA 46,64 s auf dem Drohnen-Endshot (vorher Endcard
  ab 40,84 hinter dem V1), Footage = Export ohne Animation; per Kontroll-Render
  gegen den animierten V3 bestätigt.

**Offen:** Untertitel-Render nach Freigabe; Tomasz-Material + Abwechslung
sind Cutter-Sache.

## 2026-09-11 — Untertitel-Look „Mix" (nach Abnahme von 01 übertragen)

- Sperrfenster exakt auf die Overlay-Sequenzen gesetzt (Hook bis 2,72 s,
  Flaggen 7,84–11,6 s, CTA ab 46,64 s) — dadurch ist „Wir haben hier in der
  Dispo …" wieder sichtbar.
- Plan `captions/viele-jahre-v3.plan.json`: SPRACHEN (rot), Aufzählung
  ARABISCH/POLNISCH (Wort-Kasten), KEIN PROBLEM (blau), RESPEKTVOLL (weiß),
  FÜNFZIG JAHR (rot), Glas RENTE im Himmel über Opa Didi, DU BIST KEINE ZAHL
  (Wort-Kasten); 11 von 17 Sätzen sichtbar (Begrüßungen unter dem Hook,
  Kollegen-Aufzählung unter den Flaggen, letzter Satz unter dem CTA).
- Sichtprüfung: „Du bist keine Zahl." war auf den verdeckten Folgesatz
  gekappt (ZAHL nur 7 Frames) → Satzende auf 45,6 s verlängert, per Still geprüft.
- Vorschau `Craiss-Vorschau-03-VieleJahre`.

- **Nachtrag (Feedback „sieht aus wie der alte Stil"):** Dichte wie Video 01 —
  + EINFACH (weiß), DEUTSCH (blau), KEIN PROBLEM jetzt rot, GUTE ATMOSPHÄRE
  (blau), KONTAKT (weiß); einzige Grundzeile ist der Satz mit Glas RENTE.
  Kontaktbogen neu geprüft.

- **UT-Korrektur (Kunde/Jan):** bei 40 s „und bei Craiss passt optimal." (ASR-
  „ist" gestrichen), per Still geprüft.

## 2026-09-11 — Lieferung: eine Alpha-Datei (Animationen + Untertitel)

- User-Wunsch „für jedes Video nur eine lange Datei": Remotion `Craiss →
  Alpha-Komplett` / `Craiss-Alpha-03-VieleJahre`.
- **Geliefert:** `Ergebnisse/Renders/03_VieleJahre_Alpha_Komplett_v1.mov` —
  ProRes 4444 Alpha (yuva444p12le), 2160×3840, 25 fps, 1291 Frames. Hook,
  Flaggen, CTA und Untertitel-Mix in einer Datei; ersetzt `…_HookFlagsCTA_v2.mov`.
- flicker-check: Kandidaten nur an Ein-/Ausblendungen und Satzwechseln; einziger
  isolierter Einbruch (Frame 521) = geplanter Wort-Kasten-Wechsel ARABISCH →
  POLNISCH, per Einzelbild geprüft. Kontaktbogen geprüft.

- **NAS + Resolve:** NAS `03_Medien/02_Assets/07_Animation/03_Viele_Jahre_Viele_Geschichten/`
  (ohne Tonspur); Resolve `01_Projekt_4_Ads` → Timeline
  `03_Viele_Jahre_Viele_Geschichten_V3`, neue oberste Spur V9 „NIRO Alpha
  Komplett", ab Start, 1291 Frames, nur Video (Details Protokoll 01).

**Offen:** Alte Overlay-Spur V6 (`03_VieleJahre_HookFlagsCTA_v2.mov`) noch drin —
deaktivieren, sonst doppelt; Kunden-Abnahme.
