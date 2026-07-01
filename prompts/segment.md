# Arbeitsanweisung: Aussagen-Zerlegung

**Eingabe:** ein abgeglichenes Transkript (mit Timestamps), plus die erkannte
Datei-Interpretation (`typ/bereich/name`).

**Ziel:** ein Pool einzelner, zitierfähiger **Aussagen**.

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

**Ausgabe:** Liste von Aussagen im `Statement`-Format (siehe `models.py`).
Jede Aussage MUSS mit `verify_statement()` gegen das Transkript geprüft werden;
markierte Probleme vor der Weiterverarbeitung beheben.
