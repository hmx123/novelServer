import os

from apps.common.decorators import xbqg_1h_data, qb5_1h_data
base_dir = os.path.dirname(__file__)
DEBUG = True

MySQLUser = os.environ.get('MySQLUser')
MySQLPassword = os.environ.get('MySQLPassword')
WECHAT_APPID = os.environ.get('WECHAT_APPID')
WECHAT_SECRET = os.environ.get('WECHAT_SECRET')

DB_URI = "mysql+pymysql://%s:%s@127.0.0.1:3306/novels?charset=utf8" % (MySQLUser, MySQLPassword)
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
#
# SCHEDULER_API_ENABLED = True
#
#
# JOBS = [
#         {
#             'id': 'xbqg_1h_data',
#             'func': xbqg_1h_data,
#             'args': '',
#             'trigger': 'interval',
#             'hours': 1
#         },
#         {
#             'id': 'qb5_1h_data',
#             'func': qb5_1h_data,
#             'args': '',
#             'trigger': 'interval',
#             'hours': 1
#         }
# ]

