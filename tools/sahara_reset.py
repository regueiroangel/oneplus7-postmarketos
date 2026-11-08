#!/usr/bin/env python3
"""Send a Sahara RESET to a Qualcomm device in crash-dump (05c6:900e) mode.
usage: sudo python3 -I sahara_reset.py /dev/bus/usb/BBB/DDD
Uses raw usbfs ioctls, stdlib only. Endpoints 0x01 (out) / 0x81 (in), interface 0.
"""
import ctypes, fcntl, os, struct, sys

USBDEVFS_CLAIMINTERFACE = 0x8004550F
USBDEVFS_RELEASEINTERFACE = 0x80045510
USBDEVFS_BULK = 0xC0185502


class Bulk(ctypes.Structure):
    _fields_ = [("ep", ctypes.c_uint), ("len", ctypes.c_uint),
                ("timeout", ctypes.c_uint), ("data", ctypes.c_void_p)]


def bulk(fd, ep, data=None, size=4096, timeout=3000):
    buf = ctypes.create_string_buffer(data if data is not None else size,
                                      len(data) if data is not None else size)
    b = Bulk(ep, len(buf), timeout, ctypes.cast(buf, ctypes.c_void_p))
    n = fcntl.ioctl(fd, USBDEVFS_BULK, b)
    return buf.raw[:n]


def main():
    fd = os.open(sys.argv[1], os.O_RDWR)
    fcntl.ioctl(fd, USBDEVFS_CLAIMINTERFACE, struct.pack("I", 0))
    try:
        try:
            pkt = bulk(fd, 0x81, timeout=3000)
            cmd, ln = struct.unpack("<II", pkt[:8])
            print("rx cmd=0x%x len=%d" % (cmd, ln))
            if cmd == 1:  # HELLO
                ver, compat, maxlen, mode = struct.unpack("<IIII", pkt[8:24])
                print("HELLO version=%d mode=%d" % (ver, mode))
                resp = struct.pack("<IIIIII", 2, 0x30, 2, 1, 0, mode) + b"\0" * 24
                bulk(fd, 0x01, resp)
                try:
                    pkt = bulk(fd, 0x81, timeout=3000)
                    print("rx after hello cmd=0x%x" % struct.unpack("<I", pkt[:4]))
                except OSError as e:
                    print("no packet after hello:", e)
        except OSError as e:
            print("no hello (", e, ") - sending reset anyway")
        bulk(fd, 0x01, struct.pack("<II", 7, 8))  # RESET
        print("RESET sent")
        try:
            pkt = bulk(fd, 0x81, timeout=3000)
            print("rx cmd=0x%x (8 = RESET_RESP)" % struct.unpack("<I", pkt[:4]))
        except OSError as e:
            print("no reset response:", e)
    finally:
        try:
            fcntl.ioctl(fd, USBDEVFS_RELEASEINTERFACE, struct.pack("I", 0))
        except OSError:
            pass
        os.close(fd)


main()
