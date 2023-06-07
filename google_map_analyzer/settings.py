import os
from dotenv import load_dotenv
from .logger import log

base_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(base_dir, "../.env")
log.debug(dotenv_path)
load_dotenv(dotenv_path, verbose=True)

API_KEY = os.environ.get("API_KEY")
log.debug(f"API_KEY:{API_KEY}")
