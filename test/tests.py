import os
import unittest

from app.generic import calc_hash
from app.models import Chat, ChatOption, Photo
from config import Config

basedir = os.path.abspath(os.path.dirname(__file__))
data_path = os.path.join(basedir, 'data')


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'test.db')
    TG_TOKEN = ""
    TG_ADMIN_ID = 0
    YD_TOKEN = ""


from app import create_app, db


class SimpleTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_hash(self):
        hash1 = calc_hash(os.path.join(data_path, '1.jpg'))
        hash2 = calc_hash(os.path.join(data_path, '2.jpg'))
        self.assertNotEqual(hash1, hash2)
        self.assertEqual(hash1, calc_hash(os.path.join(data_path, '1.jpg')))

    def test_models(self):
        Chat.save_to_db(1, "test1")
        ch = Chat.get_chat(1)
        self.assertEqual(1, ch.id)
        self.assertEqual("test1", ch.name)
        o = ch.options.all()
        self.assertTrue(len(o) == 2)
        ch.add_option("test_key", "test_val")
        o = ch.options.all()
        self.assertTrue(len(o) == 3)
        self.assertEqual("test_key", o[2].key)
        self.assertEqual("test_val", o[2].value)
        self.assertIsNotNone(o[2].chat)
        self.assertIsNotNone(ChatOption.get_val(ch.id, "test_key"))
        self.assertIsNone(ChatOption.get_val(ch.id, "test_val"))
        with self.assertRaises(Exception):
            ch.add_option("test_key", "exception")

    def test_parse_exif(self):
        p1 = Photo.parse_exif(os.path.join(data_path, '1.jpg'))
        self.assertTrue(p1[0])
        self.assertEquals(p1[1], '2019_11_02')
        self.assertEquals(p1[2], '18_26_44')
        p2 = Photo.parse_exif(os.path.join(data_path, '2.jpg'))
        self.assertFalse(p2[0])
        self.assertEquals(p2[1], 'photos')
        self.assertEquals(p2[2], '2.jpg')

