# chialu-a3eval environment (sanitized template of the one used for exp10). Set CHIALU_HOME (a big scratch volume:
# tools, caches, agent workspaces) and A3EVAL (this repository) before sourcing.
#
# DISK POLICY: $HOME has a 5 GB quota (~2.4 GB free) and / (which
# carries /tmp) has ~5 GB free.  Everything this project writes must land
# on /data2.  That is enforced here by moving HOME itself, plus explicit
# overrides for the tools that ignore HOME.  .ssh and .gitconfig are
# symlinked back to the real home so git and ssh keep working.
#
# Source this file first in every shell:  source $CHIALU_HOME/chialu-env.sh

export CH=${CHIALU_HOME:?set CHIALU_HOME}
export REAL_HOME=$HOME
export HOME=$CH

export A3=${A3EVAL:?set A3EVAL to this repository}
export CHIALU=$A3/3rdparty/chialu

# ---- toolchain -------------------------------------------------------
export PATH=$CH/.opencode/bin:$CH/miniconda3/envs/chia_env/bin:$CH/tools/bin:$CH/tools/oss-cad-suite/bin:$CH/tools/google-cloud-sdk/bin:$CH/.local/bin:$CH/.npm-global/bin:$PATH
for _ts in 11 12 14; do
  if [ -f /opt/rh/gcc-toolset-$_ts/enable ]; then
    . /opt/rh/gcc-toolset-$_ts/enable
    break
  fi
done
unset _ts

# ---- python / chialu -------------------------------------------------
export PYTHONPATH=$CHIALU/third_party/adir:$CHIALU
export PYTHONNOUSERSITE=1          # never let ~/.local/lib shadow chia_env
export PYTHONUNBUFFERED=1
export CHIALU_VERILATOR_JOBS=6
export CHIALU_SYNTH_REPORT=1   # the synthesis reports (critical path, paths, area by hierarchy) as feedback for every method

# ---- every cache and scratch path off / and off the home quota -------
export TMPDIR=$CH/tmp
export ADIR_AGENT_ROOT=$CH/agent_ws   # agent call directories, outside every git repository (adir.confine)
export TMP=$TMPDIR
export TEMP=$TMPDIR
export XDG_CACHE_HOME=$CH/.cache
export XDG_CONFIG_HOME=$CH/.config
export XDG_DATA_HOME=$CH/.local/share
export XDG_STATE_HOME=$CH/.local/state
export CHIALU_SIM_BUILD_CACHE=$CH/.cache/chialu/sim_build
export CHIALU_SYNTH_CACHE=$CH/.cache/chialu/synth_unit
export CHIALU_LIBERTY_CACHE=$CH/.cache/chialu/liberty
# Ray makes every node use the head's temp-dir path (it refuses --temp-dir on a
# worker), and <host>'s /data2 does not exist on <host>.  So both machines carry
# the same short path as a symlink; only the link (a few bytes) is in /tmp, the
# session files land on the big volume.
export RAY_TMPDIR=/tmp/ray-$USER
if [ "$(readlink -f /tmp/ray-$USER 2>/dev/null)" != "$CH/ray_tmp" ]; then
  ln -sfnT $CH/ray_tmp /tmp/ray-$USER 2>/dev/null
fi
export RAY_DISABLE_IMPORT_WARNING=1
export CLOUDSDK_CONFIG=$CH/.config/gcloud
export PIP_CACHE_DIR=$CH/.pip-cache
export CONDA_PKGS_DIRS=$CH/.conda-pkgs
export CCACHE_DIR=$CH/.ccache
export SBT=$CH/tools/sbt/bin/sbt
export SBT_OPTS="-Dsbt.global.base=$CH/.sbt -Dsbt.ivy.home=$CH/.ivy2 -Dsbt.boot.directory=$CH/.sbt/boot -Duser.home=$CH"
export npm_config_prefix=$CH/.npm-global   # opencode's installer shells out to npm, which
export npm_config_cache=$CH/.npm           # reads an absolute prefix and ignores HOME; without
export NPM_CONFIG_PREFIX=$CH/.npm-global   # these it put 770 MB into the home quota
export NPM_CONFIG_CACHE=$CH/.npm
export BUN_INSTALL=$CH/.bun
export COURSIER_CACHE=$CH/.coursier

# ---- cluster ---------------------------------------------------------
export THIS_MACHINE=${THIS_MACHINE:-<HEAD_IP>}   # the Ray head / EDA host IP
export REMOTE_MACHINE="<IP>"      # optional second EDA host
export CHIA_RAY_PORT=6395                # 6379 and 6390 belong to other users
export GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null)
export VERTEX_LOCATION=global
export GOOGLE_VERTEX_LOCATION=global
export GOOGLE_VERTEX_PROJECT=$GOOGLE_CLOUD_PROJECT

# Provider credentials for opencode.  The model call does not run in the shell that
# starts a run -- chia dispatches it to a ray worker (task OpenCodeLLM.prompt), whose
# environment comes from this file.  Exporting the key only in the launching shell
# makes every call fail with an empty `opencode run exited 1`, which chia then reports
# as the far less obvious `opencode call failed (rc -1)`.  The key itself stays in a
# 600 file outside every repository.
[ -r "$CH/.secrets/openrouter.env" ] && { set -a; . "$CH/.secrets/openrouter.env"; set +a; }

# opencode caps one call's output at min(the model's output limit, this variable), and without it at
# 32000, reasoning included. adir sets it per call (adir.backends.skydiscover.set_opencode_env: a role's
# max_output_tokens, else 262144), and every call of the flow -- the search, the review node, the plain
# loop -- goes through that, so this value is only the fallback for an opencode run outside adir (and
# for a Ray worker that does not receive adir's per-call value). The eval run files set max_output_tokens
# to 393216 (the targets' render: deepseek-flash, reasoning high), and this fallback matches them
# (2026-09-25 audit: was 943718).
export OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX=393216

ulimit -n 65536 2>/dev/null || ulimit -n $(ulimit -Hn)

# ---- guard: refuse to run if the redirect did not take ---------------
case "$HOME" in
  /data2/*) ;;
  *) echo "chialu-env: HOME did not move to /data2 -- refusing" >&2 ;;
esac
