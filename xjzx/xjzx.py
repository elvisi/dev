from flask_script import Manager

from app import create_app
from config import DevelopConfig
app=create_app(DevelopConfig)

manager=Manager(app)

from models import db
db.init_app(app)

from flask_migrate import Migrate,MigrateCommand
Migrate(app,db)
manager.add_command('db',MigrateCommand)

#添加管理员的命令
from super_command import CreateAdminCommand,RegisterUserCommand,LoginCountCommand
manager.add_command('admin',CreateAdminCommand())
manager.add_command('register',RegisterUserCommand())
manager.add_command('login',LoginCountCommand())

if __name__ == '__main__':
    # print(app.url_map)
    manager.run()
