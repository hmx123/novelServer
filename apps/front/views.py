from flask import Blueprint, request, jsonify

from apps.common.models import NovelType, Novels, Chapters, Contents

bp = Blueprint("front", __name__, url_prefix='/front')

@bp.route('/')
def index():
    return 'front index'

@bp.route('/gender')
def gender():
    gender = request.args.get('gender')  # 1 男 0 女
    if gender == '1':
        gender = 1
    elif gender == '0':
        gender = 0
    else:
        return jsonify({"retCode": 400, "msg": "args error", "result": []})
    type_list = []
    types = NovelType.query.filter_by(gender=gender).all()
    for type in types:
        type_list.append(
            {'id': type.id, 'type': type.type}
        )
    # {"retCode": 200, "msg": "success", "result": type_list}
    return jsonify({"retCode": 200, "msg": "success", "result": type_list})

@bp.route('/classify')
def classify():
    classify = request.args.get('classify')
    if classify and classify.isdigit():
        novels = Novels.query.filter_by(label=classify).all()
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

@bp.route('/chapter')
def chapter():
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
            "number": chapter.number,
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
        "number": content.number,
        "content": content.content,
        "state": content.state,
        "created": content.created,
        "updated": content.updated,
        "words": content.words,
        "chapterId": content.chapterId
    }
    return jsonify({"retCode": 200, "msg": "success", "result": content_detail})

# 搜索功能
@bp.route('/search')
def search():
    pass

