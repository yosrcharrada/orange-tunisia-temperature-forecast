# import xarray as xr
import matplotlib.pyplot as plt

# Load one sample file (say, the first year)
ds = xr.open_dataset("C:/Users/yosrc/OneDrive/Desktop/1950-2025 temp/tunisia_2m_temperature_1950.nc")

# View the structure of the dataset
print(ds)

# Check variable info
print(ds['t2m'])  # 2m temperature

# Plot one day of data
sample_day = ds['t2m'].sel(time='1950-01-01T12:00:00')
sample_day.plot()
plt.title("2m Temperature over Tunisia - Jan 1, 1950 @ 12:00")
plt.show()

# Get basic stats
print(ds['t2m'].mean().values)   # mean temp (in Kelvin)
print(ds['t2m'].min().values)    # min
print(ds['t2m'].max().values)    # max
