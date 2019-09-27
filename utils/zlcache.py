from exts import redis_store

def set(key, value, timeout=60):
    return redis_store.set(key, value, timeout)

def get(key):
    return redis_store.get(key)


def delete(key):
    return redis_store.delete(key)

def my_lpush(key, value):
    redis_store.lpush(key, value)


