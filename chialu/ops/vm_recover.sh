#!/bin/zsh
# One-command recovery after spot preemption or first-time provisioning.
# Laptop-side: provisions the VM via chia (its head stage fails on this
# machine and that is fine — the VM setup completes first), records the
# new IP, refreshes the read-only deploy key, clones the repo, and brings
# up the on-VM single-machine cluster inside tmux.
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
cd "$REPO"

# 0. If a stopped instance survives (STOP termination policy), restart it.
TOKEN=$($GCLOUD auth application-default print-access-token)
STATUS=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://compute.googleapis.com/compute/v1/projects/$GCP_PROJECT/zones/$GCP_ZONE/instances/$VM_NAME" \
  | python3 -c "import json,sys;print(json.load(sys.stdin).get('status',''))")
if [ "$STATUS" = "TERMINATED" ]; then
  echo "restarting stopped instance..."
  curl -s -X POST -H "Authorization: Bearer $TOKEN" -d '{}' \
    -H "Content-Type: application/json" \
    "https://compute.googleapis.com/compute/v1/projects/$GCP_PROJECT/zones/$GCP_ZONE/instances/$VM_NAME/start" >/dev/null
elif [ -z "$STATUS" ]; then
  echo "no instance: provisioning via chia (head-stage failure expected)..."
  echo "(the laptop-head cluster is gone; the VM runs its own cluster from run/cluster.yaml)"
fi

# 1. Record the current external IP.
TOKEN=$($GCLOUD auth application-default print-access-token)
IP=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://compute.googleapis.com/compute/v1/projects/$GCP_PROJECT/zones/$GCP_ZONE/instances/$VM_NAME" \
  | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['networkInterfaces'][0]['accessConfigs'][0]['natIP'])")
echo "$IP" > "$HERE/vm_ip"
echo "VM IP: $IP"

# 2. Wait for proxied sshd:443.
n=0
until ops/vmssh.sh 'echo ssh-ok' 2>/dev/null | grep -q ssh-ok; do
  n=$((n+1)); [ $n -gt 40 ] && { echo "ssh never came up"; exit 1; }
  sleep 10
done

# 3. On-VM bootstrap (idempotent).
ops/vmssh.sh 'command -v tmux >/dev/null || sudo apt-get install -y -qq tmux >/dev/null 2>&1
test -f ~/.ssh/id_ed25519 || ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519 -q
grep -qf ~/.ssh/id_ed25519.pub ~/.ssh/authorized_keys 2>/dev/null || cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/id_ed25519.pub' > /tmp/vm_deploy_key.pub

# 4. Refresh the deploy key (read-only) if this key is not registered yet.
KEY=$(cut -d" " -f2 /tmp/vm_deploy_key.pub)
if ! gh repo deploy-key list -R $GITHUB_REPO | grep -q "$KEY"; then
  gh repo deploy-key list -R $GITHUB_REPO \
    | awk '$2=="chia-safealu-vm" {print $1}' \
    | xargs -I{} gh repo deploy-key delete -R $GITHUB_REPO {} --yes 2>/dev/null || true
  gh repo deploy-key add /tmp/vm_deploy_key.pub -R $GITHUB_REPO --title $VM_NAME
fi

# 5. Clone/update the repo, regenerate artifacts, start the on-VM cluster.
ops/vmssh.sh 'set -e
test -d $VM_REPO_DIR || GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=accept-new" git clone -q git@github.com:$GITHUB_REPO.git $VM_REPO_DIR
cd $VM_REPO_DIR && git pull -q
mkdir -p run
tmux kill-session -t chialu 2>/dev/null || true
tmux new-session -d -s chialu "$ACT && cd $VM_REPO_DIR && export THIS_MACHINE=\$(hostname) && adir cluster chialu/targets/instances/cmp_alu16_hier.yaml --run-dir run && chia up --yes run/cluster.yaml 2>&1 | tee run/chia_up.log; exec bash"
echo "on-VM cluster starting in tmux"'
echo "recovery done: $IP"
