from typing import Union
import requests
import io
import base64


class Base64Img:
    __slots__ = "base64String"

    def __init__(self, base64String: str) -> None:
        self.base64String = base64String


    def save(self, path):
        with open(path, 'wb') as file:
            file.write(base64.b64decode(self.base64String))

    def to_reader(self) -> io.BytesIO:
        return io.BytesIO(base64.b64decode(self.base64String))


class ProgressState():
    __slots__ = ("progress", "eta_relative", "state", "current_image")

    def __init__(self, progress: int, eta_relative: int, state, current_image: Union[Base64Img, None]) -> None:
        self.progress = progress
        self.current_image = current_image
        self.eta_relative = eta_relative
        self.state = state


class ErrorResp(Exception):
    def __init__(self, code, value) -> None:
        super().__init__()
        self.code = code
        self.value = value

    def __str__(self) -> str:
        return f'Invalid status exception, code - {self.code}, text - {self.value}'


class Config:
    __slots__ = ("model")

    def __init__(self, resp_json: dict) -> None:
        self.model = resp_json["sd_model_checkpoint"]


def __check_resp(resp):
    if resp.status_code != 200:
        raise ErrorResp(resp.status_code, resp.content)


def upscale(url, img: Base64Img, modifier: int):
    extra_single_img_template = {
        "resize_mode": 0,
        "upscaling_resize": modifier,
        "upscaler_1": "R-ESRGAN 4x+ Anime6B",
        "image": "data:image/png;base64," + img.base64String
    }

    response = requests.post(url=f'{url}/sdapi/v1/extra-single-image', json=extra_single_img_template)
    __check_resp(response)
    return Base64Img(response.json()["image"])


def gen_img(url: str,
            prompt,
            negative_prompt,
            width,
            height,
            cfg_scale=4,
            steps=40,
            sampler="Euler a",
            enable_hr=False,
            hr_scale=2,
            hr_upscaler='R-ESRGAN 4x+ Anime6B',
            denoising_strength=0.7) -> Base64Img:
    resp = requests.post(url=f'{url}/sdapi/v1/txt2img', json={
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "steps": steps,
        "width": width,
        "height": height,
        "cfg_scale": cfg_scale,
        "sampler_name": sampler,
        "seed": -1,
        "enable_hr": enable_hr,
        "hr_scale" : hr_scale,
        "ht_upscaler": hr_upscaler,
        "denoising_strength" : denoising_strength
    })
    __check_resp(resp)

    return Base64Img(resp.json()["images"][0])


def gen_img2img(url: str,
                img: Base64Img,
                prompt="anime, anime version of",
                negative_prompt="lowres, bad anatomy",
                width=512,
                height=512,
                cfg_scale=4,
                steps=40,
                sampler="Euler a",
                denoising = 0.4) -> Base64Img:
    resp = requests.post(url=f'{url}/sdapi/v1/img2img', json={
        "init_images": [
            "data:image/png;base64," + img.base64String
        ],
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "steps": steps,
        "width": width,
        "height": height,
        "cfg_scale": cfg_scale,
        "sampler_name": sampler,
        "seed": -1,
        "denoising_strength": denoising,
    })
    __check_resp(resp)

    return Base64Img(resp.json()["images"][0])


def gen_img2img_controlnet( url: str,
                            img: Base64Img,
                            control_img: Base64Img,
                            controlnet_preprocessor : str,
                            controlnet_model : str,
                            controlnet_weight : float = 0.7,
                            guidance_start : float = 0,
                            guidance_end : float = 0.85,
                            prompt="anime, anime version of",
                            negative_prompt="lowres, bad anatomy",
                            width=512,
                            height=512,
                            cfg_scale=4,
                            steps=40,
                            sampler="Euler a",
                            denoising = 0.85) -> Base64Img:
    resp = requests.post(url=f'{url}/controlnet/img2img', json={
        "init_images": [
            "data:image/png;base64," + img.base64String
        ],
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "steps": steps,
        "width": width,
        "height": height,
        "cfg_scale": cfg_scale,
        "sampler_name": sampler,
        "seed": -1,
        "denoising_strength": denoising,
        "controlnet_units" : [{
            "input_image" : "data:image/png;base64," + control_img.base64String,
            "module" : controlnet_preprocessor,
            "model" : controlnet_model,
            "weight" : controlnet_weight,
            "resize_mode": "Scale to Fit (Inner Fit)",
            "guidance_start" : guidance_start,
            "guidance_end" : guidance_end,
            "guessmode" : False
        }]
    })
    __check_resp(resp)

    return Base64Img(resp.json()["images"][0])


def controlnet_models( url: str) -> list:
    resp = requests.get(url=f'{url}/controlnet/model_list')
    __check_resp(resp)

    return resp.json()["model_list"]


def get_progress(url: str, skip_preview: bool):
    resp = requests.get(url=f'{url}/sdapi/v1/progress', params={"skip_current_image": True})
    __check_resp(resp)

    js = resp.json()
    img = Base64Img(js["current_image"]) if js["current_image"] else None
    return ProgressState(js["progress"], js["eta_relative"], js["state"], img)


def get_options(url: str) -> Config:
    resp = requests.get(url=f'{url}/sdapi/v1/options')
    __check_resp(resp)

    js = resp.json()
    return Config(js)

def get_png_info(url, img: Base64Img) -> str:
    resp = requests.post(url=f'{url}/sdapi/v1/png-info', json={
        "image": "data:image/png;base64," + img.base64String
    })
    __check_resp(resp)

    js = resp.json()
    return js["info"]

