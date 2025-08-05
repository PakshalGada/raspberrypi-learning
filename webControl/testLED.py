import RPi.GPIO as GPIO
import time

# Set GPIO mode to BCM
GPIO.setmode(GPIO.BCM)

# Define GPIO pin
LED_PIN = 18

# Set up the GPIO pin as output
GPIO.setup(LED_PIN, GPIO.OUT)

try:
    # Turn on the LED
    GPIO.output(LED_PIN, GPIO.HIGH)
    print("LED turned ON")
    
    # Keep the LED on for 5 seconds
    time.sleep(5)
    
except KeyboardInterrupt:
    print("\nProgram interrupted")
    
finally:
    # Turn off the LED and clean up
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.cleanup()
    print("GPIO cleanup completed")
