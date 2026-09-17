# NIRO-Grading-LUTs (beide Macs)

Eigene LUTs, auf die Resolve-Grades verweisen — seit 17.09.2026 die **Belichtungs-LUTs der B-Roll** (Node 01 „BALANCE",
lineare Verstärkung in S-Log3, eine 1D-LUT je Clip). Spec: `docs/superpowers/specs/2026-09-17-autocut-grading-design.md`.

## Warum im Repo

Ein Grade speichert nur den **relativen Pfad** der LUT, z. B. `NIRO Grading/Taxodia 09.26/C0237_e+3.18_r+0.15_b-0.31.cube`.
Die Datei selbst liegt in Resolves LUT-Ordner des jeweiligen Rechners. Fehlt sie dort, zeigt das (Cloud-)Projekt die LUT
als fehlend und die B-Roll ist wieder unkorrigiert. Deshalb ist dieses Verzeichnis die Quelle, und jeder Mac installiert
daraus.

    tools/resolve/luts/NIRO Grading/<Resolve-Projekt>/<Clip>_e<Blenden>_r<Rot>_b<Blau>.cube
      → /Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/NIRO Grading/<Resolve-Projekt>/…

## Automatisch

Die Git-Hooks in `.githooks/` (`post-merge`, `post-rewrite`, `post-checkout`) rufen nach jedem `git pull` (auch
`--rebase`) und Branch-Wechsel `sh tools/resolve/luts_sync.sh --nur-installieren` auf. Voraussetzung ist einmalig je Mac
`git config core.hooksPath .githooks` (SETUP.md, Schritt 2). Läuft Resolve und gibt es `tools/autocut/venv`, aktualisiert
das Skript die LUT-Liste im offenen Projekt selbst; sonst in Resolve „Project Settings → Color Management → Update Lists"
oder Resolve neu starten.

## Neue LUTs anlegen (egal auf welchem Mac)

1. LUT **ins Repo** schreiben: `tools/resolve/luts/NIRO Grading/<Resolve-Projekt>/…` (Werkzeuge tun das künftig selbst).
2. `sh tools/resolve/luts_sync.sh` — installiert sie in Resolve und holt umgekehrt NIRO-LUTs, die nur in Resolve liegen
   (z. B. von einem Prototyp-Skript), ins Repo.
3. Committen und pushen. Der andere Mac bekommt sie beim nächsten `git pull` automatisch.

## Regeln

- Das Skript **löscht nie** und überschreibt nur mit neueren Dateien; es fasst in Resolve nur `NIRO Grading/` an.
- Dateinamen einer verwendeten LUT nie ändern — die Grades verweisen darauf. Neue Werte = neue Datei.
- Kein Schreibrecht auf den LUT-Ordner: einmalig `sudo chmod a+w "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT"`.
