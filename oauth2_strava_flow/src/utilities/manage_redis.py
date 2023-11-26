from utilities.logger import info, warn
import redis
import time
import os

REDIS_HOST = os.getenv("REDIS_HOST","localhost")
REDIS_PORT = os.getenv("REDIS_PORT",6379)
REDIS_DB = os.getenv("REDIS_DB",0)

def checkRedisConn():
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, socket_connect_timeout=2, socket_timeout=10, decode_responses=True)
    is_connected = False
    while not is_connected:
        try:
            redis_client.ping()
            is_connected = True
            info(f"Correctly connected to the redis database {REDIS_HOST}:{REDIS_PORT} on db {REDIS_DB}")
            return redis_client
        except Exception as e:
            warn(f"Database connection error...")
            time.sleep(3)