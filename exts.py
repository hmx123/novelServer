from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from flask_uploads import UploadSet, IMAGES

db = SQLAlchemy()
redis_store = FlaskRedis()
scheduler = APScheduler()
photos = UploadSet('photos', IMAGES)
