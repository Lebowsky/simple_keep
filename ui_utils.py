import json
from typing import Callable
from functools import wraps

from java import jclass

noClass = jclass("ru.travelfood.simple_ui.NoSQL")
rs_settings = noClass("rs_settings")


# Класс-декоратор для удобной работы с hashMap. Также можно добавить дополнительную логику.
class HashMap:
    def __init__(self, hash_map=None, debug: bool = False):
        self.hash_map = hash_map
        self.debug_mode = debug

    def __call__(self, func: Callable[..., None]):
        @wraps(func)
        def wrapper(hashMap, *args, **kwargs):
            self.init(hashMap)
            func(self)
            return hashMap

        return wrapper

    def init(self, hashMap):
        self.hash_map = hashMap

    def toast(self, text, add_to_log=False):
        self.hash_map.put('toast', str(text))
        if add_to_log:
            self.error_log(text)

    def debug(self, text):
        if self.debug_mode:
            self.toast(text, add_to_log=True)

    def refresh_screen(self):
        self.hash_map.put('RefreshScreen', '')

    def run_event(self, method_name):
        self['RunEvent'] = json.dumps(self._get_event(method_name))

    def run_event_async(self, method_name):
        self['RunEvent'] = json.dumps(self._get_event(method_name, True))

    def _get_event(self, method_name, async_action=False):
        evt = [{
            'action': 'runasync' if async_action else 'run',
            'type': 'python',
            'method': method_name,
        }]
        return evt

    def error_log(self, err_data):
        try:
            err_data = json.dumps(err_data, ensure_ascii=False, indent=2)
        except:
            err_data = str(err_data)

        rs_settings.put('error_log', err_data, True)

    def __getitem__(self, item):
        return self.get(item, False)

    def __setitem__(self, key, value):
        self.put(key, value, False)

    def get(self, item, from_json=False):
        if from_json:
            return json.loads(self.hash_map.get(item)) if self.hash_map.get(item) else None
        else:
            return self.hash_map.get(item)

    def put(self, key, value, to_json=False):
        if to_json:
            self.hash_map.put(key, json.dumps(value))
        else:
            self.hash_map.put(key, str(value))

    def containsKey(self, key):
        return self.hash_map.containsKey(key)


def json_to_sqlite_query(data):
    table_list = (
        'RS_doc_types', 'RS_goods', 'RS_properties', 'RS_units', 'RS_types_goods', 'RS_series', 'RS_countragents',
        'RS_warehouses', 'RS_price_types', 'RS_cells', 'RS_barcodes', 'RS_prices', 'RS_doc_types', 'RS_docs',
        'RS_docs_table', 'RS_docs_barcodes', 'RS_adr_docs', 'RS_adr_docs_table')  # ,, 'RS_barc_flow'
    table_for_delete = ('RS_docs_table', 'RS_docs_barcodes, RS_adr_docs_table')  # , 'RS_barc_flow'

    queries = []
    doc_id_list = []

    # Цикл по именам таблиц
    for table_name in table_list:
        if not data.get(table_name):
            continue

        # Добавим в запросы удаление из базы строк тех документов, что мы загружаем
        if table_name in table_for_delete:
            query = f"DELETE FROM {table_name} WHERE id_doc in ({', '.join(doc_id_list)}) "
            queries.append(query)

        column_names = data[table_name][0].keys()
        if 'mark_code' in column_names:
            query_col_names = list(column_names)
            query_col_names.append('GTIN')
            query_col_names.append('Series')
            query_col_names.remove('mark_code')
        else:
            query_col_names = column_names

        query = f"REPLACE INTO {table_name} ({', '.join(query_col_names)}) VALUES "
        values = []

        for row in data[table_name]:
            row_values = []
            list_quoted_fields = ('name', 'full_name', "mark_code")
            for col in column_names:
                if col in list_quoted_fields and "\"" in row[col]:
                    row[col] = row[col].replace("\"", "\"\"")
                if row[col] is None:
                    row[col] = ''
                if col == 'mark_code':  # Заменяем это поле на поля GTIN и Series
                    barc_struct = parse_barcode(row[col])
                    row_values.append(barc_struct['GTIN'])
                    row_values.append(barc_struct['Series'])
                else:
                    row_values.append(row[col])  # (f'"{row[col]}"')
                if col == 'id_doc' and table_name == 'RS_docs':
                    doc_id_list.append('"' + row[col] + '"')
            formatted_val = [f'"{x}"' if isinstance(x, str) else str(x) for x in row_values]
            values.append(f"({', '.join(formatted_val)})")
        query += ", ".join(values)
        queries.append(query)

    return queries


def parse_barcode(val):
    if len(val) < 21:
        return {'GTIN': '', 'Series': ''}

    val.replace('(01)','01')
    val.replace('(21)', '21')

    if val[:2] == '01':
        GTIN = val[2:16]
        Series = val[18:]
    else:
        GTIN = val[:14]
        Series = val[14:]

    return {'GTIN': GTIN, 'Series': Series}
