from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from src.analytics.csv_validator import validate_csv
from src.models.transaction import MAX_UPLOAD_SIZE_BYTES

app = FastAPI(title="PS06 Transaction Risk Investigation Assistant")


@app.get("/")
def read_root():
    return {"message": "PS06 Transaction Risk Investigation Assistant is running"}


@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a transaction CSV for validation.

    Accepts a CSV file, validates its structure and transaction data,
    and returns a structured validation result.

    **File size limit:** 10 MB
    """
    # --- Content-type sanity check ------------------------------------
    if file.content_type and file.content_type not in (
        "text/csv",
        "application/vnd.ms-excel",
        "application/octet-stream",
    ):
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
        return JSONResponse(
            status_code=400,
            content={
                "valid": False,
                "errors": ["Unable to read the uploaded file."],
            },
        )

    if len(raw_bytes) > MAX_UPLOAD_SIZE_BYTES:
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

    # --- Run validation pipeline --------------------------------------
    result = validate_csv(raw_bytes)

    status_code = 200 if result.get("valid") else 422
    return JSONResponse(status_code=status_code, content=result)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
