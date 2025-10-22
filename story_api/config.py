import os
import redis
from upstash_redis import Redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)


REDIS_TOKEN = os.getenv("REDIS_TOKEN", "")
REDIS_URL= os.getenv("REDIS_URL", "")

redis = Redis(url=REDIS_URL, token=REDIS_TOKEN)


# Create reusable Redis connection
# redis_client = redis.StrictRedis(
#     host=REDIS_HOST,
#     port=REDIS_PORT,
#     db=REDIS_DB,
#     password=REDIS_PASSWORD,
#     decode_responses=True
# )


# def test_redis_connection():
#     try:
#         redis_client.ping()
#         print("✅ Redis connection successful")
#     except Exception as e:
#         print("❌ Redis connection failed:", e)