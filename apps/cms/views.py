import time

from flask import Blueprint, render_template, views, session, request, redirect, url_for, g, jsonify, json

import config
from apps.cms.decorators import login_required
from apps.cms.forms import LoginForm, TypeSpiderForm, BqgSpiderForm
from apps.cms.models import CMSUser
from apps.common.models import NovelType, Novels, NovelTag
from utils.zlcache import my_lpush
from urllib import parse
import requests
from lxml import etree

bp = Blueprint('cms', __name__, url_prefix='/cms')





@bp.route('/')
@login_required
def index():
    return render_template('cms/index.html')


class LoginView(views.MethodView):
    def get(self, message=None):
        return render_template('cms/login.html', message=message)

    def post(self):
        form = LoginForm(request.form)
        if form.validate():
            username = form.username.data
            password = form.password.data
            remember = form.remember.data
            user = CMSUser.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session[config.CMS_USER_ID] = user.id
                if remember:
                    session.permanent = True  # 设置31天过期
                return redirect(url_for('cms.index'))
            else:
                return self.get(message='用户名或密码错误')
        else:
            message = form.errors.popitem()[1][0]
            return self.get(message=message)

# 注销功能
@bp.route('/logout/')
@login_required
def logout():
    del session[config.CMS_USER_ID]
    return redirect(url_for('cms.login'))

@bp.route('/indexv/')
@login_required
def indexv():
    typeId = request.args.get('type')

    page = request.args.get('page')
    if not page or not page.isdigit():
        page = 1
    limit = request.args.get('limit')
    if not limit or not limit.isdigit():
        limit = 10
    if not typeId or not typeId.isdigit() or int(typeId) == 0:
        pagination = Novels.query.order_by(-Novels.addtime).paginate(page=int(page), per_page=10, error_out=False)
        novelcount = pagination.total
        typeId = 0
    else:
        pagination = Novels.query.filter_by(label=typeId).order_by(-Novels.addtime).paginate(page=int(page), per_page=10, error_out=False)
        novelcount = pagination.total
    # 获取小说分类
    novel_type = NovelType.query.all()
    boy_type = []
    girl_type = []
    for novel_t in novel_type:
        if novel_t.gender == 1:
            boy_type.append(novel_t)
        elif novel_t.gender == 0:
            girl_type.append(novel_t)
    # 获取所有的小说
    novels = pagination.items
    # 修改分类 状态 开始时间 更新时间 标签
    novel_list = []
    for novel in novels:
        novel_type = NovelType.query.get(novel.label).type
        if novel.state == 1:
            state = '连载'
        else:
            state = '完本'
        timeArray = time.localtime(novel.created)
        otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        created = otherStyleTime
        timeArray = time.localtime(novel.updated)
        otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        updated = otherStyleTime
        target_list = novel.target.split(',')
        tag_list = []
        for tag in target_list:
            if tag:
                tag_list.append(NovelTag.query.get(tag).target)
        target = tag_list
        novel_list.append({
            'id': novel.id,
            'name': novel.name,
            'cover': novel.cover,
            'summary': novel.summary,
            'label': novel_type,
            'state': state,
            'words': novel.words,
            'created': created,
            'updated': updated,
            'addtime': novel.addtime,
            'target': target,
            'score': novel.score
        })
    return render_template('cms/indexv.html', boys=boy_type, girls=girl_type, novels=novel_list, pagination=pagination, typeId=int(typeId), novelcount=novelcount)


# js获取分类信息


# 免费小说之王采集  拼接分类采集字符串推送到 redis中
@bp.route('/freespider/')
@login_required
def freespider():
    novel_type = NovelType.query.all()
    return render_template('cms/freespider.html', novel_type=novel_type)

# 笔趣阁小说采集
@bp.route('/biquspider/')
@login_required
def biquspider():
    novel_type = NovelType.query.all()
    return render_template('cms/biquspider.html', novel_type=novel_type)

@bp.route('/ftypespider/', methods=['POST'])
@login_required
def ftypespider():
    # 获取post参数
    form = TypeSpiderForm(request.form)
    if form.validate():
        typeId = str(form.typeId.data)
        page = form.page.data
        limit = form.limit.data

        type_list = ['3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
        # 判断typeId是否存在数据库
        if typeId not in type_list:
            return jsonify({'code': 400, 'msg': '分类不存在'})
        categoryId = {'3': '7', '4': '3', '5': '6', '6': '8', '7': '10', '8': '11', '9': '75', '10': '74', '11': '76', '12': '72'}
        # 拼接字符串
        url = 'https://reader.browser.duokan.com/api/v2/book/list2?len=%s&page=%s&sex=2&bookStatus=0&categoryId=%s&wordCountsInterval=0&hotChoice=0' % (limit, page, categoryId[typeId])
        redis_key = 'freespider:start_urls'
        my_lpush(redis_key, url)
        return jsonify({'code': 200, 'msg': '添加采集任务成功，已在后台采集'})
    msg = form.errors.popitem()[1][0]
    return jsonify({'code': 400, 'msg': msg})

# 免费小说之王搜索采集
@bp.route('/fsearchspider/', methods=['POST'])
@login_required
def fsearchspider():
    keyword = request.form.get('keyword')
    goon = request.form.get('goon')
    key = parse.quote(keyword)
    url = 'https://reader.browser.duokan.com/search-api/v2/novel/search?query=%s&start=0&size=10' % key
    # 判断是否有命中 若无命中 是否添加采集任务
    response = requests.get(url)
    results = json.loads(response.text)
    if 'result' not in results:
        return jsonify({'code': 200, 'msg': '未匹配到小说'})
    # 获取小说id添加到redis任务队列
    bookId = results['result']['id']
    # 判断小说id是否存在
    novel = Novels.query.get(bookId)
    if novel:
        return jsonify({'code': 200, 'msg': '小说已存在'})
    book_url = 'https://reader.browser.duokan.com/api/v2/book/%s' % bookId
    redis_key = 'freesearch:start_urls'
    my_lpush(redis_key, book_url)
    return jsonify({'code': 200, 'msg': '添加采集任务成功，已在后台采集'})



# 笔趣阁采集
@bp.route('/bqgspider/', methods=['POST'])
@login_required
def bqgspider():
    form = BqgSpiderForm(request.form)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36'
    }

    if form.validate():
        typeId = str(form.typeId.data)
        page = form.page.data
        # 最新小说 http://www.xbiquge.la/
        if typeId == '1':
            # 采集最新小说
            url = 'http://www.xbiquge.la/'
            response = requests.get(url=url, headers=headers, verify=False)
            response.encoding = 'utf-8'
            html = etree.HTML(response.text)
            new_a_list = html.xpath('//div[@id="newscontent"]/div[@class="r"]/ul/li/span/a/@href')
            for a in new_a_list:
                redis_key = 'xbiquspider:start_urls'
                my_lpush(redis_key, a)
            return jsonify({'code': 200, 'msg': '添加采集任务成功，已在后台采集'})

        type_list = {'4': '1', '5': '2', '3': '3', '7': '4', '8': '6'}
        # http://www.xbiquge.la/fenlei/6_2.html 根据分类 页码请求小说
        # 判断typeId是否存在数据库
        if typeId not in type_list:
            return jsonify({'code': 400, 'msg': '分类不存在'})
        bqg_type = type_list[typeId]
        # 拼接url
        url = 'http://www.xbiquge.la/fenlei/%s_%s.html' % (bqg_type, page)
        response = requests.get(url=url, headers=headers, verify=False)
        response.encoding = 'utf-8'
        html = etree.HTML(response.text)
        new_a_list = html.xpath('//div[@id="newscontent"]/div[@class="l"]/ul/li/span[1]/a/@href')
        for a in new_a_list:
            redis_key = 'xbiquspider:start_urls'
            my_lpush(redis_key, a)
        return jsonify({'code': 200, 'msg': '添加采集任务成功，已在后台采集'})


    msg = form.errors.popitem()[1][0]
    return jsonify({'code': 400, 'msg': msg})

# 免费小说之王更新
class FreeUpdateView(views.MethodView):
    decorators = [login_required]
    def get(self, message=None):
        # 获取免费小说之王下的小说
        typeId = request.args.get('type')
        page = request.args.get('page')
        if not page or not page.isdigit():
            page = 1
        limit = request.args.get('limit')
        if not limit or not limit.isdigit():
            limit = 10
        now_timestamp = int(time.time())
        if not typeId or not typeId.isdigit() or int(typeId) == 0:
            pagination = Novels.query.filter(Novels.novel_web == 1, Novels.updated > now_timestamp-2592000).order_by(Novels.updatetime).paginate(page=int(page), per_page=10, error_out=False)
            novelcount = pagination.total
            typeId = 0
        else:
            pagination = Novels.query.filter(Novels.novel_web == 1, Novels.label == typeId, Novels.updated > now_timestamp-2592000).order_by(Novels.updatetime).paginate(page=int(page), per_page=10, error_out=False)
            novelcount = pagination.total
        # 获取小说分类
        novel_type = NovelType.query.all()
        boy_type = []
        girl_type = []
        for novel_t in novel_type:
            if novel_t.gender == 1:
                boy_type.append(novel_t)
            elif novel_t.gender == 0:
                girl_type.append(novel_t)
        # 获取所有的小说
        novels = pagination.items
        # 修改分类 状态 开始时间 更新时间 标签
        novel_list = []
        for novel in novels:
            novel_type = NovelType.query.get(novel.label).type
            if novel.state == 1:
                state = '连载'
            else:
                state = '完本'
            timeArray = time.localtime(novel.created)
            otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
            created = otherStyleTime
            timeArray = time.localtime(novel.updated)
            otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
            updated = otherStyleTime
            if novel.target == '':
                target_list = []
            else:
                target_list = novel.target.split(',')

            tag_list = []
            for tag in target_list:
                tag_list.append(NovelTag.query.get(tag).target)
            target = tag_list
            novel_list.append({
                'id': novel.id,
                'name': novel.name,
                'cover': novel.cover,
                'summary': novel.summary,
                'label': novel_type,
                'state': state,
                'words': novel.words,
                'created': created,
                'updated': updated,
                'addtime': novel.addtime,
                'target': target,
                'score': novel.score,
                'updatetime': novel.updatetime
            })
        return render_template('cms/freespider_update.html', boys=boy_type, girls=girl_type, novels=novel_list, pagination=pagination, typeId=int(typeId), novelcount=novelcount)

    def post(self):
        novels_id_list = request.values.getlist("novels_id")
        # 获取小说id 添加到redis队列
        for novelId in novels_id_list:
            novel = Novels.query.get(novelId)
            bookId = novel.bookId
            book_url = 'https://reader.browser.duokan.com/api/v2/book/%s' % bookId
            redis_key = 'freesearch:start_urls'
            my_lpush(redis_key, book_url)
        return '已添加到后台更新'


# 笔趣阁更新
class BqgUpdateView(views.MethodView):
    decorators = [login_required]
    def get(self, message=None):
        # 获取笔趣阁下的小说
        typeId = request.args.get('type')

        page = request.args.get('page')
        if not page or not page.isdigit():
            page = 1
        limit = request.args.get('limit')
        if not limit or not limit.isdigit():
            limit = 10
        now_timestamp = int(time.time())
        if not typeId or not typeId.isdigit() or int(typeId) == 0:
            pagination = Novels.query.filter(Novels.novel_web == 2, Novels.updated > now_timestamp - 2592000).order_by(
                Novels.updatetime).paginate(page=int(page), per_page=10, error_out=False)
            novelcount = pagination.total
            typeId = 0
        else:
            pagination = Novels.query.filter(Novels.novel_web == 2, Novels.label == typeId,
                                             Novels.updated > now_timestamp - 2592000).order_by(
                Novels.updatetime).paginate(page=int(page), per_page=10, error_out=False)
            novelcount = pagination.total
        # 获取小说分类
        novel_type = NovelType.query.all()
        boy_type = []
        girl_type = []
        for novel_t in novel_type:
            if novel_t.gender == 1:
                boy_type.append(novel_t)
            elif novel_t.gender == 0:
                girl_type.append(novel_t)
        # 获取所有的小说
        novels = pagination.items
        # 修改分类 状态 开始时间 更新时间 标签
        novel_list = []
        for novel in novels:
            novel_type = NovelType.query.get(novel.label).type
            # 判断小说更新时间与现在差1个月时间说明完结  不更新
            updated_timestamp = novel.updated
            if not updated_timestamp:
                continue
            now_timestamp = int(time.time())
            if now_timestamp - updated_timestamp > 2592000:
                continue
            if novel.state == 1:
                state = '连载'
            else:
                state = '完本'
            timeArray = time.localtime(novel.created)
            otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
            created = otherStyleTime
            timeArray = time.localtime(novel.updated)
            otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
            updated = otherStyleTime
            if novel.target == '':
                target_list = []
            else:
                target_list = novel.target.split(',')

            tag_list = []
            for tag in target_list:
                tag_list.append(NovelTag.query.get(tag).target)
            target = tag_list
            novel_list.append({
                'id': novel.id,
                'name': novel.name,
                'cover': novel.cover,
                'summary': novel.summary,
                'label': novel_type,
                'state': state,
                'words': novel.words,
                'created': created,
                'updated': updated,
                'addtime': novel.addtime,
                'target': target,
                'score': novel.score,
                'updatetime': novel.updatetime
            })
        return render_template('cms/biquupdate.html', boys=boy_type, novels=novel_list, pagination=pagination, typeId=int(typeId), novelcount=novelcount)

    def post(self):
        novels_id_list = request.values.getlist("novels_id")
        # 获取小说笔趣阁id 添加到redis队列
        # http://www.xbiquge.la/36/45532/
        for novelId in novels_id_list:
            novel = Novels.query.get(novelId)
            bookId = novel.bookId
            url = 'http://www.xbiquge.la/36/%s/' % bookId
            redis_key = 'xbiquspider:start_urls'
            my_lpush(redis_key, url)
        return '已添加到后台更新'

bp.add_url_rule('/login/', view_func=LoginView.as_view('login'))
bp.add_url_rule('/bqgupdate/', view_func=BqgUpdateView.as_view('bqgupdate'))
bp.add_url_rule('/freeupdate/', view_func=FreeUpdateView.as_view('freeupdate'))



