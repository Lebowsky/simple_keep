import unittest
from tinydb import TinyDB
from tiny_db_services import TinyNoSQLProvider


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


