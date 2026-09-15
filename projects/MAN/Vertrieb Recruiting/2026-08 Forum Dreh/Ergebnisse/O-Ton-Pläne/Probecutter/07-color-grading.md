# Color: S-Log3 → Rec.709

## Warum das Material grau und flau aussieht

Beide Kameras haben in **S-Log3 / S-Gamut3.Cine** aufgenommen (steht so in
den Kamera-Metadaten, wir haben es geprüft). Log ist ein Aufnahmeprofil,
das möglichst viel Dynamik (Lichter UND Schatten) in die Datei rettet —
dafür sieht das Bild erst mal kontrastarm und entsättigt aus. Das ist
kein Fehler, sondern Rohmaterial: Du musst es einmal in den normalen
Videofarbraum **Rec.709** übersetzen. Danach wird gegradet.

Gute Nachricht: Das Material ist **10 Bit 4:2:2** — es verträgt kräftige
Korrekturen, ohne dass Farbverläufe zerbrechen. Und beide Kameras haben
dasselbe Profil, du kannst sie also gleich behandeln.

## Der Weg in Premiere (empfohlen: eine Einstellungsebene für alles)

- **1.** Lege eine **Einstellungsebene** („COLOR") auf die oberste Videospur über die komplette Timeline.
- **2.** Lumetri-Farbe auf diese Ebene. In **Basiskorrektur → Eingangs-LUT** die Liste aufklappen und die mitgelieferte Sony-Konvertierung wählen — sie heißt je nach Version z. B. **„SL3SG3CToLC-709"** (S-Log3/S-Gamut3.Cine nach 709). Tipp: in der Liste nach „SL3" oder „SLog3" suchen.
- **3.** Jetzt erst graden — in derselben Lumetri-Instanz unter der LUT oder als zweite Lumetri-Instanz: Kontrast, Weiß-/Schwarzpunkt, Sättigung, Weißabgleich.
- **4.** Einmal alle Szenen durchsteppen: Wirkt ein Clip anders (dunkler Innenraum vs. helle Halle), bekommt genau der Clip zusätzlich eine eigene kleine Lumetri-Korrektur direkt auf dem Clip — **unter** der Einstellungsebene wird zuerst gerechnet, das passt so.

:::merk
Reihenfolge ist alles: **erst Konvertierung (LUT), dann Look.** Die LUT
erwartet Log-Werte. Wenn du vorher an Kontrast oder Sättigung drehst,
rechnet sie falsch. Und: LUT nur EINMAL anwenden — doppelt konvertiert
sieht aus wie zu heiß gebadet (übersättigt, abgesoffene Schatten).
:::

## Kontrolle mit den Scopes (Lumetri-Bereiche einblenden)

- **Waveform (Luma):** Gesichter der drei grob zwischen **55 und 70**; nichts Wichtiges klebt an 0 oder 100.
- **Vektorskop YUV:** Hauttöne entlang der Hauttonlinie (der schräge Strich Richtung 11 Uhr).
- Augen-Check: Weiße Hemden/Wände neutral? MAN-Rot an Fahrzeugen satt, aber nicht neonfarben?

## Der Look fürs Video

- **Clean und natürlich** — Konzern-Recruiting, kein Music-Video: neutrale bis leicht kühle Tendenz, satte aber glaubwürdige Farben, Hauttöne natürlich.
- Kein starkes Teal & Orange, keine gecrushten Schwarzwerte, keine Vignetten-Dramatik.
- Referenz: Das Bild soll aussehen wie ein sehr guter, moderner Imagefilm — man darf NICHT sehen, dass gegradet wurde.

:::tipp
Schneller Qualitäts-Check am Ende: Springe wahllos in 5 Stellen des Videos
und achte nur auf die Gesichter. Wenn alle drei Personen in allen Szenen
gleich „gesund" aussehen, bist du durch.
:::
