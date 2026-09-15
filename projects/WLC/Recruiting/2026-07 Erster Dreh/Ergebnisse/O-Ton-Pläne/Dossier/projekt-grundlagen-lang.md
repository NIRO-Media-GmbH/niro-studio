# Projekt-Grundlagen (zuerst lesen!)

## Material-Speicherort

Alles Rohmaterial liegt auf dem NIRO NAS, Wurzelpfad:

`/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/WLC Würth Logistik GmbH & CO KG/02_Projekte/01_Projekt-Dreh18.05 & 20.05/03_Medien/01_Footage/`

Darunter genau zwei Standort-Ordner — das ist die wichtigste Grenze im Projekt:

| Ordner | Drehtag | Charakter | Farbe in diesem Dokument |
|---|---|---|---|
| `Adelsheim/` | 18.05. | gewachsener Standort, Verwaltung + Lager | BLAU |
| `Kupferzell/` | 20.05. | moderner Standort (FTS-Roboter, Neubau) | GRÜN |

Unterordner je Standort: `Interviews/` (Personen-Ordner), `Hooks/` (gescriptete Kurz-Takes), `B-Roll/` (Themen-Ordner), `Drohne/`, in Adelsheim zusätzlich `Reporter Video/`. Jeder Themen-Ordner enthält einen `Proxy/`-Unterordner mit Schnitt-Proxies. Der Ordner `Adelsheim/Interviews/Nicht verwenden/` heißt so, weil er nicht verwendet wird.

## Die Standort-Regel (nicht verhandelbar)

Jedes Video gehört zu genau EINEM Standort. In einem Adelsheim-Video darf **kein einziger Frame und kein Ton** aus Kupferzell vorkommen — und umgekehrt. Das gilt für O-Töne, B-Roll, Atmos, Drohnenbilder und Schnittbilder. **Einzige Ausnahme: Video 6** (Employer-Brand) mischt bewusst beide Standorte.

Faustregel zur Selbstkontrolle: Dateinummern `FX3_8585`–`FX3_8700` = Adelsheim, `FX3_8701`–`FX3_8774` = Kupferzell. Im Zweifel: Ordnerpfad prüfen — der Standort steht immer im Pfad.

Hintergrund (damit die Regel Sinn ergibt): Die Videos werden pro Standort regional targetiert. Kupferzell wirbt mit moderner Technik; Adelsheim ist älter und größer — Mitarbeiter erkennen ihr eigenes Lager. Falsches Material im falschen Video fällt dem Kunden und den Mitarbeitenden sofort auf.

## Kameras & Ton

- **FX3 (A-Cam):** einzige Kamera mit Ton. Alle O-Töne kommen aus `FX3_*.MP4`.
- **A7MK4 (B-Cam):** lief bei den Interviews parallel (`a7MK4_*.MP4` im selben Ordner), hat **keinen Ton** — als zweite Perspektive für Multicam/Schnittbilder nutzen, Ton immer von der FX3.
- Timecodes in den Szenen-Tabellen (`von–bis`, mm:ss) beziehen sich auf die Position **innerhalb der genannten MP4-Datei**.
- In fast allen Takes sind Regie-Anweisungen vor/nach dem eigentlichen Take zu hören — die angegebenen von–bis-Bereiche sind so gesetzt, dass der Take sauber steht. Trotzdem mit Luft anfahren und auf Atmer/Anschnitte achten.
- Der Interviewer ist **niemals** zu hören. Wo eine Antwort ohne Frage unverständlich wäre, steht in der Kommentar-Spalte, wie es zu lösen ist (Caption, Umstellung).

## Personen (wer ist wer)

| Person | Standort | Ordner | Rolle |
|---|---|---|---|
| Hamid | Adelsheim | `Interviews/Azubi 1` | Azubi 2. Lehrjahr, Fachkraft Lagerlogistik |
| Torben Kempf | Adelsheim | `Interviews/Azubi 2` | Fachkraft Lagerlogistik (junger Kollege/Azubi) |
| Sebastian Franke | Adelsheim | `Interviews/Teamleiter` | Teamleiter Halbautomaten, Quereinsteiger, betreut beide Schichten |
| Jana + Reporterin | Adelsheim | `Reporter Video/` | Kauffrau-Azubine + Hostin (Video 3) |
| Marvin | Kupferzell | `Interviews/Lagerleiter` | Gruppenleiter, 29, seit 9 Jahren bei WLC (Ex-Azubi → Fachwirt) |
| Sina Osterhag | Kupferzell | `Interviews/Ausbildungsleiterin` | Ausbildungsleitung (für alle Azubis) |

Hinweis: Torben ist auf Kupferzell-Material (`Hooks/Stapler`) ebenfalls zu sehen/hören. Diese Takes sind für die Adelsheim-Videos **gesperrt** (Standort-Regel); ihre Verwendung ist gesondert geregelt bzw. noch offen.

## Wording-Tabus (vom Kunden vorgegeben)

1. Kein **„whack"** und kein aggressives Jugend-Slang-Wording (Video 1) — freigegebene Alternativen: „langweilig", „lame", „uninteressant".
2. Kein **„Deutschland"-Framing** in Video 6 (weder Caption noch VO noch Map-Wording) — Konzern-Vorgabe.
3. In Captions/Grafiken **„Zeugnisprämie"**, nicht „Notenprämie".
4. Transkript-Schreibweisen wie „BLC", „Velzer", „WellSay" in den Zitat-Spalten sind Transkriptions-Hörfehler für **„WLC"** — die Sprecher sagen (meist) WLC. Wo die reale Aussprache undeutlich ist, steht ein Hinweis im Kommentar.

## Einheitliche Bausteine (alle Videos)

- **CTA-Endcard:** schwarzer Hintergrund, weiße harte Typografie. Headline „BEWIRB DICH JETZT." (Video 6: „WLC. WÜRTH-LOGISTIK."), Sub-Zeile je Video (siehe Szenen-Tabelle), Logo WLC + Würth-Gruppen-Anker dezent.
- **CTA-VO:** „Klick auf den Button, trag dich ein und wir melden uns bei dir." — liegt je Video als echter O-Ton der Protagonisten vor (Quelle in der Szenen-Tabelle).
- **Formate:** 9:16 vertikal, Master ~45–90 s (Video 3 als Reporter-Format bis ~2 min). Für TikTok-Cuts gelten die Kürzungs-Hinweise in den Kommentaren.
- **Untertitel:** durchgehend Burned-in-Subtitles für alle O-Töne (Social-Standard), Stil einheitlich über alle 6 Videos.

## Offene Projekt-Punkte (zentral geführt, blockieren den Rohschnitt nicht)

- Hochregal-Höhe **30 m vs. 36 m** — vor Finalisierung der Typo-Hooks klären (Videos 4/5).
- Konzern-Freigabe öffentlicher Zahlen (Mitarbeiterzahl 850 vs. 750+, Standort-Map) — Videos 5/6.
- Übernahmequote als konkrete Zahl (Video 2 Beweis-Card) — beim Kunden angefragt.
- Trend-Sound-Auswahl (Videos 1/2) — erst kurz vor Live-Gang fixieren (Halbwertszeit).
