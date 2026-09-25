#!/bin/bash
# Run the format probe with the repository's sbt flow (see build.sh).
set -e
here=$(cd "$(dirname "$0")" && pwd); root=$(cd "$here/../.." && pwd); hf=$root/3rdparty/berkeley-hardfloat
out=${1:-$root/runs/hardfloat/probe}; mkdir -p "$out" "$hf/hardfloat/src/main/scala/eval"
cp "$here/ProbeFormats.scala" "$hf/hardfloat/src/main/scala/eval/"
cd "$hf"; ${SBT:-sbt} -batch "runMain hardfloat.eval.ProbeFormats $out" 2>&1 | grep -E "PROBE|error\]" || true
rm -f "$hf/hardfloat/src/main/scala/eval/ProbeFormats.scala"
