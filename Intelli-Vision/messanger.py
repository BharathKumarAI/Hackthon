import os
import asyncio
from dotenv import load_dotenv
import telegram
import requests

# Load environment variables from the .env file
load_dotenv()

# Telegram Bot Token
bot_token = os.getenv("TELEGRAM_TOKEN")

# URLs for the Telegram Bot API
base_url = f'https://api.telegram.org/bot{bot_token}/'
send_message_url = f'{base_url}sendmessage'
chat_id = '-4099647067'


def create_google_maps_link(latitude, longitude):
    return f'https://maps.google.com/?q={latitude},{longitude}'

def send_alert_notification(alert_name, latitude, longitude, image_paths):
    google_maps_link = create_google_maps_link(latitude, longitude)

    message = (
        f"New Alert: *{alert_name}* detected!\n"
        f"Location: [View on Google Maps]({google_maps_link})\n"
    )

    params = {'chat_id': chat_id, 'text': message, 'parse_mode': 'markdown'}
    response = requests.post(send_message_url, params=params)

    # Check if the message was sent successfully
    if response.status_code == 200:
        print('Message sent successfully')
    else:
        print('Failed to send message')
    
    for image_path in image_paths.split(','):
        image_path = image_path.strip()
        if image_path:
            with open(image_path, 'rb') as file:
                send_document_url = f'{base_url}sendDocument'
                files = {'document': file}
                params = {'chat_id': chat_id}
                response = requests.post(send_document_url, params=params, files=files)

                # Check if the file was sent successfully
                if response.status_code == 200:
                    print(f'File "{image_path}" sent successfully')
                else:
                    print(f'Failed to send file "{image_path}"')




