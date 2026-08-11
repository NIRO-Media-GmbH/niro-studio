# Arbeitsanweisung: Aussagen-Zerlegung

**Eingabe:** ein abgeglichenes, **diarisiertes** Transkript (jedes Wort hat
`speaker` und Timestamps), plus die erkannte Datei-Interpretation
(`typ/bereich/name`).

**Ziel:** ein Pool einzelner, zitierfähiger **Aussagen** — ausschließlich vom
Interviewten.

**Sprecher-Trennung (ZUERST, kritisch):**
- Der Interviewer/die Interviewerin darf NIE ausgewählt werden und in keinem
  Clip hörbar sein. Die 2-kanaligen WAVs trennen die Stimmen NICHT (beide
  Stimmen sind in beiden Kanälen) — deshalb nutzen wir Scribe-Diarisation.
- Bestimme den **Interviewten** = i.d.R. der Sprecher mit der Selbstvorstellung
  („Ich heiße …/ich bin …") bzw. dem größten Redeanteil. Notiere diese
  Sprecher-ID.
- Baue Aussagen **nur aus den Wörtern dieses Sprechers**. Wörter anderer
  Sprecher (Interviewer, Übersprechen) werden verworfen.

**Regeln:**
1. Eine Aussage ist eine in sich geschlossene Sinneinheit — ein vollständiger,
   für sich stehender Gedanke (nicht Satzfragmente, nicht ganze Absätze).
2. Jede Aussage bekommt: `von`, `bis` (aus den Wort-Timestamps),
   `person` (= Name aus Datei-Interpretation), `bereich`, `quelldatei`,
   `text` (Wortlaut), `thema` (kurzes Label).
3. Setze `von`/`bis` auf die Wortgrenzen der ersten/letzten Wörter der Aussage.
4. Bevorzuge natürliche Schnittpunkte (Atempausen, Satzenden) — die Zeiten
   müssen in DaVinci als saubere Schnittkante taugen.
5. Lieber etwas großzügiger schneiden (kleiner Puffer am Rand) als zu knapp.
6. **Saubere Schnittkante:** In `[von, bis]` darf KEIN Wort eines anderen
   Sprechers liegen. Falls doch (Übersprechen/Rückfrage), Grenzen enger setzen
   oder die Aussage verwerfen.

**Ausgabe:** Liste von Aussagen im `Statement`-Format (siehe `models.py`).
Jede Aussage MUSS mit `verify_statement()` gegen das Transkript geprüft werden;
zusätzlich die Sprecher-Reinheit von `[von, bis]` prüfen (Regel 6). Markierte
Probleme vor der Weiterverarbeitung beheben.
