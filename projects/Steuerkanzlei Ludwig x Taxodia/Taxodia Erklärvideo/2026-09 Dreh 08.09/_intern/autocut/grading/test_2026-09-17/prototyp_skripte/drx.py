"""Prototyp: DRX lesen/schreiben (0x81 + zstd(Protobuf)), byte-genaues Neu-Kodieren, 5-Node-Basis erzeugen."""
import re, struct, uuid
from compression import zstd

# ---------- Protobuf roh, verlustfrei ----------
def _varint(b, i):
    r = s = 0
    while True:
        c = b[i]; i += 1
        r |= (c & 0x7f) << s; s += 7
        if not c & 0x80:
            return r, i

def _enc_varint(v):
    out = bytearray()
    while True:
        c = v & 0x7f; v >>= 7
        if v:
            out.append(c | 0x80)
        else:
            out.append(c); return bytes(out)

def parse(b):
    """Liste von [feld, wiretyp, wert]; wert: int (0), bytes (1/5 roh), bytes (2) — Untermeldungen erst bei Bedarf."""
    i, out = 0, []
    while i < len(b):
        key, i = _varint(b, i)
        fn, wt = key >> 3, key & 7
        if wt == 0:
            v, i = _varint(b, i)
        elif wt == 1:
            v = b[i:i+8]; i += 8
        elif wt == 5:
            v = b[i:i+4]; i += 4
        elif wt == 2:
            n, i = _varint(b, i); v = b[i:i+n]; i += n
        else:
            raise ValueError(f"Wiretyp {wt} an {i}")
        out.append([fn, wt, v])
    return out

def build(fields):
    out = bytearray()
    for fn, wt, v in fields:
        out += _enc_varint(fn << 3 | wt)
        if wt == 0:
            out += _enc_varint(v)
        elif wt in (1, 5):
            out += v
        elif wt == 2:
            if isinstance(v, list):
                v = build(v)
            out += _enc_varint(len(v)) + v
    return bytes(out)

def get(fields, fn):
    return [f for f in fields if f[0] == fn]

# ---------- DRX-Datei ----------
def bodies(text):
    return list(re.finditer(r"<Body>([0-9a-fA-F]+)</Body>", text))

def body_decode(hexstr):
    raw = bytes.fromhex(hexstr)
    assert raw[0] == 0x81 and raw[1:5] == b"\x28\xb5\x2f\xfd", raw[:6].hex()
    return zstd.decompress(raw[1:])

def body_encode(pb):
    return (b"\x81" + zstd.compress(pb)).hex()

def nodes_info(pb):
    g = parse(get(parse(pb), 1)[0][2])
    res = []
    for _, _, nb in get(g, 7):
        n = parse(nb)
        d = {"id": get(n, 1)[0][2], "nr": get(n, 2)[0][2] if get(n, 2) else None,
             "label": get(n, 6)[0][2].decode() if get(n, 6) else ""}
        m = re.search(rb"[\x20-\x7e]{6,}\.cube", nb)
        d["lut"] = m.group(0).decode() if m else None
        res.append(d)
    edges = [(get(parse(e), 1)[0][2], get(parse(e), 3)[0][2]) for _, _, e in get(g, 8)]
    return res, edges
