# Protokoll — WTN / 5x Ads / 2026-07 Erster Dreh

## 2026-07-08 — Korrekturen an den 5 Animationen

**Gemacht:**
- Video 4 (Arbeitsbedingungen): Highlight-Overlay „Kein Konzern. Keine Nummer."
  (47,4–50,6 s) entfernt — WTN gehört zu einem Konzern, Aussage muss raus.
- Endslides vereinheitlicht: alle Headlines ohne Schlusspunkt. Nur Video 4
  war Ausreißer („Nicht wie überall. Sondern WTN." → ohne Schlusspunkt);
  Videos 1, 2, 3, 5 waren bereits korrekt und blieben unverändert.

**Geliefert:**
- `Ergebnisse/Renders/04-arbeitsbedingungen.mov` (ProRes 4444, Alpha, 9:16)
- Videos 1, 2, 3, 5: keine Änderung, kein Re-Render nötig.

**Entscheidungen:**
- Satzzeichen-Konvention Endslides: ohne Schlusspunkt (Mehrheitsstil).
- VO-Audio bleibt unangetastet (Entscheidung David): „Kein Konzern, keine
  Nummer" ist im Voiceover `Material/Voiceover/04-arbeitsbedingungen.wav`
  bei 47,7–49,6 s weiterhin gesprochen.

**Offen:**
- Der Satz muss noch aus dem VO raus (im Schnitt/NLE oder später als
  geschnittene WAV-Version). Wenn geschnitten wird, verschieben sich alle
  Overlays nach ~47 s um ca. 3,5 s → Timings anpassen und neu rendern.

## 2026-08-11 — WTN-Feedback Video 3 („30 Jahre WTN"): Dirk „hoher Maschinenpark"

**Gemacht:**
- Kundenkommentar analysiert: Dirk sagt „…einen sehr, sehr hohen Maschinenpark
  haben" — kein korrektes Deutsch. David will ohne KI-Überarbeitung lösen.
- Stelle lokalisiert: `Interview_Produktionsleiter.wav`, Take 03:27–04:06
  (Video 3, Beat 2). Wortgenaue Timecodes aus Scribe-Cache gezogen.
- Lösung gefunden, kein KI nötig: „also, einen sehr, sehr hohen Maschinenpark"
  ist ein Selbstkorrektur-Einschub. Schnitt Audio-out 03:52,9 (Ende
  „Maschinen") → Audio-in 03:55,2 (Anfang „haben") ergibt grammatisch sauberen
  Satz „…weil wir sehr, sehr viele Maschinen haben, wo man sehr, sehr viele
  Technologien … mitbekommt". Entfernt ~2,3 s.
- Alternativen geprüft: Ersatz-Take „sehr, sehr moderner Maschinenpark"
  (02:34–02:45) ist schon Abschluss von Video 2 UND im Imagefilm (Beat 6a) —
  Drittnutzung nicht empfohlen. „Fertigungstiefe" sagt nur Roland, nicht Dirk.

**Entscheidungen/Offenes:**
- Empfehlung an David übergeben (interner Cut, Optionen dokumentiert im Chat);
  Umsetzung im NLE durch Cutter steht aus.
- **Nachtrag 12.08.:** Im fertigen Schnitt von 1.3 steht bei 0:31,5–0:33,7 genau
  die unsaubere Variante („weil wir einen sehr, sehr hohen Maschinenpark haben") —
  der Cutter hatte „sehr, sehr viele Maschinen, also," bereits weggeschnitten.
  Der Fix muss also aus der Quelle neu geholt werden, nicht im vorhandenen Take.
  Auf Entscheidung David bewusst NICHT in die Stauch-Fassung gebündelt.

## 2026-08-12 — WTN-Feedback Video 1.3: Gerhard Stauch komplett raus

**Gemacht:**
- Kundenwunsch Julia Schilpp (2 Kommentare bei 0:07,408 und 0:43,048):
  Alternative ohne Gerhard Stauch, er will doch nicht zu sehen sein.
- Video identifiziert: „Video 1.3" = Kundennummerierung (`tools/motion/Videos/WTN/
  1.3 2.wav`, bytegleich mit `Material/Voiceover/03-team-sicherheit.wav`)
  = intern Video 3 „30 Jahre WTN".
- Person identifiziert: Gerhard Stauch = der „Ehemalige Ausbilder". Zwei Belege:
  in seinem eigenen Interview wird er angesprochen („Gerhard, red jetzt einfach"),
  und Milena nennt ihn namentlich („Der Gerhard Stauch hat sich noch vorgestellt").
  Er nennt seinen Namen nie selbst — daher stand er bis jetzt nur als Rolle drin.
- Beide Stellen im fertigen Schnitt exakt lokalisiert (über
  `_intern/animation-transcripts/03-team-sicherheit.words.json`, Wort-Transkript
  der Schnittfassung): 0:06,46–0:10,12 „Wir bilden nicht aus, um sie danach auf
  die Straße zu setzen." und 0:41,58–0:47,98 „Die Zukunft von WTN sind gute
  Auszubildende und aus diesem Grund bieten wir 'n sicherer Arbeitsplatz."
- Geprüft: Stauch kommt NUR in 1.3 vor — 1.1, 1.2, 1.4, 1.5 sind nicht betroffen.
- Ersatz-Takes gesucht und auf Sprecher-Reinheit geprüft (kein Interviewer im
  Schnittbereich).

**Geliefert:**
- `Ergebnisse/O-Ton-Pläne/Video_1.3_Alternative_ohne_Stauch.md` + `.pdf`
  (2 Seiten quer, Cutter-Format)
- Renderskript `_intern/work/render_aenderung_1_3.py`

**Entscheidungen (David):**
- Ersatz als **Mischung** statt einer Person: Stelle 1 → Milena
  `Interview_Werkzeugmechaniker_Milena.wav` 07:33,9–07:37,0 („Man wird auch
  eigentlich übernommen nach der Ausbildung.", 3,06 s); Stelle 2 → Eduard Weber
  `Interview_Teamleiter.wav` 05:50,9–05:56,4 („Die KI funktioniert nur dann, wenn
  du starke, intelligente, fleißige Menschen dahinter hast.", 5,52 s).
  Verteilt die Last auf zwei Stimmen und hält beide Kernaussagen.
- Maschinenpark-Fix vom 11.08. bewusst **nicht** mit eingebaut — wird getrennt
  abgestimmt, saubere Freigabe-Historie.

**Erkenntnisse:**
- Beide Ersatz-Takes sind kürzer als die Lücken (−0,60 s bzw. −0,88 s). Bewusst so
  gewählt: der Cutter lässt alle nachfolgenden Timecodes stehen, die Differenz geht
  in die vorhandenen Pausen. Dadurch bleiben Stats („30 Jahre" / „58 Ausbildungen")
  und CTA unangetastet — anders als beim Video-4-Umbau am 08.07., wo ein Schnitt
  alle Overlays verschoben hätte.
- Nur EIN Overlay muss mit: das Highlight bei 45,4 s „Ein sicherer Arbeitsplatz"
  war wortsynchron auf Stauchs Satz gebaut. Vorschlag neu: „Starke Menschen
  dahinter", Betonung „Menschen" bei 46,1 s, Start 43,6 s.
- Das Sicherheits-Versprechen bricht trotzdem nicht weg: Overlay „Ein sicherer
  Ausbildungsberuf" (12,4 s) + Eduard Webers O-Ton dazu bleiben unberührt.

**Offen:**
- [CHECK Kunde] Milenas „Man wird auch eigentlich übernommen nach der Ausbildung"
  ist eine Aussage zur Übernahmepraxis — vor Veröffentlichung von WTN freigeben
  lassen (ihre persönliche Aussage, keine NIRO-Zusage).
- Umsetzung im NLE durch Cutter + Remotion-Overlay #4 neu texten/timen und
  `team-sicherheit` neu rendern, sobald der neue Cut steht.
- Maschinenpark-Formulierung (11.08.) weiterhin offen, separat.
