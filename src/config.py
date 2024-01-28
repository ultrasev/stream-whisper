import os

from dotenv import load_dotenv

load_dotenv()
REDIS_SERVER = os.getenv('REDIS_SERVER')

if REDIS_SERVER is None:
    raise EnvironmentError(
        "The REDIS_SERVER environment variable is not set. "
        "Please set it in your .env file or as an environment variable.")
