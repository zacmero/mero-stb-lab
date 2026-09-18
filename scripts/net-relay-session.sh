#!/usr/bin/env bash
set -euo pipefail

cat >&2 <<'EOF'
RETIRED FOR SAFETY: legacy net-relay-session.sh

This script used a hard-coded STB IP without first proving that the current host
at that address still had the Sagemcom MAC. DHCP reuse could therefore target an
unrelated LAN client.

For passive/relay observation use:

  ./scripts/net-path-003.sh

NET-PATH-003 verifies the live IP->MAC binding before any mutation and requires
an interactive human start. For HTTP/HTTPS interception use the hardened:

  ./scripts/run_net_config_005.sh 180

The original implementation remains available in Git history.
EOF
exit 2
