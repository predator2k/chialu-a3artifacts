#!/bin/bash
# Emit the HardFloat FMA cascades' Verilog with the repository's own sbt flow (Chisel 3.5.6,
# Scala 2.13; on the host `~/tools/sbt/bin/sbt` with Java 8, as baselines/hardfloat/build.sh).
# The Scala file is copied into the checkout's source tree for the run and removed after,
# so the submodule stays clean. Two rows: <out>/fp16/dot_core.v (two terms) and
# <out>/fp8/dot_core.v (four terms).
#   baselines/hardfloat_dot/build.sh <out dir>
set -e
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../.." && pwd)
hf=$root/3rdparty/berkeley-hardfloat
out=${1:-$root/runs/tableb/hardfloat_dot}
mkdir -p "$out/fp16" "$out/fp8" "$hf/hardfloat/src/main/scala/eval"
cp "$here/HardFloatDotCore.scala" "$hf/hardfloat/src/main/scala/eval/"
cd "$hf"
SBT=${SBT:-sbt}
$SBT -batch "runMain hardfloat.eval.GenDotCoreFp16 --target-dir $out/fp16" \
             "runMain hardfloat.eval.GenDotCoreFp8 --target-dir $out/fp8"
rm -f "$hf/hardfloat/src/main/scala/eval/HardFloatDotCore.scala"
ls -la "$out/fp16" "$out/fp8"
