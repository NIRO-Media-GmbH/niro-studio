import subprocess, json, numpy as np
from colorlib import *
m = [x for x in json.load(open("manifest.json")) if x.get("id") == "Hein_2"][0]
L = LUTDIR + "SLog3SGamut3.CineToLC-709.cube"
fr = m["FX3"]["src_frame"]; t = (fr - 0.25) / 25
esc = L.replace(":", "\\:").replace("'", "\\'")
cmd = ["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", m["FX3"]["proxy"], "-frames:v", "1",
       "-vf", f"scale=in_range=tv:out_range=pc:in_color_matrix=bt709:flags=bicubic+accurate_rnd+full_chroma_int,format=gbrpf32le,lut3d=file='{esc}':interp=trilinear",
       "-f", "rawvideo", "-pix_fmt", "gbrpf32le", "-"]
b = subprocess.run(cmd, capture_output=True, check=True).stdout
a = np.frombuffer(b, np.float32).reshape(3, 1080, 1920)   # planar G,B,R
ff = np.stack([a[2], a[0], a[1]], -1)
x = yuv_to_rgb(np.load("frames/Hein_2_FX3.npy"))
npy = apply_lut(x, load_cube(L))
d = np.abs(ff - npy)
print("ffmpeg lut3d vs numpy: mean abs diff %.5f  p99 %.5f  (8-bit Code: mean %.2f)" % (d.mean(), np.percentile(d, 99), d.mean() * 255))
print("mean RGB ffmpeg", ff.reshape(-1, 3).mean(0).round(4), "numpy", npy.reshape(-1, 3).mean(0).round(4))
