from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler

db = SQLAlchemy()
redis_store = FlaskRedis()
scheduler = APScheduler()
