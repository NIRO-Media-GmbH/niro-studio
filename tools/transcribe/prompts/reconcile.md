# Arbeitsanweisung: Transkript-Abgleich

**Eingabe:** Zwei Transkripte derselben Audiodatei — `scribe` (ElevenLabs) und
`whisper` — je mit Wort-Timestamps.

**Ziel:** EINE saubere, korrekte deutsche Fassung.

**Regeln:**
1. **Timestamps von Scribe sind der Anker.** Übernimm Scribes Zeiten; Whisper nur
   zur Korrektur von Wortfehlern, Eigennamen, Fachbegriffen und Lücken.
2. Wo beide übereinstimmen: übernehmen.
3. Wo sie abweichen: die plausiblere Variante wählen (Fachkontext,
   Grammatik, Vollständigkeit). Im Zweifel Scribe.
4. Keine Inhalte erfinden. Füllwörter/Versprecher dürfen bereinigt werden, aber
   der Sinn bleibt unangetastet.
5. Behalte pro Wort/Segment die Start-/Endzeit, damit spätere Aussagen exakte
   von–bis-Zeiten bekommen.

**Ausgabe:** bereinigter Fließtext + eine Wortliste mit Timestamps (als Grundlage
für die Aussagen-Zerlegung).
