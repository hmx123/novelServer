import os

DEBUG = True

DB_URI = "mysql+pymysql://root:root@127.0.0.1:3306/novels?charset=utf8"
SQLALCHEMY_DATABASE_URI = DB_URI
SQLALCHEMY_TRACK_MODIFICATIONS =False

CMS_USER_ID = 'abcdefgh'
SECRET_KEY = os.urandom(24)

REDIS_URL = "redis://:@localhost:6379/0"

SQLALCHEMY_COMMIT_ON_TEARDOWN = True
SQLALCHEMY_TRACK_MODIFICATIONS = False

