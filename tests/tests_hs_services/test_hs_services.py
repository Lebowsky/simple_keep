import unittest
import json

from hs_services import HsService
from main import noClass


class TestHsService(unittest.TestCase):
    def setUp(self) -> None:
        self.rs_settings = noClass('rs_settings_local')
        self.http_settings = self.get_http_settings()
        self.service = HsService(self.http_settings)
        self.path = './tests_hs_services/http_result_data'

    def test_setup(self):
        self.assertIsNotNone(self.http_settings.get('url'))

    def test_communication_test(self):
        res = self.service.communication_test()
        self.assertEqual(self.service.http_answer.status_code, 200)

    def test_reset_exchange(self):
        self.service.reset_exchange()
        res = self.service.http_answer
        self.assertEqual(res.status_code, 200)

    def test_get_document_lines(self):
        id_doc = '37c4c709-d22b-11e4-869d-0050568b35ac'
        res = self.service.get_document_lines(id_doc)
        print(res)

    def test_send_document_lines(self):
        data = [{
            "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
            "id_good": "cbcf493f-55bc-11d9-848a-00112f43529a",
            "id_properties": "",
            "id_series": "",
            "id_unit": "",
            "id_cell": "",
            "d_qtty": 1
        }]

        res = self.service.send_document_lines(
            id_doc='37c4c709-d22b-11e4-869d-0050568b35ac',
            data=data
        )
        print(res)

    @unittest.skip
    def test_get_balances_goods_id_good_only(self):
        data = [
            {
                "id_good": "f93e113e-c83a-11e2-8026-0015e9b8c48d",
                "id_property": None,
                "id_warehouse": "6f87e83f-722c-11df-b336-0011955cba6b",
                "id_series": None,
                "qtty": 800
            },
            {
                "id_good": "f93e113e-c83a-11e2-8026-0015e9b8c48d",
                "id_property": None,
                "id_warehouse": "a4212b46-730a-11df-b338-0011955cba6b",
                "id_series": None,
                "qtty": 600
            }
        ]

        res = self.service.get_balances_goods(id_good='f93e113e-c83a-11e2-8026-0015e9b8c48d')
        print(res)

    @unittest.skip
    def test_get_data(self):
        self.service.reset_exchange()
        self.assertEqual(self.service.http_answer.status_code, 200)

        self.service.get_data()
        data = self.service.http_answer.data
        self.assertIsNotNone(data)

        self.save_to_json(data, 'get_nsi_data')

    @unittest.skip
    def test_get_document_data(self):
        self.service.get_data()
        data = self.service.http_answer.data
        self.assertIsNotNone(data)

        self.save_to_json(data, 'get_doc_data')

    def get_http_settings(self):
        http_settings = {
            'url': self.rs_settings.get("URL"),
            'user': self.rs_settings.get('USER'),
            'pass': self.rs_settings.get('PASS'),
            'device_model': self.rs_settings.get('DEVICE_MODEL'),
            'android_id': self.rs_settings.get('ANDROID_ID'),
            'user_name': self.rs_settings.get('user_name')}
        return http_settings

    def save_to_json(self, data, file_name='data'):
        with open(f'{self.path}/{file_name}.json', 'w', encoding='utf-8') as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)

