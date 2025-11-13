"""
Helper script to generate temp_scaler.pkl from training data.

This script should be run AFTER training the LSTM model to ensure
the scaler matches the one used during training.

Usage:
    python scripts/models/generate_scaler.py
"""
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_scaler_from_data(data_path: str = "data/processed/temperature_hourly.csv"):
    """
    Generate and save a MinMaxScaler based on the training data.
    
    Note: This is a placeholder implementation. Ideally, you should
    save the scaler directly from your training notebook to ensure
    it's exactly the same as used during training.
    
    Args:
        data_path: Path to the processed temperature CSV file
    """
    print("⚠️  IMPORTANT: This script generates a NEW scaler.")
    print("   For best results, save the scaler directly from your training notebook:")
    print()
    print("   In your training notebook:")
    print("   >>> import joblib")
    print("   >>> joblib.dump(scaler, 'scripts/models/temp_scaler.pkl')")
    print()
    
    if not os.path.exists(data_path):
        print(f"❌ Error: Data file not found at {data_path}")
        print(f"   Please ensure the preprocessed data exists.")
        sys.exit(1)
    
    # Load data
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    
    # Create and fit scaler
    print("Fitting MinMaxScaler...")
    scaler = MinMaxScaler()
    scaler.fit(df[['temp_c']])
    
    # Save scaler
    output_path = Path(__file__).parent / "temp_scaler.pkl"
    joblib.dump(scaler, output_path)
    
    print(f"✓ Scaler saved to {output_path}")
    print(f"  - Data min: {scaler.data_min_[0]:.2f}°C")
    print(f"  - Data max: {scaler.data_max_[0]:.2f}°C")
    print(f"  - Feature range: [0, 1]")
    print()
    print("✓ Done! You can now run the inference API.")


if __name__ == "__main__":
    generate_scaler_from_data()
