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

## 2026-09-01 — Migration ins Studio-Hauptsystem

**Gemacht:** Charge vom Zweit-MacBook übernommen und unter
`projects/Craiss/4 Ads/` eingegliedert — liegt jetzt neben der Charge
„2026-08 Dreh" (O-Ton-Pläne/Schnittanweisungen zu denselben 5 Videos).
Inhalte unverändert.
