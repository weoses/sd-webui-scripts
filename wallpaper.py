import logging
import api as api
import random
import time
import shutil
import os
import config as config
import custom_log
import pathlib
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
        logger.info(f"Copy tree {saves} -> {oldes}")
        shutil.copytree(saves, oldes, dirs_exist_ok=True)
        del_all(saves)
    except Exception as e:
        logger.warning(e)

    model = api.get_options(conf.get_value('url')).model

    img_index = 0
    while img_index < conf.get_value('count'):
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
        
        for band_index, band in enumerate(band_values):
            band_name = bands[band_index]
            if band_name == 'A':
                continue

            mn = band[0] 
            mx = band[1] 

            empty = mx-mn < 10

        if empty:
            logger.warning("Generated an empty image")        
            continue

        img_upscaled = api.upscale(conf.get_value("url"), img,  conf.get_value("upscale"))
        
        fname = f'img_{time.time()}_{img_index}.png'

        save_img_path = pathlib.Path(conf.get_value('save_folder'), fname)
        save_prompt_path = pathlib.Path(conf.get_value('save_folder'), f"{fname}.prompt.txt")
        save_model_path = pathlib.Path(conf.get_value('save_folder'), f"{fname}.model.txt")

        img_upscaled.save(save_img_path)
        save_prompt_path.write_text(prompt, encoding='utf-8')
        save_model_path.write_text(model, encoding='utf-8')
       
        img_index = img_index + 1

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()