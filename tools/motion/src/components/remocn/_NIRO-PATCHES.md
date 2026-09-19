# Lokale Anpassungen an Remocn-Komponenten

Die Dateien hier kommen byte-genau aus der Registry (`npm run remocn:add`).
Was wir bewusst geändert haben, steht hier — nach `--force` wieder anwenden.

| Datei | Änderung | Grund |
|---|---|---|
| `marker-highlight.tsx` | Prop `background?: string`, Standard `"transparent"` statt hart `"white"` am Root | Alpha-Overlays (ProRes 4444) und dunkle Szenen |
| `marker-highlight.tsx` | `{after}` in `<span style={{position:"relative", zIndex:1}}>` | Spring-Overshoot des Markers malte über die ersten Buchstaben des Folgetexts |

Stand: 19.09.2026
