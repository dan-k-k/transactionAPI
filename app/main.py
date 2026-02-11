# app/main.py
# find . -maxdepth 2 -not -path '*/.*'
from datetime import date

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy import text, Engine
from sqlalchemy.orm import Session
from .database import engine as main_engine, SessionLocal, Base 
from .schemas import SummaryStats 
from . import processing, models 

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

def process_csv_wrapper(contents: bytes, engine: Engine):
    print(f"Uploading csv...")
    try:
        rows = processing.process_csv_to_db(contents, engine)
        print(f"COMPLETE: {rows} transactions added to DB.")
        print("You may now query the /summary endpoint.\n")
        print("user_id is an integer. Dates are in format YYYY-MM-DD.\n")
    except Exception as e:
        print(f"Error during processing: {e}.")

# This is the route for the root URL "/"
@app.get("/")
def read_root():
    return {"message": "Welcome to the Transaction Analysis API"}

@app.post("/upload")
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    engine: Engine = Depends(get_engine)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    try:
        contents = await file.read()
        
        processing.validate_csv_format(contents) # fast validation
        background_tasks.add_task(process_csv_wrapper, contents, engine) # add slow full task to backgroundtasks

        return {"message": f"File '{file.filename}' accepted. Please check terminal logs for 'COMPLETE' before querying."}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during file processing: {e}")
    
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

