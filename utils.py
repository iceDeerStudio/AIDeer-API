from flask import current_app
from PIL import Image
from io import BytesIO
import hashlib
import string
import random
import requests


def generate_random_string(length) -> str:
    """
    Generate a random string with the specified length.
    """
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def save_avatar(avatar) -> str:
    """
    Save the avatar to the static folder in WEBP format and return the hash of the image.
    """
    avatar_image = Image.open(avatar)
    bytes_buffer = BytesIO()
    avatar_image.save(bytes_buffer, format="WEBP")
    bytes_buffer.seek(0)
    avatar_hash = hashlib.sha256(bytes_buffer.read()).hexdigest()
    bytes_buffer.seek(0)
    avatar_image.save(f"static/avatars/{avatar_hash}.webp")
    return avatar_hash


def get_wechat_login_info(code) -> tuple[str, str]:
    """
    Get the user's openid and session_key from WeChat.
    """
    appid = current_app.config["WECHAT_APPID"]
    secret = current_app.config["WECHAT_SECRET"]
    url = f"https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={code}&grant_type=authorization_code"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("WeChat server error")
    data = response.json()
    if "errcode" in data and data["errcode"] != 0:
        raise Exception(f"WeChat server error: {data['errmsg']}")
    openid = data["openid"]
    session_key = data["session_key"]
    return openid, session_key

def check_wechat_login_info(openid, session_key) -> bool:
    """
    Check the user's openid and session_key from WeChat.
    """
    access_token = get_access_token()
    signature = hashlib.sha256(f"{session_key}{openid}".encode("utf-8")).hexdigest()
    url = f"GET https://api.weixin.qq.com/wxa/checksession?access_token={access_token}&signature={signature}&openid={openid}&sig_method=hmac_sha256"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("WeChat server error")
    data = response.json()
    if "errcode" in data and data["errcode"] != 0:
        if data["errcode"] == 87009:
            return False
        raise Exception(f"WeChat server error: {data['errmsg']}")
    return True

def refresh_access_token() -> tuple[str, int]:
    """
    Get the access token from WeChat and return the access token and the expiration time.
    """
    app_id = current_app.config["WECHAT_APP_ID"]
    app_secret = current_app.config["WECHAT_APP_SECRET"]
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("WeChat server error")
    if "errcode" in response.json():
        raise Exception(f"WeChat server error: {response.json()['errmsg']}")
    data = response.json()
    return data["access_token"], data["expires_in"]


def get_access_token():
    """
    Get the access token from Redis. If the access token is not found or is about to expire, refresh it and store it in Redis.
    """
    redis_client = current_app.config["REDIS_CLIENT"]
    access_token = redis_client.get("wechat_access_token")
    if not access_token or redis_client.ttl("wechat_access_token") < 300:
        access_token = refresh_and_store_access_token()
    return access_token.decode("utf-8")


def refresh_and_store_access_token():
    """
    Refresh the access token and store it in Redis.
    """
    redis_client = current_app.config["REDIS_CLIENT"]
    access_token, expires_in = refresh_access_token()
    redis_client.set("wechat_access_token", access_token, ex=expires_in - 60)
    return access_token