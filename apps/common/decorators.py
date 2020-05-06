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
    # novel_href_list = html.xpath('//div[@id="newscontent"]/div[@class="r"]/ul/li/span/a/@href')
    novel_href_list = html.xpath('//div[@id="newscontent"]/div/ul/li/span[@class="s2"]/a/@href')
    # novel_name_list = html.xpath('//div[@id="newscontent"]/div[@class="r"]/ul/li/span/a/text()')
    novel_name_list = html.xpath('//div[@id="newscontent"]//ul/li/span[@class="s2"]/a/text()')
    # novel_author_list = html.xpath('//div[@id="newscontent"]/div[@class="r"]/ul/li/span[@class="s5"]/text()')
    novel_author_list = html.xpath('//div[@id="newscontent"]/div/ul/li/span[contains(@class,"s4") or contains(@class,"s5")]/text()')
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

# 每周一凌晨清空阅读分钟数 更新漫画上周总数
def ever_week_monday():
    conn = pymysql.connect(host='localhost', user='%s' % MySQLUser, passwd='%s' % MySQLPassword, db='novels',
                           charset='utf8')
    cursor = conn.cursor()
    sql = "update user set read_time=0;"
    cursor.execute(sql)
    sql2 = "select count(id) from cartoonid_typeid;"
    cursor.execute(sql2)
    count = cursor.fetchone()[0]
    sql3 = "update cartoon_count set count='%s' where id=1;"
    cursor.execute(sql3 % count)
    conn.commit()
    cursor.close()
    conn.close()

# 每天采集两次更新漫画(漫画5)
def cartoon_spider():
    url = 'http://www.kuman5.com/rank/5-1.html'
    response = requests.get(url=url, headers=headers, verify=False)
    response.encoding = 'utf8'
    html = etree.HTML(response.text)
    href_list = html.xpath('//ul[@class="mh-list col7"]/li/div/a/@href')
    # http://www.kuman5.com/21370/
    for href in href_list:
        redis_key = 'manhuawuspider:start_urls'
        new_url = 'http://www.kuman5.com' + href
        my_lpush(redis_key, new_url)








