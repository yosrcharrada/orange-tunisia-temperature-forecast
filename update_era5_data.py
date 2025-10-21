import cdsapi  # To access the Copernicus CDS API
import xarray as xr  # To handle NetCDF files
import os  # File operations
import pandas as pd  # To safely handle datetime conversion
from datetime import datetime, timedelta

# Set file paths
base_dir = r"C:\Users\yosrc\OneDrive\Desktop\1950-2025 temp"
data_file = os.path.join(base_dir, "tunisia_2m_temperature_2025.nc")  # Main dataset
log_file = os.path.join(base_dir, "update_log.txt")  # Log file

def log(msg):
    # Append a timestamped message to the log file
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {msg}\n")
    print(f"[{datetime.now()}] {msg}")

# Start update
log("\U0001F4E1 Climate update started")

# Open the existing dataset
old_ds = xr.open_dataset(data_file)

# Get the last date in the dataset safely as a datetime object
last_existing_date = pd.to_datetime(old_ds.time.values[-1]).to_pydatetime()
today = datetime.today()

# Define max available date (ERA5 provides data with 1-day delay)
max_available_date = today - timedelta(days=1)

log(f"[ℹ️] Existing file last date: {last_existing_date.date()}, Today is {today.date()}, Max available: {max_available_date.date()}")

# Create date range to fetch (1 day at a time)
start_date = last_existing_date + timedelta(days=1)
end_date = max_available_date
if start_date > end_date:
    log("[✔️] No new data to download. Dataset is up to date.")
    exit()

dates_to_download = pd.date_range(start=start_date, end=end_date)
log(f"[⬇️] Downloading {len(dates_to_download)} day(s): {start_date.date()} ➡ {end_date.date()}")

# Loop over each date and retrieve data
for date in dates_to_download:
    day_str = date.strftime("%Y-%m-%d")
    log(f"[📅] Downloading {day_str}...")
    temp_day_file = os.path.join(base_dir, "temp_day.nc")

    # Clean up existing temp file
    if os.path.exists(temp_day_file):
        try:
            os.remove(temp_day_file)
        except:
            log(f"[❌] Failed to delete temp_day.nc before download")
            continue

    # Request from CDS
    try:
        c = cdsapi.Client()
        c.retrieve(
            "reanalysis-era5-single-levels",
            {
                "product_type": "reanalysis",
                "variable": "2m_temperature",
                "year": date.strftime("%Y"),
                "month": date.strftime("%m"),
                "day": date.strftime("%d"),
                "time": [f"{h:02d}:00" for h in range(24)],
                "format": "netcdf",
                "area": [37, 7, 30, 12],  # Tunisia: North, West, South, East
            },
            temp_day_file
        )
    except Exception as e:
        log(f"[❌] Download failed for {day_str}: {e}")
        continue

    # Open new day's data
    try:
        new_ds = xr.open_dataset(temp_day_file)

        # If "expver" exists, keep only the first version
        if "expver" in new_ds.dims:
            new_ds = new_ds.sel(expver=0, drop=True)

        # Concat new data to old dataset
        combined = xr.concat([old_ds, new_ds], dim="time")

        # Save updated dataset
        combined.to_netcdf(data_file)

        # Update reference for next iteration
        old_ds = combined

        log(f"[✅] Appended {day_str} successfully")

    except Exception as e:
        log(f"[❌] Error processing {day_str}: {e}")
        continue
    finally:
        # Try to clean up the temp file even if error occurs
        try:
            os.remove(temp_day_file)
        except:
            log("[❌] Failed to delete temp_day.nc after processing")

log("[✅] Climate update completed successfully")