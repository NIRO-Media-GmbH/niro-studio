# AutoCut als eigenständiges Produkt — Plan (Design-Spec)

Datum: 2026-09-22 · Status: **Entwurf zur Entscheidung, nichts umgesetzt** (Auftrag: „Setze noch nichts um, plane
erstmal") · Grundlage: Inventar des Repos vom 22.09., Auswertung der Token-Verbräuche aller Claude-Code-Sessions seit
21.07.2026, Web-Recherche zu Nutzungsbedingungen, Datenresidenz, Resolve-Scripting und Wettbewerb (Quellen am Ende).

## 0. Kurzfassung

- **Produkt:** Desktop-Werkzeug für Videoagenturen, die interviewbasierte Filme (Image, Recruiting, Erklärvideo,
  Reels) in DaVinci Resolve schneiden. Konzept und Material rein → sortierter Schnittplan → Rohschnitt- und
  Feinschnitt-Timeline in Resolve → Kantenprüfung → Kunden-Review. Nicht „noch ein Rough-Cut-XML", sondern der ganze
  Weg bis zur abnahmefähigen Timeline. Das kann heute kein Wettbewerber.
- **Architektur:** *Der Client misst und führt aus, die Cloud plant und entscheidet.* Lokale App („Bridge") für
  Medien und Resolve; NIRO-Cloud für Konten, Prompts, alle KI-Urteile, Regeln, Schwellen, Abrechnung. Ohne Server ist
  die App ein leerer Rahmen — das ist zugleich Kopierschutz und Schutz des Handwerkswissens.
- **KI:** ausschließlich über NIROs Anthropic-API-Konto (Commercial Terms), serverseitig, für den Kunden unsichtbar.
  Kein Claude Code beim Kunden, kein eigener Key des Kunden. Claude Opus 5 für Urteile; Batch-API und ggf. Sonnet 5
  für den Bild-Index. Das Claude-Abo (Max/Pro) darf dafür nicht benutzt werden.
- **Preis:** Abo mit inkludierten „Cuts" plus Nachkauf, Material-Indexierung je Drehstunde. Vorschlag 290 / 590 /
  1.190 € je Monat, Pilotpartner 249 €. KI-Kosten je Cut planbar 10–30 € (Produkt-Pipeline) statt 50–150 € (heutiger
  Chat-Betrieb, gemessen).
- **Weg:** 4 Wochen Validierung und Name → 2–3 Pilot-Agenturen im „Concierge"-Betrieb (NIRO fährt das Werkzeug für
  sie, gegen Geld) → parallel MVP-Bau (≈ 4–6 Monate) → geschlossene Beta Frühjahr 2027 → offener Vertrieb Q2 2027.
- **Vorher zu klären:** Der Name „AutoCut" ist besetzt (autocut.com, Premiere/Resolve-Plugin). Außerdem: MVP-Umfang,
  Pilotpartner, Preisniveau, Rechtsform, AGB/AVV/EULA.

## 1. Ausgangslage: was AutoCut heute ist

**Umfang.** `tools/autocut` hat 34.190 Zeilen: 9.687 Produktivcode (44 Module), 10.439 Tests (laufen ohne Resolve,
NAS und API-Key), 8.147 Feinschnitt-Vorlagen, 3.407 CLI-Skripte. Die eigentliche „Intelligenz" steht in Text:
`WORKFLOW-AutoCut.md` (1.104 Zeilen, 98 KB), vier Prompts (449 Zeilen), `defaults.yaml` mit kalibrierten Schwellen
(143 Zeilen) und `WORKFLOW-Resolve.md` mit dem gemessenen Verhalten der Resolve-API (262 Zeilen). Dazu 19.692 Zeilen
Specs und Pläne, die jede Entscheidung begründen.

**Arbeitsteilung heute** (Studio-Muster: Claude entscheidet, Code baut und prüft hart):

| Stufe | Deterministisch (Python, lokal) | Urteil (Claude) | Wo läuft das Urteil |
|---|---|---|---|
| 1 Rohschnitt | ffprobe, Sync per Kreuzkorrelation, Verify-Hash, Timeline-Bau, Readback | Cutlist: Take, In/Out, Sperren, Pausen | Chat-Session |
| 2 / 2b B-Roll-Index | Szenenwechsel, Frames, Kontaktbögen, Cache | Bildbeschreibung je Clip/Abschnitt | **API-Aufruf im Skript** (Opus 5, Structured Output, Caching, Token-Erfassung) |
| 3a B-Roll aus Auswahl | Auswahl-Timeline lesen, Grenzen prüfen, Brennweitenregel, Zoom, Readback | Sichtung der Kontaktbögen, Shot → Beat | Chat-Session (Vision) |
| 5 Finalisieren | True Peak, XML-Roundtrip, Pegel, Time Remap | fast nichts | — |
| 6 Feinschnitt | 60 Vorlagen: Ton, Musik, SFX, Grafik, Grading, Begradigen, Gesichts-Check | ANPASSEN-Tabellen (Änderungen, Musik-Plan, SFX-Plätze, Grading-Freitext) | Chat-Session |
| Kantenprüfung | 5 Messungen am Export (Schwarzbild, Schnipsel, Knackser, Tonloch, Wortkante) | Befund-Bilder beurteilen | Chat-Session (Vision) |
| Review | Render, Ablage, Kommentare holen | Kommentare klassifizieren, umsetzen | Chat-Session |

Stufe 3 (vollautomatische B-Roll-Verteilung) ist seit 09.09. ausgesetzt; produktiv ist 3a mit der Auswahl-Timeline des
Cutters. Stufe 4 (Profil) wurde nie gebaut. Die Feinschnitt-Vorlagen sind Kopiervorlagen ohne Tests.

**Gemessene Leistung.** Taxodia-Erklärvideo: Rohschnitt 28 Beats / 97 Items / 30 Marker mit exaktem Readback;
Rohschnitt → fertiger Feinschnitt in rund 2 Stunden Session; Kantenprüfung 6.845 Frames in 18 s. Dold: 23 Reels in
einer Nacht neu geschnitten, 440 Items gegradet. B-Roll-Index MEK: 461 Clips in 25 min.

**Gemessene Kosten** (Token aus den lokalen Session-Verläufen, zu API-Listenpreisen bewertet — die tatsächliche Zahlung
läuft heute übers Abo):

| Was | Tokens / Umfang | API-Gegenwert |
|---|---|---|
| Alle 130 Sessions seit 21.07. | — | ≈ 5.800 $ |
| 22 Sessions mit AutoCut-Bezug | — | ≈ 2.800 $ (Entwicklung und Produktion gemischt) |
| Eine Projekt-Session (Dold, Taxodia, MN Deko) | 1.000–1.900 Nachrichten, 400–700 Mio. Cache-Lese-Token | 250–520 $ |
| B-Roll-Index MEK (Stufe 2) | 1,6 Mio. Eingabe / 0,38 Mio. Ausgabe / 3,2 Mio. Cache | ≈ 20–40 $ |
| Index-Nachlauf MEK (Stufe 2b) | 0,48 / 0,11 / 1,84 Mio. | ≈ 6–17 $ |

Das Muster der Chat-Sessions ist teuer, weil jeder Werkzeugaufruf den gesamten Kontext erneut liest (bis zu 700 Mio.
Cache-Token je Session). Ein reiner Produktionslauf ohne Entwicklung liegt grob bei 50–150 $ je Video. Eine
Produkt-Pipeline mit gezielten Aufrufen kommt auf 10–30 $ (Abschnitt 4).

**Das Besondere, das ein Wettbewerber nicht in Wochen nachbaut:** die Regeln aus einem Jahr Kundenfeedback
(WORKFLOW), die kalibrierten Schwellen (Knackser-Faktor, Wortkanten, Kamerafaktoren, Zoom-Grenzen), die
Sony-Telemetrie mit Brennweitenregel, die fünf QC-Messungen, die Verify-Logik und die Liste dessen, was Resolve per API
*nicht* kann (Slip, Rippeln, Stereo Fixer, stumme AddTrack-Spur, Render-Absturz). Der übrige Code (ffprobe, Sync,
XML-Roundtrip, Kontaktbögen) ist Standardhandwerk.

**Lücken für Fremdkunden** (aus dem Inventar): fest verdrahtet sind 25 fps, das Spurlayout V1 FX3 / V2 a7IV / V3 /
A1, Start-TC 01:00:00:00, Kamerarollen `ton`/`kontext`, NIRO-Pfade; Telemetrie setzt Sony-rtmd voraus (FX3/a7 IV);
Stufe 6 hängt an Remotion-Grafik, Artlist/Envato-Musik, NIRO-SFX-Bins und NIRO-LUTs; der Kunde bräuchte heute zwei
API-Keys, ffmpeg, Xcode-CLT, Node, OpenCV. Für das Produkt muss all das entweder parametrisiert, mitgeliefert oder
weggelassen werden (Abschnitt 9).

## 2. Produkt, Zielkunden, Wettbewerb, Name

**Zielkunde:** deutschsprachige Videoagenturen und Produktionsfirmen mit 2–15 Leuten, die regelmäßig interviewbasierte
Unternehmensfilme, Recruiting-Videos, Erklärvideos und Reels produzieren und in **DaVinci Resolve Studio** schneiden.
Zwei-Kamera-Interviews plus B-Roll ist ihr Standardfall. Ihr Schmerz: 4–8 Stunden Cutter-Zeit je Video für Sichten,
Auswählen, Sortieren, Synchronisieren, Rohschnitt, Pegel, B-Roll-Verteilung und Review-Runden.

**Versprechen:** „Konzept und Material rein, abnahmefähige Timeline raus." Konkret: Aussagen-Pool und Schnittplan
aus den Interviews, Rohschnitt mit beiden Kameras synchron in Resolve, B-Roll nach Regeln aus der eigenen Auswahl,
Pegel, Kantenprüfung, Review-Link für den Endkunden, Kommentare werden umgesetzt. Rohmaterial verlässt den Rechner der
Agentur nicht.

**Wettbewerb (Stand 09/2026):**

| Anbieter | Was | Preis | Abgrenzung |
|---|---|---|---|
| Eddie AI | Rough Cut aus Transkript, Export als XML für Premiere/FCP/Resolve/Avid, Chat-Bedienung | Credits: 10 $ je 1.000; 3-h-Projekt ≈ 1.100–1.700 Credits (≈ 11–17 $); Pro 167 $/Monat | Liefert XML, keine Resolve-native Feinschnitt-Timeline, kein QC, kein Review-Kreislauf, keine Zwei-Kamera-Regeln |
| Threadline Studio | Rough Cut per Prosodie-Analyse, XML-Export | ab 95 $/Monat | wie oben, Nische Doku |
| AutoCut (autocut.com) | Plugin für Premiere/Resolve: Stille schneiden, Untertitel, Podcast-Multicam, B-Roll | 9,90–19,80 $/Monat | Werkzeugkasten für Creator, kein Konzept-getriebener Schnitt — **besetzt den Namen** |
| AutoPod / Podcast Multicam | Multicam-Schnitt nach Sprecher | 29 $/Monat / 59 $ einmalig | Podcast-Nische |

Niemand verbindet Konzept → Schnittplan → Resolve-Timeline → QC → Review. Das ist die Positionierung: das Werkzeug für
Agenturen, nicht für Creator; Preis entsprechend über Eddie, klar unter einem Cutter-Tag.

**Name:** „AutoCut" ist als Produktname in genau diesem Markt vergeben (Wortmarke prüfen, aber auch ohne Marke wäre
die Verwechslung fatal). Intern kann der Name bleiben; nach außen braucht es einen neuen — zu prüfen beim DPMA/EUIPO
und als Domain. Kriterien: deutsch und englisch aussprechbar, nicht „AI" im Namen, kein Bezug auf „DaVinci"/„Resolve"
(Marke von Blackmagic).

## 3. Architektur

### 3.1 Grundsatz: Client misst und führt aus, Cloud plant und entscheidet

```
 Rechner der Agentur                                  NIRO-Cloud
 ┌──────────────────────────────┐                     ┌──────────────────────────────────────┐
 │ Desktop-App (Bridge)         │   JSON, JPEG, PNG,  │ Konten, Freischaltung, Geräte, Sitze │
 │ · Login, Projektordner       │   komprimiertes     │ Job-Steuerung, Job-Tickets           │
 │ · ffprobe, Sync, Szenen,     │   Audio             │ Prompts, WORKFLOW-Regeln, Schwellen  │
 │   Frames, Kontaktbögen,      │ ──────────────────► │ KI-Urteile (Anthropic-API, NIRO-Key) │
 │   Telemetrie, True Peak,     │                     │ Transkription (ElevenLabs, NIRO-Key) │
 │   Kanten-Messung             │ ◄────────────────── │ Verify-Logik, Bauplan-Berechnung     │
 │ · Resolve-Steuerung          │   Transkript,       │ Review-Hosting, Kommentare           │
 │   (Bau, B-Roll, Ton, Render) │   Cutlist, Bauplan, │ Abrechnung, Kostenzähler je Kunde    │
 │ · Web-UI im Fenster          │   Pläne, Urteile,   │ Admin-Panel, Update-Server           │
 └──────────────────────────────┘   Konfiguration     └──────────────────────────────────────┘
```

Was rüber geht: Audio der Interviews (16 kHz mono, komprimiert), `media.json`, `sync.json`, Kontaktbögen (JPEG,
≈ 2600×1112), Befund-Bilder (PNG), Messwerte (JSON), Resolve-Readback (JSON), optional Review-Renders (≤ 1080p).
Was zurückkommt: Transkript und Aussagen, Schnittplan, `cutlist.json`, Bauplan (`timeline.json`), B-Roll-Plan,
Feinschnitt-Tabellen, Konfiguration je Job (Schwellen, Regeln), Urteile zu Befunden. Rohmaterial bleibt lokal.

Das entspricht genau der heutigen Trennung: Stufe 2/2b läuft schon so (Kontaktbögen → API → JSON). Neu ist, dass
auch Cutlist, B-Roll-Zuordnung, Feinschnitt-Tabellen, Kanten-Urteile und Review-Umsetzung als API-Schritte laufen, dass
`verify`, `timeline_model` und die Schwellen auf den Server wandern und dass eine Bedienoberfläche dazukommt.

Warum das die Anforderungen erfüllt:

- **Kein Claude Code beim Kunden:** Die KI ist ein Dienst im Server. Der Kunde sieht Fortschritt, Ergebnisse und
  Freigabepunkte, nie ein Modell, einen Prompt oder einen Token.
- **Nicht weitergebbar:** Ohne gültiges Konto, Gerät und Job-Ticket macht die App nichts. Kopieren nützt nichts.
- **Versteckt:** Prompts, Regeln, Schwellen, Verify- und Planungslogik existieren nur auf dem Server. Im Client
  liegen Messung und Resolve-Handgriffe — der nachbaubare Teil.

### 3.2 Die KI-Schicht: drei Optionen

| Option | Beschreibung | Vorteile | Nachteile |
|---|---|---|---|
| A „Agent in der Cloud" | Claude Agent SDK auf dem Server spielt die heutige Chat-Session nach (WORKFLOW als Prompt), Werkzeugaufrufe werden an die Bridge weitergereicht | Schnellster Weg zum Laufen; das WORKFLOW-Dokument ist fertig | Teuer (Kontext-Wiederholung, 50–150 $/Video), langsam (Stunden), schwer reproduzierbar, das WORKFLOW ist für einen mitlesenden Operator geschrieben, nicht für Kunden |
| B „Pipeline mit gezielten Aufrufen" | Jeder Urteilsschritt ist ein API-Aufruf mit Structured Output, Prompt-Caching, passendem Effort; wie Stufe 2/2b heute | Billig (10–30 $/Video), schnell, testbar, Prompts kurz und geheim | Mehr Umbau: die Regeln aus WORKFLOW und Prompts müssen je Schritt in System-Prompts übersetzt werden |
| **C „Pipeline plus begrenzte Schleifen"** (Empfehlung) | B als Grundgerüst; nur dort, wo Urteil und harte Prüfung sich abwechseln (Cutlist ↔ Verify, B-Roll-Plan ↔ Verify, Kanten ↔ Bilder), eine kleine Werkzeug-Schleife (Tool Runner, 5–15 Züge, festes Token-Budget) | Qualität der Iteration bleibt, Kosten und Laufzeit bleiben begrenzt; Operator-Momente werden zu UI-Freigaben | Die Schleifen brauchen Budget- und Zug-Grenzen und Tests |

Modellwahl je Schritt (alle über NIROs Commercial-API-Konto):

| Schritt | Modell | Effort | Bemerkung |
|---|---|---|---|
| Aussagen-Pool, Schnittplan, Cutlist, B-Roll-Zuordnung, Grafik-Review, Kanten-Urteil, Review-Umsetzung | Claude Opus 5 | medium–high | Hier steckt das Urteil, hier nicht sparen |
| B-Roll-Index 2/2b | Opus 5 → Test mit Sonnet 5 | medium | Größter Kostenblock; über **Batch-API** (halber Preis, Ergebnis in Minuten bis Stunden, Schritt ist ohnehin Hintergrund) |
| Kommentare klassifizieren, Formatprüfungen | Haiku 4.5 | — | Massenware |
| Nicht im Produkt | Claude Fable 5.1 | — | Doppelter Preis, 30-Tage-Speicherpflicht, Refusal-Handling — für Kundenware ungeeignet |

Managed Agents (Anthropic hostet Schleife und Sandbox) passen nicht: die Medien und Resolve sind lokal, die Sandbox
hätte nichts zu tun. Ein Anbieterwechsel (z. B. Bedrock für EU-Kunden, Abschnitt 8) wird durch eine dünne
Modell-Schnittstelle im Server offen gehalten.

### 3.3 Der Client: drei Optionen

| Option | Beschreibung | Bewertung |
|---|---|---|
| **1 Desktop-App mit Web-UI** (Empfehlung) | Tauri 2 (Rust-Hülle, klein, signiert, notarisiert) lädt die React-Oberfläche vom NIRO-Server; ein kompilierter Python-Sidecar (Nuitka) enthält Medien- und Resolve-Code | Fühlt sich wie *ein* Werkzeug an; UI sofort aktualisierbar ohne Release; Python-Code bleibt nutzbar; Rust-Hülle ist schwerer zu lesen als Electron/asar |
| 2 Web-App plus Menüleisten-Helfer | Browser-App und winziger lokaler Helfer für Medien und Resolve | Maximale Trennung, aber zwei Dinge für den Kunden, weniger „ein Tool" |
| 3 Workflow-Integration-Plugin in Resolve | Electron-Panel im Resolve-Fenster (nur Studio) | Schöner Einstieg für später; als Basis zu brüchig (BMD-Feature, Electron in Resolve, Medienarbeit bräuchte trotzdem einen Helfer) |

macOS zuerst (Apple Vision, swiftc, das gesamte heutige Werkzeug). Windows später: der Medienteil (ffmpeg, numpy,
scipy) ist portabel; Gesichts-Check und Personenmaske brauchen dort einen Ersatz (OpenCV/ONNX). Resolve-Scripting gibt
es nur noch in **Resolve Studio** (Blackmagic hat es mit 21.1 aus der Gratisversion entfernt) — der Kunde muss Studio
haben; Studio-Nutzer sind ohnehin die Zielgruppe.

### 3.4 Der Server

- Stack-Vorschlag: Python (FastAPI) für API und Job-Steuerung, weil der vorhandene Verify-/Planungscode Python ist;
  Postgres; Redis-Queue für Jobs; Objektspeicher (S3-kompatibel) für Uploads mit automatischer Löschung nach Job-Ende;
  WebSocket für Fortschritt. Hosting in der EU (Hetzner/Frankfurt oder vergleichbar).
- Job-Modell: `Charge` → `Job` (Stufe) → `Schritte` mit Ein-/Ausgaben und Kosten. Jeder KI-Aufruf schreibt
  `usage` (Eingabe, Ausgabe, Cache) und Modell in die Datenbank, wie `broll_index.py` das heute schon je Clip tut.
- Admin-Panel: Organisationen anlegen und freischalten, Sitze, Geräte, Kontingente, Kosten je Kunde, Job-Logs,
  Version sperren, Kunden sperren.
- Eval-Korpus: die bestehenden NIRO-Projekte (MEK, Taxodia, Dold, MN Deko, Craiss …) mit Schnittplänen, Cutlists,
  Kanten-Befunden und den Sterne-Bewertungen aus NIRO Review als Regressionstests. Jede Prompt-Änderung und jeder
  Modellwechsel (Sonnet statt Opus im Index) wird dagegen gemessen, bevor er live geht.

## 4. KI-Nutzung und Kosten

**Nutzungsbedingungen (geprüft):** Produkte für Dritte dürfen nur über die Commercial-API laufen. Das Claude-Abo
(Pro/Max) und Claude-Code-OAuth-Tokens sind für Drittprodukte ausdrücklich verboten. NIRO hat schon ein API-Konto
(Schlüsselbund „niro_autocut", genutzt von Stufe 2/2b). Für den Produktbetrieb: eigener Workspace, eigene Keys je
Umgebung (dev/prod), Rate-Limit-Stufe prüfen (parallele Kunden, Batch-Limits sind getrennt), Anthropic-DPA
unterschreiben.

**„Über unsere Tokens":** ja, genau so. Der Kunde bringt keinen Key mit (BYOK). Gründe: mit eigenem Key könnte er
die Aufrufe über einen Proxy mitschneiden und die Prompts lesen; die Marge auf die KI ginge verloren; Support für
fremde Konten; und es widerspricht dem Ziel, dass alles im Werkzeug bleibt. Intern wird jeder Aufruf dem Kunden
zugerechnet; nach außen gibt es „Cuts" und „Drehstunden", nie Tokens.

**Kosten je Cut in der Produkt-Pipeline** (Annahmen: 3 h Footage, zwei Interviews à 30 min, 400 B-Roll-Clips,
4-Minuten-Film, Opus 5 für Urteile; Token-Schätzungen aus den gemessenen MEK-Werten hochgerechnet):

| Schritt | Modell / Dienst | Größenordnung | Kosten |
|---|---|---|---|
| Transkription 1,5 h Audio mit Sprecherzuordnung | ElevenLabs Scribe v2 (0,22 $/h) | — | 0,35 $ |
| Aussagen-Pool + Schnittplan | Opus 5 | 0,15 Mio. Eingabe, 15 k Ausgabe | 1–2 $ |
| B-Roll-Index 2 + 2b, 400 Clips | Opus 5, **Batch** | 1,8 Mio. Eingabe, 0,45 Mio. Ausgabe, 4,4 Mio. Cache | 12–20 $ (online 25–40 $; mit Sonnet 5 Batch 5–8 $) |
| Cutlist + Verify, 2–3 Runden | Opus 5 | 0,2 Mio. Eingabe, 15 k Ausgabe | 1,5–3 $ |
| B-Roll-Zuordnung 3a + Sichtung Kontaktbögen | Opus 5 | 0,3 Mio. Eingabe inkl. Bilder, 20 k Ausgabe | 2–5 $ |
| Feinschnitt-Tabellen (Ton, Musik, Grafik, SFX) | Opus 5 | 0,2 Mio. Eingabe, 20 k Ausgabe | 1,5–3 $ |
| Grafik-Review + Kanten-Urteile (Bilder) | Opus 5 | 0,1 Mio. Eingabe | 0,5–1,5 $ |
| Eine Review-Runde | Opus 5 | 0,1 Mio. Eingabe, 10 k Ausgabe | 1–2 $ |
| **Summe je Cut** | | | **≈ 20–37 $ mit Opus-Batch-Index; ≈ 13–25 $ mit Sonnet-Index** |

Der Index ist der Kostentreiber und skaliert mit dem Drehmaterial, nicht mit der Anzahl Videos — deshalb wird er
gesondert abgerechnet (je Drehstunde) und je Charge nur einmal berechnet (Cache je Clip-Fingerprint existiert schon).
Weitere Videos aus derselben Charge kosten dann nur 8–17 $. Planungsgröße für die Kalkulation: **25 € je Cut**
konservativ, Ziel nach Optimierung **12 €**. Zum Vergleich: der heutige Chat-Betrieb liegt bei 50–150 $ je Video.

**Kostensicherung im Betrieb:** Kontingent je Kunde und Monat (hartes Limit plus Warnung bei 80 %), Token-Budget je
Job, Zug-Grenze je Schleife, Kostenschätzung vor jedem Index-Lauf (heute schon `--dry-run`), Abbruch-Regeln bei
Wiederholungsschleifen, tägliche Kostenübersicht je Kunde im Admin.

## 5. Geschäftsmodell und Preise

**Optionen:**

| Modell | Für den Kunden | Für NIRO | Bewertung |
|---|---|---|---|
| Reines Abo (Flat je Sitz) | Planbar, einfach | Kostenrisiko bei Vielnutzern, Fair-Use nötig | Zu grob für einen Kostentreiber wie den Index |
| Reine Nutzung (Credits ohne Abo, wie Eddie) | Niedrige Hürde | Umsatz schwankt, keine Bindung, passt schlecht zu freigeschalteten B2B-Konten | Für Creator-Markt, nicht für Agenturen |
| **Abo mit inkludierten Cuts + Nachkauf** (Empfehlung) | Planbar mit Puffer, versteht jeder | Grundumsatz plus Wachstum mit Nutzung, Marge steuerbar | B2B-üblich (Frame.io, Artlist, Adobe) |

**Einheiten:** *Cut* = ein Durchlauf für ein Video bis 8 min Ziel-Länge (Schnittplan, Rohschnitt, B-Roll, Ton,
Finalisieren, Kantenprüfung, bis zu drei Review-Runden); Reels unter 90 s zählen halb; ein neuer Schnittplan derselben
Charge ist ein neuer Cut. *Material-Indexierung* je Drehstunde, einmalig je Charge (inklusive Stunden je Tarif).

**Preisvorschlag zum Testen** (netto, Monat; Jahreszahlung −15 %):

| Tarif | Preis | Inklusive | Nachkauf | Zielgruppe |
|---|---|---|---|---|
| Pilotpartner (6 Monate, max. 5 Agenturen) | 249 € | 5 Cuts, 15 Drehstunden | 39 € / Cut | Feedback, Referenz, Preisbindung |
| Starter | 290 € | 4 Cuts, 12 Drehstunden, 1 Sitz | 59 € / Cut, 9 € / Drehstunde | Kleine Agentur |
| Studio | 590 € | 10 Cuts, 30 Drehstunden, 3 Sitze | 49 € / Cut, 7 € / Drehstunde | Kernkunde |
| Agency | 1.190 € | 25 Cuts, 80 Drehstunden, 8 Sitze, Grading-Profile, Priorität | 39 € / Cut, 5 € / Drehstunde | Größere Häuser |
| Enterprise | auf Anfrage | EU-Inferenz (Bedrock Frankfurt), SSO, AVV nach Kundenvorlage | | Konzern-Inhouse |

**Rechnung:** Bei 25 € KI-Kosten je Cut liegt die Rohmarge im Studio-Tarif bei ≈ 58 %, nach Optimierung auf 12 €
bei ≈ 80 %. Wertanker für den Kunden: ein Cut ersetzt 3–6 Stunden Cutter-Zeit (150–400 €). 20 Studio-Kunden ergeben
≈ 12.000 € Monatsumsatz bei ≈ 3.000 € KI-Kosten. Fixkosten ohne Personal ≈ 150–300 €/Monat (Abschnitt 10).
Die Zahlen sind Startwerte für die Preisgespräche in Phase 0, keine Festlegung.

**Abrechnung:** Stripe Billing (Abo, Nachkauf, Rechnungen mit USt-ID, SEPA), Guthaben und Verbrauch in der App
sichtbar, Nachkauf mit einem Klick.

## 6. Login, Weitergabeschutz, Schutz vor Nachbau

**Konten und Freischaltung**

- Nur auf Einladung: NIRO legt die Organisation im Admin an, lädt den Admin der Agentur ein; jeder weitere Sitz wird
  vom Agentur-Admin eingeladen und zählt gegen das Kontingent. Registrierung ohne Einladung gibt es nicht.
- Login: E-Mail + Passwort (Argon2), optional TOTP/Passkey; Sitzungs-Token kurzlebig, Refresh-Token rotierend;
  Sperren und Abmelden aller Geräte aus dem Admin.
- Geräte: Beim ersten Start erzeugt die App ein Schlüsselpaar in der Keychain (Secure Enclave), das Gerät wird
  registriert; max. 2 Geräte je Sitz, 1 aktive Session je Sitz. Ein weitergegebener Login fällt sofort auf.

**Die App ist ohne Server leer**

- Jeder Lauf braucht ein signiertes, 15 Minuten gültiges **Job-Ticket** vom Server; Konfiguration, Schwellen, Pläne
  und Urteile kommen nur mit gültigem Ticket. Offline kann die App nichts außer Einstellungen anzeigen.
- Keine Geheimnisse im Client: Anthropic- und ElevenLabs-Keys existieren nur auf dem Server; Uploads über
  kurzlebige, signierte URLs.
- Versionsbindung: Der Server prüft Version und Signatur beim Start und lehnt veraltete Builds ab (Zwangs-Update).
  Kunden-ID im Build als Wasserzeichen, damit ein geleaktes Binär zuordenbar ist.
- Signiert und notarisiert (Apple Developer Program), Auto-Update über signierte Pakete.

**Schutz vor Nachbau — ehrlich eingeordnet**

- Alles, was Handwerkswissen ist, bleibt auf dem Server: WORKFLOW-Regeln, Prompts, `defaults.yaml`-Schwellen,
  Verify-Logik, Bauplan-Berechnung, Zuordnungsregeln. Der Kunde sieht Ergebnisse, nie Regeln.
- Was im Client liegt (Messung, Resolve-Steuerung), ist kompiliert (Nuitka → natives Binär in einer Rust-Hülle) und
  entspricht dem Teil, den das Inventar als „in Wochen nachbaubar" einstuft. Ein entschlossener Entwickler kann es
  analysieren; er bekommt dabei aber keine Regeln und keine Prompts.
- Zweite Stufe (nach dem MVP): Auch die Resolve-Handgriffe als serverseitig erzeugte Operationsfolgen (JSON)
  ausliefern; der Client wird dann zum generischen Ausführer mit den Timing-Regeln („nie schreiben, während
  abgespielt wird"). Dann ist praktisch nichts Nachbaubares mehr im Client.
- Rechtlich: EULA mit Reverse-Engineering-Verbot, Vertragsstrafe, Wasserzeichen; Marke eintragen.

## 7. Oberfläche

Eine Stepper-Logik entlang der Pipeline, in NIRO-CI, Dark Mode, deutsch/englisch:

1. **Projekt** — Kunde, Projekt, Charge; Zielformat (16:9/9:16), Bildrate, Kamerarollen (Ton-Kamera, Zweitkamera)
   werden aus dem Material vorgeschlagen und bestätigt.
2. **Material** — Ordner verbinden (NAS/SSD), Interviews und B-Roll erkannt, Proxies gefunden oder erzeugt,
   Telemetrie gelesen; Kostenvorschau „Indexierung: 3,2 Drehstunden".
3. **Aussagen & Schnittplan** — Transkripte, Aussagen-Pool mit Suche, Konzept-PDF hochladen, Schnittplan erzeugen,
   im Editor anpassen (Zeile je Aussage, Sperren, Bild-Hinweise), PDF exportieren.
4. **Rohschnitt** — „Resolve ist offen: Projekt X" wird geprüft, Bau mit Fortschritt, Bericht (Beats, Sync-Konfidenz,
   Warnungen), Timeline-Name.
5. **B-Roll** — Auswahl-Timeline wählen, Zuordnung mit Kontaktbogen-Vorschau je Beat, Abweichungen begründet,
   Einsetzen.
6. **Feinschnitt** — Ton-Pegel, eigene Musik (WAV) mit Musik-Plan, eigene Grafikdatei oder Platzhalter-Marker,
   Grading-Profil optional.
7. **Prüfung** — Kantenprüfung mit Befund-Bildern, Ein-Klick-Korrektur, erneuter Lauf.
8. **Review** — gehosteter Review-Link für den Endkunden (Frame-genaue Kommentare, Sterne), „Kommentare umsetzen" →
   V2; das bestehende NIRO Review (3.751 Zeilen, ohne Login, Port 4711) wird dafür zur mandantenfähigen Web-Version
   umgebaut — ein sichtbarer Mehrwert, den Agenturen sonst extra bezahlen (Frame.io).
9. **Konto** — Cuts und Drehstunden, Verbrauch, Team, Geräte, Rechnungen.

Jeder Freigabepunkt, an dem heute der User im Chat entscheidet (Cutlist abnehmen, B-Roll-Auswahl, Review), wird ein
Bildschirm mit Vorschau und „Weiter". Keine Chat-Oberfläche: Chat suggeriert Beliebigkeit und macht Kosten
unkontrollierbar. Ein Freitext-Feld „Anweisung für diesen Schritt" (z. B. „Hook mit Aussage 12 beginnen") reicht.

## 8. Recht und Datenschutz

- **Anthropic:** Commercial Terms, DPA abschließen; Anthropic wird Unterauftragsverarbeiter. Standard-API läuft in den
  USA (`inference_geo` kennt nur `us`/`global`, kein EU). Was übertragen wird: Transkripte (personenbezogen:
  Interviewte), Kontaktbögen mit Gesichtern, Befund-Bilder, Pläne — kein Rohmaterial. Datenminimierung: nur nötige
  Ausschnitte, Löschung der Uploads nach Job-Ende, keine Nutzung zum Training (Commercial-API-Standard).
- **EU-Option** für Kunden, die es brauchen: Claude über Amazon Bedrock in Frankfurt (eu-central-1) oder Vertex AI in
  EU-Regionen (Partner-Preise, Verfügbarkeit je Modell prüfen); Microsoft Foundry EU „coming 2026". Als
  Enterprise-Merkmal einplanen, nicht im MVP.
- **AVV/AGB/EULA:** NIRO ist Auftragsverarbeiter der Agentur; AVV nach Art. 28 DSGVO mit Unterauftragsverarbeitern
  (Anthropic, ElevenLabs, Hoster, Stripe); AGB mit Verfügbarkeit und Haftungsgrenzen; EULA für die App. Anwalt,
  einmalig 2–5 k€.
- **Blackmagic:** Nutzung der offiziellen Scripting-API ist erlaubt (viele kommerzielle Werkzeuge tun das); „DaVinci
  Resolve" nicht im Produktnamen, Kompatibilitätshinweis „für DaVinci Resolve Studio 21.1+" ist üblich.
- **ElevenLabs:** API-Nutzung im Produkt ist vorgesehen (Business-Terms prüfen, Kosten 0,22 $/h).
- **Marke:** Namensrecherche (DPMA, EUIPO, Domains), Anmeldung als Wortmarke (≈ 300 € DE, ≈ 850 € EU).
- **Struktur:** Anfangs als Produktlinie der NIRO Productions; bei Traktion eigene Gesellschaft/Marke (Haftung, Investoren,
  Fokus).

## 9. Was am Werkzeug geändert werden muss (Produktreife)

| Bereich | Heute | Für das Produkt |
|---|---|---|
| Parameter | 25 fps, FX3/a7IV-Layout, Start-TC, Kamerarollen fest | Projekt-Einstellungen: Bildrate, Auflösung, Spurlayout, beliebige zwei Kameras (oder eine), Start-TC |
| Pfade | `projects/<Kunde>/<Projekt>/<Charge>` unter NIRO Studio | Beliebiger Projektordner; `_intern` wird App-Cache |
| Telemetrie | Sony-rtmd Pflicht für Brennweitenregel | Optional; optischer Rückfall ist da; Brennweitenregel nur mit rtmd |
| Proxies | Erwartet `<Ordner>/Proxy/<stem>.mov` | Resolve-Proxies erkennen oder selbst erzeugen (ffmpeg) |
| Transkription | Zwei Keys beim User, faster-whisper lokal | Serverseitig über NIRO-Konto; kein Modell-Download beim Kunden |
| KI-Urteile in der Session | Cutlist, 3a, Feinschnitt-Tabellen, Kanten, Review | Als API-Schritte mit Structured Output und Verify-Schleife (Abschnitt 3.2) |
| Stufe 3 (automatische B-Roll) | ausgesetzt | MVP: nur 3a (Auswahl-Timeline); Stufe 3 als spätere Beta mit Telemetrie-Regeln |
| Stufe 6 Vorlagen | Kopiervorlagen ohne Tests, NIRO-Grafik/Musik/SFX/LUTs | Ton und Musik zuerst (kundeneigene WAV), Grafik als Datei/Platzhalter, SFX und Grading als spätere Module; Tests nachziehen |
| Grafik (Remotion) | 26 Kunden-Kompositionen | Nicht Teil des Produkts; später eigenes Add-on „Grafikpakete" |
| Kostenzähler | nur Stufe 2/2b | Alle Aufrufe, je Kunde und Job |
| Fehlerbilder | ~55-zeilige Tabelle im WORKFLOW | Werden zu Prüfregeln und UI-Meldungen mit Handlungsvorschlag |
| Umgebung | Homebrew, venv, swiftc, Node, OpenCV | Alles im Installer gebündelt (ffmpeg statisch, Python-Sidecar kompiliert, Swift-Helfer vorgebaut) |
| Schreibschutz in Resolve | Nur neue Bins/Timelines, Projektname = Freigabe | Bleibt; wird in der UI als „Freigabe für Projekt X" sichtbar |

## 10. Vorgehen, Aufwand, Kosten

**Phase 0 — Entscheiden und validieren (Oktober 2026, 4 Wochen neben dem Tagesgeschäft)**

- Name finden und prüfen; Domain sichern.
- 6–8 Gespräche mit Agenturen (Resolve-Studio-Nutzer, Interview-Filme): Ablauf zeigen (Bildschirmaufnahme eines
  echten Laufs, z. B. Taxodia), Preisbereitschaft abfragen (Tarife aus Abschnitt 5 als Vorlage), 2–3 als Piloten
  gewinnen.
- Anthropic: Workspace, DPA, Rate-Limit-Stufe; ElevenLabs Business; Anwalt beauftragen (AGB, AVV, EULA).
- Interner Vorlauf: Der Mitarbeiter, der gerade an NIRO Studio herangeführt wird, ist der erste „fremde" Nutzer —
  alles, was ihm erklärt werden muss, gehört in die Produkt-Liste (Abschnitt 9).
- Entscheidung Go/No-Go am Ende der Phase.

**Phase 1 — Concierge-Pilot (November 2026 bis Januar 2027)**

- NIRO fährt das heutige Werkzeug für 2–3 Pilotagenturen auf deren Material: sie liefern Footage, Konzept und
  Resolve-Projekt (Cloud-Projekt oder DRP), bekommen Timeline und Review-Link zurück. Preis z. B. 150–250 € je Video.
- Ergebnis: Belege, dass die Pipeline auf fremdem Material, fremden Kameras und fremdem Stil funktioniert; gemessene
  Kosten und Zeiten je Video; Referenzen; erste Einnahmen; Fehlerbilder, die im Produkt abgefangen werden müssen.
- Parallel beginnt der Bau des Servers (Konten, Jobs, Pipeline-Schritte) — die Concierge-Läufe werden nach und nach
  über den Server gefahren, damit die Pipeline-Schritte an echten Fällen reifen.

**Phase 2 — MVP (Dezember 2026 bis März 2027)**

| Baustein | Inhalt | Aufwand (Personentage) |
|---|---|---|
| Server-Kern | Konten, Freischaltung, Geräte, Job-Tickets, Queue, Speicher, Kostenzähler, Admin | 25–35 |
| Pipeline-Schritte | Transkription, Aussagen/Schnittplan, Cutlist+Verify, 3a-Zuordnung, Ton, Kanten-Urteil, Review-Umsetzung als API-Schritte; Eval-Korpus | 25–35 |
| Bridge-App | Tauri-Hülle, Python-Sidecar (Medien, Resolve), Installer, Signierung, Auto-Update, Parametrisierung aus Abschnitt 9 | 25–35 |
| Web-UI | Stepper aus Abschnitt 7, Review-Web-Version, Konto | 20–30 |
| Abrechnung, Recht, Betrieb | Stripe, Rechnungen, Monitoring, Backups, AVV/AGB-Einbau | 10–15 |
| **Summe** | | **105–150 PT** |

Mit Claude Code als Hauptentwickler (das heutige AutoCut mit 34 k Zeilen entstand in rund drei Wochen) sind die
Personentage eher Kalenderwochen bei halber Kapazität: realistisch **4–6 Monate** neben dem Tagesgeschäft, bei
Vollzeit 2–3 Monate. Geschlossene Beta mit den Piloten ab Februar/März 2027; Umstieg der Piloten von Concierge auf
Selbstbedienung.

**Phase 3 — Ausbau und Vertrieb (ab Q2 2027)**

- Feinschnitt-Module (Musik-Analyse, SFX, Grading-Profile), automatische B-Roll (Stufe 3 mit Telemetrie), Windows,
  Premiere über XML (nur Rohschnitt), EU-Inferenz, Workflow-Integration-Plugin als Komfort-Einstieg.
- Website, Fallstudien aus den Piloten, Demo-Videos, Vertrieb über das eigene Netzwerk, Resolve-Communities,
  Branchenverbände; Ziel 10–20 zahlende Agenturen bis Ende 2027.

**Laufende Kosten (ohne Personal)**

| Posten | Monat |
|---|---|
| Server, Datenbank, Queue, Speicher (EU) | 100–200 € |
| Monitoring, Fehlerberichte, E-Mail-Versand | 30–60 € |
| Stripe | 1,5 % + 0,25 € je Zahlung |
| Apple Developer Program | ≈ 8 € (99 $/Jahr) |
| Anthropic-API | variabel, 12–25 € je Cut |
| ElevenLabs | variabel, 0,22 $ je Audiostunde |
| **Fix gesamt** | **≈ 150–300 €** |

Einmalig: Anwalt 2–5 k€, Marke 0,3–1 k€, Design/Logo nach Bedarf.

## 11. Risiken und Gegenmaßnahmen

| Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|
| Qualität auf fremdem Material (andere Kameras, ein Interview statt zwei, keine Proxies, anderer Stil) | Enttäuschte Piloten | Concierge-Phase vor dem Produkt; Parametrisierung; Eval-Korpus; Kantenprüfung als Pflicht-Gate |
| Resolve-API ändert sich oder bricht (BMD hat gerade das Free-Scripting entfernt) | Ausfälle nach Resolve-Updates | Unterstützte Versionen festlegen und testen; Warnung in der App bei unbekannter Version; Fehlerbilder-Tabelle als Prüfregeln |
| Modellwechsel und Preisänderungen bei Anthropic | Kosten- oder Qualitätssprung | Modell-IDs festpinnen, Eval vor jedem Wechsel, Budget-Alarme, Modell-Schnittstelle für Bedrock/Vertex |
| Datenschutz-Einwände (US-Verarbeitung, Gesichter) | Verlorene Abschlüsse | AVV, DPA, Datenminimierung, Löschfristen, EU-Option als Enterprise-Merkmal |
| Name „AutoCut" | Verwechslung, Abmahnung | Vor jeder Außenkommunikation umbenennen |
| Support-Last durch Sonderfälle | Zeitfresser | Diagnose-Paket aus der App, Job-Logs am Server, Fehlerbilder mit Handlungsvorschlag, Piloten begrenzen |
| Fokus: Produktion vs. Produkt | Beides halb | Phasen mit Go/No-Go; Concierge bringt Geld, bevor gebaut wird; später eigene Einheit |
| Wettbewerb zieht nach (Eddie & Co.) | Preisdruck | Tiefe halten (Resolve-nativ, Zwei-Kamera, QC, Review); Piloten als Referenzen; schnell shippen |

## 12. Entscheidungen, die anstehen

1. **Name** für das Produkt (nicht „AutoCut").
2. **MVP-Umfang:** Empfehlung Schnittplan + Rohschnitt + 3a-B-Roll + Ton + Finalisieren + Kantenprüfung + Review;
   Musik, SFX, Grading, automatische B-Roll und Grafik später.
3. **Concierge-Pilot ja/nein** und welche 2–3 Agenturen.
4. **Preisniveau:** Studio um 590 € je Monat als Testhypothese.
5. **Client-Form:** Desktop-App mit Web-UI (Empfehlung) oder Web-App plus Helfer.
6. **Datenresidenz:** Anthropic-API mit DPA im MVP; EU-Inferenz erst als Enterprise-Merkmal.
7. **Struktur:** Produktlinie in NIRO Productions zuerst; eigene Gesellschaft bei Traktion.
8. **Zeitplan:** Phase 0 im Oktober, Go/No-Go Ende Oktober.

Nächster Schritt nach der Entscheidung: die Design-Spec für den Server-Kern und die Pipeline-Schritte (eigene Spec,
eigener Umsetzungsplan), plus die Namens- und Rechtsklärung aus Phase 0.

## Anhang A — Messwerte aus den Sessions (22.09.2026)

Auswertung der lokalen Claude-Code-Verläufe (`~/.claude/projects/-Users-jansantos-NIRO-Studio*`, 441 Dateien,
130 Sessions), Kosten zu API-Listenpreisen (Opus 5: 5 $/25 $ je Mio. Eingabe/Ausgabe, Cache-Lesen 0,50 $;
Fable 5: 10 $/50 $). Skript: `usage_scan.py` im Scratchpad dieser Session (nicht im Repo).

| Session (Datum) | Dauer | Nachrichten | Werkzeugaufrufe | Cache-Lese-Token | API-Gegenwert |
|---|---|---|---|---|---|
| Dold AutoCut (16.09.) | 24 h | 1.912 | 2.450 | 711 Mio. | 516 $ |
| „Mach weiter" (21.09.) | 27,5 h | 1.878 | 2.189 | 516 Mio. | 332 $ (Opus/Sonnet) |
| Taxodia (14.09.) | 22 h | 961 | 1.276 | 405 Mio. | 283 $ |
| MN Deko Aftermovie (17.09.) | 25,6 h | 677 | 660 | 394 Mio. | 244 $ |
| Dold Review-Runde (18.09.) | 4,4 h | 535 | 534 | 267 Mio. | 158 $ |
| MN Deko Review (21.09.) | 4 h | 474 | 478 | 188 Mio. | 135 $ |
| Wurst & Liebe Export (21.09.) | 1,9 h | 269 | 286 | 123 Mio. | 73 $ |

## Anhang B — Quellen

- Anthropic Consumer Terms / Commercial Terms und das Verbot von Abo-OAuth in Drittprodukten:
  https://www.anthropic.com/legal/commercial-terms · https://anthropic.com/legal/terms ·
  https://alternativeto.net/news/2026/2/anthropic-officially-bans-using-subscription-authentication-for-third-party-claude-use ·
  https://code.claude.com/docs/en/legal-and-compliance
- Datenresidenz (`inference_geo` nur `us`/`global`; Bedrock/Vertex EU; Foundry EU „coming 2026"):
  https://platform.claude.com/docs/en/manage-claude/data-residency · https://sonomos.ai/blog/claude-eu-data-residency-2026/ ·
  https://learn.microsoft.com/en-us/answers/questions/5867930/timeline-for-claude-in-microsoft-foundry-to-run-on
- Resolve 21.1: Scripting aus der Gratisversion entfernt:
  https://www.pugetsystems.com/blog/2026/09/10/how-davinci-resolve-free-v21-1-scripting-changes-affect-puget-bench/
- Eddie AI Preise und Credits: https://www.heyeddie.ai/pricing · https://www.redsharknews.com/eddie-ai-nab-2026-ai-video-editing-rough-cut
- AutoCut (autocut.com) Preise und Funktionen: https://www.autocut.com/en/pricing
- Threadline, AutoPod, Podcast Multicam: https://threadlinestudio.io/blog/best-ai-tools-rough-cuts-2026 ·
  https://www.premierecopilot.com/en/blog/best-ai-plugins-davinci-resolve-2026
- ElevenLabs Scribe v2 Preis (0,22 $/h): https://elevenlabs.io/pricing/api · https://developer.puter.com/tutorials/elevenlabs-api-pricing/
- Modellpreise Anthropic (Opus 5, Sonnet 5, Haiku 4.5, Fable 5.1): Claude-API-Skill, Stand 24.06.2026.

## Nachtrag 22.09.2026 — Preisprüfung, Wahrnehmung vs. Urteil, Repo-Trennung, nächste Schritte

**Preisprüfung.** Listenpreise gegen platform.claude.com/docs/en/about-claude/pricing geprüft: Opus 5 kostet 5 $ Eingabe,
6,25 $ Cache-Schreiben (5 min), 10 $ (1 h), 0,50 $ Cache-Lesen, 25 $ Ausgabe je Mio. Token; Batch halbiert. Alle
Sessions seit 21.07. komplett zu Opus-5-Preisen: 5.280 $ in 2,07 Monaten = 2.551 $/Monat, davon 67 % Cache-Lesen
(7,06 Mrd. Token, im Schnitt 280 k Token je Antwort). Das Abo bleibt intern die richtige Wahl; das Produkt muss die
Kontext-Wiederholung vermeiden, nicht das Modell wechseln.

**Wahrnehmung vs. Urteil.** 60–70 % der Kosten je Cut entfallen auf den B-Roll-Index — Beschreiben mit festem
Wortschatz, kein Urteil. Zielarchitektur: Index auf ein günstiges Vision-Modell (Gemini 3.8 Flash, 0,75 / 3,75 $, über
Vertex in EU-Regionen mit AVV) oder lokal auf dem Kunden-Mac (Qwen3-VL über MLX, 0 $ API, 30–60 min Rechenzeit);
Vorfilter aus Telemetrie (Wackeln, Schärfe) und dHash-Setups; zweistufig grob → fein; Opus 5 nur für Urteile
(Cutlist, B-Roll-Zuordnung, Feinschnitt, Review) mit knappem Kontext per Retrieval statt ganzer Transkripte.
Ziel **5–12 $ je Cut** bei unveränderter kreativer Qualität. Zweiter Urteils-Kandidat für den Eval: Gemini 3.1 Pro
(2 / 12 $). GPT-6 Astra (10 / 50 $) und GPT-5.6 Sol (5 / 30 $) bringen keinen Preisvorteil. Chinesische
Open-Weight-Modelle (GLM-5.x, Kimi K3, DeepSeek V4, Qwen 3.8) nur über EU-/US-Hoster mit Auftragsverarbeitung,
nie über die Hersteller-APIs; Selbsthosting erst bei großem Volumen. Preise sind volatil (Gemini Flash verdoppelt
sich zum 01.01.2027) → Modellschicht austauschbar, Entscheidung per Messung.

**Modell-Eval vor jeder Festlegung.** Korpus aus fünf Projekten (MEK, Taxodia, Dold, MN Deko, Craiss): angenommene
Cutlists und B-Roll-Pläne, Kanten-Befunde und die Sterne-Bewertungen aus NIRO Review als Referenz. Index-Kandidaten:
Opus 5, Sonnet 5, Gemini 3.8 Flash, Qwen3-VL lokal. Urteils-Kandidaten: Opus 5, Gemini 3.1 Pro. Kosten des Evals:
wenige Dutzend Dollar. Ergebnis: belastbare Kosten je Cut und belegte Modellwahl.

**Repo-Trennung (Entscheidung des Users, 22.09.).** Neues, privates Repo für das Produkt; NIRO Studio bleibt
unangetastet das Produktionswerkzeug und die Werkstatt. **Kein Neubau von null:** der `niro_autocut`-Kern (Medien, Sync,
Cutlist-Verify, Timeline-Modell, Resolve-API, Kanten, Telemetrie, Finalize, XML) und `niro_transcribe` werden als
Pakete mit ihren Tests übernommen und dort parametrisiert (fps, Spurlayout, Kamerarollen, Pfade — Standardwerte =
heutige Werte); WORKFLOW und Prompts werden je Schritt in Server-Prompts übersetzt. Vorgeschlagene Struktur:
`core/` (übernommene Pakete), `server/` (API, Jobs, Pipeline, Prompts), `bridge/` (Tauri + Python-Sidecar),
`web/` (React-UI), `evals/` (Korpus, Runner), `docs/`. Verbesserungen fließen an Versionsständen von Studio in den
Kern; das Produkt-Repo hält keine Kundendaten und keine NIRO-Projekte.

**Erster Durchstich statt Breite (4–6 Wochen nach Go).** Login → Projekt → Material verbinden → Transkription
(Server) → Cutlist als Pipeline-Schritt mit Verify-Schleife (Server) → Rohschnitt in Resolve (Bridge) → Review-Link.
Beweist Architektur, Kosten und Bedienung an einem echten Fall; danach B-Roll, Ton, Kantenprüfung, Abrechnung.

**Nächste Schritte Oktober 2026.**
1. Name, Domain, Markenrecherche (DPMA/EUIPO).
2. Eval-Korpus anlegen und Modellvergleich fahren (in NIRO Studio, nur lesend auf bestehende Chargen).
3. Anthropic-Workspace und Google-Cloud-Konto für das Produkt; Anthropic-DPA.
4. Demo-Video (Bildschirmaufnahme Taxodia-Lauf), 6–8 Agenturgespräche, 2–3 Pilotpartner.
5. Design-Spec für den Durchstich (Server-Kern, Pipeline-Schritt Cutlist, Bridge-Minimal, UI-Schritte 1–4).
6. Anwalt für AGB/AVV/EULA, Markenanmeldung.
7. Go/No-Go Ende Oktober; danach Concierge-Pilot zunehmend über den neuen Server-Pfad fahren.

**Ergänzende Spec (22.09., abends):** Bedienung, mehrere Schnittprogramme, Review-Modul, Installer, Preisrechner mit
Credits, Fremddienste, Sprachen, Skalierung → `2026-09-22-produkt-oberflaeche-plattform-design.md`.

**Nachtrag Wettbewerb (22.09., abends):** Die Recherche zu 20 Anbietern (Matrix, Tiefe, Preise, Quellen) steht in der
Produkt-Spec, Abschnitt 10. Kernbefund: Kein Anbieter liefert die Kette Konzept → Schnittplan → Feinschnitt im NLE →
Kanten-QC → Review mit KI-Umsetzung im Cutter-Projekt; Eddie AI v4 kommt am nächsten (Rough Cut, native .drp/.prproj,
Kommentar-„Spark", 12–16 $ je 3-h-Projekt). Marktkonform für unseren Umfang: 100–300 $ je Seat und Monat oder
50–150 € je Video — die Tarife aus Abschnitt 5 liegen darin. Größtes strategisches Risiko: native Assistenten von Adobe
(Premiere AI Assistant, Beta seit 06/2026) und Blackmagic (IntelliScript, SmartSwitch, MCP in 21.1).

**Nachtrag Entscheidungen (22.09., abends):** MVP mit automatischer B-Roll (Eingrenzung optional), Grafiken direkt
(eigene Dateien plus generierte aus dem Brand-Kit, keine Vorlagenbibliothek), Review lokal in versionierten Ordnern
statt Cloud, Mac zuerst, Resolve im Fokus, Preise wie vorgeschlagen, Fremddienste über NIRO-Konten, kein Concierge
vorerst, Produktlinie der NIRO Productions mit eigenem CI, Budget minimal. Zeitziel: interner Durchstich in 7 Tagen,
geschlossene Beta 6–8 Wochen später. Details und 7-Tage-Plan: Produkt-Spec, Abschnitt 13.
