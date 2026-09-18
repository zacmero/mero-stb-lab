# Agent Safety Rules — mero-stb-lab

These rules are mandatory for every coding/research agent working in this repository.

## Live network experiments

The home LAN is production infrastructure. Treat every ARP, routing, firewall, DHCP,
DNS, bridge, NAT, packet-injection, or gateway change as potentially disruptive.

1. **Never target a DHCP range, CIDR, wildcard, or guessed IP set.**
   A live MITM target must resolve to exactly one current STB IPv4 address from the
   known STB MAC (`68:15:90:6b:81:96`). Zero or multiple matches => abort.
2. **Never poison unrelated clients.** ARP MITM may involve only the exact STB IP and
   the gateway IP. Do not send forged ownership for any other LAN address.
3. **Never invent restoration mappings.** Cleanup must restore the authentic
   STB-IP -> STB-MAC and gateway-IP -> gateway-MAC bindings only.
4. **Never change router configuration, factory-reset the router, alter DHCP, or write
   persistent gateway state as part of an STB experiment.**
5. **Require explicit human arming for live mutation.** Preparation, capture analysis,
   and dry-run checks may be autonomous; ARP spoofing/firewall/NAT mutation may not
   start unless the user explicitly authorizes that run in the current session.
6. **Bound every live run.** Default to <=180 seconds, install EXIT/INT/TERM cleanup,
   and verify `192.168.1.1` is reachable after cleanup.
7. **Fail closed.** If target identity, gateway identity, interface, cleanup state, or
   current LAN health is ambiguous, abort rather than guess.
8. **One variable per experiment.** Preserve a baseline and change only the property
   under test so results remain interpretable.

## Incident precedent

On 2026-09-18 the original NET-CONFIG-005 harness poisoned `192.168.1.128-160`
and its cleanup incorrectly mapped every address in that range to the STB MAC.
This disrupted LAN return traffic until the STB/host were disconnected and the
router was power-cycled. Do not reintroduce that design.
