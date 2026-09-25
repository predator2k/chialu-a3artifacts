source $CHIALU_HOME/chialu-env.sh >/dev/null 2>&1
export PYTHONPATH=$CHIALU_HOME/wt/adv:$A3EVAL/3rdparty/chialu/third_party/adir
export CHIALU=$CHIALU_HOME/wt/adv
export TMPDIR=$CHIALU_HOME/tmp
export CHIALU_VERILATOR_JOBS=1 CHIALU_SYNTH_JOBS=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export CHIALU_SIM_BUILD_CACHE=$CHIALU/measurements/adversarial/scratch/sim_cache
export CHIALU_SYNTH_RECORDS=$CHIALU/measurements/adversarial/scratch/synth_records
unset RAY_ADDRESS
