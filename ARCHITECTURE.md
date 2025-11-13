# LSTM Temperature Forecasting API - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                   LSTM Temperature Forecast API                  │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐
│   Client     │────▶│   FastAPI    │────▶│  LSTM Model          │
│ (curl/Python)│     │   Server     │     │  (lstm_best.h5)      │
└──────────────┘     └──────────────┘     └──────────────────────┘
                            │
                            │ loads
                            ▼
                     ┌──────────────┐     ┌──────────────────────┐
                     │  Scaler      │     │  Metadata            │
                     │  (.pkl)      │     │  (.json)             │
                     └──────────────┘     └──────────────────────┘
```

## Request Flow

### 1. Client Request
```
POST /forecast
{
  "recent_temps": [20.1, 21.3, ..., 22.5],  // 168 hourly temps
  "steps": 24                                // Forecast 24 hours
}
```

### 2. Server Processing
```
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Validate Input (Pydantic)                                   │
│     ├─ Check array length ≥ 168                                 │
│     ├─ Validate temperature range (-20°C to 60°C)               │
│     └─ Validate steps (1-168)                                   │
│                                                                  │
│  2. Prepare Sequence (sequence_utils.py)                        │
│     ├─ Extract last 168 values                                  │
│     ├─ Scale using MinMaxScaler                                 │
│     └─ Reshape to (1, 168, 1)                                   │
│                                                                  │
│  3. Iterative Forecasting                                       │
│     For each step (1 to N):                                     │
│       ├─ Predict next value using LSTM                          │
│       ├─ Inverse scale to get actual temperature                │
│       ├─ Append to forecasts list                               │
│       └─ Feed prediction back into window for next step         │
│                                                                  │
│  4. Return Response                                             │
│     {                                                            │
│       "forecasts": [23.5, 24.1, ...],                          │
│       "steps": 24,                                              │
│       "sequence_length": 168                                    │
│     }                                                            │
└─────────────────────────────────────────────────────────────────┘
```

## Multi-Step Forecasting

The API uses **iterative prediction** for multi-step forecasting:

```
Initial Window (168 hours):
[t-167, t-166, ..., t-1, t-0]
         ↓
    LSTM Model
         ↓
   Prediction: t+1

Updated Window (168 hours):
[t-166, t-165, ..., t-0, t+1]
         ↓
    LSTM Model
         ↓
   Prediction: t+2

... and so on for N steps
```

## Component Details

### 1. FastAPI Application (`app.py`)
- **Startup**: Loads model, scaler, and metadata
- **Endpoints**:
  - `GET /` - API information
  - `GET /health` - Health check
  - `POST /forecast` - Temperature forecasting
- **Features**:
  - Auto-generated docs at `/docs`
  - Request/response validation
  - Error handling

### 2. Sequence Utilities (`sequence_utils.py`)
- `load_metadata()` - Load model configuration
- `load_scaler()` - Load MinMaxScaler
- `prepare_input_window()` - Scale and reshape input
- `iterative_forecast()` - Multi-step prediction
- `validate_input_length()` - Input validation

### 3. Model Metadata (`metadata.json`)
```json
{
  "sequence_length": 168,
  "features": ["temp_c"],
  "target": "temp_c",
  "scaling_method": "MinMaxScaler",
  "model_type": "LSTM"
}
```

### 4. Test Suite (`test_request.py`)
- Health check test
- Root endpoint test
- Forecast test (24h, 168h)
- Error handling test
- Generates synthetic test data

## Deployment Options

### Option 1: Local Python
```bash
pip install -r requirements.txt
python scripts/inference/app.py
# Access: http://localhost:8000
```

### Option 2: Docker
```bash
docker build -t lstm-forecast-api .
docker run -p 8000:8000 lstm-forecast-api
# Access: http://localhost:8000
```

### Option 3: docker-compose
```bash
docker-compose up lstm-forecast-api
# Access: http://localhost:8000
# Also starts other services (postgres, mlflow, etc.)
```

### Option 4: GitHub Container Registry
```bash
docker pull ghcr.io/yosrcharrada/lstm-forecast-api:latest
docker run -p 8000:8000 ghcr.io/yosrcharrada/lstm-forecast-api:latest
```

## CI/CD Pipeline

```
┌──────────────┐
│ Git Push to  │
│    main      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ GitHub       │
│ Actions      │
│ Workflow     │
└──────┬───────┘
       │
       ├─ Checkout code
       ├─ Login to GHCR
       ├─ Build Docker image
       └─ Push to GHCR
       
┌──────────────────────────────────┐
│ ghcr.io/yosrcharrada/           │
│   lstm-forecast-api:latest       │
└──────────────────────────────────┘
```

## Data Flow

```
ERA5 Climate Data
       │
       ▼
┌──────────────┐
│ preprocess.py│
│ (NetCDF→CSV) │
└──────┬───────┘
       │
       ▼
┌─────────────────────┐
│ temperature_hourly  │
│      .csv           │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Training Notebook   │
│ 04_DL_Forecasting   │
└──────┬──────────────┘
       │
       ├─▶ lstm_best.h5
       ├─▶ temp_scaler.pkl
       └─▶ (metrics logged to MLflow)
       
┌─────────────────────┐
│ Inference API       │
│ uses model + scaler │
└─────────────────────┘
```

## Error Handling

The API handles several error cases:

1. **Insufficient Data**
   - Status: 400 Bad Request
   - Message: "Insufficient data: need at least 168 values, got X"

2. **Invalid Temperature Range**
   - Status: 422 Unprocessable Entity
   - Message: "Temperature values seem unrealistic"

3. **Invalid Steps**
   - Status: 422 Unprocessable Entity
   - Message: "steps must be between 1 and 168"

4. **Model Not Loaded**
   - Status: 503 Service Unavailable
   - Message: "Model or scaler not loaded"

5. **Prediction Error**
   - Status: 500 Internal Server Error
   - Message: "Prediction failed: <error details>"

## Performance Considerations

- **Inference Time**: ~10-50ms per prediction (CPU)
- **Memory**: ~500MB (model + scaler + FastAPI)
- **Concurrent Requests**: Handled by uvicorn workers
- **Scaling**: Deploy multiple containers behind load balancer

## Security Features

- ✅ Input validation via Pydantic
- ✅ No arbitrary code execution
- ✅ Numeric inputs only
- ✅ Request size limits (max 168 steps)
- ✅ No external dependencies during inference
- ✅ Read-only model files

## Monitoring & Observability

Future enhancements:
- Add Prometheus metrics endpoint
- Log predictions to MLflow
- Add request/response logging
- Add performance metrics (latency, throughput)
- Add error rate monitoring

## Extension Points

The architecture supports future enhancements:

1. **Additional Models**
   - Add SARIMA endpoint
   - Add DUQ uncertainty quantification
   - Ensemble predictions

2. **Authentication**
   - API key support
   - JWT tokens
   - Rate limiting

3. **Batch Processing**
   - Batch prediction endpoint
   - Async job processing
   - Result caching

4. **Model Versioning**
   - A/B testing
   - Gradual rollout
   - Model registry integration
