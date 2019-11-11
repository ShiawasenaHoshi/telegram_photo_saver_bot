import datetime
import os
import re
import threading

import telebot
from exif import Image
from telebot.apihelper import ApiException
from yadisk import yadisk


class Bot(threading.Thread):
    def __init__(self, tg_token, download_folder, yd_token, yd_download_folder, admin_id, app):
        super().__init__()
        self.tg_token = tg_token
        self.yd_token = yd_token

        self.download_f = download_folder
        self.yd_download_f = yd_download_folder
        self.app = app
        self.admin = admin_id

    def run(self):
        app = self.app
        self.l = app.logger
        self.l.info("Bot started")
        self.y = yadisk.YaDisk(token=self.yd_token)
        self.b = telebot.TeleBot(self.tg_token)
        bot = self.b
        from app import db
        from app.models import Chat, Photo
        self.get_upload_folder("")

        @bot.message_handler(commands=['start', 'help'], func=lambda
                message: message.chat.title is not None and message.from_user.id == int(self.admin))
        def send_welcome(message):
            bot.reply_to(message,
                         "Привет! Я бот для скачивания фоток в яндекс. Не пытайтесь кидать фотки не файлами - я их удалю. Не меняйте название чата. Не удаляйте фотки в чате напрямую - скидывайте мне и я удалю их сам. Чтобы получить инструкцию о правильной заливке фото напишите мне в ЛС: /help")

        @bot.message_handler(commands=['direct_link'], func=lambda
                message: message.chat.title is not None and message.from_user.id == int(self.admin))
        def get_direct_link(message):
            yd_path = self.yd_download_f + "/" + message.chat.title
            link = self.y.get_download_link(yd_path)
            bot.send_message(message.chat.id, "Архив с фотками: " + link)

        @bot.message_handler(commands=['link'], func=lambda
                message: message.chat.title is not None and message.from_user.id == int(self.admin))
        def get_public_link(message):
            yd_path = self.yd_download_f + "/" + message.chat.title
            self.y.publish(path=yd_path, fields=["public_url"])
            link = self.y.get_meta(yd_path).public_url
            bot.send_message(message.chat.id, "Фотки здесь: " + link)

        @bot.message_handler(content_types=["group_chat_created", "migrate_to_chat_id", "migrate_from_chat_id"])
        def group_chat_created(message):
            pass

        @bot.message_handler(content_types=["photo"], func=lambda
                message: message.chat.title is not None and message.from_user.id != int(self.admin))
        def delete_compressed_image(message):
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, "Фотографии можно отправлять только файлом")

        @bot.message_handler(func=lambda message: message.chat.title and Bot.is_extension_ok(message),
                             content_types=['document'])
        def save_file(message):
            try:
                file_info = bot.get_file(message.document.file_id)
                self.l.info(
                    '{0} {1} {2} downloading'.format(message.message_id, message.document.file_id,
                                                     message.document.file_name))
                chat_name = message.chat.title
                if chat_name:
                    downloaded_file = bot.download_file(file_info.file_path)
                    local_path = self.download_f + "/" + message.document.file_id + "_" + message.document.file_name
                    with open(local_path, 'w+b') as new_file:
                        new_file.write(downloaded_file)
                    with open(local_path, 'rb') as image_file:
                        img = Image(image_file)
                        if img.has_exif:
                            dt_str = img.datetime
                            dt = datetime.datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
                            yd_path = self.get_upload_folder(chat_name, dt) + "/" + self.get_yd_name(message, dt)
                        else:
                            yd_path = self.get_upload_folder(chat_name,
                                                             "no_exif") + "/" + message.document.file_id + "_" + message.document.file_name
                    with open(local_path, "rb") as f:
                        with app.app_context():
                            if not Chat.is_exists(message.chat.id):
                                try:
                                    Chat.save_to_db(message.chat.id, message.chat.title)
                                except BaseException as e:
                                    self.l.error('{0}'.format(e))
                            if not self.y.exists(yd_path):
                                self.y.upload(f, yd_path)
                                self.l.info("YD uploaded {0} into {1}".format(message.document.file_name, yd_path))
                                if not Photo.is_exists(message.chat.id, local_path):
                                    Photo.save_to_db(local_path, message, yd_path)
                                    self.l.info("DB added: " + yd_path)
                            else:
                                bot.delete_message(message.chat.id, message.message_id)
                                text = "ДУБЛИКАТ. {0} уже есть в {1}".format(message.document.file_name, yd_path)
                                bot.send_message(message.chat.id, text)
                    os.remove(local_path)
            except ApiException as ae:
                self.l.error('{0}'.format(ae))
                if "file is too big" in ae.args[0]:
                    bot.reply_to(message, "Файл слишком большой. Залейте вручную")
            except BaseException as e:
                self.l.error('{0}'.format(e))
                bot.reply_to(message, "Файл не скачался. Повторите")

        @bot.message_handler(func=lambda message: message.chat.title is None and Bot.is_extension_ok(message),
                             content_types=['document'])
        def delete_file(message):
            with app.app_context():
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                local_path = self.download_f + "/" + message.document.file_id + "_" + message.document.file_name
                with open(local_path, 'w+b') as new_file:
                    new_file.write(downloaded_file)
                photo = Photo.get_duplicate(message.from_user.id, datetime.datetime.fromtimestamp(message.forward_date),
                                            local_path)
                if photo is None:
                    bot.send_message(message.chat.id, "Нет такого фото")
                else:
                    bot.delete_message(photo.chat_id, photo.msg_id)
                    text = "Фото удалено из чата: " + Chat.get_chat(photo.chat_id).name
                    bot.reply_to(message, text=text)
                    yd_path = photo.yd_path
                    self.y.remove(yd_path)
                    db.session.delete(photo)
                    db.session.commit()
                    self.l.info("File deleted from {0}".format(yd_path))

        self.b.polling(none_stop=True)

    def get_upload_folder(self, chat_name, folder_date=None):
        if folder_date is None:
            path = self.yd_download_f + "/" + chat_name
        else:
            if isinstance(folder_date, datetime.datetime):
                name = folder_date.strftime('%Y_%m_%d')
                path = self.get_upload_folder(chat_name) + "/" + name
            else:
                name = str(folder_date)
                path = self.get_upload_folder(chat_name) + "/" + name
        if not self.y.exists(path):
            try:
                self.y.mkdir(path)
            except BaseException as e:
                self.l.error('{0}'.format(e))
        return path

    @staticmethod
    def get_yd_name(message, dt):
        return dt.strftime('%H_%M_%S') + "_" + message.document.file_name

    @staticmethod
    def is_extension_ok(message):
        if message.document is None:
            return False
        return re.search('^.+/(jpg|jpeg|avi|mov|mp4)$', message.document.mime_type).group(0) is not None