#!/usr/bin/env bash
# Discover the receiver's post-boot lease before starting exact-target interception.
set -euo pipefail

IFACE="${IFACE:-enp5s0}"
TARGET_MAC="68:15:90:6b:81:96"
DURATION="${1:-3600}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LAST_IP_FILE="${REPO_DIR}/captures/receiver_last_ip"
WAIT_SECONDS="${RECEIVER_WAIT_SECONDS:-180}"
REQUIRE_OFFLINE="${REQUIRE_RECEIVER_OFFLINE:-0}"

if [ "${EUID}" -ne 0 ]; then
    echo "[-] Run as root; no network state was changed." >&2
    exit 1
fi

echo "[*] Waiting for one previously observed receiver lease to become live."
echo "[*] No interception state is installed during identity discovery."

declare -a CANDIDATES=()
if [ -n "${RECEIVER_IP:-}" ]; then
    CANDIDATES+=("${RECEIVER_IP}")
fi
if [ -s "${LAST_IP_FILE}" ]; then
    CANDIDATES+=("$(head -n 1 "${LAST_IP_FILE}")")
fi
while IFS= read -r candidate; do
    CANDIDATES+=("${candidate}")
done < <(
    ip neigh show dev "${IFACE}" |
        awk -v mac="${TARGET_MAC}" '$0 !~ /FAILED|INCOMPLETE/ { for (i=1; i<NF; i++) if ($i == "lladdr" && tolower($(i+1)) == tolower(mac)) print $1 }'
)

# Historical exact leases are bounded candidates, not a scan range.
CANDIDATES+=(192.168.1.62 192.168.1.61 192.168.1.57 192.168.1.54)
mapfile -t CANDIDATES < <(printf '%s\n' "${CANDIDATES[@]}" | awk '/^([0-9]{1,3}\.){3}[0-9]{1,3}$/ && !seen[$0]++')

candidate_is_receiver() {
    local candidate="$1"
    local arp_output observed_mac
    arp_output="$(arping -I "${IFACE}" -c 1 -w 2 "${candidate}" 2>&1 || true)"
    observed_mac="$(printf '%s\n' "${arp_output}" | grep -Eio '([0-9a-f]{2}:){5}[0-9a-f]{2}' | tr '[:upper:]' '[:lower:]' | sort -u)"
    [ "${observed_mac}" = "${TARGET_MAC}" ]
}

if [ "${REQUIRE_OFFLINE}" = "1" ]; then
    echo "[*] Waiting to observe the receiver go offline before post-boot discovery."
    offline_count=0
    while [ "${offline_count}" -lt 2 ]; do
        any_live=0
        for candidate in "${CANDIDATES[@]}"; do
            if candidate_is_receiver "${candidate}"; then
                observed_mac="$(ip neigh show to "${candidate}" dev "${IFACE}" | awk '$0 !~ /FAILED|INCOMPLETE/ { for (i=1; i<NF; i++) if ($i == "lladdr") print tolower($(i+1)) }' | sort -u)"
                if [ "${observed_mac}" = "${TARGET_MAC}" ]; then
                    any_live=1
                fi
            fi
        done
        if [ "${any_live}" -eq 0 ]; then
            offline_count=$((offline_count + 1))
        else
            offline_count=0
        fi
        sleep 1
    done
    echo "[+] Receiver offline transition observed; waiting for post-boot lease."
fi

deadline=$((SECONDS + WAIT_SECONDS))
CURRENT_IP=""
while [ "${SECONDS}" -lt "${deadline}" ]; do
    declare -a LIVE_IPS=()
    for candidate in "${CANDIDATES[@]}"; do
        if candidate_is_receiver "${candidate}"; then
            observed_mac="$(ip neigh show to "${candidate}" dev "${IFACE}" | awk '$0 !~ /FAILED|INCOMPLETE/ { for (i=1; i<NF; i++) if ($i == "lladdr") print tolower($(i+1)) }' | sort -u)"
            if [ "${observed_mac}" = "${TARGET_MAC}" ]; then
                LIVE_IPS+=("${candidate}")
            fi
        fi
    done
    if [ "${#LIVE_IPS[@]}" -eq 1 ]; then
        CURRENT_IP="${LIVE_IPS[0]}"
        break
    fi
    if [ "${#LIVE_IPS[@]}" -gt 1 ]; then
        echo "[-] Multiple live IPs resolve to ${TARGET_MAC}: ${LIVE_IPS[*]}" >&2
        echo "[-] STOP: no ARP, iptables, or sysctl state was changed." >&2
        exit 1
    fi
    echo "[*] Receiver not live yet; retrying exact candidates in 3 seconds..."
    sleep 3
done

if [ -z "${CURRENT_IP}" ]; then
    echo "[-] No previously observed receiver lease became live within ${WAIT_SECONDS}s." >&2
    echo "[-] STOP: no ARP, iptables, or sysctl state was changed." >&2
    exit 1
fi

mkdir -p "$(dirname "${LAST_IP_FILE}")"
printf '%s\n' "${CURRENT_IP}" >"${LAST_IP_FILE}"
echo "[+] Live receiver verified before mutation: ${CURRENT_IP} (${TARGET_MAC})"
exec env RECEIVER_IP="${CURRENT_IP}" "${SCRIPT_DIR}/run_net_config_005.sh" "${DURATION}"
