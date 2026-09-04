"""
Integration and Regression Test Suite for Phase 6 (tests/test_phase6_regression.py).

Verifies end-to-end pipeline progression across Phase 1 to Phase 6 endpoints:
GET / -> POST /api/upload -> GET /api/transactions -> GET /api/baseline -> GET /api/rules -> GET /api/attention
"""

import pathlib
import pytest
from httpx import ASGITransport, AsyncClient
from app import app
from src.analytics.state import clear_current_dataset

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def reset_state():
    clear_current_dataset()
    yield
    clear_current_dataset()


@pytest.mark.anyio
async def test_full_phase1_to_phase6_pipeline_regression():
    """Verify complete end-to-end integration across all 6 phases."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Phase 1: Health check
        root_resp = await client.get("/")
        assert root_resp.status_code == 200
        assert root_resp.json()["message"] == "PS06 Transaction Risk Investigation Assistant is running"

        # Pre-upload checks (Phases 3 - 6)
        tx_empty = await client.get("/api/transactions")
        assert tx_empty.json()["status"] == "empty"

        base_empty = await client.get("/api/baseline")
        assert base_empty.json()["status"] == "empty"

        rules_empty = await client.get("/api/rules")
        assert rules_empty.json()["status"] == "empty"

        att_empty = await client.get("/api/attention")
        assert att_empty.json()["status"] == "empty"
        assert att_empty.json()["assessment"]["attention_level"] == "INSUFFICIENT_EVIDENCE"

        # Phase 2 & 3: Upload valid dataset
        csv_bytes = (FIXTURES / "valid_single_customer.csv").read_bytes()
        upload_resp = await client.post(
            "/api/upload",
            files={"file": ("valid_single_customer.csv", csv_bytes, "text/csv")},
        )
        assert upload_resp.status_code == 200
        assert upload_resp.json()["valid"] is True

        # Phase 3 retrieval
        tx_loaded = await client.get("/api/transactions")
        assert tx_loaded.status_code == 200
        assert tx_loaded.json()["status"] == "loaded"
        assert tx_loaded.json()["customer_id"] == "CUST001"

        # Phase 4 baseline retrieval
        base_calc = await client.get("/api/baseline")
        assert base_calc.status_code == 200
        assert base_calc.json()["status"] == "calculated"

        # Phase 5 deterministic rules retrieval
        rules_eval = await client.get("/api/rules")
        assert rules_eval.status_code == 200
        assert rules_eval.json()["status"] == "evaluated"
        assert len(rules_eval.json()["rules"]) == 4

        # Phase 6 attention assessment retrieval
        att_eval = await client.get("/api/attention")
        assert att_eval.status_code == 200
        assert att_eval.json()["status"] == "evaluated"
        assessment = att_eval.json()["assessment"]
        assert "attention_level" in assessment
        assert "attention_label" in assessment
        assert "safety_statement" in assessment
        assert "does not establish that fraud occurred" in assessment["safety_statement"]
