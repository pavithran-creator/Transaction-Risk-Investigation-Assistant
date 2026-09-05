from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from src.analytics.attention_engine import evaluate_attention
from src.analytics.baseline_calculator import build_customer_baseline
from src.analytics.csv_validator import validate_csv
from src.analytics.investigation_service import generate_investigation_explanation
from src.analytics.state import clear_current_dataset, get_current_dataset, set_current_dataset
from src.analytics.transaction_loader import load_dataset_from_csv_bytes
from src.models.transaction import MAX_UPLOAD_SIZE_BYTES, error_response
from src.reports.report_service import generate_investigation_report
from src.rules.engine import evaluate_all_rules



app = FastAPI(title="PS06 Transaction Risk Investigation Assistant")

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Ensure no Python stack traces leak to API consumers."""
    return JSONResponse(
        status_code=500,
        content={
            "valid": False,
            "errors": ["An unexpected server error occurred while processing the request."],
        },
    )


@app.get("/")
def read_root(request: Request):
    """
    Root endpoint: returns HTML for browser navigation or JSON status for API requests.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return FileResponse("frontend/index.html")
    return {"message": "PS06 Transaction Risk Investigation Assistant is running"}


@app.get("/dashboard")
@app.get("/app")
def read_dashboard():
    return FileResponse("frontend/index.html")


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


@app.get("/api/baseline")
def get_baseline():
    """
    Retrieve deterministic customer baseline statistics for the loaded transaction history.

    Calculates amount distribution, channel usage, payee breakdown, temporal activity,
    and daily transaction frequency for the active customer.
    """
    dataset = get_current_dataset()
    if not dataset or dataset.transaction_count == 0:
        return JSONResponse(
            status_code=200,
            content={
                "status": "empty",
                "message": "No transaction dataset currently loaded. Please upload a CSV first.",
                "customer_id": None,
                "transaction_count": 0,
                "baseline": None,
            },
        )

    baseline = build_customer_baseline(dataset)
    if not baseline:
        return JSONResponse(
            status_code=200,
            content={
                "status": "empty",
                "message": "Unable to calculate customer baseline.",
                "customer_id": None,
                "transaction_count": 0,
                "baseline": None,
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "status": "calculated",
            "customer_id": baseline.customer_id,
            "transaction_count": baseline.transaction_count,
            "baseline": baseline.model_dump(mode="json"),
        },
    )


@app.get("/api/rules")
def get_rules():
    """
    Evaluate deterministic risk rules (R01-R04) for the loaded transaction history.

    Returns deterministic evaluation results for R01, R02, R03, and R04 along with
    rule evidence and indicators.
    """
    dataset = get_current_dataset()
    if not dataset or dataset.transaction_count == 0:
        return JSONResponse(
            status_code=200,
            content={
                "status": "empty",
                "message": "No transaction dataset currently loaded. Please upload a CSV first.",
                "customer_id": None,
                "evaluated_at_transaction_count": 0,
                "rules": [],
            },
        )

    eval_result = evaluate_all_rules(dataset)
    return JSONResponse(
        status_code=200,
        content={
            "status": "evaluated",
            "customer_id": eval_result.customer_id,
            "evaluated_at_transaction_count": eval_result.evaluated_at_transaction_count,
            "rules": [r.model_dump(mode="json") for r in eval_result.rules],
        },
    )


@app.get("/api/attention")
def get_attention():
    """
    Evaluate deterministic investigator attention assessment for the loaded transaction history.

    Combines Phase 4 customer baseline analysis and Phase 5 deterministic risk rule evidence
    to determine the appropriate investigator attention level (NO_IMMEDIATE_CONCERN, CONTEXTUAL_REVIEW,
    ATTENTION_RECOMMENDED, HIGH_ATTENTION, or INSUFFICIENT_EVIDENCE).
    """
    try:
        dataset = get_current_dataset()
        if not dataset or dataset.transaction_count == 0:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "empty",
                    "message": "No transaction dataset currently loaded. Please upload a CSV first.",
                    "customer_id": None,
                    "assessment": evaluate_attention(None).model_dump(mode="json"),
                },
            )

        assessment = evaluate_attention(dataset)
        return JSONResponse(
            status_code=200,
            content={
                "status": "evaluated",
                "customer_id": assessment.customer_id,
                "assessment": assessment.model_dump(mode="json"),
            },
        )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "An unexpected error occurred while generating the attention assessment.",
                "customer_id": None,
                "assessment": evaluate_attention(None).model_dump(mode="json"),
            },
        )


@app.get("/api/investigation")
def get_investigation():
    """
    Generate grounded Gemini investigation explanation for the loaded transaction history.

    Passes deterministic evidence to Gemini to produce investigator-oriented explanation.
    """
    try:
        dataset = get_current_dataset()
        explanation = generate_investigation_explanation(dataset)
        return JSONResponse(
            status_code=200,
            content={
                "status": "completed",
                "customer_id": explanation.customer_id,
                "explanation": explanation.model_dump(mode="json"),
            },
        )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "An unexpected error occurred while generating the investigation explanation.",
                "customer_id": None,
                "explanation": None,
            },
        )


@app.get("/api/report")
def get_report():
    """
    Generate complete, structured Investigation Report for the loaded transaction history.

    Combines baseline metrics, deterministic risk rules (R01-R04), attention level,
    and grounded Gemini investigation explanation into a traceable report.
    """
    try:
        dataset = get_current_dataset()
        if not dataset or dataset.transaction_count == 0:
            return JSONResponse(
                status_code=200,
                content={
                    "valid": False,
                    "message": "No transaction dataset is loaded. Upload a valid transaction CSV first.",
                },
            )

        report = generate_investigation_report(dataset)
        return JSONResponse(
            status_code=200,
            content={
                "status": "completed",
                "customer_id": report.customer_id,
                "report": report.model_dump(mode="json"),
            },
        )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "An unexpected error occurred while generating the investigation report.",
                "customer_id": None,
                "report": None,
            },
        )



if __name__ == "__main__":
    import threading
    import webbrowser

    def open_browser():
        import time
        time.sleep(1.2)
        try:
            webbrowser.open("http://localhost:8000")
        except Exception:
            pass

    threading.Thread(target=open_browser, daemon=True).start()
    print("\n" + "=" * 70)
    print(" PS06 Banking Transaction Risk Investigation Assistant")
    print(" Dashboard Frontend & Backend Server running at: http://localhost:8000")
    print(" Interactive API Documentation: http://localhost:8000/docs")
    print("=" * 70 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)




