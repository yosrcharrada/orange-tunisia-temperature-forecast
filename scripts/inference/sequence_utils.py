"""
Sequence preparation utilities for LSTM inference.
Handles loading scaler, building input windows, and multi-step forecasting.
"""
import json
import os
from pathlib import Path
from typing import List, Tuple

import joblib
import numpy as np
from sklearn.preprocessing import MinMaxScaler


def get_model_dir() -> Path:
    """Get the path to the models directory."""
    return Path(__file__).parent.parent / "models"


def load_metadata() -> dict:
    """Load model metadata from JSON file."""
    metadata_path = get_model_dir() / "metadata.json"
    with open(metadata_path, 'r') as f:
        return json.load(f)


def load_scaler() -> MinMaxScaler:
    """
    Load the saved MinMaxScaler used during training.
    
    Returns:
        MinMaxScaler: The fitted scaler object.
        
    Raises:
        FileNotFoundError: If scaler file doesn't exist.
    """
    scaler_path = get_model_dir() / "temp_scaler.pkl"
    
    if not scaler_path.exists():
        raise FileNotFoundError(
            f"Scaler file not found at {scaler_path}. "
            "Please generate it from the training notebook using:\n"
            "  import joblib\n"
            "  joblib.dump(scaler, 'scripts/models/temp_scaler.pkl')"
        )
    
    return joblib.load(scaler_path)


def prepare_input_window(
    recent_temps: List[float],
    scaler: MinMaxScaler,
    sequence_length: int = 168
) -> np.ndarray:
    """
    Prepare input window for LSTM prediction.
    
    Args:
        recent_temps: List of recent temperature values (at least sequence_length).
        scaler: Fitted MinMaxScaler.
        sequence_length: Length of the lookback window (default: 168).
        
    Returns:
        np.ndarray: Scaled input array of shape (1, sequence_length, 1).
        
    Raises:
        ValueError: If insufficient temperature values provided.
    """
    if len(recent_temps) < sequence_length:
        raise ValueError(
            f"Insufficient data: need at least {sequence_length} values, "
            f"got {len(recent_temps)}"
        )
    
    # Take the last sequence_length values
    window = recent_temps[-sequence_length:]
    
    # Convert to numpy array and reshape for scaler (samples, features)
    window_array = np.array(window).reshape(-1, 1)
    
    # Scale the data
    scaled_window = scaler.transform(window_array)
    
    # Reshape for LSTM input: (batch_size=1, timesteps, features=1)
    lstm_input = scaled_window.reshape(1, sequence_length, 1)
    
    return lstm_input


def iterative_forecast(
    model,
    initial_window: np.ndarray,
    scaler: MinMaxScaler,
    steps: int
) -> List[float]:
    """
    Perform multi-step iterative forecasting.
    
    The model predicts one step ahead, then the prediction is fed back
    into the sequence to predict the next step.
    
    Args:
        model: Loaded Keras LSTM model.
        initial_window: Initial scaled input window of shape (1, seq_length, 1).
        scaler: Fitted MinMaxScaler for inverse transformation.
        steps: Number of future steps to forecast.
        
    Returns:
        List[float]: List of forecasted temperature values (unscaled).
    """
    forecasts = []
    current_window = initial_window.copy()
    
    for _ in range(steps):
        # Predict next value (output shape: (1, 1))
        scaled_prediction = model.predict(current_window, verbose=0)
        
        # Inverse transform to get actual temperature
        actual_temp = scaler.inverse_transform(scaled_prediction)[0, 0]
        forecasts.append(float(actual_temp))
        
        # Update window: remove oldest value, append new prediction
        # current_window shape: (1, seq_length, 1)
        # Remove first timestep, append new prediction at end
        new_window = np.concatenate([
            current_window[0, 1:, :],  # Remove first timestep
            scaled_prediction.reshape(1, 1)  # Add new prediction
        ], axis=0)
        
        # Reshape back to (1, seq_length, 1)
        current_window = new_window.reshape(1, -1, 1)
    
    return forecasts


def validate_input_length(
    recent_temps: List[float],
    required_length: int = 168
) -> Tuple[bool, str]:
    """
    Validate that input has sufficient length.
    
    Args:
        recent_temps: List of temperature values.
        required_length: Required minimum length.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    if len(recent_temps) < required_length:
        return False, (
            f"Insufficient data: need at least {required_length} hourly "
            f"temperature values, but got {len(recent_temps)}"
        )
    return True, ""
