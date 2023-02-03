import os
import pydoc
import shutil
import types
import yaml
import logging
URL = "url"
TOKEN = "token"


NEGATIVE = "negative"
STEPS = "steps"
WIDTH = "width"
HEIGHT = "height"
SHOW_PROGRESS_PREVIEW = "show_progress_preview"
SHOW_PROGRESS = "show_progress"
UPSCALE = "upscale"
GEN_CMD = "gen_cmd"
SAVE_FOLDER = "save_folder"
IMG2IMG_DENOISING_STRENGTH = "img2img_denoising_strength"
IMG2IMG_DEFAULT_PROMPT="img2img_default_prompt"

class NotFoundException(Exception):
    pass


class ConfigNeural:
    __slots__ = ("__conf_node", "__file")

    def __init__(self, file:str) -> None:
        logging.info(f"Load neural config, file - {file}")
        self.__file = file
        self.__conf_node = yaml.load(open(self.__file, "r", encoding="utf-8"), Loader=yaml.SafeLoader)

    def get_neural_config(self):
        return self.__conf_node
    
    def get_neural_setting(self, setting:str):
        items = self.get_neural_config()
        for i in items:
            if i["code"] == setting:
                return i
        raise NotFoundException()

    def get_neural_setting_value(self, setting:str):
        return self.get_neural_setting(setting)["value"]

    def set_neural_setting_value(self, setting_code, value):
        setting = self.get_neural_setting(setting_code)
        logging.info(f"Seting config {setting_code} = '{value}'")
        tp = pydoc.locate(setting["type"])
        if tp == bool:
            if str(value).lower() == 'true' or str(value).lower() == '1':
                setting["value"] = True
            if str(value).lower() == 'false' or str(value).lower() == '0':                
                setting["value"] = False
            return

        setting["value"] = tp(value)

    def save(self):
        yaml.dump(self.__conf_node, open(self.__file, "w", encoding="utf-8"))


class Config:
    __slots__ = ("__conf_node", "__file")
    def __init__(self, file:str) -> None:
        logging.info(f"Load config, file - {file}")
        self.__file = file
        self.__conf_node = yaml.load(open(self.__file, "r", encoding="utf-8"), Loader=yaml.SafeLoader)

    def get_value(self, name:str):
        return self.__conf_node[name]


def load_msgs():
    if os.path.exists("./telegram_msgs.current.yaml"):
        return Config("./telegram_msgs.current.yaml")
    return Config("./telegram_msgs.yaml")


def load_setting():
    if os.path.exists("./telegram_config.current.yaml"):
        return Config("./telegram_config.current.yaml")
    return Config("./telegram_config.yaml")


def load_wallpaper():
    if os.path.exists("./wallpaper_config.current.yaml"):
        return Config("./wallpaper_config.current.yaml")
    return Config("./wallpaper_config.yaml")


def load_neural():
    logging.info("loading neural config")

    if not os.path.exists("./telegram_neural.current.yaml"):
        shutil.copy("./telegram_neural.yaml", "./telegram_neural.current.yaml")
    return ConfigNeural("./telegram_neural.current.yaml")


def reset_neural():
    logging.info("Deleting neural config")
    os.remove("./telegram_neural.current.yaml")
    return load_neural()