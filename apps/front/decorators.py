# coding=utf-8
from flask import request
from functools import wraps

from apps.common.models import NovelType, Author, Cartoon, CartoonType, CartoonChapter
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

# 漫画搜索关键词装饰器
def cartoon_search_counter(func):
    @wraps(func)
    def inner(*args, **kwargs):
        keyword = request.args.get('keyword')
        if keyword:
            redis_store.zincrby('CartoonHotSearch', keyword)
            return func(*args, **kwargs)
    return inner

# 取出前几条热搜
def get_top_n(num):
    '''获取排行前 N 的数据'''

    ori_data = redis_store.zrevrange('HotSearch', 0, num - 1, withscores=True)
    cleaned = [[post_id.decode(), int(count)] for post_id, count in ori_data]
    return cleaned

# 取出漫画前几条热搜
def cartoon_get_top_n(num):
    '''获取排行前 N 的数据'''

    ori_data = redis_store.zrevrange('CartoonHotSearch', 0, num - 1, withscores=True)
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
        if novel.updated:
            clickc = int(str(novel.updated)[-5:-1])
        else:
            clickc = 1046
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
            "countchapter": countchapter,
            "clickc": clickc,
            "type": 1
        })
    return novel_list

# 漫画对象解析返回漫画解析好的list
def cartoonOb_cartoonList(cartoons, host):
    # 根据id获取漫画
    cartoon_list = []
    for cartoonId in cartoons:
        cartoon = Cartoon.query.get(cartoonId.cartoonId)
        if cartoon:
            label_arr = []
            label_str = cartoon.label
            label_list = label_str.split(',')
            # 根据分类id获取分类
            for label in label_list:
                cartoon_type = CartoonType.query.get(label)
                if cartoon_type:
                    label_arr.append(cartoon_type.type)
            # 获取封面链接
            cover_href = '%s/static/cartoon/%s/%s' % (host, cartoon.id, cartoon.cover)
            # 获取最新一话的名称
            newest = CartoonChapter.query.filter_by(cid=cartoon.id, chapterId=cartoon.chaptercount).first()
            if not newest:
                newest_chapter = '第%s话' % cartoon.chaptercount
            else:
                newest_chapter = newest.name
            cartoon_dict = {
                'id': cartoon.id,
                'name': cartoon.name,
                'author': cartoon.author,
                'statu': cartoon.statu,
                'label': label_arr,
                'hotcount': cartoon.hotcount,
                'subcount': cartoon.subcount,
                'info': cartoon.info,
                'newest': newest_chapter,
                'chaptercount': cartoon.chaptercount,
                'updatetime': str(cartoon.updatetime),
                'cover': cover_href}
            cartoon_list.append(cartoon_dict)
    return cartoon_list
