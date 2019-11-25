import datetime
import os
import re

from exif import Image

from app import db
from app.generic import calc_hash, create_yd_folder_if_not_exist
from config import Config


class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_hash = db.Column(db.String(240), nullable=False)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    msg_date = db.Column(db.DateTime, nullable=False)  # date of msg or forward_date
    msg_id = db.Column(db.Integer, nullable=False)  # mandatory for delete function
    yd_filename = db.Column(db.String(240), nullable=False)
    yd_sub_folder = db.Column(db.String(240), nullable=False)

    def __init__(self, local_path, file_name, message=None):
        if message:
            self.chat_id = message.chat.id
            self.user_id = message.from_user.id
            self.msg_id = message.message_id
            if message.forward_date is not None and message.forward_date <= message.date:
                date = message.forward_date
            else:
                date = message.date
            self.msg_date = datetime.datetime.fromtimestamp(date)
        else:
            self.chat_id = 0
            self.user_id = 0
            self.msg_id = 0
            self.msg_date = datetime.datetime.fromtimestamp(0)

        h = calc_hash(local_path)
        self.file_hash = h
        parsed = Photo.parse_exif(local_path)
        self.yd_sub_folder = parsed[1]
        if parsed[0]:
            if not file_name:
                file_name = os.path.basename(local_path)
            self.yd_filename = "{0}_{1}".format(parsed[2], file_name)
        else:
            self.yd_filename = parsed[2]

    @staticmethod
    def parse_exif(local_path):
        with open(local_path, 'rb') as image_file:
            has_date = False
            dt = None
            try:
                img = Image(image_file)

                if img.has_exif and hasattr(img, 'datetime'):
                    dt_str = img.datetime
                    try:
                        if re.match("^\d+$", dt_str):
                            dt = datetime.datetime.fromtimestamp(int(dt_str) / 1000)
                        else:
                            dt = datetime.datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
                    except BaseException:
                        date_str = "unparsed"
                else:
                    date_str = "photos"
            except BaseException:
                info = os.stat(local_path)
                dt = datetime.datetime.fromtimestamp(info.st_mtime)

            if dt:
                date_str = dt.strftime('%Y_%m_%d')
                time_str = dt.strftime('%H_%M_%S')
                has_date = True
            else:
                time_str = os.path.basename(local_path)
            return has_date, date_str, time_str

    def get_yd_path(self, ya_disk=None):
        ch = Chat.get_chat(self.chat_id)
        ch_path = ch.get_yd_folder(ya_disk)
        sub_folder_path = ch_path + "/" + self.yd_sub_folder
        if ya_disk is not None:
            create_yd_folder_if_not_exist(sub_folder_path, ya_disk)
        return sub_folder_path + "/" + self.yd_filename

    @staticmethod
    def is_exists(chat_id, photo_file):
        return Photo.get_photo(chat_id, photo_file) is not None

    @staticmethod
    def get_photo(chat_id, file_path):
        h = calc_hash(file_path)
        return Photo.query.filter_by(chat_id=chat_id, file_hash=h).first()  # from any chat

    @staticmethod
    def get_duplicate(user_id, msg_date, file_path):
        h = calc_hash(file_path)
        return Photo.query.filter_by(user_id=user_id, file_hash=h, msg_date=msg_date).first()

    __table_args__ = (
        db.Index('ix_chat_hash', chat_id, file_hash),
        db.Index('ix_user_hash_date', user_id, file_hash, msg_date)
    )


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(240), nullable=False)
    options = db.relationship('ChatOption', backref='chat', lazy='dynamic')
    photos = db.relationship('Photo', backref='chat', lazy='dynamic')

    @staticmethod
    def save_to_db(chat_id, chat_name):
        chat = Chat()
        chat.id = chat_id
        chat.name = chat_name
        db.session.add(chat)
        def_options = chat._get_default_options()
        db.session.add_all(def_options)
        db.session.commit()
        return chat

    def get_local_folder(self):
        return Config.DOWNLOAD_FOLDER + "/" + self.name

    def get_yd_folder(self, ya_disk=None):
        path = Config.YD_DOWNLOAD_FOLDER + "/" + self.name
        if ya_disk is not None:
            create_yd_folder_if_not_exist(path, ya_disk)
        return path

    def add_option(self, key, value):
        co = ChatOption(self, key, value)
        db.session.add(co)
        db.session.commit()

    def _get_default_options(self):
        return [
            ChatOption(self, "photo_allowed", "0"),
            ChatOption(self, "doc_mime_filter", "^.+/(jpg|jpeg|avi|mov|mp4)$")
        ]

    @staticmethod
    def is_exists(id):
        return Chat.get_chat(id=id) is not None

    @staticmethod
    def get_chat(id):
        return Chat.query.filter_by(id=id).first()


class ChatOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'))
    key = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(240))

    def __init__(self, chat, key, value):
        self.chat_id = chat.id
        self.key = key
        self.value = value

    @staticmethod
    def get_val(chat_id, key):
        co = ChatOption.query.filter_by(chat_id=chat_id, key=key).first()
        if co:
            return co.value
        else:
            return None

    @staticmethod
    def set_val(chat_id, key, value):
        co = ChatOption.query.filter_by(chat_id=chat_id, key=key).first()
        if co:
            co.value = value
            db.session.add(co)
            db.session.commit()
        else:
            raise Exception("there is no option with name {0}".format(key))

    __table_args__ = (
        db.UniqueConstraint('chat_id', 'key', name='uc_chat_key'),
    )
