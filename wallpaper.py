import logging
import api
import random
import time
import shutil
import os
import json

def main():

    logging.basicConfig(level=logging.INFO)
    root_conf = json.load(open("./config.json", "rb"))
    wlp_conf_node = root_conf["wallpaper"]
    url = root_conf["url"]

    try:
        shutil.rmtree(wlp_conf_node["save_folder"])
    except:
        pass

    for i in range (wlp_conf_node['count']):
        prompt = random.choice(wlp_conf_node["prompts"])
        logging.info(f"Gen with prompt {prompt}")
        img = api.gen_img(
            url,
            prompt,
            wlp_conf_node["negative"],
            wlp_conf_node["width"],
            wlp_conf_node["height"])

        img_upscaled = api.upscale(url, img,  wlp_conf_node["upscale"])

        img_upscaled.save(os.path.join(wlp_conf_node['folder'], f"img_{i}.png"))

if __name__ == '__main__':
    main()