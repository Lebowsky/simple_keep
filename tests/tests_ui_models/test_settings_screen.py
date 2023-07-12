import json
import unittest
from unittest.mock import MagicMock

from ui_models import SettingsScreen, FontSizeSettingsScreen
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


class TestFontSizeSettingsScreen(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings_local')
        self.sut = FontSizeSettingsScreen(self.hash_map, self.rs_settings)

    def test_on_start_must_add_field_to_hash_map(self):
        self.rs_settings.put('TitleTextSize', '18', True)

        self.sut.on_start()

        self.assertTrue(self.hash_map.containsKey('TitleTextSize'))
        self.assertEqual(
            self.hash_map.get_json('TitleTextSize'),
            {
                "hint": "Размер заголовка",
                "default_text": "18",
            }
        )

    def test_on_input_must_update_rs_settings_and_add_no_refresh_to_hash_map(self):
        self.hash_map['TitleTextSize'] = 18

        self.sut.on_input()

        self.assertEqual(self.rs_settings.get('TitleTextSize'), '18')
        self.assertTrue(self.hash_map.containsKey('noRefresh'))

    def test_on_input_must_call_BackScreen_where_press_cancel_button(self):
        self.sut.listener = 'btn_on_cancel'
        self.sut.on_input()
        self.assertTrue(self.hash_map.containsKey('BackScreen'))

    def test_on_input_must_call_BackScreen_where_press_back_button(self):
        self.sut.listener = 'ON_BACK_PRESSED'
        self.sut.on_input()
        self.assertTrue(self.hash_map.containsKey('BackScreen'))


