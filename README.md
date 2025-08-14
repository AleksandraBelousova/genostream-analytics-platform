
![python-badge](https://img.shields.io/badge/Python-3.9-3776AB.svg?style=for-the-badge&logo=python)


![fastapi-badge](https://img.shields.io/badge/FastAPI-0.100-009688.svg?style=for-the-badge&logo=fastapi)


![clickhouse-badge](https://img.shields.io/badge/ClickHouse-23.8-FFCC01.svg?style=for-the-badge&logo=clickhouse)


![docker-badge](https://img.shields.io/badge/Docker-24.0-2496ED.svg?style=for-the-badge&logo=docker)

A containerised OLAP system for querying scRNA-seq data. The system features a Python ETL pipeline that processes .mtx sparse matrices, joins cell metadata, and ingests tidy data into a ClickHouse database. An asynchronous FastAPI service exposes endpoints for data subsetting and server-side aggregations (e.g., Pearson correlation). The stack is orchestrated via Docker Compose.

Functionality

Database: Stores scRNA-seq data in a columnar ClickHouse database using a tidy schema (cell, gene, value, patient, cell_type).

ETL: Ingests data from sparse Matrix Market (.mtx), barcode (.tsv), and gene (.tsv) file formats.

API: Exposes data through an asynchronous FastAPI backend.

Analytics: Provides endpoints for server-side calculations, including Pearson correlation and coefficient of variation.

Architecture
code
Code
download
content_copy
expand_less

┌──────────────────┐     ┌──────────────────────┐     ┌───────────────────┐     ┌─────────────────┐
│   Data Sources   │────▶│   ETL Pipeline     │────▶│  ClickHouse DB  │◀───▶│   FastAPI API   │
│ (Broad Institute)│     │ (Python, Scipy, Pandas)│     │   (OLAP Storage)  │     │ (Data Endpoints)│
└──────────────────┘     └──────────────────────┘     └───────────────────┘     └─────────────────┘
Tech Stack
Component	Technology / Library
Database	ClickHouse
API Framework	FastAPI
Data Ingestion	Python, Pandas, Scipy, clickhouse-driver
Containerization	Docker, Docker Compose
Configuration	Pydantic, python-dotenv
Setup and Deployment
Prerequisites

Docker & Docker Compose

Git

Python 3.9+

1. Clone the Repository
code
Bash
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
git clone https://github.com/AleksandraBelousova/genostream-analytics-platform.git
cd genostream-analytics-platform
2. Configure Environment

The system uses a .env file for configuration. Create one from the provided example.

code
Bash
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
# In the project root, create a file named .env with the following content:
# API_PORT=8000
# CLICKHOUSE_PORT_HTTP=8123
# CLICKHOUSE_PORT_NATIVE=9000
# CLICKHOUSE_DB=genostream
# CLICKHOUSE_USER=user
# CLICKHOUSE_PASSWORD=your_very_secret_password

(You can copy the content above and save it as .env)

3. Data Acquisition

The ETL pipeline requires four specific files from the Broad Institute's Single Cell Portal.

Navigate to the study download page: SCP259 Download

Download the following four files into the data/external/ directory:

All.meta2.txt

Epi.barcodes2.tsv

Epi.genes.tsv

gene_sorted-Epi.matrix.mtx

4. Launch the System

This command builds the API image and starts the ClickHouse and API containers.

code
Bash
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
docker-compose up --build

Wait for the log message INFO: Uvicorn running on http://0.0.0.0:8000. Keep this terminal running.

5. Run the ETL Pipeline

Open a new terminal and execute the following commands:

code
Bash
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
# Install required Python packages for the script
pip install -r requirements.txt scipy

# Run the ingestion script
python src/ingestion/pipeline.py

Wait for the --- ETL Process Finished --- message.

API Usage

The API is accessible while the Docker containers are running.

Interactive Documentation

API endpoints can be tested through the Swagger UI:

▶️ http://localhost:8000/docs

curl Examples
Get Gene Correlation
code
Bash
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
curl -X 'POST' \
  'http://localhost:8000/gene-correlation' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "gene_a": "EPCAM",
  "gene_b": "KRT18",
  "cell_types": [
    "Epithelial"
  ]
}'
Get Gene Variability
code
Bash
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
curl -X 'POST' \
  'http://localhost:8000/gene-variability' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "cell_type": "Epithelial",
  "limit": 5
}'
