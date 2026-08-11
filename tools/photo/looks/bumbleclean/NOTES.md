# BumbleClean — Look „Ultraclean Dramatic" (v5, aktiv)

**v5 (aktiv, Runde 3 „mehr Punch"):** `ultraclean_v5.png`. Kern-Neuerung:
Luma-selektive MITTELTÖNE-SENKE (C 0.32, W 0.14, A 0.13) — dunkelt Umgebung
(Boden/Wände) ab, schont schwarzen Lack (tiefer) und Reflexe (heller) →
Spotlight-Drama ohne v3-Fehler. Dazu: Gelb-Sättigung −42 %, Schwarzpunkt 2.5 %,
S-Kurve 3.2×47 %, Vignette 80 %, Clarity 0.24. Anker-Faktoren nach Senke:
02→1.25, 03→1.15, 10→1.0, 13→0.75 (Fronten/Leder liegen im Senken-Bereich und
brauchen Ausgleich).

## Historie

Datei: `ultraclean_v4.png` (HALD-12-CLUT, 16 bit). Erstellt 2026-08-03 für das
Boxster-Shooting (A7 IV + Sigma 24-70 2.8, Detailing-Halle Bad Rappenau).
`ultraclean_v3.png` = verworfene Erstfassung (Davids Feedback: zu dunkel,
unprofessionell — Mitten global abgesenkt statt Auto brillant zu halten).
v4: Mitten-Gamma 1.0 (statt 0.92), S-Kurve 2.6×47 % (statt 3.4×44 %),
Sättigung 95, Hue-Trim 98.9, Grün-Dämpfung 0.65, Highlight-Stretch 97.5 %,
Vignette nur noch 93 %. Belichtung wird seitdem pro Bild auf einer
LACK-ANKERREGION normalisiert (develop_batch.sh, Referenz-Anker 2980 = 0.1355),
nicht mehr auf Gesamtbild-Mean — sonst schwankt die Auto-Helligkeit mit dem
Bildausschnitt (Runde-1-Fehler, Faktor 6 Streuung; nach Fix < 2, motivbedingt).

## Zielbild (aus Davids Referenzen abgeleitet)

Drei Referenzen in `projects/BumbleClean/Fotos Boxster/Beispielfotos/`:
Low-Key-Studio schwarz (Stock), silbernes Hypercar in dunkler Garage, türkiser
McLaren in grauer Halle. Gemeinsame DNA: dunkle, entsättigte, kühle Umgebung;
Lack als brillanter Held mit sauberen Reflexkanten; tiefe Schwarzwerte,
kontrollierte Highlights; reduzierte Palette mit einzelnen Farbakzenten.
Davids Vorgabe: „ultraclean, darf etwas dramatisch sein, Fokus auf Auto und Lack".

## Was der Look tut

- Gelb des Schachbrettbodens → gedämpftes Gold (Hue 0.155 ±0.055: Sättigung
  −30 %, Helligkeit −26 %, Hue −0.032 Richtung Orange) — CI bleibt, schreit nicht.
- Grün (Tageslicht-Mischlicht durch Fenster) entsättigt (Hue 0.34 ±0.10, −50 %).
- Schwarzpunkt 1.8 %, Mitteltöne-Gamma 0.92, S-Kurve 3.4×44 % → satte Tiefen.
- Global: Sättigung 92 %, Hue-Trim 99.3 (gegen Rest-Grün), Blau-Gamma 1.04
  (kühle Schatten).
- NICHT in der LUT (bildabhängig, macht develop_batch.sh): Auto-Gain
  (Ziel-Luma 0.26, Klemme 0.85–2.1), Clarity-USM (Sigma = lange Kante/73,
  Stärke 0.13), Vignette (Rand 85 %).

## Anwendung

    develop_batch.sh looks/bumbleclean/ultraclean_v3.png <work> <out> 01:2980 …

Härtetest-Referenzbilder der Kalibrierung: _A7_2980 (Hero hell), _A7_2977
(Ganzaufnahme knapp belichtet, Mischlicht), _A7_2997 (Interieur dunkel).
