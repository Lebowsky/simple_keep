import json
import os
from unittest import TestCase

from tiny_db_services import NoSQLProvider
from tests.data_for_tests.nosql.initial_data import initial_data


class TestNoSQLProvider(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.nosql = NoSQLProvider('test_nosql')

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        if os.path.exists(cls.nosql.nosql.database_path):
            os.remove(cls.nosql.nosql.database_path)

    def tearDown(self) -> None:
        self.nosql.destroy()

    def test_put(self):
        self.assertEqual(self.nosql.get_all_keys(), '[]')
        self.nosql.put('1', 'Test_value')
        res = self.nosql.get('1')
        self.assertEqual(res, 'Test_value')
        self.assertEqual(self.nosql.get_all_keys(), '["1"]')
        self.nosql.put('2', 2)
        res = self.nosql.get('2')
        self.assertEqual(res, 2)
        self.assertEqual(self.nosql.get_all_keys(), '["1","2"]')
        self.nosql.put('3', True)
        res = self.nosql.get('3')
        self.assertEqual(res, True)
        self.assertEqual(self.nosql.get_all_keys(), '["1","2","3"]')
        with self.assertRaises(TypeError):
            self.nosql.put('4', ['1', '2'])
        with self.assertRaises(TypeError):
            self.nosql.put('4', b'123')
        with self.assertRaises(TypeError):
            self.nosql.put('4', {'1': '1'})
        with self.assertRaises(TypeError):
            self.nosql.put('4', ('1', '2'))
        with self.assertRaises(TypeError):
            self.nosql.put('4', None)
        with self.assertRaises(TypeError):
            self.nosql.put(1, '1')
        self.assertEqual(self.nosql.get_all_keys(), '["1","2","3"]')

    def test_delete(self):
        self.assertEqual(self.nosql.get_all_keys(), '[]')
        self.nosql.put('1', 'Test_value')
        self.nosql.put('2', 2)
        self.nosql.delete('1')
        self.assertEqual(self.nosql.get_all_keys(), '["2"]')
        self.nosql.delete('2')
        self.assertEqual(self.nosql.get_all_keys(), '[]')

    def test_find_json(self):
        first, second, third, fourth = initial_data
        self.nosql.put('1', json.dumps(first))
        self.nosql.put('2', json.dumps(second))
        self.nosql.put('3', json.dumps(third))
        self.nosql.put('4', json.dumps(fourth))

        self.assertEqual(self.nosql.get_all_keys(), '["1","2","3","4"]')
        res = self.nosql.find_json('row_key', '2')
        self.assertEqual(json.loads(res), [{'key': '2', 'value': json.dumps(second)},
                                           {'key': '3', 'value': json.dumps(third)}])

    def test_keys(self):
        self.nosql.put('1', 'Test_value')
        self.nosql.put('2', 'Test_value')
        self.assertEqual(self.nosql.keys(), ['1', '2'])

    def test_items(self):
        self.nosql.put('1', 'Test_value')
        self.nosql.put('2', 'Test_value')
        self.assertEqual(self.nosql.items(), [('1', 'Test_value'), ('2', 'Test_value')])

    def test_get_or_default(self):
        self.assertEqual(self.nosql.get('1', default='default'), 'default')
        self.nosql.put('1', 'Test_value')
        self.assertEqual(self.nosql.get('1', default='default'), 'Test_value')
        self.assertEqual(self.nosql.get('3', default={'default': 1}), {'default': 1})

    def test_get_from_json(self):
        first, *_ = initial_data
        self.nosql.put('1', json.dumps(first))
        self.assertEqual(self.nosql.get('1', from_json=True), first)
        self.nosql.get('3', from_json=True)
        self.assertEqual(self.nosql.get('3', from_json=True), None)

    def test_put_to_json(self):
        first, *_ = initial_data
        self.nosql.put('1', first, to_json=True)
        self.assertEqual(self.nosql.get('1'), json.dumps(first))
        with self.assertRaises(TypeError):
            self.nosql.put('2', {1, 2, 3}, to_json=True)
