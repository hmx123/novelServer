from elasticsearch import Elasticsearch
from flask import Blueprint, request, jsonify

from apps.common.models import NovelType, Novels, Chapters, Contents, Author

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
        novels = Novels.query.filter_by(label=classify).limit(limit).offset(offset).all()
    else:
        return jsonify({"retCode": 400, "msg": "args error", "result": []})
    novel_list = []
    for novel in novels:
        novel_list.append(
            {
                "id": novel.id,
                "name": novel.name,
                "cover": novel.cover,
                "summary": novel.summary,
                "label": novel.label,
                "state": novel.state,
                "enabled": novel.enabled,
                "words": novel.words,
                "created": novel.created,
                "updated": novel.updated,
                "authorId": novel.authorId,
                "extras": ""
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
            "novelId": chapter.novelId
        })
    return jsonify({"retCode": 200, "msg": "success", "result":chapter_list})

@bp.route('/content')
def content():
    chapterId = request.args.get('chapter')
    novelId = request.args.get('book')
    if chapterId and novelId and chapterId.isdigit() and novelId.isdigit():
        content = Contents.query.filter_by(chapterId=chapterId, novelId=novelId).first()
    else:
        return jsonify({"retCode": 400, "msg": "args error", "result": []})
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
        limit = 2
    start = (int(page) - 1) * int(limit)  # 开始的文章
    end = start + int(limit)
    if keyword:
        body = {"query": {"match": {"title": keyword}}}
        result = es.search(index="novel-index", body=body)
        novels = []
        for item in result["hits"]["hits"][start:end]:
            novelid = item['_id']
            novel = Novels.query.get(novelid)
            novels.append({
                "id": novel.id,
                "name": novel.name,
                "cover": novel.cover,
                "summary": novel.summary,
                "label": novel.label,
                "state": novel.state,
                "enabled": novel.enabled,
                "words": novel.words,
                "created": novel.created,
                "updated": novel.updated,
                "authorId": novel.authorId,
                "extras": ""
            })
        return jsonify({"retCode": 200, "msg": "success", "result": novels})
    else:
        return jsonify({"retCode": 400, "msg": "args error", "result": []})


