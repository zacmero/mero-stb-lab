#!/usr/bin/env bash
set -Eeuo pipefail

IFACE="${IFACE:-enp6s0}"
CONTROL_IFACE="${CONTROL_IFACE:-wlp4s0}"
RECEIVER_MAC="${RECEIVER_MAC:-68:15:90:6b:81:96}"
LAB_ADDR="10.74.0.1"
RECEIVER_ADDR="10.74.0.10"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RUN_USER="${SUDO_USER:-${USER}}"
RUN_HOME="$(getent passwd "$RUN_USER" | cut -d: -f6)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${RUN_DIR:-${RUN_HOME}/mero-stb-isolated/captures/${STAMP}}"
PID_HTTP=""
PID_DNSMASQ=""
PID_TCPDUMP=""
OLD_FORWARD=""
OLD_MANAGED=""

die() { echo "ERROR: $*" >&2; exit 1; }

cleanup() {
  trap - EXIT INT TERM HUP
  echo "Cleaning isolated receiver lab..."
  for pid in "$PID_HTTP" "$PID_DNSMASQ" "$PID_TCPDUMP"; do
    [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
  ip address del 186.215.183.217/32 dev "$IFACE" 2>/dev/null || true
  ip address del 191.32.31.251/32 dev "$IFACE" 2>/dev/null || true
  ip address del 213.140.61.225/32 dev "$IFACE" 2>/dev/null || true
  ip address del "${LAB_ADDR}/24" dev "$IFACE" 2>/dev/null || true
  [[ -n "$OLD_FORWARD" ]] && sysctl -q -w "net.ipv4.ip_forward=${OLD_FORWARD}" || true
  if [[ "$OLD_MANAGED" == "yes" ]]; then
    nmcli device set "$IFACE" managed yes >/dev/null 2>&1 || true
  fi
  echo "Cleanup complete. Wi-Fi was not modified. Artifacts: ${RUN_DIR}"
}
trap cleanup EXIT INT TERM HUP

[[ "$EUID" -eq 0 ]] || die "run with sudo"
[[ -d "/sys/class/net/${IFACE}" ]] || die "missing interface ${IFACE}"
[[ -d "/sys/class/net/${CONTROL_IFACE}" ]] || die "missing control interface ${CONTROL_IFACE}"
ip route show default | grep -q "dev ${CONTROL_IFACE}" || die "control default route is not ${CONTROL_IFACE}"
! ip route show default | grep -q "dev ${IFACE}" || die "refusing to modify a default-route interface"
ping -I "$CONTROL_IFACE" -c 2 -W 2 192.168.1.1 >/dev/null || die "Wi-Fi gateway preflight failed"

install -d -m 0750 -o "$RUN_USER" -g "$RUN_USER" "$RUN_DIR"
for file in http.jsonl http.stdout dnsmasq.log dnsmasq.stdout tcpdump.stdout; do
  install -m 0640 -o "$RUN_USER" -g "$RUN_USER" /dev/null "$RUN_DIR/$file"
done

OLD_FORWARD="$(sysctl -n net.ipv4.ip_forward)"
OLD_MANAGED="$(nmcli -g GENERAL.MANAGED device show "$IFACE" 2>/dev/null | tr '[:upper:]' '[:lower:]' || true)"
nmcli device set "$IFACE" managed no >/dev/null
ip link set "$IFACE" up
ip address add "${LAB_ADDR}/24" dev "$IFACE"
ip address add 191.32.31.251/32 dev "$IFACE"
ip address add 186.215.183.217/32 dev "$IFACE"
ip address add 213.140.61.225/32 dev "$IFACE"
sysctl -q -w net.ipv4.ip_forward=0

cat >"$RUN_DIR/dnsmasq.conf" <<EOF
interface=${IFACE}
bind-interfaces
port=53
no-resolv
no-hosts
log-dhcp
log-queries
log-facility=${RUN_DIR}/dnsmasq.log
dhcp-authoritative
dhcp-range=${RECEIVER_ADDR},${RECEIVER_ADDR},255.255.255.0,12h
dhcp-host=${RECEIVER_MAC},${RECEIVER_ADDR},12h
dhcp-option=3,${LAB_ADDR}
dhcp-option=6,${LAB_ADDR}
address=/#/${LAB_ADDR}
EOF
chown "$RUN_USER:$RUN_USER" "$RUN_DIR/dnsmasq.conf"
chmod 0640 "$RUN_DIR/dnsmasq.conf"

dnsmasq --keep-in-foreground --conf-file="$RUN_DIR/dnsmasq.conf" \
  >>"$RUN_DIR/dnsmasq.stdout" 2>&1 &
PID_DNSMASQ=$!
python3 "$SCRIPT_DIR/isolated_http_logger.py" --interface "$IFACE" --log "$RUN_DIR/http.jsonl" \
  >>"$RUN_DIR/http.stdout" 2>&1 &
PID_HTTP=$!
tcpdump -i "$IFACE" -U -s 0 -w "$RUN_DIR/receiver.pcap" \
  "ether host ${RECEIVER_MAC} or ether broadcast or ether multicast" \
  >>"$RUN_DIR/tcpdump.stdout" 2>&1 &
PID_TCPDUMP=$!
sleep 2
kill -0 "$PID_DNSMASQ" "$PID_HTTP" "$PID_TCPDUMP" || die "a lab service failed to start"
ip route show default | grep -q "dev ${CONTROL_IFACE}" || die "control route changed"
ping -I "$CONTROL_IFACE" -c 2 -W 2 192.168.1.1 >/dev/null || die "Wi-Fi health check failed"

cat <<EOF
READY: isolated receiver lab
  Control:  ${CONTROL_IFACE} (unchanged)
  Receiver: ${IFACE} -> ${RECEIVER_ADDR}
  Forwarding: disabled
  Artifacts: ${RUN_DIR}

Connect the receiver Ethernet cable directly to ${IFACE}, then cold boot it.
Press Ctrl-C only after capture is complete.
EOF

while :; do
  sleep 2
  kill -0 "$PID_DNSMASQ" "$PID_HTTP" "$PID_TCPDUMP" || die "a lab service exited"
done
