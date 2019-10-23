# coding=utf-8
import requests
from flask import jsonify
from lxml import etree

from utils.zlcache import my_lpush


def index_12h_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36'
    }
    url = 'http://www.xbiquge.la/'
    response = requests.get(url=url, headers=headers, verify=False)
    response.encoding = 'utf-8'
    html = etree.HTML(response.text)
    # 解析首页的最新更新链接
    new_a_list = html.xpath('//div[@id="newscontent"]/div[@class="l"]/ul/li/span[2]/a/@href')
    for a in new_a_list:
        redis_key = 'xbiquspider:start_urls'
        my_lpush(redis_key, a)
    return jsonify({'code': 200, 'msg': '添加采集任务成功，已在后台采集'})
