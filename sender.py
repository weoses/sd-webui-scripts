import json
import random
import os
import time
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
import pathlib

PICRANDOM_FOLDER='/var/kloaka_share/picrandom'
BTHREAD_FOLDER = '/var/kloaka_share/bthread'

conf = config.load_quotes()
all_picrandom_files = []
all_bthread_files = []
all_anek_files = []
all_quote_files = []


bot = telebot.TeleBot(conf.get_value("token"))

def all_files_in(folder, exts:list):
    all_files = []
    for path, currentDirectory, files in os.walk(folder):
        for file in files:
            file = file.lower()
#           print(file)
            res = False
            for e in exts :
                res = res | (pathlib.Path(file).suffix == e)

            if res:
               all_files.append(os.path.join(path, file))

    return all_files

def load_files():
    global all_picrandom_files
    global all_bthread_files
    global all_anek_files
    global all_quote_files

    all_picrandom_files = all_files_in(conf.get_value('picrandom_folder'), ['.png', '.jpg', '.jpeg'])
    all_bthread_files = all_files_in(conf.get_value('bthread_folder'),  ['.png', '.jpg', '.jpeg'])
    all_anek_files = all_files_in(conf.get_value('anek_folder'), ['.json'])
    all_quote_files = all_files_in(conf.get_value('quotes_folder'), ['.json'])

@bot.message_handler(commands=['start'])
def start_message(message):
    text = f"Привет ✌."
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['picrandom_length'])
def pic_message(message):
    text = f"Всего пикрандомов - {len(all_picrandom_files)}"
    bot.send_message(message.chat.id, text)

@bot.inline_handler(lambda query: True)
def inline_quote(inline_query):    
    ids = f'{time.time()*100000}'

    bot.answer_inline_query(inline_query.id, [
        types.InlineQueryResultArticle(f'{ids}+1', 
                                       'Отправить цитато4ку', 
                                       thumb_url=conf.get_value('quote_thumb_url'),
                                       thumb_width=128,
                                       thumb_height=128,
                                       input_message_content=types.InputTextMessageContent(get_quote())),

        types.InlineQueryResultArticle(f'{ids}+2', 
                                       'Отправить анек',
                                       thumb_url=conf.get_value('anek_thumb_url'),
                                       thumb_width=128,
                                       thumb_height=128, 
                                       input_message_content=types.InputTextMessageContent(get_anek())),

        types.InlineQueryResultArticle(f'{ids}+3', 
                                       'У картинок ниже нет подписей потому что тг говно',
                                       description='Левая - двач, правая - пикрандом. Дуров, допили клиент тг...', 
                                       thumb_url=conf.get_value('no_tittle_thumb_url'),
                                       thumb_width=128,
                                       thumb_height=128,
                                       input_message_content=types.InputTextMessageContent("Ну и нахера ты сюда нажал")),

        types.InlineQueryResultPhoto(f'{ids}+4', 
                                       title='Отправить /b/',
                                       photo_url=get_dvach(),
                                       thumb_url=conf.get_value('bthread_thumb_url'),
                                       photo_width=128,
                                       photo_height=128),

        types.InlineQueryResultPhoto(f'{ids}+5', 
                                       title='Отправить пикрандом', 
                                       photo_url=get_picrandom(),
                                       thumb_url=conf.get_value('picrandom_thumb_url'),
                                       photo_width=128,
                                       photo_height=128),
         
                                    
    ], cache_time=1)

@bot.message_handler(func=lambda message: True)
def msg_handler(message):
    if "цитату" in message.text.lower():
        send_quote(message)
    elif "анекдот" in message.text.lower():
        send_anek(message)
    elif "пикрандом" in message.text.lower():
        send_picrandom(message)
    elif "двач" in message.text.lower():
        send_dvach(message)



def send_dvach(message):
    bot.send_photo(message.chat.id, photo=get_dvach(), disable_notification=True)

def send_picrandom(message):
    bot.send_photo(message.chat.id, photo=get_picrandom(), disable_notification=True)

def send_anek(message):
    bot.send_message(message.chat.id, get_anek())

def send_quote(message):
    bot.send_message(message.chat.id, get_quote())

def get_anek():
    file = random.choice(all_anek_files)
    data = json.load(open(file, 'r'))
    text = f"{data['text']} "
    return text

def get_quote():
    file = random.choice(all_quote_files)
    data = json.load(open(file, 'r'))
    text = f"{data['text']} \n (c) {data['author']}"
    return text

def get_dvach():
    base = conf.get_value('bthread_folder')
    pic = pathlib.Path(random.choice(all_bthread_files))
    relpic = pic.relative_to(base).as_posix()

    url:str = conf.get_value("bthread_folder_url")
    if url.endswith('/'):
        url = url[:-1]

    url = f'{url}/{relpic}'
    return url

def get_picrandom():
    base = conf.get_value('picrandom_folder')
    pic = pathlib.Path(random.choice(all_picrandom_files))
    relpic = pic.relative_to(base).as_posix()

    url:str = conf.get_value("picrandom_folder_url")
    if url.endswith('/'):
        url = url[:-1]

    url = f'{url}/{relpic}'
    return url


if __name__ == '__main__':
    load_files()
    bot.infinity_polling()
