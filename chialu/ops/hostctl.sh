#!/bin/sh
# The EDA host (a LAN machine reached by plain ssh; no VM, no container):
# both repositories are pushed to bare repositories there and checked out
# in HOST_REPO_DIR (ADIR as the submodule), the CHIA cluster of a run
# file is brought up with `chia up`, and a run is `adir run` in a tmux
# window. The host's conda env, the oss-cad-suite tools and the
# Claude CLI are put on PATH here; a token in ~/.claude_env on the host
# reaches the claude worker. Settings come from ops/vm.env (see
# ops/vm.env.example).
#   ops/hostctl.sh deploy                      push main of both repositories and check them out on the host
#   ops/hostctl.sh cluster-up <run.yaml>       `chia up` on the run file's cluster keys
#   ops/hostctl.sh cluster-down <run.yaml>     `chia down`
#   ops/hostctl.sh check <run.yaml>            `adir check` on the host
#   ops/hostctl.sh seeds <name> <run.yaml>     evaluate the seeds into run/<name>/ (tmux runs:<name>)
#   ops/hostctl.sh run <name> <run.yaml> [adir run args...]
#                                              start the search in run/<name>/ (tmux runs:<name>)
#   ops/hostctl.sh exec <name> <command...>    run any command of the repository in a tmux window (run/<name>/run.log)
#   ops/hostctl.sh runs                        every run's last log lines and the live adir processes
#   ops/hostctl.sh kill [<name>]               stop one run (or every run) and its EDA children
#   ops/hostctl.sh fetch <name>                copy run/<name>/ into the local repository
#   ops/hostctl.sh tools                       the tool versions the nodes see on the host
#   ops/hostctl.sh ssh [command...]            a shell (or one command) on the host
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(dirname "$HERE")
[ -f "$HERE/vm.env" ] && . "$HERE/vm.env"
: "${HOST_SSH:=host@<IP>}" "${HOST_IP:=${HOST_SSH#*@}}"
: "${HOST_REPO_DIR:=~/chiALU}" "${HOST_BARE_DIR:=~/chiALU.git}" "${HOST_ADIR_BARE_DIR:=~/adir.git}"
: "${HOST_CONDA_DIR:=\$HOME/miniconda3}" "${HOST_CONDA_ENV:=chia_env}"
: "${HOST_TOOLS:=\$HOME/.opencode/bin:\$HOME/tools/bin:\$HOME/tools/oss-cad-suite/bin:\$HOME/.local/bin}"
# the environment of every adir process on the host: the conda env's bin
# first on PATH (no `conda activate`: the shell tmux runs a window
# command in has no conda hook), the tools, the head address the run
# files name, the Vertex project for opencode's google-vertex provider
# (the host's application-default credentials), the token file when present
ACT="export PATH=$HOST_CONDA_DIR/envs/$HOST_CONDA_ENV/bin:$HOST_TOOLS:\$PATH THIS_MACHINE=$HOST_IP PYTHONUNBUFFERED=1 GOOGLE_VERTEX_LOCATION=global GOOGLE_VERTEX_PROJECT=\${GOOGLE_VERTEX_PROJECT:-\$(gcloud config get-value project 2>/dev/null)} && ulimit -n 65536 && { [ -f \$HOME/.claude_env ] && . \$HOME/.claude_env; true; }"
# the bracket keeps pgrep -f from matching the remote shell whose command line carries the pattern
LOOP_PAT='adir (run|seeds)'
hssh() { ssh -o ConnectTimeout=30 -o LogLevel=ERROR ${HSSH_TTY:+-t} "$HOST_SSH" "$@"; }
window() {
  # window <name> <command>: a tmux window in the session `runs` running the command in run/<name>/'s repository
  NAME=$1; shift
  hssh "cd $HOST_REPO_DIR && mkdir -p run/$NAME
    tmux has-session -t runs 2>/dev/null || tmux new-session -d -s runs
    tmux kill-window -t runs:$NAME 2>/dev/null
    tmux new-window -t runs -n '$NAME' \"$ACT && cd $HOST_REPO_DIR && $* 2>&1 | tee -a run/$NAME/run.log; exec bash\"
    echo \"launched $NAME (tmux runs:$NAME, run/$NAME/run.log)\""
}
CMD=${1:-}
case "$CMD" in
ssh)
  shift; HSSH_TTY=1 hssh "$@"
  ;;
deploy)
  cd "$REPO/third_party/adir" && git push -q "$HOST_SSH:${HOST_ADIR_BARE_DIR#\~/}" main
  cd "$REPO" && git push -q "$HOST_SSH:${HOST_BARE_DIR#\~/}" main
  hssh "$ACT && cd $HOST_REPO_DIR && git pull -q && git config submodule.third_party/adir.url \$HOME/${HOST_ADIR_BARE_DIR#\~/} && git -c protocol.file.allow=always submodule update --init -q && pip install -q -e third_party/adir > /dev/null && git log --oneline -1 && git -C third_party/adir log --oneline -1"
  ;;
cluster-up)
  hssh "$ACT && cd $HOST_REPO_DIR && chia up -y $2 2>&1 | tail -6"
  ;;
cluster-down)
  hssh "$ACT && cd $HOST_REPO_DIR && chia down -y $2 2>&1 | tail -3"
  ;;
check)
  hssh "$ACT && cd $HOST_REPO_DIR && adir check $2"
  ;;
seeds)
  window "$2" "adir seeds $3 --run-dir run/$2"
  ;;
run)
  NAME=$2; INST=$3; shift 3
  window "$NAME" "adir run $INST --run-dir run/$NAME $*"
  ;;
exec)
  NAME=$2; shift 2
  window "$NAME" "$*"
  ;;
runs)
  hssh "cd $HOST_REPO_DIR
    for f in run/*/run.log; do [ -f \"\$f\" ] || continue
      echo \"== \$f\"; grep -E '^\\[adir|Traceback|stopped_by|best_score' \"\$f\" | tail -2 | cut -c1-160; done
    echo '== live'; for p in \$(pgrep -f '$LOOP_PAT'); do echo \"\$p \$(tr '\\0' ' ' < /proc/\$p/cmdline | cut -c1-120)\"; done"
  ;;
kill)
  if [ -n "${2:-}" ]; then
    hssh "tmux kill-window -t runs:$2 2>/dev/null
      for p in \$(pgrep -f '$LOOP_PAT'); do
        tr '\\0' ' ' < /proc/\$p/cmdline | grep -q 'run/$2' && kill \$p && echo killed \$p; done; true"
  else
    hssh "pkill -f '$LOOP_PAT'; sleep 1; pgrep -af '$LOOP_PAT' || echo 'all runs dead'"
  fi
  hssh "sleep 2; pkill -x yosys-abc; pkill -f 'recipe[.]ys'; pkill -f 'synth[.]ys'; pkill -f 'vv[p] '; pkill -f 'sv2[v] '; echo 'eda children stopped'"
  ;;
fetch)
  RID=$2
  hssh "cd $HOST_REPO_DIR && tar cz run/$RID" | (cd "$REPO" && tar xz)
  echo "fetched run/$RID"
  ;;
tools)
  hssh "$ACT; for t in verilator yosys yosys-abc claude python adir chia; do printf '%-10s %s\n' \$t \"\$(command -v \$t)\"; done
    verilator --version; yosys -V; claude --version; python --version"
  ;;
*)
  echo "unknown command: $CMD" >&2; sed -n 2,22p "$0"; exit 2
  ;;
esac
