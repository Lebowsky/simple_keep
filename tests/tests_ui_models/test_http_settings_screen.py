import json
import unittest
from unittest.mock import MagicMock, PropertyMock, Mock

import hs_services
from ui_models import HttpSettingsScreen
from ui_utils import HashMap
from main import noClass

from data_for_tests.utils_for_tests import hashMap


class TestHttpSettingsScreen(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings')
        self.sut = HttpSettingsScreen(self.hash_map, self.rs_settings)
        self.clear_rs_settings()

    def test_on_start_must_put_hash_map_data(self):
        # init test data
        self.hash_map['listener'] = 'btn_save'

        expect = [
            'btn_test_connection',
            'url',
            'user',
            'pass',
            'user_name',
        ]

        # execute test method
        self.sut.on_start()

        # assert test method results
        for key in expect:
            self.assertTrue(self.hash_map.containsKey(key), f'{key} is not set hash_map')

    def test_must_save_settings(self):
        settings = {'URL': 'test_url', 'USER': 'test_user', 'PASS': 'test_pass', 'user_name': 'test_user_name'}
        self.hash_map.put_data({k.lower(): v for k, v in settings.items()})
        self.sut.listener = 'btn_save'

        self.sut.on_input()

        for key, value in settings.items():
            self.assertEqual(self.rs_settings.get(key), value, f'{key} not in rs_settings')

        self.assertTrue(self.hash_map.containsKey('BackScreen'))

    def test_must_save_barcode_settings(self):
        self.sut.listener = 'barcode'
        barcode_struct = {
            'url': 'test_url',
            'user': 'test_user',
            'pass': 'test_pass',
            'user_name': 'test_user_name',
        }
        self.hash_map.put('barcode_camera2', barcode_struct, to_json=True)

        self.sut.on_input()

        self.assertEqual(self.rs_settings.get('URL'), 'test_url')
        self.assertEqual(self.rs_settings.get('USER'), 'test_user')
        self.assertEqual(self.rs_settings.get('PASS'), 'test_pass')
        self.assertEqual(self.rs_settings.get('user_name'), 'test_user_name')

        self.assertTrue(self.hash_map.containsKey('url'))
        self.assertTrue(self.hash_map.containsKey('user'))
        self.assertTrue(self.hash_map.containsKey('pass'))
        self.assertTrue(self.hash_map.containsKey('user_name'))

        self.assertIsNotNone((self.hash_map['url']))
        self.assertIsInstance(self.hash_map.get_json('url'), dict)
        self.assertIsNotNone(self.hash_map['user'])
        self.assertIsInstance(self.hash_map.get_json('user'), dict)
        self.assertIsNotNone(self.hash_map['pass'])
        self.assertIsInstance(self.hash_map.get_json('pass'), dict)
        self.assertIsNotNone(self.hash_map['user_name'])
        self.assertIsInstance(self.hash_map.get_json('user_name'), dict)

    def test_must_set_toast_invalid_barcode(self):
        self.sut.listener = 'barcode'
        self.hash_map.put('barcode_camera2', '')

        self.sut.on_input()

        self.assertTrue(self.hash_map['toast'], 'Неверный формат QR-кода')

    def test_must_set_toast_unauthorized(self):
        # TODO: AND implement test
        pass

    def test_must_set_toast_forbidden(self):
        # TODO: AND implement test
        pass

    def test_must_set_toast_connection_error(self):
        # TODO: AND implement test
        pass

    def test_must_set_toast_connection_done(self):
        # TODO: AND implement test
        pass

    def clear_rs_settings(self):
        with open('rs_settings.json', 'w') as f:
            json.dump({}, fp=f)
