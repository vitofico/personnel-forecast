import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['your-email@example.com']
    LANGUAGES = ['en', 'es', 'it']
    MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY')
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    POSTS_PER_PAGE = 25
    DOWNLOAD_FOLDER = 'static'
    UPLOAD_FOLDER = 'static'
    MAX_CONTENT_PATH = 2 * 1024 * 1024
    if os.environ.get("REDMINE_CONTAINER") is not None:
        REDMINE_URL = f'http://{os.environ.get("REDMINE_CONTAINER")}/'
    else:
        REDMINE_URL = 'https://redmine.skylife-eng.net'
    AVG_MONTHLY_HOURS = os.environ.get ('AVG_MONTHLY_HOURS') or 140
    LDAP_BASE_DN = os.environ.get('LDAP_BASE_DN') or 'dc=skylife-eng,dc=net'
    LDAP_USERNAME = os.environ.get('LDAP_USERNAME') or 'cn=ftpadmin,ou=meta,dc=skylife-eng,dc=net'
    LDAP_PASSWORD = os.environ.get('LDAP_PASSWORD') or 'ldap'
    LDAP_HOST = os.environ.get('LDAP_HOST') or '192.168.0.15'
    LDAP_USER_OBJECT_FILTER = '(uid=%s)'
    LDAP_OPENLDAP = True
    FLASK_ADMIN_SWATCH = 'cerulean'
    ADMIN_PASS = os.environ.get('ADMIN_PASS') or 'nostradamus'
