import unittest
import json

import db_models


class TestDbModels(unittest.TestCase):
    def test_can_create_doc_model_from_json(self):
        data = self.get_doc_data()
        db_models.Doc(**data)


    def get_doc_data(self):
        with open('../../_tests/test_files/5_docs.json', encoding='utf-8') as f:
            docs_data = json.load(f)

        doc_data = docs_data['data']['RS_docs'][0]
        goods = [item for item in docs_data['data']['RS_docs_table'] if item['id_doc'] == doc_data['id_doc']]
        doc_data['goods'] = goods

        return doc_data

