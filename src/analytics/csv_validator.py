"""
CSV upload parsing, validation, and normalization.

Responsibilities (Phase 2 only):
  - Parse uploaded CSV bytes into a DataFrame.
  - Validate file-level structure (empty, missing columns).
  - Validate each transaction row (types, values, uniqueness).
  - Normalize valid data into a consistent internal representation.
  - Return structured validation results.

This module does NOT perform any risk analysis, fraud detection,
or classification — those belong to later phases.
"""

from __future__ import annotations

import io
from typing import List, Tuple

import pandas as pd

from src.models.transaction import (
    REQUIRED_COLUMNS,
    SUPPORTED_CHANNELS,
    error_response,
    success_response,
)


# ===================================================================
# Public API
# ===================================================================

def validate_csv(raw_bytes: bytes) -> dict:
    """
    Full validation pipeline for an uploaded CSV file.

    Returns a dict suitable for direct JSON serialization in the API
    response. The ``"valid"`` key indicates overall success/failure.
    """
    # ------------------------------------------------------------------
    # 1. File-level: decode and parse
    # ------------------------------------------------------------------
    df, file_errors = _parse_csv_bytes(raw_bytes)
    if file_errors:
        return error_response(file_errors)

    # ------------------------------------------------------------------
    # 2. File-level: required-column check
    # ------------------------------------------------------------------
    col_errors = _check_required_columns(df)
    if col_errors:
        return error_response(col_errors)

    # ------------------------------------------------------------------
    # 3. File-level: must contain at least one data row
    # ------------------------------------------------------------------
    if len(df) == 0:
        return error_response(["CSV contains no transaction records"])

    # ------------------------------------------------------------------
    # 4. Transaction-level: validate every row
    # ------------------------------------------------------------------
    row_errors = _validate_rows(df)
    if row_errors:
        return error_response(row_errors)

    # ------------------------------------------------------------------
    # 5. Normalize valid data
    # ------------------------------------------------------------------
    df = _normalize(df)

    # ------------------------------------------------------------------
    # 6. Build success response
    # ------------------------------------------------------------------
    transactions = df.to_dict(orient="records")
    return success_response(
        transaction_count=len(df),
        customer_count=df["customer_id"].nunique(),
        columns=list(df.columns),
        transactions=transactions,
    )


# ===================================================================
# File-level helpers
# ===================================================================

def _parse_csv_bytes(raw_bytes: bytes) -> Tuple[pd.DataFrame | None, List[str]]:
    """Attempt to decode and parse raw bytes as CSV."""
    if not raw_bytes or len(raw_bytes.strip()) == 0:
        return None, ["Uploaded file is empty"]

    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw_bytes.decode("latin-1")
        except Exception:
            return None, ["Unable to decode the uploaded file. Please upload a valid UTF-8 CSV."]

    try:
        df = pd.read_csv(io.StringIO(text))
    except pd.errors.EmptyDataError:
        return None, ["Uploaded file is empty or contains no parseable data"]
    except pd.errors.ParserError as exc:
        return None, [f"Invalid CSV structure: {exc}"]
    except Exception as exc:
        return None, [f"Unable to read CSV: {exc}"]

    return df, []


def _check_required_columns(df: pd.DataFrame) -> List[str]:
    """Return errors for every required column that is missing."""
    existing = {c.strip().lower() for c in df.columns}
    errors: List[str] = []
    for col in REQUIRED_COLUMNS:
        if col not in existing:
            errors.append(f"Missing required column: {col}")
    return errors


# ===================================================================
# Transaction-level validation
# ===================================================================

def _validate_rows(df: pd.DataFrame) -> List[str]:
    """Validate individual transaction values. Returns a list of errors."""
    # Normalize column names first (lowercase + strip) so field access is safe
    df.columns = [c.strip().lower() for c in df.columns]

    errors: List[str] = []

    errors.extend(_validate_transaction_ids(df))
    errors.extend(_validate_customer_ids(df))
    errors.extend(_validate_timestamps(df))
    errors.extend(_validate_amounts(df))
    errors.extend(_validate_payees(df))
    errors.extend(_validate_descriptions(df))
    errors.extend(_validate_channels(df))

    return errors


def _row_label(row_idx: int, txn_id) -> str:
    """Human-readable row label for error messages."""
    row_num = row_idx + 2  # +1 for 0-index, +1 for header row
    if pd.notna(txn_id) and str(txn_id).strip():
        return f"Row {row_num} / {str(txn_id).strip()}"
    return f"Row {row_num}"


# --- transaction_id ---------------------------------------------------

def _validate_transaction_ids(df: pd.DataFrame) -> List[str]:
    errors: List[str] = []

    # Empty / missing
    for idx, val in df["transaction_id"].items():
        if pd.isna(val) or str(val).strip() == "":
            errors.append(f"Row {idx + 2}: transaction_id is missing or empty")

    # Duplicates (only among non-empty IDs)
    non_empty = df[df["transaction_id"].notna()].copy()
    non_empty["_tid_clean"] = non_empty["transaction_id"].astype(str).str.strip()
    non_empty = non_empty[non_empty["_tid_clean"] != ""]
    dupes = non_empty[non_empty.duplicated(subset="_tid_clean", keep=False)]
    seen = set()
    for tid in dupes["_tid_clean"]:
        if tid not in seen:
            errors.append(f"Duplicate transaction_id found: {tid}")
            seen.add(tid)

    return errors


# --- customer_id ------------------------------------------------------

def _validate_customer_ids(df: pd.DataFrame) -> List[str]:
    errors: List[str] = []
    for idx, val in df["customer_id"].items():
        if pd.isna(val) or str(val).strip() == "":
            label = _row_label(idx, df.at[idx, "transaction_id"])
            errors.append(f"{label}: customer_id is missing or empty")
    return errors


# --- timestamp --------------------------------------------------------

def _validate_timestamps(df: pd.DataFrame) -> List[str]:
    errors: List[str] = []
    for idx, val in df["timestamp"].items():
        if pd.isna(val) or str(val).strip() == "":
            label = _row_label(idx, df.at[idx, "transaction_id"])
            errors.append(f"{label}: timestamp is missing or empty")
            continue
        try:
            pd.to_datetime(str(val).strip())
        except (ValueError, TypeError):
            label = _row_label(idx, df.at[idx, "transaction_id"])
            errors.append(f"{label}: invalid timestamp value '{val}'")
    return errors


# --- amount -----------------------------------------------------------

def _validate_amounts(df: pd.DataFrame) -> List[str]:
    errors: List[str] = []
    for idx, val in df["amount"].items():
        label = _row_label(idx, df.at[idx, "transaction_id"])

        if pd.isna(val) or str(val).strip() == "":
            errors.append(f"{label}: amount is missing or empty")
            continue

        raw = str(val).strip()
        try:
            numeric = float(raw)
        except (ValueError, TypeError):
            errors.append(f"{label}: amount must be a valid number, got '{raw}'")
            continue

        if numeric <= 0:
            if numeric == 0:
                errors.append(f"{label}: amount must be greater than zero")
            else:
                errors.append(f"{label}: amount must be a positive number")

    return errors


# --- payee ------------------------------------------------------------

def _validate_payees(df: pd.DataFrame) -> List[str]:
    errors: List[str] = []
    for idx, val in df["payee"].items():
        if pd.isna(val) or str(val).strip() == "":
            label = _row_label(idx, df.at[idx, "transaction_id"])
            errors.append(f"{label}: payee is missing or empty")
    return errors


# --- description ------------------------------------------------------

def _validate_descriptions(df: pd.DataFrame) -> List[str]:
    errors: List[str] = []
    for idx, val in df["description"].items():
        if pd.isna(val) or str(val).strip() == "":
            label = _row_label(idx, df.at[idx, "transaction_id"])
            errors.append(f"{label}: description is missing or empty")
    return errors


# --- channel ----------------------------------------------------------

def _validate_channels(df: pd.DataFrame) -> List[str]:
    errors: List[str] = []
    for idx, val in df["channel"].items():
        label = _row_label(idx, df.at[idx, "transaction_id"])

        if pd.isna(val) or str(val).strip() == "":
            errors.append(f"{label}: channel is missing or empty")
            continue

        normalized = str(val).strip().upper().replace(" ", "_")
        if normalized not in SUPPORTED_CHANNELS:
            errors.append(
                f"{label}: unsupported channel '{str(val).strip()}'. "
                f"Supported channels: {', '.join(sorted(SUPPORTED_CHANNELS))}"
            )
    return errors


# ===================================================================
# Normalization
# ===================================================================

def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize validated transaction data into a consistent format.

    - Column names → lowercase stripped.
    - Timestamps → pandas datetime ISO strings.
    - Amounts → float.
    - Channels → uppercase canonical form.
    - String fields → stripped whitespace.
    - Original transaction_id preserved exactly (only stripped).
    """
    df = df.copy()

    # Column names already lowered+stripped by _validate_rows
    df["transaction_id"] = df["transaction_id"].astype(str).str.strip()
    df["customer_id"] = df["customer_id"].astype(str).str.strip()
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="mixed").dt.strftime("%Y-%m-%d %H:%M:%S")
    df["amount"] = df["amount"].astype(float)
    df["payee"] = df["payee"].astype(str).str.strip()
    df["description"] = df["description"].astype(str).str.strip()
    df["channel"] = df["channel"].astype(str).str.strip().str.upper().str.replace(" ", "_", regex=False)

    return df
