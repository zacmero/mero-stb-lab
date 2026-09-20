# Isolated Ethernet Receiver Lab

## Purpose

Connect the receiver directly to a second Linux computer and observe its boot
and application protocols without ARP spoofing, port mirroring, or changes to
the household router. The lab computer answers DHCP and DNS locally, owns the
receiver's historical service addresses, logs HTTP, and records a packet
capture.

The observation profile returns HTTP 404. It does not provide firmware or an
update manifest.

## Topology

```text
development computer --Ethernet-- household router --Wi-Fi-- lab laptop
                                                           |
                                                     Ethernet cable
                                                           |
                                                    Sagemcom DSI74
```

The lab laptop needs a household-network control interface and a dedicated
receiver Ethernet interface. The proven setup uses:

```text
control:       wlp4s0, 192.168.1.80/24
receiver:      enp6s0
lab gateway:   10.74.0.1
receiver:      10.74.0.10
receiver MAC:  68:15:90:6b:81:96
```

If the lab computer has only one interface, use its local console or add a
second interface. Reassigning the interface carrying SSH will end that session.

## Tools

- `ip`: inspect links, addresses, and routes; add isolated addresses.
- `nmcli`: temporarily release only the receiver interface from NetworkManager.
- `dnsmasq`: exact-MAC DHCP lease and catch-all local DNS.
- `tcpdump`: full receiver packet capture.
- Python `http.server`: interface-bound request logger and 404 responder.
- `ss` and `pgrep`: verify listeners and child processes.
- `jq`: inspect JSON Lines request records.
- `sha256sum`: verify deployed scripts.
- `ssh` and `scp`: supervise and deploy over the separate control interface.

Repository components:

- `scripts/run_isolated_receiver_lab.sh`
- `scripts/isolated_http_logger.py`

## Prepare the lab computer

On Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y openssh-server dnsmasq tcpdump jq
sudo systemctl enable --now ssh
```

Inventory the machine before changing anything:

```bash
ip -br link
ip -br addr
ip route
nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device
```

Confirm that the default route uses the control interface and that the intended
receiver interface has no default route. Establish and verify key-based SSH
before connecting the receiver if remote supervision is required.

## Deploy

Copy both scripts to the lab computer:

```bash
install -d -m 700 "$HOME/mero-stb-isolated/scripts"
scp scripts/run_isolated_receiver_lab.sh \
    scripts/isolated_http_logger.py \
    user@LAB_COMPUTER_IP:mero-stb-isolated/scripts/
```

On the lab computer:

```bash
chmod 700 "$HOME/mero-stb-isolated/scripts/"*
bash -n "$HOME/mero-stb-isolated/scripts/run_isolated_receiver_lab.sh"
python3 -m py_compile "$HOME/mero-stb-isolated/scripts/isolated_http_logger.py"
```

Compare local and remote `sha256sum` output before the privileged run.

## Connect the receiver directly

1. Leave the receiver powered off and Ethernet disconnected.
2. Keep the lab computer connected through its control interface.
3. Start the runner locally:

   ```bash
   sudo "$HOME/mero-stb-isolated/scripts/run_isolated_receiver_lab.sh"
   ```

4. Wait for `READY: isolated receiver lab`.
5. Verify control routing and disabled forwarding:

   ```bash
   ip route
   sysctl net.ipv4.ip_forward
   ss -lntup | grep -E '(:53 |:80 )'
   ```

6. Connect a normal Ethernet cable between the lab computer and receiver.
   Modern ports normally support auto-MDI-X; a crossover cable is not normally
   required.
7. Cold boot the receiver.
8. Wait for DHCP and initial service attempts before pressing remote buttons.
9. Trigger one intended receiver action at a time and record its timestamp.
10. Stop the runner with `Ctrl-C` after capture completes.

The runner assigns only:

```text
10.74.0.1/24
191.32.31.251/32
186.215.183.217/32
213.140.61.225/32
```

It does not enable forwarding, NAT, ARP spoofing, or firewall rules. The HTTP
socket is restricted to the receiver interface with `SO_BINDTODEVICE`.

## Analyze data

Find the current artifact directory:

```bash
run=$(find "$HOME/mero-stb-isolated/captures" \
  -mindepth 1 -maxdepth 1 -type d | sort | tail -1)
echo "$run"
```

Follow events and inspect transactions:

```bash
tail -F "$run/dnsmasq.log" "$run/http.stdout"
jq . "$run/http.jsonl"
tcpdump -nn -tttt -r "$run/receiver.pcap" \
  'ether host 68:15:90:6b:81:96'
```

Narrow protocol views:

```bash
tcpdump -nn -r "$run/receiver.pcap" 'port 53 or port 67 or port 68'
tcpdump -nn -r "$run/receiver.pcap" 'tcp port 80 or tcp port 443'
```

Each HTTP record contains timestamp, client, method, request target, headers,
body length, body SHA-256, and a bounded body preview. The pcap is the canonical
packet-level artifact.

## Cleanup verification

Normal exit, failure, `Ctrl-C`, and termination use the same cleanup trap. It
stops children, removes only addresses added by the run, restores the previous
forwarding value, and returns Ethernet to NetworkManager if previously managed.

After exit:

```bash
pgrep -af 'dnsmasq|isolated_http_logger|tcpdump.*enp6s0'
ip -br addr show enp6s0
ip route
sysctl net.ipv4.ip_forward
ping -I wlp4s0 -c 2 192.168.1.1
```

Do not reconnect the receiver to the household router before cleanup finishes.

## First-session evidence

The first isolated session established:

- exact receiver lease `10.74.0.10` and DHCP client `udhcp 1.20.2`;
- DNS query for `ucstb.vivoplay.com.br`;
- HTTPS attempts to the resolved address and `191.32.31.251`;
- an HTTP highlight request to `186.215.183.217`;
- an HTTP health probe to `191.32.31.251`;
- Vivo Play requests for `/tv-config/appConfigFit.json` and
  `/bussola/redirect`;
- connectivity probes to `8.8.8.8`, followed by gateway probes;
- clean return to the normal no-service screen after deliberate HTTP 404s.

This demonstrates controlled service observation. It does not identify a
firmware manifest or validate an update package.
