import json
import random

from elasticsearch import Elasticsearch
from flask import Blueprint, request, jsonify

from apps.common.models import NovelType, Novels, Chapters, Contents, Author, Monthly, MonthlyNovel, AppVersions, \
    NovelBanner
from apps.front.decorators import search_counter, get_top_n

bp = Blueprint("front", __name__, url_prefix='/front')
host = 'http://www.ljsb.top:5000'
@bp.route('/')
def index():
    return 'front index'

@bp.route('/channels')
def gender():
    host = 'http://%s' % request.host
    gender = request.args.get('channel')  # 1 男 0 女
    if gender == '1':
        gender = 1
    elif gender == '0':
        gender = 0
    else:
        return json.dumps({"retCode": 400, "msg": "args error", "result": []}, ensure_ascii=False)
    type_list = []
    types = NovelType.query.filter_by(gender=gender).all()
    for type in types:
        if not type.cover:
            cover_str = ""
        else:
            cover_str = type.cover
        cover = host + cover_str
        type_list.append(
            {'id': type.id, 'type': type.type, 'cover': cover, 'channelId': gender}
        )
    # {"retCode": 200, "msg": "success", "result": type_list}
    return json.dumps({"retCode": 200, "msg": "success", "result": type_list}, ensure_ascii=False)
# page页码、limit：返回数量
@bp.route('/classify')
def classify():
    classify = request.args.get('classify')
    page = request.args.get('page')
    if not page or not page.isdigit():
        page = 1

    limit = request.args.get('limit')
    if not limit or not limit.isdigit():
        limit = 10
    offset = (int(page) - 1) * int(limit)
    if classify and classify.isdigit():
        novels = Novels.query.filter_by(label=classify).order_by(-Novels.addtime).limit(limit).offset(offset).all()
    else:
        return json.dumps({"retCode": 400, "msg": "args error", "result": []}, ensure_ascii=False)
    novel_list = []
    for novel in novels:
        # 根据分类id获取分类
        novel_type = NovelType.query.get(novel.label)
        # 根据作者id获取作者
        authorId = novel.authorId
        author = Author.query.get(authorId)
        # 根据小说id获取章节总数
        countchapter = novel.chaptercount
        novel_list.append(
            {
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
             }
        )
    return json.dumps({"retCode": 200, "msg": "success", "result": novel_list, "page": page, "limit": limit}, ensure_ascii=False)

@bp.route('/author')
def author():
    authorId = request.args.get('author')
    if authorId and authorId.isdigit():
        author = Author.query.get(authorId)
    else:
        return json.dumps({"retCode": 400, "msg": "args error", "result": []}, ensure_ascii=False)
    author = {
        "id": author.id,
        "name": author.name,
        "avatar": author.avatar,
        "summary": author.summary
    }
    return json.dumps({"retCode": 200, "msg": "success", "result": author}, ensure_ascii=False)

@bp.route('/chapter')
def chapter():
    bookId = request.args.get('book')
    page = request.args.get('page')
    if not page or not page.isdigit():
        page = 1

    limit = request.args.get('limit')
    if not limit or not limit.isdigit():
        limit = 10
    offset = (int(page)-1)*int(limit)
    if bookId and bookId.isdigit():
        chapters = Chapters.query.filter_by(novelId=bookId).order_by(Chapters.chapterId).limit(limit).offset(offset).all()
    else:
        return json.dumps({"retCode": 400, "msg": "args error", "result": []}, ensure_ascii=False)
    chapter_list = []
    for chapter in chapters:
        chapter_list.append({
            "id": chapter.id,
            "name": chapter.name,
            "state": chapter.state,
            "created": chapter.created,
            "updated": chapter.updated,
            "words": chapter.words,
            "novelId": chapter.novelId,
            "num": chapter.chapterId
        })
    return json.dumps({"retCode": 200, "msg": "success", "result": chapter_list, "page": page, "limit": limit}, ensure_ascii=False)

# 请求全部章节数据
@bp.route('/chapterv')
def chapterv():
    bookId = request.args.get('book')
    if bookId and bookId.isdigit():
        chapters = Chapters.query.filter_by(novelId=bookId).order_by(Chapters.chapterId).all()
    else:
        return json.dumps({"retCode": 400, "msg": "args error", "result": []}, ensure_ascii=False)
    chapter_list = []
    for chapter in chapters:
        chapter_list.append({
            "id": chapter.id,
            "name": chapter.name,
            "state": chapter.state,
            "created": chapter.created,
            "updated": chapter.updated,
            "words": chapter.words,
            "novelId": chapter.novelId,
            "num": chapter.chapterId
        })
    return json.dumps({"retCode": 200, "msg": "success", "result": chapter_list}, ensure_ascii=False)

@bp.route('/content')
def content():
    chapterId = request.args.get('chapter')
    novelId = request.args.get('book')
    if chapterId and novelId and chapterId.isdigit() and novelId.isdigit():
        content = Contents.query.filter_by(novelId=novelId, chapterId=chapterId).first()
        if not content:
            return json.dumps({"retCode": 200, "msg": "The content doesn't exist", "result": {}}, ensure_ascii=False)
    else:
        return json.dumps({"retCode": 400, "msg": "args error", "result": {}}, ensure_ascii=False)
    content_detail = {
        'title': content.title,
        "content": content.content,
        "state": content.state,
        "created": content.created,
        "updated": content.updated,
        "words": content.words,
        "chapterId": content.chapterId
    }
    return json.dumps({"retCode": 200, "msg": "success", "result": content_detail}, ensure_ascii=False)

# 搜索功能
es = Elasticsearch()
@bp.route('/search')
@search_counter
def search():
    keyword = request.args.get('keyword')
    if len(keyword) > 10:
        return json.dumps({"retCode": 400, "msg": "关键词太长", "result": []}, ensure_ascii=False)
    page = request.args.get('page')
    if not page or not page.isdigit():
        page = 1
    limit = request.args.get('limit')
    if not limit or not limit.isdigit():
        limit = 10
    start = (int(page) - 1) * int(limit)  # 开始的文章
    end = start + int(limit)
    if keyword:
        body = {"query": {"match": {"title": keyword}}}
        result = es.search(index="novel-index", body=body)
        novel_list = []
        novelId_list = []
        for item in result["hits"]["hits"][start:end]:
            novelId_list.append(item['_id'])
        # novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
        for novel_id in novelId_list:
            novel = Novels.query.get(novel_id)
            if novel:
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
        return json.dumps({"retCode": 200, "msg": "success", "result": novel_list, "page": page, "limit": limit}, ensure_ascii=False)
    else:
        return json.dumps({"retCode": 400, "msg": "args error", "result": []}, ensure_ascii=False)

# 榜单列表返回
@bp.route('/monthly')
def monthly():
    results = Monthly.query.all()
    result_list = []
    for result in results:
        result_list.append({
            'id': result.id,
            'monthly': result.monthly
        })
    return json.dumps({"retCode": 200, "msg": "success", "result": result_list}, ensure_ascii=False)

# 根据榜单id获取小说
@bp.route('/monthnov')
def monthnov():
    monthId = request.args.get('monthly')
    page = request.args.get('page')
    if not page or not page.isdigit():
        page = 1
    limit = request.args.get('limit')
    if not limit or not limit.isdigit():
        limit = 10
    offset = (int(page) - 1) * int(limit)
    if monthId and monthId.isdigit():
        monthly_novel_list = MonthlyNovel.query.filter_by(monthlyId=monthId).limit(limit).offset(offset).all()
    else:
        return json.dumps({"retCode": 400, "msg": "args error", "result": []}, ensure_ascii=False)
    novelId_list = []
    for novel in monthly_novel_list:
        novelId_list.append({
            novel.novelId
        })
    novel_list = []
    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
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
    return json.dumps({"retCode": 200, "msg": "success", "result": novel_list, "page": page, "limit": limit}, ensure_ascii=False)

# 根据小说id获取小说
@bp.route('/book')
def book():
    bookId = request.args.get('bookId')
    if bookId and bookId.isdigit():
        novel = Novels.query.get(bookId)
    else:
        return json.dumps({"retCode": 400, "msg": "args error", "result": {}}, ensure_ascii=False)
    # 根据分类id获取分类
    novel_type = NovelType.query.get(novel.label)
    # 根据作者id获取作者
    authorId = novel.authorId
    author = Author.query.get(authorId)
    # 根据小说id获取章节总数
    countchapter = novel.chaptercount
    novel_dict = {
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
    }
    return json.dumps({"retCode": 200, "msg": "success", "result": novel_dict}, ensure_ascii=False)


# 根据bookid 采集章节id获取 内容
@bp.route('/contentv')
def contentv():
    num = request.args.get('num')
    novelId = request.args.get('book')
    if num and novelId and num.isdigit() and novelId.isdigit():
        # 获取chapterId
        chapter = Chapters.query.filter_by(novelId=novelId, chapterId=num).first()
        if not chapter:
            return json.dumps({"retCode": 200, "msg": "The content doesn't exist", "result": {}}, ensure_ascii=False)
        content = Contents.query.filter_by(chapterId=chapter.id, novelId=novelId).first()
        if not content:
            return json.dumps({"retCode": 200, "msg": "The content doesn't exist", "result": {}}, ensure_ascii=False)
    else:
        return json.dumps({"retCode": 400, "msg": "args error", "result": {}}, ensure_ascii=False)
    content_detail = {
        'title': content.title,
        "content": content.content,
        "state": content.state,
        "created": content.created,
        "updated": content.updated,
        "words": content.words,
        "chapterId": content.chapterId
    }
    return json.dumps({"retCode": 200, "msg": "success", "result": content_detail}, ensure_ascii=False)


# 版本   1安卓 2ios
@bp.route('/versions')
def versions():
    equipment = request.args.get('equipment')
    if not equipment:
        equip = 1
    elif equipment == '2':
        equip = 2
    else:
        return json.dumps({"retCode": 400, "msg": "args error", "result": {}}, ensure_ascii=False)
    app_versions = AppVersions.query.filter_by(equip_type=equip).first()
    if not app_versions:
        return json.dumps({"retCode": 200, "msg": "Version does not exist", "result": {}}, ensure_ascii=False)
    version = app_versions.version
    if equip == 1:
        version = int(version)
    return json.dumps({"retCode": 200, "msg": "success", "result": {'url': app_versions.down_url, 'version': version}}, ensure_ascii=False)

# 根据性别随机推荐小说
@bp.route('/recommend')
def recommend():
    gender = request.args.get('gender')
    if gender == '1' or gender == '0':
        offset = random.randint(0, 20)
        # 根据gender获取小说分类
        types = NovelType.query.filter_by(gender=gender).all()
        # 根据小说分类获取一本小说
        novels_list = []
        for typ in types:
            novel = Novels.query.filter_by(label=typ.id).limit(1).offset(offset).first()
            if novel:
                novels_list.append(novel)
        # 获取3本小说
        new_novels_list = novels_list[: 3]
        novel_list = []
        for novel in new_novels_list:
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
        return json.dumps({"retCode": 200, "msg": "success", "result": novel_list}, ensure_ascii=False)

    else:
        return json.dumps({"retCode": 400, "msg": "args error", "result": []}, ensure_ascii=False)

# 小说发现页banner图
@bp.route('/banner')
def banner():
    host = 'http://%s' % request.host
    banners = NovelBanner.query.filter_by(type=1).order_by(NovelBanner.rank).all()
    banner_list = []
    for banner in banners:
        cover = host + banner.imgurl
        banner_list.append({
            'imgurl': cover,
            'rank': banner.rank,
            'bookId': eval(banner.args)['bookId']
        })
    return json.dumps({"retCode": 200, "msg": "success", "result": banner_list}, ensure_ascii=False)

# 热搜关键词
@bp.route('/topsearch')
def topsearch():
    top_search_list = get_top_n(5)
    top_search = []
    for top in top_search_list:
        top_search.append(top[0])
    return json.dumps({"retCode": 200, "msg": "success", "result": top_search}, ensure_ascii=False)

# 一次返回榜单所有数据
@bp.route('/monthnovall')
def monthnovall():
    monthId_list = Monthly.query.all()
    monthly_all_list = []
    for month in monthId_list:
        monthId = month.id
        monthly_novel_list = MonthlyNovel.query.filter_by(monthlyId=monthId).all()
        novelId_list = []
        for novel in monthly_novel_list:
            novelId_list.append({
                novel.novelId
            })
        novel_list = []
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
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
        monthly_all_list.append({'monthly': monthId, 'novels': novel_list})
    return json.dumps({"retCode": 200, "msg": "success", "result": monthly_all_list}, ensure_ascii=False)


