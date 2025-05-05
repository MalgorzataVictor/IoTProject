import time
import smbus
from seeed_dht import DHT
import io
import os
from datetime import datetime
from picamera import PiCamera
from PIL import Image, ImageDraw, ImageFont
from msrest.authentication import ApiKeyCredentials
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
import json
from azure.iot.device import IoTHubDeviceClient, Message
import csv
from azure.iot.device.exceptions import ConnectionFailedError





#Communication Config
id = 'hahauekIOT'
with open("config.json") as f:
    config = json.load(f)

connection_string = config["connection_string"]

device_client = IoTHubDeviceClient.create_from_connection_string(connection_string)

print('Connecting')
device_client.connect()
print('Connected')


# Camera Config
camera = PiCamera()
camera.resolution = (640, 480)
camera.rotation = 180
time.sleep(2)

# LCD Config
ADDRESS = 0x3e
bus = smbus.SMBus(1)

# Temperature Sensor Config
sensor = DHT("11", 5)

# Azure Custom Vision Config
with open('config.json') as config_file:
    config = json.load(config_file)
prediction_url = config['prediction_url']
prediction_key = config['prediction_key']

parts = prediction_url.split('/')
endpoint = 'https://' + parts[2]
project_id = parts[6]
iteration_name = parts[9]
prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": prediction_key})
predictor = CustomVisionPredictionClient(endpoint, prediction_credentials)

# Image directory
os.makedirs('parking_images', exist_ok=True)

# Log directory
LOG_FILE = "logs.txt"

# LCD Functions
def lcd_command(cmd):
    bus.write_byte_data(ADDRESS, 0x80, cmd)

def lcd_write(text):
    for char in text:
        bus.write_byte_data(ADDRESS, 0x40, ord(char))

def lcd_clear():
    lcd_command(0x01)
    time.sleep(0.002)

def lcd_init():
    time.sleep(0.05)
    lcd_command(0x38)
    time.sleep(0.05)
    lcd_command(0x39)
    time.sleep(0.05)
    lcd_command(0x14)
    time.sleep(0.05)
    lcd_command(0x73)
    time.sleep(0.05)
    lcd_command(0x56)
    time.sleep(0.05)
    lcd_command(0x6C)
    time.sleep(0.3)
    lcd_command(0x38)
    time.sleep(0.05)
    lcd_clear()
    lcd_command(0x0C)

def display_lcd_line1(time_str, temp):
    lcd_command(0x80)
    lcd_write(f"{time_str} {temp:.1f}C")

def display_lcd_line2(text):
    lcd_command(0xC0)
    lcd_write(text[:16]) 

def analyze_parking(image_data):
    image_data.seek(0)
    results = predictor.classify_image(project_id, iteration_name, image_data.read())
    sorted_predictions = sorted(results.predictions, key=lambda p: p.probability, reverse=True)
    best_prediction = sorted_predictions[0]
    return best_prediction.tag_name, best_prediction.probability * 100

def save_image_with_results(image_data, tag, probability, filename, temperature=None):
    try:
        with open(filename, 'wb') as f:
            f.write(image_data.getvalue())

        img = Image.open(filename)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()

        draw.text((10, 10), f"Parking: {tag} ({probability:.1f}%)", font=font, fill=(255, 255, 255))

        if temperature is not None:
            temp_text = f"{temperature:.1f}°C"
            text_width, _ = draw.textsize(temp_text, font=font)
            image_width, _ = img.size
            draw.text((image_width - text_width - 10, 10), temp_text, font=font, fill=(255, 255, 255))

        annotated_filename = filename.replace("parking_images/", "parking_images/annotated_")
        img.save(annotated_filename)
        return annotated_filename

    except Exception as e:
        print(f"Error saving image: {str(e)}")
        return None


def log_data(temperature, occupancy):
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    log_entry = f"{timestamp} - {temperature:.1f}°C - {occupancy}\n"
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)


def send_with_retry(device_client, message, max_retries=3, initial_delay=1):
    for attempt in range(max_retries):
        try:
            device_client.send_message(message)
            return True
        except (ConnectionFailedError, Exception) as e:
            if attempt == max_retries - 1:
                print(f"Final attempt failed: {str(e)}")
                return False
            delay = initial_delay * (2 ** attempt) 
            print(f"Attempt {attempt+1} failed. Retrying in {delay}s...")
            time.sleep(delay)           

def take_and_process_photo():
    image_stream = io.BytesIO()
    camera.capture(image_stream, 'jpeg', quality=85)

    tag, probability = analyze_parking(image_stream)
    _, temp = sensor.read()

    log_data(temp, tag)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"parking_images/parking_{timestamp}.jpg"
    annotated_file = save_image_with_results(image_stream, tag, probability, filename, temp)

    now_str = datetime.now().strftime("%H:%M")
    lcd_clear()
    display_lcd_line1(now_str, temp)
    display_lcd_line2(tag)

    print(f"[{now_str}] {tag} ({probability:.1f}%) - Temp: {temp}°C")
    print(f"Saved: {filename}, Annotated: {annotated_file}")

      # Send data to Azure IoT Hub
    telemetry = {
        "timestamp": datetime.now().isoformat(),
        "temperature": round(temp, 1),
        "occupancy": tag
    }
    message = Message(json.dumps(telemetry))
    try:
        send_with_retry(device_client, message)
        print("Telemetry sent to Azure IoT Hub.")
    except Exception as e:
        print(f"Failed to send telemetry: {str(e)}")

def main():
    try:
        lcd_init()
        print("System running. Press Ctrl+C to stop.")
        while True:
            take_and_process_photo()
            time.sleep(10)  

    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        lcd_clear()
        bus.close()
        camera.close()
        print("Cleaned up.")

if __name__ == '__main__':
    main()
