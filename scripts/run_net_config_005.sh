#!/usr/bin/env bash
# NET-CONFIG-005: exact-target HTTP/HTTPS interception session.
set -euo pipefail

IFACE="${IFACE:-enp5s0}"
RECEIVER_IP="${RECEIVER_IP:-}"
TARGET_MAC="68:15:90:6b:81:96"
GATEWAY_IP="192.168.1.1"
HTTP_PORT="8080"
HTTPS_PORT="8443"
DURATION="${1:-1800}"
DNS_TEST_NAME="example.com"
CONNECTIVITY_URL="https://example.com/"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CAPTURES_DIR="${REPO_DIR}/captures"
PCAP_FILE="${CAPTURES_DIR}/net-config-005.pcap"
HTTP_LOG="${CAPTURES_DIR}/net-config-005.log"
INTERCEPTOR_STDOUT="${CAPTURES_DIR}/http_interceptor_config005.log"
ARP_LOG="${CAPTURES_DIR}/arp_spoofer_config005.log"
END_SESSION_FILE="/tmp/mero_end_session_$$"
FILTER_CHAIN="MNC005F_$$"
NAT_CHAIN="MNC005N_$$"

CLEANED_UP=0
SYSCTLS_CHANGED=0
FILTER_CHAIN_CREATED=0
NAT_CHAIN_CREATED=0
HTTP_PID=""
ARP_PID=""
TCPDUMP_PID=""

stop_process() {
    local name="$1"
    local pid="$2"
    if [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null; then
        echo "[*] Stopping ${name} (PID ${pid})..."
        kill -TERM "${pid}" 2>/dev/null || true
        wait "${pid}" 2>/dev/null || true
    fi
}

cleanup() {
    local failed=0
    if [ "${CLEANED_UP}" -eq 1 ]; then
        return
    fi
    CLEANED_UP=1
    trap - EXIT INT TERM
    echo "[*] Cleaning up NET-CONFIG-005..."

    stop_process "ARP redirector" "${ARP_PID}"
    stop_process "HTTP/HTTPS interceptor" "${HTTP_PID}"
    stop_process "tcpdump" "${TCPDUMP_PID}"
    rm -f "${END_SESSION_FILE}"

    if [ "${NAT_CHAIN_CREATED}" -eq 1 ]; then
        while iptables -t nat -C PREROUTING -i "${IFACE}" -j "${NAT_CHAIN}" 2>/dev/null; do
            iptables -t nat -D PREROUTING -i "${IFACE}" -j "${NAT_CHAIN}" || failed=1
        done
        iptables -t nat -F "${NAT_CHAIN}" 2>/dev/null || failed=1
        iptables -t nat -X "${NAT_CHAIN}" 2>/dev/null || failed=1
    fi
    if [ "${FILTER_CHAIN_CREATED}" -eq 1 ]; then
        while iptables -C FORWARD -i "${IFACE}" -j "${FILTER_CHAIN}" 2>/dev/null; do
            iptables -D FORWARD -i "${IFACE}" -j "${FILTER_CHAIN}" || failed=1
        done
        iptables -F "${FILTER_CHAIN}" 2>/dev/null || failed=1
        iptables -X "${FILTER_CHAIN}" 2>/dev/null || failed=1
    fi

    if [ "${SYSCTLS_CHANGED}" -eq 1 ]; then
        sysctl -w "net.ipv4.conf.all.send_redirects=${ORIG_REDIRECT_ALL}" >/dev/null || failed=1
        sysctl -w "net.ipv4.conf.${IFACE}.send_redirects=${ORIG_REDIRECT_IF}" >/dev/null || failed=1
        [ "$(sysctl -n net.ipv4.conf.all.send_redirects)" = "${ORIG_REDIRECT_ALL}" ] || failed=1
        [ "$(sysctl -n "net.ipv4.conf.${IFACE}.send_redirects")" = "${ORIG_REDIRECT_IF}" ] || failed=1
    fi

    for pid in "${ARP_PID}" "${HTTP_PID}" "${TCPDUMP_PID}"; do
        if [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null; then
            echo "[-] Cleanup verification failed: PID ${pid} is still running." >&2
            failed=1
        fi
    done
    if iptables-save | grep -Fq -- "${FILTER_CHAIN}" || iptables-save -t nat | grep -Fq -- "${NAT_CHAIN}"; then
        echo "[-] Cleanup verification failed: a run-owned iptables rule remains." >&2
        failed=1
    fi

    if [ "${failed}" -eq 0 ]; then
        echo "[+] Cleanup verified: run-owned processes and firewall rules are gone."
    else
        echo "[-] Cleanup was incomplete; inspect the errors above before another run." >&2
        return 1
    fi
}

trap cleanup EXIT
trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "[-] Required command not found: $1" >&2
        exit 1
    fi
}

network_health_check() {
    local phase="$1"
    echo "[*] ${phase}: checking gateway, DNS, and HTTPS connectivity..."
    if ! ping -I "${IFACE}" -c 2 -W 2 "${GATEWAY_IP}" >/dev/null; then
        echo "[-] ${phase}: gateway=FAIL" >&2
        return 1
    fi
    if ! getent ahostsv4 "${DNS_TEST_NAME}" >/dev/null; then
        echo "[-] ${phase}: dns=FAIL" >&2
        return 1
    fi
    if ! curl --interface "${IFACE}" --fail --silent --show-error --location \
        --connect-timeout 5 --max-time 15 --output /dev/null "${CONNECTIVITY_URL}"; then
        echo "[-] ${phase}: https=FAIL" >&2
        return 1
    fi
    echo "[+] ${phase}: gateway=PASS dns=PASS https=PASS"
}

resolve_exact_neighbor() {
    local ip="$1"
    local expected_mac="$2"
    local arp_output observed_mac

    if ! ping -I "${IFACE}" -c 1 -W 2 "${ip}" >/dev/null; then
        echo "[-] ${ip} did not answer the identity-validation ping." >&2
        exit 1
    fi
    observed_mac="$(ip neigh show to "${ip}" dev "${IFACE}" | awk '$0 !~ /FAILED|INCOMPLETE/ { for (i=1; i<NF; i++) { if ($i == "lladdr") print tolower($(i+1)) } }' | sort -u)"
    arp_output="$(arping -I "${IFACE}" -c 2 -w 3 "${ip}" 2>&1 || true)"
    observed_mac="$(printf '%s\n' "${arp_output}" | grep -Eio '([0-9a-f]{2}:){5}[0-9a-f]{2}' | tr '[:upper:]' '[:lower:]' | sort -u)"
    if [ "${observed_mac}" != "${expected_mac}" ]; then
        echo "[-] ${ip} did not resolve uniquely to expected MAC ${expected_mac}; observed: ${observed_mac:-none}" >&2
        exit 1
    fi
}

if [ "${EUID}" -ne 0 ]; then
    echo "[-] Run as root; no network state was changed." >&2
    exit 1
fi

for command_name in ip ping arping getent curl iptables iptables-save sysctl tcpdump python3 awk sort grep tr; do
    require_command "${command_name}"
done

if ! [[ "${DURATION}" =~ ^[1-9][0-9]*$ ]]; then
    echo "[-] Duration must be a positive integer." >&2
    exit 1
fi

mkdir -p "${CAPTURES_DIR}"
if iptables-save | grep -q 'MNC005'; then
    echo "[-] Stale MNC005 firewall rules exist; stop and inspect exact owners before starting another run." >&2
    exit 1
fi

echo "[*] Running read-only host-network preflight before ARP, iptables, or sysctl changes..."
network_health_check "PREFLIGHT"

# A DHCP reservation or immediately preceding passive discovery may provide a
# candidate. It is never trusted by itself: the targeted probe below only
# populates the neighbor table, and the exact MAC comparison remains mandatory.
if [ -n "${RECEIVER_IP}" ]; then
    if ! [[ "${RECEIVER_IP}" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
        echo "[-] RECEIVER_IP is not an IPv4 address: ${RECEIVER_IP}" >&2
        exit 1
    fi
    echo "[*] Validating configured receiver ${RECEIVER_IP} against exact MAC ${TARGET_MAC}..."
    resolve_exact_neighbor "${RECEIVER_IP}" "${TARGET_MAC}"
    TARGET_IPS=("${RECEIVER_IP}")
else
    # Stale prior DHCP mappings are common after a cold boot. Only consult the
    # whole neighbor cache when no actively verified current IP was supplied.
    mapfile -t TARGET_IPS < <(
        ip neigh show dev "${IFACE}" |
            awk -v mac="${TARGET_MAC}" '$0 !~ /FAILED|INCOMPLETE/ { for (i=1; i<NF; i++) { if ($i == "lladdr" && tolower($(i+1)) == tolower(mac)) print $1 } }' |
            sort -u
    )
fi

# 2. If absent from neighbor cache, passively capture DHCP/ARP broadcasts for up to 120s
if [ "${#TARGET_IPS[@]}" -eq 0 ]; then
    echo "[*] Receiver identity not found in current neighbor table."
    mapfile -t DISCOVERED_IPS < <(
        python3 "${SCRIPT_DIR}/passive_receiver_discovery.py" "${IFACE}" "${TARGET_MAC}" 120
    )
    if [ "${#DISCOVERED_IPS[@]}" -eq 1 ]; then
        CANDIDATE_IP="${DISCOVERED_IPS[0]}"
        echo "[+] Exactly one candidate IP discovered from broadcast: ${CANDIDATE_IP}"
        echo "[*] Validating candidate IP via targeted ping probe..."
        ping -I "${IFACE}" -c 1 -W 2 "${CANDIDATE_IP}" >/dev/null 2>&1 || true
        sleep 1
        mapfile -t TARGET_IPS < <(
            ip neigh show to "${CANDIDATE_IP}" dev "${IFACE}" |
                awk -v mac="${TARGET_MAC}" '$0 !~ /FAILED|INCOMPLETE/ { for (i=1; i<NF; i++) { if ($i == "lladdr" && tolower($(i+1)) == tolower(mac)) print $1 } }' |
                sort -u
        )
    elif [ "${#DISCOVERED_IPS[@]}" -gt 1 ]; then
        echo "[-] Multiple candidate IPs discovered: ${DISCOVERED_IPS[*]}; identity is ambiguous." >&2
        echo "[-] STOP: no ARP, iptables, or sysctl state was changed." >&2
        exit 1
    fi
fi

if [ "${#TARGET_IPS[@]}" -ne 1 ]; then
    echo "[-] Expected exactly one current receiver IP for ${TARGET_MAC}; found ${#TARGET_IPS[@]}." >&2
    echo "[-] STOP: no ARP, iptables, or sysctl state was changed." >&2
    exit 1
fi
TARGET_IP="${TARGET_IPS[0]}"

resolve_exact_neighbor "${TARGET_IP}" "${TARGET_MAC}"
GATEWAY_MAC="$(ip neigh show to "${GATEWAY_IP}" dev "${IFACE}" | awk '$0 !~ /FAILED|INCOMPLETE/ { for (i=1; i<NF; i++) { if ($i == "lladdr") print tolower($(i+1)) } }' | sort -u)"
if ! [[ "${GATEWAY_MAC}" =~ ^([0-9a-f]{2}:){5}[0-9a-f]{2}$ ]]; then
    echo "[-] Gateway ${GATEWAY_IP} did not resolve to one valid MAC; observed: ${GATEWAY_MAC:-none}" >&2
    exit 1
fi
resolve_exact_neighbor "${GATEWAY_IP}" "${GATEWAY_MAC}"

echo "[+] Verified receiver: ${TARGET_IP} (${TARGET_MAC})"
echo "[+] Verified gateway:  ${GATEWAY_IP} (${GATEWAY_MAC})"

ORIG_REDIRECT_ALL="$(sysctl -n net.ipv4.conf.all.send_redirects)"
ORIG_REDIRECT_IF="$(sysctl -n "net.ipv4.conf.${IFACE}.send_redirects")"

SYSCTLS_CHANGED=1
sysctl -w net.ipv4.conf.all.send_redirects=0 >/dev/null
sysctl -w "net.ipv4.conf.${IFACE}.send_redirects=0" >/dev/null

iptables -N "${FILTER_CHAIN}"
FILTER_CHAIN_CREATED=1
iptables -A "${FILTER_CHAIN}" -m mac --mac-source "${TARGET_MAC}" -s "${TARGET_IP}" -j ACCEPT
iptables -A "${FILTER_CHAIN}" -d "${TARGET_IP}" -j ACCEPT
iptables -I FORWARD 1 -i "${IFACE}" -j "${FILTER_CHAIN}"

iptables -t nat -N "${NAT_CHAIN}"
NAT_CHAIN_CREATED=1
iptables -t nat -A "${NAT_CHAIN}" -m mac --mac-source "${TARGET_MAC}" -s "${TARGET_IP}" -p tcp --dport 80 -j REDIRECT --to-ports "${HTTP_PORT}"
iptables -t nat -A "${NAT_CHAIN}" -m mac --mac-source "${TARGET_MAC}" -s "${TARGET_IP}" -p tcp --dport 443 -j REDIRECT --to-ports "${HTTPS_PORT}"
iptables -t nat -I PREROUTING 1 -i "${IFACE}" -j "${NAT_CHAIN}"

rm -f /tmp/mero_active_case.json "${END_SESSION_FILE}"
export MERO_END_SESSION_FILE="${END_SESSION_FILE}"
python3 -u "${SCRIPT_DIR}/http_interceptor.py" "${HTTP_PORT}" "${HTTP_LOG}" "${HTTPS_PORT}" >"${INTERCEPTOR_STDOUT}" 2>&1 &
HTTP_PID=$!
sleep 1
if ! kill -0 "${HTTP_PID}" 2>/dev/null; then
    echo "[-] HTTP/HTTPS interceptor failed to start." >&2
    exit 1
fi

tcpdump -i "${IFACE}" -s 0 -nn -U -w "${PCAP_FILE}" "ether host ${TARGET_MAC}" >/dev/null 2>&1 &
TCPDUMP_PID=$!
sleep 1
if ! kill -0 "${TCPDUMP_PID}" 2>/dev/null; then
    echo "[-] tcpdump failed to start." >&2
    exit 1
fi

python3 -u "${SCRIPT_DIR}/arp_spoofer.py" "${IFACE}" "${TARGET_IP}" "${TARGET_MAC}" "${GATEWAY_IP}" "${GATEWAY_MAC}" >"${ARP_LOG}" 2>&1 &
ARP_PID=$!
sleep 1
if ! kill -0 "${ARP_PID}" 2>/dev/null; then
    echo "[-] ARP redirector failed to start." >&2
    exit 1
fi

if ! network_health_check "POST-INTERCEPTION"; then
    echo "[-] Network health regressed after interception; stopping immediately." >&2
    exit 1
fi

echo "[+] READY FOR CASE-00"
echo "[+] Interception is limited to ${TARGET_IP} (${TARGET_MAC}) for ${DURATION} seconds."
echo "[+] APP-API-009B + MEDIA-010 is ready. Open Vivo Play once."
echo "[+] Selecting END SESSION in the receiver app will request immediate verified cleanup."

deadline=$((SECONDS + DURATION))
while [ "${SECONDS}" -lt "${deadline}" ]; do
    if [ -f "${END_SESSION_FILE}" ]; then
        echo "[+] Verified receiver requested END SESSION; cleaning up now."
        break
    fi
    sleep 1
done
