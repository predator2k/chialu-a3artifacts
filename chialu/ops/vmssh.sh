#!/bin/sh
# SSH to the cluster VM. Any proxy comes from ~/.ssh/config for the host;
# nothing here overrides it. User, key and port come from ops/vm.env. The VM's current IP lives in ops/vm_ip (updated
# by vm_recover.sh after each re-provision).
# Usage: ops/vmssh.sh [command...]     (VMSSH_TTY=1 allocates a terminal)
HERE=$(cd "$(dirname "$0")" && pwd)
[ -f "$HERE/vm.env" ] && . "$HERE/vm.env"
: "${VM_SSH_USER:=user}" "${VM_SSH_KEY:=$HOME/.ssh/id_rsa}" "${VM_SSH_PORT:=22}"
IP=$(cat "$HERE/vm_ip" 2>/dev/null)
[ -n "$IP" ] || { echo "ops/vm_ip missing (the VM's IP; see ops/vm.env.example)" >&2; exit 2; }
exec ssh ${VMSSH_TTY:+-t} -p "$VM_SSH_PORT" \
  -o ConnectTimeout=30 \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null \
  -o LogLevel=ERROR \
  -i "$VM_SSH_KEY" \
  "$VM_SSH_USER@$IP" "$@"
