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

class NovelType(db.Model):
    __tablename__ = 'novel_type'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(64))
    cover = db.Column(db.String(255), comment='分类封面')
    addtime = db.Column(db.DateTime)
    gender = db.Column(db.Integer, comment='1男频 0女频')

class NovelTag(db.Model):
    __tablename__ = 'novel_tag'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    target = db.Column(db.String(32))
    addtime = db.Column(db.DateTime)

class NovelGroup(db.Model):
    __tablename__ = 'novel_group'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group = db.Column(db.String(255))
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
    monthly = db.Column(db.String(64), comment='榜单')
    addtime = db.Column(db.DateTime)

class MonthlyNovel(db.Model):
    __tablename__ = 'monthly_novel'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    novelId = db.Column(db.Integer, comment='小说id')
    monthlyId = db.Column(db.Integer, comment='榜单id')


