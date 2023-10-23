import datetime
import json
import time
import unittest
from tinydb import TinyDB
from tiny_db_services import TinyNoSQLProvider, ScanningQueueService, LoggerService
from tests.data_for_tests.nosql.initial_data import initial_data
from ui_utils import DateFormat


class TestTinyNoSQLProvider(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = TinyNoSQLProvider(table_name='test_table', db_path='./')
        self.provider.drop_table('test_table')

    def tearDown(self) -> None:
        self.provider.close()

    def test_must_insert_data(self):
        expect = {'row_id': 5, 'test_data': 'test_data'}

        doc_id = self.provider.insert(expect)
        self.assertEqual(1, doc_id)

        actual = self.provider.get(row_id=5)
        self.assertEqual(actual, expect)

        doc_id = self.provider.insert(expect)
        self.assertEqual(2, doc_id)

        actual = self.provider.search(row_id=5)
        self.assertEqual(actual, [expect, expect])

    def test_must_insert_data_multiple(self):
        expect = [
            {'row_id': 5, 'test_data': 'test_data'},
            {'row_id': 6, 'test_data': 'test_data'}
        ]

        res = self.provider.insert_multiple(expect)
        self.assertEqual([1,2], res)

        actual = self.provider.get_all()
        self.assertEqual(expect, actual)

    def test_must_update_data(self):
        data = [
            {'row_id': 5, 'test_data': 'test_data'},
            {'row_id': 6, 'test_data': 'test_data'}
        ]

        expect = {'row_id': 5, 'test_data': 'test_data_new'}

        self.provider.insert_multiple(data)

        res = self.provider.update(
            data={'test_data': 'test_data_new'},
            row_id=5
        )

        self.assertEqual([1], res)

        actual = self.provider.get(row_id=5)

        self.assertEqual(expect, actual)

    def test_must_upsert_data(self):
        data = [
            {'row_id': 5, 'test_data': 'test_data'},
            {'row_id': 6, 'test_data': 'test_data'}
        ]

        self.provider.insert_multiple(data)

        res = self.provider.upsert(
            data={'test_data': 'test_data_new'},
            row_id=6
        )
        self.assertEqual([2], res)

        res = self.provider.upsert(
            data={'row_id': 7, 'test_data': 'test_data_new'},
            row_id=7
        )
        self.assertEqual([3], res)

    def test_must_remove_data(self):
        data = [
            {'row_id': 5, 'test_data': 'test_data'},
            {'row_id': 6, 'test_data': 'test_data'},
            {'row_id': 7, 'test_data': 'test_data_new'}
        ]

        self.provider.insert_multiple(data)

        self.provider.remove(test_data='test_data')

        expect = [{'row_id': 7, 'test_data': 'test_data_new'}]
        actual = self.provider.get_all()

        self.assertEqual(expect, actual)

    def test_must_check_count_data(self):
        self.assertEqual(self.provider.count(test_data='test_data'), 0)

        data = [
            {'row_id': 5, 'test_data': 'test_data'},
            {'row_id': 6, 'test_data': 'test_data'},
            {'row_id': 7, 'test_data': 'test_data_new'}
        ]

        self.provider.insert_multiple(data)

        self.assertEqual(self.provider.count(test_data='test_data'), 2)


class TestScanningQueueService(unittest.TestCase):

    def setUp(self) -> None:
        self.provider = TinyNoSQLProvider(table_name='test_table', db_path='./')
        self.provider.drop_table('test_table')
        self.provider.drop_table('scanning_queue')

    def tearDown(self) -> None:
        self.provider.close()

    def test_must_save_scanned_row_data(self):
        initial_data = [
            {'id_doc': '123', 'row_id': 5, 'test_data': 'test_data'},
            {'id_doc': '123', 'row_id': 6, 'test_data': 'test_data'}
        ]

        row_data = {
            'id_doc': '123', 'row_id': 7, 'test_data': 'test_data'
        }

        self.provider.insert_multiple(initial_data)
        sut = ScanningQueueService(provider=self.provider)
        sut.save_scanned_row_data(row_data)
        self.assertTrue(sut.provider.count(id_doc='123'), 3)

    def test_get_scanned_row_qtty(self):
        initial_data = [
            {'id_doc': '123', 'row_id': 6, 'qtty': 3},
            {'id_doc': '123', 'row_id': 6, 'qtty': 4},
            {'id_doc': '123', 'row_id': 6, 'qtty': -1}
        ]

        self.provider.insert_multiple(initial_data)
        sut = ScanningQueueService(provider=self.provider)
        result = sut.get_scanned_row_qtty(id_doc='123', row_id=6)
        self.assertEqual(result, 6)

    def test_get_send_document_lines(self):
        expect = [
            {
                "id_doc": '123',
                "id_good": 'id_good_value',
                "id_properties": 'id_property_value',
                "id_series": 'id_series_value',
                "d_qtty": 3,
                'row_key': '1',
                'sent': False
            },
            {
                "id_doc": '123',
                "id_good": 'id_good_value',
                "id_properties": 'id_property_value',
                "id_series": 'id_series_value',
                "d_qtty": 3,
                'row_key': '2',
                'sent': False
            }
        ]
        self.provider.insert_multiple(initial_data)
        sut = ScanningQueueService(provider=self.provider)
        result = sut.get_document_lines(id_doc='123', sent=False)

        self.assertEqual(expect, result)

    def test_get_all_document_lines(self):
        expect = [x for x in initial_data if x["id_doc"] == '123']
        self.provider.insert_multiple(initial_data)
        sut = ScanningQueueService(provider=self.provider)
        result = sut.get_document_lines(id_doc='123')

        self.assertEqual(expect, result)

    def test_update_sent(self):
        expect = 1

        self.provider.insert_multiple(initial_data)
        sut = ScanningQueueService(provider=self.provider)
        result = sut.get_document_lines(id_doc='123', sent=False)
        result.pop()  # Проверяем что меняет только в переданном списке (по doc_id)

        sut.update_sent_lines(result)

        new_result = sut.get_document_lines(id_doc='123', sent=False)
        self.assertEqual(expect, len(new_result))

    def test_must_remove_specific_doc_lines(self):
        expect = 0

        self.provider.insert_multiple(initial_data)
        sut = ScanningQueueService(provider=self.provider)

        sut.remove_doc_lines(id_doc='123')
        actual_123_lines = len(sut.get_document_lines(id_doc='123'))
        actual_124_lines = len(sut.get_document_lines(id_doc='124'))

        self.assertEqual(expect, actual_123_lines)
        self.assertGreater(actual_124_lines, 0)


class TestLoggerService(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = TinyNoSQLProvider(table_name='test_logger_table', base_name='TestLogger', db_path='./')
        self.provider.drop_table('test_logger_table')

    def tearDown(self) -> None:
        self.provider.close()

    def test_write_to_log(self):
        sut = LoggerService(provider=self.provider)
        sut.write_to_log(error_text="", error_type="SQL",
                         error_info="Комментарий к ошибке")
        self.assertEqual(sut.provider.count(error_type="SQL"), 1)

    def test_get_all_errors(self):
        sut = LoggerService(provider=self.provider)
        sut.write_to_log(error_text="", error_type="SQL",
                         error_info="Комментарий к ошибке")
        result = sut.get_all_errors(desc_sort=True)

        self.assertEqual(len(result), 1)

    def test_clear(self):
        sut = LoggerService(provider=self.provider)
        sut.write_to_log(error_text="", error_type="SQL",
                         error_info="Комментарий к ошибке")
        sut.clear()
        expect = 0

        result = sut.get_all_errors(desc_sort=True)

        self.assertEqual(expect, len(result))


class TestDateFormat(unittest.TestCase):

    def test_get_table_view_format(self):
        sut = DateFormat()
        date = "2023-10-17 07:52:18"
        expect = "2023-10-17 10:52:18"

        result = sut.get_table_view_format(date, user_tmz_offset='3')

        self.assertEqual(expect, result)