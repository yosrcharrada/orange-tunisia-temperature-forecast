# === Import required libraries ===
import xarray as xr         # For handling NetCDF (.nc) climate data
import pandas as pd         # For working with tabular time series data
import os                   # For working with file paths and directories

# === Define input and output paths ===
# Folder containing the NetCDF files from 1950 to 2025
nc_folder = "data/raw/"

# Output file path where processed hourly temperature data will be saved
output_csv = "data/processed/temperature_hourly.csv"

# === Collect all .nc files in the folder ===
# We sort the list to ensure the files are loaded in order (1950 → 2025)
files = sorted([
    os.path.join(nc_folder, f)
    for f in os.listdir(nc_folder)
    if f.endswith(".nc")
])

# === Load and merge all NetCDF files ===
# open_mfdataset = open multi-file dataset (loads all files as one xarray Dataset)
# combine='by_coords' aligns along shared dimensions like time, lat, lon
# engine='netcdf4' is explicitly specified for robustness
ds = xr.open_mfdataset(
    files,
    combine='by_coords',
    parallel=False,
    engine='netcdf4'
)

# === Convert temperature from Kelvin to Celsius ===
# ERA5 2-meter temperature (t2m) is in Kelvin → Convert it
t2m_c = ds['t2m'] - 273.15

# === Spatial averaging over Tunisia ===
# The data grid covers Tunisia: we average over all grid points
t2m_avg = t2m_c.mean(dim=['latitude', 'longitude'])

# === Convert xarray DataArray to pandas DataFrame ===
# This flattens the hourly time series into two columns: time and temp
df = t2m_avg.to_dataframe().reset_index()

# === Keep only the timestamp and temperature columns ===
# 'valid_time' = hourly timestamp; 't2m' = temperature in Celsius
df = df[['valid_time', 't2m']]
df.columns = ['datetime', 'temp_c']

# === Set the datetime as index (optional, helps in time series modeling) ===
df = df.set_index('datetime')

# === Optional: Sort the index just in case
df = df.sort_index()

# === Save to CSV ===
# Ensure output directory exists
os.makedirs("data/processed", exist_ok=True)

# Write the processed hourly data to CSV
df.to_csv(output_csv)

# === Done ===
print(f"✅ Saved hourly temperature data to {output_csv}")
