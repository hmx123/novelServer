import os, json
import re
import time
from datetime import datetime

import requests
from flask import Blueprint, request

import config
from apps.common.forms import RegisterForm, LoginForm, ResetpwdForm, ForgetPassword
from apps.common.models import User, BookCollect, Novels, NovelType, Author, Chapters, NovelComment, Feedback, \
    NovelHistory, CartoonComment, Cartoon, UserPraise, NovelReadingRecord, Contents, CartoonReadingRecord, \
    CartoonChapter, CommentReport
from apps.common.wyyapi import sendcode, checkcode
from apps.front.decorators import novelOb_novelList
from exts import db, photos

from utils import zlcache
from PIL import Image
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    if not phone:
        return json.dumps({"retCode": 400, "msg": "获取失败，请检查手机号是否正确", "result": {}}, ensure_ascii=False)
    ret = re.match(r"^1[35678]\d{9}$", phone)
    if not ret:
        return json.dumps({"retCode": 400, "msg": "获取失败，请检查手机号是否正确", "result": {}}, ensure_ascii=False)
    user_ip = request.remote_addr
    uu = '%s-%s' % (user_ip, phone)
    if zlcache.get(uu):
        return json.dumps({"retCode": 400, "msg": "获取失败，请不要重复获取验证码", "result": {}}, ensure_ascii=False)
    zlcache.set(uu, phone, 30)
    if sendcode(phone):
        return json.dumps({"retCode": 200, "msg": "发送成功", "result": {}}, ensure_ascii=False)
    else:
        return json.dumps({"retCode": 400, "msg": "获取失败，请不要重复获取验证码", "result": {}}, ensure_ascii=False)

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
            return json.dumps({"retCode": 400, "msg": "用户已注册", "result": {"analysis": ""}}, ensure_ascii=False)
        code = form.code.data
        password = form.password.data
        gender = form.gender.data

        if not checkcode(phone, code):
            return json.dumps({"retCode": 400, "msg": "验证码错误", "result": {"analysis": ""}}, ensure_ascii=False)
        # 生成token
        token = rand_string()
        user = User(username=phone, password=password, phone=phone, token=token, gender=gender, icon='default.png', signer='')
        db.session.add(user)
        db.session.commit()
        return json.dumps({"retCode": 200, "msg": "success", "result": {"analysis": token}}, ensure_ascii=False)
    message = form.errors.popitem()[1][0]
    return json.dumps({"retCode": 400, "msg": message, "result": {"analysis": ""}}, ensure_ascii=False)

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
                return json.dumps({"retCode": 200, "msg": "修改密码成功", "result": {"analysis": token}}, ensure_ascii=False)
            return json.dumps({"retCode": 400, "msg": "用户名或密码错误", "result": {"analysis": ""}}, ensure_ascii=False)

        return json.dumps({"retCode": 400, "msg": "该用户不存在", "result": {"analysis": ""}}, ensure_ascii=False)
    message = form.errors.popitem()[1][0]
    return json.dumps({"retCode": 400, "msg": message, "result": {"analysis": ""}}, ensure_ascii=False)

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
                return json.dumps({"retCode": 400, "msg": "验证码错误", "result": {"analysis": ""}}, ensure_ascii=False)
            # 生成token
            token = rand_string()
            user.password = password
            user.token = token
            db.session.add(user)
            db.session.commit()
            return json.dumps({"retCode": 200, "msg": "success", "result": {"analysis": token}}, ensure_ascii=False)
        return json.dumps({"retCode": 400, "msg": "该用户不存在", "result": {"analysis": ""}}, ensure_ascii=False)


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
            return json.dumps({"retCode": 200, "msg": "success", "result": {"analysis": token}}, ensure_ascii=False)
        return json.dumps({"retCode": 400, "msg": "账号或密码错误", "result": {"analysis": ""}}, ensure_ascii=False)
    message = form.errors.popitem()[1][0]
    return json.dumps({"retCode": 400, "msg": message, "result": {"analysis": ""}}, ensure_ascii=False)


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
            return json.dumps({"retCode": 400, "msg": "小说不存在", "result": {}}, ensure_ascii=False)

        book_collect = BookCollect(userId=user.id, bookId=bookId, type=1)
        db.session.add(book_collect)
        db.session.commit()
        return json.dumps({"retCode": 200, "msg": "收藏成功", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 400, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 用户取消收藏
@bp.route('/uncollect')
def uncollect():
    # token bookid 验证token
    token = request.args.get('analysis')
    bookId = request.args.get('bookId')
    user = User.query.filter_by(token=token).first()
    if user:
        # 判断用户是否收藏
        book_collect = BookCollect.query.filter_by(userId=user.id, bookId=bookId, type=1).first()

        if book_collect:
            db.session.delete(book_collect)
            return json.dumps({"retCode": 200, "msg": "取消收藏成功", "result": {}}, ensure_ascii=False)
        else:
            return json.dumps({"retCode": 400, "msg": "收藏不存在", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 400, "msg": "认证失败", "result": {}}, ensure_ascii=False)


# 用户批量取消收藏
@bp.route('/uncollectmany')
def uncollectmany():
    # token bookid 验证token
    token = request.args.get('analysis')
    bookIds = request.args.get('bookIds')
    try:
        bookId_list = bookIds.split(',')
    except:
        return json.dumps({"retCode": 400, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    user = User.query.filter_by(token=token).first()
    if user:
        # 判断用户是否收藏
        for bookId in bookId_list:
            book_collect = BookCollect.query.filter_by(userId=user.id, bookId=bookId, type=1).first()
            if book_collect:
                db.session.delete(book_collect)
                db.session.commit()
        return json.dumps({"retCode": 200, "msg": "取消收藏成功", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 400, "msg": "认证失败", "result": {}}, ensure_ascii=False)


# 获取用户收藏
@bp.route('/getcollect')
def getcollect():
    # token 验证token 认证失败 获取用户id 获取收藏
    token = request.args.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        book_collect = BookCollect.query.filter_by(userId=user.id, type=1).all()
        # 根据bookId获取小说详情
        novel_list = []
        for collect in book_collect:
            novel = Novels.query.get(collect.bookId)
            is_read = collect.isread
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
                "countchapter": countchapter,
                "isread": is_read
            })
        return json.dumps({"retCode": 200, "msg": "success", "result": novel_list}, ensure_ascii=False)
    return json.dumps({"retCode": 400, "msg": "认证失败", "result": {}}, ensure_ascii=False)

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
        return json.dumps({"retCode": 200, "msg": "修改成功", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 400, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 设置书籍已读未读
@bp.route('/isread')
def isread():
    token = request.args.get('analysis')
    bookId = request.args.get('bookId')
    user = User.query.filter_by(token=token).first()
    if user:
        # 判断用户是否收藏
        collect = BookCollect.query.filter_by(userId=user.id, bookId=bookId, type=1).first()
        if collect:
            # 修改已读状态
            collect.isread = 1
            db.session.commit()
            return json.dumps({"retCode": 200, "msg": "修改成功", "result": {}}, ensure_ascii=False)
        return json.dumps({"retCode": 400, "msg": "收藏不存在", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 400, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# -------------------------------------v2版本--start-----------------------------
# 用户收藏 增加用户书本阅读进度  本周阅读分钟数
@bp.route('/collects')
def collects():
    # token bookid 验证token
    token = request.args.get('analysis')
    bookId = request.args.get('bookId')
    # 已读未读
    isread = request.args.get('read')
    if not bookId or not bookId.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    # 阅读进度
    read_progress = request.args.get('progress')
    if isread == '1':
        isread = 1
    elif isread == '0':
        isread = 0
    else:
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    if not read_progress or not read_progress.isdigit():
        read_progress = 0
    if read_progress.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    if int(read_progress) > 100:
        read_progress = 100
    user = User.query.filter_by(token=token).first()

    if user:
        # 判断小说是否收藏过了
        is_collect = BookCollect.query.filter_by(userId=user.id, bookId=bookId, type=1).first()
        if is_collect:
            return json.dumps({"retCode": 403, "msg": "小说已在收藏夹", "result": {}}, ensure_ascii=False)
        novel = Novels.query.get(bookId)
        if not novel:
            return json.dumps({"retCode": 402, "msg": "小说不存在", "result": {}}, ensure_ascii=False)

        book_collect = BookCollect(userId=user.id, bookId=bookId, read_progress=read_progress, isread=isread, type=1)
        db.session.add(book_collect)
        db.session.commit()
        return json.dumps({"retCode": 200, "msg": "收藏成功", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 用户批量收藏
@bp.route('/collectb')
def collectb():
    books = request.args.get('books')
    progress = request.args.get('progress')
    isread = request.args.get('read')
    token = request.args.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        try:
            bookId_list = books.split(',')
            progress_list = progress.split(',')
            isread_list = isread.split(',')
        except:
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        # 判断bookId_list的长度和progress_list长度
        if len(bookId_list) == len(progress_list) == len(isread_list):
            book_collect_list = []
            for x in range(len(bookId_list)):
                bookId = bookId_list[x]
                read_progress = progress_list[x]
                if not read_progress or not read_progress.isdigit():
                    read_progress = 0
                if isread_list[x] == '1':
                    isread = 1
                elif isread_list[x] == '0':
                    isread = 0
                else:
                    return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
                # 判断小说是否收藏过了
                is_collect = BookCollect.query.filter_by(userId=user.id, bookId=bookId, type=1).first()
                if is_collect:
                    # 收藏过了 更新阅读进度和阅读状态
                    is_collect.read_progress = read_progress
                    is_collect.isread = isread
                    book_collect_list.append(is_collect)
                    continue
                novel = Novels.query.get(bookId)
                if not novel:
                    return json.dumps({"retCode": 402, "msg": "小说不存在", "result": {}}, ensure_ascii=False)
                book_collect = BookCollect(userId=user.id, bookId=bookId, read_progress=read_progress, isread=isread, type=1)

                book_collect_list.append(book_collect)
            db.session.add_all(book_collect_list)
            db.session.commit()
            return json.dumps({"retCode": 200, "msg": "收藏成功", "result": {}}, ensure_ascii=False)
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 更新用户小说的阅读进度
@bp.route('/upprogress')
def upprogress():
    # token bookid 验证token
    token = request.args.get('analysis')
    bookId = request.args.get('bookId')
    # 阅读进度
    read_progress = request.args.get('progress')
    if not read_progress or not read_progress.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    user = User.query.filter_by(token=token).first()
    if user:
        novel = Novels.query.get(bookId)
        if not novel:
            return json.dumps({"retCode": 402, "msg": "小说不存在", "result": {}}, ensure_ascii=False)
        # 获取到用户收藏的小说
        book_collect = BookCollect.query.filter_by(userId=user.id, bookId=bookId, type=1).first()
        if not book_collect:
            return json.dumps({"retCode": 405, "msg": "收藏不存在", "result": {}}, ensure_ascii=False)
        if int(read_progress) > 100:
            read_progress = 100
        book_collect.read_progress = read_progress
        db.session.add(book_collect)
        db.session.commit()
        return json.dumps({"retCode": 200, "msg": "更新成功", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 更新用户本周阅读分钟
@bp.route('/uptime')
def uptime():
    # token bookid 验证token
    token = request.args.get('analysis')
    read_time = request.args.get('readt')
    if not read_time or not read_time.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    user = User.query.filter_by(token=token).first()
    if user:
        user.read_time = user.read_time + int(read_time)
        db.session.add(user)
        db.session.commit()
        return json.dumps({"retCode": 200, "msg": "更新成功", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 获取用户收藏 返回书本 阅读进度 本周阅读分钟数
@bp.route('/getcollects')
def getcollects():
    # token bookid 验证token
    token = request.args.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        # 根据用户id获取阅读书籍
        book_collect = BookCollect.query.filter_by(userId=user.id, type=1).order_by(-BookCollect.addtime).all()
        # 用户本周阅读分钟数
        read_time = user.read_time
        # 根据bookId获取小说详情
        novel_list = []
        for collect in book_collect:
            novel = Novels.query.get(collect.bookId)
            is_read = collect.isread
            read_progress = collect.read_progress
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
                "countchapter": countchapter,
                "isread": is_read,
                "read_progress": read_progress
            })
        return json.dumps({"retCode": 200, "msg": "success", "result": {"data": novel_list, "read_time": read_time}}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 小说评论
@bp.route('/comment', methods=['POST'])
def comment():
    # 获取用户评论 获取用户token 获取小说id
    comment = request.form.get('comment')
    # if len(comment) < 5:
    #     return json.dumps({"retCode": 405, "msg": "字数不能少于5个字", "result": {}}, ensure_ascii=False)
    token = request.form.get('analysis')
    bookId = request.form.get('bookId')
    star = request.form.get('star')
    if not bookId or not bookId.isdigit():
        bookId = 0
    if not star or not star.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    if int(star) > 5:
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    if token == 0:
        user = 0
    else:
        user = User.query.filter_by(token=token).first()
    # 判断小说是否存在
    novel = Novels.query.get(bookId)
    if not novel:
        return json.dumps({"retCode": 405, "msg": "小说不存在", "result": {}}, ensure_ascii=False)
    # 判断是游客还是用户
    if user:
        # 获取用户的昵称 头像
        username = user.username
        icon = user.icon
        userId = user.id
    else:
        # ip = time.strftime("%Y%m%d", time.localtime(time.time()))
        # username = '游客%s' % ip
        # icon = 'default.png'
        # userId = 0
        return json.dumps({"retCode": 405, "msg": "登录后可以评论更多书籍哦~", "result": {}}, ensure_ascii=False)
    # 新增用户评论
    comm = NovelComment(novelId=bookId, userId=userId, comment=comment, username=username, icon=icon, commentId=0, star = star)
    db.session.add(comm)
    db.session.commit()
    return json.dumps({"retCode": 200, "msg": "评论成功", "result": {}}, ensure_ascii=False)

# 评论小说的评论
@bp.route('/comments', methods=['POST'])
def comments():
    commentId = request.form.get('commentId')
    if not commentId or not commentId.isdigit():
        commentId = 0
    bookId = request.form.get('bookId')
    if not bookId or not bookId.isdigit():
        bookId = 0
    token = request.form.get('analysis')
    comment = request.form.get('comment')
    # 判断被评论的评论是否存在
    novel_comment = NovelComment.query.get(commentId)
    if not novel_comment or str(novel_comment.novelId) != bookId:
        return json.dumps({"retCode": 405, "msg": "评论不存在", "result": {}}, ensure_ascii=False)
    if token == 0:
        user = 0
    else:
        user = User.query.filter_by(token=token).first()

    # 判断小说是否存在
    novel = Novels.query.get(bookId)
    if not novel:
        return json.dumps({"retCode": 405, "msg": "小说不存在", "result": {}}, ensure_ascii=False)
    # 判断是游客还是用户
    if user:
        # 获取用户的昵称 头像
        username = user.username
        icon = user.icon
        userId = user.id
    else:
        # ip = time.strftime("%Y%m%d", time.localtime(time.time()))
        # username = '游客%s' % ip
        # icon = 'default.png'
        # userId = 0
        return json.dumps({"retCode": 405, "msg": "登录后可以评论更多书籍哦~", "result": {}}, ensure_ascii=False)
    # 判断用户是否对相同的评论评论过了
    nc = NovelComment.query.filter_by(novelId=bookId, userId=userId, commentId=commentId).first()
    if nc:
        return json.dumps({"retCode": 405, "msg": "Hi，您已评论过哦~", "result": {}}, ensure_ascii=False)
    # 新增用户评论
    comm = NovelComment(novelId=bookId, userId=userId, comment=comment, username=username, icon=icon, commentId=commentId)
    db.session.add(comm)
    db.session.commit()
    return json.dumps({"retCode": 200, "msg": "评论成功", "result": {}}, ensure_ascii=False)

# 点赞评论
@bp.route('/compraise')
def compraise():
    # 获取评论id
    commentId = request.args.get('commentId')
    # 获取用户标识
    token = request.args.get('analysis')
    if not commentId or not commentId.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    bookId = request.args.get('bookId')
    if not bookId or not bookId.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    user = User.query.filter_by(token=token).first()
    if user:
        # 获取用户id
        userId = user.id
        # 判断用户是否点赞
        up = UserPraise.query.filter_by(uId=userId, commentId=commentId, type=1).first()
        if up:
            return json.dumps({"retCode": 405, "msg": "您已赞过了", "result": {}}, ensure_ascii=False)
        else:
            # 添加到点赞
            up = UserPraise(uId=userId, commentId=commentId, type=1)
            db.session.add(up)
    else:
        # 用户登录
        return json.dumps({"retCode": 405, "msg": "请登录后点赞", "result": {}}, ensure_ascii=False)

    # 判断被评论的评论是否存在
    novel_comment = NovelComment.query.get(commentId)
    if not novel_comment or str(novel_comment.novelId) != bookId:
        return json.dumps({"retCode": 405, "msg": "评论不存在", "result": {}}, ensure_ascii=False)
    # # 获取请求头的ip
    # ip = request.headers['X-Real-Ip']
    # comment = zlcache.get(ip)
    # if comment and commentId == comment.decode():
    #     return json.dumps({"retCode": 405, "msg": "您已赞过了", "result": {}}, ensure_ascii=False)
    # # 把这个ip加入到redis中
    # zlcache.set(ip, commentId, 86400)   # 1天

    praise = novel_comment.praise
    novel_comment.praise = praise+1
    db.session.add(novel_comment)
    db.session.commit()
    return json.dumps({"retCode": 200, "msg": "success", "result": {}})



# 根据小说id获取小说评论
@bp.route('/getcomment')
def getcomment():
    host = 'http://%s' % request.host
    # 获取小说
    bookId = request.args.get('bookId')
    if not bookId or not bookId.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    novel_comments = NovelComment.query.filter_by(novelId=bookId).all()
    comment_list = []
    for novel_comment in novel_comments[::-1]:
        if novel_comment.commentId == 0:
            # 获取这条评论的评论数量
            count = NovelComment.query.filter_by(novelId=bookId, commentId=novel_comment.id).all()
            # 判断用户userId是否是游客
            userId = novel_comment.userId
            if userId != 0:
                # 通过userId关联用户名，用户头像
                u = User.query.get(userId)
                username = u.username
                icon = u.icon
                comment_dict = {
                    'id': novel_comment.id,
                    'comment': novel_comment.comment,
                    'username': username,
                    'addtime': str(novel_comment.addtime),
                    'icon': '%s/static/images/icon/%s' % (host, icon),
                    'praise': novel_comment.praise,
                    'count': len(count),
                    'star': novel_comment.star
                }
            else:
                comment_dict = {
                    'id': novel_comment.id,
                    'comment': novel_comment.comment,
                    'username': novel_comment.username,
                    'addtime': str(novel_comment.addtime),
                    'icon': '%s/static/images/icon/%s' % (host, novel_comment.icon),
                    'praise': novel_comment.praise,
                    'count': len(count),
                    'star': novel_comment.star
                }
            comment_list.append(comment_dict)
    return json.dumps({"retCode": 200, "msg": "success", "result": comment_list}, ensure_ascii=False)

# 根据小说和评论id获取评论的评论
@bp.route('/commentcom')
def commentcom():
    host = 'http://%s' % request.host
    commentId = request.args.get('commentId')
    if not commentId or not commentId.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    bookId = request.args.get('bookId')
    if not bookId or not bookId.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    # 判断传入的格式
    # 判断评论是否存在
    novel_comment = NovelComment.query.filter_by(novelId=bookId, commentId=commentId).all()
    if novel_comment:
        comment_list = []
        for novel_comment in novel_comment[::-1]:
            # 获取这条评论的评论数量
            count = NovelComment.query.filter_by(novelId=bookId, commentId=novel_comment.id).all()
            # 判断用户userId是否是游客
            userId = novel_comment.userId
            if userId != 0:
                # 通过userId关联用户名，用户头像
                u = User.query.get(userId)
                username = u.username
                icon = u.icon
                comment_dict = {
                    'id': novel_comment.id,
                    'comment': novel_comment.comment,
                    'username': username,
                    'addtime': str(novel_comment.addtime),
                    'icon': '%s/static/images/icon/%s' % (host, icon),
                    'praise': novel_comment.praise,
                    'count': len(count),
                    'star': novel_comment.star
                }
            else:
                comment_dict = {
                    'id': novel_comment.id,
                    'comment': novel_comment.comment,
                    'username': novel_comment.username,
                    'addtime': str(novel_comment.addtime),
                    'icon': '%s/static/images/icon/%s' % (host, novel_comment.icon),
                    'praise': novel_comment.praise,
                    'count': len(count),
                    'star': novel_comment.star
                }

            comment_list.append(comment_dict)
    else:
        return json.dumps({"retCode": 405, "msg": "评论不存在", "result": []}, ensure_ascii=False)
    return json.dumps({"retCode": 200, "msg": "success", "result": comment_list}, ensure_ascii=False)


# 用户验证码登录
@bp.route('/logincode', methods=['POST'])
def logincode():
    phone = request.form.get('phone')
    if phone == '13302984135':
        # 判断数据库是否存在
        u = User.query.filter_by(phone=phone).first()
        # 生成token
        token = rand_string()
        host = 'http://%s' % request.host
        # 若用户存在 更新 否则插入新用户
        if u:
            u.token = token
            username = u.username
            icon = u.icon
        else:
            # 生成用户默认昵称
            icon = 'default.png'
            now_time = datetime.now()
            now_time = now_time.strftime("%Y%m%d")
            username = '%s_%s' % (now_time, phone[7:])
            # 新增用户默认头像，用户签名，用户昵称
            u = User(phone=phone, token=token, username=username, password='1', gender=0, icon='default.png', signer='')
        icon = '%s/static/images/icon/%s' % (host, icon)
        db.session.add(u)
        db.session.commit()
        return json.dumps(
            {"retCode": 200, "msg": "success", "result": {"analysis": token, "username": username, "icon": icon}},
            ensure_ascii=False)
    code = request.form.get('code')
    # 验证验证码
    if not checkcode(phone, code):
        return json.dumps({"retCode": 400, "msg": "验证码错误", "result": {"analysis": ""}}, ensure_ascii=False)
    # 判断数据库是否存在
    u = User.query.filter_by(phone=phone).first()
    # 生成token
    token = rand_string()
    host = 'http://%s' % request.host
    # 若用户存在 更新 否则插入新用户
    if u:
        u.token = token
        username = u.username
        icon = u.icon
    else:
        # 生成用户默认昵称
        icon = 'default.png'
        now_time = datetime.now()
        now_time = now_time.strftime("%Y%m%d")
        username = '%s_%s' % (now_time, phone[7:])
        # 新增用户默认头像，用户签名，用户昵称
        u = User(phone=phone, token=token, username=username, password='1', gender=0, icon='default.png', signer='')
    icon = '%s/static/images/icon/%s' % (host, icon)
    db.session.add(u)
    db.session.commit()
    return json.dumps({"retCode": 200, "msg": "success", "result": {"analysis": token, "username": username, "icon": icon}}, ensure_ascii=False)

# 调用微信登录
@bp.route('/wechat_login')
def wechat_login():
    code = request.args.get('code')
    host = 'http://%s' % request.host
    # 通过code获取access_token
    url = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid=%s&secret=%s&code=%s&grant_type=authorization_code'
    response = requests.get(url=url % (config.WECHAT_APPID, config.WECHAT_SECRET, code)).json()
    try:
        access_token = response['access_token']
        openid = response['openid']
        unionid = response['unionid']
    except:
        return json.dumps({"retCode": 401, "msg": "认证失败", "result": {"analysis": ""}}, ensure_ascii=False)
    token = rand_string()
    # 判断用户是否存在
    u = User.query.filter_by(phone=unionid).first()
    if u:
        u.token = token
        username = u.username
        icon = u.icon
    else:
        url_info = 'https://api.weixin.qq.com/sns/userinfo?access_token=%s&openid=%s'
        response_info = requests.get(url=url_info % (access_token, openid)).json()
        # 获取用户基本信息
        username = response_info['nickname'].encode('ISO-8859-1').decode('UTF-8')
        gender = response_info['sex']
        if gender == 2:
            gender = 0
        headimgurl = response_info['headimgurl']
        # 下载头像
        response = requests.get(url=headimgurl, verify=False)
        if response.status_code == 200:
            # 生成用户头像名
            icon = '%s.png' % rand_string()
            path = '%s/static/images/icon/%s' % (os.getcwd(), icon)
            with open(path, 'wb') as f:
                f.write(response.content)
        else:
            icon = 'default.png'
        # 将用户信息保存
        u = User(username=username, password='1', phone=unionid, gender=gender, token=token, icon=icon, signer='')
    icon = '%s/static/images/icon/%s' % (host, icon)
    db.session.add(u)
    db.session.commit()
    return json.dumps(
        {"retCode": 200, "msg": "success", "result": {"analysis": token, "username": username, "icon": icon}},
        ensure_ascii=False)

# https://api.weixin.qq.com/sns/oauth2/access_token?appid=wxb5683bff60e1a92f&secret=55428fce6006e3b5d04be932091ef16f&code=001eN3Cf2FyNtI0pwKAf2LzrCf2eN3CB&grant_type=authorization_code
# {"access_token":"27_iaAfMFIzufgMUA7DQdbW_TjLC6l3xdi574wECHkc93defcRWw-6TNW57oYzBRh-zjO7arbgZ5Udnd8NVPEqx1sGvYF0UxS0BgQXhjIDxg4I",
# "expires_in":7200,"refresh_token":"27_CGyKh3jq2q3VF1uSe5fqHogMwAH3k-vG22ilAotyoP5vSaxfAGZnO8uJuV1A3IRf2hMhZAprylLzra7tORn7-YMtVVkRB07_qi8nVXZYqcY",
# "openid":"oPk0Gw1PCODQZbntjOUUszkkR0LA","scope":"snsapi_userinfo","unionid":"o1NPcvlzEAWPQVZz0OfIbpBfA52c"}

# 获取用户信息
@bp.route('/userinfo')
def userinfo():
    token = request.args.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        host = 'http://%s' % request.host
        signer = user.signer
        if not signer:
            signer = ''
        # 获取用户信息
        user_dict = {
            'username': user.username,
            'gender': user.gender,
            'icon': '%s/static/images/icon/%s' % (host, user.icon),
            'signer': signer
        }
        return json.dumps({"retCode": 200, "msg": "success", "result": user_dict}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 修改用户昵称 头像 签名 性别
# 修改用户头像
@bp.route('/icon', methods=['POST'])
def icon():
    photo = request.files.get('photo')
    token = request.form.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        # 提取文件后缀
        suffix = os.path.splitext(photo.filename)[1]
        # 验证图片格式是否正确
        img_format = ['.jpg', '.png', '.JPG', '.PNG']
        if suffix not in img_format:
            return json.dumps({"retCode": 405, "msg": "图片格式不正确", "result": {}}, ensure_ascii=False)
        # 生成随机文件名
        filename = rand_string() + suffix
        # 保存文件
        photo.save(os.path.join(config.UPLOADED_PHOTOS_DEST, filename))
        pathname = os.path.join(config.UPLOADED_PHOTOS_DEST, filename)
        # 打开文件
        img = Image.open(pathname)
        # 设置尺寸
        img.thumbnail((256, 256))
        # 保存图片
        img.save(pathname)
        # 删除原来的头像文件（default.jpg除外）
        if user.icon != 'default.png':
            os.remove(os.path.join(config.UPLOADED_PHOTOS_DEST, user.icon))
        # 将新的头像文件名保存到数据库
        user.icon = filename
        db.session.add(user)
        return json.dumps({"retCode": 200, "msg": "修改成功", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)

@bp.route('/upinfo', methods=['POST'])
def upinfo():
    type = request.form.get('type')
    data = request.form.get('data')
    token = request.form.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        if type == 'username':
            # 判断data是否符合规范
            if len(data) > 30:
                return json.dumps({"retCode": 405, "msg": "昵称过长", "result": {}}, ensure_ascii=False)
            user.username = data
        elif type == 'gender':
            if data == '1' or data == '0':
                user.gender = data
            else:
                return json.dumps({"retCode": 405, "msg": "性别只能为男或女", "result": {}}, ensure_ascii=False)
        elif type == 'signer':
            if len(data) > 250:
                return json.dumps({"retCode": 405, "msg": "签名过长", "result": {}}, ensure_ascii=False)
            user.signer = data
        else:
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        db.session.add(user)
        db.session.commit()
        return json.dumps({"retCode": 200, "msg": "修改成功", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 用户意见反馈接口
@bp.route('/suggest', methods=['POST'])
def suggest():
    advise = request.form.get('advise')
    phone = request.form.get('phone')
    if not advise:
        return json.dumps({"retCode": 405, "msg": "请填写建议", "result": {}}, ensure_ascii=False)
    if not phone:
        phone = ''
    fb = Feedback(suggest=advise, phone=phone)
    db.session.add(fb)
    db.session.commit()
    return json.dumps({"retCode": 200, "msg": "反馈成功", "result": {}}, ensure_ascii=False)

# 添加用户浏览记录
@bp.route('/history')
def history():
    token = request.args.get('analysis')
    bookId = request.args.get('bookId')
    if not bookId or not bookId.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    user = User.query.filter_by(token=token).first()
    if user:
        novel = Novels.query.get(bookId)
        if novel:
            #判断用户是否已经添加过浏览记录了
            novel_history = NovelHistory.query.filter_by(userId=user.id, novelId=bookId, type=1).first()
            if novel_history:
                return json.dumps({"retCode": 200, "msg": "success", "result": {}}, ensure_ascii=False)
            nh = NovelHistory(userId=user.id, novelId=bookId, type=1)
            db.session.add(nh)
            db.session.commit()
            return json.dumps({"retCode": 200, "msg": "success", "result": {}}, ensure_ascii=False)
        return json.dumps({"retCode": 405, "msg": "小说不存在", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 批量添加用户浏览记录
@bp.route('/historys')
def historys():
    token = request.args.get('analysis')
    bookIds = request.args.get('bookIds')
    timees = request.args.get('timees')
    user = User.query.filter_by(token=token).first()
    if user:
        try:
            bookId_list = bookIds.split(',')
            timee_list = timees.split(',')
        except:
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        # 判断长度是否相等
        if len(bookId_list) != len(bookId_list):
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)

        for x in range(len(bookId_list)):
            bookId = bookId_list[x]
            # 判断bookid是否符合规范
            if not bookId or not bookId.isdigit():
                return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
            # 判断日期格式是否正确
            try:
                datetime.strptime(timee_list[x], '%Y-%m-%d %H:%M:%S')
            except:
                return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
            novel = Novels.query.get(bookId)
            # 判断小说是否存在
            if novel:
                # 判断用户是否已经添加过浏览记录了
                novel_history = NovelHistory.query.filter_by(userId=user.id, novelId=bookId, type=1).first()
                if not novel_history:
                    nh = NovelHistory(userId=user.id, novelId=bookId, addtime=timee_list[x], type=1)
                    db.session.add(nh)
        db.session.commit()
        return json.dumps({"retCode": 200, "msg": "success", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 获取用户浏览记录
@bp.route('/gethistory')
def gethistory():
    token = request.args.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        nh_list = NovelHistory.query.filter_by(userId=user.id, type=1).order_by(NovelHistory.addtime).all()
        novel_list = []
        for nh in nh_list[::-1]:
            novelId = nh.novelId
            novel = Novels.query.get(novelId)
            if novel:
                # 判断这本书用户是否收藏
                book_collect = BookCollect.query.filter_by(userId=user.id, bookId=novelId, type=1).first()
                if book_collect:
                    iscollect = 1
                else:
                    iscollect = 0
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
                    "countchapter": countchapter,
                    "iscollect": iscollect,
                    'timee': str(nh.addtime)
                })
        return json.dumps({"retCode": 200, "msg": "success", "result": novel_list}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 清空浏览记录
@bp.route('/clearhis')
def clearhis():
    token = request.args.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        nh_list = NovelHistory.query.filter_by(userId=user.id, type=1).all()
        for nh in nh_list:
            db.session.delete(nh)
        db.session.commit()
        return json.dumps({"retCode": 200, "msg": "success", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)
# -------------------------------------v2版本--end-------------------------------

# ----------------------------------第三版漫画接口-start------------------------------------------------
# 漫画评论
@bp.route('/carcomment', methods=['POST'])
def carcomment():
    # 获取用户评论 获取用户token 获取小说id
    comment = request.form.get('comment')
    # if len(comment) < 5:
    #     return json.dumps({"retCode": 405, "msg": "字数不能少于5个字", "result": {}}, ensure_ascii=False)
    token = request.form.get('analysis')
    bookId = request.form.get('cartoonId')
    star = request.form.get('star')
    if not bookId or not bookId.isdigit():
        bookId = 0
    if not star or not star.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    if int(star) > 5:
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    if token == 0:
        user = 0
    else:
        user = User.query.filter_by(token=token).first()
    # 判断小说是否存在
    novel = Novels.query.get(bookId)
    if not novel:
        return json.dumps({"retCode": 405, "msg": "漫画不存在", "result": {}}, ensure_ascii=False)
    # 判断是游客还是用户
    if user:
        # 获取用户的昵称 头像
        username = user.username
        icon = user.icon
        userId = user.id
    else:
        # ip = time.strftime("%Y%m%d", time.localtime(time.time()))
        # username = '游客%s' % ip
        # icon = 'default.png'
        # userId = 0
        return json.dumps({"retCode": 405, "msg": "登录后可以评论更多书籍哦~", "result": {}}, ensure_ascii=False)
    # 新增用户评论
    comm = CartoonComment(novelId=bookId, userId=userId, comment=comment, username=username, icon=icon, commentId=0, star = star)
    db.session.add(comm)
    db.session.commit()
    return json.dumps({"retCode": 200, "msg": "评论成功", "result": {}}, ensure_ascii=False)

# 评论漫画的评论
@bp.route('/carcomments', methods=['POST'])
def carcomments():
    commentId = request.form.get('commentId')
    if not commentId or not commentId.isdigit():
        commentId = 0
    bookId = request.form.get('cartoonId')
    if not bookId or not bookId.isdigit():
        bookId = 0
    token = request.form.get('analysis')
    comment = request.form.get('comment')

    # 判断被评论的评论是否存在
    novel_comment = CartoonComment.query.get(commentId)
    if not novel_comment or str(novel_comment.novelId) != bookId:
        return json.dumps({"retCode": 405, "msg": "评论不存在", "result": {}}, ensure_ascii=False)
    if token == 0:
        user = 0
    else:
        user = User.query.filter_by(token=token).first()

    # 判断小说是否存在
    novel = Cartoon.query.get(bookId)
    if not novel:
        return json.dumps({"retCode": 405, "msg": "漫画不存在", "result": {}}, ensure_ascii=False)
    # 判断是游客还是用户
    if user:
        # 获取用户的昵称 头像
        username = user.username
        icon = user.icon
        userId = user.id
        # 判断用户是否对相同的评论评论过了
        nc = CartoonComment.query.filter_by(novelId=bookId, userId=userId, commentId=commentId).first()
        if nc:
            return json.dumps({"retCode": 405, "msg": "Hi，您已评论过哦~", "result": {}}, ensure_ascii=False)
    else:
        # ip = time.strftime("%Y%m%d", time.localtime(time.time()))
        # username = '游客%s' % ip
        # icon = 'default.png'
        # userId = 0
        return json.dumps({"retCode": 405, "msg": "登录后可以评论更多书籍哦~", "result": {}}, ensure_ascii=False)
    # 新增用户评论
    comm = CartoonComment(novelId=bookId, userId=userId, comment=comment, username=username, icon=icon, commentId=commentId)
    db.session.add(comm)
    db.session.commit()
    return json.dumps({"retCode": 200, "msg": "评论成功", "result": {}}, ensure_ascii=False)

# 点赞漫画评论
@bp.route('/carcompraise')
def carcompraise():
    # 获取评论id
    commentId = request.args.get('commentId')
    if not commentId or not commentId.isdigit():
        commentId = 0
    bookId = request.args.get('cartoonId')
    if not bookId or not bookId.isdigit():
        bookId = 0
    token = request.args.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        # 获取用户id
        userId = user.id
        # 判断用户是否点赞
        up = UserPraise.query.filter_by(uId=userId, commentId=commentId, type=2).first()
        if up:
            return json.dumps({"retCode": 405, "msg": "您已赞过了", "result": {}}, ensure_ascii=False)
        else:
            # 添加到点赞
            up = UserPraise(uId=userId, commentId=commentId, type=2)
            db.session.add(up)
    else:
        # 用户登录
        return json.dumps({"retCode": 405, "msg": "请登录后点赞", "result": {}}, ensure_ascii=False)
    # 判断被评论的评论是否存在
    novel_comment = CartoonComment.query.get(commentId)
    if not novel_comment or str(novel_comment.novelId) != bookId:
        return json.dumps({"retCode": 405, "msg": "评论不存在", "result": {}}, ensure_ascii=False)
    # 获取请求头的ip
    # ip = request.headers['X-Real-Ip'] + 'cartoon'
    # comment = zlcache.get(ip)
    # if comment and commentId == comment.decode():
    #     return json.dumps({"retCode": 405, "msg": "您已赞过了", "result": {}}, ensure_ascii=False)
    # # 把这个ip加入到redis中
    # zlcache.set(ip, commentId, 86400)   # 1天
    praise = novel_comment.praise
    novel_comment.praise = praise+1
    db.session.add(novel_comment)
    db.session.commit()
    return json.dumps({"retCode": 200, "msg": "success", "result": {}})

# 根据漫画id获取漫画评论
@bp.route('/cargetcomment')
def cargetcomment():
    host = 'http://%s' % request.host
    # 获取小说
    bookId = request.args.get('cartoonId')
    if not bookId or not bookId.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    novel_comments = CartoonComment.query.filter_by(novelId=bookId).all()
    comment_list = []
    for novel_comment in novel_comments[::-1]:
        if novel_comment.commentId == 0:
            # 获取这条评论的评论数量
            count = CartoonComment.query.filter_by(novelId=bookId, commentId=novel_comment.id).all()
            # 判断用户userId是否是游客
            userId = novel_comment.userId
            if userId != 0:
                # 通过userId关联用户名，用户头像
                u = User.query.get(userId)
                username = u.username
                icon = u.icon
                comment_dict = {
                    'id': novel_comment.id,
                    'comment': novel_comment.comment,
                    'username': username,
                    'addtime': str(novel_comment.addtime),
                    'icon': '%s/static/images/icon/%s' % (host, icon),
                    'praise': novel_comment.praise,
                    'count': len(count),
                    'star': novel_comment.star
                }
            else:
                comment_dict = {
                    'id': novel_comment.id,
                    'comment': novel_comment.comment,
                    'username': novel_comment.username,
                    'addtime': str(novel_comment.addtime),
                    'icon': '%s/static/images/icon/%s' % (host, novel_comment.icon),
                    'praise': novel_comment.praise,
                    'count': len(count),
                    'star': novel_comment.star
                }

            comment_list.append(comment_dict)
    return json.dumps({"retCode": 200, "msg": "success", "result": comment_list}, ensure_ascii=False)

# 根据漫画和评论id获取评论的评论
@bp.route('/carcommentcom')
def carcommentcom():
    host = 'http://%s' % request.host
    commentId = request.args.get('commentId')
    if not commentId or not commentId.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    bookId = request.args.get('cartoonId')
    if not bookId or not bookId.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    # 判断传入的格式
    # 判断评论是否存在
    novel_comment = CartoonComment.query.filter_by(novelId=bookId, commentId=commentId).all()
    if novel_comment:
        comment_list = []
        for novel_comment in novel_comment[::-1]:
            # 获取这条评论的评论数量
            count = NovelComment.query.filter_by(novelId=bookId, commentId=novel_comment.id).all()
            # 判断用户userId是否是游客
            userId = novel_comment.userId
            if userId != 0:
                # 通过userId关联用户名，用户头像
                u = User.query.get(userId)
                username = u.username
                icon = u.icon
                comment_dict = {
                    'id': novel_comment.id,
                    'comment': novel_comment.comment,
                    'username': username,
                    'addtime': str(novel_comment.addtime),
                    'icon': '%s/static/images/icon/%s' % (host, icon),
                    'praise': novel_comment.praise,
                    'count': len(count),
                    'star': novel_comment.star
                }
            else:
                comment_dict = {
                    'id': novel_comment.id,
                    'comment': novel_comment.comment,
                    'username': novel_comment.username,
                    'addtime': str(novel_comment.addtime),
                    'icon': '%s/static/images/icon/%s' % (host, novel_comment.icon),
                    'praise': novel_comment.praise,
                    'count': len(count),
                    'star': novel_comment.star
                }

            comment_list.append(comment_dict)
    else:
        return json.dumps({"retCode": 405, "msg": "评论不存在", "result": []}, ensure_ascii=False)
    return json.dumps({"retCode": 200, "msg": "success", "result": comment_list}, ensure_ascii=False)



# -----------------------------------用户接口-start-----------------------------

# 单个添加用户浏览记录
@bp.route('/carhistory')
def carhistory():
    token = request.args.get('analysis')
    bookId = request.args.get('bookId')
    typee = request.args.get('type')  #1小说 2漫画
    if not bookId or not bookId.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    user = User.query.filter_by(token=token).first()
    if user:
        if typee == '1':
            novel = Novels.query.get(bookId)
        elif typee == '2':
            novel = Cartoon.query.get(bookId)
        else:
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        if novel:
            # 判断用户是否已经添加过浏览记录了
            novel_history = NovelHistory.query.filter_by(userId=user.id, novelId=bookId, type=typee).first()
            if novel_history:
                return json.dumps({"retCode": 200, "msg": "success", "result": {}}, ensure_ascii=False)
            nh = NovelHistory(userId=user.id, novelId=bookId, type=typee)
            db.session.add(nh)
            db.session.commit()
            return json.dumps({"retCode": 200, "msg": "success", "result": {}}, ensure_ascii=False)
        return json.dumps({"retCode": 405, "msg": "数据不存在", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 批量添加用户浏览记录
@bp.route('/carhistorys')
def carhistorys():
    token = request.args.get('analysis')
    bookIds = request.args.get('bookIds')
    timees = request.args.get('timees')
    types = request.args.get('types')
    user = User.query.filter_by(token=token).first()
    if user:
        try:
            bookId_list = bookIds.split(',')
            timee_list = timees.split(',')
            type_list = types.split(',')
        except:
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        # 判断长度是否相等
        if len(bookId_list) != len(bookId_list) != len(type_list):
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)

        for x in range(len(bookId_list)):
            bookId = bookId_list[x]
            # 判断bookid是否符合规范
            if not bookId or not bookId.isdigit():
                return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
            # 判断日期格式是否正确
            try:
                datetime.strptime(timee_list[x], '%Y-%m-%d %H:%M:%S')
            except:
                return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
            # 判断type是否正确
            typee = type_list[x]
            if typee not in ['1', '2']:
                return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
            novel = Novels.query.get(bookId)
            # 判断小说是否存在
            if novel:
                # 判断用户是否已经添加过浏览记录了
                novel_history = NovelHistory.query.filter_by(userId=user.id, novelId=bookId, type=typee).first()
                if not novel_history:
                    nh = NovelHistory(userId=user.id, novelId=bookId, addtime=timee_list[x], type=typee)
                    db.session.add(nh)
        db.session.commit()
        return json.dumps({"retCode": 200, "msg": "success", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 获取用户浏览记录
@bp.route('/cargethistory')
def cargethistory():
    host = 'http://%s' % request.host
    token = request.args.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        nh_list = NovelHistory.query.filter_by(userId=user.id).order_by(NovelHistory.addtime).all()
        novel_list = []
        for nh in nh_list[::-1]:
            novelId = nh.novelId
            typee = nh.type
            if typee == 1:
                novel = Novels.query.get(novelId)
            else:
                novel = Cartoon.query.get(novelId)
            if novel:
                # 判断这本书用户是否收藏
                book_collect = BookCollect.query.filter_by(userId=user.id, bookId=novelId, type=typee).first()
                if book_collect:
                    iscollect = 1
                else:
                    iscollect = 0
                if typee == 1:
                    # 根据作者id获取作者
                    authorId = novel.authorId
                    author = Author.query.get(authorId)
                    author = author.name
                    cover = novel.cover
                else:
                    author = novel.author
                    cover = '%s/static/cartoon/%s/%s' % (host, novel.id, novel.cover)
                novel_list.append({
                    'id': novel.id,
                    'name': novel.name,
                    'author': author,
                    'timee': str(nh.addtime),
                    'iscollect': iscollect,
                    'cover': cover,
                    'type': typee
                })
        return json.dumps({"retCode": 200, "msg": "success", "result": novel_list}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 清空用户浏览记录
@bp.route('/carclearhis')
def carclearhis():
    token = request.args.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        nh_list = NovelHistory.query.filter_by(userId=user.id).all()
        for nh in nh_list:
            db.session.delete(nh)
        db.session.commit()
        return json.dumps({"retCode": 200, "msg": "success", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)


# 用户漫画收藏 增加用户书本阅读进度
@bp.route('/carcollects')
def carcollects():
    # token bookid 验证token
    token = request.args.get('analysis')
    bookId = request.args.get('bookId')
    typee = request.args.get('type')
    if typee == '1':
        typee = 1
    elif typee == '2':
        typee = 2
    else:
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    # 已读未读
    isread = request.args.get('read')
    if not bookId or not bookId.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    # 阅读进度
    read_progress = request.args.get('progress')
    if isread == '1':
        isread = 1
    elif isread == '0':
        isread = 0
    else:
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    if not read_progress or not read_progress.isdigit():
        read_progress = 0
    if int(read_progress) > 100:
        read_progress = 100
    user = User.query.filter_by(token=token).first()

    if user:
        # 判断小说是否收藏过了
        is_collect = BookCollect.query.filter_by(userId=user.id, bookId=bookId, type=typee).first()
        if is_collect:
            return json.dumps({"retCode": 403, "msg": "小说已在收藏夹", "result": {}}, ensure_ascii=False)
        if typee == 1:
            novel = Novels.query.get(bookId)
        else:
            novel = Cartoon.query.get(bookId)
        if not novel:
            if typee == 1:
                st = '小说'
            else:
                st = '漫画'
            return json.dumps({"retCode": 402, "msg": "%s不存在" % st, "result": {}}, ensure_ascii=False)

        book_collect = BookCollect(userId=user.id, bookId=bookId, read_progress=read_progress, isread=isread, type=typee)
        db.session.add(book_collect)
        db.session.commit()
        return json.dumps({"retCode": 200, "msg": "收藏成功", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 用户批量收藏
@bp.route('/carcollectb')
def carcollectb():
    books = request.args.get('books')
    progress = request.args.get('progress')
    isread = request.args.get('read')
    typees = request.args.get('types')
    token = request.args.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        try:
            bookId_list = books.split(',')
            progress_list = progress.split(',')
            isread_list = isread.split(',')
            typee_list = typees.split(',')
        except:
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        # 判断bookId_list的长度和progress_list长度
        if len(bookId_list) == len(progress_list) == len(isread_list) == len(typee_list):
            book_collect_list = []
            for x in range(len(bookId_list)):
                bookId = bookId_list[x]
                read_progress = progress_list[x]
                if not read_progress or not read_progress.isdigit():
                    read_progress = 0
                if int(read_progress) > 100:
                    read_progress = 100
                if isread_list[x] == '1':
                    isread = 1
                elif isread_list[x] == '0':
                    isread = 0
                else:
                    return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
                if typee_list[x] == '1':
                    typee = 1
                elif typee_list[x] == '2':
                    typee = 2
                else:
                    return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
                # 判断小说是否收藏过了
                is_collect = BookCollect.query.filter_by(userId=user.id, bookId=bookId, type=typee).first()
                if is_collect:
                    # 收藏过了 更新阅读进度和阅读状态
                    is_collect.read_progress = read_progress
                    is_collect.isread = isread
                    book_collect_list.append(is_collect)
                    continue
                if typee == 1:
                    novel = Novels.query.get(bookId)
                else:
                    novel = Cartoon.query.get(bookId)
                if not novel:
                    return json.dumps({"retCode": 402, "msg": "小说不存在", "result": {}}, ensure_ascii=False)
                book_collect = BookCollect(userId=user.id, bookId=bookId, read_progress=read_progress, isread=isread,
                                           type=typee)
                book_collect_list.append(book_collect)
            db.session.add_all(book_collect_list)
            db.session.commit()
            return json.dumps({"retCode": 200, "msg": "收藏成功", "result": {}}, ensure_ascii=False)
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 更新用户漫画的阅读进度
@bp.route('/carupprogress')
def carupprogress():
    # token bookid 验证token
    token = request.args.get('analysis')
    bookId = request.args.get('cartoonId')
    # 阅读进度
    read_progress = request.args.get('progress')
    if not read_progress or not read_progress.isdigit():
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    user = User.query.filter_by(token=token).first()
    if user:
        novel = Cartoon.query.get(bookId)
        if not novel:
            return json.dumps({"retCode": 402, "msg": "漫画不存在", "result": {}}, ensure_ascii=False)
        # 获取到用户收藏的小说
        book_collect = BookCollect.query.filter_by(userId=user.id, bookId=bookId, type=2).first()
        if not book_collect:
            return json.dumps({"retCode": 405, "msg": "收藏不存在", "result": {}}, ensure_ascii=False)
        if int(read_progress) > 100:
            read_progress = 100
        book_collect.read_progress = read_progress
        book_collect.isread = 1
        db.session.add(book_collect)
        db.session.commit()
        return json.dumps({"retCode": 200, "msg": "更新成功", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)


# 获取用户收藏 返回书本 阅读进度 本周阅读分钟数
@bp.route('/cargetcollects')
def cargetcollects():
    host = 'http://%s' % request.host
    # token bookid 验证token
    token = request.args.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        # 根据用户id获取阅读书籍
        book_collect = BookCollect.query.filter_by(userId=user.id).order_by(-BookCollect.addtime).all()
        # 用户本周阅读分钟数
        read_time = user.read_time
        # 根据bookId获取小说详情
        novel_list = []
        for collect in book_collect:
            is_read = collect.isread
            read_progress = collect.read_progress
            if collect.type == 1:
                novel = Novels.query.get(collect.bookId)
                # 根据分类id获取分类
                novel_type = NovelType.query.get(novel.label)
                # 根据作者id获取作者
                authorId = novel.authorId
                author = Author.query.get(authorId)
                author = author.name
                cover = novel.cover
                novel_list.append({
                    "id": novel.id,
                    "name": novel.name,
                    "cover": cover,
                    "author": author,
                    "isread": is_read,
                    "summary": novel.summary,
                    "label": novel_type.type,
                    "countchapter": novel.chaptercount,
                    "read_progress": read_progress,
                    "type": collect.type
                })
            else:
                novel = Cartoon.query.get(collect.bookId)
                if novel:
                    author = novel.author
                    cover = '%s/static/cartoon/%s/%s' % (host, novel.id, novel.cover)
                    novel_list.append({
                        "id": novel.id,
                        "name": novel.name,
                        "cover": cover,
                        "author": author,
                        "isread": is_read,
                        "read_progress": read_progress,
                        "type": collect.type
                    })
        return json.dumps({"retCode": 200, "msg": "success", "result": {"data": novel_list, "read_time": read_time}}, ensure_ascii=False)
    return json.dumps({"retCode": 401, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 用户批量取消收藏
@bp.route('/uncarcollect')
def uncarcollect():
    # token bookid 验证token
    token = request.args.get('analysis')
    bookIds = request.args.get('bookIds')
    types = request.args.get('types')
    try:
        bookId_list = bookIds.split(',')
        type_list = types.split(',')
    except:
        return json.dumps({"retCode": 400, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    user = User.query.filter_by(token=token).first()
    if user:
        if len(type_list) != len(bookId_list):
            return json.dumps({"retCode": 400, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        # 判断用户是否收藏
        for x in range(len(bookId_list)):
            bookId = bookId_list[x]
            typee = type_list[x]
            if typee == '1':
                typee = 1
            elif typee == '2':
                typee = 2
            else:
                return json.dumps({"retCode": 400, "msg": "参数错误", "result": {}}, ensure_ascii=False)
            book_collect = BookCollect.query.filter_by(userId=user.id, bookId=bookId, type=typee).first()
            if book_collect:
                db.session.delete(book_collect)
                db.session.commit()
        return json.dumps({"retCode": 200, "msg": "取消收藏成功", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 400, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 设置用户收藏漫画已读
@bp.route('/carisread')
def carisread():
    token = request.args.get('analysis')
    bookId = request.args.get('cartoonId')
    user = User.query.filter_by(token=token).first()
    if user:
        # 判断用户是否收藏
        collect = BookCollect.query.filter_by(userId=user.id, bookId=bookId, type=2).first()
        if collect:
            # 修改已读状态
            collect.isread = 1
            db.session.commit()
            return json.dumps({"retCode": 200, "msg": "修改成功", "result": {}}, ensure_ascii=False)
        return json.dumps({"retCode": 400, "msg": "收藏不存在", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 400, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 判断这本书 或者漫画是否在书架
@bp.route('/iscollect')
def iscollect():
    token = request.args.get('analysis')
    bookId = request.args.get('bookId')
    typee = request.args.get('type')
    if typee == '1':
        typee = 1
    elif typee == '2':
        typee = 2
    else:
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
    user = User.query.filter_by(token=token).first()
    if user:
        # 判断用户是否收藏
        collect = BookCollect.query.filter_by(userId=user.id, bookId=bookId, type=typee).first()
        if collect:
            return json.dumps({"retCode": 200, "msg": "", "result": 1}, ensure_ascii=False)
        return json.dumps({"retCode": 200, "msg": "", "result": 0}, ensure_ascii=False)
    return json.dumps({"retCode": 400, "msg": "认证失败", "result": {}}, ensure_ascii=False)


# 小说记录用户阅读记录
@bp.route('/reading', methods=['POST'])
def reading():
    token = request.form.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        bookId = request.form.get('novelId')
        if not bookId or not bookId.isdigit():
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        chapterId = request.form.get('chapter')
        if not chapterId or not chapterId.isdigit() or chapterId == '0':
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        place = request.form.get('place')
        if not place or not place.isdigit():
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        # 判断是否更新该用户该书籍
        nr = NovelReadingRecord.query.filter_by(uid=user.id, bookId=bookId).first()
        if nr:
            # 更新
            nr.chapterId = chapterId
            nr.place = place
        else:
            nr = NovelReadingRecord(uid=user.id, bookId=bookId, chapterId=chapterId, place=place)
        db.session.add(nr)
        db.session.commit()
        return json.dumps({"retCode": 200, "msg": "success", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 400, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 小说获取用户当前书籍的阅读记录
@bp.route('/getreading')
def getreading():
    token = request.args.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        bookId = request.args.get('novelId')
        if not bookId or not bookId.isdigit():
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        nr = NovelReadingRecord.query.filter_by(uid=user.id, bookId=bookId).first()
        if not nr:
            # 返回该本书的第一章
            chapter = Chapters.query.filter_by(novelId=bookId).order_by(Chapters.chapterId).first()
            # chapter = Chapters.query.filter_by(novelId=bookId, chapterId=1).first()
            if not chapter:
                return json.dumps({"retCode": 404, "msg": "参数错误2", "result": {}}, ensure_ascii=False)
            content = Contents.query.filter_by(novelId=bookId, chapterId=chapter.id).first()
            if content:
                content_detail = {
                    'title': content.title,
                    "content": content.content,
                    "state": content.state,
                    "created": content.created,
                    "updated": content.updated,
                    "words": content.words,
                    "chapterId": content.chapterId
                }
                return json.dumps({"retCode": 200, "msg": "success", "result": content_detail, "place": 0, "num": 1},
                                  ensure_ascii=False)
            else:
                return json.dumps({"retCode": 404, "msg": "参数错误3", "result": {}}, ensure_ascii=False)

        # 判断用户收藏是否存在
        chapter = Chapters.query.filter_by(novelId=bookId, chapterId=nr.chapterId).first()
        if not chapter:
            return json.dumps({"retCode": 404, "msg": "参数错误4", "result": {}}, ensure_ascii=False)
        content = Contents.query.filter_by(novelId=bookId, chapterId=chapter.id).first()
        if content:
            content_detail = {
                'title': content.title,
                "content": content.content,
                "state": content.state,
                "created": content.created,
                "updated": content.updated,
                "words": content.words,
                "chapterId": content.chapterId
            }
            place = nr.place
            num = nr.chapterId
            return json.dumps({"retCode": 200, "msg": "success", "result": content_detail, "place": place, "num": num},
                              ensure_ascii=False)
        else:
            # 返回该本书的第一章
            chapter = Chapters.query.filter_by(novelId=bookId).order_by(Chapters.chapterId).first()
            if not chapter:
                return json.dumps({"retCode": 404, "msg": "参数错误5", "result": {}}, ensure_ascii=False)
            content = Contents.query.filter_by(novelId=bookId, chapterId=chapter.id).first()
            if content:
                content_detail = {
                    'title': content.title,
                    "content": content.content,
                    "state": content.state,
                    "created": content.created,
                    "updated": content.updated,
                    "words": content.words,
                    "chapterId": content.chapterId
                }
                return json.dumps({"retCode": 200, "msg": "success", "result": content_detail, "place": 0, "num": 1},
                                  ensure_ascii=False)
            else:
                return json.dumps({"retCode": 404, "msg": "参数错误6", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 400, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 漫画记录用户阅读记录
@bp.route('/readingc', methods=['POST'])
def readingc():
    token = request.form.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        bookId = request.form.get('cartoonId')
        if not bookId or not bookId.isdigit():
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        chapterId = request.form.get('chapter')
        if not chapterId or not chapterId.isdigit():
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        place = request.form.get('place')
        if not place or not place.isdigit():
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        # 判断是否更新该用户该书籍
        nr = CartoonReadingRecord.query.filter_by(uid=user.id, cartoonId=bookId).first()
        if nr:
            # 更新
            nr.chapterId = chapterId
            nr.place = place
        else:
            nr = CartoonReadingRecord(uid=user.id, cartoonId=bookId, chapterId=chapterId, place=place)
        db.session.add(nr)
        db.session.commit()
        return json.dumps({"retCode": 200, "msg": "success", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 400, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 漫画获取用户阅读记录
@bp.route('/getreadingc')
def getreadingc():
    host = 'http://%s' % request.host
    token = request.args.get('analysis')
    user = User.query.filter_by(token=token).first()
    if user:
        bookId = request.args.get('cartoonId')
        if not bookId or not bookId.isdigit():
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        nr = CartoonReadingRecord.query.filter_by(uid=user.id, cartoonId=bookId).first()
        if not nr:
            # 返回该本漫画的第一章
            cartoon_chapter = CartoonChapter.query.filter_by(cid=bookId, chapterId=1).first()
            image_list = []
            chapter_name = ''
            if cartoon_chapter:
                base_dir = os.getcwd()
                startnum = cartoon_chapter.startnum
                endnum = cartoon_chapter.endnum
                chapter_name = cartoon_chapter.name
                # {'image': 'http://ljsb.top:5000/static/cartoon/24/1/1.jpg', 'h': 300, 'w':200}
                for x in range(startnum, endnum + 1):
                    img_path = '/static/cartoon/%s/%s/%s.jpg' % (bookId, '1', x)
                    img_dir = '%s%s' % (base_dir, img_path)
                    # 获取图片的宽高
                    # 判断这个文件是否存在
                    if os.path.exists(img_dir):
                        im = Image.open(img_dir)
                        w = im.width  # 图片的宽
                        h = im.height
                        image_list.append({
                            'image': '%s%s' % (host, img_path), 'h': h, 'w': w, 'index': x
                        })
            return json.dumps({"retCode": 200, "msg": "success", "result": image_list, "place": 0, "num": 1,
                                   "chaptername": chapter_name},
                                  ensure_ascii=False)


        # 判断章节是否存在
        cartoon_chapter = CartoonChapter.query.filter_by(cid=bookId, chapterId=nr.chapterId).first()
        if cartoon_chapter:
            image_list = []
            chapter_name = ''
            if cartoon_chapter:
                base_dir = os.getcwd()
                startnum = cartoon_chapter.startnum
                endnum = cartoon_chapter.endnum
                chapter_name = cartoon_chapter.name
                # {'image': 'http://ljsb.top:5000/static/cartoon/24/1/1.jpg', 'h': 300, 'w':200}
                for x in range(startnum, endnum + 1):
                    img_path = '/static/cartoon/%s/%s/%s.jpg' % (bookId, '1', x)
                    img_dir = '%s%s' % (base_dir, img_path)
                    # 获取图片的宽高
                    # 判断这个文件是否存在
                    if os.path.exists(img_dir):
                        im = Image.open(img_dir)
                        w = im.width  # 图片的宽
                        h = im.height
                        image_list.append({
                            'image': '%s%s' % (host, img_path), 'h': h, 'w': w, 'index': x
                        })
            return json.dumps({"retCode": 200, "msg": "success", "result": image_list, "place": nr.place, "num": nr.chapterId,
                               "chaptername": chapter_name},
                              ensure_ascii=False)
        else:
            # 返回该本漫画的第一章
            cartoon_chapter = CartoonChapter.query.filter_by(cid=bookId, chapterId=1).first()
            image_list = []
            chapter_name = ''
            if cartoon_chapter:
                base_dir = os.getcwd()
                startnum = cartoon_chapter.startnum
                endnum = cartoon_chapter.endnum
                chapter_name = cartoon_chapter.name
                # {'image': 'http://ljsb.top:5000/static/cartoon/24/1/1.jpg', 'h': 300, 'w':200}
                for x in range(startnum, endnum + 1):
                    img_path = '/static/cartoon/%s/%s/%s.jpg' % (bookId, '1', x)
                    img_dir = '%s%s' % (base_dir, img_path)
                    # 获取图片的宽高
                    # 判断这个文件是否存在
                    if os.path.exists(img_dir):
                        im = Image.open(img_dir)
                        w = im.width  # 图片的宽
                        h = im.height
                        image_list.append({
                            'image': '%s%s' % (host, img_path), 'h': h, 'w': w, 'index': x
                        })
            return json.dumps({"retCode": 200, "msg": "success", "result": image_list, "place": 0, "num": 1,
                               "chaptername": chapter_name},
                              ensure_ascii=False)
    return json.dumps({"retCode": 400, "msg": "认证失败", "result": {}}, ensure_ascii=False)


# 批量判断评论是否是自己的
@bp.route('/commentis', methods=['POST'])
def commentis():
    token = request.form.get('analysis')
    user = User.query.filter_by(token=token).first()
    type = request.form.get('type')  # 0小说 1漫画
    if user:
        commentIds = request.form.get('commentIds')
        if not commentIds:
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        try:
            commentIds_list = commentIds.split(',')
        except:
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        result = []
        if type == '0':
            for commentId in commentIds_list:
                if commentId and commentId.isdigit():
                    nc = NovelComment.query.filter_by(id=commentId, userId=user.id).first()
                    if nc:
                        result.append(1)
                    else:
                        result.append(0)
        elif type == '1':
            for commentId in commentIds_list:
                if commentId and commentId.isdigit():
                    nc = CartoonComment.query.filter_by(id=commentId, userId=user.id).first()
                    if nc:
                        result.append(1)
                    else:
                        result.append(0)
        else:
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        return json.dumps({"retCode": 200, "msg": "success", "result": {'data': result}}, ensure_ascii=False)
    return json.dumps({"retCode": 400, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 删除评论
@bp.route('/delcomment', methods=['POST'])
def delcomment():
    token = request.form.get('analysis')
    user = User.query.filter_by(token=token).first()
    type = request.form.get('type')  # 0小说 1漫画
    if user:
        commentId = request.form.get('commentId')
        if not commentId:
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        if type == '0':
            if commentId and commentId.isdigit():
                nc = NovelComment.query.filter_by(id=commentId, userId=user.id).first()
                if nc:
                    db.session.delete(nc)
                    db.session.commit()
                else:
                    return json.dumps({"retCode": 400, "msg": "评论不存在", "result": {}}, ensure_ascii=False)
        elif type == '1':
            if commentId and commentId.isdigit():
                nc = CartoonComment.query.filter_by(id=commentId, userId=user.id).first()
                if nc:
                    db.session.delete(nc)
                    db.session.commit()
                else:
                    return json.dumps({"retCode": 400, "msg": "评论不存在", "result": {}}, ensure_ascii=False)
        else:
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        return json.dumps({"retCode": 200, "msg": "success", "result": {}}, ensure_ascii=False)
    return json.dumps({"retCode": 400, "msg": "认证失败", "result": {}}, ensure_ascii=False)

# 举报评论
@bp.route('/reportcom', methods=['POST'])
def reportcom():
    type = request.form.get('type')  # 0小说 1漫画
    if type == '1' or type == '0':
        commentId = request.form.get('commentId')
        cause = request.form.get('cause')
        if not commentId or not commentId.isdigit():
            return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)
        cr = CommentReport(type=type, commentId=commentId, cause=cause)
        db.session.add(cr)
        db.session.commit()
        return json.dumps({"retCode": 200, "msg": "success", "result": {}}, ensure_ascii=False)
    else:
        return json.dumps({"retCode": 404, "msg": "参数错误", "result": {}}, ensure_ascii=False)


# -----------------------------------用户接口-end-------------------------------


# ----------------------------------第三版漫画接口-end--------------------------------------------------
