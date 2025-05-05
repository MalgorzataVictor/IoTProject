import json
import base64
import pandas as pd
import matplotlib.pyplot as plt
from azure.storage.blob import ContainerClient
from matplotlib.dates import DayLocator, DateFormatter
from matplotlib.ticker import MaxNLocator
import numpy as np

# Load configuration
with open("config.json") as f:
    config = json.load(f)

connect_str = config["storage_connection_string"]
container_name = config["storage_container"]

# Create Azure Blob client
client = ContainerClient.from_connection_string(connect_str, container_name)
records = []

# Process blobs
for blob in client.list_blobs():
    try:
        data = client.download_blob(blob.name).readall().decode('utf-8')
        for line in data.splitlines():
            try:
                msg = json.loads(line)
                body_b64 = msg["Body"] + "==="[:len(msg["Body"]) % 4]
                body = json.loads(base64.b64decode(body_b64).decode('utf-8'))
                
                records.append({
                    "timestamp": pd.to_datetime(body["timestamp"]),
                    "temperature": float(body["temperature"]),
                    "occupancy": body["occupancy"]
                })
            except Exception as e:
                print(f"Skipped line: {e}")
    except Exception as e:
        print(f"Failed to process blob: {e}")

df = pd.DataFrame(records)

# Display ALL records in terminal
pd.set_option('display.max_rows', None)
print(f"\nTotal records processed: {len(df)}")
print("\nFirst 50 records:")
print(df.head(50).to_string()) 
print("\n...")

# Plot configuration for Temperature
def plot_temperature(data):
    plt.figure(figsize=(14, 7))
    ax = plt.gca()
    
    data.sort_values("timestamp", inplace=True)
    ax.plot(data["timestamp"], 
            data["temperature"], 
            marker='o', 
            linestyle='-', 
            color='blue',
            label='Temperature')
    
    # Format axes
    ax.xaxis.set_major_locator(DayLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%d/%m/%Y'))
    plt.xticks(rotation=45, ha='right')
    plt.xlabel("Date")
    plt.ylabel("Temperature (°C)")
    plt.title("Temperature Over Time")
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig("temperature_plot.png", dpi=120)
    print("\nTemperature plot saved as 'temperature_plot.png'")

# Plot configuration for Occupancy (Count-based)
def plot_occupancy(data):
    plt.figure(figsize=(16, 8))  
    ax = plt.gca()
    
 
    data['date'] = data['timestamp'].dt.date
    daily_counts = data.groupby(['date', 'occupancy']).size().unstack().fillna(0)
    
 
    states = ['completely_empty', 'mostly_empty', 'half_full', 'mostly_full', 'fully_occupied']
    colors = ['#8EB15C', '#C1E1C1', '#FFD700', '#FFA500', '#FF6B6B']  
    
   
    bar_width = 0.15
    dates = pd.to_datetime(daily_counts.index)
    x = np.arange(len(dates))
    
    for i, state in enumerate(states):
        if state in daily_counts.columns:
            ax.bar(x + i*bar_width, daily_counts[state], 
                   width=bar_width, color=colors[i], 
                   label=state.replace('_', ' ').title(),
                   edgecolor='grey', linewidth=0.5)
    
    # Format axes
    ax.set_xticks(x + bar_width*2)
    ax.set_xticklabels([date.strftime('%d/%m/%Y') for date in dates], rotation=45)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Number of Occurrences", fontsize=12)
    ax.set_title("Daily Parking Occupancy Counts", fontsize=14, pad=20)
    ax.grid(True, alpha=0.2, axis='y')
    
    # Improved legend placement and style
    legend = ax.legend(
        bbox_to_anchor=(1.25, 1),  
        loc='upper left',
        framealpha=1,
        title='Occupancy State',
        title_fontsize=12,
        fontsize=10
    )
    
    
    plt.tight_layout()
    plt.savefig("occupancy_plot.png", dpi=120, bbox_inches='tight')
    print("Occupancy counts plot saved as 'occupancy_plot.png'")

# Generate and display plots
if not df.empty:
    plot_temperature(df)
    plot_occupancy(df)
    plt.show()  
else:
    print("No valid data to plot")