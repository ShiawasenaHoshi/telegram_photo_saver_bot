import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    TG_TOKEN = os.environ.get('TG_TOKEN')
    TG_ADMIN_ID = os.environ.get('TG_ADMIN_ID')
    DOWNLOAD_FOLDER = os.environ.get('DOWNLOAD_FOLDER') or os.path.join(basedir, 'download')
    YD_TOKEN = os.environ.get('YD_TOKEN')
    YD_DOWNLOAD_FOLDER = os.environ.get('YD_DOWNLOAD_FOLDER') or "/tg_photo_saver"
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = False
    WEBHOOK_ENABLE = True
    WEBHOOK_HOST = '196.196.203.76'
    WEBHOOK_PORT = 8443  # 443, 80, 88 or 8443 (port need to be 'open')
    WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr

    WEBHOOK_SSL_CERT = basedir + '/webhook_cert.pem'  # Path to the ssl certificate
    WEBHOOK_SSL_PRIV = basedir + '/webhook_pkey.pem'  # Path to the ssl private key

    WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
    WEBHOOK_URL_PATH = "/%s/" % (TG_TOKEN)