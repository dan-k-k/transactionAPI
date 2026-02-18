# worker.py
from prefect import serve
from app.processing import run_csv_pipeline
from app.gen_daily import run_nightly_generation

if __name__ == "__main__":
    # 1. Upload any bulk CSV to add to the database. Ignores duplicate tids.
    csv_processor = run_csv_pipeline.to_deployment(
        name="csv-processor",
        tags=["csv"],
        description="Processes uploaded CSVs in the background."
    )
    
    # 2. Automatic full-day new data.
    nightly_generator = run_nightly_generation.to_deployment(
        name="daily-append-job",
        tags=["generation", "cron"],
        cron="1 0 * * *",
        description="Appends yesterday's dummy transactions."
    )

    serve(csv_processor, nightly_generator, limit=1, pause_on_shutdown=False) # serve both

