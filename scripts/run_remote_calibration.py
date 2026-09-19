#!/usr/bin/env python3
"""Interactive controller for REMOTE-MAP-007."""

import json
import atexit
import pathlib
import signal
import sys
import time
import urllib.error
import urllib.request


BASE_URL = "http://127.0.0.1:8080"
RESULTS_FILE = pathlib.Path(__file__).resolve().parent.parent / "captures" / "remote-map-007.json"
BUTTONS = [
    "UP", "DOWN", "LEFT", "RIGHT", "OK", "BACK", "EXIT", "HOME", "MENU",
    "GUIDE", "INFO", "RED", "GREEN", "YELLOW", "BLUE",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "PLAY", "PAUSE", "STOP", "RECORD", "REWIND", "FAST_FORWARD",
    "PREVIOUS", "NEXT", "VOLUME_UP", "VOLUME_DOWN", "MUTE",
    "CHANNEL_UP", "CHANNEL_DOWN", "VIVO_PLAY", "PORTAL",
]


def request_json(path, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(BASE_URL + path, data=data)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=3) as response:
        return json.load(response)


def reset_remote_map():
    try:
        request_json("/_remote_map/reset", {})
    except (OSError, urllib.error.URLError):
        pass


def main():
    try:
        request_json("/_remote_map/reset", {})
        request_json("/_remote_map/activate", {})
    except (OSError, urllib.error.URLError) as error:
        print(f"Harness is unavailable: {error}", file=sys.stderr)
        return 1

    atexit.register(reset_remote_map)
    signal.signal(signal.SIGTERM, lambda _signum, _frame: sys.exit(143))

    completed = set()
    try:
        completed = {entry["label"] for entry in json.loads(RESULTS_FILE.read_text())}
    except (OSError, ValueError, KeyError, TypeError):
        pass

    print("REMOTE-MAP-007: continuous one-button calibration", flush=True)
    print("Open Vivo Play. Waiting for the TV page-ready handshake...", flush=True)

    while request_json("/remote-map/state").get("status") != "ready":
        time.sleep(0.2)
    print("TV calibration page is ready; button capture can begin.", flush=True)

    for index, label in enumerate(BUTTONS, 1):
        if label in completed:
            print(f"[{index:02}/{len(BUTTONS)}] {label}: already captured", flush=True)
            continue
        state = request_json("/_remote_map/arm", {"label": label})
        if state.get("status") != "armed":
            print(f"  failed to arm: {state}", file=sys.stderr)
            return 1
        print(f"[{index:02}/{len(BUTTONS)}] TV armed for {label}; press {label} once.", flush=True)

        while True:
            time.sleep(0.2)
            state = request_json("/remote-map/state")
            if state.get("status") == "captured" and state.get("label") == label:
                print(f"  captured {state['code']} ({state['hex']})", flush=True)
                time.sleep(1.5)
                break

    reset_remote_map()
    print("Calibration finished. Results: captures/remote-map-007.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
