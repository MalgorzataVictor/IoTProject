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

# Custom Vision Config
prediction_url = '*'
prediction_key = '*'

# Parse Custom Vision endpoint
parts = prediction_url.split('/')
endpoint = 'https://' + parts[2]
project_id = parts[6]
iteration_name = parts[9]

# Initialize predictor
prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": prediction_key})
predictor = CustomVisionPredictionClient(endpoint, prediction_credentials)

# Create directory for saved images
os.makedirs('parking_images', exist_ok=True)

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

def display_temperature(temp):
    lcd_command(0x80)
    lcd_write("Temperature:")
    lcd_command(0xC0)
    lcd_write(f"{temp}°C")

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

        # Parking status 
        status_text = f"Parking: {tag} ({probability:.1f}%)"
        draw.text((10, 10), status_text, font=font, fill=(255, 255, 255))

        # Temperature 
        if temperature is not None:
            temp_text = f"{temperature}°C"
            text_width, _ = draw.textsize(temp_text, font=font)
            image_width, _ = img.size
            draw.text((image_width - text_width - 10, 10), temp_text, font=font, fill=(255, 255, 255))

        annotated_filename = filename.replace("parking_images/", "parking_images/annotated_")
        img.save(annotated_filename)
        return annotated_filename

    except Exception as e:
        print(f"Error saving image: {str(e)}")
        return None

def analyze_parking(image_data):
    image_data.seek(0)
    results = predictor.classify_image(project_id, iteration_name, image_data.read())

    sorted_predictions = sorted(results.predictions, key=lambda p: p.probability, reverse=True)
    for prediction in sorted_predictions:
        print(f'{prediction.tag_name:<20}: {prediction.probability * 100:.2f}%')

    best_prediction = sorted_predictions[0]
    return best_prediction.tag_name, best_prediction.probability * 100

def take_and_analyze_photo():
    try:
        image_stream = io.BytesIO()
        camera.capture(image_stream, 'jpeg', quality=85)
        image_stream.seek(0)

        tag, probability = analyze_parking(image_stream)
        _, temperature = sensor.read()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"parking_images/parking_{timestamp}.jpg"

        annotated_file = save_image_with_results(image_stream, tag, probability, filename, temperature)

        lcd_clear()
        lcd_command(0x80)
        lcd_write(f"{tag}")
        lcd_command(0xC0)
        lcd_write(f"{probability:.1f}%")

        print(f"Images saved: {filename} and {annotated_file}")
        return tag, probability

    except Exception as e:
        print(f"Analysis error: {str(e)}")
        return None, None

def main():
    try:
        lcd_init()
        print("System Ready (DHT11 + LCD + Camera + Custom Vision)")

        for i in range(5):
            _, temp = sensor.read()
            print(f'Temperature {i+1}/5: {temp}°C')
            display_temperature(temp)
            time.sleep(1)

        lcd_clear()
        lcd_command(0x80)
        lcd_write("Analyzing...")

        tag, probability = take_and_analyze_photo()
        time.sleep(5)

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        lcd_clear()
        bus.close()
        camera.close()
        print("Program completed. Resources released.")

if __name__ == '__main__':
    main()
