import shlex
import time
from telebot import TeleBot;
from telebot import types;
import config
import api
import sys
import base64
import json
import threading
import logging
import io
import os
import custom_log
from PIL import Image
import custom_log
import chat_storage

logger = custom_log.create_logger(__name__)
logging.basicConfig(level=logging.INFO)

loading_image_id = None

conf = config.load_telegram_setting()
msgs = config.load_telegram_msgs()
neural = config.load_neural()

url = conf.get_value(config.URL)

bot = TeleBot(token=conf.get_value(config.TOKEN))



controlnet_models_num2value = chat_storage.Chat_storage()

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msgs.get_value("hello"))


@bot.message_handler(commands=["anime"])
def generate_handler(message):
    global loading_image_id
    try:
        msgtext = message.text

        if not msgtext:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msgs.get_value("error_text"))
            return

        array = msgtext.split(" ", maxsplit=1)
        if len(array) < 2:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msgs.get_value("error_text"))
            return

        prompt_user = array[1]

        logger.info(f"Generate with prompt {prompt_user}")
        status_msg = __send_waiting(message)

        filename = f"img_{prompt2filename(prompt_user)}_{time.time()}.png"

        logger.info(f"Img name - {filename}")

        # GENERATING
        img = __generate(prompt_user, status_msg)

        about = api.get_png_info(url, img)

        # UPSCALE
        if neural.get_neural_setting_value(config.UPSCALE):
            img = __upscale(img, status_msg)

        img.save(os.path.join(conf.get_value(config.SAVE_FOLDER), filename))

        bot.edit_message_media(
            message_id=status_msg.message_id,
            chat_id=status_msg.chat.id,
            media=types.InputMediaPhoto(img.to_reader(), 
                                        caption=msgs.get_value("completed").format(info=about)))

        logger.info(f"Completed")

    except Exception as e:
        __logFatal(e, message.chat.id, message.id)



@bot.message_handler(commands=["anime_hr"])
def generate_handler_hr(message):
    global loading_image_id
    try:
        msgtext = message.text

        if not msgtext:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msgs.get_value("error_text"))
            return

        array = msgtext.split(" ", maxsplit=1)
        if len(array) < 2:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msgs.get_value("error_text"))
            return

        prompt_user = array[1]

        logger.info(f"Generate with prompt {prompt_user} (HR)")
        status_msg = __send_waiting(message)

        filename = f"img_{prompt2filename(prompt_user)}_{time.time()}.png"

        logger.info(f"Img name - {filename}")

        # GENERATING
        img = __generate(prompt_user, status_msg, True)
        
        about = api.get_png_info(url, img)

        img.save(os.path.join(conf.get_value(config.SAVE_FOLDER), filename))

        bot.edit_message_media(
            message_id=status_msg.message_id,
            chat_id=status_msg.chat.id,
            media=types.InputMediaPhoto(img.to_reader(), caption=
                                        msgs.get_value("completed").format(info=about)))

        logger.info(f"Completed")

    except Exception as e:
        __logFatal(e, message.chat.id, message.id)



@bot.message_handler(commands=["steps"])
def negative_handler(message: types.Message):
    try:
        msgtext = message.text

        if not msgtext:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msgs.get_value("error_text"))
            return

        array = msgtext.split(" ", maxsplit=1)
        if len(array) == 2:
            try:
                int_val = int(array[1])
                if (int_val < 100):
                    neural.set_neural_setting_value(config.STEPS, int_val)
            except:
                pass

        bot.send_message(message.chat.id, reply_to_message_id=message.id,
                         text=msgs.get_value("current_steps").format(steps=neural.get_neural_setting_value(config.STEPS)))
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["size"])
def size_handler(message: types.Message):
    # /size 960x540
    try:
        msgtext = message.text

        if not msgtext:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msgs.get_value("error_text"))
            return

        array = msgtext.split(" ", maxsplit=2)

        if len(array) != 3:
            array = msgtext.split("x", maxsplit=2)
        
        if len(array) == 3:
            try:
                width = int(array[1])
                height = int(array[2])
                if (width < 1400 and height < 1400):
                    neural.set_neural_setting_value(config.WIDTH, width)
                    neural.set_neural_setting_value(config.HEIGHT, height)
            except:
                pass

        bot.send_message(
            message.chat.id,
            reply_to_message_id=message.id,
            text=msgs.get_value("current_size")
            .format(width=neural.get_neural_setting_value(config.WIDTH),
                    height=neural.get_neural_setting_value(config.HEIGHT)
                    ))

    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["negative"])
def steps_handler(message: types.Message):
    try:
        msgtext = message.text

        if not msgtext:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msgs.get_value("error_text"))
            return

        array = msgtext.split(" ", maxsplit=1)
        if len(array) == 2:
            neural.set_neural_setting_value(config.NEGATIVE, array[1])

        bot.send_message(message.chat.id, reply_to_message_id=message.id,
                         text=msgs.get_value("current_negative_prompt").format(prompt=neural.get_neural_setting_value(config.NEGATIVE)))
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["model"])
def model_handler(message: types.Message):
    try:
        opts = api.get_options(url)
        bot.send_message(message.chat.id, reply_to_message_id=message.id,
                         text=msgs.get_value("current_model").format(model=opts.model))
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["help"])
def help_handler(message: types.Message):
    try:
        bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msgs.get_value("help"))
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["show_progress_preview"])
def progress_preview_setting_handler(message: types.Message):
    try:
        msgtext = message.text

        if not msgtext:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msgs.get_value("error_text"))
            return

        array = msgtext.split(" ", maxsplit=1)
        if len(array) == 2:
            try:
                neural.set_neural_setting_value(config.SHOW_PROGRESS_PREVIEW, (array[1] == 'True' or array[1] == "1"))
            except:
                pass

        bot.send_message(message.chat.id,
                         reply_to_message_id=message.id,
                         text=msgs.get_value("current_show_progress_preview").format(
                             show_progress_preview=neural.get_neural_setting_value(config.SHOW_PROGRESS_PREVIEW)))
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["show_progress"])
def progress_setting_handler(message: types.Message):
    try:
        msgtext = message.text

        if not msgtext:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msgs.get_value("error_text"))
            return

        array = msgtext.split(" ", maxsplit=1)
        if len(array) == 2:
            try:
                neural.set_neural_setting_value(config.SHOW_PROGRESS, array[1] == 'True' or array[1] == "1")
            except:
                pass

        bot.send_message(message.chat.id, reply_to_message_id=message.id,
                         text=msgs.get_value("current_show_progress").format(show_progress=neural.get_neural_setting_value(config.SHOW_PROGRESS)))
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(func=lambda message: 
                       (message.content_type == 'text' and message.text and message.text.startswith('/upscale')) 
                       or 
                       (message.content_type == 'photo' and message.caption and message.caption.startswith("/upscale")),
                    content_types=["photo", "document", "text"])
def upscale_handler(message: types.Message):
    try:
        reply_msg = message.reply_to_message
        img_message = message
        if reply_msg:
            img_message = reply_msg

        file_id = None
        text = None
        multipler = 2
        photo = img_message.photo
        if photo:
            file_id = photo[-1].file_id
            text = message.caption
        else:
            photo = img_message.document
            if photo:
                text = message.text
                file_id = photo.file_id

        if not file_id:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msgs.get_value("error_text"))
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
            media=types.InputMediaPhoto(img.to_reader(), caption=msgs.get_value("completed")))

    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["img2img_denoise"])
def img2img_denoise(message: types.Message):
    try:
        msgtext = message.text

        if not msgtext:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msgs.get_value("error_text"))
            return

        array = msgtext.split(" ", maxsplit=1)
        if len(array) == 2:
            try:        
                new_denoise = float(array[1])
                neural.set_neural_setting_value(config.IMG2IMG_DENOISING_STRENGTH, new_denoise)
            except:
                bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msgs.get_value("error_text"))
                return
        
        bot.send_message(message.chat.id,
                        reply_to_message_id=message.id,
                        text=msgs.get_value("current_img2img_denoising_strength").format(
                                img2img_denoising_strength=neural.get_neural_setting_value(config.IMG2IMG_DENOISING_STRENGTH)
                                ))
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["saveconfig"])
def saveconfig_handler(message: types.Message):
    try:
        neural.save()
        bot.send_message(message.chat.id,
                        reply_to_message_id=message.id,
                        text=msgs.get_value("config_saved"))
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["resetconfig"])
def resetconfig_handler(message: types.Message):
    global neural
    try:
        neural = config.reset_neural()
        bot.send_message(message.chat.id,
                        reply_to_message_id=message.id,
                        text=msgs.get_value("config_reseted"))
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["config"])
def config_handler(message: types.Message):
    try:
        items = neural.get_neural_config()
        messages = []
        msg = "BOT CONFIG \n"
        
        kbd = types.InlineKeyboardMarkup(row_width=1)        
        for item in items:
            next_entry =  f'*{item["type"]}* `{item["code"]}` \n' 
            next_entry += f'-- {item["description"]} \n'
            next_entry += f'-- `{item["value"]}`\n'
            next_entry += f'-------\n'
            
            if len(msg) + len (next_entry) > 4096:
                messages.append({"msg" :msg, "kbd":kbd})
                msg = ""
                kbd = types.InlineKeyboardMarkup(row_width=1)
            
            msg += next_entry

            #bot.send_message(chat_id=message.chat.id, text=next_entry, parse_mode="markdown")

            payload = json.dumps({"act":"conf_chg", "name":item["code"]})        
            kbd.add(types.InlineKeyboardButton(text = f'Change {item["code"]}', callback_data=payload))

        if msg:
            messages.append({"msg" :msg, "kbd":kbd})

        
        for to_send in messages:
            bot.send_message(chat_id=message.chat.id, text=to_send["msg"], reply_markup=to_send["kbd"], parse_mode="markdown")
            

    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(func=lambda message: 
                       (message.content_type == 'text' and message.text and message.text.startswith('/img2img')) 
                       or 
                       (message.content_type == 'photo' and message.caption and message.caption.startswith("/img2img")),
                    content_types=["photo", "document", "text"])
def img2img_handler(message: types.Message):
    try:
        
        reply_msg = message.reply_to_message
        img_message = message
        if reply_msg:
            img_message = reply_msg

        file_id = None
        text = None
        prompt = None
        photo = img_message.photo
        if photo:
            file_id = photo[-1].file_id
        else:
            photo = img_message.document
            if photo:
                file_id = photo.file_id

        if not file_id:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msgs.get_value("error_text"))
            return

        text = message.caption
        if not text:
            text = message.text

       
        steps=neural.get_neural_setting_value(config.STEPS)
        prompt = neural.get_neural_setting_value(config.IMG2IMG_DEFAULT_PROMPT)
        
        controlnet=neural.get_neural_setting_value(config.IMG2IMG_CONTROLNET)

        same_koef = 0.7
        if not controlnet:
            same_koef=neural.get_neural_setting_value(config.IMG2IMG_DENOISING_STRENGTH)
        else:
            same_koef=neural.get_neural_setting_value(config.IMG2IMG_CONTROLNET_WEIGHT)

        if text:
            
            prompt_line = ""
            prompt_sp = []
            try:
                prompt_sp = text.split(" ", maxsplit=1)
                prompt_line = prompt_sp[1]
            except IndexError as e:
                logger.warning(f"img2img using default prompt")

            try:
                prompt_sp_1 = prompt_line.split(" ", maxsplit=1)
                denoising = float(prompt_sp_1[0])
                prompt_sp = prompt_sp_1
            except:
                logger.warning(f"img2img using default denoising")

            try:
                prompt_sp_1 = prompt_sp[1].split(" ", maxsplit=1)
                steps = int(prompt_sp_1[0])
                prompt_sp = prompt_sp_1
            except:
                logger.warning(f"img2img using default steps")

            try:
                prompt = str(prompt_sp[1])
            except:
                logger.warning(f"img2img using default prompt")


        if steps > 100 : 
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msgs.get_value("error_text"))
            return
        
        if same_koef > 1:
            bot.send_message(message.chat.id, reply_to_message_id=message.id, text=msgs.get_value("error_text"))
            return


        file_props = bot.get_file(file_id)
        data = bot.download_file(file_props.file_path)

        status_msg = __send_waiting(message)

        input_data = io.BytesIO(data)
        output_data = io.BytesIO()

        img_pil = Image.open(input_data)

        logger.info(f"img2img incoming {img_pil.size[0]}x{img_pil.size[1]}")

        if img_pil.size[0] > 1500 or img_pil.size[1] > 1500:
            modx = 1500 / img_pil.size[0]
            mody = 1500 / img_pil.size[1]
            mod_max = max(modx, mody)
            img_pil = img_pil.resize((int(img_pil.size[0] * mod_max), int(img_pil.size[1] * mod_max)))
            logger.info(f"img2img resizied {img_pil.size[0]}x{img_pil.size[1]}")
            return
        
        # save img 
        # ex aspect radio 1024/512 = 0.5
        # need 128 x 128
        # x = 256
        # y = 128
        # y / aspect = x
        # 128 / 0.5 = 256
        xy = img_pil.size[0] / img_pil.size[1]
        if xy >= 1 : 
            # width  > height
            # incoming - 1000 x 500
            # need - 512x512
            # xy = 2
            # calc - 512 x 256  y = (x / xy)
            need_sizes = (int(neural.get_neural_setting_value(config.WIDTH)), int(neural.get_neural_setting_value(config.WIDTH) / xy))
        else :
            # width < height
            # incoming - 500 x 1000
            # need - 512x512
            # xy = 0.5
            # calc - 256 x 512 (y * xy)
            need_sizes = (int(neural.get_neural_setting_value(config.HEIGHT) * xy)), int(neural.get_neural_setting_value(config.HEIGHT))

        img_pil.save(output_data, format="png")
        output_data.seek(0)

        img_input = api.Base64Img(base64.b64encode(output_data.read()).decode("utf-8"))
        img_output = None

        if not controlnet:
            logger.info(f"img2img generating {need_sizes[0]}x{need_sizes[1]}, prompt - {prompt}, same koef - {same_koef}, steps - {steps}")

            
            img = api.gen_img2img(url, 
                                img_input, 
                                prompt=prompt, 
                                negative_prompt=neural.get_neural_setting_value(config.NEGATIVE),
                                cfg_scale=neural.get_neural_setting_value(config.CFG_SCALE),
                                steps=steps,
                                denoising=same_koef,
                                width=need_sizes[0],
                                height=need_sizes[1] )
            img_output = img
        else:
            logger.info(f"img2img generating controlnet {need_sizes[0]}x{need_sizes[1]}, prompt - {prompt}, same koef - {same_koef}, steps - {steps}")
            img = api.gen_img2img_controlnet(url, 
                                            img_input, 
                                            img_input,
                                            neural.get_neural_setting_value(config.IMG2IMG_CONTROLNET_MODULE),
                                            neural.get_neural_setting_value(config.IMG2IMG_CONTROLNET_MODEL),
                                            cfg_scale=neural.get_neural_setting_value(config.CFG_SCALE),
                                            controlnet_weight=same_koef,
                                            guidance_start=neural.get_neural_setting_value(config.IMG2IMG_CONTROLNET_GUIDANCE_START),
                                            guidance_end=neural.get_neural_setting_value(config.IMG2IMG_CONTROLNET_GUIDANCE_END),
                                            prompt=prompt, 
                                            negative_prompt=neural.get_neural_setting_value(config.NEGATIVE),
                                            steps=steps,
                                            denoising=0.85,
                                            width=need_sizes[0],
                                            height=need_sizes[1] )
            img_output = img

        about = api.get_png_info(url, img_output)
        if neural.get_neural_setting_value(config.UPSCALE):
            img_output  = __upscale(img_output, status_msg)

        
        bot.edit_message_media(
            message_id=status_msg.message_id,
            chat_id=status_msg.chat.id,
            media=types.InputMediaPhoto(img_output.to_reader(), 
                                        caption=msgs.get_value("completed").format(info=about)))

    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.callback_query_handler(func=lambda x:json.loads(x.data)["act"]=="conf_chg")
def conf_change_callback(msg:types.CallbackQuery):
    setting_name = json.loads(msg.data)["name"]
    item = neural.get_neural_setting(setting_name)

    def next_handler(msg_in:types.Message):
        text = msg_in.text
        if text == None: return

        tokens = shlex.split(text)
        if len(tokens) < 1: return

        try:
            neural.set_neural_setting_value(setting_name, tokens[0])
            bot.send_message(reply_to_message_id=msg_in.message_id, chat_id=msg_in.chat.id, text=msgs.get_value("change_config_success"))
        except:
            bot.send_message(reply_to_message_id=msg_in.message_id, chat_id=msg_in.chat.id, text=msgs.get_value("change_config_error"))

    bot.send_message(  text=msgs.get_value("change_config_msg").format(
                                        code=item["code"],
                                        description=item["description"],
                                        type=item["type"],
                                        value=item["value"]), 
                            chat_id=msg.message.chat.id)
    bot.edit_message_reply_markup(chat_id=msg.message.chat.id, message_id=msg.message.id, reply_markup=None)
  #  bot.edit_message_reply_markup(chat_id=msg.message.chat.id, message_id=msg.message.id, reply_markup=msg.message.reply_markup)
    bot.register_next_step_handler(msg.message, next_handler)


@bot.message_handler(commands=["controlnet_model"])
def controlnet_model(message: types.Message):
    try:
        global controlnet_models_num2value

        prompt_line = None
        text = message.text
        if text:
            prompt_sp = text.split(" ", maxsplit=1)
            if len(prompt_sp) == 2:
                prompt_line = prompt_sp[1]
        
        if prompt_line:
            model_name = prompt_line
            
            try:
                ind_prompt = int(prompt_line)
                if controlnet_models_num2value.msg(message)[ind_prompt]:
                    model_name = controlnet_models_num2value.msg(message)[ind_prompt]
            except Exception as e:
                pass

            neural.set_neural_setting_value(config.IMG2IMG_CONTROLNET_MODEL, model_name)
            st = f'Controlnet model changed to {model_name}'
            bot.send_message(chat_id=message.chat.id, 
                             reply_to_message_id=message.id,
                             text=st)
            return
        
        models = api.controlnet_models(url)
        pattern = '*{ind}* - `{model}`'
        result = ''
        cnt = 0

        controlnet_models_num2value.resetmsg(message)

        for model in models:
            result += pattern.format(ind=cnt, model=model)
            controlnet_models_num2value.msg(message)[cnt]=model
            result += "\n"
            cnt += 1
        
        result += f"*CURRENT*  `{neural.get_neural_setting_value(config.IMG2IMG_CONTROLNET_MODEL)}`"

        bot.send_message(chat_id=message.chat.id, 
                         reply_to_message_id=message.id,
                         text=result, parse_mode="markdown")
        
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)

@bot.message_handler(commands=["controlnet_module"])
def controlnet_module(message: types.Message):
    try:
        prompt_line = None
        text = message.text
        if text:
            prompt_sp = text.split(" ", maxsplit=1)
            if len(prompt_sp) == 2:
                prompt_line = prompt_sp[1]
        
        if prompt_line:
            neural.set_neural_setting_value(config.IMG2IMG_CONTROLNET_MODULE, prompt_line)
            bot.send_message(chat_id=message.chat.id, 
                             reply_to_message_id=message.id,
                             text=msgs.get_value("controlnet_module_change").format(module=prompt_line))
            return
        
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["controlnet_weight"])
def controlnet_weight(message: types.Message):
    try:
        prompt_line = None
        text = message.text
        if text:
            prompt_sp = text.split(" ", maxsplit=1)
            if len(prompt_sp) == 2:
                prompt_line = prompt_sp[1]
        
        
        if prompt_line:
            neural.set_neural_setting_value(config.IMG2IMG_CONTROLNET_WEIGHT, prompt_line)
            bot.send_message(chat_id=message.chat.id, 
                             reply_to_message_id=message.id,
                             text=msgs.get_value("controlnet_weight_change").format(weight=prompt_line))
            return
        
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["cfg_scale"])
def cfg_scale(message: types.Message):
    try:
        prompt_line = None
        text = message.text
        if text:
            prompt_sp = text.split(" ", maxsplit=1)
            if len(prompt_sp) == 2:
                prompt_line = prompt_sp[1]
        
        
        if prompt_line:
            neural.set_neural_setting_value(config.CFG_SCALE, prompt_line)
            bot.send_message(chat_id=message.chat.id, 
                             reply_to_message_id=message.id,
                             text=msgs.get_value("cfg_scale_state").format(scale=prompt_line))
            return
        
        bot.send_message(chat_id=message.chat.id, 
                         reply_to_message_id=message.id,
                         text=
                         msgs.get_value("cfg_scale_state").format(scale=neural.get_neural_setting_value(config.CFG_SCALE)))
        
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)


@bot.message_handler(commands=["controlnet"])
def controlnet(message: types.Message):
    try:
        prompt_line = None
        text = message.text
        if text:
            prompt_sp = text.split(" ", maxsplit=1)
            if len(prompt_sp) == 2:
                prompt_line = prompt_sp[1]
        
        
        if prompt_line:
            val = False
            val =  'true' == prompt_line.lower() or '1' == prompt_line
                
            neural.set_neural_setting_value(config.IMG2IMG_CONTROLNET, val)
            bot.send_message(chat_id=message.chat.id, 
                             reply_to_message_id=message.id,
                             text=f'Controlnet state set to {val}')
            return
        
        report = msgs.get_value("controlnet_report").format(
            state = neural.get_neural_setting_value(config.IMG2IMG_CONTROLNET),
            module = neural.get_neural_setting_value(config.IMG2IMG_CONTROLNET_MODULE),
            model = neural.get_neural_setting_value(config.IMG2IMG_CONTROLNET_MODEL),
            weight = neural.get_neural_setting_value(config.IMG2IMG_CONTROLNET_WEIGHT),
            g_start = neural.get_neural_setting_value(config.IMG2IMG_CONTROLNET_GUIDANCE_START),
            g_end = neural.get_neural_setting_value(config.IMG2IMG_CONTROLNET_GUIDANCE_END),
        )
        
        bot.send_message(chat_id=message.chat.id, 
                         reply_to_message_id=message.id,
                         text=report,
                         parse_mode='markdown')
        
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)



@bot.message_handler(commands=["shutdown"])
def shutdown_handler(message: types.Message):
    try:
        bot.send_message(message.chat.id,
                        reply_to_message_id=message.id,
                        text="Im going to die")
    except Exception as e:
        __logFatal(e, message.chat.id, message.id)

    os._exit(2)
    

def __send_waiting(message: types.Message) -> types.Message:
    global loading_image_id

    sent_msg = None
    if not loading_image_id:
        with open(f"./res/loading.png", "rb") as ph:
            sent_msg = bot.send_photo(photo=ph, chat_id=message.chat.id, reply_to_message_id=message.id,
                                      caption=msgs.get_value("working"))
            if sent_msg.photo:
                loading_image_id = sent_msg.photo[0].file_id
    else:
        sent_msg = bot.send_photo(photo=loading_image_id, chat_id=message.chat.id, reply_to_message_id=message.id,
                                  caption=msgs.get_value("working"))

    return sent_msg


def __generate(prompt_user, sent: types.Message, hr=False) -> api.Base64Img:
    global negative
    ret = []

    logger.info(f"Generating, prompt = {prompt_user}, hr = {hr}")

    def gen_func():
        img = api.gen_img(url, 
                          prompt_user, 
                          neural.get_neural_setting_value(config.NEGATIVE), 
                          neural.get_neural_setting_value(config.WIDTH), 
                          neural.get_neural_setting_value(config.HEIGHT),
                          steps=neural.get_neural_setting_value(config.STEPS),
                          enable_hr=hr,
                          hr_scale=neural.get_neural_setting_value(config.HR_SIZE),
                          hr_upscaler=neural.get_neural_setting_value(config.HR_UPSCALER))
        ret.append(img)

    th_creator = threading.Thread(target=gen_func)
    th_creator.start()

    while th_creator.is_alive():
        if neural.get_neural_setting_value(config.SHOW_PROGRESS) and sent:
            progress = api.get_progress(url, not neural.get_neural_setting_value(config.SHOW_PROGRESS_PREVIEW))

            banner = msgs.get_value("progress").format(progress=progress.progress, eta=int(progress.eta_relative))

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
        time.sleep(3)

    return ret[0]


def __upscale(img: api.Base64Img, sent: types.Message) -> api.Base64Img:
    ret = []
    logger.info(f"Upscaling...")

    bot.edit_message_caption(
        message_id=sent.message_id,
        chat_id=sent.chat.id,
        caption=msgs.get_value("upscaling"))

    def gen_func_ups():
        img_big = api.upscale(url, img, 2)
        ret.append(img_big)

    th_upscaler = threading.Thread(target=gen_func_ups)
    th_upscaler.start()
    th_upscaler.join()
    return ret[0]


def __logFatal(e: Exception, chat_id, message_id):
    logger.exception(e)
    bot.send_message(chat_id, reply_to_message_id=message_id, text=msgs.get_value("error"))


def prompt2filename(prompt: str):
    repl_prompt = prompt.replace("/", "_").replace("\\", "_")
    if len(repl_prompt) > 100:
        return repl_prompt[:100]
    return repl_prompt


def main():
    try:
        bot.polling()
    except Exception as e:
        logger.exception(e)

if __name__ == '__main__':
    main()
