import os
import io
import json
import duckdb
import pandas as pd
import anthropic
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List
from processors import FileProcessor, DataCleaner, DataMerger, ReportGenerator

load_dotenv()

app = FastAPI(title="Excel Consolidator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# In-memory storage for the session
session_data = {
    "raw_files": {},
    "cleaned_data": {},
    "consolidated": None,
    "audit_log": []
}

@app.get("/")
def root():
    return {"message": "Excel Consolidator API is running!"}

@app.post("/upload-files")
async def upload_files(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        if not (file.filename.endswith(".xlsx") or 
                file.filename.endswith(".xls") or 
                file.filename.endswith(".csv")):
            raise HTTPException(status_code=400, detail=f"{file.filename} is not a supported file type")
        
        content = await file.read()
        processor = FileProcessor(file.filename, content)
        df = processor.load()
        session_data["raw_files"][file.filename] = df
        session_data["audit_log"].append(f"Loaded {file.filename} — {len(df)} rows, {len(df.columns)} columns: {list(df.columns)}")
        
        results.append({
            "filename": file.filename,
            "rows": len(df),
            "columns": list(df.columns)
        })
    
    return {"uploaded": results}

@app.get("/map-columns")
async def map_columns():
    if not session_data["raw_files"]:
        raise HTTPException(status_code=400, detail="No files uploaded yet")
    
    files_info = {}
    for filename, df in session_data["raw_files"].items():
        files_info[filename] = list(df.columns)
    
    prompt = f"""You are a data mapping expert. I have uploaded these Excel files with these columns:

{json.dumps(files_info, indent=2)}

Identify which columns across different files represent the same concept, even if named differently.
For example: "Item Code", "SKU", "Material ID", "Product Code" all represent a product identifier.

Return ONLY a JSON object in this exact format:
{{
  "mappings": [
    {{
      "standard_name": "Product ID",
      "description": "Unique product identifier",
      "matches": {{
        "purchasing.xlsx": "Item Code",
        "sales.xlsx": "SKU",
        "inventory.xlsx": "Material ID"
      }}
    }}
  ]
}}"""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    raw = response.content[0].text
    clean = raw.replace("```json", "").replace("```", "").strip()
    mappings = json.loads(clean)
    
    session_data["audit_log"].append(f"Claude identified {len(mappings['mappings'])} column mappings")
    
    return mappings

@app.post("/clean-and-consolidate")
async def clean_and_consolidate():
    if not session_data["raw_files"]:
        raise HTTPException(status_code=400, detail="No files uploaded yet")
    
    cleaned_dfs = {}
    for filename, df in session_data["raw_files"].items():
        cleaner = DataCleaner(filename, df)
        cleaned_df, logs = cleaner.clean()
        cleaned_dfs[filename] = cleaned_df
        session_data["audit_log"].extend(logs)
    
    merger = DataMerger(cleaned_dfs)
    consolidated_df, merge_logs = merger.merge()
    session_data["audit_log"].extend(merge_logs)
    session_data["consolidated"] = consolidated_df
    
    # Use DuckDB to run a quick summary analysis
    con = duckdb.connect()
    con.register("consolidated", consolidated_df)
    summary = con.execute("SELECT COUNT(*) as total_rows, COUNT(DISTINCT \"Product ID\") as unique_products FROM consolidated").fetchdf()
    
    return {
        "message": "Data cleaned and consolidated successfully",
        "total_rows": int(summary["total_rows"][0]),
        "unique_products": int(summary["unique_products"][0]),
        "columns": list(consolidated_df.columns)
    }

@app.get("/download-excel")
async def download_excel():
    if session_data["consolidated"] is None:
        raise HTTPException(status_code=400, detail="No consolidated data yet")
    
    output_path = "output/consolidated.xlsx"
    os.makedirs("output", exist_ok=True)
    session_data["consolidated"].to_excel(output_path, index=False)
    
    return FileResponse(output_path, filename="consolidated_data.xlsx", 
                       media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.get("/download-report")
async def download_report():
    if not session_data["audit_log"]:
        raise HTTPException(status_code=400, detail="No audit log yet")
    
    generator = ReportGenerator(session_data["audit_log"], session_data["consolidated"])
    report_path = generator.generate()
    
    return FileResponse(report_path, filename="audit_report.pdf", media_type="application/pdf")

@app.get("/reset")
async def reset():
    session_data["raw_files"] = {}
    session_data["cleaned_data"] = {}
    session_data["consolidated"] = None
    session_data["audit_log"] = []
    return {"message": "Session reset successfully"}