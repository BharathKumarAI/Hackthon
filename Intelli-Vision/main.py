import cv2
import time
import json
from collections import Counter
import RPi.GPIO as GPIO
from picamera2 import Picamera2, Preview
from utils import *
from distance_utils import *
from gps_utils import *
from database_utils import *
import threading
from messanger import *

normalSize = (640, 480)
lowresSize = (320, 240)

picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": normalSize},
                                              lores={"size": lowresSize, "format": "YUV420"})
picam2.configure(config)
stride = picam2.stream_configuration("lores")["stride"]

animals = ['bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe']
electronic_devices = ['tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster']
furniture = ['chair', 'couch', 'bed', 'dining table']
food_and_drinks = ['banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl']
vehicles = ['bicycle', 'motorcycle', 'car', 'airplane', 'bus', 'train', 'truck', 'boat']
traffic = ['traffic light', 'fire hydrant', 'stop sign', 'parking meter']

# Flag to indicate if the process is running
process_running = False
# Initialize camera_thread outside the button_callback function
camera_thread = None
# Flag to indicate if the preview has been started
preview_started = False

# Set GPIO mode and pins
GPIO.setmode(GPIO.BCM)
button_pin = 17
led_pin = 18
buzzer_pin = 27

# Set up GPIO for button, LED, and buzzer
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(led_pin, GPIO.OUT)
GPIO.setup(buzzer_pin, GPIO.OUT)
print("code is running")

def initialize_preview():
    global picam2, preview_started
    if not preview_started:
        picam2.start_preview(Preview.QTGL)
        picam2.start()
        preview_started = True

def stop_preview():
    global picam2, preview_started
    if preview_started:
        picam2.stop()
        picam2.stop_preview()
        picam2.close()
        preview_started = False

def capture_and_process():
    global process_running
    # Set initial random GPS coordinates
    current_latitude, current_longitude = generate_nearby_coordinates()
    distance = generate_random_distance()  # Initial distance (in meters)
    previous_dist = -1
    print("process_running: " + str(process_running))

    try:
        while process_running:
            initialize_preview()

            # Video info
            buffer = picam2.capture_buffer("lores")
            grey = buffer[:stride * lowresSize[1]].reshape((lowresSize[1], stride))
            image = cv2.cvtColor(grey, cv2.COLOR_GRAY2RGB)

            # Check internet connectivity
            if check_internet():
                # Send image for prediction using LLM model
                response = send_images_for_prediction(image, distance)
                json_response = json.loads(response)
                alert_str = json_response['Alert']
                if alert_str.lower() == "none":
                    alert_str = ""
                if alert_str.lower() != "none" and alert_str != "":
                    text_to_speech(json_response['Description'])
                json_response["Distance"] = distance
                json_response["latitude"] = current_latitude
                json_response["longitude"] = current_longitude
                json_response["Mode"] = "Online"
            else:
                # Get predictions from YOLO model
                response = yolo_prediction(image)
                objects = []
                for box in response.boxes:
                    class_id = response.names[box.cls[0].item()]
                    cords = box.xyxy[0].tolist()
                    cords = [round(x) for x in cords]
                    conf = round(box.conf[0].item(), 2)
                    # print("Object type:", class_id)
                    # print("Coordinates:", cords)
                    # print("Probability:", conf)
                    # print("---")
                    if conf > 0.5:
                        objects.append(class_id)

                print(objects)
                # Use Counter to count occurrences of each item
                item_counts = Counter(objects)
                # Create a string representation
                item_description = ", ".join(
                    f"{item} are {count} {'item' if count == 1 else 'items'}" for item, count in item_counts.items()
                )

                # Count occurrences of "Person"
                person_count = objects.count("person")

                alert_str = ""
                desc_str = ""
                if person_count > 5:
                    alert_str += " |Overcrowded| "
                    desc_str += "Infront of you there is a overcrowded place. "

                if any(item in vehicles for item in objects) and (distance-previous_dist < 0):
                    alert_str += " |Vehicle approaching| "
                    desc_str += f"Vehicle approaching towards you. Currently at a distance of : {distance} meters " 

                if "knife" in objects:
                    alert_str += " |Knife| "
                    desc_str += "person carrying knife towards you. "

                desc_str += item_description
                alert_list = alert_str.split("|")
                alert_list = [a.strip() for a in alert_list if a]
                final_alert_str = ", ".join(alert_list)

                if alert_str:
                    text_to_speech(desc_str)

                json_response = {
                    "Mode": "Offline",
                    "Alert" : final_alert_str,
                    "Description" : desc_str,
                    "Objects": ", ".join(objects),
                    "Distance" : distance,
                    "latitude": current_latitude,
                    "longitude": current_longitude,
                }

            if distance < 20:
                print("distance alert")
            # Save the image and information to the database
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            image_path = f'captured_images/{timestamp}.jpg'  # Change the path as needed
            json_response["image_path"] = image_path

            print(json_response)
            # Save the captured image with timestamp
            cv2.imwrite(image_path, image)
            save_to_database(json_response)
            if alert_str:
                # Send notification to Telegram
                send_alert_notification(json_response["Alert"], json_response["latitude"], json_response["longitude"], json_response["image_path"])

            previous_dist = distance
            # Wait for 5 seconds before capturing the next image
            time.sleep(5)
            # Update distance for every loop
            distance = update_distance(distance)
            # Generate random GPS coordinates for Hyderabad
            current_latitude, current_longitude = generate_nearby_coordinates()

    except KeyboardInterrupt:
        pass
    finally:
        stop_preview()
        GPIO.cleanup()

def button_callback(channel):
    global process_running, camera_thread
    if not process_running:
        print("Button pressed! Turning on LED, buzzing the buzzer, and starting camera feed.")
        # Turn on LED
        GPIO.output(led_pin, GPIO.HIGH)
        # Buzz the buzzer
        GPIO.output(buzzer_pin, GPIO.HIGH)
        time.sleep(1)  # Buzz for 1 second
        GPIO.output(buzzer_pin, GPIO.LOW)

        # Start the camera process in a separate thread
        process_running = True
        camera_thread = threading.Thread(target=capture_and_process)
        camera_thread.start()
    else:
        print("Button pressed! Turning off LED, stopping buzzer, and stopping camera feed.")
        # Turn off LED
        GPIO.output(led_pin, GPIO.LOW)
        # Stop the buzzer
        GPIO.output(buzzer_pin, GPIO.LOW)
        # Stop camera feed by setting the flag to False
        process_running = False
        # Wait for the camera_thread to finish before allowing a new start
        if camera_thread:
            camera_thread.join()

# Add event listener for the button press
GPIO.add_event_detect(button_pin, GPIO.FALLING, callback=button_callback, bouncetime=300)

if __name__ == "__main__":
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        # Cleanup GPIO and close the camera
        GPIO.cleanup()