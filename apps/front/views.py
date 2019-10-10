import random

from elasticsearch import Elasticsearch
from flask import Blueprint, request, jsonify

from apps.common.models import NovelType, Novels, Chapters, Contents, Author, Monthly, MonthlyNovel, AppVersions

bp = Blueprint("front", __name__, url_prefix='/front')
host = 'http://www.ljsb.top:5000'
@bp.route('/')
def index():
    return 'front index'

@bp.route('/channels')
def gender():
    gender = request.args.get('channel')  # 1 男 0 女
    if gender == '1':
        gender = 1
    elif gender == '0':
        gender = 0
    else:
        return jsonify({"retCode": 400, "msg": "args error", "result": []})
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
    return jsonify({"retCode": 200, "msg": "success", "result": type_list})
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
        return jsonify({"retCode": 400, "msg": "args error", "result": []})
    novel_list = []
    for novel in novels:
        # 根据分类id获取分类
        novel_type = NovelType.query.get(novel.label)
        # 根据作者id获取作者
        authorId = novel.authorId
        author = Author.query.get(authorId)
        # 根据小说id获取章节总数
        countchapter = Chapters.query.filter_by(novelId=novel.id).count()
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
    return jsonify({"retCode": 200, "msg": "success", "result": novel_list})

@bp.route('/author')
def author():
    authorId = request.args.get('author')
    if authorId and authorId.isdigit():
        author = Author.query.get(authorId)
    else:
        return jsonify({"retCode": 400, "msg": "args error", "result": []})
    author = {
        "id": author.id,
        "name": author.name,
        "avatar": author.avatar,
        "summary": author.summary
    }
    return jsonify({"retCode": 200, "msg": "success", "result": author})

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
        return jsonify({"retCode": 400, "msg": "args error", "result": []})
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
    return jsonify({"retCode": 200, "msg": "success", "result":chapter_list})

# 请求全部章节数据
@bp.route('/chapterv')
def chapterv():
    bookId = request.args.get('book')
    if bookId and bookId.isdigit():
        chapters = Chapters.query.filter_by(novelId=bookId).order_by(Chapters.chapterId).all()
    else:
        return jsonify({"retCode": 400, "msg": "args error", "result": []})
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
    return jsonify({"retCode": 200, "msg": "success", "result": chapter_list})

@bp.route('/content')
def content():
    chapterId = request.args.get('chapter')
    novelId = request.args.get('book')
    if chapterId and novelId and chapterId.isdigit() and novelId.isdigit():
        content = Contents.query.filter_by(chapterId=chapterId, novelId=novelId).first()
        if not content:
            return jsonify({"retCode": 200, "msg": "The content doesn't exist", "result": {}})
    else:
        return jsonify({"retCode": 400, "msg": "args error", "result": {}})
    content_detail = {
        'title': content.title,
        "content": content.content,
        "state": content.state,
        "created": content.created,
        "updated": content.updated,
        "words": content.words,
        "chapterId": content.chapterId
    }
    return jsonify({"retCode": 200, "msg": "success", "result": content_detail})

# 搜索功能
es = Elasticsearch()
@bp.route('/search')
def search():
    keyword = request.args.get('keyword')
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
            # 根据分类id获取分类
            novel_type = NovelType.query.get(novel.label)
            # 根据作者id获取作者
            authorId = novel.authorId
            author = Author.query.get(authorId)
            # 根据小说id获取章节总数
            countchapter = Chapters.query.filter_by(novelId=novel.id).count()
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
        return jsonify({"retCode": 200, "msg": "success", "result": novel_list})
    else:
        return jsonify({"retCode": 400, "msg": "args error", "result": []})

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
    return jsonify({"retCode": 200, "msg": "success", "result": result_list})

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
        return jsonify({"retCode": 400, "msg": "args error", "result": []})
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
        countchapter = Chapters.query.filter_by(novelId=novel.id).count()
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
    return jsonify({"retCode": 200, "msg": "success", "result": novel_list})

# 根据小说id获取小说
@bp.route('/book')
def book():
    bookId = request.args.get('bookId')
    if bookId and bookId.isdigit():
        novel = Novels.query.get(bookId)
    else:
        return jsonify({"retCode": 400, "msg": "args error", "result": {}})
    # 根据分类id获取分类
    novel_type = NovelType.query.get(novel.label)
    # 根据作者id获取作者
    authorId = novel.authorId
    author = Author.query.get(authorId)
    # 根据小说id获取章节总数
    countchapter = Chapters.query.filter_by(novelId=novel.id).count()
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
    return jsonify({"retCode": 200, "msg": "success", "result": novel_dict})


# 根据bookid 采集章节id获取 内容
@bp.route('/contentv')
def contentv():
    num = request.args.get('num')
    novelId = request.args.get('book')
    if num and novelId and num.isdigit() and novelId.isdigit():
        # 获取chapterId
        chapter = Chapters.query.filter_by(novelId=novelId, chapterId=num).first()
        if not chapter:
            return jsonify({"retCode": 200, "msg": "The content doesn't exist", "result": {}})
        content = Contents.query.filter_by(chapterId=chapter.id, novelId=novelId).first()
        if not content:
            return jsonify({"retCode": 200, "msg": "The content doesn't exist", "result": {}})
    else:
        return jsonify({"retCode": 400, "msg": "args error", "result": {}})
    content_detail = {
        'title': content.title,
        "content": content.content,
        "state": content.state,
        "created": content.created,
        "updated": content.updated,
        "words": content.words,
        "chapterId": content.chapterId
    }
    return jsonify({"retCode": 200, "msg": "success", "result": content_detail})


# 版本   1安卓 2ios
@bp.route('/versions')
def versions():
    equipment = request.args.get('equipment')
    if not equipment:
        equip = 1
    elif equipment == '2':
        equip = 2
    else:
        return jsonify({"retCode": 400, "msg": "args error", "result": {}})
    app_versions = AppVersions.query.filter_by(equip_type=equip).first()
    if not app_versions:
        return jsonify({"retCode": 200, "msg": "Version does not exist", "result": {}})
    version = app_versions.version
    if equip == 1:
        version = int(version)
    return jsonify({"retCode": 200, "msg": "success", "result": {'url': app_versions.down_url, 'version': version}})

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
            countchapter = Chapters.query.filter_by(novelId=novel.id).count()
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
        return jsonify({"retCode": 200, "msg": "success", "result": novel_list})

    else:
        return jsonify({"retCode": 400, "msg": "args error", "result": []})

