# coding=utf-8
from flask import request
from functools import wraps

from apps.common.models import NovelType, Author
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

# 小说对象返回小说解析好的list
def novelOb_novelList(novels):
    novel_list = []
    for novel in novels:
        # 根据分类id获取分类
        novel_type = NovelType.query.get(novel.label)
        # 根据作者id获取作者
        authorId = novel.authorId
        author = Author.query.get(authorId)
        # 根据小说id获取章节总数
        countchapter = novel.chaptercount
        novel_list.append({
            "id": novel.id,
            "name": novel.name,
            "cover": novel.cover,
            "summary": novel.summary,
            "label": novel_type.type,
            "state": novel.state,
            "enabled": novel.enabled,
            "words": novel.words,
            "created": novel.created,
            "updated": novel.updated,
            "authorId": authorId,
            "author": author.name,
            "extras": "",
            "countchapter": countchapter
        })
    return novel_list


