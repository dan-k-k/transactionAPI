# worker.py
from prefect import serve
from app.processing import run_csv_pipeline
from app.gen_daily import run_nightly_generation

if __name__ == "__main__":
    # Create the processor deployment
    csv_processor = run_csv_pipeline.to_deployment(
        name="csv-processor",
        tags=["csv"],
        description="Processes uploaded CSVs in the background."
    )
    
    # Create the scheduled generator deployment
    nightly_generator = run_nightly_generation.to_deployment(
        name="daily-append-job",
        tags=["generation", "cron"],
        cron="1 0 * * *",
        description="Appends yesterday's dummy transactions."
    )

    # Serve both from this single worker process!
    serve(csv_processor, nightly_generator)

