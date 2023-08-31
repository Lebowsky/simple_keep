import unittest
import json
import os

from db_services import DocService, DbCreator, TimerService, DbService, SqlQueryProvider, GoodsService, get_query_result


class TestDocService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = DocService()
        self.http_results_path = './tests_db_services/http_result_data_example'
        self.sqlite_filename = 'rightscan5.db'


        service = DbCreator()
        service.drop_all_tables()
        service.create_tables()

    def test_load_data(self):
        nsi_data = self.get_data_from_file('get_nsi_data_example.json')
        doc_data = self.get_data_from_file('get_doc_data_example.json')

        self.service.update_data_from_json(nsi_data)
        self.service.update_data_from_json(doc_data)

    def test_json_to_sqlite_query_goods(self):
        data = self.get_data_from_file('goods_data_example.json')
        for item in data['RS_goods']:
            actual = self.service.json_to_sqlite_query({'RS_goods': [item]})
            expected = [
                'REPLACE INTO RS_goods (id, code, name, art, unit, type_good) VALUES ("{}", "{}", "{}", "{}", "{}", "{}")'.format(
                    item['id'], item['code'], item['name'], item['art'], item['unit'], item['type_good']
                )
            ]
            self.assertEqual(expected, actual)

    @unittest.skip
    def test_json_to_sqlite_query_document(self):
        data = self.get_data_from_file('get_doc_data_example.json')

        values = ','.join(
            ['("{}", "{}", "{}", "{}", "{}", "{}", "{}", {}, {}, {})'.format(*item.values()) for item in
             data['RS_docs_table']])
        expected = [
            'REPLACE INTO RS_docs '
            '(id_doc, doc_type, doc_n, doc_date, id_countragents, id_warehouse, control, verified) '
            'VALUES ("{}", "{}", "{}", "{}", "{}", "{}", "{}", 0)'.format(
                data['RS_docs'][0]['id_doc'],
                data['RS_docs'][0]['doc_type'],
                data['RS_docs'][0]['doc_n'],
                data['RS_docs'][0]['doc_date'],
                data['RS_docs'][0]['id_countragents'],
                data['RS_docs'][0]['id_warehouse'],
                data['RS_docs'][0]['control'],
            ),

            'DELETE FROM RS_docs_table WHERE id_doc in ("{}") '.format(data['RS_docs'][0]['id_doc']),
            'REPLACE INTO RS_docs_table '
            '(id_doc, id_good, id_properties, id_series, id_unit, id_cell, id_price, price, qtty, qtty_plan) '
            f'VALUES {values}'
        ]

        actual = self.service.json_to_sqlite_query(data)
        self.assertEqual(expected, actual)

    def get_data_from_file(self, file_name):
        with open(f'{self.http_results_path}/{file_name}', encoding='utf-8') as fp:
            return json.load(fp)


class TestTimerService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = TimerService()
        self.data_creator = DataCreator()
        self.http_results_path = './tests_db_services/http_result_data_example'

        service = DbCreator()
        service.drop_all_tables()
        service.create_tables()

    def test_save_load_data(self):
        # TODO create test
        pass

    def get_data_from_file(self, file_name):
        with open(f'{self.http_results_path}/{file_name}', encoding='utf-8') as fp:
            return json.load(fp)

    def test_get_data_to_send(self):
        self.data_creator.insert_data(*list(self.data_creator.samples.keys()))

        actual = self.service.get_data_to_send()
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), 2)

        self.assertIsNotNone((actual[0].get('RS_docs_table')))
        self.assertTrue(actual[0]['RS_docs_table'])

        self.assertIsNotNone((actual[0].get('RS_docs_barcodes')))
        self.assertTrue(actual[0]['RS_docs_barcodes'])

        self.assertIsNotNone((actual[0].get('RS_barc_flow')))
        self.assertTrue(actual[0]['RS_barc_flow'])

        self.assertIsNotNone((actual[1].get('RS_adr_docs_table')))
        self.assertTrue(actual[1]['RS_adr_docs_table'])


class TestDbService(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_write_error_log(self):
        sut = DbService()
        sut._write_error_on_log('123')
        self.assertEqual('INSERT INTO Error_log (log) VALUES (?)', sut.sql_text)
        self.assertEqual([["123"]], json.loads(sut.sql_params))


class TestSQLQueryProvider(unittest.TestCase):
    service = SqlQueryProvider

    def tests_convert_sql_params(self):
        # Test 1

        query = "SELECT * FROM users WHERE name = :name AND age = :age"

        params = {"name": "John", "age": 30}

        new_query, param_values = self.service.convert_sql_params(query, params)

        assert new_query == "SELECT * FROM users WHERE name = ? AND age = ?"

        assert param_values == ["John", 30]

        # Test 2

        query = "INSERT INTO users (name, age) VALUES (:name, :age)"

        params = {"name": "Jane", "age": 25}

        new_query, param_values = self.service.convert_sql_params(query, params)

        assert new_query == "INSERT INTO users (name, age) VALUES (?, ?)"

        assert param_values == ["Jane", 25]

        # Test 3

        query = "UPDATE users SET name = :name, age = :age WHERE id = :id"

        params = {"name": "Alice", "age": 20, "id": 1}

        new_query, param_values = self.service.convert_sql_params(query, params)

        assert new_query == "UPDATE users SET name = ?, age = ? WHERE id = ?"

        assert param_values == ["Alice", 20, 1]

        query = '''
        SELECT
            RS_adr_docs_table.id,
            RS_adr_docs_table.id_doc,
            RS_adr_docs_table.id_good,
            ifnull(RS_goods.name, :NullValue) as good_name,
            ifnull(RS_goods.code, :EmptyString) as code,
            ifnull(RS_goods.art, :EmptyString) as art,
            ifnull(RS_adr_docs_table.id_properties, :EmptyString) as id_properties,
            ifnull(RS_properties.name, :EmptyString) as properties_name,
            ifnull(RS_adr_docs_table.id_series, :EmptyString) as id_series,
            ifnull(RS_series.name, :EmptyString) as series_name,
            ifnull(RS_adr_docs_table.id_unit, :EmptyString) as id_unit,
            ifnull(RS_units.name, :EmptyString) as units_name,
            RS_adr_docs_table.qtty as qtty,
            RS_adr_docs_table.qtty_plan as qtty_plan,
            RS_adr_docs_table.qtty_plan - RS_adr_docs_table.qtty as IsDone,
            ifnull(RS_adr_docs_table.id_cell, :EmptyString) as id_cell,
            ifnull(RS_cells.name, :NullValue) as cell_name


            FROM RS_adr_docs_table 

            LEFT JOIN RS_goods 
            ON RS_goods.id=RS_adr_docs_table.id_good
            LEFT JOIN RS_properties
            ON RS_properties.id = RS_adr_docs_table.id_properties
            LEFT JOIN RS_series
            ON RS_series.id = RS_adr_docs_table.id_series
            LEFT JOIN RS_units
            ON RS_units.id=RS_adr_docs_table.id_unit
            LEFT JOIN RS_cells
            ON RS_cells.id=RS_adr_docs_table.id_cell

            WHERE id_doc = :id_doc and table_type = :table_type

             ORDER BY RS_cells.name, RS_adr_docs_table.last_updated DESC'''
        params = {'NullValue': None, 'EmptyString': '', 'table_type': 'out',
                  'id_doc': '773c92ab-fd28-11e4-92f1-0050568b35ac'}

        new_query, param_values = self.service.convert_sql_params(query, params)

        assert new_query == '''
        SELECT
            RS_adr_docs_table.id,
            RS_adr_docs_table.id_doc,
            RS_adr_docs_table.id_good,
            ifnull(RS_goods.name, ?) as good_name,
            ifnull(RS_goods.code, ?) as code,
            ifnull(RS_goods.art, ?) as art,
            ifnull(RS_adr_docs_table.id_properties, ?) as id_properties,
            ifnull(RS_properties.name, ?) as properties_name,
            ifnull(RS_adr_docs_table.id_series, ?) as id_series,
            ifnull(RS_series.name, ?) as series_name,
            ifnull(RS_adr_docs_table.id_unit, ?) as id_unit,
            ifnull(RS_units.name, ?) as units_name,
            RS_adr_docs_table.qtty as qtty,
            RS_adr_docs_table.qtty_plan as qtty_plan,
            RS_adr_docs_table.qtty_plan - RS_adr_docs_table.qtty as IsDone,
            ifnull(RS_adr_docs_table.id_cell, ?) as id_cell,
            ifnull(RS_cells.name, ?) as cell_name


            FROM RS_adr_docs_table 

            LEFT JOIN RS_goods 
            ON RS_goods.id=RS_adr_docs_table.id_good
            LEFT JOIN RS_properties
            ON RS_properties.id = RS_adr_docs_table.id_properties
            LEFT JOIN RS_series
            ON RS_series.id = RS_adr_docs_table.id_series
            LEFT JOIN RS_units
            ON RS_units.id=RS_adr_docs_table.id_unit
            LEFT JOIN RS_cells
            ON RS_cells.id=RS_adr_docs_table.id_cell

            WHERE id_doc = ? and table_type = ?

             ORDER BY RS_cells.name, RS_adr_docs_table.last_updated DESC'''

        assert param_values == [None, '', '', '', '', '', '', '', '', '', None, '773c92ab-fd28-11e4-92f1-0050568b35ac',
                                'out']


class DataCreator:
    def __init__(self):
        self.samples = {
            'RS_docs': {
                'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'doc_type': '""',
                'doc_n': '""',
                'doc_date': '""',
                'id_countragents': '""',
                'id_warehouse': '""',
                'verified': '1',
                'sent': '0'
            },
            'RS_adr_docs': {
                'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'doc_type': '""',
                'doc_n': '""',
                'doc_date': '""',
                'id_warehouse': '""',
                'verified': '1',
                'sent': '0'
            },
            'RS_docs_table': {
                'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_good': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_properties': '""',
                'id_series': '""',
                'id_unit': '""',
                'qtty': '1',
                'qtty_plan': '5',
                'sent': '0'
            },
            'RS_adr_docs_table': {
                'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_good': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_properties': '""',
                'id_series': '""',
                'id_unit': '""',
                'id_cell': '""',
                'table_type': '"in"',
                'qtty': '1',
                'qtty_plan': '5',
                'sent': '0'
            },
            'RS_docs_barcodes': {
                'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_good': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_property': '""',
                'id_series': '""',
                'id_unit': '""',
                'barcode_from_scanner': '"07623900408085tEjE+7qAAAAXi6n"',
                'GTIN': '"07623900408085"',
                'Series': '"tEjE+7q"'
            },
            'RS_barc_flow': {
                'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'barcode': '"4680134840398"',
            }
        }

    def insert_data(self, *args):
        for arg in args:
            q = 'INSERT INTO {} ({}) VALUES({})'.format(
                arg,
                ','.join(self.samples[arg].keys()),
                ','.join(self.samples[arg].values())
            )
            get_query_result(q)

