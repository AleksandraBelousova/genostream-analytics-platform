CREATE DATABASE IF NOT EXISTS genostream;
CREATE TABLE IF NOT EXISTS genostream.gene_expression
(
    `cell_barcode`     String,
    `gene_name`        String,
    `expression_value` Float32,
    `patient_id`       String,
    `cell_type`        LowCardinality(String)
)
ENGINE = MergeTree()
PARTITION BY patient_id
ORDER BY (cell_type, gene_name, cell_barcode);