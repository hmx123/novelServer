from wtforms import Form, StringField, IntegerField
from wtforms.validators import InputRequired, EqualTo



class RegisterForm(Form):
    phone = StringField(validators=[InputRequired(message='请输入手机号')])
    password = StringField(validators=[InputRequired(message='请输入密码')])
    code = StringField(validators=[InputRequired(message='请输入验证码')])
    gender = IntegerField(validators=[InputRequired(message='请输入性别')])

class LoginForm(Form):
    password = StringField(validators=[InputRequired(message='请输入密码')])
    username = StringField(validators=[InputRequired(message='请输入用户名')])

class ResetpwdForm(Form):
    analysis = StringField(validators=[InputRequired(message='请输入用户')])
    oldpwd = StringField(validators=[InputRequired(message='请输入旧密码')])
    newpwd = StringField(validators=[InputRequired(message='请输入新密码')])
    newpwd2 = StringField(validators=[EqualTo('newpwd', message='两次密码不一致'), InputRequired(message='请再次输入新密码')])

class ForgetPassword(Form):
    phone = StringField(validators=[InputRequired(message='请输入手机号')])
    code = StringField(validators=[InputRequired(message='请输入验证码')])
    password = StringField(validators=[InputRequired(message='请输入密码')])
    password2 = StringField(validators=[EqualTo('password', message='两次密码不一致'), InputRequired(message='请再次输入新密码')])


