# Erzeugt den Endcard-QR: EC-Level M, Quiet Zone 4 Module, dunkle Module
# auf weisser Platte. Skalierung so, dass die PNG-Kante >= 1000 px hat
# (Endcard 480 Design-px -> 960 echte px im 4K-Render, Downscale bleibt scharf).
import os
import segno

ZIEL = "https://jobs.man.eu/"
OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "..", "..", "..",
    "tools", "motion", "public", "clients", "man", "wz", "qr-jobs-man-eu.png",
)

qr = segno.make(ZIEL, error="m")
seite = qr.symbol_size(border=4)[0]          # Module inkl. Quiet Zone
scale = -(-1000 // seite)                    # ceil auf >= 1000 px
qr.save(OUT, kind="png", scale=scale, border=4, dark="#1a1a1a", light="#ffffff")
print("gebaut:", os.path.abspath(OUT), "module", seite, "scale", scale)
