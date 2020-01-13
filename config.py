import os

from apps.common.decorators import xbqg_1h_data, qb5_1h_data, ever_week_monday, cartoon_spider
base_dir = os.path.dirname(__file__)
DEBUG = True

MySQLUser = os.environ.get('MySQLUser')
MySQLPassword = os.environ.get('MySQLPassword')
WECHAT_APPID = os.environ.get('WECHAT_APPID')
WECHAT_SECRET = os.environ.get('WECHAT_SECRET')

DB_URI = "mysql+pymysql://%s:%s@127.0.0.1:3306/novels?charset=utf8mb4" % (MySQLUser, MySQLPassword)
SQLALCHEMY_DATABASE_URI = DB_URI
SQLALCHEMY_TRACK_MODIFICATIONS =False

CMS_USER_ID = 'abcdefgh'
SECRET_KEY = 'qwertyuiopasdfghjkl'

REDIS_URL = "redis://:@localhost:6379/0"

SQLALCHEMY_COMMIT_ON_TEARDOWN = True
# 文件上传
MAX_CONTENT_LENGTH = 3 * 1024 * 1024
UPLOADED_PHOTOS_DEST = os.path.join(base_dir, 'static/images/icon')

# 定时任务

SCHEDULER_API_ENABLED = True
JOBS = [
        {
            'id': 'xbqg_1h_data',
            'func': xbqg_1h_data,
            'args': '',
            'trigger': 'interval',
            'hours': 1
        },
        {
            'id': 'qb5_1h_data',
            'func': qb5_1h_data,
            'args': '',
            'trigger': 'interval',
            'hours': 1
        },
        {
            'id': 'ever_week_monday',
            'func': ever_week_monday,
            'args': '',
            'trigger': 'cron',
            'day_of_week': 0,
            'hour': 0,
            'minute': 0,
            'second': 0
        },
        {
            'id': 'cartoon_spider',
            'func': cartoon_spider,
            'args': '',
            'trigger': 'cron',
            'hour': 10,
            'minute': 0,
            'second': 0
        }
]

