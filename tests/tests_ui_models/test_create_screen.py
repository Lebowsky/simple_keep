import unittest

from main import create_screen, noClass, rs_settings
from ui_models import GroupScanDocDetailsScreen

from ui_utils import HashMap
from data_for_tests.utils_for_tests import hashMap


class TestMainCreateScreen(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings_local')

    def test_check_create_screen_class_and_save_on_global_variable(self):
        self.hash_map['current_screen_name'] = 'Документ товары'
        self.hash_map['current_process_name'] = 'Групповая обработка'

        screen = create_screen(self.hash_map)

        self.assertIsInstance(screen, GroupScanDocDetailsScreen)

        from new_handlers import current_screen
        self.assertIsInstance(current_screen, GroupScanDocDetailsScreen)

    def test_must_create_screen_and_not_rewrite_global_variable(self):
        self.hash_map['current_screen_name'] = 'Документ товары'
        self.hash_map['current_process_name'] = 'Групповая обработка'
        self.hash_map['listener'] = 'onStart'

        screen = create_screen(self.hash_map)

        self.assertIsInstance(screen, GroupScanDocDetailsScreen)

        self.hash_map['listener'] = 'onInput'
        sut = create_screen(self.hash_map)

        self.assertEqual(getattr(sut, 'listener'), 'onInput')
        self.assertIs(screen, sut)
