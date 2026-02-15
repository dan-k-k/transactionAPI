# app/main.py
# find . -maxdepth 2 -not -path '*/.*'
# docker system prune -a --volumes -f # nuclear
# ssh -i /path/key.pem ec2-user@<EC2-public-IP>
from datetime import date
import shutil
import uuid
import os
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from prefect.deployments import run_deployment
from sqlalchemy import text

from .database import engine as main_engine, SessionLocal
from .config import settings
from . import processing, models
from .schemas import SummaryStats

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/shared_data")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="Transaction API",
    description="API for uploading and summarising transaction data."
)

@app.on_event("startup")
async def startup_event(): print("Open Swagger UI here: http://localhost:8000/docs")

# Dependency function for engine
def get_engine():
    yield main_engine

# Dependency function for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# This is the route for the root URL "/"
@app.get("/")
def read_root():
    return {"message": "Hello from the automated cloud!"}

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    # 1. Save the file to the shared volume
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Trigger Prefect deployment asynchronously (Fire and Forget)
        # The name must match "FlowName/DeploymentName"
        asyncio.create_task(
            run_deployment(
                name="CSV Ingestion Pipeline/csv-processor",
                parameters={
                    "file_path": file_path, 
                    "database_url": settings.get_database_url()
                },
                timeout=0 # Returns immediately, doesn't wait for the flow to finish
            )
        )

        return {"message": f"File '{file.filename}' queued for processing."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue file: {e}")
    
@app.get("/summary/{user_id}", response_model=SummaryStats)
def get_summary(
    user_id: int, 
    start_date: date, 
    end_date: date, 
    db: Session = Depends(get_db)
):
    """
    Returns transaction summary statistics for a specific user within a date range.
    - **user_id**: The ID of the user
    - **start_date**: Start date for the analysis (YYYY-MM-DD)
    - **end_date**: End date for the analysis (YYYY-MM-DD)
    """
    # Add validation check for date logic
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be after end_date"
        )
    
    # Use parameterised query to prevent SQL injection
    query = text("""
    SELECT
        MAX(transaction_amount) as max_val,
        MIN(transaction_amount) as min_val,
        AVG(transaction_amount) as mean_val
    FROM transactions
    WHERE user_id = :user_id
      AND DATE(timestamp) BETWEEN :start_date AND :end_date
    """)
    
    try:
        result = db.execute(query, {
            'user_id': user_id,
            'start_date': start_date,
            'end_date': end_date
        }).fetchone()
        
        if result and result[0] is not None:
            return SummaryStats(
                user_id=user_id,
                max_transaction=result[0],
                min_transaction=result[1],
                mean_transaction=result[2],
            )
        else:
            raise HTTPException(status_code=404, detail="No transactions found for user in the given date range.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

