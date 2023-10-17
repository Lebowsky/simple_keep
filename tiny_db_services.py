import datetime
import json
import os
from typing import List, Union, Dict, Any, Optional, Tuple
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

    def remove(self, doc_ids=None, **cond):
        if doc_ids:
            return self.table.remove(doc_ids=doc_ids)
        else:
            return self.table.remove(cond=self._create_condition(**cond), doc_ids=doc_ids)

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


class ExchangeQueueBuffer:
    def __init__(self, table_name, ):
        self.table_name = table_name
        self.provider = TinyNoSQLProvider(table_name=self.table_name)

    def save_data_to_send(self, data, pk):
        return self.provider.upsert(data=data, pk=pk)

    def get_data_to_send(self):
        return self.provider.get_all()

    def remove_sent_data(self, data):
        doc_id_list = [x.doc_id for x in data]
        self.provider.remove(doc_ids=doc_id_list)


class NoSQLProvider:
    def __init__(self, name: str):
        self.nosql = noClass(name)
        self.nosql_name = name

    def put(
            self,
            key: str,
            value: Union[str, int, bool, List, Dict, Tuple],
            queue: bool = True,
            to_json: bool = False
    ) -> None:
        """
        Помещает значение в указанный ключ.
        str, int, bool - помещаем как есть
        list, dict, tuple - преобразовываем в строку.
        """
        if not isinstance(key, str):
            raise TypeError('Ключ NoSQL должен быть строкой')
        if isinstance(value, (str, int, bool)):
            self.nosql.put(key, value, queue)
            return
        if not to_json:
            raise TypeError('Список допустимых типов NoSQL: str, int, bool')
        if isinstance(value, (List, Dict, Tuple)):
            self.nosql.put(key, json.dumps(value), queue)
        else:
            raise TypeError(f'NoSQL. Нельзя сериализовать {type(value)}')

    def get(
            self,
            key: str,
            default: Optional[Any] = None,
            from_json: bool = False
    ) -> Any:
        """Получает значение по ключу"""
        result = self.nosql.get(key)
        if result is not None:
            return result if not from_json else json.loads(result)
        return result if not default else default

    def delete(self, key: str) -> None:
        """Удаляет ключ"""
        self.nosql.delete(key)

    def destroy(self) -> None:
        """Уничтожает все ключи базы"""
        self.nosql.destroy()

    def get_all_keys(self) -> str:
        """Получить список всех ключей базы в виде строки формата JSON-массива строк"""
        return self.nosql.getallkeys()

    def find_json(
            self,
            field: str,
            value: Any,
            index_name: Optional[str] = None
    ) -> str:
        """
        Медленный поиск среди всех объектов базы которые имеют тип JSON
        и в поле которых есть значение. Возвращает строку с JSON-массивом
        найденных объектов.
        Если в базе много значений - лучше использовтаь поиск с индексом.
        """
        if index_name:
            return self.nosql.findJSON_index(index_name, field, value)
        return self.nosql.findJSON(field, value)

    def run_index(self, index: str, field: str) -> None:
        """
        Создание индекса по JSON-объектам для дальнейшего использования для поиска.
        Создает, асинхроннно индекс, состоящий из объектов с указанным полем.
        """
        self.nosql.run_index(index, field)

    def keys(self) -> List[str]:
        return json.loads(self.nosql.getallkeys())

    def items(self) -> List[Tuple[str, Optional[str]]]:
        return [(key, self.nosql.get(key)) for key in self.keys()]




class LoggerService:
    def __init__(self, provider=None):
        self.table_name = "ErrorLog"
        self.provider = provider or TinyNoSQLProvider(table_name=self.table_name,
                                                      base_name='SimpleLogger')

    def write_to_log(self, **kwargs):

        data = {"timestamp": DateFormat.get_now_nosql_format(),
                "error_type": kwargs.get('error_type') or '',
                "error_text": kwargs.get('error_text') or '',
                "error_info": kwargs.get('error_info') or ''}

        self.provider.insert(data)

    def get_all_errors(self, date_sort=None):
        desc = True if not date_sort or date_sort == "Новые" else False
        all_errors = sorted(self.provider.get_all(), key=lambda k: k['timestamp'], reverse=desc)
        return all_errors

    def clear(self):
        ids_list = [x.doc_id for x in self.get_all_errors()]
        if ids_list:
            self.provider.remove(ids_list)


class DateFormat:

    @staticmethod
    def get_now_nosql_format() -> str:
        utc_date = datetime.datetime.utcnow()
        return utc_date.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def get_table_view_format(date: str, user_tmz_offset=None) -> str:
        user_tmz_offset = user_tmz_offset or rs_settings.get('user_tmz_offset')
        timezone_offset = datetime.timedelta(hours=int(user_tmz_offset))
        dt_date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        return str(dt_date + timezone_offset)