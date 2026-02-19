## Transaction Analysis API 

This project is a decoupled RESTful API and ETL service built with Python, FastAPI, Prefect, and PostgreSQL. It is fully containerised using Docker and deployed to AWS (EC2 & RDS) with a fully automated CI/CD pipeline via GitHub Actions and Terraform.

The architecture separates the web server from heavy data processing. It provides API endpoints for users to upload massive CSV files and retrieve summarised statistics, while background worker containers handle data chunking, automated nightly data generation, and idempotent database insertions.

---

### Features

* **Infrastructure as Code (IaC):** Automated cloud infrastructure provisioning (VPC, Subnets, EC2, RDS) using Terraform with remote S3 state management.
* **Decoupled Data Orchestration:** Uses Prefect to offload heavy CSV processing. 
* **Automated Cron Jobs:** A scheduled nightly pipeline to automatically generate, process, and append yesterday's simulated transactions to the database.
* **Cloud Deployment:** Hosted on AWS EC2 (Ubuntu) with a managed AWS RDS PostgreSQL database.
* **Continuous Deployment (CI/CD):** Fully automated pipeline via GitHub Actions. Pushing to main triggers Terraform infrastructure checks, automated testing (Pytest), Docker image builds to GitHub Container Registry, and zero-downtime deployment to the EC2 server via SSH.
* **Advanced SQL Analytics:** Complex data aggregations calculating user spending volatility, global ranking, and transaction velocity using PostgreSQL Window Functions and CTEs.
* **Interactive Data Visualisation**: Dynamically generates frontend HTML dashboards using Plotly to visualise daily spending trends and 7-day moving averages, utilising PostgreSQL generate_series to accurately calculate rolling averages across time-series gaps.

---

### Tech Stack
* **Backend:** Python 3.11, FastAPI, Pandas, Pytest, Plotly
* **Data Orchestration:** Prefect, SQLAlchemy, Alembic
* **Infrastructure:** Terraform, Docker, Docker Compose, AWS EC2 (Ubuntu 22.04), AWS RDS (PostgreSQL 15)
* **DevOps:** GitHub Actions (CI/CD), GitHub Container Registry (ghcr.io)

---

*Note: The live AWS EC2 and RDS instances may be down to conserve AWS Free Tier limits.*
*... Try `http://51.20.107.234/docs`*

![API Server Demo](images/API_on_server1.png)

![Prefect Runs](images/prefect_runs.png)

![New Transactions](images/new_transactions.png)

![7d Moving Average](images/7daymoving.png)


### Running Locally

**1. Clone the Repository:**
```sh
git clone https://github.com/dan-k-k/transactionapi
cd transactionapi
```
**2. Start the Application:**

```Bash
docker compose up
# wait for automatic tests to pass and open http://localhost:8000/docs
```
**3. Explore the Dashboards:**

* **FastAPI Swagger UI:** Navigate to http://localhost:8000/docs
* **Prefect Dashboard:** Navigate to http://localhost:4200 to view the active data pipelines and scheduled runs.

### API Endpoints & Usage

Navigate to http://localhost:8000/docs

**1. Generate & Ingest Data**
  1. Open the Prefect Dashboard (http://localhost:4200) and go to **Deployments**.
  2. Click on the **Bulk Data Generator Pipeline**. 
  3. Click **Run -> Custom Run**, enter your desired `num_rows` (e.g., 50000), and execute. The worker will generate the data and automatically trigger the ingestion subflow.
  *(Alternatively, you can manually upload your own CSV via the POST `/upload` endpoint in Swagger).*

**2. Get User Summary**
  1. Click on the GET `/summary/{user_id}` endpoint. Click "Try it out".
  2. Enter a `user_id` (e.g., '1') and a date range in the format YYYY-MM-DD.
  3. Click Execute to see the aggregated max, min, and mean statistics.

**3. Analyse Risk Profile**
  1. Click on the GET `/analytics/risk-profile/{user_id}` endpoint.
  2. Enter a `user_id` to execute an advanced SQL query (using CTEs and Window Functions) that calculates the user's global whale rank, spending volatility, and transaction velocity.

**4. View Interactive Dashboard**
  1. Open your browser and navigate directly to `http://localhost:8000/dashboard/1` (replace `1` with any valid `user_id`).
  2. Explore the interactive Plotly chart displaying daily spend and the accurate 7-day moving average.
  *(Note: For the raw JSON payload of this trend, use the GET `/analytics/spend-trend/{user_id}` endpoint in Swagger).*

### Developing Locally

1. Create a file named `docker-compose.override.yml` in the root directory:

```YAML
services:
  web:
    build: .
  worker:
    build: .
```

2. Run `docker compose up --build`. The app will now reflect your local changes. 

