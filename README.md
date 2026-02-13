## Transaction Analysis API

This project is a RESTful API service built with Python, FastAPI, and PostgreSQL. It is fully containerised using Docker and deployed to the cloud using AWS (EC2 & RDS) with a fully automated CI/CD pipeline via GitHub Actions.

The API provides endpoints to upload large CSV files of e-commerce transactions and retrieve summarised statistics (max, min, mean) for specific users within a given date range.

---

### Features

* **Cloud Deployment**: Hosted on AWS EC2 with a managed AWS RDS PostgreSQL database.
* **Continuous Deployment (CI/CD)**: Fully automated pipeline via GitHub Actions. Pushing to `main` triggers automated testing (pytest), Docker image builds, and zero-downtime deployment to the EC2 server via SSH.
* **Fully Containerised**: Dockerised for local development and cloud execution.
* **Chunking**: Chunks large CSV uploads and utilises background tasks to process data without blocking the API response.

---

### Tech Stack
* **Backend:** Python 3.11, FastAPI, pandas, Pytest
* **Infrastructure:** Docker, AWS EC2 (Amazon Linux), AWS RDS (PostgreSQL 15)
* **DevOps:** GitHub Actions (CI/CD), GitHub Container Registry (ghcr.io)

---

*Note: The live AWS EC2 and RDS instances may currently be down to conserve AWS Free Tier limits.*
*... Try `http://13.62.46.228/docs#/`*

![API Server Demo](images/API_on_server.png)

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
**3. Generate Test Data:**

```Bash
docker compose exec web python generate_data.py --rows 5000
# in a new terminal if needed; `cd transactionapi` again.
# now look for the generated 'dummy_transactions.csv' in root directory.
```

### Running the Application Locally

Navigate to http://localhost:8000/docs

**1. Upload Data**
  1. Click on the POST /upload endpoint.
  2. Click "Try it out".
  3. Select the dummy_transactions.csv file you just generated.
  4. Click Execute.
  5. Watch out for the 'complete' message in your terminal.

**2. Get User Summary**
  1. Click on the GET /summary/{user_id} endpoint.
  2. Click "Try it out".
  3. Enter a user_id eg. '1' and a date range in the format YYYY-MM-DD
  4. Click Execute.

### Developing Locally

1. Create a file named `docker-compose.override.yml` in the root directory:

```YAML
services:
  web:
    build: .
```

2. Run docker compose up --build. The app will now reflect your local changes.

