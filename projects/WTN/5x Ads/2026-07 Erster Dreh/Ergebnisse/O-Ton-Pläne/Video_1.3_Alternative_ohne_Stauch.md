# Video 1.3 „30 Jahre WTN" — Alternativfassung ohne Gerhard Stauch

*Kundenwunsch Julia Schilpp (WTN) vom 12.08.2026: Gerhard Stauch möchte nicht im Video zu sehen sein. Basis ist die freigegebene Schnittfassung `1.3 2.wav` (58,5 s O-Ton, CTA bis 62,0 s; intern „Video 3 / 03-team-sicherheit"). Er ist an genau zwei Stellen zu sehen — beide werden durch andere O-Töne ersetzt, Aussage und Gesamtlänge bleiben erhalten. Nur 1.3 ist betroffen: in 1.1, 1.2, 1.4 und 1.5 kommt er nicht vor.*

## Änderungen

| # | Stelle in 1.3 | Raus / Rein | Person · Rolle · Quelle · Timecode | Wortlaut | Kommentar (NIRO) |
|---|---|---|---|---|---|
| 1 | 0:06,46–0:10,12 (3,66 s) | RAUS | Gerhard Stauch (Ehemaliger Ausbilder) · `Material/Audio/Interview_Ehemaliger Ausbilder.wav` · 02:30–02:52 (Teilstück) | „Wir bilden nicht aus, um sie danach auf die Straße zu setzen." | Kundenkommentar sitzt bei 0:07,4. Bild und Ton komplett raus. |
| 1 | 0:06,5–0:09,5 (3,06 s) | REIN | Milena (Werkzeugmechanikerin, Dreh-/Fräsmaschine) · `Material/Audio/Interview_Werkzeugmechaniker_Milena.wav` · 07:33,9–07:37,0 | „Man wird auch eigentlich übernommen nach der Ausbildung." | Trägt dieselbe Zusage (Übernahme) wie der Stauch-Satz, aber aus Azubi-Sicht. 0,60 s kürzer als die Lücke — Pause davor/danach wächst, alle folgenden Timecodes bleiben unverändert. |
| 2 | 0:41,58–0:47,98 (6,40 s) | RAUS | Gerhard Stauch (Ehemaliger Ausbilder) · `Material/Audio/Interview_Ehemaliger Ausbilder.wav` · 02:30–02:52 (Teilstück) | „Die Zukunft von WTN sind gute Auszubildende und aus diesem Grund bieten wir 'n sicherer Arbeitsplatz." | Kundenkommentar sitzt bei 0:43,0. Achtung: Das Overlay „Ein sicherer Arbeitsplatz" (45,4 s) ist wortsynchron auf diesen Satz gebaut und muss mit geändert werden (siehe unten). |
| 2 | 0:41,6–0:47,1 (5,52 s) | REIN | Eduard Weber (Teamleiter Drehen/Fräsen/CNC/CAD-CAM) · `Material/Audio/Interview_Teamleiter.wav` · 05:50,9–05:56,4 | „Die KI funktioniert nur dann, wenn du starke, intelligente, fleißige Menschen dahinter hast." | Zukunfts-Argument statt Übernahme-Zusage, starker Punkt Richtung Eltern. 0,88 s kürzer als die Lücke — Abbinder, Stats und CTA bleiben auf Timecode. |

## Bild

| # | Bildquelle | Sichtbare Person | Hinweis |
|---|---|---|---|
| 1 | Interview-Setup Ordner `Interview_Werkzeugmechaniker_Milena` (Dreh 09.06.2026, NIRO-SSD-02) | Milena, Werkzeugmechanikerin | Kamera-Clip zur WAV am NLE zuordnen und vor Nutzung im Clip verifizieren. |
| 2 | Interview-Setup Ordner `Interview_Teamleiter` (Dreh 09.06.2026, NIRO-SSD-02) | Eduard Weber, Teamleiter | Kamera-Clip zur WAV am NLE zuordnen und vor Nutzung im Clip verifizieren. |

## Overlays (Remotion, `tools/motion/src/clients/wtn/projects/team-sicherheit/scenes.ts`)

Nur ein einziges Overlay ist betroffen — alle anderen bleiben unangetastet, weil beide Ersatz-Takes kürzer sind als die Lücken und die nachfolgenden Timecodes damit stehen bleiben.

| Overlay | Alt | Neu |
|---|---|---|
| Highlight #4 | Start 45,4 s · „Ein sicherer Arbeitsplatz" · Betonung „sicherer" bei 47,34 s | Start 43,6 s · „Starke Menschen dahinter" · Betonung „Menschen" bei 46,1 s · Dauer 3,4 s |
| Unverändert | 1,6 s „Direkt Teil vom Team" · 12,4 s „Ein sicherer Ausbildungsberuf" · 19,5 s Chips „Vielfalt an Technologien / Vielfalt an Wissen" · 50,2 s Stat „30 Jahre WTN" · 52,4 s Stat „58 Ausbildungen" · 55,1 s CTA „Der nächste Platz wartet auf dich" | — |

## Prüfhinweise

- Das Sicherheits-Versprechen bleibt sichtbar im Video: Das Overlay „Ein sicherer Ausbildungsberuf" (12,4 s) und Eduard Webers O-Ton dazu (0:12,52–0:23,54) sind nicht betroffen.
- Beide Ersatz-Takes wurden gegen die Wort-Transkripte geprüft: Schnittbereich ist sprecher-rein, kein Interviewer im Bereich.
- Milenas Satz beginnt mit „Man wird auch eigentlich …". Sauber ist der Take nur ungeschnitten (3,06 s). Ein Binnenschnitt auf „Man wird übernommen nach der Ausbildung" (raus: „auch eigentlich", 0,70 s) ginge, bräuchte wegen des sichtbaren Sprungs aber eine B-Roll-Überdeckung. Empfehlung: ungeschnitten lassen.
- Längere Variante für Stelle 2, falls mehr Anlauf gewünscht ist: Eduard Weber · `Interview_Teamleiter.wav` · 05:48,2–05:56,4 (8,16 s) — „Die Maschinen, die Automationen, die KI funktioniert nur dann, wenn du starke, intelligente, fleißige Menschen dahinter hast." Passt noch in das Fenster bis zum Abbinder (0:50,76), lässt davor aber nur rund 1 s Luft.
- „BTN" in den Roh-Transkripten ist ein bekannter Verhörer der Transkriptions-KI für „WTN" — Milena sagt im Original „WTN".

## Offen

- **[CHECK Kunde]** „Man wird auch eigentlich übernommen nach der Ausbildung" ist Milenas persönliche Aussage zur Übernahmepraxis, keine von NIRO formulierte Zusage. Vor Veröffentlichung von WTN freigeben lassen.
- **Separat, nicht Teil dieser Fassung:** die Maschinenpark-Formulierung von Dirk Wessel bei 0:31,5–0:33,7 („weil wir einen sehr, sehr hohen Maschinenpark haben") aus dem Feedback vom 11.08.2026. Bleibt hier bewusst unverändert und wird eigenständig abgestimmt.
