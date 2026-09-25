"""Bypass TransDot's qq register stage under `COMBINATIONAL`.

`transdot_fp4_fp8_fp16_fp32_fma` keeps one register stage between the
exponent datapath and the adder whatever `NumPipeRegs` says: the three
`always_ff` blocks that drive the `_qq` signals carry no generate guard,
so the unit is never combinational. The `COMBINATIONAL` define, which the
repository already uses to bypass the registers of
`transdot_decomp_multiplier` and `transdot_decomp_addend_datapath`, now
bypasses these as well, which makes `NumPipeRegs` 0 a register-free
configuration. Without the define the file behaves as before.
"""
import pathlib, sys

P = pathlib.Path("3rdparty/transdot/src/transdot_fp4_fp8_fp16_fp32_fma.sv")
NOTE = "// chiALU: COMBINATIONAL bypasses the qq stage"
s = P.read_text()
if NOTE in s:
    print("already patched"); sys.exit(0)
orig = pathlib.Path(str(P) + ".orig")
if not orig.exists():
    orig.write_text(s)
L = s.splitlines(True)


def find(sub, start=0):
    for i in range(start, len(L)):
        if sub in L[i]:
            return i
    raise SystemExit(f"not found: {sub!r}")


def wrap(a, b, comb):
    """Lines [a, b) guarded by `ifdef COMBINATIONAL with `comb` in front."""
    return ["`ifdef COMBINATIONAL\n", f"  {NOTE}\n"] + comb + ["`else\n"] + L[a:b] + ["`endif\n"]


# ---- 3. the valid bit (patched last-first, so earlier indices stay valid)
a = find("      inp_pipe_valid_qq <= 1'b0;") - 2
b = a
depth = 0
while True:
    if " begin" in L[b] or L[b].rstrip().endswith("begin"):
        depth += L[b].count("begin")
    depth -= L[b].count("    end") if L[b].strip() in ("end", "end else begin") else 0
    b += 1
    if L[b - 1].rstrip() == "  end":
        break
v = wrap(a, b, ["  assign inp_pipe_valid_qq = inp_pipe_valid_q;\n"])

# ---- 2. the wide qq stage
a2 = find("      exponent_product_qq       <= '0;") - 2
u = find("    end else if (pipe_qq_en) begin", a2)
b2 = u
while L[b2].rstrip() != "  end":
    b2 += 1
b2 += 1
body = [x.replace("<=", " =") for x in L[u + 1:b2 - 2]]
q = wrap(a2, b2, ["  always_comb begin\n"] + body + ["  end\n"])

# ---- 1. the tentative-sign stage
a1 = find("      tentative_sign_qq        <= 1'b0;") - 2
# the update line: `end else begin` before upstream's SIMD staging fix (cd3d062),
# `end else if (pipe_qq_en) begin` after it (the enable is one when the unit is combinational)
u1 = min(i for i in range(a1, len(L)) if L[i].startswith("    end else") and L[i].rstrip().endswith("begin"))
b1 = u1
while L[b1].rstrip() != "  end":
    b1 += 1
b1 += 1
body1 = [x.replace("<=", " =") for x in L[u1 + 1:b1 - 2]]
t = wrap(a1, b1, ["  always_comb begin\n"] + body1 + ["  end\n"])

L = L[:a1] + t + L[b1:a2] + q + L[b2:a] + v + L[b:]
P.write_text("".join(L))
print("patched", P, "| guards:", "".join(L).count("`ifdef COMBINATIONAL"))
