#!/usr/bin/env bash
set -Eeuo pipefail

# HTTP-ENDPOINT-004
# Active, bounded observation of Zac's own Sagemcom DSI74 V2.
# Reuses the verified same-LAN Bettercap relay from NET-PATH-003, but redirects
# ONLY this receiver's connections to known legacy HTTP/TLS endpoints into
# local logging sockets. No firmware is served.
#
# HTTP receives 404. TLS records the first client flight/SNI if present, then
# closes. Raw PCAP/logs stay under .local/; a concise report goes to docs/.

TARGET_IP="${TARGET_IP:-192.168.1.137}"
TARGET_MAC="${TARGET_MAC:-68:15:90:6b:81:96}"
EXPECTED_GATEWAY="${EXPECTED_GATEWAY:-192.168.1.1}"
DURATION="${DURATION:-300}"
HTTP_PORT="${HTTP_PORT:-18080}"
TLS_PORT="${TLS_PORT:-18443}"

ENDPOINTS=("186.215.183.217" "191.32.31.251" "213.140.61.225")

die() { echo "ERROR: $*" >&2; exit 1; }
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "$REPO_ROOT" ]] || die "run this inside the mero-stb-lab checkout"
cd "$REPO_ROOT"

for cmd in ip awk tr date sudo tcpdump bettercap sysctl sha256sum ping iptables python3; do
  command -v "$cmd" >/dev/null 2>&1 || die "missing required command: $cmd"
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
LOCAL_DIR="$REPO_ROOT/.local/http-endpoint-004/$STAMP"
REPORT="$REPO_ROOT/docs/experiments/http-endpoint-004-$STAMP.md"
PCAP="$LOCAL_DIR/capture.pcap"
BC_LOG="$LOCAL_DIR/bettercap.log"
TCPDUMP_LOG="$LOCAL_DIR/tcpdump.log"
APP_LOG="$LOCAL_DIR/endpoint.log"
LISTENER="$LOCAL_DIR/listener.py"
mkdir -p "$LOCAL_DIR" "$(dirname "$REPORT")"

cat >"$LISTENER" <<'PY'
#!/usr/bin/env python3
import datetime as dt, socket, struct, sys, threading
http_port, tls_port, log_path = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
lock = threading.Lock()
SAFE_HEADERS = {"host","user-agent","content-type","content-length","accept","connection","cache-control","pragma"}

def log(msg):
    line = f"{dt.datetime.now().astimezone().isoformat()} {msg}\n"
    with lock:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line); f.flush()
    print(line, end="", flush=True)

def parse_sni(data):
    try:
        if len(data) < 5 or data[0] != 0x16: return None
        rec_len = struct.unpack("!H", data[3:5])[0]
        body = data[5:5+rec_len]
        if len(body) < 42 or body[0] != 0x01: return None
        p = 4 + 2 + 32
        sess_len = body[p]; p += 1 + sess_len
        cs_len = struct.unpack("!H", body[p:p+2])[0]; p += 2 + cs_len
        comp_len = body[p]; p += 1 + comp_len
        ext_total = struct.unpack("!H", body[p:p+2])[0]; p += 2
        end = min(len(body), p + ext_total)
        while p + 4 <= end:
            etype, elen = struct.unpack("!HH", body[p:p+4]); p += 4
            ext = body[p:p+elen]; p += elen
            if etype == 0 and len(ext) >= 5:
                q = 2
                while q + 3 <= len(ext):
                    ntype = ext[q]
                    nlen = struct.unpack("!H", ext[q+1:q+3])[0]
                    q += 3
                    name = ext[q:q+nlen]; q += nlen
                    if ntype == 0: return name.decode("ascii", "replace")
    except Exception:
        return None
    return None

def recv_headers(conn, limit=65536):
    data = b""; conn.settimeout(4)
    while b"\r\n\r\n" not in data and len(data) < limit:
        chunk = conn.recv(min(4096, limit-len(data)))
        if not chunk: break
        data += chunk
    return data

def handle_http(conn, addr):
    with conn:
        try:
            raw = recv_headers(conn)
            head = raw.split(b"\r\n\r\n", 1)[0]
            lines = head.decode("iso-8859-1", "replace").split("\r\n")
            request = lines[0] if lines else "<empty>"
            selected = []
            for line in lines[1:]:
                if ":" not in line: continue
                k, v = line.split(":", 1)
                if k.strip().lower() in SAFE_HEADERS:
                    selected.append(f"{k.strip()}: {v.strip()}")
            log(f"[HTTP] peer={addr[0]}:{addr[1]} request={request!r} headers={selected!r}")
            body = b"MERO-STB observation endpoint: no firmware served\n"
            conn.sendall(b"HTTP/1.1 404 Not Found\r\nConnection: close\r\nCache-Control: no-store\r\nContent-Type: text/plain\r\n" + f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
        except Exception as e:
            log(f"[HTTP-ERROR] peer={addr!r} error={e!r}")

def handle_tls(conn, addr):
    with conn:
        try:
            conn.settimeout(4); data = conn.recv(8192)
            sni = parse_sni(data)
            log(f"[TLS] peer={addr[0]}:{addr[1]} bytes={len(data)} sni={sni!r} prefix_hex={data[:48].hex()}")
        except Exception as e:
            log(f"[TLS-ERROR] peer={addr!r} error={e!r}")

def serve(port, handler, label):
    s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", port)); s.listen(16); log(f"[LISTEN] {label} 0.0.0.0:{port}")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handler, args=(conn, addr), daemon=True).start()

threading.Thread(target=serve, args=(http_port, handle_http, "HTTP"), daemon=True).start()
serve(tls_port, handle_tls, "TLS")
PY

ORIG_FORWARD="$(sysctl -n net.ipv4.ip_forward)"
ORIG_REDIRECT_ALL="$(sysctl -n net.ipv4.conf.all.send_redirects)"
ORIG_REDIRECT_IF="$(sysctl -n "net.ipv4.conf.${IFACE}.send_redirects")"
BC_PID=""; TCPDUMP_PID=""; LISTENER_PID=""; CLEANED=0
FW_RULES=(); NAT_RULES=()

cleanup() {
  local rc=$?
  (( CLEANED == 0 )) || return "$rc"
  CLEANED=1; set +e
  if [[ -n "$BC_PID" ]] && kill -0 "$BC_PID" 2>/dev/null; then kill -INT "$BC_PID"; sleep 2; kill -TERM "$BC_PID" 2>/dev/null || true; wait "$BC_PID" 2>/dev/null || true; fi
  if [[ -n "$TCPDUMP_PID" ]] && kill -0 "$TCPDUMP_PID" 2>/dev/null; then kill -INT "$TCPDUMP_PID"; wait "$TCPDUMP_PID" 2>/dev/null || true; fi
  if [[ -n "$LISTENER_PID" ]] && kill -0 "$LISTENER_PID" 2>/dev/null; then kill -TERM "$LISTENER_PID" 2>/dev/null || true; wait "$LISTENER_PID" 2>/dev/null || true; fi
  for rule in "${NAT_RULES[@]}"; do eval "sudo iptables -w -t nat -D $rule" 2>/dev/null || true; done
  for rule in "${FW_RULES[@]}"; do eval "sudo iptables -w -D $rule" 2>/dev/null || true; done
  sudo sysctl -q -w "net.ipv4.conf.${IFACE}.send_redirects=$ORIG_REDIRECT_IF" >/dev/null 2>&1 || true
  sudo sysctl -q -w "net.ipv4.conf.all.send_redirects=$ORIG_REDIRECT_ALL" >/dev/null 2>&1 || true
  sudo sysctl -q -w "net.ipv4.ip_forward=$ORIG_FORWARD" >/dev/null 2>&1 || true
  echo; echo "Cleanup complete."; return "$rc"
}
trap cleanup EXIT INT TERM HUP

echo "HTTP-ENDPOINT-004"
echo "PC: $LOCAL_IP  receiver: $TARGET_IP ($TARGET_MAC)  gateway: $GATEWAY"
echo "Redirecting only receiver traffic to known endpoints: ${ENDPOINTS[*]}"
echo "HTTP -> $LOCAL_IP:$HTTP_PORT (404 only); TLS -> $LOCAL_IP:$TLS_PORT (ClientHello only)"
echo "Raw logs: $LOCAL_DIR"
read -r -p "Press Enter to start; Ctrl-C aborts and restores state. " _

sudo -v
sudo sysctl -q -w net.ipv4.ip_forward=1 >/dev/null
sudo sysctl -q -w net.ipv4.conf.all.send_redirects=0 >/dev/null
sudo sysctl -q -w "net.ipv4.conf.${IFACE}.send_redirects=0" >/dev/null

FW_RULES+=("FORWARD -i $IFACE -o $IFACE -s $TARGET_IP -j ACCEPT" "FORWARD -i $IFACE -o $IFACE -d $TARGET_IP -j ACCEPT" "INPUT -i $IFACE -s $TARGET_IP -p tcp --dport $HTTP_PORT -j ACCEPT" "INPUT -i $IFACE -s $TARGET_IP -p tcp --dport $TLS_PORT -j ACCEPT")
for rule in "${FW_RULES[@]}"; do eval "sudo iptables -w -I $rule"; done

for endpoint in "${ENDPOINTS[@]}"; do
  http_rule="PREROUTING -i $IFACE -s $TARGET_IP -d $endpoint -p tcp --dport 80 -j DNAT --to-destination $LOCAL_IP:$HTTP_PORT"
  tls_rule="PREROUTING -i $IFACE -s $TARGET_IP -d $endpoint -p tcp --dport 443 -j DNAT --to-destination $LOCAL_IP:$TLS_PORT"
  NAT_RULES+=("$http_rule" "$tls_rule")
  eval "sudo iptables -w -t nat -I $http_rule"
  eval "sudo iptables -w -t nat -I $tls_rule"
done

python3 "$LISTENER" "$HTTP_PORT" "$TLS_PORT" "$APP_LOG" &
LISTENER_PID=$!; sleep 1; kill -0 "$LISTENER_PID" 2>/dev/null || die "local endpoint listener failed"

sudo tcpdump -U -s0 -i "$IFACE" -w "$PCAP" "host $TARGET_IP or ether host $TARGET_MAC" >"$TCPDUMP_LOG" 2>&1 &
TCPDUMP_PID=$!; sleep 1; kill -0 "$TCPDUMP_PID" 2>/dev/null || die "tcpdump failed; see $TCPDUMP_LOG"

BC_EVAL="set arp.spoof.targets $TARGET_IP; set arp.spoof.fullduplex true; set arp.spoof.internal false; set arp.spoof.forwarding true; set arp.spoof.skip_restore false; arp.spoof on"
sudo bettercap -iface "$IFACE" -gateway-override "$GATEWAY" -silent -eval "$BC_EVAL" >"$BC_LOG" 2>&1 &
BC_PID=$!; sleep 3; kill -0 "$BC_PID" 2>/dev/null || die "bettercap exited early; see $BC_LOG"

echo "ACTIVE. Run the receiver's NETWORK CONNECTION diagnostic on the TV now."
for ((remaining=DURATION; remaining>0; remaining-=10)); do printf '\rRemaining: %3ds ' "$remaining"; sleep $(( remaining < 10 ? remaining : 10 )); done
printf '\rRemaining:   0s\n'

kill -INT "$BC_PID" 2>/dev/null || true; sleep 2; kill -TERM "$BC_PID" 2>/dev/null || true; wait "$BC_PID" 2>/dev/null || true; BC_PID=""
kill -INT "$TCPDUMP_PID" 2>/dev/null || true; wait "$TCPDUMP_PID" 2>/dev/null || true; TCPDUMP_PID=""
kill -TERM "$LISTENER_PID" 2>/dev/null || true; wait "$LISTENER_PID" 2>/dev/null || true; LISTENER_PID=""

PCAP_SHA="$(sudo sha256sum "$PCAP" | awk '{print $1}')"
HTTP_COUNT="$(grep -c '\[HTTP\]' "$APP_LOG" 2>/dev/null || true)"
TLS_COUNT="$(grep -c '\[TLS\]' "$APP_LOG" 2>/dev/null || true)"

{
  echo "# Experiment Report: HTTP-ENDPOINT-004"
  echo
  echo "- Date: $(date --iso-8601=seconds)"
  echo "- Receiver: $TARGET_IP / $TARGET_MAC"
  echo "- PC: $LOCAL_IP on $IFACE"
  echo "- Gateway: $GATEWAY"
  echo "- Duration: ${DURATION}s"
  echo "- Raw PCAP SHA-256: $PCAP_SHA (raw PCAP remains local)"
  echo "- HTTP requests observed: $HTTP_COUNT"
  echo "- TLS first-flights observed: $TLS_COUNT"
  echo
  echo "## Redirected endpoints"
  for endpoint in "${ENDPOINTS[@]}"; do echo "- $endpoint:80 and $endpoint:443"; done
  echo
  echo "## Safe endpoint observations"
  grep -E '\[(HTTP|TLS)\]' "$APP_LOG" 2>/dev/null || echo "No HTTP/TLS application request reached the local sinks."
  echo
  echo "## Interpretation"
  echo "This experiment intentionally served no firmware. HTTP received 404; TLS was observed only through the first client flight. Review request paths, Host headers and SNI for provisioning/update clues."
} >"$REPORT"

echo "DONE. Report: $REPORT"
echo "Raw private material: $LOCAL_DIR"
echo "Review, then commit only the report."
