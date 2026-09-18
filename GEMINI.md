# Gemini instructions — mero-stb-lab

Before modifying or running any network experiment, read and obey `AGENTS.md`.

Hard stop rules:
- NEVER ARP-poison a range/CIDR/list or guessed client addresses.
- NEVER use an entire DHCP pool as a target set.
- Live MITM must target exactly one IP resolved from STB MAC `68:15:90:6b:81:96`.
- NEVER alter/reset/persistently configure the router as part of STB testing.
- NEVER start ARP/firewall/NAT mutation without explicit human approval for that run.
- If target identity or cleanup correctness is uncertain, abort.

The 2026-09-18 NET-CONFIG-005 LAN outage was caused by violating these rules.
