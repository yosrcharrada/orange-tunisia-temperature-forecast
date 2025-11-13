# Orange Tunisia Temperature Forecasting

This repository contains time series forecasting models for temperature prediction in Tunisia using ERA5 climate data. It includes data preprocessing, statistical models (SARIMA, Prophet), deep learning models (LSTM, GRU, Transformer), and a production-ready REST API for LSTM-based hourly temperature forecasting.

## Features

- **Data Processing**: ERA5 NetCDF data preprocessing to hourly temperature time series
- **Statistical Models**: SARIMA and Prophet forecasting
- **Deep Learning Models**: LSTM, GRU, and Transformer architectures
- **Production API**: FastAPI-based REST API for real-time temperature forecasting
- **MLflow Integration**: Experiment tracking and model versioning
- **Docker Support**: Containerized deployment with Docker and docker-compose
- **CI/CD**: GitHub Actions workflow for automated Docker image building

## Project Structure

```
.
├── scripts/
│   ├── models/
│   │   ├── lstm_best.h5          # Trained LSTM model
│   │   ├── metadata.json         # Model configuration and metadata
│   │   └── temp_scaler.pkl       # MinMaxScaler (must be generated)
│   ├── inference/
│   │   ├── app.py                # FastAPI application
│   │   ├── sequence_utils.py     # Inference utilities
│   │   └── test_request.py       # API test script
│   ├── preprocess.py             # Data preprocessing
│   └── *.ipynb                   # Training notebooks
├── data/                         # Data directory
├── jobs/                         # ETL jobs
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container definition
└── docker-compose.yml            # Multi-service orchestration
```

## Quick Start

### Prerequisites

- Python 3.10+
- Docker and docker-compose (optional, for containerized deployment)
- Trained LSTM model (`scripts/models/lstm_best.h5`)
- Scaler file (`scripts/models/temp_scaler.pkl`)

### Generate Scaler File

⚠️ **Important**: Before running the API, you must generate the scaler file from your training notebook:

```python
# In your training notebook (e.g., scripts/04_DL_Forecasting.ipynb)
# After training and creating the scaler:

import joblib
joblib.dump(scaler, "scripts/models/temp_scaler.pkl")
```

The scaler must be the same MinMaxScaler instance used during model training to ensure correct preprocessing.

## Running the API

### Option 1: Local Python Environment

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify scaler exists**:
   ```bash
   ls -la scripts/models/temp_scaler.pkl
   ```

3. **Start the API**:
   ```bash
   python scripts/inference/app.py
   ```

4. **Access the API**:
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

### Option 2: Docker

1. **Build the Docker image**:
   ```bash
   docker build -t lstm-forecast-api .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8000:8000 lstm-forecast-api
   ```

### Option 3: Docker Compose

The LSTM forecast API is integrated into the existing docker-compose setup:

```bash
# Start only the LSTM API
docker-compose up lstm-forecast-api

# Or start all services
docker-compose up
```

## API Usage

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "sequence_length": 168,
  "model_type": "LSTM",
  "scaler_loaded": true
}
```

### Temperature Forecast

**Endpoint**: `POST /forecast`

**Request Body**:
```json
{
  "recent_temps": [20.5, 21.0, 22.3, ...],  // Minimum 168 hourly values
  "steps": 24                                 // Number of hours to forecast (1-168)
}
```

**Example using curl**:
```bash
curl -X POST http://localhost:8000/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "recent_temps": [20.5, 21.0, 22.3, ...],
    "steps": 24
  }'
```

**Example using Python**:
```python
import requests

# Prepare recent temperature data (minimum 168 hourly values)
recent_temps = [20.5, 21.0, 22.3, ...]  # Your actual temperature data

response = requests.post(
    "http://localhost:8000/forecast",
    json={
        "recent_temps": recent_temps,
        "steps": 24  # Forecast next 24 hours
    }
)

result = response.json()
forecasts = result["forecasts"]
print(f"Forecasted temperatures: {forecasts}")
```

**Response**:
```json
{
  "forecasts": [23.5, 24.1, 24.8, ...],
  "steps": 24,
  "sequence_length": 168
}
```

### Testing the API

A test script is provided to verify the API functionality:

```bash
# Make sure the API is running first
python scripts/inference/test_request.py
```

This will run a comprehensive test suite including:
- Health check endpoint
- Root endpoint
- Forecast with various time horizons
- Error handling validation

## Model Details

### LSTM Architecture

- **Input**: Last 168 hours (1 week) of temperature data
- **Preprocessing**: MinMaxScaler normalization to [0, 1]
- **Architecture**: Multi-layer LSTM with dropout
- **Output**: Single-step prediction (can be iteratively extended)
- **Multi-step Forecasting**: Uses iterative prediction (feeding predictions back as input)

### Sequence Length

The model uses a **168-hour lookback window** (1 week of hourly data). This means:
- You must provide at least 168 recent hourly temperature values
- The model uses the last 168 values to make predictions
- Multi-step forecasts are generated by iteratively feeding predictions back into the model

### Forecast Horizon

- **Minimum**: 1 hour
- **Maximum**: 168 hours (1 week)
- Forecasts are generated iteratively, so longer horizons may accumulate error

## Development

### Training Models

The training notebooks are located in `scripts/`:
- `04_DL_Forecasting.ipynb`: Deep learning models (LSTM, GRU, Transformer)
- `03_Stat_Modeling.ipynb`: Statistical models (SARIMA)
- `05_Prophet_Forecasting.ipynb`: Prophet forecasting

### Data Preprocessing

Use `scripts/preprocess.py` to process ERA5 NetCDF files into hourly CSV format.

## CI/CD

The repository includes a GitHub Actions workflow (`.github/workflows/deploy.yml`) that:
- Builds the Docker image on pushes to `main`
- Pushes the image to GitHub Container Registry (GHCR)
- Tags with `latest` and commit SHA

To use the published image:
```bash
docker pull ghcr.io/yosrcharrada/lstm-forecast-api:latest
docker run -p 8000:8000 ghcr.io/yosrcharrada/lstm-forecast-api:latest
```

## Troubleshooting

### "Scaler file not found" Error

**Problem**: The API fails to start with a FileNotFoundError for `temp_scaler.pkl`.

**Solution**: Generate the scaler file from your training notebook:
```python
import joblib
joblib.dump(scaler, "scripts/models/temp_scaler.pkl")
```

### Insufficient Data Error

**Problem**: API returns HTTP 400 "Insufficient data".

**Solution**: Ensure you provide at least 168 hourly temperature values in the `recent_temps` array.

### Model Loading Error

**Problem**: API fails to load the LSTM model.

**Solution**: 
- Verify `scripts/models/lstm_best.h5` exists
- Check TensorFlow version compatibility (2.16.1 recommended)
- Ensure the model was saved correctly during training

## Future Enhancements

- ✨ Add SARIMA endpoint for statistical forecasting
- ✨ Include uncertainty quantification (DUQ model)
- ✨ Add authentication (API key support)
- ✨ Implement rate limiting
- ✨ Add MLflow logging for inference metrics
- ✨ Support batch predictions

## License

This project is part of Orange Tunisia's climate forecasting initiative.

## Contributing

For questions or contributions, please contact the maintainers.
