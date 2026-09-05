"""
Automated Test Suite for TestCase CSV Scenarios.

Iterates over all CSV files in the TestCase directory and validates that:
1. CSV upload (/api/upload) succeeds.
2. Transactions (/api/transactions) returns loaded data matching transaction count.
3. Baseline (/api/baseline) returns valid customer baseline statistics.
4. Rules (/api/rules) evaluates R01-R04 without errors.
5. Attention (/api/attention) returns valid attention assessments.
6. Report (/api/report) generates complete investigation reports.
"""

import glob
import os
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def get_testcase_csv_files():
    """Retrieve absolute paths for all CSV files in TestCase folder."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    testcase_dir = os.path.join(base_dir, "TestCase")
    csv_paths = sorted(glob.glob(os.path.join(testcase_dir, "*.csv")))
    return csv_paths


TESTCASE_CSVS = get_testcase_csv_files()


@pytest.mark.parametrize("csv_path", TESTCASE_CSVS, ids=lambda p: os.path.basename(p))
def test_testcase_scenario_execution(csv_path):
    """Test end-to-end processing of each CSV file in the TestCase folder."""
    filename = os.path.basename(csv_path)

    # Read CSV file bytes
    with open(csv_path, "rb") as f:
        content = f.read()

    # 1. Upload CSV to /api/upload
    upload_resp = client.post(
        "/api/upload",
        files={"file": (filename, content, "text/csv")}
    )
    assert upload_resp.status_code == 200, f"Upload failed for {filename}: {upload_resp.text}"
    upload_data = upload_resp.json()
    assert upload_data.get("valid") is True, f"CSV invalid for {filename}: {upload_data.get('errors')}"
    assert upload_data.get("transaction_count", 0) > 0

    # 2. GET /api/transactions
    tx_resp = client.get("/api/transactions")
    assert tx_resp.status_code == 200
    tx_data = tx_resp.json()
    assert len(tx_data.get("transactions", [])) == upload_data.get("transaction_count")

    # 3. GET /api/baseline
    baseline_resp = client.get("/api/baseline")
    assert baseline_resp.status_code == 200
    baseline = baseline_resp.json().get("baseline", {})
    assert baseline.get("transaction_count") == upload_data.get("transaction_count")
    assert "amount_statistics" in baseline

    # 4. GET /api/rules
    rules_resp = client.get("/api/rules")
    assert rules_resp.status_code == 200
    rules_data = rules_resp.json()
    rules = rules_data.get("rules", [])
    assert len(rules) == 4
    rule_ids = {r["rule_id"] for r in rules}
    assert rule_ids == {"R01", "R02", "R03", "R04"}

    # 5. GET /api/attention
    att_resp = client.get("/api/attention")
    assert att_resp.status_code == 200
    att_data = att_resp.json().get("assessment", {})
    assert "attention_level" in att_data

    # 6. GET /api/report
    report_resp = client.get("/api/report")
    assert report_resp.status_code == 200
    report_data = report_resp.json().get("report", {})
    assert "first_finding" in report_data
    assert "transactions_requiring_review" in report_data
    assert "safety_statement" in report_data

    # Scenario-specific expectations
    if "R01_unusually_large_transfer" in filename and "negative" not in filename and "multiple" not in filename:
        r01 = next(r for r in rules if r["rule_id"] == "R01")
        assert r01["triggered"] is True, f"R01 should trigger for {filename}"

    elif "R02_new_payee_burst" in filename and "negative" not in filename:
        r02 = next(r for r in rules if r["rule_id"] == "R02")
        assert r02["triggered"] is True, f"R02 should trigger for {filename}"

    elif "R03_odd_hours_activity" in filename:
        r03 = next(r for r in rules if r["rule_id"] == "R03")
        assert r03["triggered"] is True, f"R03 should trigger for {filename}"

    elif "no_immediate_concern" in filename:
        assert att_data["attention_level"] == "NO_IMMEDIATE_CONCERN"
        assert all(not r["triggered"] for r in rules)

    elif "high_attention" in filename:
        assert att_data["attention_level"] == "HIGH_ATTENTION"

    elif "attention_recommended" in filename:
        assert att_data["attention_level"] in ("ATTENTION_RECOMMENDED", "HIGH_ATTENTION")

    elif "contextual_review" in filename:
        assert att_data["attention_level"] in ("CONTEXTUAL_REVIEW", "ATTENTION_RECOMMENDED")
