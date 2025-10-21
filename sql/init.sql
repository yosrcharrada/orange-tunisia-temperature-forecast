-- Runs once (when the pgdata volume is new)

-- Ensure app user
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'mlapp') THEN
    CREATE USER mlapp WITH PASSWORD 'mlapp';
  END IF;
END$$;

-- Create application DB for Grafana data
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'timeseriesdb') THEN
    CREATE DATABASE timeseriesdb OWNER postgres;
  END IF;
END$$;

\connect timeseriesdb;

CREATE TABLE IF NOT EXISTS raw_data (
  datetime    timestamptz PRIMARY KEY,
  temp_c      double precision NOT NULL
);

CREATE TABLE IF NOT EXISTS forecasts (
  model_name      text NOT NULL,
  forecast_time   timestamptz NOT NULL,
  ts              timestamptz NOT NULL,
  yhat            double precision NOT NULL,
  yhat_lower      double precision,
  yhat_upper      double precision,
  created_at      timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (model_name, forecast_time, ts)
);

CREATE TABLE IF NOT EXISTS metrics (
  run_id        text NOT NULL,
  model_name    text NOT NULL,
  split         text DEFAULT 'test',
  metric_name   text NOT NULL,
  metric_value  double precision NOT NULL,
  logged_at     timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (run_id, metric_name)
);

GRANT ALL PRIVILEGES ON DATABASE timeseriesdb TO mlapp;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mlapp;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mlapp;