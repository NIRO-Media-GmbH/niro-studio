# AutoCut-Grading: Vorlagen

- `NIRO_Basis_v1.drx` — selbst erzeugter 5-Node-Baum (`BALANCE → ANGLEICH → KONTRAST/SAT → LUT → HAND`, seriell, ohne
  Werte und ohne Vorschaubild). Per Skript: `TimelineItem.GetNodeGraph().ApplyGradeFromDRX(pfad, 0)`, danach Werte per
  `SetCDL` (NodeIndex 1–3) und `SetLUT(4, "Sony/SLog3SGamut3.CineToLC-709.cube")`. Von Hand: Color-Seite → Gallery →
  Import → Still auf den Clip anwenden. Am 17.09.2026 in Resolve 21.1 geprüft (Taxodia-Test-Kopie).
- Aufbau des DRX-Formats und Befunde: `docs/superpowers/specs/2026-09-17-autocut-grading-design.md` (Design 2 und Nachtrag).
- Belichtungs-LUTs der B-Roll liegen projektweise in `tools/resolve/luts/` (Abgleich auf beide Macs, siehe dortige README).
