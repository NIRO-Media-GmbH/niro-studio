import json, sys
import numpy as np, cv2
from PIL import Image, ImageDraw
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/vorlagen/feinschnitt/color/skripte")
sys.path.insert(0, ".")
import colorlib as CL
import proto_messung as PM
import proto_vergleich as PV

A = 2.4 / 1.961  # Ausgabe Rec.709-A: Code' = Code^(2.4/1.961)
werte = json.load(open("proto/werte.json"))
bericht = json.load(open(PV.TEST / "gegenprobe_prototyp.json"))

def gesehen_mac(still):          # Apple dekodiert 1.961 -> Licht wie 2.4-Referenz -> Code fuer L*-Rechnung (2.4)
    return np.clip(still, 0, 1) ** (1 / A)

def fuer_srgb_bogen(still):      # Licht = still^1.961, sRGB-Anzeige ~2.2 -> Code = still^(1.961/2.2)
    return np.clip(still, 0, 1) ** (1.961 / 2.2)

boxen = {}
import subprocess
out = subprocess.run([str(PM.FACES), str(PV.OUT / "faces_still")], capture_output=True, text=True, check=True).stdout
for z in out.strip().splitlines():
    n, _, r = z.partition("\t")
    boxen[n[:-4]] = [tuple(map(float, t.split(","))) for t in filter(None, r.split(";")) if t != "ERR"]

ergebnis = {}
zeilen = []
for key, e in werte.items():
    it = next(i for i in PM.ITEMS if i["key"] == key)
    f = it["still"]
    n = bericht["items"][key]["gegenprobe_neu"]["quellframe"]
    x = PM.decode(it["pfad"], n, it["fps"])
    modell = PM.render(x, e["werte"])
    modell_ausgabe = np.clip(modell, 0, 1) ** A
    s_neu = PV.still(PV.STILLS / f"neu_{f}.png")
    s_alt = PV.still(PV.STILLS / f"bisher_{f}.png")
    r, warp = PV.gegenprobe(modell_ausgabe, s_neu)
    kb = PV.kennwerte_still(gesehen_mac(s_alt), boxen.get(f"bisher_{f}", []))
    kn = PV.kennwerte_still(gesehen_mac(s_neu), boxen.get(f"neu_{f}", []))
    ergebnis[key] = {"werte": e["werte"], "gegenprobe_mit_709A": r, "gesehen_mac_bisher": kb, "gesehen_mac_neu": kn,
                     "hinweise": sorted({h for b in e["je_bild"] for h in b["hinweise"]})}
    zeilen.append((it, e, s_alt, s_neu, kb, kn, r, ergebnis[key]["hinweise"]))
    print(f"{key:<20} Gegenprobe dE Median {r['de2000']['median']:.2f} Mittel {r['de2000']['mittel']:.2f} p90 {r['de2000']['p90']:.2f} | dL {r['global_resolve_minus_rechnung']['dL']:+.2f}"
          f" | Mac bisher {kb} | neu {kn}")
json.dump(ergebnis, open(PV.TEST / "gegenprobe_prototyp_709A.json", "w"), indent=1, ensure_ascii=False)

W, H = 800, 450
bogen = Image.new("RGB", (2 * W, len(zeilen) * (H + 58) + 70), (16, 16, 16))
d = ImageDraw.Draw(bogen)
d.text((12, 10), "Grading-Test Taxodia 17.09. — BISHER | NEU (Node-Baum, Prototyp-Messung)", fill=(255, 255, 255), font=CL.font(24))
d.text((12, 40), "Resolve-Standbilder der Kopie, Darstellung wie am Mac (Rec.709-A). V4 Adjustment Clip und V5 Grafik aus.", fill=(190, 190, 190), font=CL.font(16))
for i, (it, e, s_alt, s_neu, kb, kn, r, hinw) in enumerate(zeilen):
    y0 = 70 + i * (H + 58)
    for c, img in enumerate((s_alt, s_neu)):
        bogen.paste(Image.fromarray(CL.to_u8(fuer_srgb_bogen(img))).resize((W, H), Image.LANCZOS), (c * W, y0 + 58))
    v = e["werte"]
    t1 = f"{it['clip']} @{it['still']}   Node 01: Belichtung {v['e']:+.2f} Bl., Rot {v['wr']:+.2f}, Blau {v['wb']:+.2f}"
    t2 = (f"Bild-Median L* {kb['median_L']} → {kn['median_L']}"
          + (f" | Haut L* {kb.get('haut_L')} → {kn.get('haut_L')}, Farbwinkel {kb.get('haut_h')}° → {kn.get('haut_h')}°, Chroma {kb.get('haut_C')} → {kn.get('haut_C')}" if "haut_L" in kn and "haut_L" in kb else "")
          + f" | Schwarz (L*≤3) {kb['anteil_L3']*100:.0f} % → {kn['anteil_L3']*100:.0f} % | Chroma p95 {kb['chroma_p95']} → {kn['chroma_p95']}")
    if hinw:
        t2 += "  ⚠ " + "; ".join(h for h in hinw if not h.startswith("Mischlicht") or "(" not in h or h == [x for x in hinw if x.startswith("Mischlicht")][0])
    d.text((10, y0 + 6), t1, fill=(255, 255, 255), font=CL.font(19))
    d.text((10, y0 + 32), t2, fill=(210, 210, 210), font=CL.font(15))
bogen.save(PV.TEST / "kontaktbogen_test_bisher_neu.jpg", quality=86)
klein = bogen.resize((bogen.width // 2, bogen.height // 2), Image.LANCZOS)
klein.save("proto/kontaktbogen_klein.jpg", quality=85)
print("ok", bogen.size)
