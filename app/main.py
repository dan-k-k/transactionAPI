# app/main.py
# find . -maxdepth 2 -not -path '*/.*' # directory local
# docker system prune -a --volumes -f # nuke local

# chmod 400 tf_key                                              # because tf_key is open (locally)
# ssh -i /path/key.pem ubuntu@<EC2-public-IP>                 # log into EC2
# cd app
# sudo docker-compose -f docker-compose.prod.yml logs -f worker # worker log
# df -h                                                         # check why EC2 froze
# cat .env                                                      # see db credentials
# sudo docker ps                                                # check what containers are running

# sudo docker exec -it 56e1c8e0a240 prefect deployment run 'Nightly Data Generator/daily-append-job'
# sudo docker run -it --rm postgres:15 psql -h terraform-20260216102256681000000002.ctaa4eca8hiy.eu-north-1.rds.amazonaws.com -U transactions -d postgres

# terraform apply -var-file="secrets.tfvars"

from datetime import date
import shutil
import uuid
import os
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from prefect.deployments import run_deployment
from sqlalchemy import text
import plotly.graph_objects as go

from .database import engine as main_engine, SessionLocal
from .config import settings
from .schemas import SummaryStats, SpendTrendItem
from . import models  # noqa: F401

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

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Fire and Forget (prefect deployment triggered)
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
    # Validation check for date logic
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be after end_date"
        )
    
    # Parameterised query to prevent SQL injection
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
    
@app.get("/analytics/risk-profile/{user_id}")
def get_user_risk_profile(user_id: int, db: Session = Depends(get_db)):
    """
    Generates an advanced financial risk profile for a user, calculating 
    spending volatility, global ranking, and transaction velocity.
    """
    query = text("""
        WITH UserAggregates AS (
            SELECT 
                user_id,
                COUNT(*) as total_transactions,
                SUM(transaction_amount) as total_spend,
                AVG(transaction_amount) as avg_spend,
                COALESCE(STDDEV_POP(transaction_amount), 0) as spend_stddev
            FROM transactions
            GROUP BY user_id
        ),
        GlobalRanking AS (
            SELECT 
                user_id,
                total_spend,
                CASE 
                    WHEN avg_spend = 0 THEN 0 
                    ELSE (spend_stddev / avg_spend) 
                END as volatility_index,
                DENSE_RANK() OVER (ORDER BY total_spend DESC) as whale_rank
            FROM UserAggregates
        ),
        UserTimeGaps AS (
            SELECT 
                user_id,
                transaction_amount,
                timestamp,
                EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (PARTITION BY user_id ORDER BY timestamp))) / 60 as mins_since_last_txn
            FROM transactions
            WHERE user_id = :uid
        )
        SELECT 
            r.whale_rank,
            ROUND(r.volatility_index, 2) as volatility_index,
            r.total_spend,
            ROUND(MIN(g.mins_since_last_txn), 2) as shortest_txn_gap_mins,
            MAX(g.transaction_amount) as max_single_spike
        FROM GlobalRanking r
        LEFT JOIN UserTimeGaps g ON r.user_id = g.user_id
        WHERE r.user_id = :uid
        GROUP BY r.whale_rank, r.volatility_index, r.total_spend;
    """)

    result = db.execute(query, {"uid": user_id}).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="User not found or no transactions exist.")

    return {
        "user_id": user_id,
        "risk_metrics": {
            "global_whale_rank": int(result.whale_rank),
            "spending_volatility_index": float(result.volatility_index),
            "total_lifetime_spend": float(result.total_spend),
            "max_single_transaction_spike": float(result.max_single_spike),
            "shortest_time_between_transactions_mins": float(result.shortest_txn_gap_mins) if result.shortest_txn_gap_mins else None
        },
        "analysis": "High volatility implies erratic spending. Short transaction gaps may indicate automated or fraudulent activity."
    }
    
def fetch_spend_trend_data(user_id: int, db: Session):
    """Helper function to fetch and calculate accurate 7-day rolling averages."""
    query = text("""
        WITH date_range AS (
            SELECT MIN(DATE(timestamp)) as start_date, MAX(DATE(timestamp)) as end_date
            FROM transactions
            WHERE user_id = :uid
        ),
        calendar AS (
            SELECT generate_series(start_date::timestamp, end_date::timestamp, '1 day'::interval)::date as spend_date
            FROM date_range
        ),
        daily_sums AS (
            SELECT 
                DATE(timestamp) as spend_date,
                SUM(transaction_amount) as daily_total
            FROM transactions
            WHERE user_id = :uid
            GROUP BY DATE(timestamp)
        )
        SELECT 
            c.spend_date,
            COALESCE(d.daily_total, 0) as daily_total,
            AVG(COALESCE(d.daily_total, 0)) OVER (
                ORDER BY c.spend_date 
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) as rolling_7d_avg
        FROM calendar c
        LEFT JOIN daily_sums d ON c.spend_date = d.spend_date
        ORDER BY c.spend_date;
    """)
    return db.execute(query, {"uid": user_id}).fetchall()


@app.get("/analytics/spend-trend/{user_id}", response_model=list[SpendTrendItem])
def get_user_spend_trend(user_id: int, db: Session = Depends(get_db)):
    """Returns pure JSON of daily spend and a 7-day rolling average."""
    results = fetch_spend_trend_data(user_id, db)

    if not results:
        raise HTTPException(status_code=404, detail="No transactions found for this user.")

    return [
        SpendTrendItem(
            spend_date=row.spend_date,
            daily_total=row.daily_total,
            rolling_7d_avg=row.rolling_7d_avg
        ) for row in results
    ]


@app.get("/dashboard/{user_id}", response_class=HTMLResponse)
def get_user_dashboard(user_id: int, db: Session = Depends(get_db)):
    """Dynamically generates an interactive Plotly HTML dashboard for the user."""
    results = fetch_spend_trend_data(user_id, db)

    if not results:
        return HTMLResponse(content=f"<h2>No data available to plot for User {user_id}</h2>", status_code=404)

    # Unpack the data for Plotly
    dates = [row.spend_date for row in results]
    daily_totals = [row.daily_total for row in results]
    rolling_avgs = [row.rolling_7d_avg for row in results]

    # Create the interactive figure
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=dates, 
        y=daily_totals, 
        name="Daily Spend", 
        opacity=0.6,
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Scatter(
        x=dates, 
        y=rolling_avgs, 
        mode='lines', 
        name="7-Day Moving Average", 
        line=dict(color='darkblue', width=3)
    ))

    fig.update_layout(
        title=f"Transaction Analysis: User {user_id}",
        xaxis_title="Date",
        yaxis_title="Amount ($)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    html_content = fig.to_html(full_html=True, include_plotlyjs='cdn')
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)  # nosec B104

