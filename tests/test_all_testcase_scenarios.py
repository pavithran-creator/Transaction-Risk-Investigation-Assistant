"""
Automated Test Suite for TestCase and TESTCASE2 CSV Scenarios.

Iterates over all CSV files in both TestCase and TESTCASE2 directories and validates that:
1. CSV upload (/api/upload) succeeds.
2. Transactions (/api/transactions) returns loaded data matching transaction count.
3. Baseline (/api/baseline) returns valid customer baseline statistics.
4. Rules (/api/rules) evaluates R01-R04 without errors.
5. Attention (/api/attention) returns valid attention assessments.
6. Report (/api/report) generates complete investigation reports.
7. Specific rule triggers (including R04 for pattern deviation testcases) are validated.
"""

import glob
import os
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def get_testcase_csv_files():
    """Retrieve absolute paths for all CSV files in TestCase, TESTCASE2, and TESTCASE3 folders."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    testcase_dir = os.path.join(base_dir, "TestCase")
    testcase2_dir = os.path.join(base_dir, "TESTCASE2")
    testcase3_dir = os.path.join(base_dir, "TESTCASE3")

    csv_paths = (
        sorted(glob.glob(os.path.join(testcase_dir, "*.csv")))
        + sorted(glob.glob(os.path.join(testcase2_dir, "*.csv")))
        + sorted(glob.glob(os.path.join(testcase3_dir, "*.csv")))
    )
    return csv_paths


TESTCASE_CSVS = get_testcase_csv_files()


@pytest.mark.parametrize("csv_path", TESTCASE_CSVS, ids=lambda p: f"{os.path.basename(os.path.dirname(p))}/{os.path.basename(p)}")
def test_testcase_scenario_execution(csv_path):
    """Test end-to-end processing of each CSV file in TestCase, TESTCASE2, and TESTCASE3 folders."""
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
    rule_map = {r["rule_id"]: r for r in rules}

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

    # Scenario-specific expectations for TestCase, TESTCASE2, and TESTCASE3
    if "R01_unusually_large_transfer" in filename and "negative" not in filename and "multiple" not in filename:
        assert rule_map["R01"]["triggered"] is True, f"R01 should trigger for {filename}"

    elif "test_02_r01_large_transfer" in filename or "test_12_r01_extreme_large_transfer" in filename:
        assert rule_map["R01"]["triggered"] is True, f"R01 should trigger for {filename}"

    elif "R02_new_payee_burst" in filename and "negative" not in filename:
        assert rule_map["R02"]["triggered"] is True, f"R02 should trigger for {filename}"

    elif "test_03_r02_new_payee_burst" in filename or "test_13_r02_rapid_payee_burst" in filename:
        assert rule_map["R02"]["triggered"] is True, f"R02 should trigger for {filename}"

    elif "R03_odd_hours_activity" in filename or "test_04_r03_odd_hours" in filename or "test_14_r03_late_night_odd_hours" in filename:
        assert rule_map["R03"]["triggered"] is True, f"R03 should trigger for {filename}"

    elif (
        "scenario_R04_established_pattern_deviation" in filename
        or "test_05_r04_pattern_deviation" in filename
        or "test_11_r04_unobserved_channel_high_amount" in filename
    ):
        assert rule_map["R04"]["triggered"] is True, f"R04 should trigger for {filename}"

    elif "test_09_boundary_conditions" in filename:
        assert rule_map["R04"]["triggered"] is True, f"R04 should trigger for boundary conditions in {filename}"
        assert "T09-0045" in rule_map["R04"]["transaction_ids"]

    elif "test_10_full_demo" in filename or "test_15_all_4_rules_high_attention" in filename:
        assert all(r["triggered"] for r in rules), f"All rules R01-R04 should trigger for {filename}"
        assert att_data["attention_level"] == "HIGH_ATTENTION"

    elif "no_immediate_concern" in filename and "TESTCASE2" not in csv_path:
        assert att_data["attention_level"] == "NO_IMMEDIATE_CONCERN"
        assert all(not r["triggered"] for r in rules)

    elif "high_attention" in filename or "test_06_multiple_rules" in filename:
        assert att_data["attention_level"] in ("HIGH_ATTENTION", "ATTENTION_RECOMMENDED")

    elif "attention_recommended" in filename:
        assert att_data["attention_level"] in ("ATTENTION_RECOMMENDED", "HIGH_ATTENTION")

    elif "contextual_review" in filename:
        assert att_data["attention_level"] in ("CONTEXTUAL_REVIEW", "ATTENTION_RECOMMENDED")
