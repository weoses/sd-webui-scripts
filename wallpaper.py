import logging
import api
import random
import time
import shutil
import os
import json
import config

def main():

    logging.basicConfig(level=logging.INFO)
    conf = config.load_wallpaper()
    try:
        shutil.rmtree(conf.get_value("save_folder"))
    except:
        pass

    for i in range (conf.get_value('count')):
        prompt = random.choice(conf.get_value("prompts"))
        logging.info(f"Gen with prompt {prompt}")
        img = api.gen_img(
            conf.get_value("url"),
            prompt,
            conf.get_value("negative"),
            conf.get_value("width"),
            conf.get_value("height"),
            cfg_scale=conf.get_value("cfg_scale"))

        img_upscaled = api.upscale(conf.get_value("url"), img,  conf.get_value("upscale"))

        img_upscaled.save(os.path.join(conf.get_value('folder'), f"img_{time.time()}_{i}.png"))

if __name__ == '__main__':
    main()