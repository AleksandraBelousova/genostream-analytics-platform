from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field, constr
from typing import List, Dict, Any
from starlette.concurrency import run_in_threadpool
import pandas as pd

from .db_client import get_db_session, Client 
app = FastAPI(
    title="GenoStream Analytics API",
    description="High-performance, asynchronous API for advanced single-cell analytics.",
    version="2.0.0",
)

class ExpressionQuery(BaseModel):
    gene_names: List[constr(strip_whitespace=True, min_length=1)] = Field(..., example=["EPCAM", "KRT18"])
    cell_types: List[constr(strip_whitespace=True, min_length=1)] = Field(..., example=["Epithelial"])

class GeneVariabilityQuery(BaseModel):
    cell_type: str = Field(..., example="Epithelial")
    limit: int = Field(10, gt=0, le=100)

class GeneVariabilityStat(BaseModel):
    gene: str
    mean_expression: float
    stddev: float
    cv: float 

class GeneCorrelationQuery(BaseModel):
    gene_a: str = Field(..., example="EPCAM")
    gene_b: str = Field(..., example="KRT18")
    cell_types: List[str] = Field(..., min_length=1, example=["Epithelial"])

class GeneCorrelation(BaseModel):
    gene_a: str
    gene_b: str
    cell_types: List[str]
    pearson_correlation: float
    observation_count: int

class GeneAnalyticsRepository:
    async def get_expression_matrix(self, client: Client, query: ExpressionQuery) -> Dict:
        sql = """
        SELECT cell_barcode, gene_name, expression_value
        FROM gene_expression
        WHERE gene_name IN %(gene_names)s AND cell_type IN %(cell_types)s
        """
        data, cols = await run_in_threadpool(client.execute, sql, params=query.model_dump(), with_column_types=True)
        df = pd.DataFrame(data, columns=[c[0] for c in cols])
        return df.to_dict(orient='split')

    async def get_gene_variability(self, client: Client, query: GeneVariabilityQuery) -> List[Dict]:
        sql = """
        SELECT
            gene_name,
            avg(expression_value) AS mean_expr,
            stddevPop(expression_value) AS std_expr,
            if(mean_expr > 0, std_expr / mean_expr, 0) AS cv
        FROM gene_expression
        WHERE cell_type = %(cell_type)s
        GROUP BY gene_name
        ORDER BY cv DESC
        LIMIT %(limit)s
        """
        result = await run_in_threadpool(client.execute, sql, params=query.model_dump())
        return [{"gene": r[0], "mean_expression": r[1], "stddev": r[2], "cv": r[3]} for r in result]
        
    async def get_gene_correlation(self, client: Client, query: GeneCorrelationQuery) -> Dict:
        sql = """
        SELECT
            if(
                isFinite(corr(
                    if(gene_name = %(gene_a)s, expression_value, 0),
                    if(gene_name = %(gene_b)s, expression_value, 0)
                )),
                corr(
                    if(gene_name = %(gene_a)s, expression_value, 0),
                    if(gene_name = %(gene_b)s, expression_value, 0)
                ),
                0.0
            ) as correlation,
            count(DISTINCT cell_barcode) as cell_count
        FROM gene_expression
        WHERE cell_type IN %(cell_types)s
          AND gene_name IN (%(gene_a)s, %(gene_b)s)
        """
        result = await run_in_threadpool(client.execute, sql, params=query.model_dump())
        
        if not result:
             raise HTTPException(status_code=404, detail="Could not compute correlation. No matching cells found.")
        
        return {
            "gene_a": query.gene_a, "gene_b": query.gene_b, "cell_types": query.cell_types,
            "pearson_correlation": float(result[0][0]),
            "observation_count": int(result[0][1])
        }

@app.post("/expression-matrix", tags=["Data Retrieval"])
async def query_expression(
    query: ExpressionQuery,
    repo: GeneAnalyticsRepository = Depends()
):
    try:
        with get_db_session() as client:
            return await repo.get_expression_matrix(client, query)
    except Exception as e:
        raise HTTPException(status_code=500,
                            el=List[GeneVariabilityStat], tags=["Analytics"])
async def get_gene_variability(
    query: GeneVariabilityQuery,
    repo: GeneAnalyticsRepository = Depends()
):
    try:
        with get_db_session() as client:
            return await repo.get_gene_variability(client, query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gene-correlation", response_model=GeneCorrelation, tags=["Analytics"])
async def get_gene_correlation(
    query: GeneCorrelationQuery,
    repo: GeneAnalyticsRepository = Depends()
):
    try:
        with get_db_session() as client:
            return await repo.get_gene_correlation(client, query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", status_code=status.HTTP_200_OK, tags=["System"])
async def health_check():
    try:
        with get_db_session() as client:
            ok = await run_in_threadpool(client.execute, "SELECT 1")
            if ok and ok[0][0] == 1:
                return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Database is unreachable: {e}")