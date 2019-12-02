import json
import random

from elasticsearch import Elasticsearch
from flask import Blueprint, request

from apps.common.models import NovelType, Novels, Chapters, Contents, Author, Monthly, MonthlyNovel, AppVersions, \
    NovelBanner, NovelGroup, GroupidNovelid, ComposePage
from apps.front.decorators import search_counter, get_top_n, novelOb_novelList

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
    types = NovelType.query.filter_by(gender=gender, version=1).all()
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
    chapter_num = offset
    for chapter in chapters:
        chapter_num += 1
        chapter_list.append({
            "id": chapter.id,
            "name": chapter.name,
            "state": chapter.state,
            "created": chapter.created,
            "updated": chapter.updated,
            "words": chapter.words,
            "novelId": chapter.novelId,
            "num": chapter.chapterId,
            "chapternum": chapter_num
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
    chapter_num = 0
    for chapter in chapters:
        chapter_num += 1
        chapter_list.append({
            "id": chapter.id,
            "name": chapter.name,
            "state": chapter.state,
            "created": chapter.created,
            "updated": chapter.updated,
            "words": chapter.words,
            "novelId": chapter.novelId,
            "num": chapter.chapterId,
            "chpternum": chapter_num
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
    if len(keyword) > 20:
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
        body = {"query": {"match": {"title": keyword}}, "size": 50}
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
    results = Monthly.query.filter_by(type_one=1).all()
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
    novels = []
    for novel in monthly_novel_list:
        novel_result = Novels.query.get(novel.novelId)
        if novel_result:
            novels.append(novel_result)
    novel_list = novelOb_novelList(novels)

    return json.dumps({"retCode": 200, "msg": "success", "result": novel_list, "page": page, "limit": limit}, ensure_ascii=False)

# 根据小说id获取小说
@bp.route('/book')
def book():
    bookId = request.args.get('bookId')
    if bookId and bookId.isdigit():
        novel = Novels.query.get(bookId)
    else:
        return json.dumps({"retCode": 400, "msg": "args error", "result": {}}, ensure_ascii=False)
    if novel:
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
    return json.dumps({"retCode": 400, "msg": "小说不存在", "result": {}}, ensure_ascii=False)

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
        novel_list = novelOb_novelList(new_novels_list)

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

        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
        novel_list = novelOb_novelList(novels)

        monthly_all_list.append({'monthly': monthId, 'novels': novel_list})
    return json.dumps({"retCode": 200, "msg": "success", "result": monthly_all_list}, ensure_ascii=False)

# 根据group分类获取小说

# 精选页接口 start
# 今日精选
@bp.route('/handpick')
def handpick():
    type = request.args.get('type')
    # today(获取女生分类中 热搜榜 古代言情)
    # must(今日必读 女生分类 热榜现代言情)
    # god(男生热搜 4本)
    # recommend(人气榜单 8本)
    # over(完本榜单5本)
    # new(新书5本)
    # weeksearch(热搜榜8本)
    # weekupdate(更新榜4本)
    # like(完本榜5本)
    if type == 'today':
        Monthly_list = MonthlyNovel.query.filter_by(monthlyId=12).all()
        novelId_list = []
        for monthly in Monthly_list:
            novelId_list.append(monthly.novelId)
        novels = Novels.query.filter(Novels.id.in_(novelId_list), Novels.label == 10).limit(5).all()
    elif type == 'must':
        Monthly_list = MonthlyNovel.query.filter_by(monthlyId=12).all()
        novelId_list = []
        for monthly in Monthly_list:
            novelId_list.append(monthly.novelId)
        novels = Novels.query.filter(Novels.id.in_(novelId_list), Novels.label == 9).all()
        # 随机获取4本
        novels = random.sample(novels, 4)
    elif type == 'god':
        Monthly_list = MonthlyNovel.query.filter_by(monthlyId=5).all()[:4]
        novelId_list = []
        for monthly in Monthly_list:
            novelId_list.append(monthly.novelId)
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    elif type == 'recommend':
        boy_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=1).all()
        girl_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=8).all()
        novelId_list = []
        for monthly in boy_Monthly_list:
            novelId_list.append(monthly.novelId)
        for monthly in girl_Monthly_list:
            novelId_list.append(monthly.novelId)
        # 打乱顺序random.shuffle(novelId_list)
        novelId_list = random.sample(novelId_list, 8)

        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    elif type == 'over':
        boy_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=7).limit(3).all()
        girl_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=14).limit(2).all()
        novelId_list = []
        for monthly in boy_Monthly_list:
            novelId_list.append(monthly.novelId)
        for monthly in girl_Monthly_list:
            novelId_list.append(monthly.novelId)
        # 打乱顺序random.shuffle(novelId_list)

        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    elif type == 'new':
        boy_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=3).limit(3).all()
        girl_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=10).limit(2).all()
        novelId_list = []
        for monthly in boy_Monthly_list:
            novelId_list.append(monthly.novelId)
        for monthly in girl_Monthly_list:
            novelId_list.append(monthly.novelId)
        # 打乱顺序random.shuffle(novelId_list)

        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    elif type == 'weeksearch':
        boy_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=5).all()
        girl_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=12).all()
        novelId_list = []
        for monthly in boy_Monthly_list:
            novelId_list.append(monthly.novelId)
        for monthly in girl_Monthly_list:
            novelId_list.append(monthly.novelId)
        # 打乱顺序
        novelId_list = random.sample(novelId_list, 8)
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    elif type == 'weekupdate':
        boy_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=6).limit(2).all()
        girl_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=13).limit(2).all()
        novelId_list = []
        for monthly in boy_Monthly_list:
            novelId_list.append(monthly.novelId)
        for monthly in girl_Monthly_list:
            novelId_list.append(monthly.novelId)
        # 打乱顺序
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    elif type == 'like':
        boy_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=7).limit(10).all()
        girl_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=14).limit(10).all()
        novelId_list = []
        for monthly in boy_Monthly_list:
            novelId_list.append(monthly.novelId)
        for monthly in girl_Monthly_list:
            novelId_list.append(monthly.novelId)
        # 打乱顺序
        novelId_list = random.sample(novelId_list, 5)
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    else:
        return json.dumps({"retCode": 200, "msg": "success", "result": []}, ensure_ascii=False)

    novel_list = novelOb_novelList(novels)

    return json.dumps({"retCode": 200, "msg": "success", "result": novel_list}, ensure_ascii=False)

# 一次返回全部的精选页数据
@bp.route('/handpickall')
def handpickall():
    novel_dict = {}
    #  获取今日推荐的 'today':
    Monthly_list = MonthlyNovel.query.filter_by(monthlyId=12).all()
    novelId_list = []
    for monthly in Monthly_list:
        novelId_list.append(monthly.novelId)
    novels = Novels.query.filter(Novels.id.in_(novelId_list), Novels.label == 10).limit(5).all()
    novel_list = novelOb_novelList(novels)
    novel_dict['today'] = novel_list

    # 获取今日必读的 elif type == 'must':
    Monthly_list = MonthlyNovel.query.filter_by(monthlyId=12).all()
    novelId_list = []
    for monthly in Monthly_list:
        novelId_list.append(monthly.novelId)
    novels = Novels.query.filter(Novels.id.in_(novelId_list), Novels.label == 9).all()
    # 随机获取4本
    novels = random.sample(novels, 4)
    novel_list = novelOb_novelList(novels)
    novel_dict['must'] = novel_list

    # 获取大神再看的 elif type == 'god':
    Monthly_list = MonthlyNovel.query.filter_by(monthlyId=5).all()[:4]
    novelId_list = []
    for monthly in Monthly_list:
        novelId_list.append(monthly.novelId)
    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    novel_list = novelOb_novelList(novels)
    novel_dict['god'] = novel_list

    #  获取小编推荐的 elif type == 'recommend':
    boy_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=1).limit(4).all()
    girl_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=8).limit(4).all()
    novelId_list = []
    for monthly in boy_Monthly_list:
        novelId_list.append(monthly.novelId)
    for monthly in girl_Monthly_list:
        novelId_list.append(monthly.novelId)
    # 打乱顺序random.shuffle(novelId_list)

    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    novel_list = novelOb_novelList(novels)
    novel_dict['recommend'] = novel_list

    # 获取完本畅读的 elif type == 'over':
    boy_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=7).limit(3).all()
    girl_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=14).limit(2).all()
    novelId_list = []
    for monthly in boy_Monthly_list:
        novelId_list.append(monthly.novelId)
    for monthly in girl_Monthly_list:
        novelId_list.append(monthly.novelId)
    # 打乱顺序random.shuffle(novelId_list)

    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    novel_list = novelOb_novelList(novels)
    novel_dict['over'] = novel_list

    # 获取新书推荐的 elifif type == 'new':
    boy_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=3).limit(3).all()
    girl_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=10).limit(2).all()
    novelId_list = []
    for monthly in boy_Monthly_list:
        novelId_list.append(monthly.novelId)
    for monthly in girl_Monthly_list:
        novelId_list.append(monthly.novelId)
    # 打乱顺序random.shuffle(novelId_list)

    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    novel_list = novelOb_novelList(novels)
    novel_dict['new'] = novel_list

    # 获取一周热搜的 elif type == 'weeksearch':
    boy_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=5).all()
    girl_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=12).all()
    novelId_list = []
    for monthly in boy_Monthly_list:
        novelId_list.append(monthly.novelId)
    for monthly in girl_Monthly_list:
        novelId_list.append(monthly.novelId)
    # 打乱顺序
    novelId_list = random.sample(novelId_list, 8)
    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    novel_list = novelOb_novelList(novels)
    novel_dict['weeksearch'] = novel_list

    # 获取一周更新的 elif type == 'weekupdate':
    boy_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=6).limit(2).all()
    girl_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=13).limit(2).all()
    novelId_list = []
    for monthly in boy_Monthly_list:
        novelId_list.append(monthly.novelId)
    for monthly in girl_Monthly_list:
        novelId_list.append(monthly.novelId)
    # 打乱顺序random.shuffle(novelId_list)

    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    novel_list = novelOb_novelList(novels)
    novel_dict['weekupdate'] = novel_list

    # 获取猜你喜欢的 elif type == 'like':
    boy_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=7).limit(10).all()
    girl_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=14).limit(10).all()
    novelId_list = []
    for monthly in boy_Monthly_list:
        novelId_list.append(monthly.novelId)
    for monthly in girl_Monthly_list:
        novelId_list.append(monthly.novelId)
    # 打乱顺序
    novelId_list = random.sample(novelId_list, 5)
    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    novel_list = novelOb_novelList(novels)
    novel_dict['like'] = novel_list


    return json.dumps({"retCode": 200, "msg": "success", "result": novel_dict}, ensure_ascii=False)

# 一次返回全部精选页数据+样式
@bp.route('/handpickalls')
def handpickalls():
    # 从数据库获取精选样式
    compose_pages = ComposePage.query.filter_by(classify='handpick').all()
    result = []
    for compose_page in compose_pages:
        # 获取小说总数
        book_count = compose_page.boycount + compose_page.girlcount
        # 判断是单榜单 还是 男女都用榜单
        if compose_page.girlmonthly and compose_page.boymonthly:
            boy_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=compose_page.girlmonthly).all()
            girl_Monthly_list = MonthlyNovel.query.filter_by(monthlyId=compose_page.boymonthly).all()

            novelId_list_boy = []
            novelId_list_girl = []
            for monthly in boy_Monthly_list:
                novelId_list_boy.append(monthly.novelId)
            for monthly in girl_Monthly_list:
                novelId_list_girl.append(monthly.novelId)
            # 判断是否有分类条件
            if compose_page.boylabel and compose_page.girllabel:
                # 判断是否要换一换
                if compose_page.mode == 1 or compose_page.mode == 2:
                    novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_boy),
                                                     Novels.label == compose_page.boylabel).all()
                    novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl),
                                                      Novels.label == compose_page.girllabel).all()
                    novels = novels_boy + novels_girl
                    novels = random.sample(novels, book_count)
                else:
                    novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_boy),
                                                     Novels.label == compose_page.boylabel).limit(compose_page.boycount).all()
                    novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl),
                                                      Novels.label == compose_page.girllabel).limit(compose_page.girlcount).all()
                    novels = novels_boy + novels_girl

            elif compose_page.boylabel:
                # 判断是否要换一换
                if compose_page.mode == 1 or compose_page.mode == 2:
                    novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_boy), Novels.label == compose_page.boylabel).all()
                    novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl)).all()
                    novels = novels_boy + novels_girl
                    novels = random.sample(novels, book_count)
                else:
                    novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_boy),
                         Novels.label == compose_page.boylabel).limit(compose_page.boycount).all()
                    novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl)).limit(compose_page.girlcount).all()
                    novels = novels_boy + novels_girl
            elif compose_page.girllabel:
                # 判断是否要换一换
                if compose_page.mode == 1 or compose_page.mode == 2:
                    novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_boy)).all()
                    novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl),
                                                      Novels.label == compose_page.girllabel).all()
                    novels = novels_boy + novels_girl
                    novels = random.sample(novels, book_count)
                else:
                    novels_boy = Novels.query.filter(
                        (Novels.id.in_(novelId_list_boy)).limit(compose_page.boycount)).all()
                    novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl),
                         Novels.label == compose_page.girllabel).limit(compose_page.girlcount).all()
                    novels = novels_boy + novels_girl
            else:
                # 判断是否要换一换
                if compose_page.mode == 1 or compose_page.mode == 2:
                    novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_boy)).all()
                    novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl)).all()
                    novels = novels_boy + novels_girl
                    novels = random.sample(novels, book_count)
                else:
                    novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_boy)).limit(compose_page.boycount).all()
                    novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl)).limit(compose_page.girlcount).all()
                    novels = novels_boy + novels_girl

        elif compose_page.girlmonthly:
            Monthly_list = MonthlyNovel.query.filter_by(monthlyId=compose_page.girlmonthly).all()
            novelId_list = []
            for monthly in Monthly_list:
                novelId_list.append(monthly.novelId)
            # 判断是否有分类条件
            if compose_page.girllabel:
                # 判断是否要换一换
                if compose_page.mode == 1 or compose_page.mode == 2:
                    novels = Novels.query.filter(Novels.id.in_(novelId_list),
                                                     Novels.label == compose_page.girllabel).all()
                    novels = random.sample(novels, compose_page.girlcount)
                else:
                    novels = Novels.query.filter(Novels.id.in_(novelId_list),
                                                 Novels.label == compose_page.girllabel).limit(compose_page.girlcount).all()
            else:
                # 判断是否要换一换
                if compose_page.mode == 1 or compose_page.mode == 2:
                    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
                    novels = random.sample(novels, compose_page.girlcount)
                else:
                    novels = Novels.query.filter(Novels.id.in_(novelId_list)).limit(compose_page.girlcount).all()

        elif compose_page.boymonthly:
            Monthly_list = MonthlyNovel.query.filter_by(monthlyId=compose_page.boymonthly).all()
            novelId_list = []
            for monthly in Monthly_list:
                novelId_list.append(monthly.novelId)
            # 判断是否有分类条件
            if compose_page.boylabel:
                # 判断是否要换一换
                if compose_page.mode == 1 or compose_page.mode == 2:
                    novels = Novels.query.filter(Novels.id.in_(novelId_list),
                                                 Novels.label == compose_page.boylabel).all()
                    novels = random.sample(novels, compose_page.boycount)
                else:
                    novels = Novels.query.filter(Novels.id.in_(novelId_list),
                                                 Novels.label == compose_page.boylabel).limit(
                        compose_page.boycount).all()
            else:
                # 判断是否要换一换
                if compose_page.mode == 1 or compose_page.mode == 2:
                    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
                    novels = random.sample(novels, compose_page.boycount)
                else:
                    novels = Novels.query.filter(Novels.id.in_(novelId_list)).limit(compose_page.boycount).all()

        else:
            return json.dumps({"retCode": 200, "msg": "success", "result": []}, ensure_ascii=False)

        novels_list = novelOb_novelList(novels)


        result_dict = {'style': compose_page.style,
                       'type': compose_page.type,
                       'title': compose_page.title,
                       'data': novels_list,
                       'other': {'mode': compose_page.mode, 'head': compose_page.head}
                       }
        result.append(result_dict)
    return json.dumps({"retCode": 200, "msg": "success", "result": result}, ensure_ascii=False)

# 女生页面接口
@bp.route('/girl')
def girl():
    type = request.args.get('type')
    # recommend(推荐女生热搜榜单数据 8本 换一换) new(女生新书榜单5本) must(都市 浪漫青春 各两本)
    # 仙剑奇缘 科幻 灵异 二次元 分类数据
    # 古言 现言 玄幻言情 浪漫青春 分类数据
    # over(女生完本)
    # 轻小说
    if type == 'recommend':
        Monthly_list = MonthlyNovel.query.filter_by(monthlyId=8).all()
        novelId_list = []
        for monthly in Monthly_list:
            novelId_list.append(monthly.novelId)
        # 打乱顺序
        novelId_list = random.sample(novelId_list, 8)
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    elif type == 'new':
        Monthly_list = MonthlyNovel.query.filter_by(monthlyId=10).limit(5).all()
        novelId_list = []
        for monthly in Monthly_list:
            novelId_list.append(monthly.novelId)
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    elif type == 'must':
        Monthly_list1 = MonthlyNovel.query.filter_by(monthlyId=12).limit(2).all()
        Monthly_list2 = MonthlyNovel.query.filter_by(monthlyId=13).limit(2).all()
        novelId_list = []
        for monthly in Monthly_list1:
            novelId_list.append(monthly.novelId)
        for monthly in Monthly_list2:
            novelId_list.append(monthly.novelId)
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    elif type == 'over':
        Monthly_list = MonthlyNovel.query.filter_by(monthlyId=14).limit(8).all()
        novelId_list = []
        for monthly in Monthly_list:
            novelId_list.append(monthly.novelId)
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    else:
        return json.dumps({"retCode": 200, "msg": "success", "result": []}, ensure_ascii=False)

    novel_list = novelOb_novelList(novels)

    return json.dumps({"retCode": 200, "msg": "success", "result": novel_list}, ensure_ascii=False)

# 一次返回女生页面全部数据
# 女生页面接口
@bp.route('/girlall')
def girlall():
    novel_dict = {}
    # 小编推荐if type == 'recommend':
    Monthly_list = MonthlyNovel.query.filter_by(monthlyId=8).all()
    novelId_list = []
    for monthly in Monthly_list:
        novelId_list.append(monthly.novelId)
    # 打乱顺序
    novelId_list = random.sample(novelId_list, 8)
    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    novel_list = novelOb_novelList(novels)
    novel_dict['recommend'] = novel_list

    # 畅销新书 elif type == 'new':
    Monthly_list = MonthlyNovel.query.filter_by(monthlyId=10).limit(5).all()
    novelId_list = []
    for monthly in Monthly_list:
        novelId_list.append(monthly.novelId)
    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    novel_list = novelOb_novelList(novels)
    novel_dict['new'] = novel_list

    # 今日必看 elif type == 'must':
    Monthly_list1 = MonthlyNovel.query.filter_by(monthlyId=12).limit(2).all()
    Monthly_list2 = MonthlyNovel.query.filter_by(monthlyId=13).limit(2).all()
    novelId_list = []
    for monthly in Monthly_list1:
        novelId_list.append(monthly.novelId)
    for monthly in Monthly_list2:
        novelId_list.append(monthly.novelId)
    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    novel_list = novelOb_novelList(novels)
    novel_dict['must'] = novel_list

    # 完本精选 elif type == 'over':
    Monthly_list = MonthlyNovel.query.filter_by(monthlyId=14).limit(8).all()
    novelId_list = []
    for monthly in Monthly_list:
        novelId_list.append(monthly.novelId)
    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    novel_list = novelOb_novelList(novels)
    novel_dict['over'] = novel_list

    return json.dumps({"retCode": 200, "msg": "success", "result": novel_dict}, ensure_ascii=False)

# 一次返回全部女生页数据+样式
@bp.route('/girlalls')
def girlalls():
    # 从数据库获取精选样式
    compose_pages = ComposePage.query.filter_by(classify='girl').all()
    result = []
    for compose_page in compose_pages:
        # 判断是否是特殊的模块仙剑奇缘23 科幻16 灵异7 二次元15 古言10 现言9 玄幻言情12 浪漫青春11 轻小说18
        if compose_page.style == 5:
            result_dict = {
                'style': 5,
                'classify': [
                    {"title": "仙剑奇缘", "classifyId": "23"},
                    {"title": "科幻", "classifyId": "16"},
                    {"title": "灵异", "classifyId": "7"},
                    {"title": "二次元", "classifyId": "15"}
                ]
            }
        elif compose_page.style == 6:
            result_dict = {
                'style': 6,
                'classify': [
                    {"title": "古言", "classifyId": "10"},
                    {"title": "现言", "classifyId": "9"},
                    {"title": "玄幻言情", "classifyId": "12"},
                    {"title": "浪漫青春", "classifyId": "11"},
                ]
            }
        elif compose_page.style == 7:
            # 获取轻小说的数据
            novels = Novels.query.filter_by(label=compose_page.girllabel).limit(4).all()
            novels_list = novelOb_novelList(novels)
            result_dict = {'style': compose_page.style,
                           'type': compose_page.type,
                           'title': compose_page.title,
                           'data': novels_list,
                           'other': {'mode': compose_page.mode, 'head': compose_page.head}
                           }
        else:
            # 获取小说总数
            book_count = compose_page.boycount + compose_page.girlcount
            # 判断男女榜单
            if compose_page.girlmonthly and compose_page.boymonthly:
                Monthly_list_girl1 = MonthlyNovel.query.filter_by(monthlyId=compose_page.girlmonthly).all()
                Monthly_list_girl2 = MonthlyNovel.query.filter_by(monthlyId=compose_page.boymonthly).all()

                novelId_list_girl1 = []
                novelId_list_girl2 = []
                for monthly in Monthly_list_girl1:
                    novelId_list_girl1.append(monthly.novelId)
                for monthly in Monthly_list_girl2:
                    novelId_list_girl2.append(monthly.novelId)
                # 判断是否有分类条件
                if compose_page.boylabel and compose_page.girllabel:
                    # 判断是否要换一换
                    if compose_page.mode == 1 or compose_page.mode == 2:
                        novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_girl1),
                                                         Novels.label == compose_page.boylabel).all()
                        novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl2),
                                                          Novels.label == compose_page.girllabel).all()
                        novels = novels_boy + novels_girl
                        novels = random.sample(novels, book_count)
                    else:
                        novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_girl1),
                                                         Novels.label == compose_page.boylabel).limit(
                            compose_page.boycount).all()
                        novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl2),
                                                          Novels.label == compose_page.girllabel).limit(
                            compose_page.girlcount).all()
                        novels = novels_boy + novels_girl

                elif compose_page.boylabel:
                    # 判断是否要换一换
                    if compose_page.mode == 1 or compose_page.mode == 2:
                        novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_girl1),
                                                         Novels.label == compose_page.boylabel).all()
                        novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl2)).all()
                        novels = novels_boy + novels_girl
                        novels = random.sample(novels, book_count)
                    else:
                        novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_girl1),
                                                         Novels.label == compose_page.boylabel).limit(
                            compose_page.boycount).all()
                        novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl2)).limit(
                            compose_page.girlcount).all()
                        novels = novels_boy + novels_girl
                elif compose_page.girllabel:
                    # 判断是否要换一换
                    if compose_page.mode == 1 or compose_page.mode == 2:
                        novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_girl1)).all()
                        novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl2),
                                                          Novels.label == compose_page.girllabel).all()
                        novels = novels_boy + novels_girl
                        novels = random.sample(novels, book_count)
                    else:
                        novels_boy = Novels.query.filter(
                            (Novels.id.in_(novelId_list_girl1)).limit(compose_page.boycount)).all()
                        novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl2),
                                                          Novels.label == compose_page.girllabel).limit(
                            compose_page.girlcount).all()
                        novels = novels_boy + novels_girl
                else:
                    # 判断是否要换一换
                    if compose_page.mode == 1 or compose_page.mode == 2:
                        novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_girl1)).all()
                        novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl2)).all()
                        novels = novels_boy + novels_girl
                        novels = random.sample(novels, book_count)
                    else:
                        novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_girl1)).limit(
                            compose_page.boycount).all()
                        novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl2)).limit(
                            compose_page.girlcount).all()
                        novels = novels_boy + novels_girl

            elif compose_page.girlmonthly:
                Monthly_list = MonthlyNovel.query.filter_by(monthlyId=compose_page.girlmonthly).all()
                novelId_list = []
                for monthly in Monthly_list:
                    novelId_list.append(monthly.novelId)
                # 判断是否有分类条件
                if compose_page.girllabel:
                    # 判断是否要换一换
                    if compose_page.mode == 1 or compose_page.mode == 2:
                        novels = Novels.query.filter(Novels.id.in_(novelId_list),
                                                     Novels.label == compose_page.girllabel).all()
                        novels = random.sample(novels, compose_page.girlcount)
                    else:
                        novels = Novels.query.filter(Novels.id.in_(novelId_list),
                                                     Novels.label == compose_page.girllabel).limit(
                            compose_page.girlcount).all()
                else:
                    # 判断是否要换一换
                    if compose_page.mode == 1 or compose_page.mode == 2:
                        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
                        novels = random.sample(novels, compose_page.girlcount)
                    else:
                        novels = Novels.query.filter(Novels.id.in_(novelId_list)).limit(compose_page.girlcount).all()

            elif compose_page.boymonthly:
                Monthly_list = MonthlyNovel.query.filter_by(monthlyId=compose_page.boymonthly).all()
                novelId_list = []
                for monthly in Monthly_list:
                    novelId_list.append(monthly.novelId)
                # 判断是否有分类条件
                if compose_page.boylabel:
                    # 判断是否要换一换
                    if compose_page.mode == 1 or compose_page.mode == 2:
                        novels = Novels.query.filter(Novels.id.in_(novelId_list),
                                                     Novels.label == compose_page.boylabel).all()
                        novels = random.sample(novels, compose_page.boycount)
                    else:
                        novels = Novels.query.filter(Novels.id.in_(novelId_list),
                                                     Novels.label == compose_page.boylabel).limit(
                            compose_page.boycount).all()
                else:
                    # 判断是否要换一换
                    if compose_page.mode == 1 or compose_page.mode == 2:
                        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
                        novels = random.sample(novels, compose_page.boycount)
                    else:
                        novels = Novels.query.filter(Novels.id.in_(novelId_list)).limit(compose_page.boycount).all()

            else:
                return json.dumps({"retCode": 200, "msg": "success", "result": []}, ensure_ascii=False)
            novels_list = novelOb_novelList(novels)
            result_dict = {'style': compose_page.style,
                           'type': compose_page.type,
                           'title': compose_page.title,
                           'data': novels_list,
                           'other': {'mode': compose_page.mode, 'head': compose_page.head}
                           }
        result.append(result_dict)
    return json.dumps({"retCode": 200, "msg": "success", "result": result}, ensure_ascii=False)

# 男生页面接口
@bp.route('/boy')
def boy():
    type = request.args.get('type')
    # recommend(推荐男生热搜榜单数据 8本 换一换) new(男生新书榜单5本) must(人气 完结 各两本)
    # 玄幻 奇幻 仙侠 武侠 分类数据
    # 都市 科幻 二次元 体育 分类数据
    # 游戏竞技
    # over(男生完本)
    # 轻小说
    if type == 'recommend':
        Monthly_list = MonthlyNovel.query.filter_by(monthlyId=5).all()
        novelId_list = []
        for monthly in Monthly_list:
            novelId_list.append(monthly.novelId)
        # 打乱顺序
        novelId_list = random.sample(novelId_list, 8)
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    elif type == 'new':
        Monthly_list = MonthlyNovel.query.filter_by(monthlyId=3).limit(5).all()
        novelId_list = []
        for monthly in Monthly_list:
            novelId_list.append(monthly.novelId)
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    elif type == 'must':
        Monthly_list1 = MonthlyNovel.query.filter_by(monthlyId=1).limit(2).all()
        Monthly_list2 = MonthlyNovel.query.filter_by(monthlyId=2).limit(2).all()
        novelId_list = []
        for monthly in Monthly_list1:
            novelId_list.append(monthly.novelId)
        for monthly in Monthly_list2:
            novelId_list.append(monthly.novelId)
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    elif type == 'over':
        Monthly_list = MonthlyNovel.query.filter_by(monthlyId=7).limit(8).all()
        novelId_list = []
        for monthly in Monthly_list:
            novelId_list.append(monthly.novelId)
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    else:
        return json.dumps({"retCode": 200, "msg": "success", "result": []}, ensure_ascii=False)

    novel_list = novelOb_novelList(novels)

    return json.dumps({"retCode": 200, "msg": "success", "result": novel_list}, ensure_ascii=False)

# 男生页面全部数据
# 男生页面接口
@bp.route('/boyall')
def boyall():
    novel_dict = {}
    # 小编推荐 if type == 'recommend':
    Monthly_list = MonthlyNovel.query.filter_by(monthlyId=5).all()
    novelId_list = []
    for monthly in Monthly_list:
        novelId_list.append(monthly.novelId)
    # 打乱顺序
    novelId_list = random.sample(novelId_list, 8)
    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    novel_list = novelOb_novelList(novels)
    novel_dict['recommend'] = novel_list

    # 畅销新书 elif type == 'new':
    Monthly_list = MonthlyNovel.query.filter_by(monthlyId=3).limit(5).all()
    novelId_list = []
    for monthly in Monthly_list:
        novelId_list.append(monthly.novelId)
    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    novel_list = novelOb_novelList(novels)
    novel_dict['new'] = novel_list

    # 今日必读 elif type == 'must':
    Monthly_list1 = MonthlyNovel.query.filter_by(monthlyId=1).limit(2).all()
    Monthly_list2 = MonthlyNovel.query.filter_by(monthlyId=2).limit(2).all()
    novelId_list = []
    for monthly in Monthly_list1:
        novelId_list.append(monthly.novelId)
    for monthly in Monthly_list2:
        novelId_list.append(monthly.novelId)
    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    novel_list = novelOb_novelList(novels)
    novel_dict['must'] = novel_list

    # 完结elif type == 'over':
    Monthly_list = MonthlyNovel.query.filter_by(monthlyId=7).limit(8).all()
    novelId_list = []
    for monthly in Monthly_list:
        novelId_list.append(monthly.novelId)
    novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    novel_list = novelOb_novelList(novels)
    novel_dict['over'] = novel_list


    return json.dumps({"retCode": 200, "msg": "success", "result": novel_dict}, ensure_ascii=False)

# 一次返回全部男生页数据+样式
@bp.route('/boyalls')
def boyalls():
    # 从数据库获取精选样式
    compose_pages = ComposePage.query.filter_by(classify='boy').all()
    result = []
    for compose_page in compose_pages:
        # 判断是否是特殊的模块仙剑奇缘23 科幻16 灵异7 二次元15 古言10 现言9 玄幻言情12 浪漫青春11 轻小说18
        if compose_page.style == 5:
            result_dict = {
                'style': 5,
                'classify': [
                    {"title": "玄幻", "classifyId": "4"},
                    {"title": "奇幻", "classifyId": "20"},
                    {"title": "仙侠", "classifyId": "5"},
                    {"title": "武侠", "classifyId": "19"}
                ]
            }
        elif compose_page.style == 6:
            result_dict = {
                'style': 6,
                'classify': [
                    {"title": "都市", "classifyId": "3"},
                    {"title": "科幻", "classifyId": "8"},
                    {"title": "二次元", "classifyId": "14"},
                    {"title": "体育", "classifyId": "22"},
                ]
            }
        elif compose_page.style == 7:
            # 获取轻小说的数据
            novels = Novels.query.filter_by(label=compose_page.girllabel).limit(4).all()
            novels_list = novelOb_novelList(novels)
            result_dict = {'style': compose_page.style,
                           'type': compose_page.type,
                           'title': compose_page.title,
                           'data': novels_list,
                           'other': {'mode': compose_page.mode, 'head': compose_page.head}
                           }
        else:
            # 获取小说总数
            book_count = compose_page.boycount + compose_page.girlcount
            # 判断男女榜单
            if compose_page.girlmonthly and compose_page.boymonthly:
                Monthly_list_girl1 = MonthlyNovel.query.filter_by(monthlyId=compose_page.girlmonthly).all()
                Monthly_list_girl2 = MonthlyNovel.query.filter_by(monthlyId=compose_page.boymonthly).all()

                novelId_list_girl1 = []
                novelId_list_girl2 = []
                for monthly in Monthly_list_girl1:
                    novelId_list_girl1.append(monthly.novelId)
                for monthly in Monthly_list_girl2:
                    novelId_list_girl2.append(monthly.novelId)
                # 判断是否有分类条件
                if compose_page.boylabel and compose_page.girllabel:
                    # 判断是否要换一换
                    if compose_page.mode == 1 or compose_page.mode == 2:
                        novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_girl1),
                                                         Novels.label == compose_page.boylabel).all()
                        novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl2),
                                                          Novels.label == compose_page.girllabel).all()
                        novels = novels_boy + novels_girl
                        novels = random.sample(novels, book_count)
                    else:
                        novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_girl1),
                                                         Novels.label == compose_page.boylabel).limit(
                            compose_page.boycount).all()
                        novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl2),
                                                          Novels.label == compose_page.girllabel).limit(
                            compose_page.girlcount).all()
                        novels = novels_boy + novels_girl

                elif compose_page.boylabel:
                    # 判断是否要换一换
                    if compose_page.mode == 1 or compose_page.mode == 2:
                        novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_girl1),
                                                         Novels.label == compose_page.boylabel).all()
                        novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl2)).all()
                        novels = novels_boy + novels_girl
                        novels = random.sample(novels, book_count)
                    else:
                        novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_girl1),
                                                         Novels.label == compose_page.boylabel).limit(
                            compose_page.boycount).all()
                        novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl2)).limit(
                            compose_page.girlcount).all()
                        novels = novels_boy + novels_girl
                elif compose_page.girllabel:
                    # 判断是否要换一换
                    if compose_page.mode == 1 or compose_page.mode == 2:
                        novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_girl1)).all()
                        novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl2),
                                                          Novels.label == compose_page.girllabel).all()
                        novels = novels_boy + novels_girl
                        novels = random.sample(novels, book_count)
                    else:
                        novels_boy = Novels.query.filter(
                            (Novels.id.in_(novelId_list_girl1)).limit(compose_page.boycount)).all()
                        novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl2),
                                                          Novels.label == compose_page.girllabel).limit(
                            compose_page.girlcount).all()
                        novels = novels_boy + novels_girl
                else:
                    # 判断是否要换一换
                    if compose_page.mode == 1 or compose_page.mode == 2:
                        novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_girl1)).all()
                        novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl2)).all()
                        novels = novels_boy + novels_girl
                        novels = random.sample(novels, book_count)
                    else:
                        novels_boy = Novels.query.filter(Novels.id.in_(novelId_list_girl1)).limit(
                            compose_page.boycount).all()
                        novels_girl = Novels.query.filter(Novels.id.in_(novelId_list_girl2)).limit(
                            compose_page.girlcount).all()
                        novels = novels_boy + novels_girl

            elif compose_page.girlmonthly:
                Monthly_list = MonthlyNovel.query.filter_by(monthlyId=compose_page.girlmonthly).all()
                novelId_list = []
                for monthly in Monthly_list:
                    novelId_list.append(monthly.novelId)
                # 判断是否有分类条件
                if compose_page.girllabel:
                    # 判断是否要换一换
                    if compose_page.mode == 1 or compose_page.mode == 2:
                        novels = Novels.query.filter(Novels.id.in_(novelId_list),
                                                     Novels.label == compose_page.girllabel).all()
                        novels = random.sample(novels, compose_page.girlcount)
                    else:
                        novels = Novels.query.filter(Novels.id.in_(novelId_list),
                                                     Novels.label == compose_page.girllabel).limit(
                            compose_page.girlcount).all()
                else:
                    # 判断是否要换一换
                    if compose_page.mode == 1 or compose_page.mode == 2:
                        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
                        novels = random.sample(novels, compose_page.girlcount)
                    else:
                        novels = Novels.query.filter(Novels.id.in_(novelId_list)).limit(compose_page.girlcount).all()

            elif compose_page.boymonthly:
                Monthly_list = MonthlyNovel.query.filter_by(monthlyId=compose_page.boymonthly).all()
                novelId_list = []
                for monthly in Monthly_list:
                    novelId_list.append(monthly.novelId)
                # 判断是否有分类条件
                if compose_page.boylabel:
                    # 判断是否要换一换
                    if compose_page.mode == 1 or compose_page.mode == 2:
                        novels = Novels.query.filter(Novels.id.in_(novelId_list),
                                                     Novels.label == compose_page.boylabel).all()
                        novels = random.sample(novels, compose_page.boycount)
                    else:
                        novels = Novels.query.filter(Novels.id.in_(novelId_list),
                                                     Novels.label == compose_page.boylabel).limit(
                            compose_page.boycount).all()
                else:
                    # 判断是否要换一换
                    if compose_page.mode == 1 or compose_page.mode == 2:
                        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
                        novels = random.sample(novels, compose_page.boycount)
                    else:
                        novels = Novels.query.filter(Novels.id.in_(novelId_list)).limit(compose_page.boycount).all()

            else:
                return json.dumps({"retCode": 200, "msg": "success", "result": []}, ensure_ascii=False)
            novels_list = novelOb_novelList(novels)
            result_dict = {'style': compose_page.style,
                           'type': compose_page.type,
                           'title': compose_page.title,
                           'data': novels_list,
                           'other': {'mode': compose_page.mode, 'head': compose_page.head}
                           }
        result.append(result_dict)
    return json.dumps({"retCode": 200, "msg": "success", "result": result}, ensure_ascii=False)




# 分类页面 -----------------------------begin---------------------------
# 分类页面 小编推荐接口
@bp.route('/typerecommend')
def typerecommend():
    type = request.args.get('type')
    # 玄幻4 奇幻20 仙侠5 武侠19 都市3 科幻8 二次元14 体育22 游戏竞技21 wbjxb 轻小说18
    # 仙侠奇缘23 科幻16 灵异7 二次元15 古言10 现言9 玄幻言情12 浪漫青春11 wbjxg 轻小说18
    # type_o = request.args.get('type_o')  # recommend  new  free
    # 获取榜单中的精选分类
    # 男生分类
    boy_type_list = ['4', '20', '5', '19', '3', '8', '14', '22', '21', '18']
    girl_type_list = ['23', '16', '7', '10', '9', '12', '11']
    if type in boy_type_list:
        monthlyId=2
    elif type in girl_type_list:
        monthlyId=9
    elif type == 'wbjxb':
        monthlyId=7
    elif type == 'wbjxg':
        monthlyId=14
    else:
        return json.dumps({"retCode": 400, "msg": "args error", "result": []}, ensure_ascii=False)
    Monthly_list = MonthlyNovel.query.filter_by(monthlyId=monthlyId).all()
    # 小编推荐 获取榜单数据

    novelId_list = []
    for monthly in Monthly_list:
        novelId_list.append(monthly.novelId)
    if type == 'wbjxb' or type == 'wbjxg':
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    else:
        novels = Novels.query.filter(Novels.id.in_(novelId_list), Novels.label == type).all()
    novels = random.sample(novels, 4)

    novel_list = novelOb_novelList(novels)

    return json.dumps({"retCode": 200, "msg": "success", "result": novel_list}, ensure_ascii=False)
# 分类页面 精选最新接口
@bp.route('/typenew')
def typenew():
    type = request.args.get('type')
    page = request.args.get('page')
    if not page or not page.isdigit():
        page = 1
    limit = request.args.get('limit')
    if not limit or not limit.isdigit():
        limit = 10
    offset = (int(page) - 1) * int(limit)
    if type == 'wbjxb':
        Monthly_list = MonthlyNovel.query.filter_by(monthlyId=7).limit(limit).offset(offset).all()
        novelId_list = []
        for monthly in Monthly_list:
            novelId_list.append(monthly.novelId)
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    elif type == 'wbjxg':
        Monthly_list = MonthlyNovel.query.filter_by(monthlyId=14).limit(limit).offset(offset).all()
        novelId_list = []
        for monthly in Monthly_list:
            novelId_list.append(monthly.novelId)
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    # 男生分类
    else:
        novels = Novels.query.filter_by(label=type).order_by(-Novels.id).limit(limit).offset(offset).all()
    novel_list = novelOb_novelList(novels)

    return json.dumps({"retCode": 200, "msg": "success", "result": novel_list}, ensure_ascii=False)

# 分类页面 免费畅读
@bp.route('/typefree')
def typefree():
    type = request.args.get('type')
    page = request.args.get('page')
    if not page or not page.isdigit():
        page = 1
    limit = request.args.get('limit')
    if not limit or not limit.isdigit():
        limit = 10
    offset = (int(page) - 1) * int(limit)
    if type == 'wbjxb':
        Monthly_list = MonthlyNovel.query.filter_by(monthlyId=7).order_by(-MonthlyNovel.id).limit(limit).offset(offset).all()
        novelId_list = []
        for monthly in Monthly_list:
            novelId_list.append(monthly.novelId)
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    elif type == 'wbjxg':
        Monthly_list = MonthlyNovel.query.filter_by(monthlyId=14).order_by(-MonthlyNovel.id).limit(limit).offset(offset).all()
        novelId_list = []
        for monthly in Monthly_list:
            novelId_list.append(monthly.novelId)
        novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
    # 男生分类
    else:
        novels = Novels.query.filter_by(label=type).limit(limit).offset(offset).all()
    novel_list = novelOb_novelList(novels)

    return json.dumps({"retCode": 200, "msg": "success", "result": novel_list}, ensure_ascii=False)

# 分类页面 更多 根据传过来的 type不同获取
@bp.route('/typepage')
def typepage():
    typepage = request.args.get('typepage')
    if typepage == 'new':
        type = request.args.get('type')
        page = request.args.get('page')
        if not page or not page.isdigit():
            page = 1
        limit = request.args.get('limit')
        if not limit or not limit.isdigit():
            limit = 10
        offset = (int(page) - 1) * int(limit)
        if type == 'wbjxb':
            Monthly_list = MonthlyNovel.query.filter_by(monthlyId=7).limit(limit).offset(offset).all()
            novelId_list = []
            for monthly in Monthly_list:
                novelId_list.append(monthly.novelId)
            novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
        elif type == 'wbjxg':
            Monthly_list = MonthlyNovel.query.filter_by(monthlyId=14).limit(limit).offset(offset).all()
            novelId_list = []
            for monthly in Monthly_list:
                novelId_list.append(monthly.novelId)
            novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
        # 男生分类
        else:
            novels = Novels.query.filter_by(label=type).order_by(-Novels.id).limit(limit).offset(offset).all()
        novel_list = novelOb_novelList(novels)

        return json.dumps({"retCode": 200, "msg": "success", "result": novel_list}, ensure_ascii=False)
    else:
        return json.dumps({"retCode": 200, "msg": "success", "result": []}, ensure_ascii=False)

# 分类页面 -------------------------------end-------------------------------

# ----------------------------书库 -start----------------------------------
# 根据 男生女生获取 小说不同的分类 v2
@bp.route('/classification')
def classification():
    host = 'http://%s' % request.host
    gender = request.args.get('gender')
    if gender == '0':   # 女
        gender = 0
    elif gender == '1':  # 男
        gender = 1
    else:
        return json.dumps({"retCode": 400, "msg": "args error", "result": []}, ensure_ascii=False)
    type_list = []
    types = NovelType.query.filter_by(gender=gender).all()
    for type in types:
        if not type.cover:
            cover_str = ""
        else:
            cover_str = type.cover
        typeId = type.id
        if typeId == 15:
            typeId = 14
        elif typeId == 23:
            typeId = 18
        cover = host + cover_str
        type_list.append(
            {'id': typeId, 'type': type.type, 'cover': cover, 'gender': gender, 'count': type.type_count}
        )
    return json.dumps({"retCode": 200, "msg": "success", "result": type_list}, ensure_ascii=False)

# 根据小说分类id获取分类页面  样式+数据
@bp.route('/types')
def types():
    type = request.args.get('type')
    compose_pages = ComposePage.query.filter_by(classify='type').all()
    result = []
    for compose_page in compose_pages:
        if compose_page.type == 'recommend':
            # 玄幻4 奇幻20 仙侠5 武侠19 都市3 科幻8 二次元14 体育22 游戏竞技21 wbjxb 轻小说18
            # 仙侠奇缘23 科幻16 灵异7 二次元15 古言10 现言9 玄幻言情12 浪漫青春11 wbjxg 轻小说18
            # type_o = request.args.get('type_o')  # recommend  new  free
            # 获取榜单中的精选分类
            # 男生分类
            boy_type_list = ['4', '20', '5', '19', '3', '8', '14', '22', '21', '18']
            girl_type_list = ['23', '16', '7', '10', '9', '12', '11']
            if type in boy_type_list:
                monthlyId = 2
            elif type in girl_type_list:
                monthlyId = 9
            elif type == 'wbjxb':
                monthlyId = 7
            elif type == 'wbjxg':
                monthlyId = 14
            else:
                return json.dumps({"retCode": 400, "msg": "args error", "result": []}, ensure_ascii=False)
            Monthly_list = MonthlyNovel.query.filter_by(monthlyId=monthlyId).all()
            # 小编推荐 获取榜单数据

            novelId_list = []
            for monthly in Monthly_list:
                novelId_list.append(monthly.novelId)
            if type == 'wbjxb' or type == 'wbjxg':
                novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
            else:
                novels = Novels.query.filter(Novels.id.in_(novelId_list), Novels.label == type).all()
            novels = random.sample(novels, 4)

        elif compose_page.type == 'new':
            if type == 'wbjxb':
                Monthly_list = MonthlyNovel.query.filter_by(monthlyId=7).limit(5).all()
                novelId_list = []
                for monthly in Monthly_list:
                    novelId_list.append(monthly.novelId)
                novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
            elif type == 'wbjxg':
                Monthly_list = MonthlyNovel.query.filter_by(monthlyId=14).limit(5).all()
                novelId_list = []
                for monthly in Monthly_list:
                    novelId_list.append(monthly.novelId)
                novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
            # 男生分类
            else:
                novels = Novels.query.filter_by(label=type).order_by(-Novels.id).limit(5).all()

        elif compose_page.type == 'free':
            if type == 'wbjxb':
                Monthly_list = MonthlyNovel.query.filter_by(monthlyId=7).order_by(-MonthlyNovel.id).limit(4).all()
                novelId_list = []
                for monthly in Monthly_list:
                    novelId_list.append(monthly.novelId)
                novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
            elif type == 'wbjxg':
                Monthly_list = MonthlyNovel.query.filter_by(monthlyId=14).order_by(-MonthlyNovel.id).limit(4).all()
                novelId_list = []
                for monthly in Monthly_list:
                    novelId_list.append(monthly.novelId)
                novels = Novels.query.filter(Novels.id.in_(novelId_list)).all()
            # 男生分类
            else:
                novels = Novels.query.filter_by(label=type).limit(4).all()
        else:
            continue
        novels_list = novelOb_novelList(novels)
        result_dict = {'style': compose_page.style,
                       'type': compose_page.type,
                       'title': compose_page.title,
                       'data': novels_list,
                       'other': {'mode': compose_page.mode, 'head': compose_page.head}
                       }
        result.append(result_dict)
    return json.dumps({"retCode": 200, "msg": "success", "result": result}, ensure_ascii=False)

# 根据 男生女生获取 榜单 v2
@bp.route('/monthlyv')
def monthlyv():
    gender = request.args.get('gender')
    if gender == '0':  # 女
        gender = 0
    elif gender == '1':  # 男
        gender = 1
    else:
        return json.dumps({"retCode": 400, "msg": "args error", "result": []}, ensure_ascii=False)
    monthlys = Monthly.query.filter_by(type_one=gender).all()
    monthly_list = []
    for monthly in monthlys:
        monthly_list.append({
            'id': monthly.id,
            'monthly': monthly.monthly
        })
    return json.dumps({"retCode": 200, "msg": "success", "result": monthly_list}, ensure_ascii=False)
# ----------------------------书库 -end----------------------------------
# ----------------------------书架 -start----------------------------------
# 用户第一次进来推荐 9本书
@bp.route('/firsttime')
def firsttime():
    # 获取9本榜单中的小说
    novels = []
    for x in range(9):
        offset_count = random.randint(0, 350)
        Monthly = MonthlyNovel.query.limit(1).offset(offset_count).first()
        novel = Novels.query.get(Monthly.novelId)
        novels.append(novel)
    novels_list = novelOb_novelList(novels)
    return json.dumps({"retCode": 200, "msg": "success", "result": novels_list}, ensure_ascii=False)

# ----------------------------书架 -end  ----------------------------------
# 根据页面不同分类 获取banner
@bp.route('/banners')
def banners():
    typee = request.args.get('type')
    host = 'http://%s' % request.host
    banner_list_tt = NovelBanner.query.filter_by(type=typee).order_by(NovelBanner.rank).all()
    banner_list = []
    for banner in banner_list_tt:
        cover = host + banner.imgurl
        banner_list.append({
            'imgurl': cover,
            'rank': banner.rank,
            'bookId': eval(banner.args)['bookId']
        })
    return json.dumps({"retCode": 200, "msg": "success", "result": banner_list}, ensure_ascii=False)

# 根据性别 页面获取不同的分类
@bp.route('/gendertype')
def gendertype():
    host = 'http://%s' % request.host
    gender = request.args.get('gender')
    if gender == '1':
        gender = 1
        gg = 'boy'
    elif gender == '0':
        gender = 0
        gg = 'girl'
    else:
        return json.dumps({"retCode": 400, "msg": "args error", "result": []}, ensure_ascii=False)
    typ = request.args.get('type')

    novel_type_list = NovelType.query.filter_by(version=2, gender=gender).all()
    type_list = []
    for novel_type in novel_type_list:
        if not novel_type.cover:
            cover_str = ""
        else:
            cover_str = novel_type.cover
            if typ == 'cheng':
                cover_str = '/static/images/%s/cheng%s' % (gg, cover_str.split('/')[-1])
        cover = host + cover_str
        if novel_type.id == 47:
            type_list.append(
                {'id': 'wbjxb', 'type': novel_type.type, 'cover': cover, 'channelId': gender}
            )
        elif novel_type.id == 48:
            type_list.append(
                {'id': 'wbjxg', 'type': novel_type.type, 'cover': cover, 'channelId': gender}
            )
        else:
            if novel_type.id == 36:
                type_id = 14
            elif novel_type.id == 45:
                type_id = 18
            else:
                type_id = novel_type.id-21
            type_list.append(
                {'id': type_id, 'type': novel_type.type, 'cover': cover, 'channelId': gender}
            )
    return json.dumps({"retCode": 200, "msg": "success", "result": type_list}, ensure_ascii=False)








