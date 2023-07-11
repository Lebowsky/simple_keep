import unittest
from unittest.mock import MagicMock

from ui_models import SettingsScreen
from ui_utils import HashMap
from main import noClass

from data_for_tests.utils_for_tests import hashMap


class TestSettingsScreen(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings_local')
        self.sut = SettingsScreen(self.hash_map, self.rs_settings)

    def test_has_check_adding_settings_to_hash_map(self):
        self.rs_settings.put('use_mark', 'true', False)

        self.sut.on_start()

        self.assertEqual(self.hash_map['use_mark'], 'true')
        self.assertTrue(self.hash_map.containsKey('ip_adr'))

    def test_on_input(self):
        # init test data
        self.sut.listener = 'btn_http_settings'

        # execute test method
        self.sut.on_input()

        # assert test method results
        self.assertEqual(
            self.hash_map['ShowScreen'], 'Настройки http соединения')
