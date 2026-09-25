"""The hint encoding, shared by the packer and the ChampSim module.

Eight bits per load PC, as in the paper:

    [7:4] selection  index into ENSEMBLE; 0 means "do not prefetch"
    [3:2] degree     0 unused, 1/2/3 = Q1 / median / Q3 of the selected
                     member's own native degree range
    [1:0] filter     0 none, 1..3 an index into the table's three-entry
                     filter-candidate list

Two bits cannot name one of twelve ensemble members, so the filter field
is an index into a three-entry side table the packer emits with the
hints: the three members the generator filters most often. The paper
does not say how it resolves this; this is our reading.

ENSEMBLE must stay in step with `make_ensemble()` in
champsim/prefetcher/lmhint/subprefetchers.h -- the selection field is an
index into it.
"""
from __future__ import annotations

import struct

ENSEMBLE = ["none", "next_line", "ip_stride", "streamer", "ampm", "sandbox", "sms"]
REDUCED = ["none", "next_line", "ip_stride", "streamer"]
MAGIC = b"LMHT1"
HINT_BITS = 8

# the native degree range of each member, as (Q1, median, Q3); mirrors
# the degrees() of each class in subprefetchers.h
DEGREES = {"none": (0, 0, 0), "next_line": (1, 2, 4), "ip_stride": (1, 3, 6),
           "streamer": (2, 4, 8), "ampm": (1, 2, 4), "sandbox": (1, 2, 4),
           "sms": (2, 4, 8)}


def members(ensemble: str = "full") -> list:
    return list(REDUCED if ensemble == "reduced" else ENSEMBLE)


def encode(select: str, degree: int, filt_slot: int, fields: str = "SDF") -> int:
    """One hint byte. `fields` drops the fields the hardware does not
    apply, so a table packed for -S carries no degree or filter bits."""
    sel = ENSEMBLE.index(select) if select in ENSEMBLE else 0
    if sel == 0:
        return 0
    d = int(degree) if ("D" in fields and degree in (1, 2, 3)) else 2
    f = int(filt_slot) if ("F" in fields and filt_slot in (1, 2, 3)) else 0
    return ((sel & 0xF) << 4) | ((d & 0x3) << 2) | (f & 0x3)


def pack(hints: dict, filter_candidates: list) -> bytes:
    """`hints` is {pc: byte}; the table is sorted by PC so the module can
    load it in one pass. `filter_candidates` names up to three members."""
    cand = [ENSEMBLE.index(c) if c in ENSEMBLE else 0 for c in (filter_candidates or [])][:3]
    cand += [0] * (3 - len(cand))
    items = sorted((int(pc), int(b) & 0xFF) for pc, b in hints.items() if int(b) & 0xFF)
    out = bytearray(MAGIC)
    out += bytes(cand)
    out += struct.pack("<I", len(items))
    out += b"".join(struct.pack("<Q", pc) for pc, _ in items)
    out += bytes(b for _, b in items)
    return bytes(out)


def unpack(blob: bytes) -> tuple:
    if blob[:5] != MAGIC:
        raise ValueError("not an LMHT1 table")
    cand = list(blob[5:8])
    (n,) = struct.unpack_from("<I", blob, 8)
    off = 12
    pcs = struct.unpack_from(f"<{n}Q", blob, off)
    off += 8 * n
    hints = blob[off:off + n]
    return {pc: h for pc, h in zip(pcs, hints)}, [ENSEMBLE[c] for c in cand]
