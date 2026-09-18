# Hardware Overview: Sagemcom DSI74 V2 HD GVT - BRA

## Physical Identification & Labels

```text
Manufacturer: Sagemcom
Model:        DSI74 V2 HD GVT - BRA
PCB Marking:  M74X-1
              25353567/99-A
Power Input:  12 V / 2.0 A DC (Center-positive barrel jack)
```

## Rear Physical Interfaces

| Port | Connector Type | Physical Status |
| :--- | :--- | :--- |
| **RF In** | F-Type Coaxial | Satellite DVB-S/S2 input |
| **HDMI** | HDMI Type-A | Digital video/audio output |
| **Composite Video** | RCA (Yellow) | Analog CVBS video output |
| **Component Video** | RCA (Green/Blue/Red) | Y/Pb/Pr analog HD video |
| **Analog Audio** | RCA (White/Red) | Stereo L/R line out |
| **Digital Audio** | RCA (Orange) | Coaxial S/PDIF output |
| **Ethernet** | 8P8C (RJ-45) | 10/100 Mbps Fast Ethernet |
| **USB** | USB Type-A | USB 2.0 Host port |
| **Power** | Barrel Jack | 12 V DC input |

## Front Panel & User Interface

- **Display:** Multi-segment numeric display driven by dedicated controller IC.
- **Controls:** Physical push buttons (Power, Channel Up/Down, Volume Up/Down).
- **Sensors:** Infrared (IR) receiver module for remote control.

## Existing Vendor Firmware & UI

The receiver currently boots the factory GVT / Vivo television firmware:
- **Firmware Version:** `1.322.20180523`
- **Portal Version:** `1.0.5`
- **Exposed Menus:**
  - Satellite / DTH installation & channel search
  - IP connection quality metrics
  - Ethernet network configuration
  - USB Wi-Fi adapter configuration (strictly prompts for a certified Vivo USB Wi-Fi dongle, confirming active USB host stack in OEM software)
  - System reboot
  - PAL-M video output standard selection
