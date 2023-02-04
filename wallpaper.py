import logging
import api as api
import random
import time
import shutil
import os
import config as config
import custom_log
from PIL import Image

logger = custom_log.create_logger(__name__)


def del_all(path):
    for file_name in os.listdir(path):
        # construct full file path
        file = os.path.join(path, file_name)
        if os.path.isfile(file):
            logger.info('Deleting file: %s', file)
            os.remove(file)

def main():
    conf = config.load_wallpaper()
    
    try:
        saves = conf.get_value("save_folder")
        oldes = conf.get_value("old_folder")
        os.makedirs(saves, exist_ok=True)
        os.makedirs(oldes, exist_ok=True)

        shutil.copytree(saves, oldes, dirs_exist_ok=True)
        del_all(saves)
    except:
        pass

    i = 0
    while i < conf.get_value('count'):
        prompt = random.choice(conf.get_value("prompts"))
        logger.info(f"Gen with prompt {prompt}")
        img = api.gen_img(
            conf.get_value("url"),
            prompt,
            conf.get_value("negative"),
            conf.get_value("width"),
            conf.get_value("height"),
            cfg_scale=conf.get_value("cfg_scale"))
        
        empty = False
        image_pilled = Image.open(img.to_reader())
        
        band_values = image_pilled.getextrema()
        bands = image_pilled.getbands()
        
        for i, band in enumerate(band_values):
            band_name = bands[i]
            if band_name == 'A':
                continue

            mn = band[0] 
            mx = band[1] 

            empty = mx-mn < 10

        if empty:
            logger.warning("Generated an empty image")        
            continue

        img_upscaled = api.upscale(conf.get_value("url"), img,  conf.get_value("upscale"))

        img_upscaled.save(os.path.join(conf.get_value('save_folder'), f"img_{time.time()}_{i}.png"))
        i = i + 1

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()