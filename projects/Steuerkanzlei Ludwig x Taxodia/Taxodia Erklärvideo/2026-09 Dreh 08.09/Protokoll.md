# Protokoll — Steuerkanzlei Ludwig x Taxodia · Taxodia Erklärvideo · 2026-09 Dreh 08.09

## Session 14.09.2026 — Projekt angelegt

**Gemacht**
- Kunde, Projekt und Charge im Studio angelegt. Die Namen folgen dem NAS-Ordner `01_Taxodia Erklärvideo`, die Charge dem Drehtag 08.09.2026 aus den Kamera-Metadaten. Unterordner folgen erst, wenn eine Funktion läuft.
- NAS-Bestand nur gelesen: `NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/Steuerkanzlei Ludwig x Taxodia/02_Projekte/01_Taxodia Erklärvideo/03_Medien/01_Footage/`
  - `Kamera-A`: Sony a7 IV (ILCE-7M4), 9 Clips, 1 h 46 min, 108 GB, UHD 25p, 09:56–13:22
  - `Kamera-B`: Sony FX3 (ILME-FX3), 8 Clips, 1 h 39 min, 101 GB, UHD 25p, 10:08–13:30
  - `B-Roll`: Sony FX3A (ILME-FX3A), 28 Clips (C0235–C0262), 19 min, 29 GB, UHD 50p, 13:09–14:06; in `Proxy/` liegen erst 19 von 28 Proxys
  - Leer: `01_Corporate Identity`, `01_Video-Onboarding`, `02_Video-Konzept`, `03_Medien/02_Assets`, `04_Exportiert`, `05_Finale Videos`
- Websites gelesen (Stand 14.09.):
  - **Taxodia GmbH** (taxodia.de), Zur Braake 52, 27374 Visselhövede, GF Jörn Flammann. „Online-Steuerfachschule für Quereinsteiger“: Sie macht branchenfremde Kanzlei-Mitarbeiter in 12 Wochen zu produktivem Fachpersonal, mit Schwerpunkt landwirtschaftliches Rechnungswesen und Steuerrecht. Die Module sind online und flexibel, abgerechnet werden nur begonnene Module. Leitgedanke: „Dem Fachkräftemangel begegnen“.
  - **Steuerkanzlei Ludwig – Landwirtschaftliche Buchstelle** (lbl-bw.de), Steinbrunnenstr. 3, 74532 Ilshofen, Steuerberater Friedrich Ludwig, gegründet 2003. Schwerpunkte: Land- und Forstwirtschaft, erneuerbare Energien, Mittelstand. Leitbild „Zukunft. Gemeinsam. Gestalten.“
  - Beziehung: Auf lbl-bw.de/netzwerk heißt Taxodia „Partner in der Online-Weiterbildung“, und taxodia.de führt die Kanzlei unter „Unsere Kunden“.

**Geliefert**
- Keine Dateien, nur die Projektanlage.

**Befunde**
- Der NAS-Ordnername `01_Taxodia Erklärvideo` ist in NFD gespeichert, die Studio-Ordner in NFC. Skripte, die Pfade vergleichen, müssen normalisieren.
- Die Zeitzonen-Stempel sind uneinheitlich: a7 IV und FX3 schreiben +01:00, die FX3A +02:00.

**Offen**
- Konzept oder Script fehlt (NAS-Konzeptordner leer). Es wird für Schnittplan und Video-Auswahl gebraucht.
- Wer spricht (Namen, Rollen) und wer ist Absender des Videos: Taxodia oder die Kanzlei? Davon hängen CI, Endcard/CTA-URL und die maßgebliche Website ab.
- Ton-Kamera beim Dreh-Team erfragen, nicht aus dem Pegel raten. Danach beide Interview-Kameras transkribieren.
- Format (16:9 oder 9:16), Länge und CI (NAS-CI-Ordner leer).

## Session 14.09.2026 — Schnittplan (Funktion „Schnittplan:")

**Gemacht**
- Konzept-PDF (1 Video, 6 Kapitel, 25 Interviewfragen) aus dem Chargen-Ordner nach `Material/Konzept/` verschoben und in `_intern/script_structured.json` strukturiert.
- Beide Interview-Kameras transkribiert (17 Clips, Scribe, `_intern/transcribe_taxodia.py`), keine B-Roll. Zuordnung über Selbstvorstellung, Kontaktbogen und Website: FX3_0222 = Friedrich Ludwig, FX3_0223 = Jörn Flammann, FX3_0225/0226/0228 = Jan Philipp Hein (a7: 0117/0118, 0119/0748, 0750–0752). Index mit Person und Kamerarolle, Utterances gebaut.
- Technik-Inventar `_intern/footage_probe.json`: alles S-Log3, Interviews 25p, B-Roll 50p. Proxys inzwischen 28/28 (B-Roll) plus 4 für Kamera-A.
- Kontaktbögen `_intern/sichtung/` (Kamera-A, Kamera-B, B-Roll), größere B-Roll-Raster und Zooms für den Datenschutz-Check, CTA-Blickrichtung geprüft.
- Websites gesichert (`_intern/website/`, 15 Seiten taxodia.de, 21 Seiten lbl-bw.de) und gegen alle Konzept-Claims geprüft.
- Ton gemessen (`_intern/pegel.py`) an allen gewählten Bereichen.
- 60 O-Ton-Kandidaten wortgenau verortet (`_intern/kandidaten.py`, `_intern/teilbereiche.py`, `_intern/woerter.py`), Plan-Zeilen mit exaktem Wortlaut per `_intern/plan_rows.py` (28 Zeilen, 4:56 roh).
- Analyse `Ergebnisse/O-Ton-Pläne/00-material-und-abweichungen.md`, Langfassung mit Clip-Funden `Dossier/video-1-taxodia-weg-lang.md`, Cutter-Plan `video-1-taxodia-weg.md` (28 Zeilen, volle Zitate), Übersicht `01-projekt-grundlagen.md`, Anhang `99-anhang-alternativen-und-material.md` (A1–A16 mit Wortlaut). Eine erste Fassung in zwei gekürzten Teilen wurde nach den User-Antworten ersetzt.
- Verifikation `_intern/verify_plans.py`: Cutter-Plan + Anhang 42 Quellen/49 Zitat-Fragmente, Langfassung 26/33, alle wortgenau und aus der FX3. Gegentest mit falschem Zitat und falschem Timecode schlägt korrekt an. `_intern/pagecheck.py` (max. 20 Seiten, fast leere Schlussseiten): 8 Seiten, keine leere Schlussseite.
- **Nicht in Resolve umgesetzt** (User: kommt im zweiten Schritt).

**Geliefert**
- `Ergebnisse/O-Ton-Pläne/Taxodia-Schnittanweisungen.pdf` (8 S.: Deckblatt, Übersicht, Video 1 mit 4 S., Anhang 2 S.).

**Entscheidungen (User, 14.09.)**
- Ton-Kamera **Kamera-B (FX3)**, a7 IV nur zweiter Winkel.
- **16:9, Ziellänge ca. 4–5 min.**
- **Bild-Spalte nur mit Motiven, generell** (keine B-Roll-Clips im Cutter-PDF; Clip-Funde ins Dossier) → `tools/transcribe/WORKFLOW-Schnittplan.md` angepasst.
- **Umfang:** „So viele Seiten wie nötig, nicht über 20" → volle Zitate statt Kürzung.

**Umsetzung im Plan (von mir, nicht mit Kunde abgestimmt)**
- Kaltstart mit drei Stimmen (Ludwig „Anzeigen sind schon lange tot." → Flammann „leichter, einem Landwirt das Steuerrecht beizubringen …" → Hein „ohne den Taxodia-Kurs … nicht im Steuerrecht gelandet"), danach Titel.
- Hein früher als im Konzept (Kapitel 1), sonst drei Ludwig-Takes in Folge. Sprecherfolge nie mehr als 2.
- Einblendungen nur mit neuen, website-belegten Fakten (Regel vom 14.09.): Software der Kanzlei, Niveau Bachelor Professional, Einstieg jederzeit, keine Hotel-/Reisekosten, Kanzlei sieht Lernfortschritt, keine Vorkasse/Stornokosten, Live-Einheit vor der mündlichen Prüfung. Platz 1+2 und Note nicht als Einblendung.

**Befunde**
- FX3-Ton sehr leise (−31 bis −39 LUFS, CH1 = CH2). FX3_0222 12:43–14:16 ohne Ton (Mikrotausch), danach Ludwig ≈ 4 dB lauter. FX3-Uhr ≈ 8 min vor der a7. Beide CTAs schauen in die FX3.
- Konzept vs. O-Ton/Website: „von Anfang an produktiv" nicht belegt (Hein: erste Tätigkeiten nach 5–6 Wochen, Website: nach ca. 340 UStd). „30 Jahre" → Website „mehr als 25". Preis 480–500 €, „21 Wochen Präsenz", Montag-Anruf, „sechs der zwölf Prüfungsbesten" und „Frühjahr 2027" sagt niemand. Platz 1+2, Note 1,06 und Ampel stehen nicht auf der Website → nur O-Ton. Musterkurs verwechselt Flammann mit dem Einstieg.
- **Taxodia ist B2B** (Anmeldung nur über Arbeitgeber) → Heins CTA „teste den Taxodia-Einsteigerkurs" braucht eine Endcard-Zeile über den Weg über eine Kanzlei.
- B-Roll/C0255 zeigt Heins echten Kursplan (Name + Teilnehmer-ID lesbar) → blurren. Mandantendaten nirgends lesbar.
- Gesperrt: Veganer-Äußerungen, Recruiter-Schelte, „nur noch uns in Süddeutschland", Preise/Provision/Gehalt, Fall der Landwirtin mit Note, Durchfaller, Hein-Take 1 „Fachwirt".
- Nicht gedreht: Landwirtschaft/Hof, LMS-Screenrecordings, Ampel im Dummy-Account, Team-Alltag, Fotos von Prüfung/Zeugnis. Logos fehlen (CI-Ordner leer).
- Werkzeug-Falle: Das Rappold-`verify_plans.py` hat 0 Zitate erkannt (Regex erwartet “/”, Pläne schließen mit "). Für Taxodia korrigiert und mit Leerlauf-Schutz versehen, im Workflow vermerkt. Rappold-Nachprüfung als eigene Aufgabe angelegt.

**Offen**
- Taxodia: Beleg für „die zwei Besten", Freigabe der Ampel-Grafik.
- Endcard-Zeile für Quereinsteiger + Logos Taxodia und Kanzlei.
- Acker/Hof-B-Roll (Nachdreh auf Heins Hof oder Stock), LMS-Screenrecordings/Dummy-Account von Taxodia.
- Musik (Artlist/Envato). Umsetzung in Resolve (AutoCut) als nächster Schritt.

## 2026-09-14 20:22 — AutoCut: Rohschnitt

- Timeline „AutoCut video-1-taxodia-weg 2026-09-14 2022 (roh)“ gebaut aus video-1-taxodia-weg.md: 28 Beats, Länge 05:34 (Ziel 05:00)
- V2 (a7IV): 25 von 26 O-Ton-Beats
- 4 Warnungen (siehe Bericht)
- Bericht: /Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/Ergebnisse/Rohschnitt/video-1-taxodia-weg-rohschnitt.md
- Resolve: Projekt 'Taxodia 09.26', Bin AutoCut/video-1-taxodia-weg, 97 Items, 30 Marker, SaveProject ok
- Dateien: /Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/_intern/autocut/timeline.json, /Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/_intern/autocut/build.json, /Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/Ergebnisse/Rohschnitt/video-1-taxodia-weg-rohschnitt.md

## Session 14.09.2026 — Rohschnitt in Resolve (Funktion „AutoCut:", Stufe 1)

**Auftrag (User):** „Baue jetzt den Rohschnitt ohne B-Roll nach dem Schnittplan." Freigegeben zum Schreiben: das offene Resolve-Projekt **„Taxodia 09.26"** (vor jedem schreibenden Schritt Name gelesen und abgeglichen).

**Gemacht**
- Chargen-Daten AutoCut-tauglich gemacht, ohne Code-Änderung: `_intern/transcripts_index.json` Kategorie „Interviews" (Kamera-Ordner als `kamera_ordner` erhalten). `_intern/autocut/media.json` Kamerapaare nach Person gruppiert, weil das Material nach Kamera getrennt liegt (Ludwig FX3_0222 × a7 0118, Flammann FX3_0223 × a7 0119/0748, Hein FX3_0228 × a7 0752).
- Cutlist aus den geprüften Plan-Zeilen: `_intern/cutlist_aus_plan.py` → `_intern/autocut/cutlist.json`. 28 Beats (26 O-Ton, Titel und Endcard als Grafik-Platzhalter), 33 Cuts auf exakten Wortgrenzen, ein Cut je Bereich bei „[…]", 14 Sperren mit Zeitbereich. Der Entwurf von `autocut_cutlist_draft.py` hatte Bereiche zusammengelegt und keine Sperren → ersetzt, Sicherung `cutlist_entwurf.json`.
- Sync per Wellenform: 0222×0118 +986 f (Konf. 45,5), 0223×0119 +1383 f (31,1), 0228×0752 +489 f (36,7) ok. 0223×0748 −53747 f (−2149,875 s) nur Konf. 3,7 → nicht ok. Der Versatz passt zu den Wortzeiten, bleibt aber bewusst gesperrt: CTA #26 soll frontal auf der FX3 bleiben.
- Prüfung (Hash) ok: 0 Fehler, 2 Warnungen (#26 ohne a7). Resolve-Probe ok (endFrame exklusiv, recordFrame absolut, Marker relativ, Marker hinter dem Ende möglich). Die Probe-Timeline wurde vom Skript gelöscht, den leeren eigenen Bin „AutoCut/PROBE" habe ich danach gelöscht.
- Bau: Timeline **„AutoCut video-1-taxodia-weg 2026-09-14 2022 (roh)"** im Bin `AutoCut/video-1-taxodia-weg`. Die Clips kamen aus dem vorhandenen `01_FOOTAGE`, es wurde nichts doppelt importiert.
- Readback (nur lesend, eigenes Skript gegen `timeline.json`): alle 97 Items gleich (Spur, Datei, Record-In/Out, Source-In, aktiv), alle 30 Marker samt Notizen gleich.
  - V1 FX3 33, A1 FX3-Ton 33 (deckungsgleich), V2 a7IV 31, V3 B-Roll leer.
  - Marker: 26 blau (O-Ton), 2 lila (Grafik), 2 rot (V2 fehlt #26).
  - Aktive Timeline danach: „Interview_Timeline 11" (User).

**Geliefert**
- Resolve „Taxodia 09.26": Timeline „AutoCut video-1-taxodia-weg 2026-09-14 2022 (roh)" (3840×2160, 25 fps, Start 01:00:00:00).
- `Ergebnisse/Rohschnitt/video-1-taxodia-weg-rohschnitt.md` (Beats, Sync, Warnungen, Sperren).

**Befunde**
- Länge laut Plan 05:33:18: O-Ton 04:56:18, Grafik-Platzhalter 10 s, 27 × 1 s Pause. Ohne Pausen sind es 05:06:18.
  - Die Timeline in Resolve endet schon bei 05:25:18. Die Endcard (#28) ist nur ein lila Marker bei 05:26:18 ohne Clip.
- #26 CTA Kanzleien: V2 leer. Der Innenschnitt bei 05:05:12 ist deshalb ein sichtbarer Sprung im Frontalbild und braucht B-Roll oder einen Zoom.
- Pegel unbearbeitet (roh): FX3 weiter −31 bis −39 LUFS. Finalisieren (Stufe 5) setzt `probe_xml.json` voraus. Das braucht `broll_index.json` mit einem B-Roll-Clip ab 50 fps, also erst den B-Roll-Index (Stufe 2).
- API-Eigenheit Resolve 21.1: `GetIsTrackEnabled` liefert für nicht aktive Timelines `false`, auch bei den Vorlagen des Users. Das ist kein Hinweis auf gesperrte Spuren.

**Offen**
- Feinschnitt/Straffen auf 4–5 min (Pausen kürzen), Titel- und Endcard-Grafik, Musik.
- Pegel: Finalisieren erst nach B-Roll-Index, oder Pegel von Hand im Cutter-Schnitt.
- B-Roll bleibt leer (Stufe 3 ausgesetzt, User-Regel 09.09.).
- Punkte aus dem Schnittplan-Eintrag (Beleg „die zwei Besten", Ampel-Freigabe, Endcard-Zeile, Logos, Hof-B-Roll) unverändert offen.

## 2026-09-15 09:41 — AutoCut: Rohschnitt

- Timeline „AutoCut video-1-taxodia-weg 2026-09-15 0941 (roh)“ gebaut aus video-1-taxodia-weg.md: 24 Beats, Länge 04:34 (Ziel 04:30)
- V2 (a7IV): 21 von 22 O-Ton-Beats
- 6 Warnungen (siehe Bericht)
- Bericht: /Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/Ergebnisse/Rohschnitt/video-1-taxodia-weg-rohschnitt.md
- Resolve: Projekt 'Taxodia 09.26', Bin AutoCut/video-1-taxodia-weg, 87 Items, 27 Marker, SaveProject ok
- Dateien: /Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/_intern/autocut/timeline.json, /Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/_intern/autocut/build.json, /Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/Ergebnisse/Rohschnitt/video-1-taxodia-weg-rohschnitt.md

## Session 15.09.2026 — Kurzfassung (Schnittplan + Rohschnitt, eine Minute kürzer)

**Auftrag (User):** Das Video ist zu lang, „1 min weniger wäre schon gut". Nach meinem Kürzungsvorschlag: „kürze es so weit, dass alle wichtigen Aussagen drin sind". Umgesetzt wurde der empfohlene Vorschlag ohne die optionalen Extras (Fachagrarwirt-Satz, „kein Präsenzprogramm", „Glücksfall", Füllwörter).

**Gemacht**
- Langfassung gesichert: `_intern/archiv/2026-09-14 Langfassung/` (Plan-Markdowns, PDF, plan_rows, Cutlist, timeline/build/verify, Rohschnitt-Bericht).
- **Gestrichen:** Hein „Regentage/Acker", Flammann „nicht allein lassen", Hein „Antwort am gleichen Tag", Hein „Live-Meeting vor der Prüfung". Alle vier stehen mit Wortlaut im Anhang A17–A20. Die Einblendung „Live-Einheit vor der mündlichen Prüfung" entfällt.
- **Gekürzt:**
  - Ludwig und Hein ohne Namensvorstellung, das übernimmt die Bauchbinde.
  - Ampel ohne „um einen guten Überblick … haben wir", jetzt „Wir haben, […] ein Controlling …".
  - CTA Kanzleien ohne „im Zeitalter des Fachkräftemangels … die Arbeit bleibt liegen".
- **Plan neu nummeriert:** 24 Zeilen, Sprecherfolge nie mehr als 2 derselben Person. `_intern/plan_rows.py` ergibt 4:01 inkl. Titel und Endcard. Die Dossier-Langfassung behält die alten Nummern, oben steht jetzt die Zuordnung.
- **Aktualisiert:**
  - `video-1-taxodia-weg.md` und Anhang, Querverweise dort neu nummeriert.
  - Übersicht (Länge, Hof-B-Roll nur optional), `00-material-und-abweichungen.md`.
  - `pdf_meta.json` mit Stand 15.09.
  - Anhang „Fehlendes Material" auf zwei Punkte gekürzt, damit keine fast leere Schlussseite entsteht.
- **Prüfungen:**
  - `verify_plans.py`: 42 Quellen, 50 Zitat-Fragmente wortgenau.
  - `pagecheck.py`: 8 Seiten, keine fast leere Schlussseite.
  - Cutlist neu (Entwurf `--force` → `_intern/cutlist_aus_plan.py`, Ziel 270 s): 24 Beats, 30 Cuts, 14 Sperren. Prüfung ok mit 0 Fehlern, 3 Warnungen (#22 ohne a7). Probelauf 87 Items, 04:34.
- **Resolve „Taxodia 09.26":**
  - Vor dem Bau war der User in seiner Timeline „B-Roll Auswahl" (Bin „Edit - 16x9 Querformat") → per Rückfrage abgestimmt („Jetzt bauen").
  - Gebaut: **„AutoCut video-1-taxodia-weg 2026-09-15 0941 (roh)"**.
  - Der Build stellt nur die Timeline wieder her, der Media-Pool-Bin stand danach auf „Kamera-B". Ich habe ihn per MCP auf „Edit - 16x9 Querformat" zurückgesetzt.
  - Readback gegen `timeline.json`: 87/87 Items und 27/27 Marker gleich (V1 30, A1 30, V2 27, V3 leer; 22 blau, 2 lila, 3 rot). Aktiv danach wieder „B-Roll Auswahl".
- Die Langfassungs-Timeline „… 2026-09-14 2022 (roh)" bleibt stehen.

**Geliefert**
- `Ergebnisse/O-Ton-Pläne/Taxodia-Schnittanweisungen.pdf` (8 S., Stand 15.09., gekürzt), Plan-Markdowns aktualisiert.
- Resolve: Timeline „AutoCut video-1-taxodia-weg 2026-09-15 0941 (roh)", Bericht `Ergebnisse/Rohschnitt/video-1-taxodia-weg-rohschnitt.md`.

**Befunde**
- **Länge:** 4:33:20 statt 5:33:18, also genau 60 s kürzer. Davon O-Ton 4:00:20, Grafik-Platzhalter 10 s, 23 × 1 s Pause; ohne Pausen 4:10:20. Die Resolve-Timeline endet bei 4:25:20, die Endcard ist nur ein Marker.
- **Enge Anschlüsse gegenhören:**
  - #16: „Wir haben," ist ein 10-Frame-Schnipsel vor „ein Controlling".
  - #22: nach „appellieren," kaum Pause. Der CTA hat keine a7, also zwei Innenschnitte per Punch-in.
- **B-Roll:** Der User sortiert die Shots in „B-Roll Auswahl" vor (wenig Material) und gibt Bescheid. Erst dann B-Roll einsetzen; bis dahin gilt die Aussetzung von Stufe 3 weiter.

**Offen**
- B-Roll aus „B-Roll Auswahl" nach Freigabe des Users.
- Pegel, Titel- und Endcard-Grafik, Musik.
- Unverändert offen: Beleg „die zwei Besten", Ampel-Freigabe, Endcard-Zeile für Quereinsteiger, Logos.

## Session 15.09.2026 — B-Roll aus der User-Auswahl eingesetzt

**Auftrag (User):** „B-Roll ist ausgewählt in der aktuell offenen Timeline, du darfst nur die Bereiche, die darin sind, nutzen, also die Clips nicht verlängern, kürzen geht natürlich." Das ist die ausdrückliche Freigabe für B-Roll in diesem Video. Die generelle Aussetzung von AutoCut Stufe 3 bleibt davon unberührt.

**Gemacht**
- Die Auswahl-Timeline „B-Roll Auswahl" (User) nur gelesen: 30 Shots der FX3A (50p, C0235–C0262), lückenlos, ohne Marker, alle in Echtzeit, zusammen 99,9 s → `_intern/autocut/broll_auswahl.json` (`_intern/broll_auswahl.py`).
- Je Shot vier Standbilder aus dem echten In/Out (Proxy) als Kontaktbögen `_intern/sichtung/broll-auswahl/`, gesichtet.
  - Sechs Situationen: Hein am Arbeitsplatz, Ankunft/Begrüßung, Ludwig und Flammann am Schreibtisch, Ludwig am Telefon, Hein und Flammann am Laptop, Flammann telefoniert im Sessel.
  - Die Bildschirm-Shots habe ich in 4K geprüft (siehe Befunde).
- **Plan** (`_intern/broll_einsetzen.py`), nach Wortzeiten auf der Timeline, Bild-Vorschlag im Plan und AutoCut-Regeln:
  - Titel: Ankunft.
  - Kanzlei (#5): Büro.
  - Hein (#7): Arbeitsplatz.
  - Taxodia (#9): Lernplattform, Gespräch.
  - Studium (#10): Gesetzbuch.
  - Bachelor Professional (#11): Hein lernt.
  - Einstieg (#12): Laptop, deckt beide Innenschnitte.
  - Rechnung (#13).
  - Mitarbeit (#15): Hein telefoniert.
  - Ampel (#16): Monitor mit Kursplan, Anrufe; deckt beide Innenschnitte.
  - Kanzlei informiert (#17): Flammann ruft an.
  - Faire Abrechnung (#18).
  - Zweifel (#19): Laptop, deckt den Innenschnitt.
  - Gesicht bleibt bei Kaltstart, Bauchbinden, Suche, Entscheidung, Lernwoche, Ergebnis/Note und beiden CTAs.
  - Wer im B-Roll selbst spricht, liegt möglichst nicht unter seinem eigenen O-Ton. Kein Einstellungs-Doppel in Folge.
- **Probelauf:** jeder Shot höchstens einmal, alle Bereiche innerhalb der Auswahl, keine Überlappung.
- **Resolve „Taxodia 09.26"** (Projekt vorher geprüft), eigene Timeline „AutoCut video-1-taxodia-weg 2026-09-15 0941 (roh)":
  - 30 Items auf V3 in einem Append.
  - Readback: 30/30 identisch, 0 außerhalb der Auswahl, V1/V2/A1 unverändert (30/27/30).
  - Aktive Timeline „B-Roll Auswahl" und Bin „B-Roll" des Users danach wiederhergestellt, SaveProject ok.
- **Marker-Fehler:** Die drei Hinweis-Marker scheiterten zunächst an einer vertauschten Argument-Reihenfolge in meinem Skript (behoben). Ich habe sie per MCP auf der inaktiven Timeline nachgesetzt, ohne Timeline-Wechsel (Readback 30 Marker: 22 blau, 2 lila, 4 rot, 2 gelb).
- Rohschnitt-Bericht um den Abschnitt „B-Roll" ergänzt (Tabelle mit allen 30 Shots).

**Geliefert**
- Resolve: V3 der Kurzfassung gefüllt: 84,0 s B-Roll = 32 % der Timeline, 100 % Tempo.
- `Ergebnisse/Rohschnitt/video-1-taxodia-weg-rohschnitt.md` (Abschnitt B-Roll), `_intern/autocut/broll_einsatz.json`.

**Befunde**
- **C0255 Monitor nah** (S18, im Schnitt 02:53:12): Heins echter Kursplan mit „Hein, Jan-Philipp", URL, Lesezeichenleiste und „Dozentin: Heike Becker" → roter Marker, blurren.
- **C0260/C0261 Laptop** (01:14:12, 02:08:22): Dozentenprofil „Karin Thomas, Dipl.-Finanzwirtin (FH)" lesbar, steht nicht auf taxodia.de → gelbe Marker, mit Taxodia klären oder blurren.
- 16 s der Auswahl bleiben ungenutzt (gekürzte Enden), die Pausen ohne B-Roll bleiben schwarz.

**Offen**
- B-Roll-Abnahme durch den User; Blur C0255 und Klärung „Karin Thomas".
- Zeitlupe (50p konformieren) nur auf Wunsch.
- Pegel, Titel- und Endcard-Grafik, Musik.

## Session 15.09.2026 — Ton, Animationen, Musik (Funktionen „Resolve:" + „Animation:")

**Auftrag (User):** „Lade passende Musik herunter und mache die Animationen, außerdem nutze Audio-Normalisation auf allen Ton-Sprachspuren. Und Voice Isolation auf der Track." CI-Quellen vom User: taxodia.de/ueberblick, lbl-bw.de/netzwerk.

**Ton (Resolve „Taxodia 09.26", eigene Timeline „AutoCut video-1-taxodia-weg 2026-09-15 0941 (roh)")**
- Alle 30 Clips auf A1 „FX3 Ton" per `Timeline.NormalizeAudioLevel` normalisiert: True Peak −3 dBTP, unabhängig je Clip (Standard aus dem AutoCut-Feedback 04.09.). Das ergibt +12,2 bis +21,3 dB (`_intern/audio_normalisieren.py`).
- Nachgemessen mit ffmpeg ebur128 (True Peak im Clipbereich): alle 30 Clips innerhalb ±0,1 dB → `_intern/autocut/audio.json`.
- Voice Isolation auf Spur A1 eingeschaltet (`SetVoiceIsolationState`, Stärke 50, vorher aus). NormalizeAudioLevel lief ohne Timeline-Wechsel, SaveProject ok.

**Animationen (Remotion, Client `taxodia`)**
- **CI gemessen** (computed styles im Browser, Werte vom User bestätigt):
  - taxodia.de: Grün #9ABC44, Band #7B9636, Überschriften-Grün #667D2D, Flächen #F8F9F2/#E2E9C9, Text Schwarz. Die Schrift „Como" ist eine Kaufschrift mit Webfont-Lizenz → Ersatz **Urbanist** (engster Vergleich von 7 freien Schriften).
  - lbl-bw.de: Grün #73AA17, Dunkelgrün #125746 (Rambla/Arimo).
  - Design: helle Karten wie auf taxodia.de, Akzentbalken Taxodia-Grün, Kanzlei-Bauchbinden in Ludwig-Grün.
- **Logos** mit Freigabe des Users geladen: taxodia.de `Taxodia-Logo-2wagq522c83axpf.svg` (7,7 KB), lbl-bw.de `logo-new.svg` (9,2 KB) → `tools/motion/public/clients/taxodia/logos/`.
- **Komposition** `Taxodia-Erklaervideo-Grafikebene`: eine Alpha-Spur 3840×2160, 25 fps, 6845 Frames. Zeiten = Timeline-Frames nach Wortzeiten.
  - Titel „Der Taxodia-Weg" über der Ankunft.
  - Bauchbinden Ludwig, Hein, Flammann.
  - 6 Faktenkarten: Software der Kanzlei, Bachelor-Niveau, Einstieg jederzeit, Kosten, Monitoring, keine Vorkasse.
  - Endcard: Logos, „Taxodia Musterkurs · Ohne Risiko. Ohne Kosten.", taxodia.de, „Für Quereinsteiger: Die Anmeldung funktioniert nur über den Arbeitgeber.".
  - Alle Texte wörtlich bzw. sinngleich auf taxodia.de belegt (Stellen im Chat geprüft, u. a. „mindestens 50% günstiger als in vergleichbaren Präsenzkursen").
- **Nicht gebaut:** Ampel-Grafik (#16), laut Schnittplan erst nach Freigabe durch Taxodia.
- **Review auf echtem Bild** (`tools/motion/scripts/stills-multi.ts` + `_intern/grafik_review.py`): Remotion-Standbilder über dem Timeline-Bild (V3 vor V2 vor V1, bei Interviews beide Kamerawinkel) → `_intern/sichtung/grafik-review/`.
  - **Befund:** Die Karte „Bachelor Professional" hätte in C0246 (Hein nah) sein Kinn verdeckt → später gesetzt (ab 2881) und nach unten links.
  - Kicker auf 18–19 px vergrößert. Endcard mittiger.
- **Render:** `Ergebnisse/Renders/taxodia-grafikebene-v1.mov` (ProRes 4444, yuva444p12le, 3840×2160, 25 fps, 6845 Frames, 1,5 GB).
  - Alpha-Stichprobe: Frame 100 transparent, 540 Bauchbinde 6 %, 6800 Endcard deckend.
- **In Resolve gesetzt** (`_intern/grafik_einsetzen.py`): Spur V4 „Grafik" angelegt, Render im eigenen Bin, Start 0, Dauer 6845, Alpha „Straight".
  - Timeline jetzt 4:33:20 (V1 30 / V2 27 / V3 30 / V4 1).
  - Timeline und Bin des Users danach wiederhergestellt, gespeichert → `_intern/autocut/grafik_einsatz.json`.

## Session 15.09.2026 — Feinschnitt (Grafik v2, A/B-Wechsel, Musik, B-Roll-Tempo) (Funktionen „Animation:" + „Resolve:")

**Auftrag (User):**
- Alle Schwarzframes mit Grafik oder B-Roll decken.
- Deutlich mehr Grafiken, auch Vollbild (z. B. Karte bei „Ilshofen", Vorbild HBL-Imagefilm).
- Zwischen A- und B-Perspektive wechseln, hier und da L-/J-Cuts.
- Die 3 Tracks aus `Material/Musik/` nutzen: Wechsel pro Thema, nahtlose Übergänge.
- Parallel Color Grading: S-Log3, A/B angleichen, hochwertiger cleaner Look.
- B-Roll stabilisieren, wo es gut aussieht 50 % Tempo.

**Grafikebene v2** → `Ergebnisse/Renders/taxodia-grafikebene-v2.mov` (ProRes 4444, 6845 Frames, 2,4 GB)
- **Vollbild neu:**
  - Flashes „Fachkräftemangel" / „Quereinsteiger" im Kaltstart.
  - Karte Ilshofen (Zoom, 50-km-Kreis, „Landwirtschaftliche Buchstelle").
  - Karte Visselhövede → Ilshofen („online").
  - Grafik „Der Taxodia-Weg" (Einstiegskurs 4 Wochen · 32 UStd → Teil I/II ca. 350 UStd → Prüfung Bachelor Professional).
  - Kapitelblenden „Die Online-Steuerfachschule", „Online lernen", „Das Ergebnis", „Für Kanzleien", „Für Quereinsteiger".
  - Endcard als Wipe.
- **Karten:** Software der Kanzlei, Bachelor Professional, Kosten, Monitoring, Abrechnung pro Modul. Die Karte „Einstieg" ist in der Taxodia-Weg-Grafik aufgegangen.
- **Kartendaten:** Natural Earth 10m admin-1 (gemeinfrei), vereinfacht → `tools/motion/src/clients/taxodia/geo/deutschland-laender.json`.

**Neue Timeline „AutoCut video-1-taxodia-weg 2026-09-15 1149 Feinschnitt"** (Resolve „Taxodia 09.26"; Roh-Timelines bleiben unverändert) — `_intern/feinschnitt_bauen.py`, Bericht `_intern/autocut/feinschnitt.json`
- **Spuren:**
  - V1 FX3 (30 Clips), V2 a7IV in 12 Abschnitten (ca. 57 s).
  - V3 30 B-Roll: 20 × 50 % mit „Nearest" (50p-Quelle, jedes Bild einmal), alle 30 per `Stabilize()` stabilisiert, alle innerhalb der User-Auswahl.
  - V4 Grafik v2.
  - A1 FX3-Ton (True Peak −3 je Clip, Voice Isolation 50), A2/A3 Musik (8 Items), 10 Marker.
- **Schnitt:**
  - J-Cut #20→#21: Flammann bleibt nach dem Satz 1,5 s im Bild, Heins Ton startet 12 Frames vor dem Bild.
  - Pause #6→#7 im Bild gedeckt.
  - Punch-in 112 % im dritten CTA-Stück #22.
- **Schwarzframes:** Deckkraft der Grafikebene je Frame gemessen (`_intern/grafik/alpha_v2.json`).
  - Die Vollbild-Grafiken decken beim Wipe-in/Iris-out 3–10 Frames nicht ganz. Deshalb hält an 13 Stellen das O-Ton-Bild darunter entsprechend länger.
  - Ergebnis: **0 Frames ohne Bild und ohne deckende Grafik** (vorher 51).
- **Gesichts-Check** (`_intern/gesichtscheck/`: Apple Vision auf den Proxys gegen die Alpha-Maske, jedes 2. Frame, 546 Prüf-Frames):
  - Die Karte „Kosten" lag in der a7-Perspektive 16 px (1080p) unter Ludwigs Kinn → a7-Abschnitt 02:30:18–02:33:06 gestrichen, dort bleibt FX3.
  - Danach 0 kritische Stellen, engster Abstand 86 px (1080p).
  - Wipes der Vollbild-Grafiken über Gesichtern sind gewollte Übergänge.
- **Musik:**
  - Campagna im Einstieg; Anhebung zum Titel auf dem Downbeat.
  - Ab der Blende „Die Online-Steuerfachschule" (01:06) 2050.
  - Ab „Online lernen" (02:33) Ikoliks. Bei 03:40 Sprung auf den Aufbau, beat-genau: exakt 8 Takte per Onset-Korrelation, Rest −10 ms.
  - Unter den CTAs zurückgenommen, Endcard-Finale; das Songende fällt auf das Videoende.
  - Offline nachgebaute Mischung gemessen (`_intern/musik/mischung_pruefen.py`):
    - Sprache −19,2 LUFS.
    - Musik unter Sprache im Median 14,0 LU leiser; vorher 9–12 LU → Musikpegel je Abschnitt um 1–5 dB gesenkt.
    - Übergänge ±1,5 LU, True Peak −2,6 dBTP.
- **Zwischenfall:** Der User hat den Feinschnitt im Vollbild abgespielt, während die Ikoliks-Items ersetzt werden sollten.
  - Resolve verweigerte die Löschung, `run_script` hing.
  - Ein abgebrochenes Prüfskript löschte das Endcard-Musik-Item nach Ende der Wiedergabe → sofort wiederhergestellt, danach korrigiert.
  - Voller Readback gegen den Plan: alle 7 Spuren identisch, Musik-Quell-In identisch, Timeline und Projekt gespeichert.

**Umbau für manuelles Feintuning** (User: „B-Cam wieder da rein wo sie war und disable den Bereich … schneide aus der Grafikebene alle toten Bereiche heraus") — `_intern/feinschnitt_umbau.py`, Bericht `_intern/autocut/feinschnitt_umbau.json`
- Vorher geprüft: V1, V2 und V4 unverändert seit dem Bau (keine Handänderungen überschrieben).
- **V2 a7:** wieder durchgehend unter jedem FX3-Stück wie im Rohschnitt (Quelle aus den Roh-Paaren), an den bisherigen A-Abschnitten geteilt.
  - 41 Stücke, davon 12 aktiv (= die bisherigen A-Abschnitte), 29 deaktiviert.
  - Das Bild bleibt identisch; Wechsel lassen sich per Roll-Edit verschieben oder per Aktivieren setzen.
- **V4 Grafik:** 20 Clips, je Grafik-Element einer, auf die sichtbaren Frames getrimmt (Alpha-Maximum je Frame, `_intern/grafik/alpha_v2_ymax.txt`). 190,7 s transparente Bereiche herausgeschnitten.
- Readback: V2/V4 identisch mit Plan, V1/V3/Audio unverändert, Ende 6845. Aktive Timeline und Bin des Users („B-Roll") unverändert, gespeichert.
- `feinschnitt_bauen.py` baut diesen Aufbau bei einem Neubau direkt so.

**Color Grading** — Analyse per Agent (`_intern/color/grading_vorschlag.json`, Kontaktbögen), Anwendung `_intern/color/grading_anwenden.py`, Bericht `grading_einsatz.json` (V3) / `grading_einsatz_v1v2.json`
- **Befund Material:** alle drei Kameras S-Log3/S-Gamut3.Cine.
  - Die a7 IV ist je Set 0,5–1,2 Blenden dunkler, wärmer und flacher als die FX3.
  - Die FX3 hat blaustichige Schwärzen.
- **Projekt-Farbmanagement** (nur gelesen, nicht verändert): DaVinci YRGB Color Managed v2, Input/Timeline „Rec.709 (Scene)", Output „Rec.709-A". Die Clips gehen dadurch unkonvertiert als S-Log3 in den Node.
- **Umsetzung Node 1 je Item:**
  - CDL je Kamera und Person (Angleich + Look: Log-Kontrast 1,20 um 18 % Grau, Sättigung 1,03), danach LUT `Sony/SLog3SGamut3.CineToLC-709.cube`.
  - Aktive lokale Farbversion; keine neue Version, weil die Stabilisierung daran hängen könnte.
- **Anwendung:** 101 Items gegradet (V1 30, V2 41 inkl. deaktivierter Stücke, V3 30), 0 Fehler; LUT-Readback korrekt. V4 Grafik unberührt.
- **Angleich laut Messung:** Haut-ΔE2000 FX3↔a7 im Mittel 2,0 / 1,4 / 0,9 (Ludwig/Flammann/Hein), vorher 9,6 / 16,8 / 14,3.
- **B-Roll:** gemeinsame Basis-CDL plus Belichtungs-Trim je Einsatz (`_intern/color/broll_trims.py`).
  - Median-L* auf halben Weg zum Median aller Shots, höchstens ±0,5 Blenden. Spanne vorher L* 17,9–80,3, nachher 27,1–72,5.
  - Kontaktbogen `kontaktbogen_BRoll_trims.jpg`.
- **Prüfung:**
  - `ExportLUT` geht nur auf der Color-Seite. Die Seite wurde nicht gewechselt, weil der User auf der Edit-Seite arbeitet.
  - Sichtprüfung per Fensteraufnahme des Resolve-Viewers (Flammann FX3 total): sauber, neutral, hell.
  - Einzel-Frames der a7 und der B-Roll in Resolve noch nicht angesehen.

**Interview-Shots begradigt** (User: „alle Interviewshots begradigen über Transform … Pitch, Yaw, Rotation, Zoom und Position") — `_intern/begradigen/`
- **Kameralage gemessen** aus der Sony-Metadatenspur (rtmd) jedes Clips (`lage_messen.py`): Beschleunigungssensor (Satz 0xe44b, 8192 = 1 g) und Brennweite (0x8005/0x8004, RDD-18-Format). Die Kamera stand über den ganzen Clip stabil (Stativ).
  - FX3 geneigt: Ludwig 2,7°, Flammann 2,1°, Hein 1,9°.
  - a7 geneigt: 0,5° / 0,8° / 1,2°.
  - Nicken −1,9° bis +2,4°.
  - Brennweiten FX3 57,5–70 mm, a7 91–117 mm.
- **Gegen Bildlinien geprüft** (`linien_messen.py`, LSD, Person maskiert): Die Rollwinkel stimmen bei Setups mit echten Architekturkanten auf 0,1–0,3°. Achsen des Sensors: x links, y oben, z vorwärts.
- **Resolve-Transform vermessen** (`kalibrierung_*.py`: ArUco-Raster in eigener Timeline, Quick Export ProRes, Rest < 0,3 px):
  - Rotation in Grad, + = gegen den Uhrzeigersinn.
  - Pan/Tilt in Timeline-Pixeln, Tilt + = nach oben.
  - Pitch/Yaw = reine Trapezverzerrung um die Bildmitte (Perspektivterm 2·Pitch/Höhe bzw. 2·Yaw/Breite), zuerst angewendet, dann Zoom/Rotation, dann Position.
  - `ExportCurrentFrameAsStill` enthält die Inspector-Transformationen nicht.
- **Werte** (`parameter_berechnen.py`): waagerechte virtuelle Kamera → Rotation, Pitch, Yaw (kleiner Kopplungsanteil). Den Bildausschnitt habe ich behalten, also keine Verschiebung wie bei einer echten Kameradrehung.
  - Zoom minimal ohne schwarze Ränder: a7 1,017–1,038, FX3 1,060–1,083.
  - Position ≤ 1 % zur Zoom-Entlastung.
  - CTA-Punch-in #22 = Begradigung × 1,12 mit Pan −200.
- **Prüfung in Resolve** (eigene Prüf-Timeline, Quick Export, `pruefung/vergleich_*.jpg`): Senkrechte vorher −2,5° bis +1,6°, nachher sichtbar gerade (FX3 Hein +0,1°, FX3 Flammann +0,3°); keine schwarzen Ränder.
- **Angewendet** (`anwenden.py`, Bericht `anwendung.json` mit Vorher-Werten): 71 Items (V1 30 inkl. Punch-in, V2 41 inkl. deaktivierter Stücke), Zuordnung per Clipname, Readback 71/71, gespeichert.
- **Gesichts-Check** mit den Transformationen erneut: 0 kritisch, engster Abstand 79 px (1080p).
- Eigene Kalibrier- und Prüf-Timelines sowie das Rasterbild wieder gelöscht. Timeline und Bin des Users nach jedem Wechsel wiederhergestellt.

**Kopfposition A/B angeglichen** (User: „Verschiebe die B Perspektive so dass der Kopf da liegt wo er bei der A Perspektive ist, nutze dann Zoom …", dann „Du kannst auch beide verschieben … so wie es am besten aussieht und relativ einheitlich über alle Personen hinweg")
- A = a7 (Kamera-A), B = FX3 (Kamera-B, Ton-Kamera).
- **Messung** (`_intern/begradigen/kopf_angleichen.py`): je FX3-Stück 5 synchrone Zeitpunkte in beiden Kameras, Apple Vision auf den Proxys, a7-Kopf durch dessen Resolve-Transform ins Ausgabebild gerechnet.
- **Befund:** Nur die FX3 zu verschieben hätte bei Flammann und Hein 1,84–2,27× Zoom gebraucht, weil der Kopf in der Totalen sehr hoch sitzt → verworfen.
- **Umsetzung** (`kopf_beide.py --ziel=300,-325,-550`, Bericht `kopf_beide.json` mit Vorher-Werten, Vorschau `kopf_beide_vergleich_X300_a-325_b-550.jpg`), beide Perspektiven verschoben:
  - **Seitlich** exakt gleich und für alle Personen einheitlich: 300 px neben der Bildmitte (4K), Ludwig und Flammann rechts, Hein gespiegelt links.
  - **a7-Nahe:** Kopfmitte 325 px über der Mitte (Augen auf der oberen Drittellinie), ganzer Kopf im Bild.
  - **FX3-Totale:** Kopf 225 px höher (10 % Bildhöhe), vorher lagen 14–23 % Höhe plus seitlicher Versatz dazwischen.
  - Begradigung (Rotation/Pitch/Yaw) bleibt; Zoom = kleinster Wert ohne Rand: FX3 Ludwig 1,23–1,34, Flammann 1,14–1,32, Hein 1,36–1,58; a7 1,06–1,26.
  - CTA #22 (ohne a7) auf dieselbe Position, drittes Stück behält Punch-in ×1,12.
- 71 Items gesetzt (V1 30, V2 41), Readback 71/71, gespeichert. Gesichts-Check mit den Werten je Item: 0 kritisch.
- **User-Feedback „sein Kopf ist zu nah an der Oberkante"** (Ludwig a7, 00:28:10): Der Kopfraum war nur aus der Gesichtsbox geschätzt (Mindestwert 20 px); gemessen blieben bei Ludwig im Mittel 43 px, stellenweise ragte der Kopf hinaus.
  - Neu gemessen: echte Kopfoberkante per Vision-Personenmaske (`personenmaske.swift`, `kopf/kopf_oben.json`). Schädeldach ≈ 1,0 Gesichtshöhen über der Kopfmitte.
  - Original-Kopfraum a7 ≈ 330 px (15 %), FX3 Ludwig ≈ 440 px, FX3 Flammann/Hein nur 80–118 px.
  - **Neue Regeln** (`kopf_final.py`, Bericht `kopf_final.json` mit Vorher-Werten, Vorschau `kopf_final_vergleich.jpg`):
    - Seitlich A = B, einheitlich ±250 px.
    - a7: einheitlich 12 % Kopfraum (≈ 258 px).
    - FX3: Kopfhöhe so nah an der a7 wie möglich mit Zoom ≤ 1,45 und Kopfraum ≥ min(6 %, Original).
    - Ludwig: A und B jetzt auch in der Höhe deckungsgleich (FX3 Zoom 1,15–1,31). Flammann/Hein: FX3 Zoom 1,44, Höhenversatz 8–13 % (CTA #23 21 %), Kopfraum über dem Original.
  - Angewendet 71/71, gespeichert.
- **Gesichts-Check danach:** 11 Frames kritisch (01:55:19–01:59:11). Die Karte „Bachelor Professional" liegt 46–58 px (1080p) unter Flammanns Kinn in der a7, keine Überdeckung.
  - Korrektur berechnet (`nachbesserung.py`): im a7-Stück 2812–3005 Kopf 40 px höher, Abstand 69 px, Kopfraum 10 %.
  - Resolve verweigerte in dem Moment alle Item-Schreibzugriffe (SetProperty = False auf jedem Item, keine Wiedergabe; im Fenster war ein SFX im Source-Viewer/Inspector geöffnet).
  - `karte_nachsetzen.py` versucht es im Hintergrund erneut. Stand siehe `nachbesserung.json`.

**Sound-Design (SFX)** — Plan per Agent (`_intern/sfx/sfx_plan.json`, `sfx_plan.md`, Prüfmischung `vorschau_mischung.wav`), Einsatz `_intern/sfx/sfx_einsetzen.py`, Bericht `sfx_einsatz.json`
- Die SFX-Bins „02_AUDIO/SFX" des Users waren offline (NAS-Ordner umbenannt in „03_Vorlagen und Tools"); der User hat sie neu verknüpft. Alle 17 genutzten Dateien kommen aus dessen Bin, nichts importiert.
- **39 Platzierungen** auf 19 Grafik-Elementen, Spuren A4 „SFX 1" (35) / A5 „SFX 2" (4):
  - luftige Whooshes (Whoosh 2-1…2-5) auf den Vollbild-Wipes, Iris-Swells (Woosh_AI004 / Riser Woosh_AI005)
  - leise Luft-Swishes (Ninja Jump 1/5/6) auf Karten und Bauchbinden
  - Pops/Clicks (Pop Notification, Menu Select, Smartphone Click) auf Pins und Stationen
  - Digital Interface Notification auf „online"-Chip und URL
  - Shimmer auf Titel und Endcard-Logos
- **Pegel dezent:** unter Sprache SFX-Peaks ≤ −26 dBFS, in Sprechpausen etwa auf Musikpegel; Lautheitsbeitrag 0,0 LU, True Peak −2,5 dBTP.
- Readback: 39/39 Position, Länge, Quell-In, Pegel wie Plan.
- **Verknüpfung mit den Grafik-Clips nur teilweise:** Resolve nimmt pro Link-Gruppe offenbar nur einen Clip je Spur auf. Verknüpft ist je Grafik ein SFX (19); die übrigen 20 SFX auf A4 sind nicht verknüpft.
- **Nachsetzen der Karten-Korrektur:** `karte_nachsetzen.py` hat die Korrektur beim 5. Versuch gesetzt (Readback ok, gespeichert). Gesichts-Check danach: 0 kritisch.
- **Resolve-Bedienung:** Kurz danach meldete der User, die Timeline sei nicht bedienbar. Sofort geprüft:
  - Eigene Skripte gestoppt, kein Render, keine Spur gesperrt, API antwortete.
  - Zeitgleich waren zwei weitere Claude-Sessions per Scripting verbunden („niro-studio-46" seit 13:43, „test-67" seit 09:46).
  - Link-Gruppen sauber (19 Paare). Der User meldete kurz darauf „geht wieder"; die Ursache ist nicht geklärt.
- **User: „SFX Clips sind nicht zu hören"** — technisch in Ordnung (Spuren aktiv, online, Mapping nicht stumm), aber zu leise gepegelt: Momentanlautheit −33 bis −42 LUFS bei Sprache ≈ −19.
  - Neu (`_intern/sfx/pegel_neu.json`, `pegel_anheben.py`, Bericht `pegel_anhebung.json`): −28 LUFS unter Sprache, −24 LUFS in sprachfreien Momenten, Spitze ≤ −10 dBFS. Anhebung 2–14 dB (Median 12), 39/39 gesetzt, gespeichert.
  - Prüfmischung neu: −19,1 LUFS unverändert, True Peak −2,47 dBTP, SFX-Stem Peak −9,8 dBTP, 0 übersteuert. `sfx_plan.json` trägt die neuen Pegel, die Agent-Werte stehen in `gain_db_vorher_agent`.
- **User: „ich höre die SFX Clips immer noch nicht"** — echte Ursache gefunden:
  - Ton-Render aus Resolve (20 s, `_intern/sfx/rendertest/ton_0000_0500.mov`): dort, wo der erste Whoosh ohne Sprache/Musik liegt, digitale Stille.
  - Isolationstests in eigener Timeline (danach gelöscht): Clip aus dem User-Bin, frischer Import, per API angelegte Spur und Verknüpfung klingen normal. Eine per `AddTrack` NACHTRÄGLICH (Timeline hat schon Clips) angelegte Spur ist stumm (−180 dB).
  - A4/A5 im Feinschnitt wurden nachträglich angelegt → ohne Bus-Ausgang.
  - Bus-Zuweisung ist per API nicht möglich → der User weist A4 „SFX 1" und A5 „SFX 2" in Resolve dem Main-Bus zu (Fairlight → Bus Assign). Danach Ton-Render zur Kontrolle.
  - Deliver-Einstellungen für die Test-Renders als Preset gesichert und wiederhergestellt, eigene Jobs gelöscht.
- **Bus-Zuweisung durch den User half nicht** (Render weiterhin stumm, Spurmeter zeigten aber Pegel).
  - Nebenwirkung meiner Test-Renders: Resolve blieb auf der Deliver-Seite mit „Export Video" aus, In/Out 0–20 s, Testname/-ort. Behoben: ganze Timeline, Video an, Ziel `Ergebnisse/Export`, Edit-Seite. Der frühere Dateiname und Ort des Users waren nicht wiederherstellbar.
  - Ein Duplikat-Test scheiterte (`StartRendering` = False); das Duplikat ist gelöscht.
- **Lösung vom User:** Track-Effekt **Stereo Fixer, Fix Mode 2** auf der SFX-Spur. Als feste Regel aufgenommen: auf alle SFX- und Sprachspuren (per API nicht setzbar, daher Hinweis nach jedem Bau).
  - Stand letzter Fensteraufnahme: „fx" nur auf A4. A5 „SFX 2" und A1 „FX3 Ton" brauchen den Effekt ebenfalls.

**Beleg-Prüfung Grafik „Der Taxodia-Weg"** (User-Frage „wie kommst du auf diese Zahlen? Sind die belegt?"), geprüft gegen taxodia.de/kurse, Sicherung `_intern/website/www.taxodia.de/kurse.txt` vom 14.09. und live am 15.09.:
- **Belegt:**
  - Einstiegskurs „4 Wochen · 32 UStd / 8 UStd pro Woche" (Karte „Teil I Einstieg": „4 Wochen Unterricht mit insgesamt 32 UStd", „8 UStd pro Woche")
  - „Einstieg jederzeit möglich" („Der Kurs kann jederzeit gestartet werden")
  - Teil I „ca. 350 UStd" (Karte Teil I)
  - „startet jeden Monat" (Gesamtkurs, Teil I, Teil II); „Hauptkurs" ist unsere Formulierung
  - Prüfung „Bachelor Professional" (Kursname)
- **Widersprüchlich auf der Website:** Teil II. Die Gesamtkurs-Karte nennt „∅ 16 UStd im 2. Teil (ca. 350 UStd)", die Karte „Teil II" dagegen „Zweiter Teil (ca. 370 UStd)", und der Gesamtumfang „ca. 720 UStd" passt nur zu 350 + 370.
  - Die Grafik zeigt „ca. 350 UStd" (aus der Gesamtkurs-Karte übernommen) → Empfehlung „ca. 370 UStd" oder bei Taxodia klären.

**Offen:**
- Grading gegenprüfen:
  - a7-Abschnitte und dunkle B-Roll im Viewer ansehen.
  - C0246 (S07, Hein nah) bleibt durch das Raumlicht warm: Weißabgleich von Hand.
  - C0262 (S29/S30): Fenster clippt.
- Blur C0255 und Klärung „Karin Thomas" (Marker).
- Ampel-Grafik erst nach Taxodia-Freigabe.
- Abnahme von Musik, Grafik und A/B-Wechsel durch den User.
- Lieferlautheit (Mischung derzeit −19 LUFS).
- Aktiver Bin nach dem Build „video-1-taxodia-weg" (Start-Bin nicht protokolliert; das Skript loggt ihn seitdem).

## 2026-09-16 11:07 — AutoCut: Kantenprüfung

- Kantenprüfung „AutoCut video-1-taxodia-weg 2026-09-15 1149 Feinschnitt“ am Export AutoCut video-1-taxodia-weg 2026-09-15 1149 Feinschnitt.mov: 4 Befunde (Schwarzbild 0, Schnipsel 0, Knackser 4, Tonloch 0, Wort angeschnitten 0), 16 Grafik-Übergänge als Hinweis
- Umfang: 122 Bild-Schnitte, 136 Ton-Schnitte, 30 Tonclips mit Transkript; Schnappschuss plan (2026-09-16T11:01:42)
- Bericht: /Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/Ergebnisse/Rohschnitt/video-1-taxodia-weg-kanten.md

## 2026-09-16 11:09 — Session: AutoCut-Kantenprüfung (Kalibrierung an dieser Charge)

- **Gemacht:** neue AutoCut-Funktion „Kanten" (Kantenprüfung + Schnittbild, Idee aus browser-use/video-use) am
  Feinschnitt-Export vom 15.09. kalibriert. Schnappschuss aus dem Bauplan (`feinschnitt_bauen.py`), weil „Taxodia 09.26"
  nicht in Resolve geöffnet war — Resolve wurde nicht angefasst.
- **Erster Lauf (Startwerte, 11:02):** 17 Befunde — 16 Schnipsel, alle Flash/Wipe/Iris der Grafikebene V4, und 1 Knackser
  (Sprachtransient 3,6 ms neben einem SFX-Ende). Daraufhin Regeln angepasst: AR-Knackser-Maß (±2 ms), Schnipsel an
  V4-Kanten = Hinweis „Grafik-Übergang".
- **Geliefert:** `Ergebnisse/Rohschnitt/video-1-taxodia-weg-kanten.md`, `_intern/autocut/kanten.json`,
  `_intern/autocut/kanten_readback.json` (Quelle „plan"), Schnittbilder `_intern/autocut/work/schnittbild/kante_001…004_*.png`.
- **Offen — zum Gegenhören (Knackser-Verdacht):** 01:00:04:07 (Musikstart Campagna), 01:01:07:14 (O-Ton-Einsatz
  FX3_0223 über der Kapitelkarte), 01:02:49:12 (O-Ton-Einsatz FX3_0223), 01:02:50:04 (Innenschnitt FX3_0223). Falls
  hörbar: Kante in die Pause legen oder 1-Frame-Blende auf A1 — nur nach Rücksprache.

## 2026-09-16 11:27 — AutoCut: Kantenprüfung

- Kantenprüfung „AutoCut video-1-taxodia-weg 2026-09-15 1149 Feinschnitt“ ohne Export (nur Wortkanten): 8 Befunde (Schwarzbild 0, Schnipsel 0, Knackser 0, Tonloch 0, Wort angeschnitten 8), 0 Grafik-Übergänge als Hinweis
- Umfang: 143 Bild-Schnitte, 147 Ton-Schnitte, 38 Tonclips mit Transkript, 0 ohne erreichbaren Rohclip; Schnappschuss resolve (2026-09-16T11:19:18)
- Bericht: /Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/Ergebnisse/Rohschnitt/video-1-taxodia-weg-kanten.md

## 2026-09-16 11:28 — Session: Kantenprüfung am Hand-Schnitt (nach Änderungen des Users)

- **Gelesen (nur lesend):** Feinschnitt-Timeline in „Taxodia 09.26" nach den Handänderungen — 6625 statt 6845 Frames
  (−8,8 s), A1 38 statt 30 Stücke (neue Innenschnitte), Grafik von V4 auf V5, V4 = Adjustment Clip über die ganze Länge.
  Resolve danach sofort wieder freigegeben (User schneidet weiter).
- **Export vom 15.09. ist veraltet:** Die Knackser-Stellen aus dem Eintrag oben (01:00:04:07, 01:01:07:14, 01:02:49:12,
  01:02:50:04) beziehen sich auf den alten Stand und sind damit hinfällig. Für Schwarzbild/Schnipsel/Knackser/Tonloch
  am neuen Stand braucht es einen neuen Export (Quick Export „H.265 Master" nach `Ergebnisse/Export/`).
- **Wortkanten ohne Export (`--ohne-export`) — 8 Verdachtsfälle zum Gegenhören**, alle am Rohclip-Schnittbild
  bestätigt (`_intern/autocut/work/schnittbild/kante_001…008_wort_*.png`):
  - 01:00:54:21 Ende „nicht." und 01:00:54:22 Anfang „Und" (Innenschnitt, beide Kanten im Klang)
  - 01:02:08:17 Anfang „äh," · 01:02:26:11 Ende vor „Und" (durchgehende Sprache „geben. Und")
  - 01:02:34:06 Anfang „Aber" (erste ~70 ms fehlen) · 01:03:16:05 Anfang „äh,"
  - 01:03:52:12 Anfang „ich" („Ja, i|ch") · 01:03:53:11 Ende „im"
- **Werkzeug nachgeschärft:** Wortregel misst jetzt den Quellton (die reine Scribe-Zeitregel hatte 4 Fehlalarme in
  Pegeltälern), Grafik-Erkennung über den Dateipfad statt fester Spur V4.
- **Offen:** Stellen gegenhören und ggf. Kanten in die Pause legen; nach dem Weiterschneiden neuer Export → volle
  Kantenprüfung.


## 2026-09-17 11:25 — Session: Grading-Test Node-Baum (Spec `docs/superpowers/specs/2026-09-17-autocut-grading-design.md`)

- **Anlass:** User 17.09.: Grading „oft viel zu dunkel, übersättigt, zu hoher Kontrast, Weißabgleich oft off"; Test auf
  Freigabe des Users („Taxodia ist offen, mache jetzt den Test").
- **Resolve (Projekt „Taxodia 09.26"):** Kopie **„AutoCut video-1-taxodia-weg 2026-09-17 1040 Grading-Test"** der
  Feinschnitt-Timeline angelegt (10 Spuren, Clips/Positionen/In-Punkte identisch), Original unverändert. Resolve
  schaltete die Kopie selbst aktiv. Auf der Kopie:
  - Probe-Item V1 @444 (FX3_0222): eigene 3-Node-DRX neu verpackt → angenommen; erzeugter 5-Node-Baum ohne
    Vorschaubild (`BALANCE, ANGLEICH, KONTRAST/SAT, LUT, HAND`) → angenommen, `SetCDL` Node 1–3 + `SetLUT(4)` ok. Trägt
    Testwerte (keine Messung).
  - 8 Test-Items umgegradet (Node 01 gemessen, Node 02 neutral, Node 03 Kontrast 1,00/Sättigung 0,95, Node 04 Sony
    LC-709): V2 a7_0118 @652 (01:00:27:05), V1 FX3_0228 @971 (01:00:40:10), V1 FX3_0222 @1372 (01:01:01:15),
    V1 FX3_0223 @1788 (01:01:14:00), V3 C0242 @2169 (01:01:28:00), C0246 @2576 (01:01:44:15), C0255 @4167
    (01:02:49:09), C0261 @5038 (01:03:22:17). Alle anderen Items der Kopie tragen den alten Grade.
  - Für die Standbilder V4 (Adjustment Clip) und V5 (Grafik) der Kopie kurz aus, danach wieder an; Bin „Fast"
    unverändert; Projekt gespeichert.
- **Befunde:**
  - Node-Rechnung stimmt: `ExportLUT` (Color-Seite) gegen Modell Mittel 0,15–0,25 / p95 0,6–1,2 8-Bit-Stufen.
  - **Ausgabe Rec.709-A:** Resolve-Standbild = LUT-Ausgabe^(2,4/1,961) (Fehler 1,1 Stufen; ohne diese Wandlung 12,4;
    Hypothese Video-Pegel am Eingang 11,7). Mit Wandlung Gegenprobe ΔE2000 Median 0,47–0,78 an allen 8 Items. Die alte
    Rechnung (15.09.) kannte die Wandlung nicht; Apple-Wiedergabe gleicht sie aus, Windows/Android/viele Browser zeigen
    die Dateien dunkler und kontrastreicher.
  - `ExportCurrentFrameAsStill` auf der Color-Seite enthält die Begradigen-Transforms (Ausrichtung per SIFT nötig).
  - B-Roll C0261/C0242 im Original ≈ 2 Blenden unterbelichtet (S-Log3 Mittel 0,27) → Grenze +2 Blenden greift.
  - Mischlicht C0246: globaler Weißabgleich über den Hautwinkel ging schief (Haut-Chroma 50) → verworfen; Clip gelb,
    Gesicht von Hand.
- **Ergebnis (gemessen an den Resolve-Standbildern, Darstellung wie am Mac):** Schwarz (L\*≤3) bis 16 % → 0 %,
  Chroma p95 −2 bis −5, Hautwinkel Flammann 32° → 43°, Hein Haut L\* 76 → 65, Ludwig 58 → 62, B-Roll-Median L\*
  32 → 38–42; C0255 34 statt 38 (flacher, wirkt milchig); Fenster hinter Ludwig clippt 10 % (vorher 0).
- **Geliefert:** `_intern/autocut/grading/test_2026-09-17/` — `kontaktbogen_test_bisher_neu.jpg`,
  `look_varianten_test.jpg`, `gegenprobe_prototyp_709A.json`, `gegenprobe_prototyp.json`, `stills/` (16 PNG, ≈ 400 MB),
  `exportlut_*.cube`, Test-DRX `T1…T3`. Prototyp-Skripte im Session-Scratchpad.
- **Offen:** Look-Variante wählen (A 0,95/0,90 · B 1,00/0,95 · C 1,05/1,00); Ausgabe-Farbraum Rec.709-A vs.
  Rec.709 Gamma 2.4 entscheiden (nur der User); Spec nachziehen (Rec.709-A im Modell, Mischlicht = Handarbeit,
  Lichterschutz-Bezug, B-Roll-Grenze/Bild-Anker, Stills mit Transform); Test-Kopie behalten oder löschen (eigenes
  Objekt, nur auf Wunsch).

## 2026-09-17 11:10 — Session: Grading Look C auf alle Clips der Test-Kopie

- **User-Entscheidungen:** Look **C** (Node 03 Kontrast 1,05 um 18 % Grau, Sättigung 1,00); Ausgabe bleibt **Rec.709-A**;
  „kannst alle so machen" → alle Clips der Kopie graden.
- **Messung neu mit Look C** (Prototyp, 10-Bit-Originale): 238 Bilder aus 25 Clips (je aktivem Einsatz 3), 202 mit Gesicht;
  Wert je Clip, eigener Einsatz-Wert bei > 0,7 Bl. bzw. > 0,3 Bl. — nur 3 Einsätze von C0261 (@2984, @3747, @5096).
  Deaktivierte a7-Stücke tragen den Clip-Wert. Node 02 (Angleich a7 → FX3) noch neutral.
- **Resolve („Taxodia 09.26", Kopie „AutoCut video-1-taxodia-weg 2026-09-17 1040 Grading-Test"):** 115 Items (V1 37, V2 49
  inkl. 35 deaktivierter, V3 29) mit 5-Node-Baum; Readback 115/115 ok (5 Nodes, Namen, LUT), 99 s, gespeichert. V4/V5 und
  das Original unberührt; Kopie ist aktive Timeline, Bin „Fast". Log `_intern/autocut/grading/test_2026-09-17/einsatz_alle_lookC.json`.
- **Werte je Clip (Belichtung in Blenden):** Interviews FX3_0222 +0,38 · FX3_0223 −0,53 · FX3_0228 −1,15 · a7_0118 +1,24 ·
  a7_0119 +0,73 · a7_0752 +0,14. B-Roll +0,05 (C0247) bis +2,00; **10 von 19 B-Roll-Clips an der Grenze +2**
  (C0237, C0240, C0242, C0250, C0252, C0253, C0255, C0257, C0260, C0261) — Material im Original deutlich dunkler belichtet.
- **Geliefert:** `uebersicht_alle_lookC.jpg`, `plan_alle_lookC.json`, `einsatz_alle_lookC.json`, Prototyp-Skripte in
  `_intern/autocut/grading/test_2026-09-17/prototyp_skripte/`.
- **Offen:** Abnahme im Viewer (V4-Adjustment-Clip wirkt beim Abspielen mit); A/B-Angleich (Node 02); C0246 Mischlicht =
  Hand; Fenster hinter Ludwig clippt; B-Roll an der +2-Grenze ggf. von Hand nachziehen; Hinweis „Mischlicht/Haut
  außerhalb" schlägt im Prototyp zu oft an (nur Hinweis, keine Korrektur); Spec-Nachtrag + Umsetzungsplan.

## 2026-09-17 11:40 — Session: Grading-Test — Blendengrenze aufgehoben, Fenster Ludwig geprüft

- **User:** „Hebe die Blendengrenze auf, ich kann später ja NR drauf machen"; Frage nach dem ausgebrannten Fenster und
  nach Power Windows.
- **Neu gemessen ohne ±2-Grenze** (Look C, Cache): B-Roll jetzt C0237 +3,12 · C0255 +3,08 (Einsatz @4167 eigener Wert
  +1,50) · C0261 +2,96 (@710 +1,33, @2984 +3,02) · C0253 +2,94 · C0260 +2,90 · C0252 +2,75 · C0242 +2,72 · C0250 +2,66 ·
  C0257 +2,46 · C0240 +2,16. Übrige Clips ±0,03 → nicht angefasst.
- **Resolve (Kopie „… 2026-09-17 1040 Grading-Test"):** Node 01 von 16 V3-Items neu gesetzt (`SetCDL` NodeIndex 1),
  16/16 ok, gespeichert. Vorher Baum-Prüfung je Item (5 Nodes, Namen, LUT, HAND leer) — alle unverändert; Resolve stand
  auf Edit, deshalb keine Werte-Prüfung per `ExportLUT`. Log `test_2026-09-17/einsatz_v2_ohne_blendengrenze.json`.
- **Fenster hinter Ludwig (FX3_0222):** im Sensor ausgebrannt — ein Kanal steht auf dem Clip-Plateau S-Log3 CV 891/892
  (≈ +6,1 Blenden über 18 % Grau, ≈ 10 % der Bildfläche), die anderen Kanäle bei CV 790–860, lokale Zeichnung im Median
  < 1 Codewert. Ein Power Window kann das Fenster nur grauer machen, keine Zeichnung zurückholen.
- **Power Windows:** keine API-Funktion; im DRX-Format enthalten (Parameterfamilien 0x085…, 0x08f…, 0x0885…, Matrizen
  0x883…–0x88f… in den PW-Nodes der Team-Grades), Bedeutung der Werte nur per Versuch auf der Kopie belegbar.
- **Offen:** Entscheidung Fenster (weiß lassen / leicht abdunkeln per Window-Test); NR auf der hochgezogenen B-Roll von
  Hand; Lichterschutz-Regel: Sensor-Clip je Kamera als Plateau erkennen (FX3 ≈ CV 891), ausgebrannte Pixel nicht
  als Grund zum Abdunkeln werten.

## 2026-09-17 12:20 — Session: Grading-Test — B-Roll mit linearer Belichtung (User-Feedback am Viewer)

- **User-Feedback (Screenshots Color-Seite):** C0261 Hand/Maus „zu dunkel"; C0237 Tippen „kaum Kontrast, Schwarz komplett zu
  hell gezogen"; C0253 BenQ „kaum Kontrast"; „Schatten zu dunkel"; „Farben ziehen sich komplett so durch, nur die Interviews
  sind on point".
- **Ursache:** Belichtung als CDL-Offset im S-Log3-Raum ist nur im Log-Abschnitt eine lineare Verstärkung; bei +2 … +3
  Blenden hebt sie den Schwarzpunkt (S-Log3-Schwarz CV 95 → ≈ 340) → milchig, flach, blasse Farben. Interviews (±1 Blende)
  unauffällig.
- **Neu nur für V3 (B-Roll), Interviews unverändert:**
  - Node 01 = **1D-LUT je Clip** (4096 Stützstellen, exakte S-Log3-Rechnung: linear × 2^(e + w_Kanal)), CDL in Node 01 neutral;
    LUTs unter `/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/NIRO Grading/Taxodia 09.26/` (19 Dateien,
    Name mit Werten).
  - **Ein Wert je Clip** (Einsatz-Sonderwerte kamen aus unterschiedlichen Messankern, nicht aus anderem Licht), WB je Clip.
  - Lichterschutz nur auf im Sensor nicht ausgebrannte Pixel (FX3/FX3A-Clip-Plateau CV 891), **Toleranz 5 %** — gewählt am
    Vergleich 2/4/5/8 % (`toleranz_vergleich2.jpg`); ohne Schutz überstrahlten C0254/C0257/C0262, mit 2 % blieben C0239/C0246/C0247
    dunkel. Kein Schatten-Toe (Flare-Regel ≤ 5 % unter L\* 5 schlug überall voll an → milchig, verworfen).
  - Belichtung je Clip: C0235 +1,18 · C0237 +3,18 · C0239 +1,32 · C0240 +2,18 · C0242 +2,76 · C0246 +2,71 · C0247 +0,76 ·
    C0249 +2,85 · C0250 +2,81 · C0251 +2,18 · C0252 +2,80 · C0253 +3,16 · C0254 +3,20 · C0255 +3,45 · C0257 +3,32 · C0259 +1,89 ·
    C0260 +2,91 · C0261 +3,09 · C0262 +1,30.
- **Resolve (Kopie „… 2026-09-17 1040 Grading-Test"):** 29/29 V3-Items: Node-01-CDL neutral + `SetLUT(1, …)`, Readback Pfad ok,
  gespeichert; Baum-Prüfung vorher ok (Seite Edit → keine Werte-Prüfung). Gegenprobe am Standbild C0252 (Abspielkopf des Users,
  nicht bewegt; Adjustment Clip ohne Grade, V5 leer): linear ΔE2000 Median 0,81 / p90 1,16, Quellframe 502 wie berechnet;
  Offset-Modell p90 5,68 → LUT wirkt als lineare Verstärkung.
- **Geliefert:** `uebersicht_broll_final.jpg`, `vergleich_offset_linear.jpg`, `toleranz_vergleich2.jpg`,
  `plan_broll_final_t05.json`, `einsatz_broll_final_lut1d.json`, Standbild `stills/final_C0252_441.png`.
- **Offen:** Sichtung durch den User; NR auf Clips ≥ +3 Blenden (C0237, C0253, C0254, C0255, C0257, C0261); Fenster in Gegenlicht-
  Szenen brennen aus (Handarbeit/Power Window); **LUT-Ordner fehlt auf anderen Rechnern** (Cloud-Projekt → Zweit-MacBook zeigt
  sonst fehlende LUTs); Interviews für Konsistenz später ebenfalls auf lineare Belichtung umstellen (Wirkung dort klein).
