from flask_script import Manager
from app import create_app
from config import DevelopConfig
from models import db
from flask_migrate import Migrate, MigrateCommand

app = create_app(DevelopConfig)

manager = Manager(app)

db.init_app(app)

Migrate(app, db)
manager.add_command('db', MigrateCommand)

# 添加管理员的命令
from super_command import CreateAdminCommand,RegisterUserCommand
manager.add_command('admin',CreateAdminCommand())
manager.add_command('regt',RegisterUserCommand())

if __name__ == '__main__':
    manager.run()
