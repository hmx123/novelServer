from werkzeug.security import generate_password_hash, check_password_hash

from exts import db
from datetime import datetime

class Novels(db.Model):
    __tablename__ = 'novels'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), comment='小说名字')
    cover = db.Column(db.String(255), comment='小说封面')
    summary = db.Column(db.Text, comment='小说简介')
    label = db.Column(db.Integer, comment='小说类别')
    state = db.Column(db.Integer, comment='小说状态:连载/完本')
    enabled = db.Column(db.Integer, comment='开关版权相关原因下架即:小说是否可读 Boolean')
    words = db.Column(db.Integer, comment='小说字数')
    created = db.Column(db.Integer, comment='小说开始时间: 时间戳')
    updated = db.Column(db.Integer, comment='小说更新时间: 时间戳')
    authorId = db.Column(db.Integer, comment='作者ID')
    extras = db.Column(db.String(255), comment='其他')
    group = db.Column(db.Integer, comment='小说分组')
    target = db.Column(db.String(32), comment='小说标签')
    score = db.Column(db.Float, comment='小说评分')
    bookId = db.Column(db.Integer)
    addtime = db.Column(db.DATETIME, default=datetime.now)
    novel_web = db.Column(db.Integer, comment='小说采集网站id')
    updatetime = db.Column(db.DATETIME, comment='小说更新时间')
    chaptercount = db.Column(db.Integer, comment='小说章节总数')

class NovelType(db.Model):
    __tablename__ = 'novel_type'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(64))
    cover = db.Column(db.String(255), comment='分类封面')
    addtime = db.Column(db.DateTime)
    gender = db.Column(db.Integer, comment='1男频 0女频')
    type_count = db.Column(db.Integer)
    version = db.Column(db.Integer)

class NovelTag(db.Model):
    __tablename__ = 'novel_tag'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    target = db.Column(db.String(32))
    addtime = db.Column(db.DateTime)

class MiddleTagNov(db.Model):
    __tablename__ = 'middle_tag_nov'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tagId = db.Column(db.Integer)
    novelId = db.Column(db.Integer)

class Contents(db.Model):
    __tablename__ = 'contents'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), comment='正文标题')
    number = db.Column(db.Integer, comment='正文对应章节数字')
    content = db.Column(db.Text, comment='正文内容')
    state = db.Column(db.Integer, comment='当前章节是否需要付费/或版权问题')
    created = db.Column(db.Integer, comment='创建时间: 时间戳')
    updated = db.Column(db.Integer, comment='更新时间: 时间戳')
    words = db.Column(db.Integer, comment='正文字数')
    chapterId = db.Column(db.Integer, comment='对应的章节id')
    novelId = db.Column(db.Integer, comment='对应的小说id')

class Chapters(db.Model):
    __tablename = 'chapters'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), comment='章节标题')
    number = db.Column(db.Integer, comment='第几章数字')
    state = db.Column(db.Integer, comment='当前章节是否需要付费/或版权问题')
    created = db.Column(db.Integer, comment='创建时间: 时间戳')
    updated = db.Column(db.Integer, comment='更新时间: 时间戳')
    words = db.Column(db.Integer, comment='章节字数')
    novelId = db.Column(db.Integer, comment='小说ID')
    chapterId = db.Column(db.Integer)

class Author(db.Model):
    __tablename__ = 'author'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), comment='作者名称')
    avatar = db.Column(db.String(255), comment='头像')
    summary = db.Column(db.Text, comment='简介')
    addtime = db.Column(db.DateTime)

class Monthly(db.Model):
    __tablename__ = 'monthly'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type_one = db.Column(db.Integer)
    monthly = db.Column(db.String(64), comment='榜单')
    addtime = db.Column(db.DateTime)

class MonthlyNovel(db.Model):
    __tablename__ = 'monthly_novel'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    novelId = db.Column(db.Integer, comment='小说id')
    monthlyId = db.Column(db.Integer, comment='榜单id')

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50))
    _password = db.Column(db.String(100))
    phone = db.Column(db.String(50), nullable=True)
    gender = db.Column(db.Integer)
    token = db.Column(db.String(128))
    join_time = db.Column(db.DATETIME, default=datetime.now)
    read_time = db.Column(db.Integer, default=0)
    icon = db.Column(db.String(128), default='default.png')
    signer = db.Column(db.Text, default='')

    def __init__(self, username, password, phone, token, gender, icon, signer):
        self.username = username
        self.password = password
        self.phone = phone
        self.token = token
        self.gender = gender
        self.icon = icon
        self.signer = signer

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, rew_password):
        self._password = generate_password_hash(rew_password)

    def check_password(self, rew_password):
        result = check_password_hash(self.password, rew_password)
        return result

class BookCollect(db.Model):
    __tablename__ = 'book_collect'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer)
    bookId = db.Column(db.Integer)
    addtime = db.Column(db.DATETIME, default=datetime.now)
    isread = db.Column(db.Integer, default=0)
    read_progress = db.Column(db.Integer, default=0)
    type = db.Column(db.Integer)

class NovelWeb(db.Model):
    __tablename__ = 'novel_web'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128))
    url = db.Column(db.String(255))

# 版本
class AppVersions(db.Model):
    __tablename__ = 'app_versions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    down_url = db.Column(db.String(255))
    version = db.Column(db.String(16))
    equip_type = db.Column(db.Integer)

# 小说banner
class NovelBanner(db.Model):
    __tablename__ = 'novel_banner'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(16))
    imgurl = db.Column(db.String(255))
    rank = db.Column(db.Integer)
    args = db.Column(db.String(128))


# group
class NovelGroup(db.Model):
    __tablename__ = 'novel_group'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group = db.Column(db.String(16))
    type_one = db.Column(db.String(16))
    type_two = db.Column(db.String(16))
    type_three = db.Column(db.String(16))
    addtime = db.Column(db.DATETIME, default=datetime.now)
    remarks = db.Column(db.String(32))

class GroupidNovelid(db.Model):
    __tablename__ = 'groupid_novelid'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    groupId = db.Column(db.Integer)
    novelId = db.Column(db.Integer)

class ComposePage(db.Model):
    __tablename__ = 'compose_page'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    classify = db.Column(db.String(16))
    title = db.Column(db.String(16))
    style = db.Column(db.Integer)
    type = db.Column(db.String(16))
    mode = db.Column(db.Integer)
    head = db.Column(db.String(16))
    girlcount = db.Column(db.Integer)
    boycount = db.Column(db.Integer)
    girlmonthly = db.Column(db.Integer)
    boymonthly = db.Column(db.Integer)
    girllabel = db.Column(db.Integer)
    boylabel = db.Column(db.Integer)

class ComposeStyle(db.Model):
    __tablename__ = 'compose_style'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    style = db.Column(db.Integer)
    remarks = db.Column(db.String(32))

class NovelComment(db.Model):
    __tablename__ = 'novel_comment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    novelId = db.Column(db.Integer)
    userId = db.Column(db.Integer)
    comment = db.Column(db.Text, default='')
    username = db.Column(db.String(32))
    addtime = db.Column(db.DATETIME, default=datetime.now)
    icon = db.Column(db.String(64))
    commentId = db.Column(db.Integer)
    praise = db.Column(db.Integer, default=0)
    star = db.Column(db.Integer, default=5)

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    suggest = db.Column(db.Text)
    addtime = db.Column(db.DATETIME, default=datetime.now)
    phone = db.Column(db.String(64))

class NovelHistory(db.Model):
    __tablename__ = 'novel_history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer)
    novelId = db.Column(db.Integer)
    addtime = db.Column(db.DATETIME, default=datetime.now)
    type = db.Column(db.Integer)

# -------------第三版本新增漫画start-------------
class Cartoon(db.Model):
    __tablename__ = 'cartoon'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64))
    author = db.Column(db.String(16))
    statu = db.Column(db.Integer)
    label = db.Column(db.String(32))
    hotcount = db.Column(db.Integer)
    subcount = db.Column(db.Integer)
    info = db.Column(db.String(255))
    chaptercount = db.Column(db.Integer)
    updatetime = db.Column(db.DATETIME)
    addtime = db.Column(db.DATETIME)
    cover = db.Column(db.String(128))
    webId = db.Column(db.Integer)
    cartoonId = db.Column(db.Integer)

class CartoonChapter(db.Model):
    __tablename__ = 'cartoon_chapter'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cid = db.Column(db.Integer)
    name = db.Column(db.String(32))
    startnum = db.Column(db.Integer)
    endnum = db.Column(db.Integer)
    isbuy = db.Column(db.Integer)
    price = db.Column(db.Integer)
    updatetime = db.Column(db.DATETIME)
    chapterId = db.Column(db.Integer)

class CartoonType(db.Model):
    __tablename__ = 'cartoon_type'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(16))
    version = db.Column(db.Integer)
    img = db.Column(db.String(64))

class CartoonidTypeid(db.Model):
    __tablename__ = 'cartoonid_typeid'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    typeId = db.Column(db.Integer)
    cartoonId = db.Column(db.Integer)

class CartoonMonthly(db.Model):
    __tablename__ = 'cartoon_monthly'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type_one = db.Column(db.Integer)
    monthly = db.Column(db.String(16))
    addtime = db.Column(db.DATETIME)

class CartoonMonthlyNovel(db.Model):
    __tablename__ = 'cartoon_monthly_novel'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cartoonId = db.Column(db.Integer)
    monthlyId = db.Column(db.Integer)
    hotcount = db.Column(db.Integer)

class CartoonComment(db.Model):
    __tablename__ = 'cartoon_comment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    novelId = db.Column(db.Integer)
    userId = db.Column(db.Integer)
    comment = db.Column(db.Text, default='')
    username = db.Column(db.String(32))
    addtime = db.Column(db.DATETIME, default=datetime.now)
    icon = db.Column(db.String(64))
    commentId = db.Column(db.Integer)
    praise = db.Column(db.Integer, default=0)
    star = db.Column(db.Integer, default=5)

class BookcityBanner(db.Model):
    __tablename__ = 'bookcity_banner'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(16))
    imgurl = db.Column(db.String(255))
    rank = db.Column(db.Integer)
    book = db.Column(db.Integer)
    version = db.Column(db.Integer)
# -------------第三版本新增漫画end---------------
