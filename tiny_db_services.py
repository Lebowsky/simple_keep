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
        self.db = TinyDB(os.path.join(self.db_path, f'{self.base_name}.json'))
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


class ScanningQueueService:
    def __init__(self, provider=None):
        self.table_name = 'scanning_queue'
        self.provider = provider or TinyNoSQLProvider(table_name=self.table_name)

    def get_doc_scanning_queue(self, id_doc) -> dict:
        result = {}
        data = self.provider.search(id_doc=id_doc)

        for row in data:
            result[row['row_key']] = row['qtty']## NOT WORK

        return result

    def save_scanned_row_data(self, data, sent=False):  #TODO в тесты Олег
        # id_doc, row_id, qtty
        data['sent'] = sent
        self.provider.insert(data=data)
        return self.provider.count(id_doc=data['id_doc'])

    def get_scanned_row_qtty(self, id_doc, row_id):
        data = self.provider.search(id_doc=id_doc, row_id=row_id)
        return sum([row['qtty'] for row in data])  # or 'd_qtty'

    def get_document_lines(self, id_doc, sent=None) -> list:
        if sent is not None:
            data = self.provider.search(id_doc=id_doc, sent=sent)
        else:
            data = self.provider.search(id_doc=id_doc)
        return data

    def update_sent_lines(self, sent_data: list, sent=True):
        doc_id_list = [x.doc_id for x in sent_data]
        self.provider.table.update({'sent': sent}, doc_ids=doc_id_list)

    def has_unsent_lines(self, id_doc) -> bool:
        qtty = self.provider.count(id_doc=id_doc, sent=False)
        return True if qtty > 0 else False

    def remove_doc_lines(self, id_doc):
        self.provider.remove(id_doc=id_doc)




