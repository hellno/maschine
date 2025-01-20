import base64
import os


def generate_random_secret() -> str:
    return base64.b64encode(os.urandom(32)).decode("utf-8")
