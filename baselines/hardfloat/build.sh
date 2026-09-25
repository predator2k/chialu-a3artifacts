#!/bin/bash
# Emit the HardFloat wrapper's Verilog with the repository's own sbt flow (Chisel 3.5.6,
# Scala 2.13, sbt 1.8.2; on the host `~/tools/sbt/bin/sbt` is a current launcher and
# Java 8 suffices). The Scala file is copied into the checkout's source tree for the
# run and removed after, so the submodule stays clean.
#   baselines/hardfloat/build.sh <out dir>
set -e
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../.." && pwd)
hf=$root/3rdparty/berkeley-hardfloat
out=${1:-$root/runs/hardfloat}
mkdir -p "$out" "$hf/hardfloat/src/main/scala/eval"
cp "$here/HardFloatAluCore.scala" "$hf/hardfloat/src/main/scala/eval/"
cd "$hf"
SBT=${SBT:-sbt}
$SBT -batch "runMain hardfloat.eval.GenAluCore --target-dir $out"
rm -f "$hf/hardfloat/src/main/scala/eval/HardFloatAluCore.scala"
ls -la "$out"
