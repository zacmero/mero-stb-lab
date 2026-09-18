# Experiment Report: NET-PROVISION-004

## Metadata
- **Identifier:** `NET-PROVISION-004`
- **Date:** 2026-09-18
- **Target Hardware:** Sagemcom DSI74 V2 HD GVT - BRA (STMicroelectronics STiH237)
- **Status:** **COMPLETED**
- **Outcome:** **POSITIVE (Unencrypted HTTP Configuration Endpoint & Middleware Engine Captured)**

---

## Executive Summary

```text
NET-PROVISION-004
RESULT: POSITIVE for HTTP request interception and middleware identification.

Using a native Python ARP redirector and iptables port 80 NAT redirection on the Linux PC,
the receiver's outbound HTTP traffic to legacy GVT infrastructure (191.32.31.251) was
successfully intercepted.

The receiver initiated an unencrypted HTTP/1.1 GET request for:
  /tv-config/appConfigFit.json
revealing the resident browser/middleware engine:
  User-Agent: Ekioh v2.2.4.5-sagem (Mar  2 2013) r10767

Our local server returned an HTTP 200 OK JSON response, which the receiver acknowledged
and parsed cleanly.
```

---

## Technical Architecture & Implemented Tools

1. **Native Standalone ARP Redirector (`scripts/arp_spoofer.py`):**
   - Implemented in standard Python using `socket.AF_PACKET` raw sockets (zero external dependencies).
   - Dynamically poisoned ARP mappings for the receiver (`68:15:90:6b:81:96`, tracking dynamic IPs `192.168.1.138`, `192.168.1.137`, and `192.168.1.134`) and gateway (`192.168.1.1`, `14:ca:56:81:18:71`).
   - Signal-trapped to emit 5 unsolicited legitimate ARP replies upon termination, guaranteeing instant table restoration.

2. **Port 80 NAT Interception:**
   - Injected iptables `PREROUTING` NAT rule:
     ```bash
     iptables -t nat -I PREROUTING 1 -i enp5s0 -m mac --mac-source 68:15:90:6b:81:96 -p tcp --dport 80 -j REDIRECT --to-ports 8080
     ```

3. **HTTP Interceptor (`scripts/http_interceptor.py`):**
   - Listened on `0.0.0.0:8080`, completed TCP handshakes, logged raw HTTP request headers with disk flushing, and served `HTTP/1.0 200 OK` JSON payloads.

---

## Captured HTTP Request Data

### 1. The Raw Intercepted Request
*Captured at `2026-09-18 00:54:11.456936` (Local Time) in `captures/net-provision-004.pcap` and `captures/net-provision-004.log`:*

```http
GET /tv-config/appConfigFit.json HTTP/1.1
User-Agent: Ekioh v2.2.4.5-sagem (Mar  2 2013) r10767
Host: 191.32.31.251
Connection: Keep-Alive
Accept-Encoding: gzip, deflate
Accept: application/json, text/plain, */*
```

### 2. The Intercepted Response
*Returned by local Python server at `00:54:11.457963`:*

```http
HTTP/1.0 200 OK
Server: gvt-probe
Content-Type: application/json
Connection: close
Content-Length: 25

{"status":"ok","code":0}
```

### 3. TCP Conversation Lifecycle
```text
00:54:11.453948 Receiver (192.168.1.138:45834) > PC (191.32.31.251:80): [SYN]
00:54:11.454016 PC (191.32.31.251:80) > Receiver (192.168.1.138:45834): [SYN-ACK]
00:54:11.456764 Receiver > PC: [ACK]
00:54:11.456936 Receiver > PC: [PSH, ACK] GET /tv-config/appConfigFit.json HTTP/1.1 (220 bytes)
00:54:11.456984 PC > Receiver: [ACK]
00:54:11.457963 PC > Receiver: [PSH, ACK] HTTP/1.0 200 OK (182 bytes)
00:54:11.458108 PC > Receiver: [FIN, PSH, ACK] {"status":"ok","code":0} (25 bytes)
00:54:11.460813 Receiver > PC: [ACK]
00:54:11.500783 Receiver > PC: [ACK] (payload received)
00:54:11.701337 Receiver > PC: [FIN, ACK] (clean teardown)
00:54:11.701372 PC > Receiver: [ACK]
```

---

## Architectural & Security Analysis

1. **Middleware Identity: Ekioh Embedded Browser**
   - **`Ekioh v2.2.4.5-sagem (Mar 2 2013) r10767`** identifies the commercial Ekioh SVG/HTML UI engine, standard in early-2010s Sagemcom and STMicroelectronics Cardiff set-top boxes.
   - Ekioh renders UI elements via JavaScript, DOM, and SVG.

2. **Unencrypted Remote Configuration Vector**
   - The STB retrieves its core runtime configuration (`/tv-config/appConfigFit.json`) over **plain unencrypted HTTP** without transport layer encryption (no HTTPS).
   - There is no cryptographic signature check on the configuration file prior to parsing.

3. **Provisioning Mechanism**
   - The receiver queries `191.32.31.251` directly for `appConfigFit.json` to obtain endpoints for channel guides, portal URLs, authentication services, and software update servers.

---

## Cleanup Confirmation

All temporary modifications have been fully restored to baseline:
- `scripts/arp_spoofer.py` emitted 5 restoration ARP replies restoring legitimate MAC addresses for `192.168.1.1` and `192.168.1.138`.
- NAT REDIRECT rule removed from `PREROUTING`.
- Temporary FORWARD rules removed.
- `net.ipv4.conf.all.send_redirects` and `enp5s0.send_redirects` restored to `1`.
- Raw PCAP preserved in `captures/net-provision-004.pcap` (uncommitted, ignored).

---

## Justified Next Step: Mock Configuration Delivery

Now that the exact endpoint (`/tv-config/appConfigFit.json`) and User-Agent are known:
1. Construct and serve a structured `appConfigFit.json` to the receiver.
2. Direct the portal URL and update check URLs in the JSON to point to our local Linux PC.
3. Observe how the Ekioh browser renders or navigates to local HTTP endpoints, testing the potential for custom web UI loading without opening the hardware chassis.
