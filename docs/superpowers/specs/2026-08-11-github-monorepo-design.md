# NIRO Studio auf GitHub — Monorepo für das Werkzeug

**Stand:** 2026-08-11 · **Entschieden mit:** David

## Zweck

Das Werkzeug soll versioniert auf GitHub liegen, damit es im Team verteilt
werden kann und ein Festplattenausfall keine Arbeit vernichtet. Die
Arbeitsergebnisse sollen ausdrücklich **nicht** dorthin — weder als Upload
durch David noch versehentlich durch ein Teammitglied.

## Ausgangslage

Vier voneinander unabhängige Git-Repos ohne jedes Remote: die Studio-Wurzel
(9 Dateien) sowie `tools/transcribe`, `tools/motion` und `tools/photo`. Beim
Einlesen fielen drei Dinge auf:

- In `tools/motion` waren **sieben komplette Kunden-Ordner nie committet**
  (bumble-clean, foerch, hbl, niro, wlc, Teile von rem-maler) — Wochen an
  Arbeit, die nur auf einer Festplatte existierte.
- `public/clients/man/` enthält 5,2 GB Kundenvideo, dazu vier
  `public-<kunde>/`-Renderspiegel mit zusammen 4,1 GB. Die Videos griffen
  bereits bestehende `*.mov`/`*.mp4`-Regeln; die Spiegel waren ungeschützt.
- Die gesamte Schnittplan-Funktion (Workflow + zwei Skripte) war unversioniert.

## Entscheidungen

| Frage | Entscheidung | Begründung |
|---|---|---|
| Sichtbarkeit | Privat, NIRO-Media-Organisation | Lizenzierte Corporate-Fonts (MAN Global, Meutas, Robout) und Kundenlogos dürfen intern liegen, aber nicht öffentlich |
| Aufbau | Ein Monorepo | Team macht `git clone` und `git pull` — keine Submodul-Befehle, die erfahrungsgemäß die häufigste Fehlerquelle sind |
| Schreibrechte | Nur David | Entspricht dem Betriebsmodell: David pflegt das Werkzeug, das Team zieht Updates |
| Kunden-Kompositionen (Motion) | Kommen mit | Sind Code und die Substanz des Tools; ohne Marken-Definitionen startet ein Teammitglied bei null |
| Kunden-Looks (Foto) | Bleiben lokal | Je ~10 MB Binärdaten, aber vollständig reproduzierbar aus `make_look_lut.sh` + `NOTES.md` |
| Projekt-Specs in `docs/` | Wandern zum Projekt | Gehören zum Kundenauftrag, nicht zur Werkzeug-Doku |

## Aufbau

Ein privates Repo `niro-studio`. Die Trennlinie verläuft zwischen Werkzeug und
Arbeit:

```
niro-studio/
├── CLAUDE.md            Routing der fünf Funktionen
├── SETUP.md             Einrichtung von null auf lauffähig
├── .githooks/           Größensperre
├── docs/                nur Werkzeug-Architektur
└── tools/
    ├── transcribe/      Python: Interviews, Footage, Schnittpläne
    ├── motion/          Remotion: 15 Kunden mit CI, Fonts, Logos
    └── photo/           Skripte der ARW-Pipeline

projects/                ignoriert — existiert nach dem Klonen nicht
```

Dass Projektstände nicht hochgehen können, ist damit **strukturell** gelöst und
nicht bloß über Rechte: `projects/` ist ignoriert, also hätte selbst jemand mit
Schreibrecht nichts hochzuladen.

## Umbau

Die drei Sub-Repos wurden per `git merge -s ours` plus `git read-tree --prefix`
eingeschmolzen — die Index-Variante ohne `-u`. Weil die Dateien bereits am
Zielort lagen und die Sub-Repos sauber waren, entstand ein konsistenter Stand,
ohne dass eine einzige Datei angefasst wurde. `git subtree add` schied aus: es
verlangt ein leeres Zielverzeichnis, und ein Beiseiteräumen hätte 16 GB
ignorierter Inhalte bewegt.

`tools/photo` wurde bewusst **ohne** Ancestry importiert. Seine Historie
enthält die drei LUT-PNGs als Blobs; ein normaler Merge hätte die 30 MB durch
die Hintertür doch ins Repo geholt. Die alte Historie liegt als Bundle in
`~/NIRO-Studio-Backups/`.

Für `tools/motion` bleibt die Historie vollständig erhalten, obwohl darin noch
alte Voiceover-WAVs (~66 MB) liegen. Ein Rewrite hätte ein Zusatzwerkzeug
gebraucht und alle Commit-IDs geändert — für 66 MB nicht gerechtfertigt.

## Schutz vor versehentlichen Uploads

Zwei Ebenen, weil eine erfahrungsgemäß irgendwann durchlässig ist:

1. **`.gitignore`** — `projects/`, `public-*/`, Medien-Endungen (auch die
   Großschreibung `.MOV`/`.MP4` der Kameras), `venv/`, `node_modules/`,
   `.env`, `looks/**/*.png`, `bin/`.
2. **`.githooks/pre-commit`** — blockt jede Datei über 5 MB, Ausnahmeliste für
   die Corporate-Fonts. Aktivierung über `git config core.hooksPath .githooks`,
   dokumentiert in SETUP.md. Umgehbar mit `--no-verify`, aber dann bewusst.

Die zweite Ebene existiert, weil große Dateien nach dem Push nur noch mit einem
Rewrite der Historie zu entfernen sind — und der zwingt jeden im Team zu einem
Neuklon.

## Rückwege

- `~/NIRO-Studio-Backups/*.bundle` — die drei Sub-Repo-Historien, je in einer
  Datei, Stand vor dem Umbau
- `~/NIRO-Studio-Backups/*-dotgit` — die verschachtelten `.git`-Ordner im
  Original
- Tag `vor-monorepo-umbau` im Studio-Repo

## Bewusst nicht gelöst

- **Der Foto-Look ist einkundenfähig.** `make_look_lut.sh` trägt die Parameter
  des aktiven BumbleClean-Looks fest im Skript-Kopf. Beim zweiten Foto-Kunden
  müssen die Parameter pro Kunde ablegbar werden.
- **Fonts liegen im Repo.** Vertretbar, solange es privat und intern bleibt.
  Sollte das Repo je den Besitzer wechseln oder öffentlich werden, müssen sie
  vorher raus — inklusive Historien-Rewrite.
