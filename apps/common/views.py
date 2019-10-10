import time

from flask import Blueprint, request, jsonify
from itsdangerous import Serializer

import config
from apps.common.forms import RegisterForm, LoginForm, ResetpwdForm, ForgetPassword
from apps.common.models import User, BookCollect, Novels, NovelType, Author, Chapters
from apps.common.wyyapi import sendcode, checkcode
from exts import db

from utils import zlcache

bp = Blueprint('common', __name__, url_prefix='/common')


@bp.route('/')
def index():
    token = rand_string()
    print(token)
    return 'common index'


# 获取验证码
@bp.route('/getcode', methods=['POST'])
def getcode():
    # 获取手机号码
    phone = request.form.get('phone')
    user_ip = request.remote_addr
    uu = '%s-%s' % (user_ip, phone)
    if zlcache.get(uu):
        return jsonify({"retCode": 400, "msg": "Try again in 60 seconds", "result": []})
    zlcache.set(uu, phone, 30)
    if sendcode(phone):
        return jsonify({"retCode": 200, "msg": "success", "result": []})
    else:
        return jsonify({"retCode": 400, "msg": "args error", "result": []})

# 生成用户token
def rand_string(length=32):
    import random
    base_str = 'abcdefghjklmnopqrstuvwyz1234567890'
    return ''.join(random.choice(base_str) for i in range(length))



# 用户注册
@bp.route('/register', methods=['POST'])
def register():
    # 手机号 验证码 密码 性别
    form = RegisterForm(request.form)
    if form.validate():
        phone = form.phone.data
        # 判断用户是否存在
        user = User.query.filter_by(phone=phone).first()
        if user:
            return jsonify({"retCode": 400, "msg": "用户已注册", "result": {"analysis": ""}})
        code = form.code.data
        password = form.password.data
        gender = form.gender.data

        if not checkcode(phone, code):
            return jsonify({"retCode": 400, "msg": "验证码错误", "result": {"analysis": ""}})
        # 生成token
        token = rand_string()
        user = User(username=phone, password=password, phone=phone, token=token, gender=gender)
        db.session.add(user)
        db.session.commit()
        return jsonify({"retCode": 200, "msg": "success", "result": {"analysis": token}})
    message = form.errors.popitem()[1][0]
    return jsonify({"retCode": 400, "msg": message, "result": {"analysis": ""}})

# 用户修改密码
@bp.route('/resetpwd', methods=['POST'])
def resetpwd():
    form = ResetpwdForm(request.form)
    if form.validate():
        analysis = form.analysis.data
        user = User.query.filter_by(token=analysis).first()
        if user:
            oldpwd = form.oldpwd.data
            # 验证旧密码
            result = user.check_password(oldpwd)
            if result:
                # 生成token
                token = rand_string()
                newpwd = form.newpwd2.data
                user.password = newpwd
                user.token = token
                db.session.add(user)
                db.session.commit()
                return jsonify({"retCode": 200, "msg": "修改密码成功", "result": {"analysis": token}})
            return jsonify({"retCode": 400, "msg": "用户名或密码错误", "result": {"analysis": ""}})

        return jsonify({"retCode": 400, "msg": "该用户不存在", "result": {"analysis": ""}})
    message = form.errors.popitem()[1][0]
    return jsonify({"retCode": 400, "msg": message, "result": {"analysis": ""}})

# 用户忘记密码
@bp.route('/forgetpwd', methods=['POST'])
def forgetpwd():
    form = ForgetPassword(request.form)
    if form.validate():
        phone = form.phone.data
        code = form.code.data
        password = form.password.data
        user = User.query.filter_by(phone=phone).first()
        if user:
            if not checkcode(phone, code):
                return jsonify({"retCode": 400, "msg": "验证码错误", "result": {"analysis": ""}})
            # 生成token
            token = rand_string()
            user.password = password
            user.token = token
            db.session.add(user)
            db.session.commit()
            return jsonify({"retCode": 200, "msg": "success", "result": {"analysis": token}})
        return jsonify({"retCode": 400, "msg": "该用户不存在", "result": {"analysis": ""}})


# 用户登录
@bp.route('/login', methods=['POST'])
def login():
    form = LoginForm(request.form)
    if form.validate():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            # 生成token
            token = rand_string()
            user.token = token
            db.session.commit()
            return jsonify({"retCode": 200, "msg": "success", "result": {"analysis": token}})
        return jsonify({"retCode": 400, "msg": "账号或密码错误", "result": {"analysis": ""}})
    message = form.errors.popitem()[1][0]
    return jsonify({"retCode": 400, "msg": message, "result": {"analysis": ""}})

# 用户收藏
@bp.route('/collect')
def collect():
    # token bookid 验证token
    token = request.args.get('analysis')
    bookId = request.args.get('bookId')
    user = User.query.filter_by(token=token).first()
    if user:
        novel = Novels.query.get(bookId)
        if not novel:
            return jsonify({"retCode": 400, "msg": "小说不存在", "result": {}})

        book_collect = BookCollect(userId=user.id, bookId=bookId)
        db.session.add(book_collect)
        db.session.commit()
        return jsonify({"retCode": 200, "msg": "收藏成功", "result": {}})
    return jsonify({"retCode": 400, "msg": "认证失败", "result": {}})

# 用户取消收藏
@bp.route('/uncollect')
def uncollect():
    # token bookid 验证token
    token = request.args.get('analysis')
    bookId = request.args.get('bookId')
    user = User.query.filter_by(token=token).first()
    if user:
        # 判断用户是否收藏
        book_collect = BookCollect.query.filter_by(userId=user.id, bookId=bookId).first()
        print(book_collect)
        if book_collect:
            db.session.delete(book_collect)
            return jsonify({"retCode": 200, "msg": "取消收藏成功", "result": {}})
        else:
            return jsonify({"retCode": 400, "msg": "收藏不存在", "result": {}})
    return jsonify({"retCode": 400, "msg": "认证失败", "result": {}})


# 用户批量取消收藏
@bp.route('/uncollectmany')
def uncollectmany():
    # token bookid 验证token
    token = request.args.get('analysis')
    bookIds = request.args.get('bookIds')
    try:
        bookId_list = bookIds.split(',')
    except:
        return jsonify({"retCode": 400, "msg": "参数错误", "result": {}})
    user = User.query.filter_by(token=token).first()
    if user:
        # 判断用户是否收藏
        print(bookId_list)
        for bookId in bookId_list:
            book_collect = BookCollect.query.filter_by(userId=user.id, bookId=bookId).first()
            if book_collect:
                db.session.delete(book_collect)
                db.session.commit()
        return jsonify({"retCode": 200, "msg": "取消收藏成功", "result": {}})
    return jsonify({"retCode": 400, "msg": "认证失败", "result": {}})


# 获取用户收藏
@bp.route('/getcollect')
def getcollect():
    # token 验证token 认证失败 获取用户id 获取收藏
    token = request.args.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        book_collect = BookCollect.query.filter_by(userId=user.id).all()
        # 根据bookId获取小说详情
        novelId_list = []
        for novel in book_collect:
            novelId_list.append({novel.bookId})
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
    return jsonify({"retCode": 400, "msg": "认证失败", "result": []})

# 用户性别重选
@bp.route('/resetgender')
def resetgender():
    # 获取用户token
    # token 验证token 认证失败 获取用户id 获取收藏
    token = request.args.get('analysis')
    gender = request.args.get('gender')
    user = User.query.filter_by(token=token).first()
    if user:
        user.gender = gender
        db.session.commit()
        return jsonify({"retCode": 200, "msg": "修改成功", "result": {}})
    return jsonify({"retCode": 400, "msg": "认证失败", "result": {}})
