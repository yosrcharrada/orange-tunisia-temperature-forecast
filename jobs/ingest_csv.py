import os
import argparse
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "timeseriesdb"),
        user=os.getenv("DB_USER", "mlapp"),
        password=os.getenv("DB_PASSWORD", "mlapp"),
    )

def upsert_raw(df: pd.DataFrame):
    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"], infer_datetime_format=True, utc=False)
    rows = list(df[["datetime", "temp_c"]].itertuples(index=False, name=None))
    sql = """
        INSERT INTO raw_data(datetime, temp_c)
        VALUES %s
        ON CONFLICT (datetime) DO UPDATE SET temp_c = EXCLUDED.temp_c
    """
    with get_conn() as conn, conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=10000)
        conn.commit()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="CSV with columns: datetime,temp_c")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    if not {"datetime", "temp_c"}.issubset(df.columns):
        raise ValueError("CSV must contain columns: datetime,temp_c")
    upsert_raw(df)
    print(f"Ingested {len(df)} rows into raw_data.")