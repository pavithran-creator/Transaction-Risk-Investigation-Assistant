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


@pytest.mark.anyio
async def test_root_still_works():
    """GET / must continue returning the running message."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["message"] == "PS06 Transaction Risk Investigation Assistant is running"


@pytest.mark.anyio
async def test_upload_valid_csv():
    """POST /api/upload with a valid CSV returns 200 and valid=True."""
    csv_bytes = (FIXTURES / "valid.csv").read_bytes()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/upload",
            files={"file": ("valid.csv", csv_bytes, "text/csv")},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["valid"] is True
    assert body["transaction_count"] == 7


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
async def test_upload_no_file():
    """POST /api/upload without a file returns 422 (FastAPI validation)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/upload")
    assert resp.status_code == 422
