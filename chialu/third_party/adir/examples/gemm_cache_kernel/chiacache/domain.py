"""The Kernel template: every variable is fixed (the hardware is the
specification), the searched object is the text of four C kernels, one
per shape class, and the declaration block carries the domain's BUFFER
and TILE lines. The seed generator writes three plans (naive, tiled_l2,
packed_tiled); the harness generator writes the driver."""
from __future__ import annotations

from adir import Enum, LineKind, PromptSource, Range, TacticSource, Template, Variable
from adir.declaration import parse_fields

MEMBERS = ("gemm_small", "gemm_large", "gemm_tall", "gemm_wide")
ELEM_BYTES = {"fp32": 4}
DEFAULT_TILES = {"gemm_small": (32, 32, 64), "gemm_large": (64, 64, 128),
                 "gemm_tall": (128, 32, 128), "gemm_wide": (32, 128, 128)}


def capacity_bytes(ctx) -> int:
    return int(ctx.value("l2.size_kb")) * 1024


def parse_buffer(tokens):
    d = parse_fields(tokens)
    if not d.get("_") or "bytes" not in d:
        raise ValueError("BUFFER <name> bytes=<n>")
    return {"name": d["_"][0], "bytes": int(d["bytes"])}


def parse_tile(tokens):
    d = parse_fields(tokens)
    if not d.get("_") or d["_"][0] not in MEMBERS:
        raise ValueError(f"TILE <member in {MEMBERS}> mb=<m> nb=<n> kb=<k>")
    for k in ("mb", "nb", "kb"):
        if k not in d or int(d[k]) < 1:
            raise ValueError(f"TILE needs {k}>=1")
    return {"member": d["_"][0], "mb": int(d["mb"]), "nb": int(d["nb"]), "kb": int(d["kb"])}


def check_buffer(ctx, entries):
    cap = capacity_bytes(ctx)
    total = sum(e["bytes"] for e in entries)
    if total > cap:
        return False, f"BUFFER bytes sum to {total}, above the capacity {cap}"
    return True, f"{len(entries)} buffers, {total} of {cap} bytes"


def check_tile(ctx, entries):
    elem = ELEM_BYTES[str(ctx.value("kernel.dtype"))]
    decl = ctx.declaration
    buffers = 0
    for kind, tokens in decl.lines:
        if kind == "BUFFER":
            try:
                buffers += parse_buffer(tokens)["bytes"]
            except ValueError:
                pass
    seen = set()
    for e in entries:
        if e["member"] in seen:
            return False, f"two TILE lines for {e['member']}"
        seen.add(e["member"])
        ws = (e["mb"] * e["kb"] + e["kb"] * e["nb"] + e["mb"] * e["nb"]) * elem
        if buffers and ws > buffers:
            return False, (f"TILE {e['member']}: the working set {ws} bytes exceeds the "
                           f"declared buffers ({buffers} bytes)")
    missing = [m for m in MEMBERS if m not in seen]
    if missing:
        return False, f"no TILE line for {missing}"
    return True, "tiles consistent with the buffers"


# ------------------------------------------------------------- the kernels

SIG = "void {name}(int M, int N, int K, const float *A, const float *B, float *C)"
HEAD = "#include <stddef.h>\n"      # each member is a translation-unit fragment; size_t before the function


def _naive(name):
    return HEAD + f"""{SIG.format(name=name)} {{
    /* plan naive: the reference loop order, no blocking */
    for (int i = 0; i < M; i++)
        for (int j = 0; j < N; j++) {{
            float acc = 0.0f;
            for (int k = 0; k < K; k++)
                acc += A[(size_t)i * K + k] * B[(size_t)k * N + j];
            C[(size_t)i * N + j] = acc;
        }}
}}
"""


def _tiled(name, mb, nb, kb):
    return HEAD + f"""{SIG.format(name=name)} {{
    /* plan tiled_l2: i-k-j loop order over {mb} x {nb} x {kb} blocks so a block of B stays cached */
    const int MB = {mb}, NB = {nb}, KB = {kb};
    for (int i = 0; i < M; i++)
        for (int j = 0; j < N; j++)
            C[(size_t)i * N + j] = 0.0f;
    for (int i0 = 0; i0 < M; i0 += MB)
        for (int k0 = 0; k0 < K; k0 += KB)
            for (int j0 = 0; j0 < N; j0 += NB) {{
                int i1 = i0 + MB < M ? i0 + MB : M;
                int k1 = k0 + KB < K ? k0 + KB : K;
                int j1 = j0 + NB < N ? j0 + NB : N;
                for (int i = i0; i < i1; i++)
                    for (int k = k0; k < k1; k++) {{
                        float a = A[(size_t)i * K + k];
                        const float *b = B + (size_t)k * N;
                        float *c = C + (size_t)i * N;
                        for (int j = j0; j < j1; j++)
                            c[j] += a * b[j];
                    }}
            }}
}}
"""


def _packed(name, mb, nb, kb):
    return HEAD + f"""{SIG.format(name=name)} {{
    /* plan packed_tiled: a {kb} x {nb} panel of B is packed contiguously, then {mb}-row blocks of A stream through it */
    const int MB = {mb}, NB = {nb}, KB = {kb};
    static float Bp[{kb} * {nb}];
    for (int i = 0; i < M; i++)
        for (int j = 0; j < N; j++)
            C[(size_t)i * N + j] = 0.0f;
    for (int k0 = 0; k0 < K; k0 += KB) {{
        int k1 = k0 + KB < K ? k0 + KB : K;
        for (int j0 = 0; j0 < N; j0 += NB) {{
            int j1 = j0 + NB < N ? j0 + NB : N;
            int nb = j1 - j0;
            for (int k = k0; k < k1; k++)
                for (int j = j0; j < j1; j++)
                    Bp[(k - k0) * nb + (j - j0)] = B[(size_t)k * N + j];
            for (int i0 = 0; i0 < M; i0 += MB) {{
                int i1 = i0 + MB < M ? i0 + MB : M;
                for (int i = i0; i < i1; i++) {{
                    float *c = C + (size_t)i * N + j0;
                    for (int k = k0; k < k1; k++) {{
                        float a = A[(size_t)i * K + k];
                        const float *bp = Bp + (k - k0) * nb;
                        for (int j = 0; j < nb; j++)
                            c[j] += a * bp[j];
                    }}
                }}
            }}
        }}
    }}
}}
"""


def seed_generator(ctx, name):
    elem = ELEM_BYTES[str(ctx.value("kernel.dtype"))]
    texts, lines = {}, []
    total = 0
    for m in MEMBERS:
        mb, nb, kb = DEFAULT_TILES[m]
        if name == "naive":
            texts[m] = _naive(m)
        elif name == "tiled_l2":
            texts[m] = _tiled(m, mb, nb, kb)
        elif name == "packed_tiled":
            texts[m] = _packed(m, mb, nb, kb)
        else:
            raise ValueError(name)
        lines.append(("TILE", [m, f"mb={mb}", f"nb={nb}", f"kb={kb}"]))
        total = max(total, (mb * kb + kb * nb + mb * nb) * elem)
    lines.insert(0, ("BUFFER", ["working_set", f"bytes={total}"]))
    return texts, {}, lines


def gen_harness(ctx):
    disp = "\n".join(f'    if (strcmp(name, "{m}") == 0) return {m};' for m in MEMBERS)
    protos = "\n".join(SIG.format(name=m) + ";" for m in MEMBERS)
    return f"""/* the driver: fills random operands, runs a kernel, and under `check` compares it with the reference */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
{protos}
void gemm_ref(int M, int N, int K, const float *A, const float *B, float *C);
typedef void (*kernel_fn)(int, int, int, const float *, const float *, float *);
static kernel_fn pick(const char *name) {{
{disp}
    return 0;
}}
static void fill(float *x, size_t n, unsigned seed) {{
    unsigned s = seed * 2654435761u + 1u;
    for (size_t i = 0; i < n; i++) {{ s = s * 1664525u + 1013904223u; x[i] = ((s >> 8) & 0xffff) / 65536.0f - 0.5f; }}
}}
int main(int argc, char **argv) {{
    if (argc < 6) {{ fprintf(stderr, "usage: %s <member> M N K <check|run> [seed]\\n", argv[0]); return 2; }}
    kernel_fn f = pick(argv[1]);
    if (!f) {{ fprintf(stderr, "no kernel %s\\n", argv[1]); return 2; }}
    int M = atoi(argv[2]), N = atoi(argv[3]), K = atoi(argv[4]);
    int check = strcmp(argv[5], "check") == 0;
    unsigned seed = argc > 6 ? (unsigned)atoi(argv[6]) : 1u;
    float *A = malloc(sizeof(float) * (size_t)M * K), *B = malloc(sizeof(float) * (size_t)K * N);
    float *C = malloc(sizeof(float) * (size_t)M * N), *R = check ? malloc(sizeof(float) * (size_t)M * N) : 0;
    fill(A, (size_t)M * K, seed); fill(B, (size_t)K * N, seed + 7);
    f(M, N, K, A, B, C);
    if (check) {{
        gemm_ref(M, N, K, A, B, R);
        double maxerr = 0.0, maxref = 0.0;
        for (size_t i = 0; i < (size_t)M * N; i++) {{
            double e = fabs((double)C[i] - (double)R[i]); if (e > maxerr) maxerr = e;
            double r = fabs((double)R[i]); if (r > maxref) maxref = r;
        }}
        double tol = 1e-4 * (maxref > 1.0 ? maxref : 1.0) * (K > 64 ? K / 64.0 : 1.0);
        printf("%s maxerr=%g tol=%g\\n", maxerr <= tol ? "OK" : "MISMATCH", maxerr, tol);
        return maxerr <= tol ? 0 : 1;
    }}
    printf("ran %s %d %d %d checksum=%g\\n", argv[1], M, N, K, (double)C[0] + (double)C[(size_t)M * N - 1]);
    return 0;
}}
"""


# ------------------------------------------------------------- prompt and tactic sources

def _plan_table(instance, archive, parent):
    if not parent:
        return ""
    d = parent.get("declarations") or {}
    L = ["## The plan of the current program", "", "| line | fields |", "| --- | --- |"]
    for kind, tokens in d.get("lines") or []:
        L.append(f"| {kind} | {' '.join(str(t) for t in tokens)} |")
    return "\n".join(L) + "\n"


def _worst_member(instance, archive, parent):
    if not parent:
        return []
    seeds = [r for r in archive.records() if r.get("is_seed")]
    if not seeds:
        return []
    base = ((seeds[0].get("measurements") or {}).get("sim") or {}).get("value") or {}
    cur = ((parent.get("measurements") or {}).get("sim") or {}).get("value") or {}
    bc, cc = base.get("cycles") or {}, cur.get("cycles") or {}
    ratios = {}
    for shape, c in cc.items():
        member = shape.split(":")[0]
        if isinstance(c, (int, float)) and isinstance(bc.get(shape), (int, float)) and c > 0:
            ratios.setdefault(member, []).append(bc[shape] / c)
    if not ratios:
        return []
    worst = min(ratios, key=lambda m: sum(ratios[m]) / len(ratios[m]))
    gain = sum(ratios[worst]) / len(ratios[worst])
    return [f"`{worst}` has the least improvement over the seed (x{gain:.3f} in cycles); its shapes are "
            "the ones to work on"]


PLAN_TABLE = PromptSource("chiacache_plan_table", _plan_table, doc="the BUFFER and TILE lines of the parent")
WORST_MEMBER = TacticSource("worst_member", _worst_member)

KERNEL = Template(
    name="chiacache.Kernel",
    variables=[
        Variable("l2.size_kb", Range(64, 65536), {"fixed"}, doc="the last-level cache the simulation configures, KB"),
        Variable("l2.ways", Range(1, 64), {"fixed"}, doc="its associativity"),
        Variable("l2.line_bytes", Enum((32, 64, 128)), {"fixed"}, doc="its line size"),
        Variable("l1.size_kb", Range(8, 512), {"fixed"}, doc="the first-level data cache, KB"),
        Variable("isa.ext", Enum(("plain_c",)), {"fixed"},
                 doc="plain_c: the kernels are portable C with no inline assembly, intrinsics or pragmas"),
        Variable("kernel.op", Enum(("gemm",)), {"fixed"}, doc="C = A x B, row-major, C overwritten"),
        Variable("kernel.dtype", Enum(("fp32",)), {"fixed"}, doc="the element type"),
    ],
    generators={"harness": gen_harness,
                "kernels": lambda ctx: seed_generator(ctx, "naive")[0]},   # the artifact's base text: the naive plan
    seed_generator=seed_generator,
    seeds=("naive", "tiled_l2", "packed_tiled"),
    line_kinds=[LineKind("BUFFER", parse_buffer, check_buffer), LineKind("TILE", parse_tile, check_tile)],
    comment_syntax={"c": "//"},
    doc="Four GEMM kernels in C, one per shape class (small, large, tall, wide), measured under a "
        "cache simulation of the fixed L1 and L2; the declaration block states the plan as BUFFER "
        "(the bytes the plan keeps resident) and TILE (the block sizes per kernel) lines, which the "
        "checks hold against the capacity.",
)
