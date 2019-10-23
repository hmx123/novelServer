# coding=utf-8
from flask import request
from functools import wraps
from exts import redis_store


# 搜索关键词装饰器
def search_counter(func):
    @wraps(func)
    def inner(*args, **kwargs):
        keyword = request.args.get('keyword')
        if keyword:
            redis_store.zincrby('HotSearch', keyword)
            return func(*args, **kwargs)
    return inner


# 取出前几条热搜
def get_top_n(num):
    '''获取排行前 N 的数据'''

    ori_data = redis_store.zrevrange('HotSearch', 0, num - 1, withscores=True)
    cleaned = [[post_id.decode(), int(count)] for post_id, count in ori_data]
    return cleaned

