"""NAS nach Audiodateien scannen (nur lesend) → data/nas_scan.tsv (Größe, mtime, Pfad)."""
import os

from config import AUDIO_EXT, DATA, EIGENE_LIBRARIES, NAS_ROOT

DATA.mkdir(exist_ok=True)
n = 0
with open(DATA / "nas_scan.tsv", "w", encoding="utf-8") as out:
    for dirpath, dirnames, filenames in os.walk(NAS_ROOT):
        dirnames[:] = [d for d in dirnames if not d.startswith((".", "#")) and d not in EIGENE_LIBRARIES]
        for fn in filenames:
            if fn.startswith("._") or os.path.splitext(fn)[1].lower() not in AUDIO_EXT:
                continue
            p = os.path.join(dirpath, fn)
            try:
                st = os.stat(p)
            except OSError:
                continue
            out.write(f"{st.st_size}\t{int(st.st_mtime)}\t{p}\n")
            n += 1
print(f"{n} Audiodateien gescannt")
