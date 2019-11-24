import os
import threading
from os import listdir
from os.path import isfile, join

from yadisk import yadisk

from app import db
from app.models import Photo, Chat


class Uploader(threading.Thread):
    scan_interval = 10

    def __init__(self, yd_token, yd_download_folder, scanner_folder, app):
        super().__init__()
        self.yd_token = yd_token
        self.scanner_folder = scanner_folder
        self.yd_download_f = yd_download_folder
        self.app = app
        self.l = app.logger
        self.y = yadisk.YaDisk(token=self.yd_token)

    def scan_and_upload(self):
        onlyfiles = [f for f in listdir(self.scanner_folder) if isfile(join(self.scanner_folder, f))]
        for local_path in onlyfiles:
            photo = Photo(local_path, None, None)
            if not self.upload_photo(photo, local_path):
                self.l.info('{0} duplicate'.format(photo.get_yd_path()))

    def upload_photo(self, photo, local_path):
        return Uploader.upload(self.y, self.l, photo, local_path, "FolderScanner")

    @staticmethod
    def upload(yd, log, photo, local_path, chat_title):
        yd_path = photo.get_yd_path(yd)
        uploaded = False
        with open(local_path, "rb") as f:
            if not Chat.is_exists(photo.chat_id):
                try:
                    Chat.save_to_db(photo.chat_id, chat_title)
                except BaseException as e:
                    log.error('{0}'.format(e))
            if not yd.exists(yd_path):
                yd.upload(f, yd_path)
                log.info("YD uploaded: {0}".format(yd_path))
                if not Photo.is_exists(photo.chat_id, local_path):
                    db.session.add(photo)
                    db.session.commit()
                    log.info("DB added: " + yd_path)
                uploaded = True
        os.remove(local_path)
        return uploaded
