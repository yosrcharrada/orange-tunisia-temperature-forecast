"""
FastAPI application for LSTM temperature forecasting.
Provides REST API endpoints for health checks and multi-step forecasting.
"""
import sys
from pathlib import Path
from typing import List

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import tensorflow as tf

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from inference.sequence_utils import (
    load_metadata,
    load_scaler,
    prepare_input_window,
    iterative_forecast,
    validate_input_length
)


# ==================== Pydantic Schemas ====================

class ForecastRequest(BaseModel):
    """Request schema for temperature forecasting."""
    recent_temps: List[float] = Field(
        ...,
        description="List of recent hourly temperatures (minimum 168 values)",
        min_items=168
    )
    steps: int = Field(
        default=24,
        description="Number of hours to forecast (1-168)",
        ge=1,
        le=168
    )
    
    @validator('recent_temps')
    def validate_temps(cls, v):
        """Validate temperature values are reasonable."""
        if not all(isinstance(temp, (int, float)) for temp in v):
            raise ValueError("All temperature values must be numeric")
        # Basic sanity check: reasonable temperature range for Tunisia
        if not all(-20 <= temp <= 60 for temp in v):
            raise ValueError(
                "Temperature values seem unrealistic (expected range: -20°C to 60°C)"
            )
        return v


class ForecastResponse(BaseModel):
    """Response schema for temperature forecasting."""
    forecasts: List[float] = Field(
        ...,
        description="List of forecasted temperatures"
    )
    steps: int = Field(
        ...,
        description="Number of steps forecasted"
    )
    sequence_length: int = Field(
        ...,
        description="Lookback window length used"
    )


class HealthResponse(BaseModel):
    """Response schema for health check."""
    status: str
    model_loaded: bool
    sequence_length: int
    model_type: str
    scaler_loaded: bool


# ==================== FastAPI Application ====================

app = FastAPI(
    title="LSTM Temperature Forecast API",
    description="Production API for hourly temperature forecasting using LSTM",
    version="1.0.0"
)

# Global variables for model and scaler
model = None
scaler = None
metadata = None


@app.on_event("startup")
async def startup_event():
    """Load model and scaler on startup."""
    global model, scaler, metadata
    
    try:
        # Load metadata
        metadata = load_metadata()
        print(f"✓ Loaded metadata: {metadata['model_type']} model")
        
        # Load scaler
        scaler = load_scaler()
        print(f"✓ Loaded scaler: {metadata['scaling_method']}")
        
        # Load LSTM model
        model_path = Path(__file__).parent.parent / "models" / "lstm_best.h5"
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at {model_path}")
        
        # Load model without compilation (inference only)
        model = tf.keras.models.load_model(str(model_path), compile=False)
        print(f"✓ Loaded LSTM model from {model_path}")
        
        print("\n" + "="*50)
        print("🚀 LSTM Temperature Forecast API is ready!")
        print(f"   Sequence length: {metadata['sequence_length']} hours")
        print(f"   Model type: {metadata['model_type']}")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        raise


@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint with usage information."""
    return {
        "message": "LSTM Temperature Forecast API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health (GET)",
            "forecast": "/forecast (POST)"
        },
        "usage": {
            "forecast": {
                "method": "POST",
                "url": "/forecast",
                "body": {
                    "recent_temps": "List of ≥168 hourly temperatures",
                    "steps": "Number of hours to forecast (1-168)"
                }
            }
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Returns model status and configuration.
    """
    if model is None or scaler is None or metadata is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model or scaler not loaded"
        )
    
    return HealthResponse(
        status="healthy",
        model_loaded=model is not None,
        sequence_length=metadata['sequence_length'],
        model_type=metadata['model_type'],
        scaler_loaded=scaler is not None
    )


@app.post("/forecast", response_model=ForecastResponse)
async def forecast_temperature(request: ForecastRequest):
    """
    Generate multi-step temperature forecast.
    
    Accepts a sequence of recent hourly temperatures and returns
    forecasted temperatures for the next N hours using iterative prediction.
    
    Args:
        request: ForecastRequest with recent_temps and steps
        
    Returns:
        ForecastResponse with forecasted values
        
    Raises:
        HTTPException: If model not loaded or input validation fails
    """
    if model is None or scaler is None or metadata is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model or scaler not loaded"
        )
    
    try:
        # Validate input length
        seq_length = metadata['sequence_length']
        is_valid, error_msg = validate_input_length(request.recent_temps, seq_length)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Prepare input window
        input_window = prepare_input_window(
            request.recent_temps,
            scaler,
            seq_length
        )
        
        # Generate forecasts
        forecasts = iterative_forecast(
            model,
            input_window,
            scaler,
            request.steps
        )
        
        return ForecastResponse(
            forecasts=forecasts,
            steps=request.steps,
            sequence_length=seq_length
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


if __name__ == "__main__":
    """Run the API server."""
    print("Starting LSTM Temperature Forecast API server...")
    print("Access the API at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
