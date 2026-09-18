#!/usr/bin/env python3
"""
MERO-STB-LAB: Differential Experiment Campaign Runner
Automates the execution of up to 12 distinct differential test cases against
the set-top box, monitoring experiment_transactions.jsonl for receiver-originated evidence.
"""

import os
import sys
import time
import json
import hashlib
import urllib.request
import urllib.parse

HARNESS_URL = "http://127.0.0.1:8080/_harness/set_case"
JSONL_LOG = "/home/zacmero/projects/mero-stb-lab/captures/experiment_transactions.jsonl"
EVIDENCE_TABLE = "/home/zacmero/projects/mero-stb-lab/captures/differential_results.json"

# Definition of the 12 Bounded Test Cases
CASES = [
    {
        "case_id": "CASE-00-BASELINE",
        "description": "Repeatable baseline - minimal JSON, no navigation fields, no redirects",
        "endpoint": "/bussola/redirect",
        "provenance": "Control baseline",
        "bussola_status": 200,
        "bussola_headers": {"Content-Type": "application/json; charset=utf-8"},
        "bussola_body": json.dumps({"status": "ok", "code": 0}),
        "appconfig_status": 200,
        "appconfig_headers": {"Content-Type": "application/json; charset=utf-8"},
        "appconfig_body": json.dumps({"status": "ok", "code": 0}),
        "expected_marker": None
    },
    {
        "case_id": "CASE-01-BUSSOLA-URL",
        "description": "Candidate key: url (top-level string in 200 JSON)",
        "endpoint": "/bussola/redirect",
        "provenance": "Guess (REST convention)",
        "bussola_status": 200,
        "bussola_headers": {"Content-Type": "application/json; charset=utf-8"},
        "bussola_body": json.dumps({"status": "ok", "code": 0, "url": "http://191.32.31.251/marker/bussola_c01_url"}),
        "expected_marker": "/marker/bussola_c01_url"
    },
    {
        "case_id": "CASE-02-BUSSOLA-PORTALURL",
        "description": "Candidate key: portalUrl (top-level string in 200 JSON)",
        "endpoint": "/bussola/redirect",
        "provenance": "Supported by Ekioh ecosystem artifacts",
        "bussola_status": 200,
        "bussola_headers": {"Content-Type": "application/json; charset=utf-8"},
        "bussola_body": json.dumps({"status": "ok", "code": 0, "portalUrl": "http://191.32.31.251/marker/bussola_c02_portalurl"}),
        "expected_marker": "/marker/bussola_c02_portalurl"
    },
    {
        "case_id": "CASE-03-BUSSOLA-REDIRECTURL",
        "description": "Candidate key: redirectUrl (top-level string in 200 JSON)",
        "endpoint": "/bussola/redirect",
        "provenance": "Guess (Mirada camelCase convention)",
        "bussola_status": 200,
        "bussola_headers": {"Content-Type": "application/json; charset=utf-8"},
        "bussola_body": json.dumps({"status": "ok", "code": 0, "redirectUrl": "http://191.32.31.251/marker/bussola_c03_redirecturl"}),
        "expected_marker": "/marker/bussola_c03_redirecturl"
    },
    {
        "case_id": "CASE-04-BUSSOLA-TARGET",
        "description": "Candidate key: target (top-level string in 200 JSON)",
        "endpoint": "/bussola/redirect",
        "provenance": "Guess (SVG/HTML navigation target)",
        "bussola_status": 200,
        "bussola_headers": {"Content-Type": "application/json; charset=utf-8"},
        "bussola_body": json.dumps({"status": "ok", "code": 0, "target": "http://191.32.31.251/marker/bussola_c04_target"}),
        "expected_marker": "/marker/bussola_c04_target"
    },
    {
        "case_id": "CASE-05-BUSSOLA-RESULT-URL",
        "description": "Candidate structure: result.url (nested object in 200 JSON)",
        "endpoint": "/bussola/redirect",
        "provenance": "Supported by Mirada bussola schema references",
        "bussola_status": 200,
        "bussola_headers": {"Content-Type": "application/json; charset=utf-8"},
        "bussola_body": json.dumps({"status": "ok", "code": 0, "result": {"status": "ok", "url": "http://191.32.31.251/marker/bussola_c05_resulturl"}}),
        "expected_marker": "/marker/bussola_c05_resulturl"
    },
    {
        "case_id": "CASE-06-BUSSOLA-DATA-URL",
        "description": "Candidate structure: data.url (nested object in 200 JSON)",
        "endpoint": "/bussola/redirect",
        "provenance": "Guess (JSON-RPC wrapper convention)",
        "bussola_status": 200,
        "bussola_headers": {"Content-Type": "application/json; charset=utf-8"},
        "bussola_body": json.dumps({"status": "ok", "code": 0, "data": {"url": "http://191.32.31.251/marker/bussola_c06_dataurl"}}),
        "expected_marker": "/marker/bussola_c06_dataurl"
    },
    {
        "case_id": "CASE-07-BUSSOLA-ACTION-OPEN",
        "description": "Candidate structure: action:open + url (Mirada command in 200 JSON)",
        "endpoint": "/bussola/redirect",
        "provenance": "Supported by Mirada middleware action specification",
        "bussola_status": 200,
        "bussola_headers": {"Content-Type": "application/json; charset=utf-8"},
        "bussola_body": json.dumps({"status": "ok", "code": 0, "action": "open", "url": "http://191.32.31.251/marker/bussola_c07_action"}),
        "expected_marker": "/marker/bussola_c07_action"
    },
    {
        "case_id": "CASE-08-BUSSOLA-VODURL",
        "description": "Candidate key: vodUrl (query-informed parameter matching type=vod)",
        "endpoint": "/bussola/redirect",
        "provenance": "Supported by observed query parameter type=vod",
        "bussola_status": 200,
        "bussola_headers": {"Content-Type": "application/json; charset=utf-8"},
        "bussola_body": json.dumps({"status": "ok", "code": 0, "vodUrl": "http://191.32.31.251/marker/bussola_c08_vodurl"}),
        "expected_marker": "/marker/bussola_c08_vodurl"
    },
    {
        "case_id": "CASE-09-BUSSOLA-ISOLATED-302",
        "description": "Isolated HTTP 302 redirect test with Location header",
        "endpoint": "/bussola/redirect",
        "provenance": "HTTP-layer redirection baseline",
        "bussola_status": 302,
        "bussola_headers": {
            "Content-Type": "application/json; charset=utf-8",
            "Location": "http://191.32.31.251/marker/bussola_c09_302"
        },
        "bussola_body": json.dumps({"status": "redirect"}),
        "expected_marker": "/marker/bussola_c09_302"
    },
    {
        "case_id": "CASE-10-APPCONFIG-PORTALURL",
        "description": "Candidate key: portalUrl in appConfigFit.json",
        "endpoint": "/tv-config/appConfigFit.json",
        "provenance": "Supported by Sagemcom application config artifacts",
        "appconfig_status": 200,
        "appconfig_headers": {"Content-Type": "application/json; charset=utf-8"},
        "appconfig_body": json.dumps({"status": "ok", "code": 0, "portalUrl": "http://191.32.31.251/marker/cfg_c10_portalurl"}),
        "expected_marker": "/marker/cfg_c10_portalurl"
    },
    {
        "case_id": "CASE-11-APPCONFIG-STARTURL",
        "description": "Candidate key: startUrl in appConfigFit.json",
        "endpoint": "/tv-config/appConfigFit.json",
        "provenance": "Supported by Sagemcom firmware strings",
        "appconfig_status": 200,
        "appconfig_headers": {"Content-Type": "application/json; charset=utf-8"},
        "appconfig_body": json.dumps({"status": "ok", "code": 0, "startUrl": "http://191.32.31.251/marker/cfg_c11_starturl"}),
        "expected_marker": "/marker/cfg_c11_starturl"
    }
]

def activate_case_on_harness(case_data):
    req = urllib.request.Request(HARNESS_URL, data=json.dumps(case_data).encode("utf-8"), method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[-] Failed to set case on harness: {e}")
        return False

def restore_baseline():
    return activate_case_on_harness(CASES[0])

def get_log_offset():
    if not os.path.exists(JSONL_LOG):
        return 0
    return os.path.getsize(JSONL_LOG)

def read_new_transactions(offset):
    if not os.path.exists(JSONL_LOG):
        return [], 0
    records = []
    with open(JSONL_LOG, "r", encoding="utf-8") as f:
        f.seek(offset)
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
        new_offset = f.tell()
    return records, new_offset

def evaluate_case(case_data, wait_timeout=60, observe_timeout=30, prompt=None):
    case_data = dict(case_data)
    case_id = case_data["case_id"]
    run_id = f"{case_id}-{time.time_ns()}"
    case_data["run_id"] = run_id
    endpoint = case_data["endpoint"]
    expected_marker = case_data.get("expected_marker")
    
    # Calculate expected response body SHA-256
    if endpoint == "/bussola/redirect":
        exp_body_str = case_data.get("bussola_body", "")
    else:
        exp_body_str = case_data.get("appconfig_body", "")
    expected_resp_sha256 = hashlib.sha256(exp_body_str.encode("utf-8")).hexdigest()

    target_host = "191.32.31.251"
    target_method = "GET"
    target_path_prefix = endpoint.split("?")[0]

    print(f"\n{'='*70}")
    print(f" EXECUTING CASE: {case_id}")
    print(f" Target Endpoint: {target_method} {target_host}{target_path_prefix}")
    print(f" Expected SHA256: {expected_resp_sha256[:16]}...")
    print(f" Provenance:      {case_data['provenance']}")
    print(f" Description:     {case_data['description']}")
    if expected_marker:
        print(f" Expected Marker: {expected_marker}")
    print(f"{'='*70}")

    offset = get_log_offset()
    if not activate_case_on_harness(case_data):
        return {
            "case_id": case_id,
            "run_id": run_id,
            "endpoint": endpoint,
            "provenance": case_data["provenance"],
            "delivered": False,
            "marker_expected": expected_marker,
            "marker_hit": False,
            "marker_type": None,
            "script_executed": False,
            "verdict": "ERROR",
            "status": "ERROR_HARNESS_UNREACHABLE",
            "tx_details": None,
        }

    if prompt:
        print(f"READY FOR {case_id} (run_id={run_id})")
        input(f"{prompt}\nPress Enter only after completing that action: ")

    # Phase 1: WAITING_FOR_REQUEST (up to wait_timeout seconds)
    print(f"[*] State: WAITING_FOR_REQUEST (up to {wait_timeout}s)...")
    wait_start = time.time()
    response_delivered = False
    delivered_tx = None

    while time.time() - wait_start < wait_timeout:
        txs, offset = read_new_transactions(offset)
        for tx in txs:
            if tx.get("source") != "RECEIVER_HW":
                continue
            
            # Require exact target Host + method + path prefix
            tx_path = urllib.parse.urlsplit(tx.get("path", "")).path
            if (tx.get("method") == target_method and 
                tx.get("host") == target_host and 
                tx_path == target_path_prefix):
                
                # Require matching case_id and expected response body SHA-256
                tx_case = tx.get("case_id")
                tx_sha = tx.get("response_body_sha256")
                
                if (tx_case == case_id and tx.get("run_id") == run_id and
                        tx_sha == expected_resp_sha256):
                    response_delivered = True
                    delivered_tx = tx
                    print(f"\n  [+] MATCHING REQUEST DELIVERED from {tx.get('client')}:")
                    print(f"      Path:        {tx.get('path')}")
                    print(f"      Status:      HTTP {tx.get('response_status')}")
                    print(f"      Case ID:     {tx_case}")
                    print(f"      Run ID:      {run_id}")
                    print(f"      Timestamp:   {tx.get('timestamp')}")
                    print(f"      Body SHA256: {tx_sha} (MATCHED)")
                    break
                else:
                    print(f"  [-] Receiver request matched path but case/SHA mismatch: case={tx_case}, sha={tx_sha}")

        if response_delivered:
            break
        time.sleep(0.5)

    if not response_delivered:
        print(f"[-] WAITING_FOR_REQUEST timed out ({wait_timeout}s). No matching request received.")
        return {
            "case_id": case_id,
            "run_id": run_id,
            "endpoint": endpoint,
            "provenance": case_data["provenance"],
            "delivered": False,
            "marker_expected": expected_marker,
            "marker_hit": False,
            "marker_type": None,
            "script_executed": False,
            "verdict": "UNTESTED",
            "tx_details": None
        }

    # Phase 2: OBSERVING_AFTER_RESPONSE (allow full observe_timeout seconds)
    print(f"\n[*] State: OBSERVING_AFTER_RESPONSE. Allowing full {observe_timeout}s for downstream behavior...")
    obs_start = time.time()
    marker_hit = False
    marker_type = None
    script_executed = False
    marker_tx = None

    is_302_case = (case_data.get("bussola_status") == 302 or case_id.endswith("-302"))

    while time.time() - obs_start < observe_timeout:
        txs, offset = read_new_transactions(offset)
        for tx in txs:
            if tx.get("source") != "RECEIVER_HW":
                continue

            path = urllib.parse.urlsplit(tx.get("path", "")).path
            # Attribute marker to correct case
            if (expected_marker and path == expected_marker and
                    tx.get("case_id") == case_id and tx.get("run_id") == run_id):
                marker_hit = True
                marker_tx = tx
                marker_type = "HTTP_302" if is_302_case else "JSON_FIELD"
                print(f"  [*** EVIDENCE HIT ***] Marker {expected_marker} ({marker_type}) fetched by RECEIVER_HW from {tx.get('client')}!")
                print(f"      Timestamp: {tx.get('timestamp')} | Run ID: {run_id}")

            if (path == "/report/script_exec" and tx.get("case_id") == case_id and
                    tx.get("run_id") == run_id):
                script_executed = True
                print(f"  [*** CRITICAL HIT ***] Script callback executed by RECEIVER_HW!")

        time.sleep(0.5)

    # Determine verdict
    if script_executed:
        verdict = "SCRIPT_EXECUTION_DEMONSTRATED"
    elif marker_hit:
        verdict = f"MARKER_FETCHED_{marker_type}"
    elif expected_marker is None:
        verdict = "DELIVERED"
    else:
        verdict = "NEGATIVE (Response delivered, candidate NOT followed)"

    print(f"[*] Evaluation completed: Verdict = {verdict}")

    result = {
        "case_id": case_id,
        "run_id": run_id,
        "endpoint": endpoint,
        "provenance": case_data["provenance"],
        "delivered": True,
        "marker_expected": expected_marker,
        "marker_hit": marker_hit,
        "marker_type": marker_type,
        "script_executed": script_executed,
        "verdict": verdict,
        "tx_details": delivered_tx,
        "marker_details": marker_tx
    }
    return result

def main():
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--single":
            if len(sys.argv) < 3:
                print("--single requires CASE_ID", file=sys.stderr)
                sys.exit(2)
            cid = sys.argv[2]
            matching = [c for c in CASES if c["case_id"] == cid]
            if not matching:
                print(f"Case {cid} not found.")
                sys.exit(1)
            wait_t = int(sys.argv[3]) if len(sys.argv) > 3 else 60
            obs_t = int(sys.argv[4]) if len(sys.argv) > 4 else 30
            res = evaluate_case(matching[0], wait_timeout=wait_t, observe_timeout=obs_t)
            print("\n" + "=" * 70)
            print("SINGLE CASE RESULT:")
            print(json.dumps(res, indent=2))
            return

        if len(sys.argv) > 1 and sys.argv[1] != "--interactive-three":
            print("Usage: run_differential_campaign.py [--interactive-three | --single CASE_ID [WAIT [OBSERVE]]]", file=sys.stderr)
            sys.exit(2)

        sequence = [
            (CASES[0], "Open Vivo Play once."),
            (CASES[9], "Close and reopen Vivo Play."),
            (CASES[1], "Close and reopen Vivo Play."),
        ]
        print("MERO-STB-LAB: INTERACTIVE THREE-CASE SESSION")
        results = []
        for case_data, prompt in sequence:
            if not restore_baseline():
                print("[-] Could not restore baseline; stopping.", file=sys.stderr)
                break
            result = evaluate_case(case_data, wait_timeout=60, observe_timeout=30, prompt=prompt)
            results.append(result)
            if result["verdict"] in ("UNTESTED", "ERROR"):
                print("[!] Sequence stopped; no later case was activated.")
                break

        print("\n" + "=" * 70)
        print("             INTERACTIVE SESSION RESULTS SUMMARY              ")
        print("=" * 70)
        print(f"{'Case ID':<26} | {'Provenance':<30} | {'Marker Hit':<10} | {'Verdict'}")
        print("-" * 90)
        for r in results:
            print(f"{r['case_id']:<26} | {r['provenance'][:30]:<30} | {str(r['marker_hit']):<10} | {r['verdict']}")

        with open(EVIDENCE_TABLE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\n[+] Results written to {EVIDENCE_TABLE}")

    finally:
        print("\n[*] Restoring harness to CASE-00-BASELINE...")
        restore_baseline()

if __name__ == "__main__":
    main()
