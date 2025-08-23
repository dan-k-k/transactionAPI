# Transaction Analysis API for Suade Challenge

This project is a RESTful API service built with Python and FastAPI. It provides endpoints to upload a large CSV file of e-commerce transactions and retrieve summarised statistics for specific users within a given date range.

---

## Features

* **/upload**: Accepts a large CSV file, processes it efficiently, and stores the data in a database.
* **/summary/{user_id}**: Returns key statistics (max, min, mean) for a user's transactions.
* **Efficient Processing**: Handles large datasets (1M+ rows) with low memory usage by processing the file in chunks.
* **Asynchronous Operations**: The file upload endpoint uses background tasks to avoid blocking and provide an immediate response.
* **Robust & Tested**: Includes a full suite of unit tests using `pytest` to ensure reliability.
* **Database-backed**: Uses SQLAlchemy with a SQLite database for data persistence and fast querying.

---

## Tech Stack

* **Language**: Python 3.10+
* **API Framework**: FastAPI
* **Data Processing**: pandas
* **Database**: SQLite with SQLAlchemy
* **Testing**: Pytest

---

## Setup and Installation

Follow these steps to set up the project environment locally.

**1. Prerequisites:**
* Python 3.10 or newer
* `pip` and `venv`

**2. Clone the Repository:**
```sh
git clone <your-repository-url>
cd suadeChallenge
3. Create and Activate a Virtual Environment:

Bash
# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate
4. Install Dependencies:
All required packages are listed in requirements.txt.

Bash
pip install -r requirements.txt
5. Generate Sample Data (Optional):
A script is provided to generate a dummy_transactions.csv file with 1 million records for testing.

Bash
python generate_data.py
Running the Application
To run the FastAPI server, use uvicorn:

Bash
uvicorn app.main:app --reload
The API will be available at http://127.0.0.1:8000. You can access the interactive Swagger UI documentation at http://127.0.0.1:8000/docs.

API Usage and Endpoints
1. Upload Transaction Data

Uploads a CSV file for processing. The processing is handled in the background, so you will receive an immediate response.

Endpoint: POST /upload

Request Body: multipart/form-data with a file key.

Example using curl:

Bash
curl -X POST -F "file=@/path/to/your/dummy_transactions.csv" [http://127.0.0.1:8000/upload](http://127.0.0.1:8000/upload)
Success Response (200 OK):

JSON
{
  "message": "File 'dummy_transactions.csv' accepted and is being processed in the background."
}
2. Get User Summary

Returns summary statistics for a given user within a specified date range.

Endpoint: GET /summary/{user_id}

Path Parameter: user_id (integer)

Query Parameters:

start_date (string, YYYY-MM-DD)

end_date (string, YYYY-MM-DD)

Example using curl:

Bash
curl "[http://127.0.0.1:8000/summary/123?start_date=2025-01-01&end_date=2025-12-31](http://127.0.0.1:8000/summary/123?start_date=2025-01-01&end_date=2025-12-31)"
Success Response (200 OK):

JSON
{
  "user_id": 123,
  "max_transaction": 495.5,
  "min_transaction": 10.25,
  "mean_transaction": 251.73
}
Error Response (404 Not Found):
If no transactions are found for the user in the given range.

JSON
{
  "detail": "No transactions found for user in the given date range."
}
Running the Tests
The project includes a comprehensive test suite. To run the tests, execute the following command from the root directory:

Bash
pytest -v
The tests run against a clean, in-memory SQLite database to ensure isolation and speed.

Design Choices and Key Decisions 🧠
Framework Choice (FastAPI): I chose FastAPI for its high performance, native async support, and automatic generation of interactive API documentation (Swagger UI), which is excellent for development and testing.

Handling Large Files: To meet the requirement of handling large datasets efficiently, I implemented a chunking strategy. The /upload endpoint reads the CSV file in smaller chunks using pandas, ensuring that the server's memory usage remains low and constant, regardless of the file size.

Concurrency (BackgroundTasks): Data processing and database insertion can be time-consuming. I used FastAPI's BackgroundTasks to offload this work. This allows the API to immediately respond to the client's upload request, creating a non-blocking, responsive user experience.

Database and ORM (SQLite & SQLAlchemy): For the scope of this challenge, SQLite is a simple and effective file-based database that requires no separate server setup. I used SQLAlchemy as the ORM for its powerful engine and connection management, which allows for robust, backend-agnostic database interactions. An index was added to the (user_id, timestamp) columns to ensure that summary queries remain fast even with millions of rows.

Testing Strategy: The tests are designed to be independent and fast. Using an in-memory SQLite database for the test suite ensures that tests don't interfere with each other or require a persistent database file. The dependency injection system in FastAPI was used to seamlessly swap the production database engine with the test engine.