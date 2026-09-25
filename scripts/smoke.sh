#!/bin/bash
# exp10 smoke test (run before exp10/run.sh, against the <host>-only cluster): 3 iterations each of
#   free best_of_n on int_subword_alu and on fp_alu_cmp,
#   one chiALU pipeline on fp_alu_cmp (seeds = run/fp_alu_cmp.surrogate3/discovered.json, front_1..front_8 incl.
#     front_3/front_4, the members the seed-relative screen dropped in exp9),
#   one plain loop on int_subword_alu;
# run dirs run/smoke10.*; rc of every step in logs/smoke_driver.log; then smoke_check.py asserts the audit's fixes.
set -u
source $CHIALU_HOME/chialu-env.sh >/dev/null 2>&1
export TMPDIR=$CHIALU_HOME/tmp
export RAY_ADDRESS=${THIS_MACHINE:?}:${CHIA_RAY_PORT:-6395}
export ADIR_RAY_SCHEDULING=SPREAD ADIR_HISTORY_NOTES=1
unset ADIR_UNIT_HIERARCHY_NOTE
cd $CHIALU || exit 1
E=$CHIALU_HOME/exp10; L=$E/logs; A=$A3EVAL; IT=3; P=smoke10
mkdir -p $L
log() { echo "$(date '+%F %T') $*" >> $L/smoke_driver.log; }
{ for r in "a3eval $A" "chiALU $CHIALU" "ADIR $CHIALU/third_party/adir" "chia $CHIALU_HOME/src/chia"; do
    set -- $r; echo "$1 $(git -C $2 rev-parse HEAD) dirty=$(git -C $2 status --porcelain --untracked-files=no | wc -l)"; done
} > $L/smoke_commits.txt
withnote() { local N=$1; shift; if [ "$N" = int_subword_alu ]; then env ADIR_UNIT_HIERARCHY_NOTE=1 "$@"; else env -u ADIR_UNIT_HIERARCHY_NOTE "$@"; fi; }
arch() { python3 $A/harness/archive_sessions.py $1 --jobs 4 >> $L/smoke_archive.log 2>&1; log "archive $1 rc=$?"; }
for d in run/$P.*; do [ -e "$d" ] && { echo "stale $d: move it away first" >&2; exit 1; }; done

free() { local yaml=$1 N=$2 tag=$3 d=run/$P.$2.$3 rc
  withnote $N python3 -m adir.cli seeds $yaml --run-dir $d >> $L/$P.$N.$tag.log 2>&1; rc=$?; log "$N.$tag seeds rc=$rc"
  withnote $N python3 -m adir.cli run $yaml --run-dir $d --iterations $IT --seed 1 >> $L/$P.$N.$tag.log 2>&1; rc=$?
  log "$N.$tag run rc=$rc"; arch $d; }
chialu() { local F=$1 N=$2 d=run/$P.$2.chialu rc
  mkdir -p $d && cp run/$N.surrogate3/discovered.json $d/
  withnote $N python3 -m chialu.pipeline targets/$F --run-dir $d --synth-repeats 3 --stage seeds >> $L/$P.$N.chialu.log 2>&1
  rc=$?; log "$N.chialu seeds rc=$rc"
  withnote $N python3 -m chialu.pipeline targets/$F --run-dir $d --synth-repeats 3 --stage search --search-iterations $IT \
    --search-seed 1 >> $L/$P.$N.chialu.log 2>&1; rc=$?; log "$N.chialu search rc=$rc"; arch $d; }
plain() { local F=$1 N=$2 d=run/$P.$2.plain rc
  withnote $N python3 $A/harness/plain_loop.py targets/$F --calls $IT --out $d --provider deepseek --model deepseek-flash \
    >> $L/$P.$N.plain.log 2>&1; rc=$?; log "$N.plain rc=$rc"; arch $d; }

log "smoke10 launch"
free targets/int_subword_alu.free_best_of_n.yaml int_subword_alu best_of_n &
free targets/eval/fp_alu_cmp.free_best_of_n.yaml fp_alu_cmp best_of_n &
chialu eval/fp_alu_cmp.yaml fp_alu_cmp &
plain int_subword_alu.yaml int_subword_alu &
wait
log "smoke10 steps returned"
python3 $E/smoke_check.py --prefix $P --iterations $IT > $L/smoke_check.txt 2>&1
rc=$?; log "smoke_check rc=$rc (logs/smoke_check.txt)"; cat $L/smoke_check.txt; exit $rc
