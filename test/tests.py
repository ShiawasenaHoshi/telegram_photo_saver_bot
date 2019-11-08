import os
import unittest


from app.generic import calc_hash
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
