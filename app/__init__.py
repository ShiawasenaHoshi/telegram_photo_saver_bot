import logging

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    app.logger.setLevel(logging.INFO)
    if not config_class.TESTING and config_class.BOT_ENABLE and config_class.TG_TOKEN and config_class.TG_ADMIN_ID and config_class.YD_TOKEN:
        from app.bot import Bot
        Bot(Config.TG_TOKEN, Config.DOWNLOAD_FOLDER, Config.YD_TOKEN, Config.YD_DOWNLOAD_FOLDER, Config.TG_ADMIN_ID,
            app).start()
    elif config_class.SCANNER_ENABLE and config_class.YD_TOKEN:
        from app.uploader import Uploader
        Uploader(Config.YD_TOKEN, Config.YD_DOWNLOAD_FOLDER, Config.SCANNER_FOLDER, app).start()
    else:
        print("App is not configured. Check config.py")
    return app
