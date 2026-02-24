"""FastAPI backend for FinanceRecon."""

import json
import os
import tempfile
import uuid
from io import BytesIO

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from profiles import delete_profile, load_profiles, save_profile
from reconcile import compare_data, format_output

app = FastAPI(title="FinanceRecon API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory token → Excel bytes cache
_download_cache: dict[str, bytes] = {}


@app.post("/api/columns")
async def get_columns(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        df = pd.read_excel(BytesIO(contents), dtype=str)
        return {"columns": list(df.columns)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/compare")
async def run_compare(
    first_file: UploadFile = File(...),
    second_file: UploadFile = File(...),
    config: str = Form(...),
):
    cfg = json.loads(config)
    first_bytes = await first_file.read()
    second_bytes = await second_file.read()

    try:
        first_df = pd.read_excel(BytesIO(first_bytes), dtype=str)
        second_df = pd.read_excel(BytesIO(second_bytes), dtype=str)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Error reading files: {exc}")

    tolerance_type = cfg.get("tolerance_type")
    if tolerance_type == "None":
        tolerance_type = None

    try:
        result = compare_data(
            first_df,
            second_df,
            cfg["match_keys_first"],
            cfg["match_keys_second"],
            cfg["compare_col_first"],
            cfg["compare_col_second"],
            tolerance_type=tolerance_type,
            tolerance_value=cfg.get("tolerance_value"),
            distinct_list=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Comparison error: {exc}")

    # Build formatted Excel for download
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        result.merged.to_excel(tmp_path, index=False)
        format_output(tmp_path, result.merged)
        with open(tmp_path, "rb") as f:
            excel_bytes = f.read()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    token = str(uuid.uuid4())
    _download_cache[token] = excel_bytes

    # Use pandas to_json so NaN/inf are serialised as null rather than
    # bare float('nan') which Python's json module rejects.
    rows_df = result.merged.copy()
    rows_list = json.loads(rows_df.to_json(orient="records"))

    return {
        "stats": {
            "total_records": result.total_records,
            "matched_records": result.matched_records,
            "match_percentage": result.match_percentage,
        },
        "columns": list(rows_df.columns),
        "rows": rows_list,
        "download_token": token,
    }


@app.get("/api/download/{token}")
def download_result(token: str):
    excel_bytes = _download_cache.get(token)
    if not excel_bytes:
        raise HTTPException(status_code=404, detail="Download not found or expired")
    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=reconciliation_results.xlsx"
        },
    )


@app.get("/api/profiles")
def get_profiles_route():
    return load_profiles()


@app.post("/api/profiles/{name}")
def save_profile_route(name: str, config: dict):  # type: ignore[type-arg]
    save_profile(name, config)
    return {"status": "saved"}


@app.delete("/api/profiles/{name}")
def delete_profile_route(name: str):
    delete_profile(name)
    return {"status": "deleted"}
