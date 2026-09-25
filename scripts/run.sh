#!/bin/bash
# exp10 (after the 2026-09-25 full audit, exp9 aborted): ONE launch, no auto-restart. 54 runs, 20 iterations each
# (iteration = one prompt to the coding agent + one evaluation), every evaluation through the <host>-only Ray
# cluster ($CHIALU_HOME/cluster_head.yaml; bring it up first), DeepSeek deepseek-flash, synthesis
# median of 3.
#   chiALU (chialu.pipeline from run/<t>.surrogate3/discovered.json, --synth-repeats 3)  x3 targets x3
#   free best_of_n / beam_search / adaevolve                                              x3 targets x3
#   plain loop (--provider deepseek --model deepseek-flash)                              x3 targets x3
#   hand_adaevolve from FPnew PARALLEL / HardFloat / TransDot MERGED                     x3
# ADIR_UNIT_HIERARCHY_NOTE=1 for the int target only (unset everywhere else). The rc of every step (seeds and run
# separately) goes to logs/driver.log; a failed step is logged and NOT restarted. Completion is judged afterwards
# from each run's status.json / iteration.txt / pipeline.json (plain: summary.json) into logs/completion.tsv.
set -u
source $CHIALU_HOME/chialu-env.sh >/dev/null 2>&1
export TMPDIR=$CHIALU_HOME/tmp
export RAY_ADDRESS=${THIS_MACHINE:?}:${CHIA_RAY_PORT:-6395}          # explicit: the <host>-only cluster (THIS_MACHINE:CHIA_RAY_PORT)
export ADIR_RAY_SCHEDULING=SPREAD ADIR_HISTORY_NOTES=1
unset ADIR_UNIT_HIERARCHY_NOTE
cd $CHIALU || exit 1
E=$CHIALU_HOME/exp10; L=$E/logs; A=$A3EVAL; IT=20; P=exp10
mkdir -p $L
log() { echo "$(date '+%F %T') $*" >> $L/driver.log; }

# ---- provenance: the commit of every repository at the start ------------------------------------------
{ echo "# exp10 start $(date '+%F %T'); RAY_ADDRESS=$RAY_ADDRESS"
  for r in "a3eval $A" "chiALU $CHIALU" "ADIR $CHIALU/third_party/adir" "chia $CHIALU_HOME/src/chia"; do
    set -- $r
    echo "$1 $(git -C $2 rev-parse HEAD) dirty=$(git -C $2 status --porcelain --untracked-files=no | wc -l) $2"
  done
  echo "opencode $(opencode --version 2>/dev/null) OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX=${OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX:-}"
} > $L/commits.txt
python3 -c "import ray; ray.init(address='$RAY_ADDRESS', log_to_driver=False); print('cluster', ray.cluster_resources())" \
  >> $L/commits.txt 2>&1 || { log "no Ray cluster at $RAY_ADDRESS; not launching"; exit 1; }

# the unit-hierarchy note for the int target only; the variable is absent (not 0) for every other run
withnote() { local N=$1; shift; if [ "$N" = int_subword_alu ]; then env ADIR_UNIT_HIERARCHY_NOTE=1 "$@"; else env -u ADIR_UNIT_HIERARCHY_NOTE "$@"; fi; }
arch() { python3 $A/harness/archive_sessions.py $1 --jobs 4 >> $L/archive.log 2>&1; log "archive $1 rc=$?"; }

chialu() { local F=$1 N=$2 k=$3 d=run/$P.$2.chialu.r$3 rc
  mkdir -p $d && cp run/$N.surrogate3/discovered.json $d/
  log "$N.chialu r$k seeds start"
  withnote $N python3 -m chialu.pipeline targets/$F --run-dir $d --synth-repeats 3 --stage seeds >> $L/$N.chialu.r$k.log 2>&1
  rc=$?; log "$N.chialu r$k seeds end rc=$rc"
  withnote $N python3 -m chialu.pipeline targets/$F --run-dir $d --synth-repeats 3 --stage search \
    --search-iterations $IT --search-seed $k >> $L/$N.chialu.r$k.log 2>&1
  rc=$?; log "$N.chialu r$k search end rc=$rc"
  arch $d; }
free() { local yaml=$1 N=$2 tag=$3 k=$4 d=run/$P.$2.$3.r$4 rc
  log "$N.$tag r$k seeds start"
  withnote $N python3 -m adir.cli seeds $yaml --run-dir $d >> $L/$N.$tag.r$k.log 2>&1
  rc=$?; log "$N.$tag r$k seeds end rc=$rc"
  withnote $N python3 -m adir.cli run $yaml --run-dir $d --iterations $IT --seed $k >> $L/$N.$tag.r$k.log 2>&1
  rc=$?; log "$N.$tag r$k run end rc=$rc"
  arch $d; }
plain() { local F=$1 N=$2 k=$3 d=run/$P.$2.plain.r$3 rc
  log "$N.plain r$k start"
  withnote $N python3 $A/harness/plain_loop.py targets/$F --calls $IT --out $d --provider deepseek --model deepseek-flash \
    >> $L/$N.plain.r$k.log 2>&1
  rc=$?; log "$N.plain r$k end rc=$rc"
  arch $d; }

log "exp10 launch"
declare -A TF=([int_subword_alu]=int_subword_alu.yaml [fp_alu_cmp]=eval/fp_alu_cmp.yaml [fp_alu_cmp_hf]=eval/fp_alu_cmp_hf.yaml)
for k in 1 2 3; do
  for N in int_subword_alu fp_alu_cmp fp_alu_cmp_hf; do F=${TF[$N]}; S=targets/${F%.yaml}
    chialu $F $N $k &
    for b in best_of_n beam_search adaevolve; do free $S.free_$b.yaml $N $b $k & done
    plain $F $N $k &
  done
  # the hand targets are fp: no unit-hierarchy note
  for ref in fpnew hardfloat transdot; do free targets/eval/fp_alu_cmp_${ref}.hand_adaevolve.yaml $ref hand_adaevolve $k & done
done
wait
log "exp10 all steps returned"

# ---- completion: from the runs' own records, not from the exit codes ------------------------------------
python3 - "$CHIALU/run" "$P" "$IT" > $L/completion.tsv 2>> $L/driver.log <<'PY'
import json, sys
from pathlib import Path
root, prefix, it = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])
def js(p):
    try:
        return json.loads(p.read_text())
    except Exception:
        return None
print("run\tcomplete\titerations\tstate\tdetail")
for d in sorted(root.glob(f"{prefix}.*")):
    detail = ""
    if ".plain." in d.name:
        s = js(d / "summary.json") or {}
        n, state = int(s.get("calls") or 0), ("done" if s else "no summary.json")
        ok = n >= it
    else:
        st = js(d / "status.json") or {}
        state = st.get("state", "no status.json")
        try:
            n = int((d / "iteration.txt").read_text().strip())
        except Exception:
            n = 0
        ok = state == "done" and n >= it
        if ".chialu." in d.name:
            pj = js(d / "pipeline.json") or {}
            ex = {k: (v.get("exit") if isinstance(v, dict) else v) for k, v in (pj.get("stages") or {}).items()}
            detail = f"pipeline stages {ex} synth_repeats={pj.get('synth_repeats')}"
            ok = ok and ex.get("seeds") == 0 and ex.get("search") == 0
    print(f"{d.name}\t{'yes' if ok else 'NO'}\t{n}\t{state}\t{detail}")
PY
log "exp10 done: $(grep -c $'\tyes\t' $L/completion.tsv) complete of $(($(wc -l < $L/completion.tsv) - 1)) runs (logs/completion.tsv)"
