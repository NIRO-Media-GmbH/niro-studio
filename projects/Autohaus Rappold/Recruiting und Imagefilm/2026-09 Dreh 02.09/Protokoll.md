# Protokoll — Autohaus Rappold · Recruiting und Imagefilm · 2026-09 Dreh 02.09

## Session 14.09.2026 — Schnittplan (Funktion „Schnittplan:")

**Gemacht**
- Charge angelegt; Konzept-PDF aus `projects/` nach `Material/Konzept/` verschoben (4 Videos: Serviceberater, Kfz-Mechatroniker, Schlüsselbox 22:47, Einmal durch Rappold).
- Material auf dem NAS: `NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/Autohaus Rappold GmbH/02_Projekte/01_Dreh_2026.09 Image & Ads, Schlüsselbox/03_Medien/01_Footage/` (team-vorsortiert: Interviews/<Name - Beruf>, Schlüsselbox Carlo, B-Roll, Drohne). Originale nur gelesen.
- Ton-Kamera beim User erfragt: **FX3**. Beide Kameras transkribiert (15 Clips, 3 h 49 min, `_intern/transcribe_rappold.py`, drei Worker parallel).
- Website `autohaus-rappold.de` gesichert (`_intern/website/`) und gegen Konzept-Claims geprüft.
- B-Roll/Drohne per Kontaktbogen gesichtet (`_intern/contact_sheets.py` → `_intern/sichtung/`), Technik-Inventar (`_intern/probe_footage.py`), Personen per Standbild abgeglichen.
- Analyse `Ergebnisse/O-Ton-Pläne/00-material-und-abweichungen.md`; Langfassungen `Dossier/video-1…4-*-lang.md`; Cutter-Pläne `video-1…4-*.md`, Übersicht `01-projekt-grundlagen.md`, Anhang `99-anhang-material-und-nachdreh.md`.
- Verifikation: `_intern/verify_plans.py` (54 Quellen Cutter-Fassung, 43 Langfassung — alle wortgenau, alle FX3), Seitenbudget `_intern/pagecheck.py`, Zeilenhöhen `_intern/rowcheck.py`.

**Geliefert**
- `Ergebnisse/O-Ton-Pläne/Rappold-Schnittanweisungen.pdf` (12 S.: Deckblatt, Übersicht, je 2 S. Video 1–4, 2 S. Anhang).

**Entscheidungen (User, 14.09.)**
- Ton-Kamera FX3, a7MK4 nur zweiter Winkel.
- Video 3: 22:47-/Nachtmotiv gestrichen, Start direkt mit Christophers „Kennst du das?"-Take; Arbeitstitel „Auto abgeben, wann es passt".
- Video 2: Hannes führt, Christos zweite Stimme.
- Kim (nicht im Konzept) als Team-Stimme in Video 1.
- Formate: Video 1–3 9:16, Video 4 16:9.

**Befunde / Offen**
- Konzept-Hook V1 nie gefragt; iPad-Annahme noch nicht eingeführt; Feierabend „fifty-fifty"; Feierabend-Treffen nur alle paar Wochen (Do/Fr); „neue Halle" 6–8 Jahre alt; kein Licht-an, keine Nacht-, Feierabend- oder One-Take-Aufnahmen.
- Nicht auf der Website: Schlüsselbox/Carlo/24/7, Camper-Verleih, Tankgutscheine, Klima, Hebebühnen, Slogan → nur O-Ton, Captions nach Freigabe. Quereinstieg-Aussage widerspricht Stellenanzeige.
- Offen beim Kunden: Endcard-/Formular-URL, Claim-Freigaben, Carlo-Ablauf (Check-in-Code?), Einverständnis der Kunden-Darsteller, Nachnamen Kim/Christos (falls gewünscht), Verkäufer in `Beratung am Auto`/`Kaufvertrag` (vermutl. Christopher).
- Nachdreh-Optionen im Anhang (Licht-an, Feierabend-Tisch, Box mit Kunde, One-Take).

## Nachtrag 14.09.2026 — B-Roll nur als Vorschlag

**Gemacht**
- Auf User-Wunsch alle konkreten B-Roll-Verweise (Ordner, Clip-Nummern) aus der Cutter-Fassung entfernt. Die Spalte heißt jetzt „Bild-Vorschlag" und nennt nur Motive (z. B. „Klingelndes Telefon, volle Theke"); den B-Roll wählt der Cutter.
- Video 3: Display-/Fach-Nahaufnahmen als Motiv beschrieben, Hinweis auf die zweite Kamera ohne Dateinummern. Video 4: alle Stationen als Motiv-Vorschläge.
- Anhang: „B-Roll-Hinweise" → „Sperr- und Prüfhinweise". Gesperrte Clips (Fremdfahrzeug, NIRO-Kamera im Bild, Bodenaufnahme, Kamera-Rig) bleiben benannt, der Empfehlungs-Punkt (Käfer Cabrio/Modellautos) ist raus.
- Dossier-Langfassungen behalten die Clip-Funde als interne Sichtungsnotiz (Hinweis oben ergänzt).

**Geliefert**
- `Rappold-Schnittanweisungen.pdf` neu gerendert: weiterhin 12 S., alle Kapitel im Budget, 54 Zitate unverändert verifiziert.

**Offen**
- Klären, ob „nur Motiv-Vorschläge" künftig Standard für alle Schnittpläne ist. Dann `tools/transcribe/WORKFLOW-Schnittplan.md` anpassen; dort nennt die Bild-Spalte bisher Ordner + Personen.

## Nachtrag 14.09.2026 — lesefreundlichere Fassung (bis 4 Seiten pro Video)

**Gemacht**
- User erlaubt 3–4 Seiten pro Video, wenn es sich besser liest. Die Kürzungen, die nur für das 2-Seiten-Budget nötig waren, sind zurückgenommen: Zitate wieder vollständig (nur Kims Innenschnitt #11 bleibt mit […]), ausführlichere Kommentare mit In/Out-Hinweisen, Material als Stichpunkte, Alternativen wieder mit Wortlaut und Timecode, „Offen" in Video 2 wieder als eigener Abschnitt.
- Bild-Spalte bleibt „Bild-Vorschlag" (nur Motive). `_intern/pagecheck.py` prüft jetzt auf max. 4 Seiten pro Video.

**Geliefert**
- `Rappold-Schnittanweisungen.pdf` neu: 14 S. (Video 1 und 2 je 3 S., Video 3 und 4 je 2 S., Anhang 2 S.), 54 Zitate verifiziert.

## Nachtrag 14.09.2026 — iPad freigegeben, Länge max. 60 s

**Entscheidungen (User)**
- iPad darf in die Videos, auch mit der Aussage, dass es erst im Kommen ist.
- Längen-Standard NIRO: max. 60 s, sofern das Konzept keine Länge vorgibt.

**Geprüft**
- Konzept-PDF (Textsuche nach Sekunden/Länge/Dauer): Nur Video 4 hat eine Vorgabe — „Ca. 30 Sekunden schneller Durchlauf". Video 1–3 ohne Längenangabe → max. 60 s.

**Gemacht**
- Video 1 neu auf ≈ 58 s: iPad-O-Ton Michael (FX3_1009 04:51,8–04:55,5 + 04:59,2–05:02,6) als #7, Pain gekürzt, Schlüsselbox-Satz gekürzt, Kim zweimal (Team hilft, Familienbetrieb), Rückkehrer kompakt + „Die haben sich gefreut, dass ich wieder gekommen bin." (13:04,8). iPad-Sperre überall entfernt (Material, Übersicht, Warnbox, Dossier).
- Video 2 neu auf ≈ 57 s: 11 O-Töne (H H C H H C H C H C H); raus: Eigene Kiste, Immer Hilfe, Qualität als O-Ton (jetzt Caption), Crafter/Wohnmobil, Rat „versauern" → alle mit Timecode in den Alternativen.
- Video 3 ≈ 50 s und Video 4 ≈ 40 s (Durchlauf ≈ 30 s laut Konzept) unverändert; Video 4 bekommt optional den iPad-VO des Geschäftsführers (FX3_1014 18:12,3–18:16,5).
- Übersicht: Längen-Spalte und Regel „max. 60 s" ergänzt; auf eine Seite verdichtet.

**Geliefert**
- `Rappold-Schnittanweisungen.pdf`: 14 S. (Übersicht 1, Video 1 3 S., Video 2 3 S., Video 3 2 S., Video 4 2 S., Anhang 2 S.), 47 Zitate verifiziert.
