from flask import current_app
from flask_script.commands import Command
from models import db,UserInfo
from datetime import datetime
import random
class CreateAdminCommand(Command):
    def run(self):
        '''
        创建管理员：账号，密码
        '''
        mobile=input('请输入账号：')
        pwd=input('请输入密码：')
        #验证：账号是否存在
        user_exists=UserInfo.query.filter_by(mobile=mobile).count()
        if user_exists>0:
            print('此账号已经存在')
            return
        #创建用户对象
        user=UserInfo()
        user.mobile=mobile
        user.password=pwd
        user.isAdmin=True
        #保存到数据库
        db.session.add(user)
        db.session.commit()
        print('管理员创建成功')

class RegisterUserCommand(Command):
    def run(self):
        user_list=[]
        now=datetime.now()
        for i in range(1000):
            user=UserInfo()
            user.mobile=str(i)
            # user.password=str(i)
            user.create_time=datetime(2018,random.randint(1,6),random.randint(1,28))
            user.update_time=datetime(2018,random.randint(1,6),random.randint(1,28))
            user_list.append(user)
        db.session.add_all(user_list)
        db.session.commit()

class LoginCountCommand(Command):
    def run(self):
        time_list = ["08:15", "09:15", "10:15", "11:15", "12:15", "13:15", "14:15", "15:15", "16:15", "17:15", "18:15", "19:15"]
        login_key='login2018_6_4'
        redis_client=current_app.redis_client
        for time in time_list:
            redis_client.hset(login_key,time,random.randint(100,500))



