# The evaluation tree's environment on the EDA host: chiALU and its ADIR from this tree first.
# Source after the host's own env.sh (the tools, the conda environment, gcc-toolset).
A3=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export PYTHONPATH="$A3/3rdparty/chialu/third_party/adir:$A3/3rdparty/chialu${PYTHONPATH:+:$PYTHONPATH}"
export CHIALU_SYNTH_REPORT=0
