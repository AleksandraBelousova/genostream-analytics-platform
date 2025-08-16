
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
