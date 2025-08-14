import os
import pandas as pd
from scipy.io import mmread
from pathlib import Path
from clickhouse_driver import Client
from dotenv import load_dotenv

load_dotenv()

class MtxIngestionPipeline:
    DATA_DIR = Path("data/external")
    MATRIX_PATH = DATA_DIR / "gene_sorted-Epi.matrix.mtx"
    BARCODES_PATH = DATA_DIR / "Epi.barcodes2.tsv"
    GENES_PATH = DATA_DIR / "Epi.genes.tsv"
    METADATA_PATH = DATA_DIR / "All.meta2.txt"
    SCHEMA_PATH = Path("src/database/schema.sql")
    BATCH_SIZE = 500_000
    def __init__(self):
        self.client = Client(host="localhost", port=os.getenv("CLICKHOUSE_PORT_NATIVE"), user=os.getenv("CLICKHOUSE_USER"), password=os.getenv("CLICKHOUSE_PASSWORD"))
        self.db_name = os.getenv("CLICKHOUSE_DB")
        self.table_name = "gene_expression"
    def _ensure_schema_exists(self):
        print("[1] Ensuring database schema exists...")
        with open(self.SCHEMA_PATH) as f:
            queries = f.read().split(';')
            for query in queries:
                if query.strip():
                    self.client.execute(query)
        print("    -> Schema is ready.")

    def _load_ancillary_data(self):
        print("    -> Loading barcodes, genes, and metadata...")
        barcodes = pd.read_csv(self.BARCODES_PATH, sep='\t', header=None)[0].to_list()
        genes = pd.read_csv(self.GENES_PATH, sep='\t', header=None)[0].to_list()
        
        metadata = pd.read_csv(self.METADATA_PATH, sep="\t", header=0, dtype=str)
        metadata.columns = metadata.columns.str.strip()
        metadata = metadata.set_index('NAME')[['Cluster', 'Subject']].rename(columns={'Subject': 'patient_id', 'Cluster': 'cell_type'})
        return barcodes, genes, metadata.dropna(subset=['cell_type'])
    
    def run(self):
        print("--- Starting Gene Expression ETL (Robust Mode) ---")
        self._ensure_schema_exists() 
        print("[2] Loading auxiliary data...")
        barcodes, genes, metadata = self._load_ancillary_data() 
        print(f"[3] Reading sparse expression matrix '{self.MATRIX_PATH.name}'...")
        matrix = mmread(self.MATRIX_PATH).tocoo()
        print(f"[4] Preparing target table '{self.table_name}'...")
        self.client.execute(f'TRUNCATE TABLE {self.db_name}.{self.table_name}')  
        print(f"[5] Processing and ingesting {len(matrix.data):,} non-zero expression values...")
        batch = []
        total_rows_ingested = 0 
        query = f'INSERT INTO {self.db_name}.{self.table_name} VALUES'
        for r, c, value in zip(matrix.row, matrix.col, matrix.data):
            batch.append({'cell_barcode': barcodes[c], 'gene_name': genes[r], 'expression_value': float(value)})
            if len(batch) >= self.BATCH_SIZE:
                batch_df = pd.DataFrame(batch).merge(metadata, left_on='cell_barcode', right_index=True, how='inner')
                if not batch_df.empty:
                    data_to_insert = batch_df.to_dict('records')
                    self.client.execute(query, data_to_insert, types_check=True)
                    total_rows_ingested += len(batch_df)
                print(f"    ...ingested {total_rows_ingested:,} rows...")
                batch.clear()  
        if batch:
            batch_df = pd.DataFrame(batch).merge(metadata, left_on='cell_barcode', right_index=True, how='inner')
            if not batch_df.empty:
                data_to_insert = batch_df.to_dict('records')
                self.client.execute(query, data_to_insert, types_check=True)
                total_rows_ingested += len(batch_df)

        print("\n--- ETL Process Finished ---")
        print(f"Total Rows Ingested: {total_rows_ingested:,}")
if __name__ == "__main__":
    MtxIngestionPipeline().run()