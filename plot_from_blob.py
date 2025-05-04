import json
import base64
import pandas as pd
import matplotlib.pyplot as plt
from azure.storage.blob import ContainerClient
from matplotlib.dates import DateFormatter, MinuteLocator

# Load configuration
with open("config.json") as f:
    config = json.load(f)

connect_str = config["storage_connection_string"]
container_name = config["storage_container"]

# Create Azure Blob client
client = ContainerClient.from_connection_string(connect_str, container_name)
records = []

# Process ALL blobs in the container
blob_list = list(client.list_blobs())  
print(f"Found {len(blob_list)} blobs in container")

for blob in blob_list:
    try:
        # Download full blob content
        data = client.download_blob(blob.name).readall().decode('utf-8')
        
        # Process each line in the blob
        for line in data.splitlines():
            try:
                msg = json.loads(line)
                body_b64 = msg["Body"] + "==="[:len(msg["Body"]) % 4]
                body = json.loads(base64.b64decode(body_b64).decode('utf-8'))
                
                records.append({
                    "timestamp": pd.to_datetime(body["timestamp"]),
                    "temperature": round(float(body["temperature"]) * 2) / 2,
                    "occupancy": body["occupancy"]
                })
            except Exception as e:
                print(f"Skipped line in {blob.name}: {e}")
    except Exception as e:
        print(f"Failed to process blob {blob.name}: {e}")

df = pd.DataFrame(records)

# Display ALL records
pd.set_option('display.max_rows', None)
print(f"\nTotal records processed: {len(df)}")
print("\nFirst 50 records:")
print(df.head(50).to_string()) 
print("\n...")  

# Plot configuration 
plt.figure(figsize=(16, 8))
ax = plt.gca()

if not df.empty:
    df.sort_values("timestamp", inplace=True)
    
    # Plot without value labels above dots
    ax.plot(df["timestamp"], 
            df["temperature"], 
            marker='o', 
            linestyle='-', 
            color='blue',
            label='Temperature')
    
    # Set y-axis to show 0.5 increments
    min_temp = min(df["temperature"]) - 0.5
    max_temp = max(df["temperature"]) + 0.5
    plt.yticks([x/2 for x in range(int(min_temp*2), int(max_temp*2)+1)])
    
    # Set x-axis to show labels every 10 minutes
    ax.xaxis.set_major_locator(MinuteLocator(interval=10))
    ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    
    # Rotate labels
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.2)
    
    # Graph labels
    plt.title("Temperature Over Time", pad=20)
    plt.xlabel("Time (HH:MM)")
    plt.ylabel("Temperature (°C)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig("temperature_plot.png", dpi=120, bbox_inches='tight')
    print("\nPlot saved as 'temperature_plot.png'")
    plt.show()
else:
    print("No valid data to plot")