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
    WEBHOOK_ENABLE = os.environ.get('WEBHOOK_ENABLE') or True
    WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST')
    WEBHOOK_PORT = os.environ.get('WEBHOOK_PORT') or 8443  # 443, 80, 88 or 8443 (port need to be 'open')
    WEBHOOK_LISTEN = os.environ.get('WEBHOOK_LISTEN') or '0.0.0.0'  # In some VPS you may need to put here the IP addr

    WEBHOOK_SSL_CERT = os.environ.get(
        'WEBHOOK_SSL_CERT') or basedir + '/webhook_cert.pem'  # Path to the ssl certificate
    WEBHOOK_SSL_PRIV = os.environ.get(
        'WEBHOOK_SSL_PRIV') or basedir + '/webhook_pkey.pem'  # Path to the ssl private key

    WEBHOOK_URL_BASE = os.environ.get('WEBHOOK_URL_BASE') or "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
    WEBHOOK_URL_PATH = os.environ.get('WEBHOOK_URL_PATH') or "/%s/" % (TG_TOKEN)
