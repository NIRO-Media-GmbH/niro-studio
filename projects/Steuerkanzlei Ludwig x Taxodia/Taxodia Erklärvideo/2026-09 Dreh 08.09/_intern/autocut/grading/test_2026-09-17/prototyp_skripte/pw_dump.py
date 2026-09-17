import sys, glob, struct
sys.path.insert(0, '.')
import drx
from pb_raw import decode

def params(msg, pfad=""):
    """Alle (param_id, wert) aus Korrektur-Bloecken: Muster {1: id, 2: {..wert..}}."""
    out = []
    for fn, t, v in msg:
        if t == 'm':
            ids = [x for x in v if x[0] == 1 and x[1] == 'v']
            vals = [x for x in v if x[0] == 2 and x[1] == 'm']
            if ids and vals and ids[0][2] > 1000:
                out.append((pfad + f".{fn}", ids[0][2], vals[0][2]))
            out += params(v, pfad + f".{fn}")
    return out

files = sorted(set(glob.glob("/Users/jansantos/Downloads/*.drx") + glob.glob("/Users/jansantos/Desktop/**/*.drx", recursive=True)))
gesehen = set()
for f in files:
    t = open(f, encoding="utf-8").read()
    pb = drx.body_decode(drx.bodies(t)[0].group(1))
    g = drx.parse(drx.get(drx.parse(pb), 1)[0][2])
    for _, _, nb in drx.get(g, 7):
        n = drx.parse(nb)
        lab = drx.get(n, 6)
        label = lab[0][2].decode() if lab else ""
        if "PW" not in label.upper() and "WINDOW" not in label.upper():
            continue
        m = decode(nb)
        ps = params(m)
        sig = (label.strip(), tuple(sorted({hex(pid) for _, pid, _ in ps})))
        if sig in gesehen:
            continue
        gesehen.add(sig)
        print("=====", f.split('/')[-1][:30], "| Node", drx.get(n, 2)[0][2] if drx.get(n, 2) else None, repr(label))
        for pfad, pid, val in ps:
            print(f"   {pfad:<22} {hex(pid):<12} {pid:<11} {val}")
