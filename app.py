
import time
import smbus
from seeed_dht import DHT
import io
from picamera import PiCamera


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

def take_photo():
    try:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"temp_photo_{timestamp}.jpg"
        camera.capture(filename)
        print(f"Photo saved as {filename}")
        return filename
    except Exception as e:
        print(f"Camera error: {str(e)}")
        return None

def main():
    try:
        lcd_init()
        print("System Ready (DHT11 + LCD + Camera)")
        
        for i in range(5):  
            _, temp = sensor.read()
            print(f'Temperature {i+1}/5: {temp}°C')
            
        
            display_temperature(temp)
            time.sleep(1)
            
        
    
        lcd_command(0x80)
        lcd_write("Taking photo...")
        photo_filename = take_photo()
        
        if photo_filename:
            lcd_command(0xC0)
            lcd_write(photo_filename[:16])  
            time.sleep(2)
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
    
        lcd_clear()
        bus.close()
        camera.close()
        print("Program completed. Resources released.")

if __name__ == '__main__':
    main()