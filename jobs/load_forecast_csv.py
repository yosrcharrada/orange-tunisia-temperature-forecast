import os
import argparse
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dateutil import parser as dateparser

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "timeseriesdb"),
        user=os.getenv("DB_USER", "mlapp"),
        password=os.getenv("DB_PASSWORD", "mlapp"),
    )

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Forecast CSV path")
    ap.add_argument("--model-name", required=True)
    ap.add_argument("--forecast-time", default=None, help="ISO timestamp when the forecast was generated (default: now UTC)")
    ap.add_argument("--ts-col", default="ts")
    ap.add_argument("--yhat-col", default="yhat")
    ap.add_argument("--yhat-lower-col", default="yhat_lower")
    ap.add_argument("--yhat-upper-col", default="yhat_upper")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)

    req = {args.ts_col, args.yhat_col}
    if not req.issubset(df.columns):
        raise ValueError(f"CSV must have at least columns: {args.ts_col},{args.yhat_col}")

    rename_map = {}
    if args.ts_col in df.columns: rename_map[args.ts_col] = "ts"
    if args.yhat_col in df.columns: rename_map[args.yhat_col] = "yhat"
    if args.yhat_lower_col in df.columns and args.yhat_lower_col in df: rename_map[args.yhat_lower_col] = "yhat_lower"
    if args.yhat_upper_col in df.columns and args.yhat_upper_col in df: rename_map[args.yhat_upper_col] = "yhat_upper"
    df = df.rename(columns=rename_map)
    df["ts"] = pd.to_datetime(df["ts"], utc=True, infer_datetime_format=True)

    keep = ["ts", "yhat"]
    if "yhat_lower" in df.columns: keep.append("yhat_lower")
    if "yhat_upper" in df.columns: keep.append("yhat_upper")
    df = df[keep]

    if args.forecast_time is None:
        forecast_time = pd.Timestamp.utcnow()
    else:
        forecast_time = pd.Timestamp(dateparser.parse(args.forecast_time), tz='UTC')

    rows = []
    for r in df.itertuples(index=False):
        ts = r[0].to_pydatetime()
        yhat = float(r[1])
        yhat_lower = float(r[2]) if "yhat_lower" in df.columns and len(r) > 2 and pd.notna(r[2]) else None
        yhat_upper = float(r[3]) if "yhat_upper" in df.columns and len(r) > 3 and pd.notna(r[3]) else None
        rows.append((args.model_name, forecast_time.to_pydatetime(), ts, yhat, yhat_lower, yhat_upper))

    sql = """
      INSERT INTO forecasts (model_name, forecast_time, ts, yhat, yhat_lower, yhat_upper)
      VALUES %s
      ON CONFLICT (model_name, forecast_time, ts) DO UPDATE
      SET yhat = EXCLUDED.yhat,
          yhat_lower = COALESCE(EXCLUDED.yhat_lower, forecasts.yhat_lower),
          yhat_upper = COALESCE(EXCLUDED.yhat_upper, forecasts.yhat_upper)
    """
    with get_conn() as conn, conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=10000)
        conn.commit()

    print(f"Upserted {len(rows)} rows for model={args.model_name} at forecast_time={forecast_time.isoformat()}.")