#!/usr/bin/env python3
"""Dump FDT nodes matching a regex (with properties), resolving phandles.
usage: fdt_dump.py <file> <offset|dtbo> <node-regex>
  offset: hex offset of a single FDT in file; 'dtbo' scans an Android DTBO image.
stdlib only.
"""
import re, struct, sys


def parse(b):
    magic, total, ost, ostr = struct.unpack(">IIII", b[:16])
    b = b[:total]
    i = ost; path = []; nodes = []; cur = None
    while True:
        tok = struct.unpack(">I", b[i:i+4])[0]; i += 4
        if tok == 1:
            e = b.index(b"\0", i); name = b[i:e].decode(errors="replace"); i = (e + 4) & ~3
            path.append(name); cur = {"path": "/".join(path) or "/", "props": []}; nodes.append(cur)
        elif tok == 2:
            path.pop()
        elif tok == 3:
            ln, no = struct.unpack(">II", b[i:i+8]); i += 8
            v = b[i:i+ln]; i = (i + ln + 3) & ~3
            pn = b[ostr+no:b.index(b"\0", ostr+no)].decode()
            # find innermost node with this path
            p = "/".join(path) or "/"
            for n in reversed(nodes):
                if n["path"] == p:
                    n["props"].append((pn, v)); break
        elif tok == 4:
            continue
        else:
            break
    return nodes


def fmt(v, phmap, name):
    if v and v[-1:] == b"\0" and all(32 <= c < 127 or c == 0 for c in v):
        return repr(v.rstrip(b"\0").decode().split("\0"))
    if len(v) % 4 == 0:
        cells = [struct.unpack(">I", v[k:k+4])[0] for k in range(0, len(v), 4)]
        if name.endswith("-supply") or name in ("clocks",):
            return "<%s>" % " ".join(phmap.get(c, hex(c)) for c in cells)
        return "<%s>" % " ".join(hex(c) for c in cells)
    return v.hex()


def dump(b, rx, tag=""):
    nodes = parse(b)
    phmap = {}
    for n in nodes:
        for pn, v in n["props"]:
            if pn in ("phandle", "linux,phandle") and len(v) == 4:
                phmap[struct.unpack(">I", v)[0]] = "&" + n["path"].split("/")[-1]
    for n in nodes:
        if re.search(rx, n["path"]):
            print("%s%s" % (tag, n["path"]))
            for pn, v in n["props"]:
                print("    %s = %s" % (pn, fmt(v, phmap, pn)))
    return nodes


b = open(sys.argv[1], "rb").read()
if sys.argv[2] == "dtbo":
    magic, total, hsz, esz, cnt, eoff = struct.unpack(">IIIIII", b[:24])
    assert magic == 0xD7B7AB1E, hex(magic)
    for k in range(cnt):
        e = b[eoff + k*esz: eoff + (k+1)*esz]
        dsz, doff, did, drev = struct.unpack(">IIII", e[:16])
        custom = struct.unpack(">IIII", e[16:32])
        print("== dtbo entry %d id=0x%x rev=0x%x custom=%s size=%d" % (k, did, drev, [hex(c) for c in custom], dsz))
        dump(b[doff:doff+dsz], sys.argv[3], "  ")
else:
    o = int(sys.argv[2], 16)
    dump(b[o:], sys.argv[3])
