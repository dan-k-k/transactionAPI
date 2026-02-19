# worker.py
from prefect import serve
from app.processing import run_csv_pipeline
from app.gen_daily import run_nightly_generation
from app.gen_bulk import run_bulk_generation # <-- Add this import

if __name__ == "__main__":
    # 1. Upload any bulk CSV to add to the database.
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

    # 3. On-demand bulk generation
    bulk_generator = run_bulk_generation.to_deployment(
        name="bulk-generation-job",
        tags=["generation", "manual"],
        description="Generates a custom number of rows and uploads them to the DB."
    )

    serve(csv_processor, nightly_generator, bulk_generator, limit=1, pause_on_shutdown=False)

