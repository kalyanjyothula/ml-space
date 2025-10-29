import os
# import redis
from upstash_redis import Redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)


REDIS_TOKEN = os.getenv("REDIS_TOKEN", "")
REDIS_URL= os.getenv("REDIS_URL", "")

redis = Redis(url=REDIS_URL, token=REDIS_TOKEN)
