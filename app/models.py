from app import db
from config import Config


class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(240), nullable=False) #fixme
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    msg_date = db.Column(db.DateTime, nullable=False)
    filename = db.Column(db.String(240), nullable=False)

    # @staticmethod
    # def get_photo(message):
    #     photo = Photo.query.filter_by(id=message.document.id).first()
    #     if chat is None:
    #         chat = Chat()
    #         chat.id = message.chat.chat_id
    #         chat.name = message.chat.title
    #         chat.local_folder = Config.DOWNLOAD_FOLDER + "/" + chat.name
    #         chat.yd_folder = Config.YD_DOWNLOAD_FOLDER + "/" + chat.name
    #     return chat




class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(240), nullable=False)
    local_folder = db.Column(db.String(240), nullable=False)
    yd_folder = db.Column(db.String(240), nullable=False)

    @staticmethod
    def get_chat(message):
        chat = Chat.query.filter_by(id=message.chat.chat_id).first()
        if chat is None:
            chat = Chat()
            chat.id = message.chat.chat_id
            chat.name = message.chat.title
            chat.local_folder = Config.DOWNLOAD_FOLDER + "/" + chat.name
            chat.yd_folder = Config.YD_DOWNLOAD_FOLDER + "/" + chat.name
        return chat
