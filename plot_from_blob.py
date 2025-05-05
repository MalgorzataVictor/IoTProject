import json
import base64
import pandas as pd
import matplotlib.pyplot as plt
from azure.storage.blob import ContainerClient
from matplotlib.dates import DateFormatter
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

# If not empty, continue with plots
if not df.empty:
    df.sort_values("timestamp", inplace=True)
    df_latest = df.tail(22).copy()
    df_latest["synthetic_time"] = pd.date_range(start=pd.Timestamp.now(), periods=22, freq="10s")

    # Show latest 22 records
    print("\nLatest 22 records:")
    print(df_latest.to_string(index=False))

    # Temperature Plot (keep as is)
    def plot_temperature(data):
        plt.figure(figsize=(14, 7))
        ax = plt.gca()
        ax.plot(data["synthetic_time"], data["temperature"], marker='o', linestyle='-', color='blue', label='Temperature')

        ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
        plt.xticks(rotation=45, ha='right')
        plt.xlabel("Time ")
        plt.ylabel("Temperature (°C)")
        plt.title("Temperature Over Synthetic Time")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig("temperature_plot.png", dpi=120)
        print("\nTemperature plot saved as 'temperature_plot.png'")

    # Occupancy Bar Chart (counts per category, original style)
    def plot_occupancy_counts(data):
        plt.figure(figsize=(10, 6))
        occupancy_order = ['completely_empty', 'mostly_empty', 'half_full', 'mostly_full', 'fully_occupied']
        color_map = {
            'completely_empty': '#8EB15C',
            'mostly_empty': '#C1E1C1',
            'half_full': '#FFD700',
            'mostly_full': '#FFA500',
            'fully_occupied': '#FF6B6B'
        }

        counts = data['occupancy'].value_counts().reindex(occupancy_order, fill_value=0)

        plt.bar(counts.index.str.replace('_', ' ').str.title(), counts.values,
                color=[color_map[o] for o in counts.index])
        plt.xlabel("Occupancy State", fontsize=12)
        plt.ylabel("Count", fontsize=12)
        plt.title("Occupancy State Counts", fontsize=14, pad=20)
        plt.xticks(rotation=30)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig("occupancy_plot.png", dpi=120)
        print("Occupancy plot saved as 'occupancy_plot.png'")

    # Plot both
    plot_temperature(df_latest)
    plot_occupancy_counts(df)

else:
    print("No valid data to plot.")
