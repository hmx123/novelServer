from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from Perfect import create_app
from apps.cms.models import CMSUser
from exts import db

app = create_app()
manager = Manager(app)

Migrate(app, db)   #绑定app跟db
manager.add_command('db', MigrateCommand)

headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36'
    }
@manager.option('-u', '--username', dest='username')
@manager.option('-p', '--password',dest='password')
@manager.option('-e', '--email',dest='email')
def create_cms_user(username, password, email):
    user = CMSUser(username=username, password=password, email=email)
    db.session.add(user)
    db.session.commit()
    print('cms添加用户成功')


if __name__ == '__main__':
    manager.run()
