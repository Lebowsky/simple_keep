import json

from ui_utils import parse_barcode
from ui_global import get_query_result


class DocService:
    def __init__(self, doc_id):
        self.doc_id = doc_id

    def get_last_edited_goods(self, to_json=False):
        query_docs = f'SELECT * FROM RS_docs WHERE id_doc = ? and verified = 1'

        query_goods = '''
        SELECT * FROM RS_docs_table
        WHERE id_doc = ? and sent = 0
        '''

        try:
            res_docs = get_query_result(query_docs, (self.doc_id,), True)
            res_goods = get_query_result(query_goods, (self.doc_id,), True)
        except Exception as e:
            raise e
            # return {'Error': e.args[0]}

        if not res_goods:
            return None

        for item in res_docs:
            filtered_list = [d for d in res_goods if d['id_doc'] == item['id_doc']]
            item['RS_docs_table'] = filtered_list
            item['RS_docs_barcodes'] = []
            item['RS_barc_flow'] = []

        if to_json:
            return json.dumps(res_docs)
        else:
            return res_docs

    def update_data_from_json(self, json_data):
        try:
            data = json.loads(json_data)
        except:
            data = json_data

        if data.get('RS_docs'):
            self.update_docs(data)
        else:
            self.update_nsi(data)

    def update_docs(self, data):
        doc_ids = ','.join([f'"{item.get("id_doc")}"' for item in data['RS_docs']])

        query = f'''
            SELECT id_doc, verified
            FROM RS_docs
            WHERE id_doc IN ({doc_ids})
        '''
        docs = {item['id_doc']: item['verified'] for item in self._get_query_result(query_text=query, return_dict=True)}

        queries = self.json_to_sqlite_query(data, docs)

        for query in queries:
            try:
                self._get_query_result(query)
            except Exception as e:
                raise e

        return docs

    def update_nsi(self, data):
        queries = self.json_to_sqlite_query(data)

        for query in queries:
            try:
                self._get_query_result(query)
            except Exception as e:
                raise e

    def update_sent_data(self, data):
        if data:
            for doc in data:
                id_doc = doc['id_doc']
                id_goods = ','.join([f'"{item.get("id_good")}"' for item in doc.get('RS_docs_table', [])])

                query = f'''
                    UPDATE RS_docs_table
                    SET sent = 1
                    WHERE id_doc = '{id_doc}' AND id_good IN ({id_goods})
                    '''

                self._get_query_result(query)

    @staticmethod
    def json_to_sqlite_query(data, docs=None):
        qlist = []
        # Цикл по именам таблиц
        table_list = (
            'RS_doc_types', 'RS_goods', 'RS_properties', 'RS_units', 'RS_types_goods', 'RS_series', 'RS_countragents',
            'RS_warehouses', 'RS_price_types', 'RS_cells', 'RS_barcodes', 'RS_prices', 'RS_doc_types', 'RS_docs',
            'RS_docs_table', 'RS_docs_barcodes', 'RS_adr_docs', 'RS_adr_docs_table')  # ,, 'RS_barc_flow'
        table_for_delete = ('RS_docs_table', 'RS_docs_barcodes, RS_adr_docs_table')  # , 'RS_barc_flow'
        doc_id_list = []
        for table_name in table_list:
            if not data.get(table_name):
                continue

            # Добавим в запросы удаление из базы строк тех документов, что мы загружаем
            if table_name in table_for_delete:
                query = f"DELETE FROM {table_name} WHERE id_doc in ({', '.join(doc_id_list)}) "
                qlist.append(query)

            column_names = data[table_name][0].keys()
            if 'mark_code' in column_names:
                query_col_names = list(column_names)
                query_col_names.append('GTIN')
                query_col_names.append('Series')
                query_col_names.remove('mark_code')
            else:
                query_col_names = list(column_names)

            if docs and table_name == 'RS_docs':
                query_col_names.append('verified')

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

                if docs and table_name == 'RS_docs':
                    row_values.append(docs[row['id_doc']])

                formatted_val = [f'"{x}"' if isinstance(x, str) else str(x) for x in row_values]
                values.append(f"({', '.join(formatted_val)})")
            query += ", ".join(values)
            qlist.append(query)

        return qlist

    @staticmethod
    def _get_query_result(query_text, args=None, return_dict=False):
        return get_query_result(query_text, args=args, return_dict=return_dict)

    def set_doc_value(self, key, value):
        query = f'''
            UPDATE RS_docs
            SET {key} = {value}
            WHERE id_doc = "{self.doc_id}"
            '''

        self._get_query_result(query)

    def get_doc_types(self) -> list:
        query = 'SELECT DISTINCT doc_type from RS_docs'
        doc_types = [rec[0] for rec in self._get_query_result(query)]
        return doc_types

    def get_doc_view_data(self, doc_type='') -> list:
        query_text = '''
            SELECT RS_docs.id_doc,
                RS_docs.doc_type,
                RS_docs.doc_n,
                RS_docs.doc_date,
                RS_docs.id_countragents,
                RS_docs.id_warehouse,
                ifnull(RS_countragents.full_name,'') as RS_countragent,
                ifnull(RS_warehouses.name,'') as RS_warehouse,
                RS_docs.verified,
                RS_docs.sent,
                RS_docs.add_mark_selection

            FROM RS_docs
            LEFT JOIN RS_countragents as RS_countragents
                ON RS_countragents.id = RS_docs.id_countragents
            LEFT JOIN RS_warehouses as RS_warehouses
                ON RS_warehouses.id=RS_docs.id_warehouse
        '''
        where = '' if not doc_type else 'WHERE RS_docs.doc_type=?'

        query_text = f'''
            {query_text}
            {where}
            ORDER BY RS_docs.doc_date
        '''

        result = self._get_query_result(query_text, (doc_type, ), return_dict=True)
        return result
