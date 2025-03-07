from sense_hat import SenseHat
import time
from datetime import datetime

# Initialize the Sense HAT
sense = SenseHat()
sense.clear()  # Clear the LED matrix

print("Raspberry Pi Sense HAT RGB Color Test")
print("======================================")

# Function to read light levels using LED matrix as a light sensor
def get_light_level():
    # Turn off all LEDs first to ensure accurate reading
    sense.clear()
    time.sleep(0.2)  # Brief pause to let LEDs turn off
    
    # Get raw humidity and temperature readings
    humidity_dark = sense.get_humidity()
    temp_dark = sense.get_temperature()
    
    # Turn on all LEDs at full brightness (white)
    all_white = [(255, 255, 255)] * 64
    sense.set_pixels(all_white)
    time.sleep(0.2)  # Wait for LEDs to reach full brightness
    
    # Get readings with LEDs on
    humidity_bright = sense.get_humidity()
    temp_bright = sense.get_temperature()
    
    # Calculate differences 
    humidity_diff = abs(humidity_bright - humidity_dark)
    temp_diff = abs(temp_bright - temp_dark)
    
    # Combine both sensors for more robust reading
    combined_diff = (humidity_diff * 4 + temp_diff * 2)
    
    # Map to inverse scale: higher diff = lower light level
    if combined_diff < 0.05:
        light_level = 100  # Very bright environment
    elif combined_diff > 2.0:
        light_level = 0   # Very dark environment
    else:
        # Map to a 0-100% scale with inverse relationship
        light_level = max(0, min(100, 100 - (combined_diff * 50)))
    
    # Return to neutral display
    sense.clear()
    
    return light_level, humidity_diff, temp_diff

# Function to test RGB color detection using LED matrix
def test_rgb_detection():
    # Test colors (R, G, B)
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cyan
        (255, 255, 255) # White
    ]
    
    color_names = ["Red", "Green", "Blue", "Yellow", "Magenta", "Cyan", "White"]
    
    try:
        while True:
            # Get current time
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # First measure ambient light with all LEDs off
            light_level, humidity_diff, temp_diff = get_light_level()
            
            print(f"\n[{current_time}] Light and Color Test:")
            print("------------------------------")
            print(f"Light Level: {light_level:.1f}%")
            print(f"Humidity Difference: {humidity_diff:.4f}%")
            print(f"Temperature Difference: {temp_diff:.4f}°C")
            
            # Try to detect color using the LED matrix
            print("\nTesting color detection using LED matrix:")
            
            # Check if color sensor is available (experimental)
            has_color_sensor = False
            try:
                if hasattr(sense, 'color') and sense.color is not None:
                    has_color_sensor = True
                    print("Color sensor detected! Testing actual color sensor...")
                    
                    # Set parameters for better sensitivity
                    sense.color.gain = 60
                    sense.color.integration_cycles = 64
                    
                    # Wait for integration time to complete
                    time.sleep(2 * sense.color.integration_time)
                    
                    # Get color sensor readings
                    red, green, blue, clear = sense.color.colour
                    
                    print(f"Color sensor readings - R: {red:.2f}, G: {green:.2f}, B: {blue:.2f}, C: {clear:.2f}")
                    
                    # Calculate dominant color
                    max_val = max(red, green, blue)
                    if max_val < 10:  # Very low values
                        dominant = "Dark/Black"
                    elif red == max_val and red > green * 1.5 and red > blue * 1.5:
                        dominant = "Red"
                    elif green == max_val and green > red * 1.5 and green > blue * 1.5:
                        dominant = "Green"
                    elif blue == max_val and blue > red * 1.5 and blue > green * 1.5:
                        dominant = "Blue"
                    elif red > blue * 1.5 and green > blue * 1.5 and abs(red - green) < 20:
                        dominant = "Yellow"
                    elif red > green * 1.5 and blue > green * 1.5 and abs(red - blue) < 20:
                        dominant = "Magenta/Purple"
                    elif green > red * 1.5 and blue > red * 1.5 and abs(green - blue) < 20:
                        dominant = "Cyan"
                    elif (red > 200 and green > 200 and blue > 200) or (clear > 200):
                        dominant = "White/Bright"
                    else:
                        dominant = "Mixed/Unknown"
                    
                    print(f"Detected dominant color: {dominant}")
                    
            except Exception as e:
                print(f"Color sensor test error: {e}")
            
            if not has_color_sensor:
                print("No color sensor available, testing with LED matrix...")
                
                # Test each color
                for i, (color, name) in enumerate(zip(colors, color_names)):
                    print(f"\nTesting {name} color...")
                    
                    # Fill the entire display with this color
                    sense.clear(color)
                    time.sleep(1)
                    
                    # Take sensor readings
                    temp = sense.get_temperature()
                    humidity = sense.get_humidity()
                    pressure = sense.get_pressure()
                    
                    print(f"Temperature: {temp:.2f}°C")
                    print(f"Humidity: {humidity:.2f}%")
                    print(f"Pressure: {pressure:.2f} millibars")
                    
                    # Clear the display before next color
                    sense.clear()
                    time.sleep(0.5)
            
            print("\nPlace different colored objects near the Sense HAT")
            print("Press Ctrl+C to exit the test")
            
            # Wait before next test cycle
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nTest terminated by user")
        sense.clear()  # Clear the LED matrix on exit

if __name__ == "__main__":
    test_rgb_detection()