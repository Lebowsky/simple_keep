import unittest
from unittest.mock import MagicMock
import json
import os

from ui_models import Timer
from ui_utils import HashMap
from main import noClass
from hs_services import HsService
from db_services import DocService

from data_for_tests.utils_for_tests import hashMap


class TestMainEvents(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings')
        self.hash_map['DEVICE_MODEL'] = self.rs_settings.get('DEVICE_MODEL')
        self.hash_map['ANDROID_ID'] = self.rs_settings.get('ANDROID_ID')
        self.data_path = './data_for_tests/http_requests'
        self.sut = Timer(self.hash_map, self.rs_settings)

    def test_setUp(self):
        pass
        # print(self.sut.http_settings)

    def test_timer_on_start(self):
        self.sut.timer_on_start()

    @unittest.skip
    def test_load_docs(self):
        self.rs_settings.put('URL', 'url', True)
        self.rs_settings.put('USER', 'user', True)
        self.rs_settings.put('PASS', '1234', True)
        self.rs_settings.put('notification_id', None, True)
        sut = Timer(self.hash_map, self.rs_settings)

        load_data = self.get_load_data()
        HsService.get_data = MagicMock(return_value=load_data)

        DocService.update_data_from_json = MagicMock()

        sut.load_docs()
        HsService.get_data.assert_called_once()

        DocService.update_data_from_json.assert_called_once()
        self.assertIsNone(self.rs_settings.get('notification_id'))

    def get_load_data(self):
        with open(f'{self.data_path}/nsi_data.json', encoding='utf-8') as fp:
            return json.load(fp)



