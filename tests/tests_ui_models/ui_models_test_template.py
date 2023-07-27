import unittest
from unittest.mock import MagicMock

from ui_models import Model_Name_Class
from ui_utils import HashMap
from main import noClass

from data_for_tests.utils_for_tests import hashMap


class Test_Model_Name_Class(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings_local')
        self.sut = Model_Name_Class(self.hash_map, self.rs_settings)

    def test_some_method_result(self):
        # init test data
        self.hash_map['some_key'] = 'some_value'
        expect = 'some_result_value'

        # execute test method
        actual = self.sut.some_method()

        # assert test method results
        self.assertEqual(expect, actual)

