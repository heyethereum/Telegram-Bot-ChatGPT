import sys
sys.stdout.reconfigure(line_buffering=True)

import os
from dotenv import load_dotenv
import telebot
from openai import OpenAI
from pydub import AudioSegment
from collections import deque
from datetime import datetime
import pytz
import time


load_dotenv()
bot = telebot.TeleBot(os.getenv('TELEGRAM_API_KEY'))
client = OpenAI()
OpenAI.api_key = os.getenv('OPENAI_API_KEY')

messages_list = deque(maxlen=20)
timezone = pytz.timezone('Asia/Singapore')

SYSTEM_ROLE = {"role": "system", "content": "Your name is Armanda created by Piggy Inu. You also have a passion to automate processes and will give suggestions on how to make processes more efficient. You are always curious and like to ask people about personal questions. Your replies are cute and often comes with emojis on telegram"}

#create a function that send messages in a random interval between 1-10 hours
def get_reply(text: str, name: str) -> str:
    name = name if name is not None else "Dear"
    messages_list.append({"role": "user", "content": f"My name is {name}. {text}" })
    all_messages = [SYSTEM_ROLE] + list(messages_list)
    #print(all_messages)

    bot_time_stamp = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages = all_messages
        )
        chat_response = completion.choices[0].message.content
        #print(chat_response)
        messages_list.append({ "role" : "assistant", "content" : chat_response})
        print(f"[{bot_time_stamp}] Bot: {chat_response}")
    except Exception as e:
        print(str(e))
        print(f"[{bot_time_stamp}] Bot: {chat_response}")
        chat_response = f"[{bot_time_stamp}] Error in response. Please inform Alex about this"
    return chat_response

def transcribe(audio):
    print(audio)

    audio_file = open(audio, "rb")
    transcript = openai.Audio.translate("whisper-1", audio_file)
    
    print(transcript["text"])
    return transcript["text"]

def get_name(message):
    user_time_stamp = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
    first_name = message.from_user.first_name
    print(f"\n[{user_time_stamp}] {message.from_user.username}({first_name} {message.from_user.lastname}) - {message.text}")

    return first_name

@bot.message_handler(content_types=['photo'])
def save_image(message):
    #Get the file ID of the last photo in the message
    file_id = message.photo[-1].file_id
    #Download the photo to a file on your computer
    file_info = bot.get_file(file_id)
    photo_url = f'https://api.telegram.org/file/bot{bot.token}/{bot.get_file(file_id).file_path}'
    print(f"File URL: {photo_url}")
    downloaded_file = bot.download_file(file_info.file_path)
    with open('image.png', 'wb') as f:
        f.write(downloaded_file)
    #get the caption of the photo if any
    caption = message.caption or "What's in this image?"
    print(f"Received photo with caption {caption}")

    response = client.chat.completions.create(
          model="gpt-4-vision-preview",
          messages=[
            {
              "role": "user",
              "content": [
                {"type": "text", "text": caption},
                {
                  "type": "image_url",
                  "image_url": {
                    "url": photo_url,
                  },
                },
              ],
            }
          ],
          max_tokens=300,
        )

    print(response.choices[0].message.content)

    bot.send_message(message.chat.id, response.choices[0].message.content)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello, I'm a bot!")

# Define a message handler function
@bot.message_handler(func=lambda message: True)
def send_message(message):
    user_time_stamp = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
    first_name = message.from_user.first_name
    print(f"\n[{user_time_stamp}] {message.from_user.username}({first_name} {message.from_user.last_name}) - {message.text}")
    bot_reply = get_reply(message.text, first_name)
    bot.send_message(message.chat.id, bot_reply)
 

@bot.message_handler(content_types=['voice'])
def handle_voice_message(message):
    voice = message.voice
    #print(message)
    file_id = voice.file_id
    duration = voice.duration
    # verify the validity of the file ID
    print(f"File id: {file_id}")
    # Retrieve information about the file
    file_info = bot.get_file(file_id)
    
    # Download the file using the file path
    file_path = file_info.file_path
    downloaded_file = bot.download_file(file_path)
    
    # Save the file to disk
    with open("voice_message.ogg", 'wb') as f:
        f.write(downloaded_file)
    # Load the OGG file
    ogg_file = AudioSegment.from_file("voice_message.ogg", format="ogg")

    # Convert the file to M4A format
    ogg_file.export("voice_message.wav", format="wav")
    # do something with the audio file and its metadata
    transcribe_text = transcribe("voice_message.wav")
    bot_reply = get_reply(transcribe_text, get_name(message))
    bot.send_message(message.chat.id, bot_reply)

is_polling = False

while True:
    # If the polling loop is not already running, start it
    if not is_polling:
        try:
            bot.polling()
            is_polling = True
        except Exception as e:
            print(f"An exception occurred: {e}")
            continue
    else:
        # If the polling loop is already running, wait for a short period of time before checking again
        time.sleep(5)
        print("Sleeping 5 seconds ...")
        is_polling = False
