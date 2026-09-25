#!/bin/bash
# Table A: 3 ALU targets x (chiALU, best_of_n, beam_search, adaevolve, plain loop) x 3 repetitions.
# Phase 1: 20 iterations; phase 2: every run resumed to 70 in all.
source $CHIALU_HOME/chialu-env.sh >/dev/null 2>&1
export RAY_ADDRESS=<HEAD_IP>:6395
cd $CHIALU
L=$CHIALU_HOME/exp/logs
T=$CHIALU_HOME/exp/timing.jsonl
N1=${N1:-20}; N2=${N2:-70}
stamp() { echo "{\"job\": \"$1\", \"leg\": \"$2\", \"event\": \"$3\", \"t\": $(date +%s), \"rc\": ${4:-null}}" >> $T; }
leg() { local j=$1 g=$2; shift 2; stamp $j $g start; "$@" >> $L/$j.log 2>&1; local rc=$?; stamp $j $g end $rc; }
chialu() { # target file, name, k
  local f=$1 n=$2 k=$3 d=run/exp.$2.chialu.r$3 j=$2.chialu.r$3
  mkdir -p $d && cp run/$n.surrogate/discovered.json $d/
  leg $j first  python3 -m chialu.pipeline targets/$f --run-dir $d --stage seeds --stage search --search-iterations $N1 --search-seed $k
  leg $j extend python3 -m chialu.pipeline targets/$f --run-dir $d --resume --search-iterations $N2
}
free() { # target file stem, name, backend, k
  local s=$1 n=$2 b=$3 k=$4 d=run/exp.$2.$3.r$4 j=$2.$3.r$4
  leg $j seeds  python3 -m adir.cli seeds targets/$s.free_$b.yaml --run-dir $d
  leg $j first  python3 -m adir.cli run targets/$s.free_$b.yaml --run-dir $d --iterations $N1 --seed $k
  leg $j extend python3 -m adir.cli run targets/$s.free_$b.yaml --run-dir $d --resume --iterations $N2
}
plain() { # target file, name, k
  local f=$1 n=$2 k=$3 d=run/exp.$2.plain.r$3 j=$2.plain.r$3
  leg $j first  python3 ../../harness/plain_loop.py targets/$f --calls $N1 --out $d
  leg $j extend python3 ../../harness/plain_loop.py targets/$f --calls $N2 --out $d --resume
}
for k in 1 2 3; do
  for spec in "int_subword_alu.yaml int_subword_alu int_subword_alu" "eval/fp_alu_cmp.yaml fp_alu_cmp eval/fp_alu_cmp" "eval/fp_alu_cmp_hf.yaml fp_alu_cmp_hf eval/fp_alu_cmp_hf"; do
    set -- $spec
    chialu $1 $2 $k &
    for b in best_of_n beam_search adaevolve; do free $3 $2 $b $k & done
    plain $1 $2 $k &
  done
done
wait
echo ALL DONE >> $L/driver.log
