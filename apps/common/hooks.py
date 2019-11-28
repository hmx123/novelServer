# coding=utf-8
import time

from utils import zlcache
from .views import bp
from flask import request, jsonify

'''
限制访问频率的中间件: 最高频率为 3 次/秒

    1.  1535500000.00
    ------------------------
    2.  1535500000.01
    3.  1535500000.02
    4.  1535500001.00
    ------------------------
    5.  1535500001.17        now
    ------------------------
    6.  1535500001.99
    7.  1535500002.55
'''

@bp.before_request
def process_request():
    user_ip = request.headers['X-Real-Ip']
    request_key = 'Request-%s' % user_ip  # 用户请求时间的 key
    block_key = 'Block-%s' % user_ip      # 被封禁用户的 key

    # 检查用户 IP 是否被封禁
    if zlcache.get(block_key):
        print('你已被封禁')
        return jsonify({"retCode": 400, "msg": "Too many requests", "result": []})

    # 取出当前时间，及历史访问时间
    now = time.time()
    request_history = zlcache.get(request_key)
    if not request_history:
        request_history = [0, 0, 0]
    else:
        request_history = eval(request_history.decode())
    # 检查与最早访问时间的间隔
    if now - request_history.pop(0) >= 30:
        request_history.append(now)              # 滚动更新时间
        zlcache.set(request_key, request_history)  # 将时间存入缓存
        return
    else:
        # 访问超过限制，将用户 IP 加入缓存
        zlcache.set(block_key, True, 10)  # 封禁用户
        return jsonify({"retCode": 400, "msg": "Too many requests", "result": []})
