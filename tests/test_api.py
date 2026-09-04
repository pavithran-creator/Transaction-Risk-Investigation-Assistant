"""
Integration tests for the upload API endpoint (POST /api/upload).
"""

import pathlib

import pytest
from httpx import AsyncClient, ASGITransport

from app import app

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def anyio_backend():
    return "asyncio"


from src.analytics.state import clear_current_dataset


@pytest.fixture(autouse=True)
def reset_in_memory_state():
    """Ensure in-memory state is cleared before each test."""
    clear_current_dataset()
    yield
    clear_current_dataset()


@pytest.mark.anyio
async def test_root_still_works():
    """GET / must continue returning the running message."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["message"] == "PS06 Transaction Risk Investigation Assistant is running"


@pytest.mark.anyio
async def test_get_transactions_before_upload():
    """GET /api/transactions before uploading a dataset returns status empty."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/transactions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "empty"
    assert body["transaction_count"] == 0
    assert body["transactions"] == []


@pytest.mark.anyio
async def test_upload_single_customer_valid_csv():
    """POST /api/upload with a single-customer valid CSV succeeds and loads transactions."""
    csv_bytes = (FIXTURES / "valid_single_customer.csv").read_bytes()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload_resp = await client.post(
            "/api/upload",
            files={"file": ("valid_single_customer.csv", csv_bytes, "text/csv")},
        )
        assert upload_resp.status_code == 200
        assert upload_resp.json()["valid"] is True

        get_resp = await client.get("/api/transactions")
        assert get_resp.status_code == 200
        get_body = get_resp.json()
        assert get_body["status"] == "loaded"
        assert get_body["customer_id"] == "CUST001"
        assert get_body["transaction_count"] == 3
        assert len(get_body["transactions"]) == 3
        # Check no risk-related fields are exposed
        for txn in get_body["transactions"]:
            assert "risk_score" not in txn
            assert "fraud_probability" not in txn


@pytest.mark.anyio
async def test_upload_multiple_customers_rejected():
    """POST /api/upload with multiple customers returns 422 MULTIPLE_CUSTOMERS_NOT_ALLOWED."""
    csv_bytes = (FIXTURES / "valid.csv").read_bytes()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/upload",
            files={"file": ("valid.csv", csv_bytes, "text/csv")},
        )
    assert resp.status_code == 422
    body = resp.json()
    assert body["valid"] is False
    assert any("MULTIPLE_CUSTOMERS_NOT_ALLOWED" in err for err in body["errors"])


@pytest.mark.anyio
async def test_upload_missing_column():
    """POST /api/upload with a CSV missing a required column returns 422."""
    csv_bytes = (FIXTURES / "missing_column.csv").read_bytes()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/upload",
            files={"file": ("missing_column.csv", csv_bytes, "text/csv")},
        )
    assert resp.status_code == 422
    body = resp.json()
    assert body["valid"] is False


@pytest.mark.anyio
async def test_upload_empty_file():
    """POST /api/upload with empty bytes returns an error."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/upload",
            files={"file": ("empty.csv", b"", "text/csv")},
        )
    assert resp.status_code == 422
    body = resp.json()
    assert body["valid"] is False


@pytest.mark.anyio
async def test_get_baseline_before_upload():
    """GET /api/baseline before uploading returns status empty."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/baseline")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "empty"
    assert body["baseline"] is None


@pytest.mark.anyio
async def test_get_baseline_after_upload():
    """GET /api/baseline after uploading returns calculated customer baseline profile."""
    csv_bytes = (FIXTURES / "valid_single_customer.csv").read_bytes()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload_resp = await client.post(
            "/api/upload",
            files={"file": ("valid_single_customer.csv", csv_bytes, "text/csv")},
        )
        assert upload_resp.status_code == 200

        base_resp = await client.get("/api/baseline")
        assert base_resp.status_code == 200
        body = base_resp.json()
        assert body["status"] == "calculated"
        assert body["customer_id"] == "CUST001"
        assert body["transaction_count"] == 3

        baseline_data = body["baseline"]
        assert baseline_data["amount_statistics"]["mean"] > 0
        assert "NEFT" in baseline_data["channel_usage"]
        assert "ABC Corp" in baseline_data["payee_usage"]
        # Ensure no risk fields present in baseline
        assert "risk_score" not in baseline_data
        assert "fraud_probability" not in baseline_data


@pytest.mark.anyio
async def test_get_rules_before_upload():
    """GET /api/rules before uploading returns status empty."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/rules")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "empty"
    assert body["evaluated_at_transaction_count"] == 0
    assert body["rules"] == []


@pytest.mark.anyio
async def test_get_rules_after_upload():
    """GET /api/rules after uploading returns evaluated risk rules results."""
    csv_bytes = (FIXTURES / "valid_single_customer.csv").read_bytes()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload_resp = await client.post(
            "/api/upload",
            files={"file": ("valid_single_customer.csv", csv_bytes, "text/csv")},
        )
        assert upload_resp.status_code == 200

        rules_resp = await client.get("/api/rules")
        assert rules_resp.status_code == 200
        body = rules_resp.json()
        assert body["status"] == "evaluated"
        assert body["customer_id"] == "CUST001"
        assert body["evaluated_at_transaction_count"] == 3

        rules = body["rules"]
        assert len(rules) == 4
        rule_ids = [r["rule_id"] for r in rules]
        assert rule_ids == ["R01", "R02", "R03", "R04"]

        for rule in rules:
            assert "triggered" in rule
            assert "evidence" in rule
            assert "risk_score" not in rule
            assert "fraud_probability" not in rule



