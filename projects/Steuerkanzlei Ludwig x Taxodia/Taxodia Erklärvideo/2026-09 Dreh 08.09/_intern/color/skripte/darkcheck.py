import json, numpy as np
src = open("levels_check.py").read().split("for clip, frame in")[0]
ns = {}; exec(src, ns)
raw, planes, NAS = ns["raw"], ns["planes"], ns["NAS"]
faces = {l.split("\t")[0][:-4]: [list(map(float, p.split(","))) for p in l.rstrip("\n").split("\t")[1].split(";")] for l in open("faces.tsv")}
man = {m["id"]: m for m in json.load(open("manifest.json")) if "person" in m}
for fid, cam in [("Hein_2", "A7"), ("Hein_2", "FX3"), ("Ludwig_2", "A7"), ("Ludwig_2", "FX3")]:
    m = man[fid]; clip = m[cam]["clip"]; fr = m[cam]["src_frame"]
    d = "Kamera-A" if cam == "A7" else "Kamera-B"
    x0, y0, x1, y1, _ = faces[f"{fid}_{cam}"][0]
    W, H = 1920, 1080
    w, h = (x1 - x0) * W, (y1 - y0) * H; cx = (x0 + x1) / 2 * W
    ya, yb = int(y1 * H + 0.8 * h), int(min(y1 * H + 2.0 * h, H - 1)); xa, xb = int(cx - 0.8 * w), int(cx + 0.3 * w)
    bp = raw(f"{NAS}/{d}/Proxy/{clip[:-4]}.mov", fr, 25, "yuv444p", W, H, 8)
    yp, cbp, crp = planes(bp, W, H, W, H)
    sel = yp[ya:yb, xa:xb] < 60
    print(fid, cam, "PROXY  Y mean %.2f  Cb mean %.3f sd %.3f  Cr mean %.3f sd %.3f  frac Cb==128 %.2f" % (
        yp[ya:yb, xa:xb][sel].mean(), cbp[ya:yb, xa:xb][sel].mean(), cbp[ya:yb, xa:xb][sel].std(),
        crp[ya:yb, xa:xb][sel].mean(), crp[ya:yb, xa:xb][sel].std(), (cbp[ya:yb, xa:xb][sel] == 128).mean()))
    bo = raw(f"{NAS}/{d}/{clip}", fr, 25, "yuv422p10le", 3840, 2160, 10)
    yo, cbo, cro = planes(bo, 3840, 2160, 1920, 2160)
    Y = yo[2*ya:2*yb, 2*xa:2*xb]; Cb = cbo[2*ya:2*yb, xa:xb]; Cr = cro[2*ya:2*yb, xa:xb]
    s2 = Y < 60 * 1023 / 219 * 0 + (60 - 16) * 1023 / 219
    sC = s2[:, ::2]
    print(fid, cam, "ORIG   Y mean %.1f  Cb-512 mean %.3f sd %.3f  Cr-512 mean %.3f sd %.3f" % (
        Y[s2].mean(), Cb[sC].mean() - 512, Cb[sC].std(), Cr[sC].mean() - 512, Cr[sC].std()))
