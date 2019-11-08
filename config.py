import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    TG_TOKEN = os.environ.get('TG_TOKEN')
    TG_ADMIN_ID = int(os.environ.get('TG_ADMIN_ID'))
    DOWNLOAD_FOLDER = os.environ.get('DOWNLOAD_FOLDER') or os.path.join(basedir, 'download')
    YD_TOKEN = os.environ.get('YD_TOKEN')
    YD_DOWNLOAD_FOLDER = os.environ.get('YD_DOWNLOAD_FOLDER') or "/tg_photo_saver"
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False