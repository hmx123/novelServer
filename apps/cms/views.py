from flask import Blueprint, render_template, views, session, request, redirect, url_for, g, jsonify

import config
from apps.cms.decorators import login_required
from apps.cms.forms import LoginForm, TypeSpiderForm
from apps.cms.models import CMSUser
from apps.common.models import NovelType
from utils.zlcache import my_lpush

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
    # 获取小说分类
    novel_type = NovelType.query.all()
    boy_type = []
    girl_type = []
    for novel_t in novel_type:
        if novel_t.gender == 1:
            boy_type.append(novel_t)
        elif novel_t.gender == 0:
            girl_type.append(novel_t)
    return render_template('cms/indexv.html', boys=boy_type, girls=girl_type)


# js获取分类信息


# 免费小说之王采集  拼接分类采集字符串推送到 redis中
@bp.route('/freespider/')
@login_required
def freespider():
    novel_type = NovelType.query.all()
    return render_template('cms/freespider.html', novel_type=novel_type)

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
        categoryId = {'3': '7', '4': '3', '5': '6', '6': '12', '7': '10', '8': '11', '9': '75', '10': '74', '11': '76', '12': '72'}
        # 拼接字符串
        url = 'https://reader.browser.duokan.com/api/v2/book/list2?len=%s&page=%s&sex=2&bookStatus=0&categoryId=%s&wordCountsInterval=0&hotChoice=0' % (limit, page, categoryId[typeId])
        key = 'freespider:start_urls'
        my_lpush(key, url)
        return jsonify({'code': 200, 'msg': '添加采集任务成功，已在后台采集'})
    msg = form.errors.popitem()[1][0]
    return jsonify({'code': 400, 'msg': msg})




bp.add_url_rule('/login/', view_func=LoginView.as_view('login'))



