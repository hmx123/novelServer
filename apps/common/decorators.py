import os

import pymysql
import requests
from lxml import etree

from utils.zlcache import my_lpush


headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36'
    }
MySQLUser = os.environ.get('MySQLUser')
MySQLPassword = os.environ.get('MySQLPassword')

# 每1小时更新一次  新笔趣阁
def xbqg_1h_data():
    # 链接数据库
    conn = pymysql.connect(host='localhost', user='%s' % MySQLUser, passwd='%s' % MySQLPassword, db='novels', charset='utf8')
    cursor = conn.cursor()
    url = 'http://www.xbiquge.la/'
    response = requests.get(url=url, headers=headers, verify=False)
    response.encoding = 'utf-8'
    html = etree.HTML(response.text)
    # 解析首页的最新更新链接
    novel_href_list = html.xpath('//div[@id="newscontent"]/div[@class="r"]/ul/li/span/a/@href')
    novel_name_list = html.xpath('//div[@id="newscontent"]/div[@class="r"]/ul/li/span/a/text()')
    novel_author_list = html.xpath('//div[@id="newscontent"]/div[@class="r"]/ul/li/span[@class="s5"]/text()')
    for x in range(len(novel_href_list)):
        # 获取小说作者id
        sql = "select id from author where name='%s';"
        fin = cursor.execute(sql % novel_author_list[x])
        authorId = ''
        if fin:
            authorId = cursor.fetchone()[0]
        sql = "select id from novels where name='%s' and authorId='%s' and novel_web!=2;"
        cursor.execute(sql % (novel_name_list[x], authorId))
        if cursor.fetchone():
            continue
        redis_key = 'xbiquspider:start_urls'
        my_lpush(redis_key, novel_href_list[x])
    cursor.close()
    conn.close()

# 每1小时更新一次   全本小说网
def qb5_1h_data():
    conn = pymysql.connect(host='localhost', user='%s' % MySQLUser, passwd='%s' % MySQLPassword, db='novels', charset='utf8')
    cursor = conn.cursor()
    url = 'https://www.qb5.tw/'
    response = requests.get(url=url, headers=headers, verify=False)
    response.encoding = 'gbk'
    html = etree.HTML(response.text)
    novel_href_list = html.xpath('//ul[@class="titlelist"]/li/div[@class="zp"]/a/@href')
    novel_name_list = html.xpath('//ul[@class="titlelist"]/li/div[@class="zp"]/a/text()')
    novel_author_list = html.xpath('//ul[@class="titlelist"]/li/div[@class="author"]/text()')
    # 获取小说名字和作者 判断其他 webid 没有采集过
    for x in range(len(novel_href_list)):
        # 获取小说作者id
        sql = "select id from author where name='%s';"
        fin = cursor.execute(sql % novel_author_list[x])
        authorId = ''
        if fin:
            authorId = cursor.fetchone()[0]
        sql = "select id from novels where name='%s' and authorId='%s' and novel_web!=3;"
        cursor.execute(sql % (novel_name_list[x], authorId))
        if cursor.fetchone():
            continue
        redis_key = 'qb5tw:start_urls'
        my_lpush(redis_key, novel_href_list[x])
    cursor.close()
    conn.close()







