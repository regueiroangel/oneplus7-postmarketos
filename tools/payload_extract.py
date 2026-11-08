#!/usr/bin/env python3
"""Minimal Android A/B payload.bin extractor (full OTA only, stdlib only).
usage: payload_extract.py <ota.zip> <outdir> <partition> [partition...]
"""
import bz2, lzma, struct, sys, zipfile, os, hashlib

def varint(b, i):
    r = s = 0
    while True:
        c = b[i]; i += 1
        r |= (c & 0x7f) << s; s += 7
        if not c & 0x80:
            return r, i

def fields(b):
    i = 0; out = []
    while i < len(b):
        k, i = varint(b, i); f, t = k >> 3, k & 7
        if t == 0:
            v, i = varint(b, i)
        elif t == 1:
            v = b[i:i+8]; i += 8
        elif t == 2:
            l, i = varint(b, i); v = b[i:i+l]; i += l
        elif t == 5:
            v = b[i:i+4]; i += 4
        else:
            raise ValueError("wire type %d" % t)
        out.append((f, t, v))
    return out

def main():
    zpath, outdir, wanted = sys.argv[1], sys.argv[2], set(sys.argv[3:])
    os.makedirs(outdir, exist_ok=True)
    z = zipfile.ZipFile(zpath)
    p = z.open("payload.bin")
    hdr = p.read(24)
    assert hdr[:4] == b"CrAU", hdr[:4]
    ver, msize = struct.unpack(">QQ", hdr[4:20])
    sigsize = struct.unpack(">I", hdr[20:24])[0] if ver >= 2 else 0
    if ver < 2:
        p.seek(20)
    manifest = p.read(msize)
    data_start = (24 if ver >= 2 else 20) + msize + sigsize
    block = 4096
    parts = []
    for f, t, v in fields(manifest):
        if f == 3 and t == 0:
            block = v
        if f == 13:
            parts.append(v)
    for pv in parts:
        name = None; ops = []; size = None
        for f, t, v in fields(pv):
            if f == 1: name = v.decode()
            elif f == 8: ops.append(v)
            elif f == 7:
                for ff, tt, vv in fields(v):
                    if ff == 1: size = vv
        print("partition %-24s size=%s ops=%d" % (name, size, len(ops)))
        if name not in wanted:
            continue
        with open(os.path.join(outdir, name + ".img"), "wb") as out:
            if size: out.truncate(size)
            for ov in ops:
                typ = 0; off = 0; ln = 0; dst = []
                for f, t, v in fields(ov):
                    if f == 1: typ = v
                    elif f == 2: off = v
                    elif f == 3: ln = v
                    elif f == 6:
                        e = dict((ff, vv) for ff, tt, vv in fields(v))
                        dst.append((e.get(1, 0), e.get(2, 0)))
                p.seek(data_start + off)
                raw = p.read(ln)
                if typ == 0: data = raw
                elif typ == 1: data = bz2.decompress(raw)
                elif typ == 8: data = lzma.decompress(raw)
                elif typ == 6: data = b"\0" * sum(n for _, n in dst) * block
                else: raise SystemExit("unsupported op type %d in %s" % (typ, name))
                pos = 0
                for start, n in dst:
                    out.seek(start * block)
                    out.write(data[pos:pos + n * block]); pos += n * block
        print("  -> extracted", name)

main()
