## Transaction Analysis API

This project is a RESTful API service built with Python, FastAPI, and PostgreSQL. It is fully containerised using Docker to ensure easy distribution and consistent execution.

The API provides endpoints to upload large CSV files of e-commerce transactions and retrieve summarised statistics (max, min, mean) for specific users within a given date range.

---

### Features

* **Fully Containerised**: via Docker Compose. 
* **Efficient Processing**: chunks CSV uploads. 
* **Asynchronous Operations**: background tasks to process uploads without blocking the API response.
* **Robust Statistics**: summaries from the db.
* **Tested**

---

### Stack
**Python 3.11, FastAPI, pandas, PostgreSQL 15, Docker & Docker Compose, Pytest**

---

### Setup and Installation

**1. Clone the Repository:**
```sh
git clone https://github.com/dan-k-k/transactionAPI
cd transactionAPI
```
**2. Start the Application:**

```Bash
docker compose up
# wait for automatic tests to pass and open http://localhost:8000/docs
```
**3. Generate Test Data:**

```Bash
docker compose exec web python generate_data.py --rows 5000
# in a new terminal if needed; `cd transactionAPI` again.
# now look for the generated 'dummy_transactions.csv' in root directory.
```

### Running the Application

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