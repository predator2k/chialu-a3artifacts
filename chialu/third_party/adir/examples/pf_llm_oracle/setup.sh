#!/bin/bash
# Build everything this example measures with: ChampSim carrying the lmhint
# L1D module, Intel Pin and the ChampSim pintool, the benchmarks, and one
# trace per benchmark.
#
#   ROOT=/somewhere/with/space ./setup.sh
#
# Nothing here is licensed: ChampSim is Apache-2.0, Pin is free for
# non-commercial use, the benchmarks are in bench/. The traces are cut from
# binaries built right here, which is the point -- a ChampSim trace record
# carries the PC but no opcode, so a hint generator that reads disassembly
# needs the binary the trace came from. `-no-pie` keeps an objdump address
# equal to the PC in the trace.
set -euo pipefail
ROOT=${ROOT:-$PWD/.pfllm}
HERE=$(cd "$(dirname "$0")" && pwd)
JOBS=${JOBS:-8}
TRACE_INSTRUCTIONS=${TRACE_INSTRUCTIONS:-50000000}
PIN_URL=${PIN_URL:-https://software.intel.com/sites/landingpage/pintool/downloads/pin-external-3.31-98869-gfa6f126a8-gcc-linux.tar.gz}
mkdir -p "$ROOT"/{tools,traces,bench/bin,work}
export TMPDIR=${TMPDIR:-$ROOT/tmp}; mkdir -p "$TMPDIR"

echo "== ChampSim"
[ -d "$ROOT/champsim" ] || git clone https://github.com/ChampSim/ChampSim "$ROOT/champsim"
cp -r "$HERE/lmhint" "$ROOT/champsim/prefetcher/lmhint" 2>/dev/null || cp "$HERE"/lmhint/* "$ROOT/champsim/prefetcher/lmhint/"
cd "$ROOT/champsim"
git submodule update --init
./vcpkg/bootstrap-vcpkg.sh -disableMetrics
./vcpkg/vcpkg install
python3 - "$ROOT" <<'PY'
import json, sys
c = json.load(open("champsim_config.json"))
c["L1D"]["prefetcher"] = "lmhint"          # the ensemble, the PHT and the PHB live in one module
c["executable_name"] = "champsim_lmhint"   # every configuration is an env var, so one binary serves all
json.dump(c, open(sys.argv[1] + "/lmhint_config.json", "w"), indent=1)
PY
./config.sh "$ROOT/lmhint_config.json"
make -j"$JOBS"

echo "== Intel Pin and the ChampSim pintool"
if [ ! -d "$ROOT/tools/pin" ]; then
  curl -sSL -o "$TMPDIR/pin.tar.gz" "$PIN_URL"
  tar xzf "$TMPDIR/pin.tar.gz" -C "$ROOT/tools" && rm "$TMPDIR/pin.tar.gz"
  mv "$ROOT"/tools/pin-external-* "$ROOT/tools/pin"
fi
PIN_ROOT="$ROOT/tools/pin" make -C "$ROOT/champsim/tracer/pin"

echo "== benchmarks: the GAP suite (-no-pie: an objdump address is the PC in the trace)"
# SERIAL=1 matters: OpenMP would make the trace non-deterministic, and ChampSim
# models one core here. The marker patch puts the region of interest around the
# kernel call in benchmark.h, which covers all eight kernels at once.
[ -d "$ROOT/gapbs" ] || git clone https://github.com/sbeamer/gapbs "$ROOT/gapbs"
python3 - "$ROOT/gapbs/src/benchmark.h" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); t = p.read_text()
if "__champsim_start_trace" not in t:
    t = t.replace("#ifndef BENCHMARK_H_\n#define BENCHMARK_H_", """#ifndef BENCHMARK_H_
#define BENCHMARK_H_
extern "C" {
__attribute__((noinline)) void __champsim_start_trace(void) { __asm__ volatile(""); }
__attribute__((noinline)) void __champsim_stop_trace(void) { __asm__ volatile(""); }
}""")
    t = t.replace("    auto result = kernel(g);",
                  "    __champsim_start_trace();\n    auto result = kernel(g);\n    __champsim_stop_trace();")
    p.write_text(t)
PY
make -C "$ROOT/gapbs" SERIAL=1 CXX_FLAGS="-std=c++11 -O3 -w -no-pie -fno-pie" -j"$JOBS"
for b in bfs pr sssp cc; do cp "$ROOT/gapbs/$b" "$ROOT/bench/bin/$b"; done

# The four single-pattern C benchmarks in bench/ are kept as a fast check that
# the pipeline is wired up; they are too small to measure anything with.
for b in bfs spmv chase_mix gemm_tiled; do
  gcc -O2 -march=x86-64 -no-pie -fno-pie -I"$HERE/bench" -o "$ROOT/bench/toy_$b" "$HERE/bench/$b.c"
done

echo "== traces"
for b in bfs pr sssp cc; do
  [ -s "$ROOT/traces/$b.champsim" ] && continue
  "$ROOT/tools/pin/pin" -t "$ROOT/champsim/tracer/pin/obj-intel64/champsim_tracer.so" \
    -o "$ROOT/traces/$b.champsim" -t "$TRACE_INSTRUCTIONS" \
    -start_symbol __champsim_start_trace -stop_symbol __champsim_stop_trace \
    -- "$ROOT/gapbs/$b" -g 20 -n 3
done

cat <<ENV

Ready. Export these before `adir check | seeds | run`:

  export BENCH_DIR=$ROOT/bench/bin
  export TRACE_DIR=$ROOT/traces
  export CHAMPSIM_BIN=$ROOT/champsim/bin/champsim_lmhint
  export PFLLM_WORK=$ROOT/work
  export PFLLM_WORKERS=32          # concurrent ChampSim processes
ENV
