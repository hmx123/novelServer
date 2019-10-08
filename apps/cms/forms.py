from wtforms import Form, StringField, IntegerField, BooleanField
from wtforms.validators import InputRequired

class LoginForm(Form):
    password = StringField(validators=[InputRequired(message='请输入密码')])
    username = StringField(validators=[InputRequired(message='请输入用户名')])
    remember = BooleanField()


class TypeSpiderForm(Form):
    typeId = IntegerField(validators=[InputRequired(message='typeId')])
    page = IntegerField(validators=[InputRequired(message='page')])
    limit = IntegerField(validators=[InputRequired(message='limit')])

class BqgSpiderForm(Form):
    typeId = IntegerField(validators=[InputRequired(message='typeId')])
    page = IntegerField(validators=[InputRequired(message='page')])
