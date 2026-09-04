from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import uvicorn

from src.analytics.csv_validator import validate_csv
from src.analytics.state import clear_current_dataset, get_current_dataset, set_current_dataset
from src.analytics.transaction_loader import load_dataset_from_csv_bytes
from src.models.transaction import MAX_UPLOAD_SIZE_BYTES, error_response

app = FastAPI(title="PS06 Transaction Risk Investigation Assistant")


@app.get("/")
def read_root():
    return {"message": "PS06 Transaction Risk Investigation Assistant is running"}


@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a transaction CSV for validation and in-memory loading.

    Accepts a CSV file, validates structure & transaction data,
    enforces single-customer constraint, and stores validated data in memory.

    **File size limit:** 10 MB
    """
    # --- Content-type sanity check ------------------------------------
    if file.content_type and file.content_type not in (
        "text/csv",
        "application/vnd.ms-excel",
        "application/octet-stream",
    ):
        clear_current_dataset()
        return JSONResponse(
            status_code=400,
            content={
                "valid": False,
                "errors": [
                    f"Unsupported file type: {file.content_type}. Please upload a CSV file."
                ],
            },
        )

    # --- Read file bytes with size protection -------------------------
    try:
        raw_bytes = await file.read()
    except Exception:
        clear_current_dataset()
        return JSONResponse(
            status_code=400,
            content={
                "valid": False,
                "errors": ["Unable to read the uploaded file."],
            },
        )

    if len(raw_bytes) > MAX_UPLOAD_SIZE_BYTES:
        clear_current_dataset()
        return JSONResponse(
            status_code=413,
            content={
                "valid": False,
                "errors": [
                    f"File size exceeds the maximum allowed limit of "
                    f"{MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
                ],
            },
        )

    # --- Phase 2 CSV Validation ---------------------------------------
    validation_res = validate_csv(raw_bytes)
    if not validation_res.get("valid", False):
        clear_current_dataset()
        return JSONResponse(status_code=422, content=validation_res)

    # --- Phase 3 Single-Customer & Dataset Loading -------------------
    dataset, errors = load_dataset_from_csv_bytes(raw_bytes, enforce_single_customer=True)
    if errors:
        clear_current_dataset()
        return JSONResponse(status_code=422, content=error_response(errors))

    set_current_dataset(dataset)
    return JSONResponse(status_code=200, content=validation_res)


@app.get("/api/transactions")
def get_transactions():
    """
    Retrieve currently loaded in-memory transaction history.

    Returns the chronological list of validated transactions for the active customer,
    or a status message if no dataset is loaded.
    """
    dataset = get_current_dataset()
    if not dataset or dataset.transaction_count == 0:
        return JSONResponse(
            status_code=200,
            content={
                "status": "empty",
                "message": "No transaction dataset currently loaded. Please upload a CSV first.",
                "transaction_count": 0,
                "customer_id": None,
                "transactions": [],
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "status": "loaded",
            "customer_id": dataset.customer_id,
            "transaction_count": dataset.transaction_count,
            "date_range": {
                "earliest": dataset.date_range.earliest.isoformat() if dataset.date_range and dataset.date_range.earliest else None,
                "latest": dataset.date_range.latest.isoformat() if dataset.date_range and dataset.date_range.latest else None,
            },
            "transactions": [t.model_dump(mode="json") for t in dataset.transactions],
        },
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

