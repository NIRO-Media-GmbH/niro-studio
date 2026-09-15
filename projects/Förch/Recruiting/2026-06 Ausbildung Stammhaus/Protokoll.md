# Protokoll — Förch / Recruiting / 2026-06 Ausbildung Stammhaus

## 2026-07-21 — Projektanlage & Schnittplan-Start

**Gemacht:**
- Projekt angelegt (aus Platzhalter umbenannt): Projekt „Recruiting", Charge „2026-06 Ausbildung Stammhaus" (Drehdatum 30.06.2026, Stammhaus Neuenstadt).
- Konzept erhalten: 4 PDFs „Theo Förch – Recruiting-Videos" (Video-Konzepte AZ-A–AZ-M, Drehplan nach Drehort, Schienen-Strategie, Casting-Plan) → `Material/Konzept/`.
- Footage-Quelle (NUR LESEN): NAS `01_Kunden/Förch GmbH & Co. KG/02_Projekte/03_30.05.26/03_Medien/01_Footage/Sortiert/` — Interviews (6 Personen), Video spezifisch (AZ-A/B/C/F, 1 Wort 1 Bereich), B-Roll, Actioncam.
- Schnittplan-Workflow gestartet (WORKFLOW-Schnittplan.md).

**Entscheidungen/Offenes:**
- AZ-D/E im Konzept gestrichen (ersetzt durch F–L) — Lücke im Alphabet ist gewollt.
- AZ-M (Bewerbungsprozess, 3 HR-Personen): kein Footage gefunden — vermutlich nicht gedreht (Casting lief noch).
- Zwei Kameras: C99xx (Sony FX?) + a7MK4; Ton-Kamera wird per ffprobe/Pegel verifiziert.

## 2026-07-21 — Schnittplan komplett (gleiche Session)

**Gemacht:**
- Ton-Kamera per Pegelmessung verifiziert: **Interviews = a7MK4** (C99xx nur Scratch, bei Luis/Mia quasi stumm); „Video spezifisch" = FX3/C-Clips mit Direktton.
- 76 Clips transkribiert (ElevenLabs, 0 Fehler) → `_intern/transcripts_index.json`, `_intern/cache/`; Utterances (1.558) → `_intern/utterances.json`; Digests → `_intern/interviews_digest.txt`, `_intern/videospezifisch_digest.txt`.
- Kern-Erkenntnis „Video spezifisch": alle Werbespot-Sprechtexte (AZ-A/B/C) wurden live am Set von den Azubis gesprochen — Ads komplett aus O-Tönen schneidbar; Take-Picking mit Timecodes in den Plänen.
- Material-Analyse → `Ergebnisse/O-Ton-Pläne/00-material-analyse.md` (Wer-ist-wer, Abdeckungsmatrix, Sperren).
- 9 Schnittpläne gebaut (AZ-A/B/C + AZ-G–L): Langfassungen in `Dossier/`, Kompaktfassungen `video-1…9-*.md`; 39 Stichproben-Zitate gegen utterances.json verifiziert (0 Fehlschläge).
- Übersichtsseite + Anhang (Blooper/Extras) + PDF gerendert: **`Foerch-Recruiting-Schnittanweisungen.pdf`** (21 Seiten: Titel + 1 Übersicht + 9×2 + 1 Anhang — Budget eingehalten).

**Entscheidungen:**
- Wording-Änderungen vom Set übernommen (z. B. „Einkauf und Produktmanagement" statt „Procurement", „Real Talk" statt „keine Floskel", AZ-C-Outro mit „Also worauf wartest du?").
- Sperren definiert: Tobias-KI-Passage (09:44–10:28), Gehalts-Aussagen (Tobias/Emili), FX3_9930 „Partnermodell"; AZ-L-Ausland nur mit DHBW-Framing; keine SAP-/Data-Science-Captions (nicht belegt).

**Offen (für David/Kunde):**
- AZ-F: nur Hooks gedreht — HR-Talking-Head fehlt → Nachdreh oder Umbau. AZ-M: komplett offen.
- AZ-B-Hook-Entscheid (Kaltstart „Willkommen bei Förch" vs. Caption-Hook), AZ-H-CTA (Alisa hat keinen), Luis' Studiengangs-Name, Endcard-URLs, Sprecher-Identitäten der Ad-Takes im Bild.

## 2026-07-21 — Finalisierung: offene Punkte entschieden (David: „wähle du")

**NIRO-Entscheidungen in Pläne eingearbeitet, PDF neu gerendert (21 Seiten, Budget ok):**
- AZ-A: Hook A gesetzt; Doppellaufbahn-Animations-Beat entfällt im Hauptcut (Tempo), als Option dokumentiert.
- AZ-B: Hook = Pain-Caption („…keiner deinen Namen gemerkt?", Script-Hook-A-Wortlaut) über anonymer B-Roll + harter Cut auf Fabians „Willkommen bei Förch"-Kaltstart (Beat 1a/1b).
- AZ-C: Hook C (Paket, FX3_9859 mit Etikett); Hook B bleibt Alternative.
- AZ-H: CTA als Endcard-Caption (keine Nachvertonung); falls AZ-F-Nachdreh kommt, CTA optional mit einsprechen.
- AZ-J: Insert/Endcard sicher „Duales Studium IT (m/w/d)"; „Wirtschaftsinformatik" erst nach Kundenbestätigung.
- AZ-K: CTA 15:24-Version (grammatisch sauber); Insert-Schreibweise „Emili".

**Beim Kunden weiterhin offen:** Endcard-URLs, Luis' Studiengangs-Titel, Sprecher-Namen der Ad-Takes (Inserts), Nachdreh-Empfehlung AZ-F (HR-TH) + AZ-M beim nächsten Termin.

## 2026-07-21 — AZ-B-Opening umgebaut (David-Feedback nach Sichtung)

- Befund David: „Willkommen bei Förch"-Satz ist in keinem Take frontal in die Kamera (deckt sich mit Set-Regie in FX3_9917: „Dann schauen wir nicht in die Kamera" — Text lag neben der Kamera).
- Neu: Opening = Doppel-Caption (Pain „…keiner deinen Namen gemerkt?" → Antwort „Hier bist du nicht Azubi Nr. 487.") über anonymer bzw. persönlicher B-Roll; „Willkommen bei Förch" nur noch optional als Off-VO. Alle AZ-B-Sätze laufen als VO über Szenenbildern (script-konform, Hook war die einzige Direkt-Ansprache-Stelle).
- Fallback dokumentiert: 9918/9919/9922 auf frontale Momente prüfen. PDF neu gerendert (AZ-B weiter 2 Seiten, gesamt 21).

## 2026-08-06 — Abnahme-Check Leon V1 (Frame.io-Lieferung)

**Gemacht:**
- Leons V1-Schnitte geprüft (8 MP4s, `~/Downloads/Förch Leon V1/Förch Videos/`, Frame.io 18:25, alle verifiziert): alle 8 transkribiert (`_intern/leon_v1_transcripts.json`, Cache wiederverwendet) + Frames gesichtet (`_intern/work/leon-v1-frames/`), Skript `_intern/check_leon_v1.py`.
- Abgleich gegen die 9 Schnittpläne; auffällige Takes gegen `utterances.json` rückverifiziert.

**Befund kurz:** Berufe/Personen/Kernaussagen stimmen überall; ALLE Sperren eingehalten (keine KI-/Gehalts-Passagen, kein „Partnermodell", Ausland mit „Von der Hochschule aus", SAP nur bei Mia); Endcards einheitlich berufsspezifisch mit (m/w/d); AZ-J korrekt „Duales Studium IT" (nicht Wirtschaftsinformatik). Technik: 8× 9:16 4K/25fps.

**Nacharbeit/Klärung (Details im Chat-Bericht 06.08.):**
1. **AZ-B fehlt komplett** (9 Pläne, 8 Lieferungen) — bei Leon nachfragen.
2. **AZ-K CTA = falsche Take-Version** („…dich AUF eine praxisnahe… interessierst", Grammatikfehler; Plan-Entscheid war 15:24-„für"-Version) — wortgleich gegen Quellmaterial verifiziert.
3. **AZ-H Schluss-Take aus gesperrter Meta-Zone** („für mich persönlich ist es optimal, die optimale Lösung… natürlich auch Geld verdienen…") — Doppler + streift Gehalts-Tabu.
4. **AZ-C: Titel-Beat „Nach drei Jahren…" + „Also worauf wartest du?" fehlt** — ersetzt durch Tobias' Interview-CTA („…dann hörst du von uns", fremde Stimme im Ad-Outro).
5. Bereichs-Videos 38–51 s statt 60–75 s — Erklär-Beats fehlen (G: modern/digital + 2+1-Jahre + 300-€/Fallschirm; H: Studienaufbau/Bachelor/Machbar-Closer; J: Modell/Struktur; K: KAM-Story + Praktikums-Beat (HR-Wunsch); L: Theorie-Praxis-Hauptgrund/Patenmodell). Hooks überall Kaltstart statt Caption-Hook.
6. AZ-L-Endcard „Internationaler Handel" vs. O-Ton „internationaler technischer Handel" (Kundenbestätigung ausstehend — bekannter offener Punkt).
7. AZ-J-**Dateiname** enthält „(Wirtschaftsinformatik)" — vor Kundenversand umbenennen.
8. Reinhören: AZ-G 38,5 s („Hochregallager"? ASR hört „Robotiklager", Quellmaterial kennt nur Hochregallager), AZ-H 12-s-Satz endet evtl. ohne „zur Verfügung", AZ-K „ab-abwechslungsreich"-Stotterer, AZ-A Caption „AKTIVER TEIL DES TEAMS" (~15 s) sitzt über Lager-Szene vor passendem O-Ton (HAND./KOPF.-Captions nicht gesichtet).
9. Endcards ohne URL/QR („Bewirb dich in unter 1 Minute" ohne Ziel) — Endcard-URLs beim Kunden weiter offen.

## 2026-08-07 — Änderungsplan V1→V2 für Leon (PDF)

**Gemacht:**
- Material-Restbestand für David aufbereitet (Chat): pro Sprecher verfügbare, ungenutzte und gesperrte Passagen.
- **Neue Opening-Regel (David):** Bereichs-Videos starten nicht mehr mit der Vorstellung — Sekunde 0 = stärkste Aussage als O-Ton-Kaltstart, Vorstellung als Beat 2. In alle 6 Umbau-Kapitel eingearbeitet (G: 65.000 Stellplätze · H: Kochertürn-100.000 · I: SAP-bis-Apple-Salve · J: Glücksrad · K: „nur im Büro hocken? auf jeden Fall nicht" · L: Verantwortung).
- **`Ergebnisse/O-Ton-Pläne/Foerch-Recruiting-Aenderungsplan-V2.pdf`** (12 S.: Deckblatt + Übersicht + 9 Kapitel, AZ-B 2 S., Rest je 1 S.; [NEU]/[FIX]/[CHECK]-Zeilenfarben). Inhalte: alle Befunde vom 06.08. als konkrete Anweisungen mit V1-Fundstellen + Quell-Timecodes; AZ-B als kompletter Neuschnitt-Plan (Endcard im V1-Serien-System); Ziellängen zurück auf 60–75 s.
- Neue Sperren dokumentiert: Alisa 18:02–18:54 (Meta-Zone) und Emilis „auf…"-CTA-Takes.
- MD-Quellen des Änderungsplans: `_intern/work/aenderungsplan-v2/` (eigener Render-Ordner, Original-Pläne unangetastet; Render via `tools/transcribe/scripts/render_schnittplan_pdf.py`).

**NIRO-Entscheidungen im Plan (David informieren):** AZ-G-CTA hart nach „bei uns" (ohne „…hörst du von uns"); AZ-A-Team-Caption entfällt zugunsten HAND./KOPF.; AZ-L-Endcard vorläufig „Internationaler Technischer Handel" (= O-Ton) bis Kundenfreigabe; AZ-K-Benefits bleibt als Kürzungs-Puffer.

**Offen:** PDF an Leon senden + AZ-B-Fehlen ansprechen; Kundenpunkte unverändert (Endcard-URLs, Luis'/Fabians Studiengangs-Titel, Nachdreh AZ-F/AZ-M).
