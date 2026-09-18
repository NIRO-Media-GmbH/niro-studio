"""WAV (RIFF) lesen und mit neuem LIST/INFO- und id3-Chunk schreiben — Audiodaten bitgleich."""
import hashlib
import struct
import unicodedata

PUFFER = 8 << 20
# RIFF-INFO-Felder, die Artlist selbst setzt bzw. die wir schreiben
INFO_REIHENFOLGE = ["INAM", "IART", "IPRD", "IGNR", "ISBJ", "ICMT", "IKEY", "ICOP", "ICRD", "ISRC", "ISFT"]


def chunks(f):
    """Liste (id, offset_daten, groesse) aller Top-Level-Chunks einer RIFF/WAVE-Datei."""
    f.seek(0)
    kopf = f.read(12)
    if len(kopf) < 12 or kopf[:4] != b"RIFF" or kopf[8:12] != b"WAVE":
        raise ValueError("keine RIFF/WAVE-Datei (evtl. RF64)")
    liste, pos = [], 12
    while True:
        f.seek(pos)
        h = f.read(8)
        if len(h) < 8:
            break
        cid, groesse = struct.unpack("<4sI", h)
        liste.append((cid, pos + 8, groesse))
        pos += 8 + groesse + (groesse & 1)
    return liste


def lies_info(f):
    info = {}
    for cid, off, groesse in chunks(f):
        if cid != b"LIST":
            continue
        f.seek(off)
        daten = f.read(groesse)
        if daten[:4] != b"INFO":
            continue
        p = 4
        while p + 8 <= len(daten):
            sid, sg = struct.unpack("<4sI", daten[p:p + 8])
            wert = daten[p + 8:p + 8 + sg].rstrip(b"\x00")
            info[sid.decode("latin-1")] = wert.decode("utf-8", errors="replace")
            p += 8 + sg + (sg & 1)
    return info


def ascii_text(wert):
    """RIFF-INFO kennt keine Zeichenkodierung (exiftool/Windows lesen Latin-1, ffmpeg UTF-8): nur ASCII schreiben."""
    for alt, neu in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("Ä", "Ae"), ("Ö", "Oe"), ("Ü", "Ue"), ("ß", "ss"), ("’", "'"), ("–", "-")):
        wert = wert.replace(alt, neu)
    return unicodedata.normalize("NFKD", wert).encode("ascii", "ignore").decode()


def baue_info(felder):
    teile = [b"INFO"]
    for schluessel in INFO_REIHENFOLGE:
        wert = felder.get(schluessel)
        if not wert:
            continue
        roh = ascii_text(unicodedata.normalize("NFC", str(wert))).encode("ascii") + b"\x00"
        teile.append(struct.pack("<4sI", schluessel.encode(), len(roh)) + roh + (b"\x00" if len(roh) & 1 else b""))
    inhalt = b"".join(teile)
    return struct.pack("<4sI", b"LIST", len(inhalt)) + inhalt


def schreibe(quelle, ziel, info_felder, id3_bytes):
    """Kopiert WAVE-Chunks (ohne alte LIST/INFO- und id3-Chunks), fügt neue ein.

    Rückgabe: MD5 des data-Chunks (wie geschrieben).
    """
    md5 = hashlib.md5()
    with open(quelle, "rb") as src, open(ziel, "wb") as dst:
        teile = chunks(src)
        dst.write(b"RIFF\x00\x00\x00\x00WAVE")
        info_geschrieben = False
        for cid, off, groesse in teile:
            if cid in (b"id3 ", b"ID3 "):
                continue
            if cid == b"LIST":
                src.seek(off)
                if src.read(4) == b"INFO":
                    continue
            if cid == b"data" and not info_geschrieben:
                dst.write(baue_info(info_felder))
                info_geschrieben = True
            dst.write(struct.pack("<4sI", cid, groesse))
            src.seek(off)
            rest = groesse
            while rest:
                block = src.read(min(PUFFER, rest))
                if not block:
                    raise IOError(f"Quelle zu kurz: {quelle}")
                if cid == b"data":
                    md5.update(block)
                dst.write(block)
                rest -= len(block)
            if groesse & 1:
                dst.write(b"\x00")
        if not info_geschrieben:
            dst.write(baue_info(info_felder))
        if id3_bytes:
            dst.write(struct.pack("<4sI", b"id3 ", len(id3_bytes)) + id3_bytes + (b"\x00" if len(id3_bytes) & 1 else b""))
        gesamt = dst.tell()
        dst.seek(4)
        dst.write(struct.pack("<I", gesamt - 8))
    return md5.hexdigest()


def data_md5(pfad):
    md5 = hashlib.md5()
    with open(pfad, "rb") as f:
        for cid, off, groesse in chunks(f):
            if cid == b"data":
                f.seek(off)
                rest = groesse
                while rest:
                    block = f.read(min(PUFFER, rest))
                    if not block:
                        break
                    md5.update(block)
                    rest -= len(block)
                return md5.hexdigest()
    raise ValueError(f"kein data-Chunk: {pfad}")
