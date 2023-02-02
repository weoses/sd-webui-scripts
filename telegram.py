import time
import traceback

from telebot import TeleBot;
from telebot import types;
import api
import base64
import json
import threading
import logging
import io
import os
from PIL import Image

logging.basicConfig(level=logging.INFO)
loading_image_id = None

data = json.load(open("./config.json", "rb"))
url = data["url"]
conf_node = data["telegram"]
msg_conf_node = conf_node["msgs"]

bot = TeleBot(token=conf_node["token"])


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msg_conf_node["hello"])


@bot.message_handler(commands=[conf_node["gen_cmd"]])
def generate_handler(message):
    global loading_image_id
    try:
        msgtext = message.text

        if not msgtext:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msg_conf_node["error_text"])
            return

        array = msgtext.split(" ", maxsplit=1)
        if len(array) < 2:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msg_conf_node["error_text"])
            return

        prompt_user = array[1]

        logging.info(f"Generate with prompt {prompt_user}")
        status_msg = __send_waiting(message)

        filename = f"img_{prompt2filename(prompt_user)}_{time.time()}.png"

        logging.info(f"Img name - {filename}")

        # GENERATING
        img = __generate(prompt_user, status_msg)

        # UPSCALE
        if conf_node["upscale"]:
            img = __upscale(img, status_msg)

        img.save(os.path.join(conf_node["folder"], filename))

        bot.edit_message_media(
            message_id=status_msg.message_id,
            chat_id=status_msg.chat.id,
            media=types.InputMediaPhoto(img.to_reader(), caption=msg_conf_node["completed"]))

        logging.info(f"Completed")

    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["steps"])
def negative_handler(message: types.Message):
    try:
        msgtext = message.text

        if not msgtext:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msg_conf_node["error_text"])
            return

        array = msgtext.split(" ", maxsplit=1)
        if len(array) == 2:
            try:
                int_val = int(array[1])
                if (int_val < 100):
                    conf_node["steps"] = int_val
            except:
                pass

        bot.send_message(message.chat.id, reply_to_message_id=message.id,
                         text=msg_conf_node["current_steps"].format(steps=conf_node["steps"]))
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["size"])
def size_handler(message: types.Message):
    try:
        msgtext = message.text

        if not msgtext:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msg_conf_node["error_text"])
            return

        array = msgtext.split(" ", maxsplit=2)
        if len(array) == 3:
            try:
                width = int(array[1])
                height = int(array[2])
                if (width < 1400 and height < 1400):
                    conf_node["width"] = width
                    conf_node["height"] = height
            except:
                pass

        bot.send_message(
            message.chat.id,
            reply_to_message_id=message.id,
            text=msg_conf_node["current_size"]
            .format(width=conf_node["width"],
                    height=conf_node["height"]
                    ))

    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["negative"])
def steps_handler(message: types.Message):
    try:
        msgtext = message.text

        if not msgtext:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msg_conf_node["error_text"])
            return

        array = msgtext.split(" ", maxsplit=1)
        if len(array) == 2:
            conf_node["negative"] = array[1]

        bot.send_message(message.chat.id, reply_to_message_id=message.id,
                         text=msg_conf_node["current_negative_prompt"].format(prompt=conf_node["negative"]))
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["model"])
def model_handler(message: types.Message):
    try:
        opts = api.get_options(url)
        bot.send_message(message.chat.id, reply_to_message_id=message.id,
                         text=msg_conf_node["current_model"].format(model=opts.model))
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["help"])
def help_handler(message: types.Message):
    try:
        bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msg_conf_node["help"])
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["show_progress_preview"])
def progress_preview_setting_handler(message: types.Message):
    try:
        msgtext = message.text

        if not msgtext:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msg_conf_node["error_text"])
            return

        array = msgtext.split(" ", maxsplit=1)
        if len(array) == 2:
            try:
                conf_node["show_progress_preview"] = (array[1] == 'True' or array[1] == "1")
            except:
                pass

        bot.send_message(message.chat.id,
                         reply_to_message_id=message.id,
                         text=msg_conf_node["current_show_progress_preview"].format(
                             show_progress_preview=conf_node["show_progress_preview"]))
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["show_progress"])
def progress_setting_handler(message: types.Message):
    try:
        msgtext = message.text

        if not msgtext:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msg_conf_node["error_text"])
            return

        array = msgtext.split(" ", maxsplit=1)
        if len(array) == 2:
            try:
                conf_node["show_progress"] = (array[1] == 'True' or array[1] == "1")
            except:
                pass

        bot.send_message(message.chat.id, reply_to_message_id=message.id,
                         text=msg_conf_node["current_show_progress"].format(show_progress=conf_node["show_progress"]))
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(func=lambda message: message.caption.startswith("/upscale"), content_types=["photo", "document"])
def upscale_handler(message: types.Message):
    try:
        file_id = None
        text = None
        multipler = 2
        photo = message.photo
        if photo:
            file_id = photo[-1].file_id
            text = message.caption
        else:
            photo = message.document
            if photo:
                text = message.text
                file_id = photo.file_id

        if not file_id:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msg_conf_node["error_text"])
            return
        if text:
            texts = text.split(" ", maxsplit=1)
            try:
                multipler = int(texts[1])
                if multipler > 4:
                    multipler = 4
            except:
                pass

        file_props = bot.get_file(file_id)
        data = bot.download_file(file_props.file_path)

        status_msg = __send_waiting(message)

        input_data = io.BytesIO(data)
        output_data = io.BytesIO()

        Image.open(input_data).save(output_data, format="png")
        output_data.seek(0)

        img = api.Base64Img(base64.b64encode(output_data.read()).decode("utf-8"))
        img = api.upscale(url, img, multipler)

        bot.edit_message_media(
            message_id=status_msg.message_id,
            chat_id=status_msg.chat.id,
            media=types.InputMediaPhoto(img.to_reader(), caption=msg_conf_node["completed"]))

    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(func=lambda message: message.caption.startswith("/img2img"), content_types=["photo", "document"])
def img2img_handler(message: types.Message):
    try:
        file_id = None
        text = None
        prompt = ""
        photo = message.photo
        if photo:
            file_id = photo[-1].file_id
            text = message.caption
        else:
            photo = message.document
            if photo:
                text = message.text
                file_id = photo.file_id

        if not file_id:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msg_conf_node["error_text"])
            return
        if text:
            texts = text.split(" ", maxsplit=1)
            try:
                prompt = texts[1]
            except IndexError as e:
                logging.warning(f"prompt not found warning {e}")

        file_props = bot.get_file(file_id)
        data = bot.download_file(file_props.file_path)

        status_msg = __send_waiting(message)

        input_data = io.BytesIO(data)
        output_data = io.BytesIO()

        Image.open(input_data).save(output_data, format="png")
        output_data.seek(0)

        img = api.Base64Img(base64.b64encode(output_data.read()).decode("utf-8"))
        img = api.gen_img2img(url, img, prompt=prompt)

        bot.edit_message_media(
            message_id=status_msg.message_id,
            chat_id=status_msg.chat.id,
            media=types.InputMediaPhoto(img.to_reader(), caption=msg_conf_node["completed"]))

    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


def __send_waiting(message: types.Message) -> types.Message:
    global loading_image_id

    sent_msg = None
    if not loading_image_id:
        with open(f"./res/loading.png", "rb") as ph:
            sent_msg = bot.send_photo(photo=ph, chat_id=message.chat.id, reply_to_message_id=message.id,
                                      caption=msg_conf_node["working"])
            if sent_msg.photo:
                loading_image_id = sent_msg.photo[0].file_id
    else:
        sent_msg = bot.send_photo(photo=loading_image_id, chat_id=message.chat.id, reply_to_message_id=message.id,
                                  caption=msg_conf_node["working"])

    return sent_msg


def __generate(prompt_user, sent: types.Message) -> api.Base64Img:
    global negative
    ret = []

    logging.info(f"Generating, prompt = {prompt_user}")

    def gen_func():
        img = api.gen_img(url, prompt_user, conf_node["negative"], conf_node["width"], conf_node["height"],
                          steps=conf_node["steps"])
        ret.append(img)

    th_creator = threading.Thread(target=gen_func)
    th_creator.start()

    while th_creator.is_alive():
        if conf_node["show_progress"]:
            progress = api.get_progress(url, not conf_node["show_progress_preview"])

            banner = msg_conf_node["progress"].format(progress=progress.progress, eta=int(progress.eta_relative))

            if progress.current_image:
                bot.edit_message_media(
                    message_id=sent.message_id,
                    chat_id=sent.chat.id,
                    media=types.InputMediaPhoto(progress.current_image.to_reader(), caption=banner))
            else:
                bot.edit_message_caption(
                    message_id=sent.message_id,
                    chat_id=sent.chat.id,
                    caption=banner)
        time.sleep(2)

    return ret[0]


def __upscale(img: api.Base64Img, sent: types.Message) -> api.Base64Img:
    ret = []
    logging.info(f"Upscaling...")

    bot.edit_message_caption(
        message_id=sent.message_id,
        chat_id=sent.chat.id,
        caption=msg_conf_node["upscaling"])

    def gen_func_ups():
        img_big = api.upscale(url, img, 2)
        ret.append(img_big)

    th_upscaler = threading.Thread(target=gen_func_ups)
    th_upscaler.start()
    th_upscaler.join()
    return ret[0]


def __logFatal(e: Exception, chat_id, message_id):
    logging.fatal(traceback.format_exc())
    bot.send_message(chat_id, reply_to_message_id=message_id, text=msg_conf_node["error"])


def prompt2filename(prompt: str):
    repl_prompt = prompt.replace("/", "_").replace("\\", "_")
    if len(repl_prompt) > 100:
        return repl_prompt[:100]
    return repl_prompt


def main():
    th = threading.Thread(target=main_impl)
    th.start()
    th.join()
    exit(0)


def main_impl():
    while True:
        try:
            bot.polling()
            time.sleep(10)
        except:
            pass


if __name__ == '__main__':
    main()
