import os

import telebot
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from yadisk import yadisk

from config import Config
from threading import Thread
import re
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    Thread(target=start_echo_bot).start()
    return app


def start_echo_bot():
    # with app.app_context():
        bot = telebot.TeleBot(Config.TG_TOKEN)
        y = yadisk.YaDisk(token=Config.YD_TOKEN)
        @bot.message_handler(content_types=["text"])
        def repeat_all_messages(message):  # Название функции не играет никакой роли, в принципе
            bot.send_message(message.chat.id, message.text)

        @bot.message_handler(content_types=["document"])
        # @bot.message_handler(func=lambda message: message.document and message.text.lower())
        def it_is_image(message):
            if re.search('^.+/(jpg|jpeg|avi|mov|mp4)$', message.document.mime_type).group(0):
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                local_path = Config.DOWNLOAD_FOLDER + "/" + message.document.file_id + "_" + message.document.file_name
                yd_path = Config.YD_DOWNLOAD_FOLDER + "/" + message.document.file_id + "_" + message.document.file_name
                with open(local_path, 'w+b') as new_file:
                    new_file.write(downloaded_file)
                if not y.exists(yd_path):
                    with open(local_path, "rb") as f:
                        y.upload(f, yd_path)
                os.remove(local_path)

        bot.polling(none_stop=True)
