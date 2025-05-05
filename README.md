# IoT Parking Monitoring System with Azure Integration   🚗
*A Raspberry Pi-powered solution for smart parking management with **AI-powered visual classification***   

---

## 📌 Table of Contents  
- [Project Overview](#-project-overview)  
- [System Architecture](#-system-architecture)  
- [Prerequisites](#-prerequisites)  
- [Setup & Installation](#-setup--installation)  
- [Data Flow](#-data-flow)  
- [Custom Vision](#-custom-vision)  
- [IoT Storage](#-iot-storage)  
- [Data Visualization](#-data-visualization)  
- [Project Demo](#-project-demo)  
- [Troubleshooting](#-troubleshooting)  
- [Challenges & Solutions](#-challenges--solutions)  

---

## 📷 Project Overview  
### **Smart parking meets AI vision** 
This system combines Raspberry Pi hardware with Azure cloud services to monitor a parking spaces and detect occupancy levels using Azure Custom Vision AI. 
Predictions are sent to Azure IoT Hub, processed with Azure Functions, stored in Blob Storage, and visualized through Python-based analytics. 

### **Features:**
- Establishes a secure connection with Azure IoT Hub  
- Captures parking lot images using Pi Camera  
- Monitors temperature with DHT11 sensor  
- Classifies parking occupancy using Azure Custom Vision AI  
- Displays time, temperature and occupancy on LCD screen  
- Transmits JSON telemetry to Azure IoT Hub  
- Annotates images with occupancy and temperature data  
- Stores time-stamped data locally and in Azure Blob  
- Generates charts from blob storage data  

---

## 📐 System Architecture  

---

## 📦 Prerequisites  
### **Hardware**  
- Raspberry Pi 4 
- Grove base hat for Raspberry PI
- Raspberry Pi Camera v2 
- Grove temperature and humidity sensor (DHT11)
- Grove - 16 x 2 LCD
- Parking (in my case DIY)


### **Software**  
- Raspberry Pi OS (Legacy 32-bit) Lite - BULLSEYE
- Python 3.9  
- Azure IoT Hub, Blob Storage, and Function App configured
- Custom Vision AI Project
- Install dependencies from the included requirements file:  

```bash
pip install -r requirements.txt 

```
## 🔧 Installation & Usage

### **Installation**  
 **1. Clone the Repository**
```bash
git clone https://github.com/MalgorzataVictor/IoTProject
cd iot-parking-system
```

**2. Install Dependencies**
```bash
pip install -r requirements.txt
```

**3. Set Up Azure Services (locally)**
```bash
func azure functionapp publish parking-system-function 
```
### **Configuration**  

**1. Environment Setup**  
Create config.json file in project root with own settings
```bash
{
    "prediction_url": "",
    "prediction_key": "",
    "connection_string": "",
    "storage_connection_string": "",
    "storage_container": ""
}

```
**2. Hardware Configuration** 
| Component       | Connection               |
|-----------------|--------------------------|
| 📷 Pi Camera    | CSI Port                 |
| 🌡️ DHT11 Sensor | GPIO 5 (Pin 29)          |
| 🖥️ LCD Display  | I2C (Address `0x3E`)     |

*Remember to enable Legacy Camera (Bullseye/Buster OS) using sudo 'raspi-config'*

### **Usage**  

**1. Start the System - monitoring** 
```bash
python app.py 
```
**2. Plotting the graphs** 
```bash
python plot_from_blob.py
```

---

## 🌀 Data Flow  
The Raspberry Pi runs app.py to capture images and temperature data every 10 seconds. Azure Custom Vision AI analyzes each image, classifying parking occupancy into five states with confidence scores. This data merges into JSON payloads and transmits to Azure IoT Hub. Azure Functions processes data, while Blob Storage archives raw data for. Locally, plot_from_blob.py generates real-time dashboards.

![Azure Stats](./resources/LCD.jpg)

### **Telementry Payload**
```bash
{
  "timestamp": "2024-05-20T14:30:00Z",
  "device_id": "parking-pi-01",
  "temperature": 23.5,
  "occupancy": "mostly_empty",
  "confidence": 0.92
}
```


![Azure Stats](./resources/azure_stats.png)
    

---

## 👁️ Custom Vision  
The system leverages Azure Custom Vision’s image classification model, trained on 200+  parking lot images. The model distinguishes five occupancy states, defined by precise capacity ranges: **completely_empty** (0%), **mostly_empty** (10-30%), **half_full** (40-60%), **mostly_full** (70-90%), and **fully_occupied** (100%).


### **Integration Workflow:**

1.Configuration: The app.py script loads the Custom Vision endpoint and prediction key from config.json, dynamically extracting the project ID and iteration name from the prediction URL.

2.Real-Time Inference: Each captured image is sent to the trained model, which returns both the occupancy classification (e.g., "mostly_empty") and a confidence score (0–1). 

3.Edge Processing: Results are locally annotated on images (saved to parking_images/) and packaged into JSON telemetry for Azure IoT Hub


![Azure Stats](./resources/customVision.png)

*AI classifies parking states with high accuracy, working best for empty spots and needing minor improvements for full occupancy detection.*

---

## 🗄️ IoT Storage  
### **Local**

```bash
2025-05-05T00:41:21 - 23.0°C - completely_empty
2025-05-05T00:41:32 - 23.0°C - half_full
2025-05-05T00:41:44 - 22.0°C - half_full
2025-05-05T00:41:56 - 22.0°C - fully_occupied
2025-05-05T00:42:08 - 22.0°C - mostly_empty
2025-05-05T00:42:19 - 22.0°C - completely_empty
2025-05-05T00:42:31 - 22.0°C - half_full
2025-05-05T00:42:42 - 22.0°C - half_full
2025-05-05T00:42:54 - 22.0°C - mostly_empty
2025-05-05T00:43:06 - 23.0°C - fully_occupied
2025-05-05T00:43:17 - 23.0°C - half_full
2025-05-05T00:43:28 - 23.0°C - fully_occupied
2025-05-05T00:43:40 - 24.0°C - mostly_full
2025-05-05T00:43:51 - 24.0°C - mostly_full
```

### **Azure Blob**

JSON-encoded telemetry is stored in Azure Blob Storage. Messages are base64 encoded by Event Hub, decoded in plot_from_blob.py. Each blob contains multiple newline-delimited messages
```bash
{"EnqueuedTimeUtc":"2025-05-04T23:41:21.3940000Z","Properties":{},"SystemProperties":{"connectionDeviceId":"soil-moisture-sensor","connectionAuthMethod":"{\"scope\":\"device\",\"type\":\"sas\",\"issuer\":\"iothub\"}","connectionDeviceGenerationId":"638765239356645892","enqueuedTime":"2025-05-04T23:41:21.3940000Z"},"Body":"eyJ0aW1lc3RhbXAiOiAiMjAyNS0wNS0wNVQwMDo0MToyMS4zMDM0NjgiLCAidGVtcGVyYXR1cmUiOiAyMywgIm9jY3VwYW5jeSI6ICJjb21wbGV0ZWx5X2VtcHR5In0="}
{"EnqueuedTimeUtc":"2025-05-04T23:41:32.9560000Z","Properties":{},"SystemProperties":{"connectionDeviceId":"soil-moisture-sensor","connectionAuthMethod":"{\"scope\":\"device\",\"type\":\"sas\",\"issuer\":\"iothub\"}","connectionDeviceGenerationId":"638765239356645892","enqueuedTime":"2025-05-04T23:41:32.9560000Z"},"Body":"eyJ0aW1lc3RhbXAiOiAiMjAyNS0wNS0wNVQwMDo0MTozMi44NjQwNTUiLCAidGVtcGVyYXR1cmUiOiAyMywgIm9jY3VwYW5jeSI6ICJoYWxmX2Z1bGwifQ=="}

```

---

## 📊 Data Visualization  

![Occupancy Plot](./resources/occupancy_plot.png) ![Temperature Plot](./resources/temperature_plot.png)

---

## 🎬 Project Demo  

---

## ⚠️ Troubleshooting  

### **1. Camera Not Detected**
- **Symptoms**:  
  `picamera.exc.PiCameraError` 
- **Fix**:  
  ```bash
  sudo raspi-config  
  sudo reboot
  vcgencmd get_camera  # Verify "supported=1 detected=1"

---

## ⚔️ Challenges  

---