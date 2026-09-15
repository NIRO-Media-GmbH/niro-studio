import numpy as np

L = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/Sony/"

def load_cube(path):
    size = None; dmin = np.zeros(3); dmax = np.ones(3); vals = []
    for line in open(path):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("LUT_3D_SIZE"):
            size = int(s.split()[1]); continue
        if s.startswith("DOMAIN_MIN"):
            dmin = np.array(list(map(float, s.split()[1:4]))); continue
        if s.startswith("DOMAIN_MAX"):
            dmax = np.array(list(map(float, s.split()[1:4]))); continue
        if s[0].isalpha():
            continue
        vals.append(list(map(float, s.split()[:3])))
    v = np.array(vals, dtype=np.float64)
    assert v.shape[0] == size**3, (v.shape, size)
    # cube order: R fastest -> index [b, g, r]
    return v.reshape(size, size, size, 3), dmin, dmax

def apply_lut(rgb, lut):
    n = lut.shape[0]
    x = np.clip(rgb, 0, 1) * (n - 1)
    i0 = np.floor(x).astype(int); i0 = np.clip(i0, 0, n - 2); f = x - i0
    r0, g0, b0 = i0[..., 0], i0[..., 1], i0[..., 2]
    fr, fg, fb = f[..., 0:1], f[..., 1:2], f[..., 2:3]
    c = lambda db, dg, dr: lut[b0 + db, g0 + dg, r0 + dr]
    c00 = c(0, 0, 0) * (1 - fr) + c(0, 0, 1) * fr
    c01 = c(0, 1, 0) * (1 - fr) + c(0, 1, 1) * fr
    c10 = c(1, 0, 0) * (1 - fr) + c(1, 0, 1) * fr
    c11 = c(1, 1, 0) * (1 - fr) + c(1, 1, 1) * fr
    c0 = c00 * (1 - fg) + c01 * fg
    c1 = c10 * (1 - fg) + c11 * fg
    return c0 * (1 - fb) + c1 * fb

def slog3_encode(x):
    x = np.asarray(x, float)
    return np.where(x >= 0.01125, (420 + np.log10((x + 0.01) / 0.19) * 261.5) / 1023,
                    (x * (171.2102946929 - 95) / 0.01125 + 95) / 1023)

if __name__ == "__main__":
    for name in ["SLog3SGamut3.CineToLC-709.cube", "SLog3SGamut3.CineToLC-709TypeA.cube",
                 "SLog3SGamut3.CineToCine+709.cube", "SLog3SGamut3.CineToSLog2-709.cube"]:
        lut, dmin, dmax = load_cube(L + name)
        print("==", name, "size", lut.shape[0], "domain", dmin, dmax)
        print("  corner [0,0,0]", lut[0, 0, 0].round(4), " [1,1,1]", lut[-1, -1, -1].round(4),
              " pure R in (1,0,0)", lut[0, 0, -1].round(3))
        for label, refl in [("0% black", 0.0), ("2% ", 0.02), ("9% ", 0.09), ("18% grey", 0.18), ("38%", 0.38), ("90% white", 0.90), ("180%", 1.8), ("500%", 5.0)]:
            full = float(slog3_encode(refl))
            legal = (full * 1023 - 64) / 876
            of = apply_lut(np.array([[full] * 3]), lut)[0]
            ol = apply_lut(np.array([[legal] * 3]), lut)[0]
            print(f"  {label:9s} full-in {full:.4f} -> {of.round(4)} | legal-in {legal:.4f} -> {ol.round(4)}")
        # where does neutral output reach ~0?
        xs = np.linspace(0, 0.3, 301)
        outs = apply_lut(np.stack([xs] * 3, -1), lut)[:, 1]
        nz = xs[np.argmax(outs > 0.002)]
        print("  neutral G output first > 0.002 at input", round(float(nz), 4), " output at 0:", outs[0].round(4))
