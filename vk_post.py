import os
import vk_api
import logging
import config as config
import custom_log
from datetime import datetime
import pathlib

logger = custom_log.create_logger(__name__)

conf = config.load_vk_post()

def main():
    group_id = conf.get_value("group_id")
    album_id = conf.get_value("album_id")

    folder = conf.get_value("folder")

    vk_session = vk_api.VkApi(
        app_id=conf.get_value("app_id"),
        client_secret=conf.get_value("app_secret"),
        login=conf.get_value("login"),
        password=conf.get_value("password"))

    logging.info(f"Auth...")
    vk_session.auth()
    vk = vk_session.get_api()

    upload = vk_api.VkUpload(vk_session)
    photos = []
    logging.info(f"Uploading photos...")

    files = os.listdir(folder)
    current_files_str = ','.join(files).lower()
    try:
        with open("./vk_last", 'r+') as f:
            last_files_str = f.read()

            if current_files_str == last_files_str:
                logging.info("Files not changed!")
                return
    except:
        pass

    with open("./vk_last", 'w') as f:
        f.write(current_files_str)

    for file in files:
        if str(file).endswith('.txt'):
            continue

        prompt = 'Stable diffusion'
        model = ''
        
        img_file = pathlib.Path(folder, file)
        
        img_prompt_file = pathlib.Path(folder, file+".prompt.txt")
        if img_prompt_file.exists():
            prompt = img_prompt_file.read_text(encoding='utf-8')
        
        img_model_file = pathlib.Path(folder, file+".model.txt")
        if img_model_file.exists():
            model = img_model_file.read_text(encoding='utf-8')

        descr = f'Model: {model}\n Prompt: {prompt}'

        photo_item = upload.photo(str(img_file), album_id=album_id, group_id=group_id, description=descr)
        uploaded_name = f"photo{photo_item[0]['owner_id']}_{photo_item[0]['id']}"
        logging.info(f"Photo {file} uploaded as {uploaded_name}")
        photos.append(uploaded_name)

    logging.info(f"Creating post")
    vk.wall.post(message=f'Images {datetime.today().strftime("%Y-%m-%d")}', owner_id=-group_id, from_group="1", attachments=','.join(photos))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()