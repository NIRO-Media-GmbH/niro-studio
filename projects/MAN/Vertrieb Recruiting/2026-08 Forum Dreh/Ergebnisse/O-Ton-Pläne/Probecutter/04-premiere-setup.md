# Premiere einrichten

## Schritt für Schritt

- **1. Projekt anlegen** — lokal auf deiner Arbeitsplatte, Name: `MAN-Gesamtvideo_<DeinName>`.
- **2. Material importieren** — über den Medienbrowser den Übergabe-Ordner ansteuern und die Ordner **Interviews** und **B-Roll** importieren (Ordnerstruktur mitnehmen, dann findest du alles wie im Plan benannt).
- **3. Sequenz anlegen** — am einfachsten: eine FX3-Interviewdatei aus dem Projektfenster auf den „Neues Objekt"-Button ziehen. Ergebnis prüfen: **2160×3840 (Hochformat), 25 fps**. Das muss so bleiben.
- **4. Spuren sortieren** — bewährtes Layout: V1 = Interview (Sprecher), V2 = B-Roll, V3 = frei lassen (da kommen später Grafiken von NIRO drauf) · A1 = O-Ton (FX3), A2 = Musik.
- **5. Autosave prüfen** — Voreinstellungen → Automatisches Speichern, alle 5–10 min.

:::merk
Die Clips sind technisch quer aufgenommen und tragen ein Dreh-Flag
(rotation = 90°). Premiere liest das automatisch und zeigt alles hochkant
an — du musst nichts rotieren. Falls ein Clip doch quer erscheint:
Rechtsklick → Ändern → Filmmaterial interpretieren → Rotation auf 90°.
:::

## Wenn die Wiedergabe ruckelt

Das Material ist UHD in 10-Bit 4:2:2 (H.264, ~140 Mbit/s) — das fordert
den Rechner. In dieser Reihenfolge probieren:

- **1. Wiedergabeauflösung** im Programmmonitor auf **1/2** stellen (reicht meistens).
- **2. Proxies bauen:** Clips im Projektfenster markieren → Rechtsklick → **Proxy → Proxys erstellen** → ProRes Proxy. Encoding läuft im Hintergrund — derweil mit halber Auflösung weiterarbeiten, Proxy-Button in den Monitor legen.

## Ton-Grundregeln

- O-Ton kommt **immer von der FX3-Datei** (sauberes PCM 48 kHz). Der a7MK4-Ton ist nur Sync-Referenz.
- Beim Schneiden auf **Kopfhörern** arbeiten — die Interviews haben leise Regie-Zwischenfragen, die du sauber wegschneiden musst.
- Pegel-Ziel und Musik-Mix stehen im Musik-Kapitel; der Feinmix kommt am Schluss.

:::tipp
Leg dir die vier FX3-Interviewdateien als Erstes in den Quellmonitor und
klick die Timecodes aus dem Schnittplan einmal quer durch — nach 10
Minuten kennst du alle Stimmen und weißt, wie das Material klingt.
:::
