import datetime
import os
import re
from threading import Thread

import telebot
from exif import Image
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

    Thread(target=start_bot, args=(app,)).start()
    return app


def start_bot(app):
    from app.models import Chat, Photo
    with app.app_context():
        bot = telebot.TeleBot(Config.TG_TOKEN)
        y = yadisk.YaDisk(token=Config.YD_TOKEN)

        def get_upload_folder(chat_name, folder_date=None):
            if folder_date is None:
                path = Config.YD_DOWNLOAD_FOLDER + "/" + chat_name
            else:
                if isinstance(folder_date, datetime.datetime):
                    name = folder_date.strftime('%Y_%m_%d')
                    path = get_upload_folder(chat_name) + "/" + name
                else:
                    name = str(folder_date)
                    path = get_upload_folder(chat_name) + "/" + name
            if not y.exists(path):
                y.mkdir(path)
            return path

        get_upload_folder("")

        @bot.message_handler(content_types=["photo"], func=lambda
                message: message.chat.title is not None and message.from_user.id != int(Config.TG_ADMIN_ID))
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
                with open(local_path, 'w+b') as new_file:
                    new_file.write(downloaded_file)
                with open(local_path, 'rb') as image_file:
                    img = Image(image_file)
                    if img.has_exif:
                        dt_str = img.datetime
                        dt = datetime.datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
                        yd_path = get_upload_folder(chat_name, dt) + "/" + get_yd_name(message, dt)
                    else:
                        yd_path = get_upload_folder(chat_name,
                                                    "no_exif") + "/" + message.document.file_id + "_" + message.document.file_name
                with open(local_path, "rb") as f:
                    with app.app_context():
                        if not Chat.is_exists(message.chat.id):
                            Chat.save_to_db(message.chat.id, message.chat.title)
                        if not y.exists(yd_path):
                            y.upload(f, yd_path)
                            if not Photo.is_exists(message.chat.id, local_path):
                                Photo.save_to_db(local_path, message, yd_path)
                os.remove(local_path)

    @bot.message_handler(func=lambda message: message.chat.title is None and is_extension_ok(message),
                         content_types=['document'])
    def delete_file(message):
        with app.app_context():
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            local_path = Config.DOWNLOAD_FOLDER + "/" + message.document.file_id + "_" + message.document.file_name
            with open(local_path, 'w+b') as new_file:
                new_file.write(downloaded_file)
            photo = Photo.get_duplicate(message.from_user.id, datetime.datetime.fromtimestamp(message.forward_date),
                                        local_path)
            if photo is None:
                bot.send_message(message.chat.id, "Нет такого фото")
            else:
                bot.delete_message(photo.chat_id, photo.msg_id)
                text = "Фото удалено из чата: " + Chat.get_chat(photo.chat_id).name
                bot.send_message(chat_id=message.chat.id, text=text)
                y.remove(photo.yd_path)
                db.session.delete(photo)
                db.session.commit()

    def get_yd_name(message, dt):
        return dt.strftime('%H_%M_%S') + "_" + message.document.file_name

    def is_extension_ok(message):
        return re.search('^.+/(jpg|jpeg|avi|mov|mp4)$', message.document.mime_type).group(0) is not None

    bot.polling(none_stop=True)
