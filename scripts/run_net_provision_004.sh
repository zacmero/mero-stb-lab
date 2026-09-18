#!/usr/bin/env bash
set -euo pipefail

cat >&2 <<'EOF'
RETIRED FOR SAFETY: NET-PROVISION-004 multi-IP runner

This historical runner targeted several guessed/stale DHCP addresses and is not
safe to execute on the production LAN. The 2026-09-18 incident demonstrated why
multi-IP ARP targeting is unacceptable.

Use the hardened exact-target runner instead:

  ./scripts/run_net_config_005.sh 180

That command performs a read-only preflight by default. Only after verifying the
single resolved STB identity should a live run be explicitly armed:

  sudo env ALLOW_ARP_MITM=YES ./scripts/run_net_config_005.sh 180

The original implementation remains available in Git history for archaeology.
EOF
exit 2
