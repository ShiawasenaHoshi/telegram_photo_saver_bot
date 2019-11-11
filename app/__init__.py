import logging

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app.bot import Bot
from config import Config

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    app.logger.setLevel(logging.INFO)
    Bot(Config.TG_TOKEN, Config.DOWNLOAD_FOLDER, Config.YD_TOKEN, Config.YD_DOWNLOAD_FOLDER, Config.TG_ADMIN_ID,
            app).start()
    return app
