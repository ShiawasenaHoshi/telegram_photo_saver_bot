import telebot
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
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

        # @bot.message_handler(content_types=["text"])
        # def repeat_all_messages(message):  # Название функции не играет никакой роли, в принципе
        #     bot.send_message(message.chat.id, message.text)

        @bot.message_handler(content_types=["document"])
        def it_is_image(message):  # Название функции не играет никакой роли, в принципе
            m = re.search('^.+/(jpg|jpeg|avi|mov|mp4)$', message.document.mime_type)
            if m.group(0):
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)

                with open(Config.DOWNLOAD_FOLDER + "/" + message.document.file_name, 'w+b') as new_file:
                    new_file.write(downloaded_file)
                # bot.send_message(message.chat.id, message.document.file_name + " downloaded!")

        bot.polling(none_stop=True)
