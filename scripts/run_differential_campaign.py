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

def evaluate_case(case_data, timeout_seconds=45):
    case_id = case_data["case_id"]
    endpoint = case_data["endpoint"]
    expected_marker = case_data.get("expected_marker")
    
    print(f"\n{'='*70}")
    print(f" EXECUTING CASE: {case_id}")
    print(f" Target Endpoint: {endpoint}")
    print(f" Provenance:      {case_data['provenance']}")
    print(f" Description:     {case_data['description']}")
    if expected_marker:
        print(f" Expected Marker: {expected_marker}")
    print(f"{'='*70}")

    offset = get_log_offset()
    if not activate_case_on_harness(case_data):
        return {"case_id": case_id, "status": "ERROR_HARNESS_UNREACHABLE"}

    print(f"[*] Case {case_id} active on harness. Monitoring receiver for up to {timeout_seconds}s...")

    start_time = time.time()
    response_delivered = False
    marker_hit = False
    script_executed = False
    delivered_tx = None

    while time.time() - start_time < timeout_seconds:
        txs, offset = read_new_transactions(offset)
        for tx in txs:
            src = tx.get("source")
            path = tx.get("path", "")
            tx_case = tx.get("case_id")
            
            # We ONLY credit RECEIVER_HW
            if src == "RECEIVER_HW":
                # Check if target endpoint was exercised
                if path.startswith(endpoint.split("?")[0]):
                    response_delivered = True
                    delivered_tx = tx
                    print(f"  [+] RECEIVER EXERCISED {endpoint}! Client: {tx.get('client')}, Status: {tx.get('response_status')}")

                # Check if marker URL was fetched
                if expected_marker and path == expected_marker:
                    marker_hit = True
                    print(f"  [*** EVIDENCE HIT ***] Marker {expected_marker} fetched by RECEIVER_HW!")

                # Check if script callback was executed
                if path.startswith("/report/script_exec"):
                    script_executed = True
                    print(f"  [*** CRITICAL HIT ***] Script callback executed by RECEIVER_HW!")

        if response_delivered and (marker_hit or not expected_marker or time.time() - start_time > 15):
            # If marker was hit, or if baseline (no marker), or if sufficient wait after delivery
            break
        time.sleep(1.0)

    # Determine verdict
    if not response_delivered:
        verdict = "UNTESTED (STB made no request to this endpoint)"
    elif marker_hit and script_executed:
        verdict = "SCRIPT_EXECUTION_DEMONSTRATED"
    elif marker_hit:
        verdict = "MARKER_FETCHED (Candidate Accepted)"
    elif response_delivered and not expected_marker:
        verdict = "BASELINE_DELIVERED (Accepted without error)"
    else:
        verdict = "NEGATIVE (Response delivered, candidate NOT followed)"

    result = {
        "case_id": case_id,
        "endpoint": endpoint,
        "provenance": case_data["provenance"],
        "delivered": response_delivered,
        "marker_expected": expected_marker,
        "marker_hit": marker_hit,
        "script_executed": script_executed,
        "verdict": verdict,
        "tx_details": delivered_tx
    }
    return result

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        cid = sys.argv[2]
        matching = [c for c in CASES if c["case_id"] == cid]
        if not matching:
            print(f"Case {cid} not found.")
            sys.exit(1)
        res = evaluate_case(matching[0], timeout_seconds=int(sys.argv[3]) if len(sys.argv) > 3 else 30)
        print(json.dumps(res, indent=2))
        return

    print("=" * 70)
    print("   MERO-STB-LAB: AUTOMATED DIFFERENTIAL EXPERIMENT CAMPAIGN    ")
    print(f"   Total Cases: {len(CASES)} | Mode: Strict Receiver Evidence")
    print("=" * 70)

    results = []
    for c in CASES:
        r = evaluate_case(c, timeout_seconds=20)
        results.append(r)
        # Always restore baseline between tests
        activate_case_on_harness(CASES[0])
        time.sleep(2)

    print("\n" + "=" * 70)
    print("             DIFFERENTIAL CAMPAIGN RESULTS SUMMARY             ")
    print("=" * 70)
    print(f"{'Case ID':<26} | {'Provenance':<30} | {'Marker Hit':<10} | {'Verdict'}")
    print("-" * 90)
    for r in results:
        print(f"{r['case_id']:<26} | {r['provenance'][:30]:<30} | {str(r['marker_hit']):<10} | {r['verdict']}")

    with open(EVIDENCE_TABLE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] Raw results written to {EVIDENCE_TABLE}")

if __name__ == "__main__":
    main()
