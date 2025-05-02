import time
import smbus
from seeed_dht import DHT
import io
from picamera import PiCamera
from msrest.authentication import ApiKeyCredentials
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient

# Camera Config
camera = PiCamera()
camera.resolution = (640, 480)
camera.rotation = 180  
time.sleep(2)  

# LCD Config
ADDRESS = 0x3e  # From your i2cdetect output
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
    lcd_command(0x80)  # 1st line
    lcd_write("Temperature:")
    lcd_command(0xC0)  # 2nd line
    lcd_write(f"{temp}°C")

def analyze_parking(image_data):
    """Send image to Custom Vision and return results"""
    image_data.seek(0)
    results = predictor.classify_image(project_id, iteration_name, image_data.read())
    
 
    occupied = 0
    empty = 0
    for prediction in results.predictions:
        if prediction.tag_name == 'occupied_space':
            occupied += 1
        elif prediction.tag_name == 'empty_space':
            empty += 1
        print(f'{prediction.tag_name}:\t{prediction.probability * 100:.2f}%')
    
    return occupied, empty

def take_and_analyze_photo():
    """Capture photo and analyze parking spaces"""
    try:
     
        image_stream = io.BytesIO()
        camera.capture(image_stream, 'jpeg')
        
       
        occupied, empty = analyze_parking(image_stream)
        
    
        lcd_clear()
        lcd_command(0x80)
        lcd_write(f"Occupied: {occupied}")
        lcd_command(0xC0)
        lcd_write(f"Free: {empty}")
        
        return occupied, empty
        
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
        
        occupied, empty = take_and_analyze_photo()
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