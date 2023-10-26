import unittest
import json
import os

from db_services import DocService, DbCreator, TimerService, DbService, SqlQueryProvider, GoodsService, \
    get_query_result, BarcodeService, FlowDocService, AdrDocService
from ui_utils import BarcodeParser


class TestDocService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = DocService()
        self.data_creator = DataCreator()
        self.http_results_path = './tests_db_services/http_result_data_example'
        self.sqlite_filename = 'rightscan5.db'

        service = DbCreator()
        service.drop_all_tables()
        service.create_tables()

    def get_data_from_file(self, file_name):
        with open(f'{self.http_results_path}/{file_name}', encoding='utf-8') as fp:
            return json.load(fp)

    def test_can_get_docs_stat_for_no_group_scan_docs(self):
        self.data_creator.insert_data('RS_docs', 'RS_docs_table')
        self.assertTrue(self.service.get_docs_stat())

    def test_get_only_docs_stat(self):
        self.data_creator.insert_data('RS_docs', 'RS_docs_table')

        result = self.service.get_docs_stat()
        for tile in result:
            docs_count = tile['count']
            doc_type = tile['docType']
            samples_docs_for_tile = [x for x in self.data_creator.samples['RS_docs']
                                     if x['is_group_scan'] == '0'
                                     and x['is_barc_flow'] == '0'
                                     and x['doc_type'] == f'"{doc_type}"']

            self.assertEqual(len(samples_docs_for_tile), docs_count)

    def test_get_only_barc_flow_stat(self):
        self.data_creator.insert_data('RS_docs', 'RS_docs_table')

        result = self.service.get_doc_flow_stat()
        docs = []
        id = '"37c4c709-d22b-11e4-869d-0050568b35ac2"'
        doc = self.data_creator.samples['RS_docs'][1]
        for tile in result:
            docs_count = tile['count']
            doc_type = tile['docType']
            samples_docs_for_tile = [x for x in self.data_creator.samples['RS_docs']
                                     if x['is_group_scan'] == '0'
                                     and (x['is_barc_flow'] == '1' or not self.doc_has_lines(x['id_doc']))
                                     and x['doc_type'] == f'"{doc_type}"']
            docs.append(samples_docs_for_tile)

            self.assertEqual(len(samples_docs_for_tile), docs_count)

    def test_can_get_doc_view_data_if_no_group_scan(self):
        self.data_creator.insert_data('RS_docs', 'RS_docs_table')
        self.assertTrue(self.service.get_doc_view_data(doc_status='К выгрузке', doc_type='Заказ'))

    def test_can_get_docs_stat_for_group_scan_docs(self):
        self.data_creator.insert_data('RS_docs', 'RS_docs_table')
        self.service.is_group_scan = True

        result = self.service.get_docs_stat()

        self.assertTrue(result)

    def test_can_get_doc_view_data_if_group_scan(self):
        self.data_creator.insert_data('RS_docs', 'RS_docs_table')
        self.service.is_group_scan = True
        self.assertTrue(self.service.get_doc_view_data(doc_status='К выгрузке', doc_type='Заказ'))

    def test_get_correct_documents_doc_types(self):
        self.data_creator.insert_data('RS_docs', 'RS_docs_table')
        self.service.docs_table_name = 'RS_docs'
        self.service.is_group_scan = False
        self.service.is_barc_flow = False
        expect = [x['doc_type'] for x in self.data_creator.samples['RS_docs'] if
                  x['is_group_scan'] == '0' and x['is_barc_flow'] == '0']

        result = [f'"{x}"' for x in self.service.get_doc_types()]

        self.assertListEqual(expect, result)

    def test_get_correct_group_scan_doc_types(self):
        self.data_creator.insert_data('RS_docs', 'RS_docs_table')
        self.service.is_group_scan = True
        self.service.docs_table_name = 'RS_docs'
        expect = [x['doc_type'] for x in self.data_creator.samples['RS_docs']
                  if x['is_barc_flow'] == '0']

        result = [f'"{x}"' for x in self.service.get_doc_types()]

        self.assertListEqual(expect, result)

    def test_get_correct_barc_flow_doc_types(self):
        self.data_creator.insert_data('RS_docs', 'RS_docs_table')
        self.service.is_group_scan = False
        self.service.is_barc_flow = True
        self.service.docs_table_name = 'RS_docs'

        expect = [x['doc_type'] for x in self.data_creator.samples['RS_docs']
                  if (x['is_barc_flow'] == '1' or not self.doc_has_lines(x['id_doc']))
                  and x['is_group_scan'] == '0']

        result = [f'"{x}"' for x in self.service.get_doc_types()]

        self.assertListEqual(expect, result)

    def test_clear_barcode_data_nulify_is_group_scan(self):
        self.data_creator.insert_data('RS_docs', 'RS_docs_table')
        self.service.is_group_scan = True
        expect = '0'

        id_doc = '37c4c709-d22b-11e4-869d-0050568b35ac2'
        self.service.clear_barcode_data(id_doc)
        result_doc = [x for x in self.service.get_doc_view_data() if x['id_doc'] == id_doc][0]
        self.assertEqual(expect, result_doc['is_group_scan'])

    def test_clear_barcode_data_nulify_is_barc_flow(self):
        self.data_creator.insert_data('RS_docs', 'RS_docs_table')
        self.service = FlowDocService()
        expect = '0'

        id_doc = '37c4c709-d22b-11e4-869d-0050568b35ac3'
        self.service.clear_barcode_data(id_doc)
        result_doc = [x for x in self.service.get_doc_view_data() if x['id_doc'] == id_doc][0]
        self.assertEqual(expect, result_doc['is_barc_flow'])

    def test_get_doc_details_rows_count(self):
        self.data_creator.insert_data('RS_docs', 'RS_docs_table')
        id_doc = '37c4c709-d22b-11e4-869d-0050568b35ac1'
        expect_count = len(self.get_lines_by_field_value('id_doc', id_doc))

        actual_count = self.service.get_doc_details_rows_count(id_doc)

        self.assertEqual(expect_count, actual_count)

    def doc_has_lines(self, doc_id):
        result = [x for x in self.data_creator.samples['RS_docs_table'] if x['id_doc'] == doc_id]
        return True if result else False

    def get_lines_by_field_value(self, field, value):
        result = [x for x in self.data_creator.samples['RS_docs_table'] if x[field] == f'"{value}"']
        return result

    def test_write_error_on_log(self):
        self.service.write_error_on_log(
            error_type="HS_service",
            error_text="",
            error_info='Ошибка соединения при отправке'
        )
class TestAdrDocService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = AdrDocService()
        self.data_creator = DataCreator()

        service = DbCreator()
        service.drop_all_tables()
        service.create_tables()

    def test_must_get_all_docs(self):
        self.data_creator.insert_data('RS_adr_docs')

        res = self.service.get_doc_view_data()
        self.assertTrue(res)

    def test_must_get_only_to_send_docs(self):
        self.data_creator.insert_data('RS_adr_docs')

        res = self.service.get_doc_view_data(doc_status='К выгрузке')
        self.assertTrue(res)


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
        self.assertEqual(len(actual), self.get_count_docs_to_send_from_samples())

        self.assertIsNotNone((actual[0].get('RS_docs_table')))
        self.assertTrue(actual[0]['RS_docs_table'])

        self.assertIsNotNone((actual[0].get('RS_docs_barcodes')))
        self.assertTrue(actual[0]['RS_docs_barcodes'])

        self.assertIsNotNone((actual[0].get('RS_barc_flow')))
        self.assertTrue(actual[0]['RS_barc_flow'])

        first_adr_doc_index = self.get_count_docs_to_send_from_samples(is_adr_doc=False)

        self.assertIsNotNone((actual[first_adr_doc_index].get('RS_adr_docs_table')))
        self.assertTrue(actual[first_adr_doc_index]['RS_adr_docs_table'])

    def get_count_docs_to_send_from_samples(self, is_adr_doc=None):
        if is_adr_doc is True:
            all_docs_pull = self.data_creator.samples['RS_adr_docs']
        elif is_adr_doc is False:
            all_docs_pull = self.data_creator.samples['RS_docs']
        else:
            all_docs_pull = self.data_creator.samples['RS_docs'] + self.data_creator.samples['RS_adr_docs']
        result = [x for x in all_docs_pull if x['sent'] == '0' and x['verified'] == '1']
        return len(result)


class TestDbService(unittest.TestCase):
    def setUp(self) -> None:
        pass

    @unittest.skip
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


class TestBarcodeService(unittest.TestCase):
    def setUp(self) -> None:
        self.data_creator = DataCreator()

        service = DbCreator()
        service.drop_all_tables()
        service.create_tables()

    def test_must_getting_barcode_data_ean13(self):
        self.data_creator.insert_data('RS_barcodes')
        barcode_info = BarcodeParser.BarcodeInfo(
            barcode='2000000025988',
            gtin='',
            serial=''
        )
        id_doc = '37c4c709-d22b-11e4-869d-0050568b35ac1'

        sut = BarcodeService()
        expect = {
            'id_good': '37c4c709-d22b-11e4-869d-0050568b35ac1',
            'id_property': '',
            'id_series': '',
            'id_unit': '',
            'mark_id': 0,
            'id_price': '',
            'price': 0.0,
            'ratio': 1,
            'approved': 0,
            'use_mark': 0,
            'row_key': '',
            'use_series': 0,
            'd_qtty': 0.0,
            'qtty': 0.0,
            'qtty_plan': 0.0,
        }

        actual = sut.get_barcode_data(barcode_info, id_doc)

        self.assertEqual(expect, actual)

    def test_must_getting_barcode_data_ean13_and_get_doc_key(self):
        self.data_creator.insert_data('RS_barcodes', 'RS_docs_table')
        barcode_info = BarcodeParser.BarcodeInfo(
            barcode='2000000025988',
            gtin='',
            serial=''
        )
        id_doc = '37c4c709-d22b-11e4-869d-0050568b35ac1'

        sut = BarcodeService()
        expect = {
            'id_good': '37c4c709-d22b-11e4-869d-0050568b35ac1',
            'id_property': '',
            'id_series': '',
            'id_unit': '',
            'mark_id': 0,
            'id_price': '',
            'price': 0.0,
            'ratio': 1,
            'approved': 0,
            'use_mark': 0,
            'row_key': 1,
            'use_series': 0,
            'd_qtty': 0.0,
            'qtty': 1.0,
            'qtty_plan': 5.0,
        }

        actual = sut.get_barcode_data(barcode_info, id_doc)

        self.assertEqual(expect, actual)

    def test_must_getting_barcode_data_ean13_with_mark(self):
        self.data_creator.insert_data('RS_barcodes', 'RS_docs_table', 'RS_docs_barcodes')
        barcode_info = BarcodeParser.BarcodeInfo(
            barcode='2000000025988',
            gtin='07623900408085',
            serial='tEjE+7q'
        )
        id_doc = '37c4c709-d22b-11e4-869d-0050568b35ac1'

        sut = BarcodeService()
        expect = {
            'id_good': '37c4c709-d22b-11e4-869d-0050568b35ac1',
            'id_property': '',
            'id_series': '',
            'id_unit': '',
            'mark_id': 3,
            'id_price': '',
            'price': 0.0,
            'ratio': 1,
            'approved': 0,
            'use_mark': 0,
            'row_key': 1,
            'use_series': 0,
            'qtty': 1.0,
            'd_qtty': 0.0,
            'qtty_plan': 5.0,
        }

        actual = sut.get_barcode_data(barcode_info, id_doc)

        self.assertEqual(expect, actual)

    def test_must_getting_barcode_data_ean13_with_mark_use_adr_doc_table(self):
        self.data_creator.insert_data('RS_barcodes', 'RS_adr_docs_table', 'RS_docs_barcodes')
        barcode_info = BarcodeParser.BarcodeInfo(
            barcode='2000000025988',
            gtin='07623900408085',
            serial='tEjE+7q'
        )
        id_doc = '37c4c709-d22b-11e4-869d-0050568b35ac1'

        sut = BarcodeService()
        expect = {
            'id_good': '37c4c709-d22b-11e4-869d-0050568b35ac1',
            'id_property': '',
            'id_series': '',
            'id_unit': '',
            'mark_id': 3,
            'id_price': '',
            'price': 0.0,
            'ratio': 1,
            'approved': 0,
            'use_mark': 0,
            'row_key': 1,
            'use_series': 0,
            'qtty': 1.0,
            'd_qtty': 1.0,
            'qtty_plan': 5.0,
        }

        actual = sut.get_barcode_data(
            barcode_info, id_doc, is_adr_doc=True, id_cell='some_cell', table_type='in')

        self.assertEqual(expect, actual)

    def test_must_getting_barcode_data_ean13_use_mark(self):
        self.data_creator.insert_data('RS_barcodes', 'RS_docs_table', 'RS_goods', 'RS_types_goods')
        barcode_info = BarcodeParser.BarcodeInfo(
            barcode='2000000025988',
            gtin='',
            serial=''
        )
        id_doc = '37c4c709-d22b-11e4-869d-0050568b35ac1'

        sut = BarcodeService()
        expect = {
            'id_good': '37c4c709-d22b-11e4-869d-0050568b35ac1',
            'id_property': '',
            'id_series': '',
            'id_unit': '',
            'mark_id': 0,
            'id_price': '',
            'price': 0.0,
            'ratio': 1,
            'approved': 0,
            'use_mark': 1,
            'row_key': 1,
            'use_series': 0,
            'qtty': 1.0,
            'd_qtty': 0.0,
            'qtty_plan': 5.0,
        }

        actual = sut.get_barcode_data(barcode_info, id_doc)

        self.assertEqual(expect, actual)

    def test_get_table_line_success(self):
        self.data_creator.insert_data('RS_docs_table')
        filters = {
            'id_doc': '37c4c709-d22b-11e4-869d-0050568b35ac1',
            'id_good': '37c4c709-d22b-11e4-869d-0050568b35ac1',
            'id_properties': '',
            'id_unit': ''
        }

        expect = {'id': 1, 'id_doc': '37c4c709-d22b-11e4-869d-0050568b35ac1',
                  'id_good': '37c4c709-d22b-11e4-869d-0050568b35ac1',
                  'id_properties': '', 'id_series': '', 'id_unit': '',
                  'qtty': 1.0, 'd_qtty': None, 'qtty_plan': 5.0, 'price': None,
                  'id_price': None, 'sent': 0,
                  'is_plan': 'True', 'id_cell': None, 'use_series': 0}

        sut = BarcodeService()
        actual = sut.get_table_line(table_name='RS_docs_table', filters=filters)
        del actual['last_updated']

        self.assertEqual(expect, actual)

    def test_get_table_line_empty(self):
        self.data_creator.insert_data('RS_docs_table')
        filters = {
            'id_doc': '37c4c709-d22b-11e4-869d-0050568b35ac1',
            'id_good': '37c4c709-d22b-11e4-869d-0050568b35ac1',
            'id_properties': 'sssssssssssss',
            'id_unit': ''
        }

        sut = BarcodeService()
        actual = sut.get_table_line(table_name='RS_docs_table', filters=filters)

        self.assertIsNone(actual)


class TestFlowDocService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = FlowDocService()
        self.data_creator = DataCreator()
        self.http_results_path = './tests_db_services/http_result_data_example'
        self.sqlite_filename = 'rightscan5.db'

        service = DbCreator()
        service.drop_all_tables()
        service.create_tables()

    def test_set_bark_flow_status(self):
        self.data_creator.insert_data('RS_docs')
        self.service.doc_id = '37c4c709-d22b-11e4-869d-0050568b35ac1'
        self.service.set_barc_flow_status()
        result = self.service.get_doc_view_data()
        self.assertEqual(result[0].get('is_barc_flow'), '1')

    def test_get_doc_view_data(self):
        self.data_creator.insert_data('RS_docs', 'RS_docs_table')
        self.service.doc_id = '37c4c709-d22b-11e4-869d-0050568b35ac1'
        expect = '"37c4c709-d22b-11e4-869d-0050568b35ac1"'

        result_docs_list = self.service.get_doc_view_data(doc_type='Заказ')

        result_flow_values = ['1' if not self.doc_has_lines(expect)
                              else x['is_barc_flow'] for x in result_docs_list]

        self.assertNotIn('0', result_flow_values)

    def doc_has_lines(self, doc_id):
        result = [x for x in self.data_creator.samples['RS_docs_table'] if x['id_doc'] == doc_id]
        return True if result else False


class DataCreator:
    def __init__(self):
        self.samples = {
            'RS_docs': [
                {
                    'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                    'doc_type': '"Заказ"',
                    'doc_n': '""',
                    'doc_date': '""',
                    'id_countragents': '""',
                    'id_warehouse': '""',
                    'verified': '1',
                    'sent': '0',
                    'is_group_scan': '0',
                    'is_barc_flow': '0'
                },
                {
                    'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac2"',
                    'doc_type': '"Тип2"',
                    'doc_n': '""',
                    'doc_date': '""',
                    'id_countragents': '""',
                    'id_warehouse': '""',
                    'verified': '1',
                    'sent': '0',
                    'is_group_scan': '1',
                    'is_barc_flow': '0'
                },
                {
                    'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac3"',
                    'doc_type': '"Тип3"',
                    'doc_n': '""',
                    'doc_date': '""',
                    'id_countragents': '""',
                    'id_warehouse': '""',
                    'verified': '0',
                    'sent': '0',
                    'is_group_scan': '0',
                    'is_barc_flow': '1'
                }
            ],
            'RS_adr_docs': [{
                'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'doc_type': '""',
                'doc_n': '""',
                'doc_date': '""',
                'id_warehouse': '""',
                'verified': '1',
                'sent': '0'
            }],
            'RS_docs_table': [{
                'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_good': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_properties': '""',
                'id_series': '""',
                'id_unit': '""',
                'qtty': '1',
                'qtty_plan': '5',
                'sent': '0',
                'use_series': '0'
            }],
            'RS_adr_docs_table': [{
                'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_good': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_properties': '""',
                'id_series': '""',
                'id_unit': '""',
                'id_cell': '"some_cell"',
                'table_type': '"in"',
                'qtty': '1',
                'qtty_plan': '5',
                'sent': '0',
                'use_series': '0'
            }],
            'RS_docs_barcodes': [{
                'id': '3',
                'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_good': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_property': '""',
                'id_series': '""',
                'id_unit': '""',
                'barcode_from_scanner': '"07623900408085tEjE+7qAAAAXi6n"',
                'approved': '0',
                'GTIN': '"07623900408085"',
                'Series': '"tEjE+7q"',
                'mark_code': '""'
            }],
            'RS_barc_flow': [{
                'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'barcode': '"4680134840398"',
            }],
            'RS_barcodes': [{
                'barcode': '"2000000025988"',
                'id_good': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_property': '""',
                'id_series': '""',
                'id_unit': '""',
                'ratio': '1'
            }],
            'RS_goods': [{
                'id': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'type_good': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'code': '""',
                'name': '"item_name"'
            }],
            'RS_types_goods': [{
                'id': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'name': '"type_name"',
                'use_mark': '1'
            }]
        }

    def insert_data(self, *args):
        for arg in args:
            values = [','.join(item.values()) for item in self.samples[arg]]
            q = 'INSERT INTO {} ({}) VALUES {}'.format(
                arg,
                ','.join(self.samples[arg][0].keys()),
                ','.join(['({})'.format(value) for value in values])
            )
            get_query_result(q)
