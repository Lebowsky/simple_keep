import unittest
import json
import os

from db_services import DocService, DbCreator


class TestDocService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = DocService()
        self.http_results_path = './tests_db_services/http_result_data_example'
        self.sqlite_filename = 'rightscan5.db'

        if os.path.exists(self.sqlite_filename):
            os.remove(self.sqlite_filename)

    def test_load_data(self):
        nsi_data = self.get_data_from_file('get_nsi_data_example.json')
        doc_data = self.get_data_from_file('get_doc_data_example.json')

        service = DbCreator()
        service.create_tables()

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


    def get_data_from_file(self, file_name):
        with open(f'{self.http_results_path}/{file_name}', encoding='utf-8') as fp:
            return json.load(fp)
