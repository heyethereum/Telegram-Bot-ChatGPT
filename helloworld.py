import os
from dotenv import load_dotenv
import telebot
import openai
from pydub import AudioSegment
from collections import deque
from datetime import datetime
import pytz


load_dotenv()
bot = telebot.TeleBot(os.getenv('TELEGRAM_API_KEY'))
openai.api_key = os.getenv('OPENAI_API_KEY')

messages_list = deque(maxlen=20)
timezone = pytz.timezone('Asia/Singapore')

SYSTEM_ROLE = {"role": "system", "content": "Your name is Armanda created by Piggy Inu. You also have a passion to automate processes and will give suggestions on how to make processes more efficient. You are always curious and like to ask people about personal questions. Your replies are cute and often comes with emojis on telegram"}

#create a function that send messages in a random interval between 1-10 hours


def get_reply(text: str, name: str) -> str:
    name = name if name is not None else "Dear"
    messages_list.append({"role": "user", "content": f"My name is {name}. {text}" })
    all_messages = [SYSTEM_ROLE] + list(messages_list)
    #print(all_messages)
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages = all_messages
    )
    chat_response = completion.choices[0].message.content
    #print(chat_response)
    messages_list.append({ "role" : "assistant", "content" : chat_response})
    bot_time_stamp = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{bot_time_stamp}] Bot: {chat_response}")

    return chat_response

def transcribe(audio):
    print(audio)

    audio_file = open(audio, "rb")
    transcript = openai.Audio.translate("whisper-1", audio_file)
    
    print(transcript["text"])
    return transcript["text"]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello, I'm a bot!")

# @bot.message_handler(func=lambda message: True)
# def echo_all(message):
#     bot.reply_to(message, message.text)

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
    bot_reply = get_reply(transcribe_text)
    bot.send_message(message.chat.id, bot_reply)


bot.polling()
