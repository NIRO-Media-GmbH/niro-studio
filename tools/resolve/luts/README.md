# NIRO-Grading-LUTs (beide Macs, über das NAS)

Eigene LUTs, auf die Resolve-Grades verweisen — seit 17.09.2026 die **Belichtungs-LUTs der B-Roll** (Node 01 „BALANCE",
lineare Verstärkung in S-Log3, eine 1D-LUT je Clip). Spec: `docs/superpowers/specs/2026-09-17-autocut-grading-design.md`.

## Ablage

- **Gemeinsam (NAS):** `NIRO NAS/NIRO Productions/01_Projekte/03_Vorlagen und Tools/02_Davinci Resolve/LUTs/NIRO Grading/<Resolve-Projekt>/` — neben den Phantom-,
  FTF- und Artlist-LUTs des Teams.
- **Lokal (je Mac):** `/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/NIRO Grading/<Resolve-Projekt>/`.

Ein Grade speichert nur den relativen Pfad (z. B. `NIRO Grading/Taxodia 09.26/C0237_e+3.18_r+0.15_b-0.31.cube`); Resolve
liest ihn aus dem lokalen LUT-Ordner. Fehlt die Datei dort, zeigt das Cloud-Projekt die LUT als fehlend. Die lokale Kopie
hält Grades und Renders auch ohne NAS lauffähig.

## Abgleich — nur beim Arbeiten (User-Entscheid 17.09.2026, kein Hintergrunddienst)

    sh tools/resolve/luts_sync.sh

- Holt NIRO-LUTs vom NAS in den lokalen Resolve-Ordner und legt nur lokal liegende NIRO-LUTs aufs NAS.
- Löscht nie, überschreibt nur mit neueren Dateien, fasst nur `NIRO Grading` an. Ohne NAS: Hinweis, lokal bleibt alles.
- Läuft Resolve und gibt es `tools/autocut/venv`, aktualisiert das Skript die LUT-Liste im offenen Projekt; sonst in Resolve
  „Project Settings → Color Management → Update Lists" oder Resolve neu starten.
- **Claude ruft es vor jeder Arbeit in Resolve und nach jedem Grading selbst auf** (CLAUDE.md, Resolve-Regeln).

## Regeln

- Neue LUTs lokal nach `NIRO Grading/<Resolve-Projekt>/` schreiben und direkt danach abgleichen.
- Dateinamen einer verwendeten LUT nie ändern — die Grades verweisen darauf. Neue Werte = neue Datei.
- Kein Schreibrecht auf den LUT-Ordner: einmalig `sudo chmod a+w "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT"`.
- Die AutoCut-Regel „NAS nur lesen" hat genau hier ihre Ausnahme (nur dieser Ordner, nur über das Skript).
