from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import List
import requests

# Load environment variables
load_dotenv()

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
}

# Control-M API Configuration
CONTROL_M_BASE_URL = "https://ctm.us.dell.com:8446/automation-api/run/jobs/status"
API_KEY = os.getenv("CONTROL_M_API_KEY")

HEADERS = {
    "accept": "application/json",
    "x-api-key": API_KEY
}

# FastAPI app setup
app = FastAPI()

# Enable CORS for frontend access (e.g., Streamlit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can lock this down later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ExperimentResponse(BaseModel):
    experiment_id: str

class JobStatusResponse(BaseModel):
    jobId: str
    status: str

# Root
@app.get("/")
def read_root():
    return {"message": "API is running. Use /api/experiments or /api/job_status."}

# Endpoint 1: Get experiment IDs from PostgreSQL
@app.get("/api/experiments", response_model=List[ExperimentResponse])
def get_experiments(date: str = Query(..., description="YYYY-MM-DD")):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        query = """
            SELECT "EXPERIMENT_ID"
            FROM sim_tables.scenario_manager
            WHERE "SIMULATION_TYPE" = 'BASELINE'
              AND "SCENARIO_RUN_TS"::date = %s
        """
        cursor.execute(query, (date,))
        rows = cursor.fetchall()

        return [{"experiment_id": row[0]} for row in rows]

    except Exception as e:
        return [{"experiment_id": f"Error: {str(e)}"}]

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

# Endpoint 2: Get Control-M job status
@app.get("/api/job_status", response_model=List[JobStatusResponse])
def get_job_status(
    limit: int = Query(1000),
    jobname: str = Query(...),
    folder: str = Query(...),
    historyRunDate: str = Query(..., description="YYMMDD format")
):
    params = {
        "limit": limit,
        "jobname": jobname,
        "folder": folder,
        "historyRunDate": historyRunDate
    }

    try:
        response = requests.get(CONTROL_M_BASE_URL, headers=HEADERS, params=params, verify=False)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"API request failed: {str(e)}")

    data = response.json()
    statuses = data.get("statuses", [])

    if not statuses:
        raise HTTPException(status_code=404, detail="No job statuses found.")

    return [{"jobId": job.get("jobId"), "status": job.get("status")} for job in statuses]
