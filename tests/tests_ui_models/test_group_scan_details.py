import json
import unittest
from unittest.mock import MagicMock

from ui_models import GroupScanDocDetailsScreen, GroupScanDocDetailsScreenNew
from ui_utils import HashMap
from main import noClass
from hs_services import HsService
from db_services import DocService
from ui_utils import BarcodeWorker

from data_for_tests.utils_for_tests import hashMap


class TestGroupScanDocDetailsScreen(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings')
        self.sut = GroupScanDocDetailsScreen(self.hash_map, self.rs_settings)
        self.path_to_test_data = './data_for_tests/http_requests'

    def tearDown(self) -> None:
        pass
        #self.sut.queue_service.provider.close()

    def test_can_call_communication_and_return_true(self):
        answer = HsService.HttpAnswer(
            error=False,
            error_text='',
            status_code=200,
            url='')

        HsService.communication_test = MagicMock(return_value=answer)
        self.sut.hs_service.http_answer = answer
        res = self.sut._check_connection()
        self.assertTrue(res)
        HsService.communication_test.assert_called_once_with(timeout=1)

    def test_can_call_communication_and_return_false(self):
        answer = HsService.HttpAnswer(
            error=True,
            error_text='',
            status_code=404,
            url='')

        HsService.communication_test = MagicMock(return_value=answer)
        self.sut.hs_service.http_answer = answer
        res = self.sut._check_connection()
        self.assertFalse(res)
        HsService.communication_test.assert_called_once_with(timeout=1)

        HsService.communication_test = MagicMock(side_effect=Exception('err'))
        with self.assertRaises(Exception) as context:
            res = self.sut._check_connection()

            self.assertEqual('err', context)

        self.assertFalse(res)

    def test_method_must_return_doc_data(self):
        expect = self.get_test_data('doc_data_example.json')
        answer = HsService.HttpAnswer(
            error=False,
            error_text='',
            status_code=200,
            url='',
            data=expect,
            unauthorized=False,
            forbidden=False,
        )

        HsService.get_data = MagicMock()
        self.sut.hs_service.http_answer = answer

        actual = self.sut._get_update_current_doc_data()

        HsService.get_data.assert_called_once()
        self.assertEqual(expect, actual)

    def test_method_must_call_toast_error(self):
        expect = 'Ошибка авторизации сервера 1С'

        answer = HsService.HttpAnswer(
            error=True,
            error_text='',
            status_code=403,
            url='',
            data=None,
            unauthorized=True,
            forbidden=False,
        )

        HsService.get_data = MagicMock()
        self.sut.hs_service.http_answer = answer

        res = self.sut._get_update_current_doc_data()
        actual = self.hash_map['toast']

        HsService.get_data.assert_called_once()
        self.assertEqual(expect, actual)
        self.assertIsNone(res)

    def test_method_must_call_toast_and_notify_error(self):
        expect = 'forbidden'

        answer = HsService.HttpAnswer(
            error=True,
            error_text='forbidden',
            status_code=403,
            url='',
            data=None,
            unauthorized=False,
            forbidden=True,
        )

        HsService.get_data = MagicMock()
        self.sut.hs_service.http_answer = answer
        self.rs_settings.put("notification_id", 0, True)

        res = self.sut._get_update_current_doc_data()
        actual = self.hash_map['toast']

        HsService.get_data.assert_called_once()
        self.assertEqual(expect, actual)
        self.assertIsNone(res)
        self.assertTrue(self.hash_map.containsKey('basic_notification'))
        self.assertEqual(
            self.hash_map['basic_notification'],
            json.dumps([{
                    'number': 1,
                    'title': 'Ошибка обмена',
                    'message': 'forbidden'
            }])
        )

    def test_method_must_call_write_error_log(self):
        expect = 'Ошибка загрузки документа:  error'

        answer = HsService.HttpAnswer(
            error=True,
            error_text='error',
            status_code=404,
            url='',
            data=None,
            unauthorized=False,
            forbidden=False,
        )

        HsService.get_data = MagicMock()
        self.sut.hs_service.http_answer = answer
        DocService.write_error_on_log = MagicMock()

        res = self.sut._get_update_current_doc_data()

        HsService.get_data.assert_called_once()
        DocService.write_error_on_log.assert_called_once_with(expect)
        self.assertIsNone(res)

    def get_test_data(self, file_name):
        with open(f'{self.path_to_test_data}/{file_name}', encoding='utf-8') as fp:
            return json.load(fp)


class TestGroupScanDocDetailsScreenNew(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings_local')
        self.rs_settings.put("path_to_databases", "./", True)
        self.sut = GroupScanDocDetailsScreenNew(self.hash_map, self.rs_settings)
        self.path_to_test_data = './data_for_tests/http_requests'
        self.barcode_worker: BarcodeWorker

    def tearDown(self) -> None:
        self.sut.queue_service.provider.close()

    def test_get_barcode(self):
        from tests.data_for_tests.nosql.initial_data import barcode_data

        self.hash_map.put('barcode_camera', '00000046198488X?io+qCABm8wAYa')
        self.hash_map.put('have_mark_plan', False)

        BarcodeWorker._get_barcode_data = MagicMock(return_value=barcode_data)

        result = self.sut._barcode_scanned()

