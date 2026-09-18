#!/usr/bin/env bash
set -Eeuo pipefail

# NET-PATH-003: bounded observation of Zac's own Sagemcom DSI74 V2.
# PC and receiver stay on the same home router.
# Only the verified receiver is redirected/captured. No DNS spoofing, proxying,
# payload modification, firmware serving, unrelated scanning, or receiver writes.

TARGET_IP="${TARGET_IP:-192.168.1.134}"
TARGET_MAC="${TARGET_MAC:-68:15:90:6b:81:96}"
EXPECTED_GATEWAY="${EXPECTED_GATEWAY:-192.168.1.1}"
DURATION="${DURATION:-300}"

die() { echo "ERROR: $*" >&2; exit 1; }

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "$REPO_ROOT" ]] || die "run this inside the mero-stb-lab checkout"
cd "$REPO_ROOT"

for cmd in ip awk tr date sudo tcpdump bettercap sysctl sha256sum ping iptables; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "Missing required command: $cmd" >&2
    [[ "$cmd" == "bettercap" ]] && echo "Arch: sudo pacman -S bettercap" >&2
    [[ "$cmd" == "tcpdump" ]] && echo "Arch: sudo pacman -S tcpdump" >&2
    [[ "$cmd" == "iptables" ]] && echo "Arch: sudo pacman -S iptables-nft" >&2
    exit 1
  }
done

[[ "$DURATION" =~ ^[0-9]+$ ]] || die "DURATION must be an integer"
(( DURATION >= 30 && DURATION <= 900 )) || die "DURATION must be 30..900 seconds"

TARGET_MAC="$(tr '[:upper:]' '[:lower:]' <<<"$TARGET_MAC")"
ROUTE="$(ip -4 route get "$TARGET_IP" 2>/dev/null | head -n1)"
IFACE="$(awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}' <<<"$ROUTE")"
LOCAL_IP="$(awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}' <<<"$ROUTE")"
[[ -n "$IFACE" && -n "$LOCAL_IP" ]] || die "could not resolve route to receiver"

GATEWAY="$(ip -4 route show default dev "$IFACE" | awk '/default/ {print $3; exit}')"
[[ -n "$GATEWAY" ]] || die "could not determine gateway"
[[ "$GATEWAY" == "$EXPECTED_GATEWAY" ]] || die "gateway changed: expected $EXPECTED_GATEWAY, found $GATEWAY"

ping -c1 -W1 "$TARGET_IP" >/dev/null 2>&1 || true
ping -c1 -W1 "$GATEWAY" >/dev/null 2>&1 || true
sleep 1

SEEN_MAC="$(ip neigh show "$TARGET_IP" dev "$IFACE" | awk '/lladdr/ {print tolower($5); exit}')"
[[ -n "$SEEN_MAC" ]] || die "receiver MAC missing; power the Sagemcom on first"
[[ "$SEEN_MAC" == "$TARGET_MAC" ]] || die "$TARGET_IP belongs to $SEEN_MAC, not $TARGET_MAC"

GATEWAY_MAC="$(ip neigh show "$GATEWAY" dev "$IFACE" | awk '/lladdr/ {print tolower($5); exit}')"
[[ -n "$GATEWAY_MAC" ]] || die "could not resolve gateway MAC"
HOST_MAC="$(tr '[:upper:]' '[:lower:]' <"/sys/class/net/$IFACE/address")"

STAMP="$(date +%Y%m%d-%H%M%S)"
LOCAL_DIR="$REPO_ROOT/.local/net-path-003/$STAMP"
REPORT="$REPO_ROOT/docs/experiments/net-path-003-$STAMP.txt"
PCAP="$LOCAL_DIR/capture.pcap"
BC_LOG="$LOCAL_DIR/bettercap.log"
TCPDUMP_LOG="$LOCAL_DIR/tcpdump.log"
mkdir -p "$LOCAL_DIR" "$(dirname "$REPORT")"

ORIG_FORWARD="$(sysctl -n net.ipv4.ip_forward)"
ORIG_REDIRECT_ALL="$(sysctl -n net.ipv4.conf.all.send_redirects)"
ORIG_REDIRECT_IF="$(sysctl -n "net.ipv4.conf.${IFACE}.send_redirects")"

BC_PID=""
TCPDUMP_PID=""
FW_ADDED=0
CLEANED=0

cleanup() {
  local rc=$?
  (( CLEANED == 0 )) || return "$rc"
  CLEANED=1
  set +e

  if [[ -n "$BC_PID" ]] && kill -0 "$BC_PID" 2>/dev/null; then
    kill -INT "$BC_PID" 2>/dev/null
    sleep 2
    kill -TERM "$BC_PID" 2>/dev/null || true
    wait "$BC_PID" 2>/dev/null || true
  fi

  if [[ -n "$TCPDUMP_PID" ]] && kill -0 "$TCPDUMP_PID" 2>/dev/null; then
    kill -INT "$TCPDUMP_PID" 2>/dev/null
    wait "$TCPDUMP_PID" 2>/dev/null || true
  fi

  if (( FW_ADDED == 1 )); then
    sudo iptables -w -D FORWARD -i "$IFACE" -o "$IFACE" -s "$TARGET_IP" -j ACCEPT 2>/dev/null || true
    sudo iptables -w -D FORWARD -i "$IFACE" -o "$IFACE" -d "$TARGET_IP" -j ACCEPT 2>/dev/null || true
  fi

  sudo sysctl -q -w "net.ipv4.conf.${IFACE}.send_redirects=$ORIG_REDIRECT_IF" >/dev/null 2>&1 || true
  sudo sysctl -q -w "net.ipv4.conf.all.send_redirects=$ORIG_REDIRECT_ALL" >/dev/null 2>&1 || true
  sudo sysctl -q -w "net.ipv4.ip_forward=$ORIG_FORWARD" >/dev/null 2>&1 || true
  echo
  echo "Cleanup complete."
  return "$rc"
}
trap cleanup EXIT INT TERM HUP

cat <<EOF
NET-PATH-003
  interface: $IFACE
  PC:        $LOCAL_IP ($HOST_MAC)
  receiver:  $TARGET_IP ($TARGET_MAC)
  gateway:   $GATEWAY ($GATEWAY_MAC)
  duration:  ${DURATION}s
  raw:       $PCAP  [git ignored]
  report:    $REPORT
EOF
echo
read -r -p "Press Enter to start; Ctrl-C aborts safely. " _

sudo -v
sudo sysctl -q -w net.ipv4.ip_forward=1 >/dev/null
sudo sysctl -q -w net.ipv4.conf.all.send_redirects=0 >/dev/null
sudo sysctl -q -w "net.ipv4.conf.${IFACE}.send_redirects=0" >/dev/null

# Exact temporary receiver-only forwarding allowances. Existing firewall rules are preserved.
sudo iptables -w -I FORWARD 1 -i "$IFACE" -o "$IFACE" -s "$TARGET_IP" -j ACCEPT
sudo iptables -w -I FORWARD 1 -i "$IFACE" -o "$IFACE" -d "$TARGET_IP" -j ACCEPT
FW_ADDED=1

sudo tcpdump -U -s0 -i "$IFACE" -w "$PCAP" \
  "host $TARGET_IP or ether host $TARGET_MAC" >"$TCPDUMP_LOG" 2>&1 &
TCPDUMP_PID=$!
sleep 1
kill -0 "$TCPDUMP_PID" 2>/dev/null || die "tcpdump failed; see $TCPDUMP_LOG"

# Bettercap defaults arp.spoof.spoofed to the gateway; gateway is explicitly overridden here.
BC_EVAL="set arp.spoof.targets $TARGET_IP; set arp.spoof.fullduplex true; set arp.spoof.internal false; set arp.spoof.forwarding true; set arp.spoof.skip_restore false; arp.spoof on"
sudo bettercap -iface "$IFACE" -gateway-override "$GATEWAY" \
  -env-file "" -no-history -no-colors -eval "$BC_EVAL" >"$BC_LOG" 2>&1 &
BC_PID=$!
sleep 3
kill -0 "$BC_PID" 2>/dev/null || die "bettercap exited early; see $BC_LOG"

echo
echo "CAPTURE ACTIVE."
echo "Run the receiver's normal NETWORK-CONNECTION diagnostic on the TV now."
echo "Do not choose firmware update or factory reset."
echo

for ((remaining=DURATION; remaining>0; remaining-=10)); do
  printf '\rRemaining: %3ds ' "$remaining"
  sleep $(( remaining < 10 ? remaining : 10 ))
done
printf '\rRemaining:   0s\n'

# Stop Bettercap first so it can restore ARP while forwarding still works.
kill -INT "$BC_PID" 2>/dev/null || true
sleep 2
kill -TERM "$BC_PID" 2>/dev/null || true
wait "$BC_PID" 2>/dev/null || true
BC_PID=""

kill -INT "$TCPDUMP_PID" 2>/dev/null || true
wait "$TCPDUMP_PID" 2>/dev/null || true
TCPDUMP_PID=""

PCAP_SHA="$(sudo sha256sum "$PCAP" | awk '{print $1}')"
PACKETS="$(sudo tcpdump -nn -r "$PCAP" 2>/dev/null | wc -l | tr -d ' ')"
OUT_RELAY="$(sudo tcpdump -enn -r "$PCAP" "ether src $TARGET_MAC and ether dst $HOST_MAC and not arp" 2>/dev/null | wc -l | tr -d ' ')"
BACK_RELAY="$(sudo tcpdump -enn -r "$PCAP" "ether src $HOST_MAC and ether dst $TARGET_MAC and not arp" 2>/dev/null | wc -l | tr -d ' ')"

RELAY_STATUS="not demonstrated"
if (( OUT_RELAY > 0 && BACK_RELAY > 0 )); then
  RELAY_STATUS="bidirectional relay observed"
elif (( OUT_RELAY > 0 || BACK_RELAY > 0 )); then
  RELAY_STATUS="one-way relay evidence only"
fi

{
  echo "NET-PATH-003 targeted receiver observation"
  echo "generated: $(date --iso-8601=seconds)"
  echo
  echo "interface: $IFACE"
  echo "pc: $LOCAL_IP / $HOST_MAC"
  echo "receiver: $TARGET_IP / $TARGET_MAC"
  echo "gateway: $GATEWAY / $GATEWAY_MAC"
  echo "duration: ${DURATION}s"
  echo "packets: $PACKETS"
  echo "pcap-sha256: $PCAP_SHA"
  echo "relay-out receiver->pc non-ARP frames: $OUT_RELAY"
  echo "relay-back pc->receiver non-ARP frames: $BACK_RELAY"
  echo "relay-status: $RELAY_STATUS"
  echo
  echo "=== DNS ==="
  sudo tcpdump -nn -vv -r "$PCAP" 'udp port 53 or tcp port 53' 2>/dev/null | head -n 200 || true
  echo
  echo "=== HTTP/80 packet headers ==="
  sudo tcpdump -nn -r "$PCAP" 'tcp port 80' 2>/dev/null | head -n 200 || true
  echo
  echo "=== TLS/443 packet headers ==="
  sudo tcpdump -nn -r "$PCAP" 'tcp port 443' 2>/dev/null | head -n 200 || true
  echo
  echo "=== FIRST 500 RECEIVER PACKET HEADERS ==="
  sudo tcpdump -enn -tttt -r "$PCAP" 2>/dev/null | head -n 500 || true
} >"$REPORT"

echo
echo "DONE: $RELAY_STATUS"
echo "Review and then push this report:"
echo "  $REPORT"
echo
echo "Commands:"
echo "  git add \"$REPORT\""
echo "  git commit -m 'docs(experiments): record NET-PATH-003 capture'"
echo "  git push"
echo
echo "Raw PCAP/logs remain private under:"
echo "  $LOCAL_DIR"
