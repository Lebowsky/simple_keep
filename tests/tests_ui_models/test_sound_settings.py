import unittest
from unittest.mock import MagicMock

from ui_models import SoundSettings
from ui_utils import HashMap
from main import noClass

from data_for_tests.utils_for_tests import hashMap


class Test_Model_SoundSettings(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings_local')
        self.sut = SoundSettings(self.hash_map, self.rs_settings)


    def test_on_save_pressed(self):
        # init test data
        self.sut.listener = 'save_btn'
        expect = 'Настройки и обмен'
        # execute test method
        self.sut.on_input()
        self.assertEqual('Настройки и обмен', self.sut.hash_map.get('ShowScreen'))





