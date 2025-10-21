import cdsapi
import os

client = cdsapi.Client()

years = [str(y) for y in range(1950, 2026)]  # 1950 to 2025 inclusive

for year in years:
    filename = f"tunisia_2m_temperature_{year}.nc"

    # Skip if file already exists
    if os.path.exists(filename):
        print(f"Already downloaded: {filename}")
        continue

    print(f"⏳ Downloading year {year}...")

    client.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": "reanalysis",
            "variable": ["2m_temperature"],
            "year": year,
            "month": [f"{m:02d}" for m in range(1, 13)],
            "day": [f"{d:02d}" for d in range(1, 32)],
            "time": [f"{h:02d}:00" for h in range(24)],
            "format": "netcdf",
            "area": [37.76, 7.52, 30.23, 11.88]  # North, West, South, East
        },
        filename
    )

    print(f"✅ Download complete: {filename}")
