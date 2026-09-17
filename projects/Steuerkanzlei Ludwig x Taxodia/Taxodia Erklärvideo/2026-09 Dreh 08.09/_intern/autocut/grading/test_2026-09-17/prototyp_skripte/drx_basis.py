"""Prototyp: Test-DRX erzeugen (T1 = Vorlage neu verpackt, T2 = 5 Nodes mit Vorschaubild, T3 = 5 Nodes ohne Vorschaubild)."""
import re, sys, uuid, struct
sys.path.insert(0, '.')
import drx

VORLAGE = "/Users/jansantos/Downloads/Still 2026-08-29 171537_1.1.1.drx"
NAMEN = ["BALANCE", "ANGLEICH", "KONTRAST/SAT", "LUT", "HAND"]
t = open(VORLAGE, encoding="utf-8").read()
m_clip, m_track = drx.bodies(t)
pb = drx.body_decode(m_clip.group(1))
top = drx.parse(pb)
graph = drx.parse(drx.get(top, 1)[0][2])

# T1: identischer Inhalt, neu komprimiert
t1 = t[:m_clip.start(1)] + drx.body_encode(drx.build(top)) + t[m_clip.end(1):]
assert drx.body_decode(drx.bodies(t1)[0].group(1)) == pb

# Bausteine aus der Vorlage (leerer Node id 5)
leer = next(drx.parse(nb) for _, _, nb in drx.get(graph, 7) if drx.get(drx.parse(nb), 1)[0][2] == 5)
f9 = drx.get(leer, 9)[0][2]; f10 = drx.get(leer, 10)[0][2]; f12 = drx.get(leer, 12)[0][2]
g12 = drx.get(graph, 12)[0][2]; g2 = drx.get(graph, 2)[0][2]; g11 = drx.get(graph, 11)[0][2]
res15 = next(v for fn, wt, v in drx.parse(drx.get(graph, 3)[0][2]) if fn == 15)
f32 = lambda x: struct.pack("<f", x)
res = [[1, 0, 3840], [2, 0, 2160], [3, 5, f32(1.0)], [4, 0, 3840], [5, 0, 2160], [6, 5, f32(1.0)],
       [7, 0, 3840], [8, 0, 2160], [9, 0, 1], [15, 2, res15]]
N = len(NAMEN)
g = [[1, 0, N], [2, 0, g2], [3, 2, drx.build(res)]]
for i, name in enumerate(NAMEN, start=1):
    g.append([7, 2, drx.build([[1, 0, i], [2, 0, i], [4, 0, 190 + 300 * (i - 1)], [5, 0, 180], [6, 2, name.encode()],
                               [7, 0, 1], [8, 0, 44], [9, 2, f9], [10, 2, f10], [12, 0, f12]])])
for i in range(1, N):
    g.append([8, 2, drx.build([[1, 0, i], [3, 0, i + 1], [5, 0, 64], [6, 0, 64], [7, 0, i]])])
g.append([9, 2, drx.build([[1, 0, 1], [2, 0, 80], [3, 2, drx.build([[1, 0, 1], [2, 0, 64], [3, 0, 1], [4, 0, 1]])]])])
g.append([10, 2, drx.build([[1, 0, 2], [2, 0, 64], [3, 2, drx.build([[1, 0, N + 1], [2, 0, 64], [3, 0, 2], [4, 0, N]])]])])
g.append([11, 0, g11]); g.append([12, 0, g12])
top5 = [[1, 2, drx.build(g)]] + [f for f in top if f[0] != 1]
body5 = drx.body_encode(drx.build(top5))

def neue_ids(text):
    return re.sub(r'DbId="[0-9a-f-]+"', lambda _: f'DbId="{uuid.uuid4()}"', text)

t2 = t[:m_clip.start(1)] + body5 + t[m_clip.end(1):]
t2 = neue_ids(t2).replace("<SrcHint>Cinemtatic Werbeanzeige</SrcHint>", "<SrcHint>NIRO Basis v1</SrcHint>")
t2 = re.sub(r"<Width>\d+</Width>", "<Width>3840</Width>", t2)
t2 = re.sub(r"<Height>\d+</Height>", "<Height>2160</Height>", t2)
# T3: ohne Vorschaubilder, ohne lokalen Galerie-Pfad
t3 = re.sub(r"<Buffer>[0-9a-fA-F]+</Buffer>", "<Buffer/>", t2)
t3 = re.sub(r"<ClipThumbnails>[0-9a-fA-F]+</ClipThumbnails>", "<ClipThumbnails/>", t3)
t3 = re.sub(r"<GalleryPath>[^<]*</GalleryPath>", "<GalleryPath/>", t3)
for name, text in (("T1_vorlage_neu_verpackt.drx", t1), ("T2_basis5_mit_vorschau.drx", t2), ("T3_basis5_ohne_vorschau.drx", t3)):
    open(name, "w", encoding="utf-8").write(text)
    nodes, edges = drx.nodes_info(drx.body_decode(drx.bodies(text)[0].group(1)))
    print(name, len(text), "Zeichen |", [(n['id'], n['nr'], n['label']) for n in nodes], "| Kanten", edges)
