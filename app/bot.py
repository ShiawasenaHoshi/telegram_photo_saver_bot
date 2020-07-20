import datetime
import re
import threading
import time

import flask
import telebot
from telebot.apihelper import ApiException
from yadisk import yadisk

from app import db
from app.generic import create_yd_folder_if_not_exist, create_folder_if_not_exists
from app.models import Chat, Photo, ChatOption
from app.uploader import Uploader
from config import Config, basedir


class Bot(threading.Thread):

    def __init__(self, tg_token, download_folder, yd_token, yd_download_folder, admin_id, app):
        super().__init__()
        self.tg_token = tg_token
        self.yd_token = yd_token

        self.download_f = download_folder
        self.yd_download_f = yd_download_folder
        self.app = app
        self.admin = admin_id
        self.l = app.logger
        self.y = yadisk.YaDisk(token=self.yd_token)
        self.bot = telebot.TeleBot(self.tg_token)
        self.photo_warn_last_time = 0
        self.photo_warn_timeout = 60

    def run(self):
        self.l.info("Bot starting")
        create_yd_folder_if_not_exist(self.yd_download_f, self.y)
        create_folder_if_not_exists(self.download_f)
        self.init_commands()
        self.init_bot_options()
        self.use_webhooks(Config.WEBHOOK_ENABLE)

    def use_webhooks(self, value):
        bot = self.bot
        app = self.app
        bot.remove_webhook()
        time.sleep(0.1)
        if value:
            if not Config.WEBHOOK_HOST:
                raise Exception("WEBHOOK_HOST is not defined")

            @app.route('/', methods=['GET', 'HEAD'])
            def index():
                return ''

            @app.route(Config.WEBHOOK_URL_PATH, methods=['POST'])
            def webhook():
                if flask.request.headers.get('content-type') == 'application/json':
                    json_string = flask.request.get_data().decode('utf-8')
                    update = telebot.types.Update.de_json(json_string)
                    bot.process_new_updates([update])
                    self.l.debug("hook: " + json_string)
                    return ''
                else:
                    flask.abort(403)

            bot.set_webhook(url=Config.WEBHOOK_URL_BASE + Config.WEBHOOK_URL_PATH,
                            certificate=open(Config.WEBHOOK_SSL_CERT, 'r'))
        else:
            bot.polling(none_stop=True)
        self.l.info("Webhook enabled: " + str(value))

    def init_bot_options(self):
        with self.app.app_context():
            ch = Chat.get_chat(1)
            if ch is None:
                Chat.save_to_db(1, "BotOptions")

    def init_commands(self):
        bot = self.bot
        app = self.app

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
                help(message)

        @bot.message_handler(commands=['help'], func=lambda
                message: message.chat.title is not None and message.from_user.id == int(self.admin))
        def help(message):
            with app.app_context():
                bot.send_message(message.chat.id,
                                 'Привет! Я фото-бот. Зачем я нужен? Мне всегда очень жаль, когда у Пети одни фотки, у Кати другие, у Стёпы третьи. Уже несколько лет назад было дано обещание обменяться фотками, но до дела так и не дошло. Потому что муторно :-\\'
                                 + '\n\nЯ же соберу все фото из этого чата и залью их на яндекс-диск, чтобы у всех друзей к концу отпуска был одинаковый набор фото. Также я их рассортирую по дате и времени, чтобы можно было посмотреть на моменты отпуска с разного ракурса'
                                 + '\n\nПри этом я хочу чтобы все фото из альбома можно было легко отретушировать и распечатать без потери в четкости, поэтому я их сохраняю в максимальном качестве'
                                 + '\n\nЧто нужно мне, чтобы я смог сделать всё обещанное? Просто отправлять в этом чате все фотки ФАЙЛАМИ. Сейчас покажу как.')

                if ChatOption.get_val(1, "android_how_to_video_id"):
                    bot.send_video(message.chat.id, ChatOption.get_val(1, "android_how_to_video_id"))
                else:
                    f = open(basedir + '/android_how_to.mp4', 'rb')
                    msg = bot.send_document(message.chat.id, f, None)
                    Chat.get_chat(1).add_option("android_how_to_video_id", msg.video.file_id)

                bot.send_message(message.chat.id,
                                 '6 шагов: \n1) скрепка\n2) тянем вверх\n3) галерея\n4) camera\n5) отмечаем фото\n6) без сжатия')

        @bot.message_handler(commands=['direct_link'], func=lambda
                message: is_initialized(message) and message.chat.title is not None and message.from_user.id == int(
            self.admin))
        def get_direct_link(message):
            yd_path = self.yd_download_f + "/" + message.chat.title
            link = self.y.get_download_link(yd_path)
            bot.send_message(message.chat.id, "Архив с фотками: " + link)
            bot.delete_message(message.chat.id, message.message_id)

        @bot.message_handler(commands=['link'], func=lambda
                message: is_initialized(message) and message.chat.title is not None and message.from_user.id == int(
            self.admin))
        def get_public_link(message):
            yd_path = self.yd_download_f + "/" + message.chat.title
            self.y.publish(path=yd_path, fields=["public_url"])
            link = self.y.get_meta(yd_path).public_url
            bot.send_message(message.chat.id, "Фотки здесь: " + link)
            bot.delete_message(message.chat.id, message.message_id)

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
            bot.delete_message(message.chat.id, message.message_id)

        @bot.message_handler(commands=['space'], func=lambda
                message: message.from_user.id == int(self.admin) and message.chat.title is None)
        def yd_ls(message):
            info_obj = self.y.get_disk_info()
            text = "Доступно {0:.3f} ГБ".format((info_obj.total_space - info_obj.used_space) / (1024 * 1024 * 1024))
            bot.send_message(message.chat.id, text)
            bot.delete_message(message.chat.id, message.message_id)

        @bot.message_handler(content_types=["group_chat_created", "migrate_to_chat_id", "migrate_from_chat_id"])
        def group_chat_created(message):
            if not is_initialized(message) and message.from_user.id == int(self.admin):
                send_welcome(message)

        @bot.message_handler(content_types=["photo"],
                             func=lambda message: is_initialized(message) and message.chat.title is not None)
        def delete_compressed_image(message):
            save_file(message)
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
        def save_file(message):
            with app.app_context():
                try:
                    if message.document:
                        file_info = bot.get_file(message.document.file_id)
                        file_name = message.document.file_name
                    else:
                        file_info = bot.get_file(message.photo[1].file_id)
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
                        photo = Photo(local_path, file_name, message)

                        if not upload_photo(photo, local_path, chat_name):
                            bot.delete_message(photo.chat_id, photo.msg_id)
                            text = "{0} дубликат".format(photo.yd_filename)
                            self.l.info(
                                '{0} {1} {2} duplicate'.format(message.message_id, file_id, file_name))
                            bot.send_message(photo.chat_id, text)

                except ApiException as ae:
                    self.l.error('{0}'.format(ae))
                    if "file is too big" in ae.args[0]:
                        bot.reply_to(message, "Файл слишком большой. Залейте вручную")
                except BaseException as e:
                    self.l.error('{0}'.format(e))
                    bot.reply_to(message, "Файл не скачался. Повторите")

        def upload_photo(photo, local_path, chat_title):
            return Uploader.upload(self.y, self.l, photo, local_path, chat_title)

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
