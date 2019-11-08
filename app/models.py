import datetime

from app import db
from app.generic import calc_hash
from config import Config


class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_hash = db.Column(db.String(240), nullable=False)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    msg_date = db.Column(db.DateTime, nullable=False)
    yd_path = db.Column(db.String(240), nullable=False)

    # @staticmethod
    # def get_photo(photo_file, message, yd_path):
    #     h = calc_hash(photo_file)
    #     photo = Photo.query.filter_by(chat_id=message.chat.id, file_hash=h).first()
    #     if photo is None:
    #         photo = Photo()
    #         photo.file_hash = h
    #         photo.chat_id = message.chat.id
    #         photo.user_id = message.from_user.id
    #         photo.msg_date = datetime.datetime.fromtimestamp(message.date)
    #         photo.yd_path = yd_path
    #         db.session.add(photo)
    #         db.session.commit()
    #     return photo

    @staticmethod
    def save_to_db(file_path, message, yd_path):
        h = calc_hash(file_path)
        photo = Photo()
        photo.file_hash = h
        photo.chat_id = message.chat.id
        photo.user_id = message.from_user.id
        photo.msg_date = datetime.datetime.fromtimestamp(message.date)
        photo.yd_path = yd_path
        db.session.add(photo)
        db.session.commit()
        return photo

    @staticmethod
    def is_exists(chat_id, photo_file):
        return Photo.get_photo(chat_id, photo_file) is not None

    @staticmethod
    def get_photo(chat_id, file_path):
        h = calc_hash(file_path)
        return Photo.query.filter_by(chat_id=chat_id, file_hash=h).first()

    __table_args__ = (
        db.Index('ix_chat_hash', chat_id, file_hash),
    )


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(240), nullable=False)
    local_folder = db.Column(db.String(240), nullable=False)
    yd_folder = db.Column(db.String(240), nullable=False)

    # @staticmethod
    # def get_chat(message):
    #     chat = Chat.query.filter_by(id=message.chat.id).first()
    #     if chat is None:
    #         chat = Chat()
    #         chat.id = message.chat.id
    #         chat.name = message.chat.title
    #         chat.local_folder = Config.DOWNLOAD_FOLDER + "/" + chat.name
    #         chat.yd_folder = Config.YD_DOWNLOAD_FOLDER + "/" + chat.name
    #         db.session.add(chat)
    #         db.session.commit()
    #     return chat

    @staticmethod
    def save_to_db(chat_id, chat_name):
        chat = Chat()
        chat.id = chat_id
        chat.name = chat_name
        chat.local_folder = Config.DOWNLOAD_FOLDER + "/" + chat.name
        chat.yd_folder = Config.YD_DOWNLOAD_FOLDER + "/" + chat.name
        db.session.add(chat)
        db.session.commit()
        return chat

    @staticmethod
    def is_exists(id):
        return Chat.get_chat(id=id) is not None

    @staticmethod
    def get_chat(id):
        return Chat.query.filter_by(id=id).first()
