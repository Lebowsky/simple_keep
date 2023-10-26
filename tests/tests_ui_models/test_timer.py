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
        self.sut = Timer(self.hash_map)

    def test_can_upload_buffer_data_barcodes(self):
        http_result = HsService.HttpAnswer(url='', status_code=200)
        HsService.send_barcodes = MagicMock(return_value=http_result)

        from tiny_db_services import ExchangeQueueBuffer
        self.rs_settings.put('path_to_databases', './', True)

        buffer_data = {
            "id_good": "190a7469-3325-4d33-b5ec-28a63ac83b06-848a00112f43529a11d955bce8a71ff6",
            "barcode": "2000000058455",
            "id_property": None,
            "id_unit": None
        }
        buffer = ExchangeQueueBuffer('barcodes')
        buffer.save_data_to_send(buffer_data, pk='barcode')

        self.sut._upload_buffer_data()
        self.assertFalse(buffer.provider.get_all())

    def test_must_save_upload_buffer_data_barcodes_with_error(self):
        http_result = HsService.HttpAnswer(url='', status_code=404, error=True)
        HsService.send_barcodes = MagicMock(return_value=http_result)

        from tiny_db_services import ExchangeQueueBuffer
        buffer_data = {
            "id_good": "190a7469-3325-4d33-b5ec-28a63ac83b06-848a00112f43529a11d955bce8a71ff6",
            "barcode": "2000000058455",
            "id_property": None,
            "id_unit": None
        }
        buffer = ExchangeQueueBuffer('barcodes')
        buffer.save_data_to_send(buffer_data, pk='barcode')

        self.sut._upload_buffer_data()
        self.assertTrue(buffer.provider.get_all())


    def get_load_data(self):
        with open(f'{self.data_path}/nsi_data.json', encoding='utf-8') as fp:
            return json.load(fp)



