"""The SpmGemm template: a workload of the paper (M, K, N), the SVE
vector length and the SPM version are fixed; the K-tile `kc` and the
M-tile `mc` are searched or fixed; the driver loop nest is the seed
artifact, the harness is generated, the microkernel headers come from
the artifact checkout."""
from __future__ import annotations

import os
import re
from pathlib import Path

from adir import BindError, Elaboration, Enum, PromptSource, Range, Template, Variable

# the paper's workloads: name -> (M, K, N)
WORKLOADS = {"W1": (128, 4096, 11008), "W2": (256, 4096, 4096), "W3": (256, 2048, 2048),
             "W4": (512, 768, 768), "W5": (2048, 2048, 2048), "W6": (2048, 64, 2048),
             "W7": (784, 256, 1024)}
# The artifact's pinned cells (v3, per VL): workload -> vl -> (KC, MC). Transcribed from the
# `-o "M K N iter KC MC"` of its own reference runs, experiments/vl_length/results/reference/
# W<n>_v3_vl<vl>.log, so a seed is the cell the paper reports and not a guess. Note W4 at VL4:
# MC 784 over an M of 512, which is why no bound ties MC to the workload's M.
BEST = {"W1": {16: (320, 128), 8: (512, 128), 4: (1024, 128)},
        "W2": {16: (320, 256), 8: (512, 256), 4: (512, 256)},
        "W3": {16: (320, 256), 8: (512, 256), 4: (512, 256)},
        "W4": {16: (256, 256), 8: (384, 256), 4: (768, 784)},
        "W5": {16: (320, 512), 8: (512, 1024), 4: (1024, 1024)},
        "W6": {16: (64, 512), 8: (64, 1024), 4: (64, 1024)},
        "W7": {16: (256, 784), 8: (256, 784), 4: (256, 784)}}
KC_MAX = {4: 1024, 8: 512, 16: 341}      # SPM capacity per VL (sets consumed per B slice); the
                                         # one source: the harness prints it, `elaborate` bounds
                                         # `kc` by it, and nodes.SPM_PORTS carries the port counts


DRIVER_SRC = "kernels/gemm/cacheflex/src/v3_fused.cpp"
# the host-side timers of the artifact's main: `Clock::now()` is not compiled out under
# GEM5, so they sit inside the measured ROI, and a candidate that merely deleted them
# would read as a speedup. They go, and every candidate is measured without them.
_TIMERS = re.compile(r"^\s*(auto _t = _now\(\);|t_(packA|packB|kernel) \+= us_since\(_t\);"
                     r"|\+\+(packA|spmcp)_calls;)\s*$")
# the buffers are locals of that main and parameters of `gemm_v3`; MOCK_SPM's `B_tile`
# and the SPM path's `B_pad` are one padded tile, which the harness allocates once
_BUFFERS = (("A.data()", "A"), ("B.data()", "B"), ("C.data()", "C"),
            ("A_mc.data()", "A_mc"), ("B_tile.data()", "B_pad"), ("B_pad.data()", "B_pad"))


def artifact_root() -> Path:
    root = os.environ.get("CACHEFLEX_ROOT")
    if not root:
        raise BindError("cacheflex", "CACHEFLEX_ROOT is unset: the seed is read from the "
                                     "artifact checkout (github.com/JingqunZhang/cacheflex-ae), "
                                     "the same variable its own build.sh requires")
    return Path(root).expanduser()


def nest_from_artifact() -> str:
    """The ROI loop nest of the artifact's `v3_fused` driver, as the body of
    `gemm_v3`. The artifact writes it inline in `main`, so the extraction is
    the ROI between its markers, less the host timers, with the buffers
    renamed to the parameters. Nothing about the loop order, the SPMCP call
    sites, the accumulate flag or the padding path is rewritten here: the
    seed is the artifact's, and a change upstream changes the seed."""
    src = artifact_root() / DRIVER_SRC
    if not src.is_file():
        raise BindError("cacheflex", f"no {src}: CACHEFLEX_ROOT does not name a cacheflex-ae checkout")
    text = src.read_text()
    if "ROI_BEGIN();" not in text or "ROI_END();" not in text:
        raise BindError("cacheflex", f"{src} carries no ROI_BEGIN()/ROI_END(): the driver changed "
                                     f"shape and this extraction needs rewriting")
    body = text.split("ROI_BEGIN();", 1)[1].split("ROI_END();", 1)[0]
    body = "\n".join(l for l in body.splitlines() if not _TIMERS.match(l))
    for old, new in _BUFFERS:
        body = body.replace(old, new)
    body = re.sub(r"\n{3,}", "\n\n", body).strip("\n").rstrip()
    if "spm_gemm_fused_8x3VL" not in body or "pack_A_fp16_8row" not in body:
        raise BindError("cacheflex", f"the ROI of {src} calls neither the SPM microkernel nor the "
                                     f"A pack; the extraction found the wrong region")
    return body


def shapes_of(binding) -> list:
    """The workloads a binding names: one where it is `fixed`, the set
    where it is `runtime`. The binding is the only place a run says which
    shapes it is about, so the prompt, the seed and the graph read it
    rather than each carrying a list."""
    return [str(binding.value)] if binding.time == "fixed" else [str(m) for m in binding.members]


def gen_driver(ctx) -> str:
    """The seed: the artifact's own v3_fused loop nest, lifted out of its
    `main` into `gemm_v3(...)`. The text above the EVOLVE region (the
    microkernel headers) is fixed and matches the artifact's include set."""
    return r'''// the artifact's headers (fixed text above the mutable region): the microkernels, the packers, the buffers
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <algorithm>
#ifdef MOCK_SPM
#  include "kernels_sve.hpp"
#  include "kernels_fused.hpp"
#else
#  include "kernels_spm.hpp"
#  include "kernels_fused.hpp"
#endif
// gemm_v3: the loop nest around the fixed SPM microkernel, as cacheflex-ae writes it in
// kernels/gemm/cacheflex/src/v3_fused.cpp. A: M x K, B: K x N, C: M_pad x N_pad (row-major,
// fp16). KC and MC are the K and M tile sizes; NT = 3 * VL halfwords is the N tile the
// microkernel computes. A_mc holds one packed A block, B_pad one padded B tile.
static void gemm_v3(size_t M, size_t K, size_t N, size_t KC, size_t MC,
                    const __fp16* A, const __fp16* B, __fp16* C, size_t N_pad,
                    __fp16* A_mc, __fp16* B_pad)
{
    const size_t NT = 3 * svcnth();
    const size_t MT = 8;
__NEST__
}
'''.replace("__NEST__", nest_from_artifact())


def gen_harness(ctx) -> str:
    """The driver's main: the artifact's headers, the operands, the ROI
    around one gemm_v3 call, the checksum; under VERIFY (the QEMU mock
    build) a naive reference and the maximum error. The SPM capacity cap
    is written in from `KC_MAX` at the bound vector length, so the
    binary, the searched domain and the card cannot drift apart."""
    kc_max = KC_MAX[int(ctx.value("vl"))]
    return r'''
#include "common_print.hpp"
#include <cmath>

// ADIR-DRIVER: the loop nest is the mutable part above this point; it is included before these lines
int main(int argc, char** argv)
{
    const size_t M  = (argc > 1) ? (size_t)atoi(argv[1]) : 784;
    const size_t K  = (argc > 2) ? (size_t)atoi(argv[2]) : 256;
    const size_t N  = (argc > 3) ? (size_t)atoi(argv[3]) : 1024;
    const int NITER = (argc > 4) ? atoi(argv[4]) : 1;
    const size_t KC = (argc > 5) ? (size_t)atoi(argv[5]) : 256;
    const size_t MC = (argc > 6) ? (size_t)atoi(argv[6]) : 784;
    const size_t KC_MAX = __KC_MAX__;          // the SPM capacity at the bound vector length
    // the artifact guards this in its SPM build alone; here the QEMU mock refuses it too, so an
    // over-wide KC costs a QEMU run rather than a gem5 cell. `kc`'s domain makes it unreachable.
    if (KC > KC_MAX) { fprintf(stderr, "FATAL: KC=%zu exceeds the SPM capacity cap %zu for this VL\n", KC, KC_MAX); return 1; }
    const size_t NT = 3 * svcnth(), MT = 8;
    const size_t M_pad = ((M + MT - 1) / MT) * MT;
    const size_t N_pad = ((N + NT - 1) / NT) * NT;
    const size_t max_ab = (MC + MT - 1) / MT;
    AlignedBuffer<__fp16> A(M * K), B(K * N), C(M_pad * N_pad);
    fill_random(A.data(), M * K, -0.1f, 0.1f, 1);
    fill_random(B.data(), K * N, -0.1f, 0.1f, 2);
    std::memset(C.data(), 0, M_pad * N_pad * sizeof(__fp16));
    AlignedBuffer<__fp16> A_mc(max_ab * MT * KC);
    std::memset(A_mc.data(), 0, max_ab * MT * KC * sizeof(__fp16));
    AlignedBuffer<__fp16> B_pad(KC * NT);
    std::memset(B_pad.data(), 0, KC * NT * sizeof(__fp16));
    printf("=== gemm_v3 === M=%zu K=%zu N=%zu KC=%zu MC=%zu NT=%zu\n", M, K, N, KC, MC, NT);
#ifdef GEM5
    m5_reset_stats(0, 0);
#endif
    ROI_BEGIN();
    for (int it = 0; it < NITER; ++it)
        gemm_v3(M, K, N, KC, MC, A.data(), B.data(), C.data(), N_pad, A_mc.data(), B_pad.data());
    ROI_END();
#ifdef GEM5
    m5_dump_stats(0, 0);
#endif
    print_checksum_logical(C.data(), M, N, N_pad);
#ifdef VERIFY
    double maxerr = 0.0, maxref = 0.0;
    for (size_t i = 0; i < M; ++i)
        for (size_t j = 0; j < N; ++j) {
            float acc = 0.0f;
            for (size_t k = 0; k < K; ++k) acc += (float)A.data()[i * K + k] * (float)B.data()[k * N + j];
            double ref = (double)(__fp16)acc, got = (double)(float)C.data()[i * N_pad + j];
            maxerr = std::max(maxerr, std::fabs(ref - got));
            maxref = std::max(maxref, std::fabs(ref));
        }
    // fp16 accumulation over K terms: the error grows with the length of the sum, so a
    // tolerance calibrated on one K refuses a correct kernel at a larger one. sqrt(K/256)
    // normalises to the reference shape and never tightens below it. A real fault is two
    // orders of magnitude away -- a doubly accumulated column reads 0.25, not 0.002.
    double kscale = std::sqrt((double)K / 256.0);
    if (kscale < 1.0) kscale = 1.0;
    double tol = 2e-3 * kscale * (maxref > 1.0 ? maxref : 1.0);
    printf("VERIFY %s maxerr=%g tol=%g\n", maxerr <= tol ? "OK" : "MISMATCH", maxerr, tol);
    return maxerr <= tol ? 0 : 1;
#endif
    return 0;
}
'''.replace("__KC_MAX__", str(kc_max))


def elaborate(bindings):
    """`kc` exists inside the SPM capacity at this vector length, so a run
    file that widens it is a bind error rather than a search whose every
    candidate aborts in the binary. No such bound ties `mc` to the
    workload: the artifact's own W4 cell at VL4 pins MC 784 over an M of
    512, so M is guidance for the model, not a cap."""
    vl = int(bindings["vl"].value)
    names = shapes_of(bindings["workload"])
    ms = [WORKLOADS[w][0] for w in names]
    ks = [WORKLOADS[w][1] for w in names]
    k_txt = (f"this workload's K is {ks[0]}" if len(names) == 1
             else f"the measured K range from {min(ks)} to {max(ks)}")
    m_txt = (f"this workload's M is {ms[0]}" if len(names) == 1
             else f"the measured M range from {min(ms)} to {max(ms)}")
    return Elaboration(
        variables=[
            Variable("kc", Range(32, KC_MAX[vl]), {"fixed", "search"},
                     doc=f"the K tile (rows of B per SPMCP); the SPM holds {KC_MAX[vl]} rows at VL {vl}, "
                         f"and {k_txt}, above which KC only widens the SPM tile"),
            Variable("mc", Range(8, 2048), {"fixed", "search"},
                     doc=f"the M tile (rows of A packed per block); a multiple of 8 keeps the last "
                         f"block full, and {m_txt}"),
        ],
        info={"kc_max": KC_MAX[vl], "nt": 3 * vl * 8})


def seed_generator(ctx, name):
    """The `paper` seed: the artifact's loop nest at the KC and MC its own
    reference run for this workload and vector length used. A pair the
    table does not carry is an error rather than a guess -- the seed is
    what `ratio_to_seed` scores every candidate against."""
    names = shapes_of(ctx.instance.bindings["workload"])
    # one declaration serves every shape the run measures, and the artifact pins a cell per
    # shape; the first is the reference the tiles start from and the search moves them
    w = names[0]
    vl = int(ctx.value("vl"))
    pinned = BEST.get(w, {}).get(vl)
    if pinned is None:
        raise BindError("cacheflex", f"no pinned cell for {w} at VL {vl}: BEST carries "
                                     f"{sorted(BEST)} from the artifact's reference logs")
    kc, mc = pinned
    vars_ = {}
    if not ctx.has("kc") or ctx.instance.bindings["kc"].time == "search":
        vars_["kc"] = kc
    if not ctx.has("mc") or ctx.instance.bindings["mc"].time == "search":
        vars_["mc"] = mc
    return gen_driver(ctx), vars_, []


def _layout(instance, archive, parent) -> str:
    vl = int(instance.bindings["vl"].value)
    info = instance.elaboration.info          # the same numbers `kc`'s domain was bound from
    nt, kc_max = info["nt"], info["kc_max"]
    names = shapes_of(instance.bindings["workload"])
    rows = []
    for w in names:
        M, K, N = WORKLOADS[w]
        ntiles = -(-N // nt)
        tail = N - (ntiles - 1) * nt
        rows.append(f"| `{w}` | {M} | {K} | {N} | {ntiles} | "
                    f"{'none' if tail == nt else tail} | {-(-K // kc_max)} |")
    head = ("## The scratchpad and the shapes measured\n\n"
            f"* SVE vector length {vl} x 128 bits: the microkernel computes 8 rows by 3 x {vl * 8} "
            f"columns per call (NT = {nt})\n"
            f"* the SPM holds one K-tile of B: KC at most {kc_max} at this VL (the binary refuses "
            f"more); MC rows of A are packed per M block\n"
            "* SPMCP calls per GEMM = ceil(K/KC) x ceil(M/MC) x ceil(N/NT)\n\n")
    if len(names) == 1:
        M, K, N = WORKLOADS[names[0]]
        return head + f"* the shape measured is {names[0]}: M={M} K={K} N={N}, fp16, one GEMM per cell\n"
    return head + ("Every shape below is measured and the goal is their geometric mean, so a change "
                   "that helps one and hurts another has to earn the difference. The nest is called "
                   "with M, K and N and may take a different path for each.\n\n"
                   "| shape | M | K | N | N tiles | tail | K tiles at KC max |\n"
                   "| --- | --- | --- | --- | --- | --- | --- |\n" + "\n".join(rows) + "\n")


LAYOUT = PromptSource("cacheflex_layout", _layout, static=True,
                      doc="the SPM layout, the workload's shape and the tile counts")

SPM_GEMM = Template(
    name="cacheflex.SpmGemm",
    variables=[
        Variable("workload", Enum(tuple(WORKLOADS)), {"fixed", "runtime"},
                 doc="the paper's workload: " + "; ".join(f"{k} = {v[0]}x{v[1]}x{v[2]}" for k, v in WORKLOADS.items())),
        Variable("vl", Enum((4, 8, 16)), {"fixed"}, doc="the SVE vector length in 128-bit units"),
        # `kc` and `mc` are the elaboration's: their bounds follow `vl` and `workload`
    ],
    elaborate=elaborate,
    generators={"driver": gen_driver, "harness": gen_harness},
    seed_generator=seed_generator,
    seeds=("paper",),
    comment_syntax={"cpp": "//"},
    doc="The loop nest that drives the CacheFlex SPM GEMM microkernel (gemm_v3) with the K and M "
        "tiles it uses; the microkernel, the A packing and the SPMCP copy are the artifact's and are "
        "fixed. A cell compiles the nest through the SPM encoder, checks it under QEMU and runs it "
        "on the artifact's gem5 fork.",
)
