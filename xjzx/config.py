class Config(object):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql9527@localhost:3306/xjzx10'
    SQLALCHEMY_TRACK_MODIFICATIONS = True


class DevelopConfig(Config):
    DEBUG = True
