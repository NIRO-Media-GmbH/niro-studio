# Protokoll — Dold Holzwerke · Recruiting · Charge 2026-07 Dreh 27-28.07

## 2026-08-13 — Schnittplan Reels R01–R26

**Auftrag:** Schnittanweisungen für die Werbeanzeigen (Reels). Langformate kommen
in einen separaten zweiten Schnittplan. **Baggerfahrer (R06) hat Prio 1** und steht
deshalb als Video 01 vorne, zusätzlich als Warnbox auf dem Deckblatt.

**Gemacht**

- Alle 13 FX3-Interviews mit Scribe transkribiert (Diarisierung, Wort-Timings),
  Cache unter `_intern/cache/`. a7MK4 nur als Kontext-Kamera, nie als Tonquelle.
- Wer-ist-wer geklärt: mehrere Ordnernamen weichen vom echten Namen ab
  (`Interview_Ahmet_` = **Waquar Ahmed**, `Interview_Gnaju_Schleiferei` =
  **Ignacio Curia**, Bereich ist die **Schärferei**, `Sebastion` = **Sebastian Tost**).
- Konzept-/Materialabdeckung geprüft → `Ergebnisse/O-Ton-Pläne/00-analyse-abdeckung.md`
  (nicht Teil des PDFs).
- 26 Reel-Kapitel gebaut, jedes Zitat wortgenau gegen das Transkript verifiziert
  (`_intern/zitat_timecode.py`).
- PDF gerendert: `Ergebnisse/O-Ton-Pläne/Dold-Schnittanweisungen-Reels.pdf`,
  56 Seiten = Deckblatt + 1 Übersichtsseite + 26 × 2 Seiten + 2 Seiten Anhang.
  Seitenbudget mit pypdf geprüft, kein Kapitel über 2 Seiten.

**Geliefert**

- `Ergebnisse/O-Ton-Pläne/Dold-Schnittanweisungen-Reels.pdf`
- `01-projekt-grundlagen.md` (Übersicht) · `video-01…26-*.md` · `99-anhang-personen-und-sperren.md`
- `_intern/pdf_meta.json`

**Entscheidungen**

- Reihenfolge nach Priorität, nicht nach Reel-Nummer: 01=R06 (Prio 1), 02=R24,
  03=R03, 04=R05, 05=R14, 06=R15, 07=R07, 08=R04, 09=R16, 10=R17, 11=R19, 12=R23,
  13=R09, 14=R10, 15=R11, 16=R12, 17=R13, 18=R08, 19=R20, 20=R21, 21=R25, 22=R26,
  23=R18, 24=R22, 25=R01, 26=R02.
- **Ersatzbesetzungen** für nie gedrehte Personen: R07 „Spiesla" → Kai · R04 Felix
  Molitor/Alessandro D. → Sebastian Tost · R17 Matthias Trautz → David Ruch ·
  R08 Alexandra → Vier-Männer-Fassung · R01 Konrad Fehrenbach → Interimsfassung
  ohne O-Ton · R02 Bruno → Streichkandidat bzw. Kurzfassung von R23.
- **R26** (Biomasseheizkraftwerk) steht unter Freigabevorbehalt und wird ohne
  Kundenfreigabe nicht produziert.
- **Kannibalisierungs-Cluster** in jedem Kapitel vermerkt: „Nicht nur eine Säge"
  R04/R11/R16 · Sicherheit R09/R10/R12 · Bioenergie R21/R25/R26 · Maschinen ohne
  Menschen R11/R18/R22 · Rundholzplatz R06/R24/R18. Jeweils **max. zwei parallel**.

**Offen / an Dold**

- Endcard-Wortlaut und Bewerbungs-URL.
- Zahlen-Konflikte: 140 vs. 137 Jahre · 80.000 vs. 53.000 m²/Monat · 60 % vs.
  2,2 MW · 75.000 vs. 70.000 t Pellets · 25.000 Menschen vs. 3.000 Haushalte.
- Freigabe Biomasseheizkraftwerk (entscheidet über R26 und Maschine 9 in R22).
- Nachnamen Dominik / Lars / Kai · persönliche Freigabe Thomas Frey für die
  Notfall-Passage (Video 18, Szene 4) · persönliche Zustimmung Waquar Ahmed zum
  O-Ton mit Sprachfehlern (Video 21).
- **Nachdrehe:** Sägewerk (Spanerlinie/Gatter), Trocknung, Entrinden, CNC ·
  Interview mit einem Industriemechaniker · Interview mit einem Staplerfahrer ·
  **Interview mit mindestens einer Mitarbeiterin** (im Material kommt keine Frau vor).

**Als Nächstes:** zweiter Schnittplan für die Langformate (Imagefilm, Werksporträts,
GF-Interview). Abdorrahman (FX3_0343) ist in keinem Reel verplant und dort Reserve.

## 2026-08-20 — Animation: Recruiting-Endcard (Logo + CTA)

**Auftrag:** Einfache Logo-Animation als Endcard für die Reels, ~10 s, Logo groß
in der Safe Zone (liegt im Schnitt über einem unscharf gestellten Drohnenshot),
CTA „Jetzt in unter 1 Minute bewerben". Muss hinten kürzbar sein.

**Gemacht**

- Neuen Motion-Client `dold` angelegt, CI von dold-holzwerke.com abgeleitet:
  Markengrün `#00694D`, Roboto, Akzentgelb `#F6EA5E` (vom „Wir stellen ein"-Badge).
  Logo-SVGs (grün + weiß generiert) unter `tools/motion/public/clients/dold/`.
- Komposition `Dold-Endcard` + `Dold-Endcard-Transparent` (1080×1920 @ 30 fps, 10 s),
  auf Wunsch bewusst simpel: Logo blendet als Ganzes weich ein (ab 0,13 s), Slogan
  „INNOVATION IN HOLZ" direkt hinterher, dann Job-Ansage „Wir suchen /
  BAGGERFAHRER (m/w/d)", CTA-Pille (weiß, grüne Schrift) ab ~0,93 s,
  Website-Zeile ab ~1,3 s. Nach ~2,2 s steht alles statisch → hinten beliebig
  kürzbar, kein Outro. (Erste Fassung mit Balken-Wipes/Buchstaben-Stagger und
  später CTA in der Abnahme verworfen — zu verspielt, Pille zu spät.)
- Job-Ansage als Props (`jobEyebrow`/`jobTitle`/`jobSuffix`), damit dieselbe
  Komposition die Endcards der übrigen Reels mit anderer Rolle liefern kann;
  `jobTitle` leer = Block wird nicht gerendert.
- Gesamtes Layout innerhalb der IG-Reels-Safe-Zone (oben 7–57,5 %), untere
  Bildhälfte bleibt frei für Drohnenshot + IG-UI. Mit Safe-Zone-Guides und als
  Alpha-Still geprüft: `tools/motion/_review/still-dold-*.png`.

**Geliefert**

- `Ergebnisse/Renders/Dold-Recruiting-Endcard_1080x1920_ProRes4444-Alpha.mov`
  (10,0 s, ProRes 4444 mit Alpha, 143,9 MB, inkl. Baggerfahrer-Ansage — als
  Overlay über den unscharfen Drohnenshot legen)
- Preview/Feinjustage: `http://localhost:3111/Dold-Endcard`

**Entscheidungen**

- Gestapeltes Lockup (Marke groß, Slogan darunter) statt der horizontalen
  Original-Anordnung — passt besser ins Hochformat; Slogan per `showSlogan` abschaltbar.
- **Optischer Versatz der Marke: `markShiftX` +30 px** (bei 660er Logo-Breite),
  per Sichtvergleich 0/+10…+50 abgenommen — die Schräglage lässt die Box-zentrierte
  Marke links wirken; reine Box-/Massen-Zentrierung greift hier nicht.
- Logo weiß als Default (auf Footage), per `logoColor` auf grün umstellbar;
  CTA-Pille per `ctaStyle` weiß/grün.
- Website-Zeile: `dold-holzwerke.com` — die Bewerbungs-URL ist laut Kunde noch
  offen (`/karriere` liefert aktuell 404); per Prop `website` änderbar oder leerbar.

**Offen**

- Endgültiger CTA-Wortlaut / Bewerbungs-URL vom Kunden (siehe 2026-08-13) —
  bei Änderung Props anpassen und neu rendern.

## 2026-09-01 — Migration ins Studio-Hauptsystem

**Gemacht:** Charge vom Zweit-MacBook übernommen; Kunde neu angelegt als
`projects/Dold` (Kurzname nach Studio-Konvention, vorher „Dold Holzwerke").
`_intern/__pycache__` entfernt, Inhalte sonst unverändert.

## 2026-09-01 — Reels-Schnittplan R01–R26 komplett neu gebaut

**Auftrag:** Gesamter Schnittplan für alle Ads neu (Plan vom 13.08. kam bei
der Migration nicht mit — `Ergebnisse/O-Ton-Pläne/` war leer), Konzepte
erneut prüfen.

**Gemacht**

- Konzeptprüfung Sheets 1–4: Reel-Sheet (Sheet3) unverändert; **Sheet4 (neu
  eingegangen 01.09.) = Re-Export der Langformat-Leitfäden 1–7** — betrifft
  die Reels nicht; GF-Heizkraftwerk-Fragen dort gestrichen (bestätigt Sperre).
  Ersatzbesetzungs-Entscheide vom 13.08. übernommen.
- Alle 18 FX3-Ton-Transkripte als lesbare Dumps nach `_intern/work/`
  exportiert und komplett durchgearbeitet; Wer-ist-wer gegen die
  Selbstvorstellungen verifiziert (Waquar Ahmed, Ignacio Curia, Abdorrahman,
  Kevin „Ringers"?; Nachnamen Dominik/Kai/Lars weiter offen).
- **Zahlen-Konflikte im O-Ton verortet:** 140 (Nikolaus 2x) vs. 137 (Bernd) ·
  53.000 m2/„7–8 Fußballfelder" (Nikolaus) vs. 80.000 m2 (Bernd) · 70.000 t
  (Waquar) vs. 75.000 t „angepeilt" (Kevin) · „60 %" (Kevin) und „2,2 MW/80 %"
  (Nikolaus) betreffen beide das NEUE HKW → gesperrt · Kevins „25.000 Menschen"
  ist Wärme, nicht Strom · Rundholz-Radius laut GF „80–100 km" (Konzeptfrage
  60/80 damit beantwortet). Details in `00-analyse-abdeckung.md`.
- 26 Kapitel neu geschrieben (Prio-Reihenfolge wie 13.08., 01=R06 Bagger …
  26=R02), je max. 2 PDF-Seiten, dreiteilige Quellen, Kommentar-Spalte,
  Kannibalisierungs-Cluster vermerkt. Übersichtsseite + Anhang
  (Personen/Sperren/Nachdreh) neu.
- **Alle 94 Zitate wortgenau gegen den Scribe-Cache verifiziert** — neues
  Batch-Skript `_intern/verify_zitate.py` (Füller-tolerant, prüft Wortlaut +
  Zeitfenster + […]‑Reihenfolge); 11 anfängliche Glättungen auf den exakten
  Wortlaut korrigiert, Endstand 0 Fehler.
- Sperrliste erweitert (gegenüber 13.08. neu): Lars' Frauen-Passage (1. Fassung),
  Kevins „geiler Typ"-CTA + Ex-Kollege-Schicht-Story + „alles uralt", Davids
  Lagerordnungs-/Deutschkurs-/Arbeitszeitbetrug-Passagen, Sebastians
  Ausbildungs-Interna, Ignacios soufflierte 140-Jahre-Passage, soufflierte
  Benefits-Aufzählungen, „32 Tage Urlaub" (vorgesagt), „Gelände 10.000 m2"
  (Versprecher).

**Geliefert**

- `Ergebnisse/O-Ton-Pläne/Dold-Schnittanweisungen-Reels.pdf` — 47 Seiten =
  Deckblatt + 1 Übersicht + 26 Kapitel + 2 Seiten Anhang; Seitenbudget mit
  pypdf geprüft, kein Kapitel über 2 Seiten.
- `01-projekt-grundlagen.md` · `video-01…26-*.md` · `99-anhang-personen-und-sperren.md` ·
  `00-analyse-abdeckung.md` (intern) · `_intern/verify_zitate.py`.
- Nachtrag gleiche Session: `00-sperrliste-detail.md` (alle Sperren mit vollem
  Wortlaut, Kontext und Begründung); dabei eine Sperre ergänzt — Davids
  „Alles gestumpen und erlogen"-Ironie (FX3_0188 · 11:25, direkt hinter dem
  verplanten Feedback-Take). Anhang + PDF entsprechend aktualisiert (47 Seiten, Budget ok).

**Entscheidungen**

- Keine separaten Dossier-Langfassungen (wie Lieferung 13.08. — bei 26 kurzen
  Reels ist die Kompaktfassung der Plan; Alternativen-Blöcke ersetzen das Dossier).
- Video 22 (R26) bleibt komplett unter Freigabevorbehalt; Video 25/26 als
  Interim-/Kurzfassungen gekennzeichnet [NACHDREH].
- Bernds Kurzarbeit-Take wird erst NACH der strittigen „137" geschnitten
  („…haben wir noch keinen einzigen Tag Kurzarbeit gehabt und noch jeden Monat
  ist Geld gekommen") — so nutzbar trotz Zahlen-Konflikt.

**Offen / an Dold** (unverändert + präzisiert)

- Endcard-Wortlaut + Bewerbungs-URL (dold-holzwerke.com/karriere weiter 404).
- Zahlen bestätigen: 140 vs. 137 Jahre · Platten-m2/Monat · Pellets-Tonnen ·
  Strom-Haushalte · 32 Urlaubstage · Spreißel-Claim-Wortlaut.
- Freigaben: neues Heizkraftwerk (→ Video 22 + Kessel in 24) · Thomas Frey
  (Notfall-Passage, Video 18) · Waquar Ahmed (O-Töne, Video 21).
- Nachnamen Dominik / Kai / Lars („Loyal"?) / Kevin („Ringers"?).
- Nachdrehe: Sägewerk innen, Trocknung, Entrinden, CNC, Industriemechaniker-
  und Staplerfahrer-Interview, mindestens eine Mitarbeiterin.

**Als Nächstes:** zweiter Schnittplan für die Langformate (Leitfäden liegen
aktuell in Sheet4); Abdorrahman bleibt Reserve.
