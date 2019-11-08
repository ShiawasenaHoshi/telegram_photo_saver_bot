import os
import re
from threading import Thread

import telebot
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from yadisk import yadisk

from config import Config

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

    def get_chat_folder(chat_name):
        path = Config.YD_DOWNLOAD_FOLDER + "/" + chat_name
        if not y.exists(path):
            y.mkdir(path)
        return path

    get_chat_folder("")

    @bot.message_handler(content_types=["photo"], func=lambda
            message: message.chat.title is not None and message.from_user.id != Config.TG_ADMIN_ID)
    def delete_compressed_image(message):
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, "Фотографии можно отправлять только файлом")

    @bot.message_handler(func=lambda message: message.chat.title and is_extension_ok(message),
                         content_types=['document'])
    def save_file(message):
        file_info = bot.get_file(message.document.file_id)
        chat_name = message.chat.title
        if chat_name:
            downloaded_file = bot.download_file(file_info.file_path)
            local_path = Config.DOWNLOAD_FOLDER + "/" + message.document.file_id + "_" + message.document.file_name
            yd_path = get_chat_folder(chat_name) + "/" + message.document.file_id + "_" + message.document.file_name
            with open(local_path, 'w+b') as new_file:
                new_file.write(downloaded_file)
            if not y.exists(yd_path):
                with open(local_path, "rb") as f:
                    y.upload(f, yd_path)
            os.remove(local_path)

    @bot.message_handler(func=lambda message: message.chat.title is None and is_extension_ok(message),
                         content_types=['document'])
    def delete_file(message):
        pass

    def is_extension_ok(message):
        return re.search('^.+/(jpg|jpeg|avi|mov|mp4)$', message.document.mime_type).group(0) is not None

    bot.polling(none_stop=True)
