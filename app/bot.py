import datetime
import os
import re
import threading

import telebot
from telebot.apihelper import ApiException
from yadisk import yadisk

from app.generic import create_yd_folder_if_not_exist
from app.models import ChatOption


class Bot(threading.Thread):

    def __init__(self, tg_token, download_folder, yd_token, yd_download_folder, admin_id, app):
        super().__init__()
        self.tg_token = tg_token
        self.yd_token = yd_token

        self.download_f = download_folder
        self.yd_download_f = yd_download_folder
        self.app = app
        self.admin = admin_id

    @staticmethod
    def get_yd_name(message, dt):
        return dt.strftime('%H_%M_%S') + "_" + message.document.file_name

    def run(self):
        app = self.app
        self.l = app.logger
        self.l.info("Bot started")
        self.y = yadisk.YaDisk(token=self.yd_token)
        self.b = telebot.TeleBot(self.tg_token)
        self.photo_warn_last_time = 0
        self.photo_warn_timeout = 60
        bot = self.b
        from app import db
        from app.models import Chat, Photo
        create_yd_folder_if_not_exist(self.yd_download_f, self.y)

        # self.get_upload_folder("") #todo remove

        def check_chat_option(message, name, value=None):
            with app.app_context():
                if value:
                    return ChatOption.get_val(message.chat.id, name) == value
                else:
                    return ChatOption.get_val(message.chat.id, name) == "1"

        def write_chat_option(message, name, value):
            with app.app_context():
                ChatOption.set_val(message.chat.id, name, value)

        def is_extension_ok(message):
            if message.document is None:
                return False
            with app.app_context():
                return re.match(ChatOption.get_val(message.chat.id, "doc_mime_filter"), message.document.mime_type)

        @bot.message_handler(commands=['init'], func=lambda
                message: message.chat.title is not None and message.from_user.id == int(self.admin))
        def init_chat(message):
            with app.app_context():
                if not is_initialized(message):
                    if not Chat.is_exists(message.chat.id):
                        try:
                            ch = Chat.save_to_db(message.chat.id, message.chat.title)
                        except BaseException as e:
                            self.l.error('{0}'.format(e))
                    ch.get_yd_folder(self.y)

        def is_initialized(message):
            with app.app_context():
                return Chat.is_exists(message.chat.id)

        @bot.message_handler(commands=['start'], func=lambda
                message: message.chat.title is not None and message.from_user.id == int(self.admin))
        def send_welcome(message):
            if not is_initialized(message):
                init_chat(message)
                bot.send_message(message.chat.id,
                                 "Привет! Я бот для скачивания фоток в яндекс. Не пытайтесь кидать фотки не файлами - я их удалю. Не меняйте название чата. Не удаляйте фотки в чате напрямую - скидывайте мне и я удалю их сам. Чтобы получить инструкцию о правильной заливке фото напишите мне в ЛС: /help")

        @bot.message_handler(commands=['direct_link'], func=lambda
                message: is_initialized(message) and message.chat.title is not None and message.from_user.id == int(
            self.admin))
        def get_direct_link(message):
            yd_path = self.yd_download_f + "/" + message.chat.title
            link = self.y.get_download_link(yd_path)
            bot.send_message(message.chat.id, "Архив с фотками: " + link)

        @bot.message_handler(commands=['link'], func=lambda
                message: is_initialized(message) and message.chat.title is not None and message.from_user.id == int(
            self.admin))
        def get_public_link(message):
            yd_path = self.yd_download_f + "/" + message.chat.title
            self.y.publish(path=yd_path, fields=["public_url"])
            link = self.y.get_meta(yd_path).public_url
            bot.send_message(message.chat.id, "Фотки здесь: " + link)

        @bot.message_handler(commands=['photo_toggle'], func=lambda
                message: is_initialized(message) and message.chat.title is not None and message.from_user.id == int(
            self.admin))
        def compressed_toggle(message):
            if check_chat_option(message, "photo_allowed"):
                write_chat_option(message, "photo_allowed", "0")
                bot.send_message(message.chat.id, "Сжатые фото запрещены")
            else:
                write_chat_option(message, "photo_allowed", "1")
                bot.send_message(message.chat.id, "Сжатые фото разрешены")

        @bot.message_handler(commands=['space'], func=lambda
                message: message.from_user.id == int(self.admin) and message.chat.title is None)
        def yd_ls(message):
            info_obj = self.y.get_disk_info()
            text = "Доступно {0:.3f} ГБ".format((info_obj.total_space - info_obj.used_space) / (1024 * 1024 * 1024))
            bot.send_message(message.chat.id, text)

        @bot.message_handler(content_types=["group_chat_created", "migrate_to_chat_id", "migrate_from_chat_id"])
        def group_chat_created(message):
            if not is_initialized(message) and message.from_user.id == int(self.admin):
                send_welcome(message)

        @bot.message_handler(content_types=["photo"],
                             func=lambda message: is_initialized(message) and message.chat.title is not None)
        def delete_compressed_image(message):
            save_file(message, True)
            if not check_chat_option(message, "photo_allowed"):
                bot.delete_message(message.chat.id, message.message_id)
                timestamp = datetime.datetime.now().timestamp()
                if self.photo_warn_timeout + self.photo_warn_last_time <= timestamp:
                    text = "@{0} фотографии можно отправлять только файлом".format(message.from_user.username)
                    bot.send_message(message.chat.id, text)
                    self.photo_warn_last_time = timestamp

        @bot.message_handler(
            func=lambda message: is_initialized(message) and message.chat.title and is_extension_ok(message),
            content_types=['document'])
        def save_file(message, allow_compressed=False):
            with app.app_context():
                try:
                    if allow_compressed:
                        file_info = bot.get_file(message.photo[1].file_id)
                    else:
                        file_info = bot.get_file(message.document.file_id)
                    if message.document.file_name:
                        file_name = message.document.file_name
                    else:
                        file_name = file_info.file_path.replace("/", "_")
                    file_id = file_info.file_id
                    self.l.info(
                        '{0} {1} {2} downloading'.format(message.message_id, file_id, file_name))
                    chat_name = message.chat.title
                    if chat_name:
                        downloaded_file = bot.download_file(file_info.file_path)
                        local_path = self.download_f + "/" + file_id + "_" + file_name
                        with open(local_path, 'w+b') as new_file:
                            new_file.write(downloaded_file)
                        photo = Photo(message, local_path, file_name, file_id, allow_compressed)
                        yd_path = photo.get_yd_path(self.y)
                        with open(local_path, "rb") as f:

                            if not Chat.is_exists(message.chat.id):
                                try:
                                    Chat.save_to_db(message.chat.id, message.chat.title)
                                except BaseException as e:
                                    self.l.error('{0}'.format(e))
                            if not self.y.exists(yd_path):
                                self.y.upload(f, yd_path)
                                self.l.info("YD uploaded {0} into {1}".format(file_name, yd_path))
                                if not Photo.is_exists(message.chat.id, local_path):
                                    db.session.add(photo)
                                    db.session.commit()
                                    self.l.info("DB added: " + yd_path)
                            elif allow_compressed:
                                pass
                            else:
                                bot.delete_message(message.chat.id, message.message_id)
                                text = "ДУБЛИКАТ. {0} уже есть в {1}".format(file_name, yd_path)
                                bot.send_message(message.chat.id, text)
                        os.remove(local_path)
                except ApiException as ae:
                    self.l.error('{0}'.format(ae))
                    if "file is too big" in ae.args[0]:
                        bot.reply_to(message, "Файл слишком большой. Залейте вручную")
                except BaseException as e:
                    self.l.error('{0}'.format(e))
                    if not allow_compressed:
                        bot.reply_to(message, "Файл не скачался. Повторите")

        @bot.message_handler(
            func=lambda message: message.chat.title is None, content_types=['document'])
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
                    yd_path = photo.get_yd_path()
                    self.y.remove(yd_path)
                    db.session.delete(photo)
                    db.session.commit()
                    self.l.info("File deleted from {0}".format(yd_path))

        self.b.polling(none_stop=True)
