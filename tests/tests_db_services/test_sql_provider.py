import json
import unittest
from unittest.mock import MagicMock

from db_services import SqlQueryProvider


class TestSqlQueryProvider(unittest.TestCase):
    def setUp(self) -> None:
        self.sut = SqlQueryProvider()
        self.sut.debug = True

    # @unittest.skip
    def test_check_exception_value_error_on_call_public_methods(self):
        sut = SqlQueryProvider(debug=True)
        test_data = [{'1': '1', '2': '2'}]
        with self.assertRaises(ValueError) as context:
            sut.create(test_data)
            sut.replace(test_data)
            sut.update(test_data)
            sut.delete(test_data)
            sut.select(test_data)

        self.assertEqual(context.exception.args[0], 'table_name must be specified')

    def test_create(self):
        sut = SqlQueryProvider(debug=True)
        sut.table_name = 'table'

        data = {'id': 'id_5', 'id_doc': 'id_doc_5', 'qtty': 5, 'price': '500'}
        sut.create(data)

        expect = 'INSERT INTO table (id, id_doc, qtty, price) VALUES (?,?,?,?)'
        actual = sut.sql_text
        self.assertEqual(expect, actual)

        expect = json.dumps([['id_5', 'id_doc_5', 5, '500']])
        actual = sut.sql_params
        self.assertEqual(expect, actual)

        data = [
            {'id': 'id_5', 'id_doc': 'id_doc_5', 'qtty': 5, 'price': '500'},
            {'id': 'id_5', 'id_doc': 'id_doc_5', 'qtty': 5, 'price': '500'}
        ]
        sut.create(data)

        expect = 'INSERT INTO table (id, id_doc, qtty, price) VALUES (?,?,?,?)'
        actual = sut.sql_text
        self.assertEqual(expect, actual)

        expect = json.dumps([['id_5', 'id_doc_5', 5, '500'], ['id_5', 'id_doc_5', 5, '500']])
        actual = sut.sql_params
        self.assertEqual(expect, actual)

    def test_replace(self):
        # TODO AND create test
        pass

    def test_update(self):
        sut = SqlQueryProvider(debug=True)
        sut.table_name = 'table'

        ## data dict
        data = {'id': 'id_5', 'id_doc': 'id_doc_5', 'qtty': 5, 'price': '500'}
        sut.update(data)

        expect = 'UPDATE table SET id=?, id_doc=?, qtty=?, price=? WHERE true'
        actual = sut.sql_text
        self.assertEqual(expect, actual)

        expect = json.dumps([['id_5', 'id_doc_5', 5, '500']])
        actual = sut.sql_params
        self.assertEqual(expect, actual)

        ## data list[dict]
        data = [
            {'id': 'id_5', 'id_doc': 'id_doc_5', 'qtty': 5, 'price': '500'},
            {'id': 'id_5', 'id_doc': 'id_doc_5', 'qtty': 5, 'price': '500'}
        ]
        sut.update(data)

        expect = 'UPDATE table SET id=?, id_doc=?, qtty=?, price=? WHERE true'
        actual = sut.sql_text
        self.assertEqual(expect, actual)

        expect = json.dumps([['id_5', 'id_doc_5', 5, '500'], ['id_5', 'id_doc_5', 5, '500']])
        actual = sut.sql_params
        self.assertEqual(expect, actual)

        ## data list[dict], filter
        sut.update(data, {'id': 'id_5', 'id_doc': 'id_doc_5'})

        expect = 'UPDATE table SET id=?, id_doc=?, qtty=?, price=? WHERE id=? and id_doc=?'
        actual = sut.sql_text
        self.assertEqual(expect, actual)

        expect = json.dumps([['id_5', 'id_doc_5', 5, '500', 'id_5', 'id_doc_5'], ['id_5', 'id_doc_5', 5, '500', 'id_5', 'id_doc_5']])
        actual = sut.sql_params
        self.assertEqual(expect, actual)


    def test_delete(self):
        sut = SqlQueryProvider(debug=True)
        sut.table_name = 'table'

        ## No filter
        sut.delete()

        expect = 'DELETE FROM table WHERE true'
        actual = sut.sql_text
        self.assertEqual(expect, actual)

        expect = json.dumps([[]])
        actual = sut.sql_params
        self.assertEqual(expect, actual)


        ## filter dict
        data = {'id': 'id_5', 'id_doc': 'id_doc_5'}
        sut.delete(data)

        expect = 'DELETE FROM table WHERE id=? and id_doc=?'
        actual = sut.sql_text
        self.assertEqual(expect, actual)

        expect = json.dumps([['id_5', 'id_doc_5']])
        actual = sut.sql_params
        self.assertEqual(expect, actual)

    def test_select(self):
        # TODO AND create test
        pass
