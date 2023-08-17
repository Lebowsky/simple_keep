import unittest
from unittest.mock import MagicMock

from ui_models import BarcodeTestScreen
from ui_utils import HashMap
from main import noClass

from data_for_tests.utils_for_tests import hashMap


class TestBarcodeTestScreen(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings_local')
        self.sut = BarcodeTestScreen(self.hash_map, self.rs_settings)

    def test_on_back_pressed_must_set_hash_map_value_BackScreen(self):
        # init test data
        self.sut.listener = 'ON_BACK_PRESSED'

        # execute test method
        self.sut.on_input()
        actual = self.hash_map.containsKey('BackScreen')

        # assert test method results
        self.assertTrue(actual)

    def test_on_back_button_must_set_hash_map_value_BackScreen(self):
        # init test data
        self.sut.listener = 'BACK_BUTTON'

        # execute test method
        self.sut.on_input()
        actual = self.hash_map.containsKey('BackScreen')

        # assert test method results
        self.assertTrue(actual)

    def test_barcode_scanned_must_set_hash_map_barcode_fields(self):
        barcode = '2000000000015'
        self.hash_map['barcode_camera'] = barcode

        self.sut._barcode_scanned()

        expect = {
            'fld_1': 'GTIN: 2000000000015',
            'fld_2': 'BARCODE: 2000000000015',
            'fld_3': 'SCHEME: EAN13',
            'fld_4': '',
            'fld_5': '',
            'fld_6': '',
            'fld_7': '',
        }

        for i, (k, v) in enumerate(expect.items()):
            self.assertTrue(self.hash_map.containsKey(k))
            self.assertEqual(v, self.hash_map[k], msg=f'i={i}')

    def test_barcode_scanned_must_not_set_hm_where_non_barcode(self):
        self.hash_map['barcode_camera'] = ''

        self.sut._barcode_scanned()

        expect = {
            'fld_1': 'GTIN: 2000000000015',
            'fld_2': 'SERIAL: ',
            'fld_3': 'BARCODE: 2000000000015',
            'fld_4': 'SCHEME: EAN13',
            'fld_5': '',
            'fld_6': '',
            'fld_7': '',
        }

        for i, (k, v) in enumerate(expect.items()):
            self.assertFalse(self.hash_map.containsKey(k))
