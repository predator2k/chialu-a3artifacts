#!/bin/sh
# ops/vmctl.sh — one reliable entry point for the chiALU GCP VM and the
# on-VM chia cluster. ADC-only auth (never reads private keys); all VM
# access goes through the SOCKS proxy in ~/.ssh/config (vmssh.sh, port 22).
#
#   ops/vmctl.sh status               instance + ssh + cluster + running loops
#   ops/vmctl.sh start                start the (stopped) instance, record IP
#   ops/vmctl.sh stop                 stop the instance (billing off)
#   ops/vmctl.sh provision            full recovery/first-time provisioning
#   ops/vmctl.sh ssh [cmd...]         shell / one-off command on the VM
#   ops/vmctl.sh up|deploy <inst.yaml> cluster.yaml from the instance (adir cluster), chia up
#   ops/vmctl.sh deploy               git pull on the VM + restart the cluster
#   ops/vmctl.sh up | down            start / stop the on-VM chia cluster
#   ops/vmctl.sh run <name> <cmd...>  launch a loop in tmux; log run/<name>.log
#   ops/vmctl.sh runs                 list runs + tail of each active log
#   ops/vmctl.sh kill [name]          stop one loop window, or all loops
#   ops/vmctl.sh fetch <run-id>       copy run/<run-id>/ from the VM to local
#   ops/vmctl.sh codex-image          build chialu-codex:latest on the VM (ops/CodexDockerfile)
#   ops/vmctl.sh codex-login          ChatGPT device-code login into ~/.codex on the VM (interactive)
#   ops/vmctl.sh codex-status         login state of ~/.codex on the VM
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(dirname "$HERE")
# machine-specific settings: ops/vm.env (see ops/vm.env.example); defaults below
[ -f "$HERE/vm.env" ] && . "$HERE/vm.env"
: "${GCP_PROJECT:=my-gcp-project}" "${GCP_ZONE:=us-central1-a}" "${VM_NAME:=chia-alu-vm}"
: "${VM_SSH_USER:=user}" "${VM_SSH_KEY:=$HOME/.ssh/id_rsa}" "${VM_SSH_PORT:=22}"
: "${VM_REPO_DIR:=~/chiALU}" "${VM_CONDA_SH:=~/miniconda3/etc/profile.d/conda.sh}" "${VM_CONDA_ENV:=chia_env}"
: "${GITHUB_REPO:=owner/chiALU}" "${GCLOUD:=gcloud}"
ACT="source $VM_CONDA_SH && conda activate $VM_CONDA_ENV"
API="https://compute.googleapis.com/compute/v1/projects/$GCP_PROJECT/zones/$GCP_ZONE/instances/$VM_NAME"

tok() { "$GCLOUD" auth application-default print-access-token; }
api() { # api <suffix> [POST]
  if [ "${2:-GET}" = "POST" ]; then
    curl -s -X POST -H "Authorization: Bearer $(tok)" \
      -H "Content-Type: application/json" -d '{}' "$API$1"
  else
    curl -s -H "Authorization: Bearer $(tok)" "$API$1"
  fi
}
vssh() { "$HERE/vmssh.sh" "$@"; }
# The chia cluster yaml is generated from an instance's cluster: section
# (adir cluster) into run/cluster.yaml on the VM.
cluster_yaml() {
  [ -n "$1" ] || { echo "usage: ops/vmctl.sh up|deploy <instance.yaml>" >&2; exit 2; }
  vssh "cd $VM_REPO_DIR && $ACT && mkdir -p run && adir cluster $1 --run-dir run >/dev/null && echo run/cluster.yaml"
}

wait_ssh() {
  n=0
  until vssh 'echo ssh-ok' 2>/dev/null | grep -q ssh-ok; do
    n=$((n+1)); [ "$n" -gt 40 ] && { echo "ssh never came up" >&2; return 1; }
    sleep 10
  done
  echo "ssh ok"
}
# the pattern text itself must not match this script's own remote argv,
# so the trailing character sits in a bracket class
LOOP_PAT='adir run'

case "${1:-status}" in
status)
  ST=$(api "" | python3 -c \
    "import json,sys;print(json.load(sys.stdin).get('status','ABSENT'))")
  echo "instance: $ST  (ip: $(cat "$HERE/vm_ip" 2>/dev/null || echo '?'))"
  [ "$ST" = "RUNNING" ] || exit 0
  vssh "echo 'ssh: ok'
    $ACT 2>/dev/null
    C=\$(ray status 2>/dev/null | grep -E 'eda|opencode_creds|codex_creds')
    if [ -n \"\$C\" ]; then echo \"\$C\" | sed 's/^ */cluster: /'; else echo 'cluster: down'; fi
    L=\$(pgrep -af 'adir run')
    if [ -n \"\$L\" ]; then echo \"\$L\" | sed 's/^/loop: /'; else echo 'loop: none running'; fi
    R=\$(ls -dt $VM_REPO_DIR/run/*/ 2>/dev/null | head -5)
    [ -n \"\$R\" ] && echo \"\$R\" | sed 's/^/run: /' || echo 'run: (none yet)'"
  ;;
ssh)
  shift; vssh "$@"
  ;;
deploy)
  vssh "cd $VM_REPO_DIR && git pull -q && git log --oneline -1"
  "$0" up "$2"
  ;;
up)
  # the previous bring-up log is removed first, so the wait below reads
  # only this bring-up's log (ray status would show the old cluster
  # until chia down takes it away)
  CY=$(cluster_yaml "$2"); [ -n "$CY" ] || exit 1
  vssh "cd $VM_REPO_DIR && mkdir -p run && rm -f run/chia_up.log
    tmux kill-session -t chialu 2>/dev/null
    tmux new-session -d -s chialu \"$ACT && cd $VM_REPO_DIR && export THIS_MACHINE=\\\$(hostname) && chia down --yes $CY >/dev/null 2>&1; chia up --yes $CY 2>&1 | tee run/chia_up.log; exec bash\"
    echo \"cluster starting from $CY in tmux session chialu (log: run/chia_up.log)\""
  n=0
  while :; do
    L=$(vssh "cat $VM_REPO_DIR/run/chia_up.log 2>/dev/null")
    echo "$L" | grep -q "Cluster 'chialu' up" && break
    echo "$L" | grep -qE 'ERROR|Traceback' && { echo "$L" | tail -15 >&2; echo "cluster bring-up failed (run/chia_up.log)" >&2; exit 1; }
    n=$((n+1)); [ "$n" -gt 90 ] && { echo "cluster never came up" >&2; exit 1; }
    sleep 10
  done
  vssh "$ACT && ray status 2>/dev/null | grep -E 'eda|opencode_creds|codex_creds'"
  echo "cluster up"
  ;;
down)
  vssh "$ACT
    cd $VM_REPO_DIR && export THIS_MACHINE=\$(hostname)
    [ -f run/cluster.yaml ] && chia down --yes run/cluster.yaml >/dev/null 2>&1
    tmux kill-session -t chialu 2>/dev/null; echo 'cluster down'"
  ;;
run)
  # ops/vmctl.sh run <name> <instance.yaml> [run.py args...]: the run lives in
  # run/<name>/ on the VM (every generated file lands there).
  shift; NAME=$1; INST=$2; shift 2; ARGS=$*
  vssh "cd $VM_REPO_DIR && mkdir -p run/$NAME
    tmux has-session -t runs 2>/dev/null || tmux new-session -d -s runs
    tmux new-window -t runs -n '$NAME' \
      \"$ACT && cd $VM_REPO_DIR/run/$NAME && export PYTHONUNBUFFERED=1 && adir run ../../$INST --run-dir . $ARGS 2>&1 | tee run.log; exec bash\"
    echo \"launched $NAME (tmux runs:$NAME, run/$NAME/run.log)\""
  ;;
runs)
  vssh "cd $VM_REPO_DIR
    for f in run/*/run.log; do [ -f \"\$f\" ] || continue
      echo \"== \$f\"; grep '^\\[flat\\]\\|^\\[hier\\]\\|^\\[run\\]\\|Traceback' \"\$f\" | tail -2 | cut -c1-160; done
    echo '== live'; for p in \$(pgrep -f 'adir run'); do echo \"\$p \$(readlink /proc/\$p/cwd)\"; done"
  ;;
kill)
  # kill <name>: the run whose cwd is run/<name>; no name: every loop
  if [ -n "${2:-}" ]; then
    vssh "tmux kill-window -t runs:$2 2>/dev/null
      for p in \$(pgrep -f 'adir run'); do
        [ \"\$(readlink /proc/\$p/cwd)\" = \"\$HOME/chiALU/run/$2\" ] && kill \$p && echo killed \$p; done; true"
  else
    vssh "pkill -f '$LOOP_PAT'; sleep 1; pgrep -af '$LOOP_PAT' || echo 'all loops dead'"
  fi
  ;;
fetch)
  # fetch <name>: copy run/<name>/ from the VM into the local repo
  RID=$2
  vssh "cd $VM_REPO_DIR && tar cz run/$RID" | (cd "$REPO" && tar xz)
  echo "fetched run/$RID"
  ;;
codex-image)
  # the codex worker image: the opencode image plus the Codex CLI, built
  # on the VM (cluster.yaml never pulls it); the image holds no credentials
  vssh "cd $VM_REPO_DIR && docker build -q -t chialu-codex:latest -f ops/CodexDockerfile ops && docker run --rm chialu-codex:latest codex --version"
  ;;
codex-login)
  # the ChatGPT login for the codex worker: device-code flow inside the
  # image (the VM has no browser), writing ~/.codex/auth.json on the VM,
  # which cluster.yaml mounts into the container; needs a terminal
  VMSSH_TTY=1 vssh "mkdir -p ~/.codex && chmod 700 ~/.codex
    docker run -it --rm -v \$HOME/.codex:/home/ray/.codex -e CODEX_HOME=/home/ray/.codex chialu-codex:latest codex login --device-auth"
  ;;
codex-status)
  vssh "if [ -f ~/.codex/auth.json ]; then docker run --rm -v \$HOME/.codex:/home/ray/.codex -e CODEX_HOME=/home/ray/.codex chialu-codex:latest codex login status; else echo 'codex: not logged in (no ~/.codex/auth.json on the VM)'; fi"
  ;;
*)
  echo "unknown command: $CMD" >&2; sed -n 2,20p "$0"; exit 2
  ;;
esac
