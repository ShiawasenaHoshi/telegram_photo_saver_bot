import os
import re
import threading
import time
from os import listdir
from os.path import isfile, join

from yadisk import yadisk
from yadisk.exceptions import PathExistsError

from app import db
from app.generic import create_folder_if_not_exists, get_extension
from app.models import Photo, Chat
from config import Config


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
        create_folder_if_not_exists(Config.SCANNER_FOLDER)

    def run(self):
        with self.app.app_context():
            self.l.info("Uploader starting")
            while True:
                self.scan_and_upload()
                time.sleep(self.scan_interval)

    def scan_and_upload(self):
        onlyfiles = [f for f in listdir(self.scanner_folder) if isfile(join(self.scanner_folder, f))]
        for file_name in onlyfiles:
            if self.is_extension_ok(file_name.lower()):
                path = join(self.scanner_folder, file_name)
                try:
                    photo = Photo(path, file_name, None)
                    if not self.upload_photo(photo, path):
                        self.l.info('{0} duplicate'.format(photo.get_yd_path()))
                except PathExistsError as pee:
                    self.l.warn(pee)
                    os.remove(path)
                except BaseException as e:
                    self.l.error(e)

    def is_extension_ok(self, path):
        return re.match("^\.(jpg|jpeg|avi|mov|mp4|mkv)$", get_extension(path))

    def upload_photo(self, photo, local_path):
        with self.app.app_context():
            return Uploader.upload(self.y, self.l, photo, local_path, "FolderScanner")

    @staticmethod
    def upload(yd, log, photo, local_path, chat_title, ):
        uploaded = False
        with open(local_path, "rb") as f:
            if not Chat.is_exists(photo.chat_id):
                try:
                    Chat.save_to_db(photo.chat_id, chat_title)
                except BaseException as e:
                    log.error('{0}'.format(e))
            yd_path = photo.get_yd_path(yd)
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
