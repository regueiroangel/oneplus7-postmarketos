#!/usr/bin/env python3
"""Scan a file for FDT blobs and print root-node model / qcom ids. stdlib only."""
import struct, sys

def root_props(b, o):
    magic, total, off_struct, off_strings = struct.unpack(">IIII", b[o:o+16])
    b = b[o:o+total]  # work on a copy so 4-byte alignment is relative to blob start
    st = off_struct; ss = off_strings
    i = st; depth = 0; props = {}
    while True:
        tok = struct.unpack(">I", b[i:i+4])[0]; i += 4
        if tok == 1:  # BEGIN_NODE
            e = b.index(b"\0", i); i = (e + 4) & ~3; depth += 1
        elif tok == 2:  # END_NODE
            depth -= 1
            if depth == 0: break
        elif tok == 3:  # PROP
            ln, no = struct.unpack(">II", b[i:i+8]); i += 8
            val = b[i:i+ln]; i = (i + ln + 3) & ~3
            if depth == 1:
                name = b[ss+no:b.index(b"\0", ss+no)].decode()
                props[name] = val
        elif tok == 4: continue
        elif tok == 9: break
        else: break
    return total, props

def cells(v): return [struct.unpack(">I", v[k:k+4])[0] for k in range(0, len(v), 4)]

b = open(sys.argv[1], "rb").read()
o = 0; n = 0
while True:
    o = b.find(b"\xd0\x0d\xfe\xed", o)
    if o < 0: break
    try:
        total, p = root_props(b, o)
    except Exception:
        o += 4; continue
    if "model" in p or "qcom,msm-id" in p:
        n += 1
        f = lambda k: cells(p[k]) if k in p else None
        print("@0x%x size=%d model=%r msm-id=%s board-id=%s pmic-id=%s" % (
            o, total, p.get("model", b"").rstrip(b"\0").decode(errors="replace"),
            f("qcom,msm-id"), f("qcom,board-id"), f("qcom,pmic-id")))
    o += max(total, 4)
print("dtbs:", n)
