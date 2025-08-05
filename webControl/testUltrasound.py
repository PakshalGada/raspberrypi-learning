import RPi.GPIO as GPIO
import time
from datetime import datetime

# Set GPIO mode to BCM
GPIO.setmode(GPIO.BCM)

# Define GPIO pins
TRIG = 23
ECHO = 24

# Set up GPIO pins
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# Ensure trigger is low initially
GPIO.output(TRIG, False)
print("Initializing sensor...")
time.sleep(2)

def measure_distance():
    # Send 10us trigger pulse
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    # Initialize variables
    pulse_start = None
    pulse_end = None

    # Wait for ECHO to go high (start of pulse) with timeout
    timeout_start = time.time()
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start - timeout_start > 0.01:  # 10ms timeout
            return None  # No echo start detected

    # Wait for ECHO to go low (end of pulse) with timeout
    timeout_start = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end - timeout_start > 0.1:  # 100ms timeout
            return None  # No echo end detected

    # Calculate distance
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150  # Speed of sound / 2 (cm/s)
    distance = round(distance, 2)

    return distance

try:
    print("Starting ultrasonic sensor test...")
    while True:
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Measure distance
        distance = measure_distance()
        
        if distance is None:
            print(f"[{timestamp}] Error: No valid echo received")
        elif distance < 2 or distance > 400:
            print(f"[{timestamp}] Out of range: {distance} cm")
        else:
            print(f"[{timestamp}] Distance: {distance} cm")
        
        # Wait before next measurement
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nTest stopped by user")
except Exception as e:
    print(f"\nError occurred: {e}")
finally:
    print("Cleaning up GPIO")
    GPIO.cleanup()