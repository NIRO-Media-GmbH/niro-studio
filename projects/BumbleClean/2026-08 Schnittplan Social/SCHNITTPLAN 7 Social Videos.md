# BUMBLE CLEAN — Schnittplan: 7 Social-Media-Videos

**Stand:** 08.08.2026 · **Footage:** `/Volumes/NIRO-SSD-02/Bumbleclean/Footage/B-Roll/` · **Ziel:** Kundengewinnung
**Business:** bumble-clean.de · Riemenstraße 13, 74906 Bad Rappenau · IG/TikTok **@bumble.clean** · WhatsApp +49 1551 0015990 · Online-Buchung auf der Website
**Plattformen:** Instagram Reels + TikTok + YouTube Shorts (ein Export für alle drei)
**Kein VO, keine Sprache** — nur B-Roll, Sound-Design, Text-Overlays, Branded Animationen.

> Sichtungshilfe: `Kontaktboegen/` — 20 Kontaktbögen (Kachel-Reihenfolge = alphabetisch, Zuordnung in `kachel-zu-dateiname.txt`, Dauer + fps aller 261 Clips in `clip-inventar-dauer-fps.txt`).

---

## 0. Globale Specs (gelten für alle 7 Videos)

| Thema | Spec |
|---|---|
| Timeline | 1080×1920 (9:16), **25 fps**, DaVinci Resolve |
| Slow-Motion | 100p-Clips → 25 % Tempo (4× slow), 50p → 50 % (2× slow). Immer conformen, nie Optical Flow auf nativen Clips |
| Grade | S-Log3/S-Gamut3.Cine → DaVinci Wide Gamut → Rec.709. Look „Onyx & Honig": tiefes sattes Schwarz, Gold-Akzente warm, Mitten leicht kühl, sanftes Highlight-Rolloff. Ein Grade-Preset für alle 7 → Wiedererkennung |
| Safe-Zones | Oben 200 px frei (Username), unten 320 px (Caption/UI), rechts 120 px (Buttons). Text zwischen 25–60 % Bildhöhe |
| Audio | Musik −14 LUFS integriert, True Peak −1 dB. SFX-Ebene IMMER dabei (auch bei Musik-Videos) — Social ohne SFX wirkt tot |
| Loop | Wo möglich letzte Einstellung visuell an erste anschließen (explizit bei V2 + V4) |
| Kennzeichen | „SHA X 987" ist mehrfach lesbar. Dein Auto, deine Entscheidung — drinlassen wirkt authentisch (SHA ≠ Business-Region Bad Rappenau, liest sich aber als „Kunde kommt von auswärts angereist") oder in Post blurren. Empfehlung: drinlassen |

### CI-Motion-Baukasten (einmal in Fusion bauen, in allen 7 nutzen)

1. **Waben-Wipe** (Signature-Transition): goldene Hexagon-Kacheln fluten das Bild diagonal von unten-links in 8 Frames, dahinter Alpha-Reveal des nächsten Shots. Gold aus dem Logo (`~#C9A24B`, Referenz: `NIRO Studio/tools/motion/public-niro/clients/bumble-clean/logo-4x.png`).
2. **Logo-Stinger** (1,0 s): die 7 Hexagon-Zellen des Logos poppen nacheinander mit Scale-Overshoot ein (je 2 Frames versetzt), Wortmarke „BUMBLE CLEAN – CAR DETAILING" faded darunter ein. Auf Bass-Impact-SFX.
3. **Text-Cards**: Weiß + Gold auf Footage, cleane Sans (Montserrat SemiBold o. CI-Font), kleines Hexagon als Bullet/Nummern-Container. Pop-in 3 Frames mit 5 % Overshoot, immer auf den Beat.
4. **CTA-Endcard** (1,5 s): Logo-Stinger + eine Zeile: `Termin? DM „TERMIN" · Link in Bio`.

### SFX-Einkaufsliste (für den leeren `Assets/SFX`-Ordner)

Whoosh kurz/lang · Bass-Impact (Sub-Drop) · Schaum-Zischen · Wasserstrahl/Hochdruck · Wassertropfen einzeln · Dampf-Fauchen · Polierer-Surren (an/aus) · Klebeband-Abrollen · Schrauber-Klick · Mikrofaser-Wisch · Kamera-Shutter. Quellen: Artlist SFX / Epidemic Sound SFX, Suchwörter englisch (foam hiss, pressure washer, steam burst, drill click, tape rip, whoosh, sub drop).

---

## V1 „DIE VERWANDLUNG" — Before/After · 15 s

**Job im Funnel:** Beweis. Das Video, das Kunden zeigt, WAS sie bekommen.
**Sound:** Trending-Transition-Sound (Glow-up-/Transformation-Trend, Impact bei Sekunde ~6). Fallback: 90 BPM Cinematic Hip-Hop, Suchbegriffe „dark cinematic hip hop confident 90 bpm". Beat = 0,667 s, Vorher-Cuts alle 2 Beats.
**Struktur:** 6 s Misere → Waben-Wipe-Impact → 7 s Glanz → 2 s CTA.

| Zeit | Datei (Ordner) | Inhalt / Regie | Speed | Overlay/Anim |
|---|---|---|---|---|
| 0:00,0–1,3 | `FX3_0432` (Lack Vorher) | Totale: dreckiger Boxster draußen auf staubigem Hof, Dach zu | 100 % | Hook-Text pop: **„So kam er zu uns."** |
| 1,3–2,7 | `FX3_0440` (Lack Vorher) | Macro: verdrecktes Porsche-Wappen | 50 % | — |
| 2,7–4,0 | `FX3_0438` (Lack Vorher) | Macro: staubiger „Boxster"-Schriftzug Heck | 50 % | — |
| 4,0–5,3 | `a7MK4_20260730_0061` (Lack Vorher) | Swirls/Kratzer wandern unter der Inspektionslampe | 100 % | Text: **„Swirls. Staub. 19 Jahre."** |
| 5,3–6,0 | `FX3_0444` (Lack Vorher) | David beugt sich mit Lampe über die Haube | 100 % | — |
| **6,0** | **WABEN-WIPE** | 8 Frames, Gold flutet das Bild | — | Bass-Impact + Whoosh |
| 6,3–8,0 | `a7MK4_20260731_0099` (Lack Nachher) | **Signature-Shot: Hexagon-Wand spiegelt sich im frischen Lack** | 50 % | — |
| 8,0–9,7 | `FX3_0526` (Lack Nachher) | Metallic-Flakes funkeln unter dem Spot | 25 % | — |
| 9,7–11,3 | `FX3_0524` (Lack Nachher) | Front/Radlauf glossy im Studio | 25 % | — |
| 11,3–13,0 | `FX3_0494` (Innenraum Nachher) | Offenes Cockpit von oben, gelb-schwarzer Boden | 25 % | Text: **„Und innen? Auch."** |
| 13,0–15,0 | CTA-Endcard | Logo-Stinger | — | **„Dein Auto kann das auch. → DM ‚TERMIN'"** |

**Caption:** „Basaltschwarz, 2007. Sah nur keiner mehr. Lackkorrektur + Innenraum-Detailing bei BUMBLE CLEAN. Termin per DM oder Online-Buchung (Link in Bio). 📍 Bad Rappenau"
**Hashtags:** #cardetailing #lackkorrektur #porscheboxster #detailingdeutschland #vorhernachher #badrappenau #heilbronn

---

## V2 „FOAM THERAPY" — ASMR/Satisfying · 18 s

**Job im Funnel:** Reichweite. Das Scroll-Stopper-Video — pure Befriedigung, maximales Save/Share-Potenzial.
**Sound:** KEIN Musiktrack. Geschichtetes Original-/SFX-Design: Schaum-Zischen, satter Wasserdruck, einzelne Tropfen, tiefer Roomtone. Alternativ beim Posten: trending ASMR-/Satisfying-Sound drüberlegen (leise, 20 %).
**Schnitt:** langsam, hypnotisch — Cuts alle 2–2,5 s, keine harten Impacts. Alles 100p-Material auf 25 %.

| Zeit | Datei | Inhalt / Regie | Speed | Overlay |
|---|---|---|---|---|
| 0:00,0–2,5 | `FX3_0398` (Waschen) | Schaumlanze feuert die erste Ladung aufs Heck | 25 % | klein: **„🔊 Ton an"** |
| 2,5–5,0 | `FX3_0400` (Waschen) | Porsche-Wappen verschwindet unter dickem Schaum | 25 % | — |
| 5,0–7,5 | `FX3_0403` (Waschen) | Schaumteppich-Struktur macro, langsames Kriechen | 25 % | — |
| 7,5–9,5 | `FX3_0412` (Waschen) | Seitlicher 987-Lufteinlass, Schaum tropft ab | 25 % | — |
| 9,5–11,5 | `FX3_0409` (Waschen) | Scheinwerfer unter Schaum | 100 % (25p) | — |
| 11,5–13,5 | `FX3_0417` (Waschen) | Hochdruck spült von oben, Schaum reißt auf | 50 % | — |
| 13,5–15,5 | `FX3_0419` (Waschen) | Endrohre im Wassernebel, Gegenlicht | 25 % | — |
| 15,5–17,0 | `FX3_0420` (Waschen) | „Boxster S"-Schriftzug mit Wasserperlen | 50 % | — |
| 17,0–18,0 | Mini-Logo (dezent, 60 % Größe) | ohne CTA-Text — Caption trägt den CTA | — | — |

**Loop-Trick:** Letzter Wasserperlen-Shot dunkel auslaufen lassen → erster Frame (dunkles Heck) schließt nahtlos an.
**Caption:** „Therapie gefällig? 🧖 Snow Foam auf Basaltschwarz. Termine: DM ‚TERMIN' / Link in Bio."
**Hashtags:** #asmr #satisfying #snowfoam #carwash #detailing #oddlysatisfying #porsche

---

## V3 „EIN GANZER TAG IN 18 SEKUNDEN" — Prozess-Rush · 18,5 s

**Job im Funnel:** Kompetenz + Preis-Rechtfertigung. Zeigt den ECHTEN Umfang eines Detailing-Tags — inkl. deiner 3 echten Timelapses.
**Sound:** 128 BPM Drum'n'Bass-light/Electronic treibend („energetic electronic build 128 bpm"). Beat = 0,469 s. **Jeder Cut exakt auf den Beat.** Uhrzeit-Overlays erzählen den Tag.

| Zeit (Beats) | Datei | Inhalt | Speed | Overlay |
|---|---|---|---|---|
| 0,0–0,9 (2) | `FX3_0443` (Reinfahren) | Tracking: Wagen rollt Richtung Halle | 200 % | **„07:30"** |
| 0,9–1,4 (1) | `FX3_0374` (Waschen) | Sprühflasche trifft Felge | 100 % | **„Felgen"** klein |
| 1,4–1,9 (1) | `FX3_0376` (Waschen) | Roter PORSCHE-Sattel durch Speichen | 100 % | — |
| 1,9–2,3 (1) | `FX3_0383` (Waschen) | Felgenbürste arbeitet | 100 % | — |
| 2,3–3,3 (2) | `FX3_0398` (Waschen) | Schaumlanze feuert | 50 % | **„09:00"** |
| 3,3–3,8 (1) | `FX3_0402` (Waschen) | Haube unter Schaumdecke | 100 % | — |
| 3,8–4,2 (1) | `FX3_0414` (Waschen) | Waschhandschuh zieht Bahn | 100 % | — |
| 4,2–4,7 (1) | `FX3_0418` (Waschen) | Abspülen von oben | 100 % | — |
| 4,7–5,2 (1) | `FX3_0424` (Waschen) | Trockentuch über Scheibe | 100 % | — |
| 5,2–6,1 (2) | `FX3_0515` (Kennzeichen) | Hände clipsen Front-Kennzeichen ab | 100 % | **„11:15"** |
| 6,1–6,6 (1) | `FX3_0516` (Kennzeichen) | Schrauber-Macro | 100 % | — |
| 6,6–7,5 (2) | `FX3_0488` (Abkleben) | Gelbes Tape entlang der Scheibenleiste | 150 % | **„Abkleben"** |
| 7,5–8,0 (1) | `FX3_0489` (Abkleben) | Tape-Kante Tür | 100 % | — |
| 8,0–8,9 (2) | `a7MK4_20260731_0090` (Entfetten) | Wisch über die Haube, Wappen im Bild | 150 % | **„Entfetten"** |
| 8,9–10,8 (4) | `FX3_0521` (Politurstufe 1) | **TIMELAPSE: komplette Politur-Session** | 300 % | **„13:00 — Politur"** |
| 10,8–11,3 (1) | `FX3_0531` (Politurstufe 1) | Polierer-Macro blauer Pad | 100 % | — |
| 11,3–11,7 (1) | `a7MK4_20260730_0050` (Ber. Polieren) | Mikrofaser wischt Politur ab — Glanz darunter | 100 % | — |
| 11,7–13,6 (4) | `FX3_0485` (Innenraum) | **TIMELAPSE: 63 min Innenraum/Matten-Station** | 400 % | **„16:00 — Innenraum"** |
| 13,6–14,1 (1) | `a7MK4_20260730_0085` (Innenraum) | Dampf faucht um Schaltknauf | 100 % | — |
| 14,1–14,5 (1) | `FX3_0480` (Innenraum) | Sprühextraktion auf Matte | 100 % | — |
| 14,5–15,5 (2) | `FX3_0526` (Lack Nachher) | Metallic funkelt | 25 % | **„18:30"** |
| 15,5–16,4 (2) | `a7MK4_20260730_0071` (Lack Vorher*) | Front mit Kennzeichen im Studio — fertig & stolz (*Clip liegt im Vorher-Ordner, zeigt aber den Studio-Stand) | 50 % | — |
| 16,4–18,5 | CTA-Endcard | Logo-Stinger | — | **„1 Tag. 1 Ergebnis. → DM"** |

**Caption:** „Was in einem Detailing-Tag wirklich passiert — 11 Stunden in 18 Sekunden. Genau deshalb dauert gut. Termine: Link in Bio."
**Hashtags:** #detailing #prozess #timelapse #cardetailingdeutschland #handwerk #porsche987

---

## V4 „BLACK MIRROR" — Carporn pur · 16 s

**Job im Funnel:** Premium-Positionierung. Kein Prozess, keine Erklärung — nur Ergebnis. Für die Zielgruppe, die ihr Auto liebt.
**Sound:** 70 BPM Dark Ambient / Cinematic („dark luxury cinematic 70 bpm slow"). Lange Shots, Speed-Ramps statt Schnitte. SFX: tiefer Sub-Puls auf jedem Shot-Wechsel.

| Zeit | Datei | Inhalt / Regie | Speed | Overlay |
|---|---|---|---|---|
| 0:00,0–2,0 | `a7MK4_20260730_0044` + `_0045` (Allgemein) | Felgen durch die Lamellenwand — Vordergrund verdeckt, mystisch | 50 % | Hook: **„Basaltschwarz. Frisch korrigiert."** |
| 2,0–4,5 | `FX3_0526` (Lack Nachher) | Metallic-Flakes im Spot, langsamer Drift | 25 % | — |
| 4,5–7,0 | `a7MK4_20260731_0099` (Lack Nachher) | Hexagon-Wand wandert als Spiegelung durch den Lack | 50 % | — |
| 7,0–9,0 | `FX3_0525` (Lack Nachher) | Lackkurve, Highlight-Kante läuft | 25 % | — |
| 9,0–11,0 | `FX3_0536` (Politurstufe 1) | Heck-3/4, rote Sättel glühen unter weißen Felgen | 25 % | — |
| 11,0–12,5 | `FX3_0498` (Innenraum Nachher) | Lenkrad-Wappen macro | 25 % | — |
| 12,5–14,0 | `FX3_0501` (Innenraum Nachher) | Schaltknauf macro, Schaltschema scharf | 25 % | — |
| 14,0–14,5 | `FX3_0528` (Lack Nachher) | Funkel-Peak als Blitz | 25 % | Shutter-SFX |
| 14,5–16,0 | Logo-Stinger auf Schwarz | — | — | dezent: **„BUMBLE CLEAN"** |

**Loop-Trick:** Start und Ende sind fast schwarz — läuft endlos.
**Caption:** „Kein Filter. Nur Politur. #basaltschwarz" (bewusst kurz — das Video IST die Aussage)
**Hashtags:** #carporn #porscheboxster #987 #blackcar #paintcorrection #detailing

---

## V5 „INTERIOR RESET" — Innenraum-Deep-Clean · 17 s

**Job im Funnel:** Zielgruppen-Erweiterung. Spricht auch Alltagsautos, Familienkutschen, Leasing-Rückgaben an — dein größter Markt.
**Sound:** 100 BPM Clean/Minimal House („minimal house clean 100 bpm"). Beat = 0,6 s, Cuts alle 2–3 Beats. SFX: Sauger, Bürste, Dampf, Sprühstoß.

| Zeit | Datei | Inhalt | Speed | Overlay |
|---|---|---|---|---|
| 0:00,0–1,5 | `FX3_0464` (Innenraum) | Macro: PORSCHE-Fußmatte, Staub sichtbar | 50 % | Hook: **„Der Ort, den jeder vergisst."** |
| 1,5–3,0 | `FX3_0459` (Innenraum, Ausschnitt) | Fugendüse saugt Sitzritze | 50 % | — |
| 3,0–4,5 | `FX3_0461` (Innenraum, Ausschnitt) | Konsole/Schalttasche wird ausgesaugt | 50 % | — |
| 4,5–6,0 | `FX3_0473` (Innenraum) | Orbital-Bürste arbeitet auf der Matte | 50 % | — |
| 6,0–7,5 | `FX3_0480` (Innenraum) | Sprühextraktions-Düse macro, Schmutzwasser | 50 % | — |
| 7,5–9,0 | `a7MK4_20260730_0079` (Innenraum) | **50/50-Matte: sauberer Streifen neben Schmutz** | 100 % | Text: **„Sichtbar? Sichtbar."** |
| 9,0–10,5 | `a7MK4_20260730_0085` (Innenraum, Ausschnitt) | Dampf faucht um den Schaltknauf | 50 % | — |
| 10,5–12,0 | `FX3_0485` (Innenraum, Ausschnitt) | Timelapse Matten-Station | 150 % | — |
| 12,0–13,5 | `FX3_0494` (Innenraum Nachher) | Cockpit von oben — offen, sauber, fertig | 25 % | Text: **„Reset."** |
| 13,5–15,0 | `FX3_0499` (Innenraum Nachher) | Schaltknauf clean macro | 25 % | — |
| 15,0–17,0 | CTA-Endcard | Logo-Stinger | — | **„Innenaufbereitung ab 119 € → DM ‚TERMIN'"** |

**Caption:** „Innenraum-Detailing: Absaugen, Bürsten, Sprühextraktion, Dampf. Auch ohne Porsche. 😉 Innenaufbereitung ab 119 €, innen + außen ab 179 €. Leasing-Rückgabe? Meld dich rechtzeitig → Online-Buchung, Link in Bio. 📍 Bad Rappenau"
**Hashtags:** #innenraumreinigung #interiordetailing #leasingrückgabe #autopflege #detailing #badrappenau

---

## V6 „LACKKORREKTUR IN 4 SCHRITTEN" — Education · 20 s

**Job im Funnel:** Vertrauen + Abgrenzung von jeder Waschanlage. Erklärt ohne ein gesprochenes Wort, warum das ein Handwerk ist.
**Sound:** 85 BPM ruhig/seriös („minimal tech documentary 85 bpm"). Beat = 0,706 s. Kapitel-Cards mit Hexagon-Nummer poppen auf den Downbeat, Tape-/Polierer-SFX real.

| Zeit | Card | Datei | Inhalt | Speed |
|---|---|---|---|---|
| 0:00,0–2,0 | HOOK | `a7MK4_20260730_0061` (Lack Vorher) | Swirls wandern unter der Lampe | 100 % — Text: **„Jeder schwarze Lack hat sie: Swirls."** |
| 2,0–4,0 | **⬡ 01 ABKLEBEN** | `FX3_0488` (Abkleben) | Gelbes Tape entlang Scheibenleiste | 150 % |
| 4,0–6,0 | ⬡ 01 | `FX3_0490` (Abkleben) | Tape-Rolle + Türkante, Hexagon-Spiegelung | 100 % |
| 6,0–8,0 | **⬡ 02 ENTFETTEN** | `a7MK4_20260731_0090` (Entfetten) | Wisch über Haube, Wappen im Bild | 100 % |
| 8,0–10,0 | ⬡ 02 | `a7MK4_20260731_0091` (Entfetten) | Scheinwerfer-Wisch, Waben spiegeln sich | 100 % |
| 10,0–12,0 | **⬡ 03 POLIEREN** | `FX3_0448` (Ber. Polieren) | **Test-Spot im gelben Tape-Rahmen** — Maschine arbeitet im Feld | 100 % |
| 12,0–13,5 | ⬡ 03 | `a7MK4_20260731_0096` (Ber. Polieren) | Polierer-Macro, Maschine spiegelt sich im korrigierten Lack | 50 % |
| 13,5–15,0 | ⬡ 03 | `a7MK4_20260730_0050` (Ber. Polieren) | Mikrofaser nimmt Politur ab — Reveal | 100 % |
| 15,0–16,5 | **⬡ 04 FINISH** | `FX3_0526` (Lack Nachher) | Metallic-Funkeln | 25 % |
| 16,5–18,0 | ⬡ 04 | `a7MK4_20260731_0099` (Lack Nachher) | Hexagon-Spiegelung im Lack | 50 % |
| 18,0–20,0 | OUTRO | Text-Card + Logo-Stinger | **„Das ist der Unterschied zwischen Waschen und Aufbereiten."** + kleiner: „Komplett + Politur · ab 349 €" | — |

**Caption:** „Lackkorrektur ≠ Polieren ab Baumarkt. Abkleben → Entfetten → maschinell korrigieren → versiegeln. Im Komplettpaket ab 349 €. Fragen? DM offen. 📍 Bad Rappenau"
**Hashtags:** #lackkorrektur #paintcorrection #detailingwissen #swirls #autoaufbereitung #heilbronn

---

## V7 „DELIVERY DAY" — Emotional + härtester CTA · 15 s

**Job im Funnel:** Abschluss/Conversion. Das Gefühl: „Dein Auto kommt besser zurück, als es je war." Kennzeichen-Demontage-Clips **rückwärts** = Montage, letzte Handgriffe, Übergabe-Stimmung.
**Sound:** 95 BPM warm & aufbauend („uplifting warm cinematic build 95 bpm"), Finale öffnet sich. SFX: Schrauber-Klick, letzter Wisch, Sub-Impact auf Endcard.

| Zeit | Datei | Inhalt / Regie | Speed | Overlay |
|---|---|---|---|---|
| 0:00,0–1,5 | `FX3_0517` **REVERSE** (Kennzeichen) | Kennzeichen wird „angeclipst", Low Angle Front | 100 % | Hook: **„Letzter Schritt."** |
| 1,5–3,5 | `FX3_0516` **REVERSE** (Kennzeichen) | Schrauber-Macro, Handschuhe | 100 % | — |
| 3,5–5,0 | `FX3_0513` **REVERSE** (Kennzeichen) | Heck: Halter + Endrohre im Bild | 100 % | — |
| 5,0–6,5 | `a7MK4_20260731_0093` (Entfetten) | Letzter Wisch über Radlauf/Felge | 50 % | — |
| 6,5–8,0 | `FX3_0525` (Lack Nachher) | Lackkurve-Macro, makellos glänzend | 25 % | — |
| 8,0–10,0 | `FX3_0494` (Innenraum Nachher) | Offenes Cockpit von oben | 25 % | Text: **„Bereit."** |
| 10,0–12,5 | `a7MK4_20260730_0071` → `_0070` (Lack Vorher*) | Front mit Kennzeichen im Studio, langsamer Push (*Studio-Stand trotz Ordnername) | 50 % | — |
| 12,5–15,0 | CTA-Endcard (länger als sonst) | Logo-Stinger | — | **„Dein Termin: DM ‚TERMIN' oder Link in Bio."** |

**Caption:** „Abholbereit. Wenn du dein Auto beim Abholen zweimal anschaust, haben wir alles richtig gemacht. Termine für [Monat] offen → DM ‚TERMIN', WhatsApp oder Online-Buchung (Link in Bio). 📍 Bad Rappenau"
**Hashtags:** #cardetailing #deliveryday #porscheboxster #autoaufbereitung #badrappenau #heilbronn

---

## Posting-Plan & Systematik

**Reihenfolge (2 Videos/Woche, ~3,5 Wochen Content):**
1. **V1 Verwandlung** — stärkster Erstkontakt, etabliert die Marke
2. **V2 Foam Therapy** — Reichweiten-Push hinterher
3. **V6 Lackkorrektur** — Kompetenz festigen
4. **V5 Interior Reset** — Zielgruppe verbreitern
5. **V3 Ein Tag** — Preis-Anker („so viel Arbeit steckt drin")
6. **V4 Black Mirror** — Premium-Image
7. **V7 Delivery Day** — Conversion-Abschluss der Serie

Beste Zeiten DACH: Di–Do 17–20 Uhr, So 10–12 Uhr. Erste 30 min auf Kommentare antworten (Algorithmus). Jedes Video zusätzlich als Story mit Link-Sticker.

**Trending-Sound-Regel:** V1 + V2 beim Posten in der App prüfen, ob ein passender Trend-Sound im gleichen Tempo läuft (V1: Transformation-Sounds, V2: ASMR-Sounds). Der Schnitt ist auf BPM-Raster gebaut — Sound gleichen Tempos drüberlegen funktioniert ohne Neuschnitt.

**Export:** H.264, 1080×1920, 25 fps, ~20 Mbit/s, Rec.709-A Tag (QuickTime), Audio AAC 320 kbit/s. Ein Master → alle drei Plattformen nativ hochladen (nie TikTok-Wasserzeichen recyceln).

---

## Offene Punkte für dich

1. ~~Ort/Region~~ ✅ von bumble-clean.de übernommen: **Bad Rappenau** (Captions + Hashtags angepasst).
2. ~~Preis-Nennung~~ ✅ eingebaut: V5-Endcard „Innenaufbereitung ab 119 €" (weiterhin belegt), V6-Outro „Komplett + Politur · ab 349 €". **Website-Update 29.08.2026:** „Einstufige Politur ab 199 €" existiert nicht mehr, neuer Claim „Showroom-Finish. Ohne Kompromisse." — das bereits gerenderte V1 zeigt noch „AB 199 €" (siehe Protokoll).
3. ~~Buchungslink~~ ✅ Online-Buchung auf bumble-clean.de → „Link in Bio" zeigt auf die Buchungsseite.
4. `Assets/Musik` + `Assets/SFX` befüllen — Suchbegriffe stehen bei jedem Video bzw. in der SFX-Liste.
5. In V7-Caption **[Monat]** beim Posten einsetzen.
