import os
from typing import List, Union, Dict
from functools import reduce
from tinydb import TinyDB, Query, where

from java import jclass


noClass = jclass("ru.travelfood.simple_ui.NoSQL")
rs_settings = noClass("rs_settings")



class TinyNoSQLProvider:
    def __init__(self, table_name, base_name='SimpleKeep', db_path=''):
        self.table_name = table_name
        self.base_name = base_name or rs_settings.get('sqlite_name')
        self.db_path = db_path or rs_settings.get('path_to_databases')
        self.db = TinyDB(os.path.join(db_path, f'{base_name}.json'))
        self.table = self.db.table(self.table_name)
        self.query = Query()

    def drop_table(self, table_name):
        self.db.drop_table(table_name)

    def get_all(self) -> list:
        return self.table.all()

    def get(self, **cond) -> Union[Dict, None]:
        return self.table.get(cond=self._create_condition(**cond))

    def search(self, **cond) -> list:
        return self.table.search(cond=self._create_condition(**cond))

    def insert(self, data: dict) -> int:
        return self.table.insert(data)

    def insert_multiple(self, data: List[dict]) -> List[int]:
        return self.table.insert_multiple(data)

    def update(self, data: dict, **cond) -> List[int]:
        """
        delete(key): delete a key from the document
        increment(key): increment the value of a key
        decrement(key): decrement the value of a key
        add(key, value): add value to the value of a key (also works for strings)
        subtract(key, value): subtract value from the value of a key
        set(key, value): set key to value
        db.update(delete('key1'), User.name == 'John')
        db.update(your_operation(arguments), query)
        """

        return self.table.update(data, cond=self._create_condition(**cond))

    def upsert(self, data, **cond) -> List[int]:
        return self.table.upsert(data, cond=self._create_condition(**cond))

    def remove(self, **cond):
        self.table.remove(cond=self._create_condition(**cond))

    def contains(self, **cond):
        return self.table.contains(self._create_condition(**cond))

    def count(self, **cond):
        return self.table.count(self._create_condition(**cond))

    def close(self):
        self.db.close()

    def _create_condition(self, **cond) -> Query:
        conditions = [(self.query[key] == value) for key, value in cond.items()]
        return reduce(lambda a, b: a & b, conditions)



if __name__ == '__main__':
    provider = TinyNoSQLProvider(table_name='test_table', db_path='./')
    print(provider.insert({}))
    # data = {
    #     "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #     "doc_type": "Заказ поставщику",
    #     "doc_n": "ТД00-000008",
    #     "doc_date": "2017-03-03T18:12:48",
    #     "id_countragents": "63d65996-d51a-11df-aeac-0015e9b8c48d",
    #     "id_warehouse": "6f87e83f-722c-11df-b336-0011955cba6b",
    #     "control": "0",
    #     'goods': [
    #         {
    #             "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #             "id_good": "7b7230d4-9257-11e3-8058-0015e9b8c48d",
    #             "id_properties": "",
    #             "id_series": "",
    #             "id_unit": "",
    #             "id_cell": "",
    #             "id_price": "",
    #             "price": 2300,
    #             "qtty": 6,
    #             "qtty_plan": 6
    #         },
    #         {
    #             "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #             "id_good": "7b7230d4-9257-11e3-8058-0015e9b8c48d",
    #             "id_properties": "1b603c2a-6a59-11e8-91e9-14dae9b19a48",
    #             "id_series": "",
    #             "id_unit": "",
    #             "id_cell": "",
    #             "id_price": "",
    #             "price": 2300,
    #             "qtty": 999,
    #             "qtty_plan": 6
    #         },
    #         {
    #             "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #             "id_good": "7b7230d6-9257-11e3-8058-0015e9b8c48d",
    #             "id_properties": "",
    #             "id_series": "",
    #             "id_unit": "",
    #             "id_cell": "",
    #             "id_price": "",
    #             "price": 2400,
    #             "qtty": 0,
    #             "qtty_plan": 15
    #         },
    #         {
    #             "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #             "id_good": "b9c33dea-1fec-11e0-aee7-0015e9b8c48d",
    #             "id_properties": "",
    #             "id_series": "",
    #             "id_unit": "",
    #             "id_cell": "",
    #             "id_price": "",
    #             "price": 2500,
    #             "qtty": 0,
    #             "qtty_plan": 16
    #         },
    #         {
    #             "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #             "id_good": "b9c33deb-1fec-11e0-aee7-0015e9b8c48d",
    #             "id_properties": "",
    #             "id_series": "",
    #             "id_unit": "",
    #             "id_cell": "",
    #             "id_price": "",
    #             "price": 2600,
    #             "qtty": 0,
    #             "qtty_plan": 16
    #         },
    #         {
    #             "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #             "id_good": "bd72d927-55bc-11d9-848a-00112f43529a",
    #             "id_properties": "",
    #             "id_series": "",
    #             "id_unit": "",
    #             "id_cell": "",
    #             "id_price": "",
    #             "price": 5400,
    #             "qtty": 0,
    #             "qtty_plan": 15
    #         },
    #         {
    #             "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #             "id_good": "bd72d927-55bc-11d9-848a-00112f43529a",
    #             "id_properties": "1b603c2a-6a59-11e8-91e9-14dae9b19a48",
    #             "id_series": "",
    #             "id_unit": "",
    #             "id_cell": "",
    #             "id_price": "",
    #             "price": 5400,
    #             "qtty": 999,
    #             "qtty_plan": 15
    #         },
    #         {
    #             "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #             "id_good": "bd72d92c-55bc-11d9-848a-00112f43529a",
    #             "id_properties": "",
    #             "id_series": "",
    #             "id_unit": "",
    #             "id_cell": "",
    #             "id_price": "",
    #             "price": 6700,
    #             "qtty": 0,
    #             "qtty_plan": 15
    #         },
    #         {
    #             "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #             "id_good": "bd72d930-55bc-11d9-848a-00112f43529a",
    #             "id_properties": "",
    #             "id_series": "",
    #             "id_unit": "",
    #             "id_cell": "",
    #             "id_price": "",
    #             "price": 7100,
    #             "qtty": 0,
    #             "qtty_plan": 15
    #         },
    #         {
    #             "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #             "id_good": "bd72d935-55bc-11d9-848a-00112f43529a",
    #             "id_properties": "",
    #             "id_series": "",
    #             "id_unit": "",
    #             "id_cell": "",
    #             "id_price": "",
    #             "price": 5600,
    #             "qtty": 0,
    #             "qtty_plan": 15
    #         },
    #         {
    #             "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #             "id_good": "cbcf4994-55bc-11d9-848a-00112f43529a",
    #             "id_properties": "",
    #             "id_series": "",
    #             "id_unit": "",
    #             "id_cell": "",
    #             "id_price": "",
    #             "price": 5700,
    #             "qtty": 0,
    #             "qtty_plan": 16
    #         },
    #         {
    #             "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #             "id_good": "e8a71fec-55bc-11d9-848a-00112f43529a",
    #             "id_properties": "",
    #             "id_series": "",
    #             "id_unit": "",
    #             "id_cell": "",
    #             "id_price": "",
    #             "price": 6700,
    #             "qtty": 0,
    #             "qtty_plan": 16
    #         },
    #         {
    #             "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #             "id_good": "e8a71fee-55bc-11d9-848a-00112f43529a",
    #             "id_properties": "",
    #             "id_series": "",
    #             "id_unit": "",
    #             "id_cell": "",
    #             "id_price": "",
    #             "price": 5400,
    #             "qtty": 0,
    #             "qtty_plan": 16
    #         },
    #         {
    #             "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #             "id_good": "e8a71ffa-55bc-11d9-848a-00112f43529a",
    #             "id_properties": "",
    #             "id_series": "",
    #             "id_unit": "",
    #             "id_cell": "",
    #             "id_price": "",
    #             "price": 6700,
    #             "qtty": 0,
    #             "qtty_plan": 16
    #         },
    #         {
    #             "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #             "id_good": "e8a71ffc-55bc-11d9-848a-00112f43529a",
    #             "id_properties": "",
    #             "id_series": "",
    #             "id_unit": "",
    #             "id_cell": "",
    #             "id_price": "",
    #             "price": 5600,
    #             "qtty": 0,
    #             "qtty_plan": 16
    #         }
    #     ]
    # }
    #
    # provider.update({})

    # provider.insert_multiple([{
    #             "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #             "id_good": "e8a71ffa-55bc-11d9-848a-00112f43529a",
    #             "id_properties": "",
    #             "id_series": "",
    #             "id_unit": "",
    #             "id_cell": "",
    #             "id_price": "",
    #             "price": 6700,
    #             "qtty": 0,
    #             "qtty_plan": 16
    #         },
    #         {
    #             "id_doc": "37c4c709-d22b-11e4-869d-0050568b35ac",
    #             "id_good": "e8a71ffc-55bc-11d9-848a-00112f43529a",
    #             "id_properties": "",
    #             "id_series": "",
    #             "id_unit": "",
    #             "id_cell": "",
    #             "id_price": "",
    #             "price": 5600,
    #             "qtty": 0,
    #             "qtty_plan": 16
    #         }])
    #
    # print(provider.get_all())
    # print(provider.get(id_doc='37c4c709-d22b-11e4-869d-0050568b35ac', doc_type='Заказ поставщику'))
    # print(provider.count(id_doc='37c4c709-d22b-11e4-869d-0050568b35ac'))
    # provider.remove(id_good='e8a71ffc-55bc-11d9-848a-00112f43529a')
    # print(provider.count(id_doc='37c4c709-d22b-11e4-869d-0050568b35ac'))
