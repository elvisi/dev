from flask import Flask
from views_admin import admin_blueprint
from views_news import new_blueprint
from views_user import user_blueprint


def create_app(config):
    app = Flask(__name__)

    app.config.from_object(config)

    app.register_blueprint(admin_blueprint)
    app.register_blueprint(new_blueprint)
    app.register_blueprint(user_blueprint)



    return app
