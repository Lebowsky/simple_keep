import json
from typing import List

from ru.travelfood.simple_ui import SimpleSQLProvider as sqlClass
from ui_global import get_query_result, bulk_query
from tiny_db_services import TinyNoSQLProvider, ScanningQueueService


class DbService:
    def __init__(self):
        self.sql_text = ''
        self.sql_params = None
        self.debug = False
        self.provider = SqlQueryProvider(sql_class=sqlClass())

    def _write_error_on_log(self, error_text: str):
        if error_text:
            self.provider.table_name = 'Error_log'
            self.provider.create({'log': error_text})
            self.sql_text = self.provider.sql_text
            self.sql_params = self.provider.sql_params

    def _sql_exec(self, q, params, table_name=''):
        if table_name:
            self.provider.table_name = table_name
        if isinstance(params, str):
            self.provider.sql_exec(q, params)
        else:
            self.provider.sql_exec_many(q, params)

    def _sql_query(self, q, params: str = '', table_name=''):
        if table_name:
            self.provider.table_name = table_name
        return self.provider.sql_query(q, params)


class TimerService(DbService):
    def __int__(self):
        super().__init__()

    def save_load_data(self, data):
        if not data:
            return

        clear_tables = ['RS_docs_table', 'RS_adr_docs_table', 'RS_docs_barcodes, RS_barc_flow']

        for table_name, values in data.items():
            self.provider.table_name = table_name

            if table_name in clear_tables and values:
                id_doc = values[0]['id_doc']
                _filter = {'id_doc': id_doc}

                self.provider.delete(_filter)
                self.provider.replace(values)
            else:
                self.provider.replace(values)

    def get_new_load_docs(self, data: dict) -> dict:
        loaded_documents = {}

        for doc_type in ['RS_docs', 'RS_adr_docs']:
            for item in data.get(doc_type, []):
                loaded_documents[item['id_doc']] = item

        if not loaded_documents:
            return loaded_documents

        q = '''
            SELECT id_doc FROM RS_docs
            UNION
            SELECT id_doc FROM RS_adr_docs
        '''

        db_docs = self.provider.sql_query(q)
        for doc in db_docs:
            if doc['id_doc'] in loaded_documents:
                loaded_documents.pop(doc['id_doc'])

        return loaded_documents

    def get_data_to_send(self):
        data = DocService().get_data_to_send() + AdrDocService().get_data_to_send()
        return data


class BarcodeService(DbService):
    def __init__(self):
        super().__init__()
        self.provider = SqlQueryProvider(table_name='Rs_barcodes', sql_class=sqlClass())

    def get_barcode_data(self, barcode_info, id_doc):
        if barcode_info.scheme == 'GS1':
            search_value = barcode_info.gtin
        else:
            search_value = barcode_info.barcode

        q = '''
            SELECT 
                barcodes.id_good AS id_good, 
                barcodes.id_property AS id_property,
                barcodes.id_series AS id_series,
                barcodes.id_unit AS id_unit,
                barcodes.ratio AS ratio,
                IFNULL(doc_barcodes.approved, 0) AS approved,
                IFNULL(doc_barcodes.id, 0) AS mark_id,
                IFNULL(goods.use_mark, false) AS use_mark,
                IFNULL(doc_table.id, '') AS row_key,
                IFNULL(doc_table.qtty, 0.0) AS qtty,
                IFNULL(doc_table.qtty_plan, 0.0) AS qtty_plan
                
            FROM RS_barcodes AS barcodes
            LEFT JOIN 
                    (SELECT 
                        goods.id AS id_goods, 
                        types_goods.use_mark 
                        
                    FROM  RS_goods AS goods
                    JOIN RS_types_goods AS types_goods ON goods.type_good = types_goods.id) AS goods
                ON barcodes.id_good = goods.id_goods
            
            LEFT JOIN RS_docs_table AS doc_table 
                ON barcodes.id_good = doc_table.id_good
                     AND barcodes.id_property = doc_table.id_properties
                     AND barcodes.id_unit = doc_table.id_unit
                     AND doc_table.id_doc = {}
                     
            LEFT JOIN RS_docs_barcodes as doc_barcodes
                ON doc_barcodes.id_doc = {}
                    AND doc_barcodes.GTIN = {}
                    AND doc_barcodes.Series = {}
                
            WHERE barcodes.barcode = {}'''.format(
            id_doc, id_doc, barcode_info.GTIN, barcode_info.Series, search_value)

        result = self.provider.sql_query(q)
        if result:
            return result[0]

    def get_barcode_from_doc_table(self, id_doc_table: str) -> str:
        q = '''
        SELECT barcode
          FROM RS_barcodes 
        LEFT JOIN   RS_docs_table ON 
        RS_docs_table.id_good = RS_barcodes.id_good AND 
        RS_docs_table.id_properties = RS_barcodes.id_property AND 
        RS_docs_table.id_unit = RS_barcodes.id_unit  
        
        WHERE RS_docs_table.id = ?
        
        LIMIT 1 '''

        result = self.provider.sql_query(q, id_doc_table)
        if result:
            return result[0]['barcode']
        else:
            return '0000000000011'

    @staticmethod
    def update_table(table_name, docs_table_update_data):
        provider = SqlQueryProvider(table_name=table_name)
        provider.replace(docs_table_update_data)

    @staticmethod
    def insert_no_sql(queue_update_data):
        provider = ScanningQueueService()
        provider.save_scanned_row_data(queue_update_data)


class DocService:
    def __init__(self, doc_id=''):
        self.doc_id = doc_id
        self.docs_table_name = 'RS_docs'
        self.details_table_name = 'RS_docs_table'
        self.isAdr = False
        self.sql_text = ''
        self.sql_params = None
        self.debug = False
        self.provider = SqlQueryProvider(self.docs_table_name, sql_class=sqlClass())

    def get_last_edited_goods(self, to_json=False):
        query_docs = f'SELECT * FROM {self.docs_table_name} WHERE id_doc = ? and verified = 1'

        query_goods = f'''
        SELECT * FROM {self.docs_table_name}_table
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

        return self.form_data_for_request(res_docs, res_goods, to_json)

    def form_data_for_request(self, res_docs, res_goods, to_json):
        for item in res_docs:
            filtered_list = [d for d in res_goods if d['id_doc'] == item['id_doc']]
            goods_table = f'{self.docs_table_name}_table'
            item[goods_table] = filtered_list
            if not self.isAdr:
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

        if data.get(self.docs_table_name):
            self.update_docs(data)
        else:
            self.update_nsi(data)

    def update_docs(self, data):
        doc_ids = ','.join([f'"{item.get("id_doc")}"' for item in data[self.docs_table_name]])

        query = f'''
            SELECT id_doc, verified
            FROM {self.docs_table_name}
            WHERE id_doc IN ({doc_ids})
        '''
        docs = {item['id_doc']: item['verified'] or False for item in
                self._get_query_result(query_text=query, return_dict=True)}

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
                    UPDATE {self.details_table_name}
                    SET sent = 1
                    WHERE id_doc = '{id_doc}' AND id_good IN ({id_goods})
                    '''

                self._get_query_result(query)

            query = f'UPDATE {self.docs_table_name} SET sent=1 WHERE id_doc = "{self.doc_id}"'
            self._get_query_result(query)

    def json_to_sqlite_query(self, data: dict, docs=None):
        if docs is None:
            docs = {}

        qlist = []
        # Цикл по именам таблиц
        table_list = (
            'RS_doc_types', 'RS_goods', 'RS_properties', 'RS_units', 'RS_types_goods', 'RS_series', 'RS_countragents',
            'RS_warehouses', 'RS_price_types', 'RS_cells', 'RS_barcodes', 'RS_prices', 'RS_doc_types', 'RS_docs',
            'RS_docs_table', 'RS_docs_barcodes', 'RS_adr_docs', 'RS_adr_docs_table')  # ,, 'RS_barc_flow'
        table_for_delete = ('RS_docs_table', 'RS_docs_barcodes, RS_barc_flow', 'RS_adr_docs_table')  # , 'RS_barc_flow'
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

            if table_name in ('RS_docs', 'RS_adr_docs'):  #
                query_col_names.append('verified')

            query = f"REPLACE INTO {table_name} ({', '.join(query_col_names)}) VALUES "
            values = []

            for row in data[table_name]:
                row_values = []
                list_quoted_fields = ('name', 'full_name', "mark_code")
                for col in query_col_names:
                    if col in list_quoted_fields and "\"" in row[col]:
                        row[col] = row[col].replace("\"", "\"\"")

                    # Здесь устанавливаем флаг verified!!!
                    if col == 'verified' and (table_name in ['RS_docs', 'RS_adr_docs']):
                        row[col] = docs.get(row['id_doc'], 0)

                    if row.get(col) is None:
                        row[col] = ''

                    if col == 'mark_code':  # Заменяем это поле на поля GTIN и Series
                        barc_struct = self.parse_barcode(row[col])
                        row_values.append(barc_struct['GTIN'])
                        row_values.append(barc_struct['Series'])
                    else:
                        row_values.append(row[col])  # (f'"{row[col]}"')

                    if col == 'id_doc' and (table_name in ['RS_docs', 'RS_adr_docs']):
                        doc_id_list.append('"' + row[col] + '"')

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
            UPDATE {self.docs_table_name}
            SET {key} = {value}
            WHERE id_doc = "{self.doc_id}"
            '''

        self._get_query_result(query)

    def get_doc_value(self, key, id_doc):
        query = f'SELECT {key} from {self.docs_table_name}  WHERE id_doc = ?'
        res = self._get_query_result(query, (id_doc,), True)
        if res:
            return res[0][key]

    def get_doc_types(self) -> list:
        query = f'SELECT DISTINCT doc_type from {self.docs_table_name}'
        doc_types = [rec[0] for rec in self._get_query_result(query)]
        return doc_types

    def get_doc_view_data(self, doc_type='', doc_status='') -> list:
        fields = [
            f'{self.docs_table_name}.id_doc',
            f'{self.docs_table_name}.doc_type',
            f'{self.docs_table_name}.doc_n',
            f'{self.docs_table_name}.doc_date',
            f'{self.docs_table_name}.id_warehouse',
            f'ifnull(RS_warehouses.name,"") as RS_warehouse',
            f'ifnull({self.docs_table_name}.verified, 0) as verified',
            f'ifnull({self.docs_table_name}.sent, 0) as sent',
            f'{self.docs_table_name}.add_mark_selection',
        ]

        if self.docs_table_name == 'RS_docs':
            fields.append(f'{self.docs_table_name}.id_countragents')
            fields.append(f'ifnull(RS_countragents.full_name, "") as RS_countragent')

        query_text = 'SELECT ' + ',\n'.join(fields)

        joins = f'''FROM {self.docs_table_name}
            LEFT JOIN RS_warehouses as RS_warehouses
                ON RS_warehouses.id = {self.docs_table_name}.id_warehouse
        '''

        if self.docs_table_name == 'RS_docs':
            joins += f'''
            LEFT JOIN RS_countragents as RS_countragents
                ON RS_countragents.id = {self.docs_table_name}.id_countragents
                '''

        where = ''

        if doc_status:
            if doc_status == "Выгружен":
                where = "WHERE sent=1 AND verified=1"
            elif doc_status == "К выгрузке":
                where = "WHERE ifnull(verified,0)=1 AND ifnull(sent,0)=0"
            elif doc_status == "К выполнению":
                where = "WHERE ifnull(verified,0)=0 AND ifnull(sent,0)=0"

        if not doc_type or doc_type == "Все":
            args_tuple = None
        else:
            args_tuple = (doc_type,)
            if not doc_status or doc_status == "Все":
                where = 'WHERE doc_type=?'
            else:
                where += ' AND doc_type=?'

        query_text = f'''
            {query_text}
            {joins}
            {where}
            ORDER BY {self.docs_table_name}.doc_date
        '''

        result = self._get_query_result(query_text, args_tuple, return_dict=True)
        return result

    def delete_doc(self, id_doc):
        queryes = (f'DELETE FROM {self.docs_table_name} WHERE id_doc = ?',
        'DELETE FROM RS_barc_flow WHERE id_doc = ?',
        'DELETE FROM RS_docs_table WHERE id_doc = ?',
        'DELETE FROM RS_adr_docs_table WHERE id_doc = ?')

        for query in queryes:
            self._get_query_result(query, (id_doc,))


    def get_docs_stat(self):
        query = f'''
        WITH tmp AS (
            SELECT 
                doc_type,
                {self.docs_table_name}.id_doc,
                1 as doc_Count,
                IFNULL({self.docs_table_name}.sent,0) as sent,
                IFNULL({self.docs_table_name}.verified,0) as verified, 
                CASE WHEN IFNULL(verified,0)=0 THEN 
                    COUNT({self.details_table_name}.id)
                ELSE 
                    0 
                END as count_verified,
                CASE WHEN IFNULL(verified,0)=1 THEN 
                    count({self.details_table_name}.id)
                ELSE 
                    0 
                END as count_unverified,
                CASE WHEN IFNULL(verified,0)=0 THEN
                     SUM({self.details_table_name}.qtty_plan)
                ELSE 
                    0 
                END as qtty_plan_verified,
                CASE WHEN IFNULL(verified,0)=1 THEN 
                    SUM({self.details_table_name}.qtty_plan)
                ELSE 
                    0 
                END as qtty_plan_unverified
            FROM {self.docs_table_name}
            LEFT JOIN {self.details_table_name} 
                ON {self.details_table_name}.id_doc = {self.docs_table_name}.id_doc
            GROUP BY {self.docs_table_name}.id_doc
        )
        SELECT 
            doc_type as docType, 
            COUNT(id_doc),
            SUM(doc_Count) as count, 
            SUM(sent) as sent, 
            SUM(verified) as verified,
            SUM(count_verified) as count_verified,
            SUM(count_unverified) as count_unverified,
            SUM(qtty_plan_verified) as qtty_plan_verified,
            SUM(qtty_plan_unverified) as qtty_plan_unverified
        FROM tmp
        GROUP BY doc_type
        '''

        res = self._get_query_result(query, return_dict=True)
        return res

    def get_doc_flow_stat(self):
        query = f'''
        WITH tmp AS (
            SELECT 
                doc_type,
                RS_docs.id_doc,
                1 as doc_Count,
                IFNULL(RS_docs.sent,0) as sent,
                IFNULL(RS_docs.verified,0) as verified,

                count(RS_barc_flow.barcode) as barc_count

            FROM RS_docs
            
            LEFT JOIN RS_barc_flow 
                ON RS_docs.id_doc = RS_barc_flow.id_doc
                
           WHERE  RS_docs.id_doc not in (SELECT distinct
                id_doc
                From 
                RS_docs_table
                )              
                  
            GROUP BY RS_docs.id_doc
        )
        SELECT 
            doc_type as docType, 
            COUNT(id_doc) as id_count,
            SUM(doc_Count) as count, 
            SUM(sent) as sent, 
            SUM(verified) as verified,
            SUM(barc_count) as barc_count
        FROM tmp
        GROUP BY doc_type
        '''
        res = self._get_query_result(query, return_dict=True)
        return res

    def get_doc_details_data(self, id_doc, first_elem, items_on_page, row_filters=None, search_string=None) -> list:
        select_query = f"""
            SELECT
            RS_docs_table.id,
            RS_docs_table.id_doc,
            RS_docs_table.id_good,
            RS_goods.name as good_name,
            RS_goods.code,
            RS_goods.art,
            RS_docs_table.id_properties,
            RS_properties.name as properties_name,
            RS_docs_table.id_series,
            RS_series.name as series_name,
            RS_docs_table.id_unit,
            RS_units.name as units_name,
            RS_docs_table.qtty,
            RS_docs_table.qtty_plan,
            RS_docs_table.price,
            RS_price_types.name as price_name,
            RS_docs_table.qtty_plan -RS_docs_table.qtty as IsDone,
            RS_docs_table.last_updated
            
            FROM RS_docs_table 

            LEFT JOIN RS_goods 
            ON RS_goods.id=RS_docs_table.id_good
            LEFT JOIN RS_properties
            ON RS_properties.id =RS_docs_table.id_properties
            LEFT JOIN RS_series
            ON RS_series.id =RS_docs_table.id_series
            LEFT JOIN RS_units
            ON RS_units.id = RS_docs_table.id_unit
            LEFT JOIN RS_price_types
            ON RS_price_types.id =RS_docs_table.id_price
            """

        where = f"""WHERE id_doc = '{str(id_doc)}'"""
        row_filters_condition = """AND qtty != COALESCE(qtty_plan, '0') """ if row_filters else ''
        search_string_condition = f"""AND good_name LIKE '%{search_string}%'""" if search_string else ''

        where_query = f"""
        {where}
        {row_filters_condition}
        {search_string_condition}
        """
        order_by = """ORDER BY last_updated DESC"""
        limit = f'LIMIT {items_on_page} OFFSET {first_elem}'
        query = f"{select_query} {where_query} {order_by} {limit}"

        res = self._get_query_result(query, return_dict=True)
        # res = self._sql_query(query, '')
        return res

    def parse_barcode(self, val):
        if len(val) < 21:
            return {'GTIN': '', 'Series': ''}

        val.replace('(01)', '01')
        val.replace('(21)', '21')

        if val[:2] == '01':
            GTIN = val[2:16]
            Series = val[18:]
        else:
            GTIN = val[:14]
            Series = val[14:]

        return {'GTIN': GTIN, 'Series': Series}

    def clear_barcode_data(self, id_doc):
        query_text = ('Update RS_docs_barcodes Set approved = 0 Where id_doc=:id_doc',
                      'Delete From RS_docs_barcodes Where  id_doc=:id_doc And is_plan = 0',
                      'Update RS_docs_table Set qtty = 0 Where id_doc=:id_doc',
                      'Delete From RS_docs_table Where id_doc=:id_doc and is_plan = "False"',
                      'Delete From RS_barc_flow Where id_doc = :id_doc')
        try:
            for el in query_text:
                get_query_result(el, ({'id_doc': id_doc}))
        except Exception as e:
            return {'result': False, 'error': e.args[0]}

        return {'result': True, 'error': ''}

    def get_doc_barcode_data(self, args):
        query = '''
            SELECT
            "(01)" || GTIN || "(21)" || Series as mark_code,
            approved
            FROM RS_docs_barcodes
            Where
            id_doc = :id_doc AND
            id_good = :id_good AND
            id_property = :id_property AND
            id_series = :id_series 
            --AND  id_unit = :id_unit
         '''

        res = self._get_query_result(query, args, return_dict=True)
        return res

    def get_docs_count(self, doc_type=''):
        query = f'SELECT COUNT(*) AS docs_count FROM {self.docs_table_name}'
        args = None

        if doc_type:
            query = '\n'.join([query, 'WHERE doc_type = ?'])
            args = (doc_type,)

        res = self._get_query_result(query, args, True)
        if res:
            return res[0].get('docs_count', 0)
        return 0

    def get_existing_docs(self):
        query_text = f"SELECT doc_n,doc_type FROM {self.docs_table_name}"
        res = get_query_result(query_text)
        return res

    @staticmethod
    def write_error_on_log(Err_value):
        if Err_value:
            qtext = 'Insert into Error_log(log) Values(?)'
            get_query_result(qtext, (Err_value,))

    def get_docs_and_goods_for_upload(self):

        query_docs = f'''SELECT * FROM {self.docs_table_name} WHERE verified = 1  and (sent <> 1 or sent is null)'''
        query_goods = f'''SELECT * FROM {self.details_table_name} WHERE (sent = 0 OR sent is Null)'''
        try:
            res_docs = get_query_result(query_docs, None, True)
            res_goods = get_query_result(query_goods, None, True)
        except Exception as e:
            raise e
        if not res_goods:
            return None
        return self.form_data_for_request(res_docs, res_goods, False)

    def get_data_to_send(self):
        data = []

        q = f'''SELECT id_doc
                FROM {self.docs_table_name} 
                WHERE verified = 1  AND (sent = 0 OR sent IS NULL)
            '''
        res = self.provider.sql_query(q)

        for row in res:
            id_doc = row['id_doc']

            doc_data = {
                'id_doc': id_doc,
            }

            fields = ['id_doc', 'id_good', 'id_properties', 'id_series', 'id_unit', 'qtty', 'qtty_plan']
            q = '''
                SELECT {}
                FROM RS_docs_table
                WHERE id_doc = ? AND (sent = 0 OR sent IS NULL)
            '''.format(','.join(fields))

            goods = self.provider.sql_query(q, id_doc)
            doc_data['RS_docs_table'] = goods


            fields = ['id_doc', 'id_good', 'id_property', 'id_series', 'barcode_from_scanner', 'GTIN', 'Series']
            q = '''
                SELECT {}
                FROM RS_docs_barcodes
                WHERE id_doc = ?
            '''.format(','.join(fields))

            doc_barcodes = self.provider.sql_query(q, id_doc)
            doc_data['RS_docs_barcodes'] = doc_barcodes


            fields = ['id_doc', 'barcode']
            q = '''
                SELECT {}
                FROM RS_barc_flow
                WHERE id_doc = ?
            '''.format(','.join(fields))

            barc_flow = self.provider.sql_query(q, id_doc)
            doc_data['RS_barc_flow'] = barc_flow

            data.append(doc_data)

        return data


    def get_count_mark_codes(self, id_doc):
        q = '''
            SELECT DISTINCT COUNT(id) as col_str 
            FROM RS_docs_barcodes WHERE id_doc = ? AND is_plan = 1
        '''
        res = self._sql_query(
            q=q,
            params=id_doc,
        )

        return res[0]['col_str']

    @staticmethod
    def update_uploaded_docs_status(doc_in_str):
        qtext = f'UPDATE RS_docs SET sent = 1  WHERE id_doc in ({doc_in_str}) '
        get_query_result(qtext)

        qtext = f'UPDATE RS_adr_docs SET sent = 1  WHERE id_doc in ({doc_in_str}) '
        get_query_result(qtext)

        qtext = f'UPDATE RS_docs_table SET sent = 1  WHERE id_doc in ({doc_in_str}) '
        get_query_result(qtext)

    @staticmethod
    def update_rs_docs_table_sent_status(table_string_id: str):
        qtext = f'UPDATE RS_docs_table SET sent = 0  WHERE id in ({table_string_id}) '
        get_query_result(qtext)

    def set_doc_status_to_upload(self, doc_id):
        qtext = f"UPDATE {self.docs_table_name} SET sent = 0, verified = 0  WHERE id_doc = '{doc_id}'"
        get_query_result(qtext)

    def update_doc_table_row(self, row_id, data):
        self.provider.table_name = self.details_table_name
        self.provider.update(data=data, _filter={'id': row_id})

    def _sql_exec(self, q, params, table_name=''):
        if table_name:
            self.provider.table_name = table_name
        if isinstance(params, str):
            self.provider.sql_exec(q, params)
        else:
            self.provider.sql_exec_many(q, params)

    def _sql_query(self, q, params, table_name=''):
        if table_name:
            self.provider.table_name = table_name
        return self.provider.sql_query(q, params)


class AdrDocService(DocService):
    def __init__(self, doc_id='', cur_cell='', table_type='in'):
        self.doc_id = doc_id
        self.docs_table_name = 'RS_Adr_docs'
        self.details_table_name = 'RS_adr_docs_table'
        self.isAdr = True
        self.current_cell = cur_cell
        self.table_type = table_type
        self.provider = SqlQueryProvider(self.docs_table_name, sql_class=sqlClass())

    def get_current_cell(self):
        pass

    def get_doc_details_data(self, first_elem, items_on_page, row_filters=None, search_string=None, id_doc='',
                             curCell='', ) -> list:
        select_query = '''SELECT
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
            '''

        basic_where = f"""WHERE id_doc = :id_doc and table_type = :table_type"""

        cur_cell_condition = '''and (id_cell=:current_cell OR id_cell="" OR id_cell is Null)''' if curCell else ''
        row_filters_condition = """AND qtty != COALESCE(qtty_plan, '0') """ if row_filters else ''
        search_string_condition = f"""AND good_name LIKE '%{search_string}%'""" if search_string else ''

        where_full = f"""
                {basic_where}
                {cur_cell_condition}
                {row_filters_condition}
                {search_string_condition}
        """

        order_by = f"""ORDER BY RS_cells.name, RS_adr_docs_table.last_updated DESC"""
        limit = f'LIMIT {items_on_page} OFFSET {first_elem}'
        query_text = f"{select_query} {where_full} {order_by} {limit}"
        # self.table_type = 'out'  #****** ОТЛАДОЧНОЕ
        params_dict = {'id_doc': id_doc, 'NullValue': None, 'EmptyString': '', 'table_type': self.table_type}
        if curCell:
            params_dict['current_cell'] = curCell
        res = self._get_query_result(query_text, params_dict, return_dict=True)
        return res

    def clear_barcode_data(self, id_doc):
        query_text = ('Update RS_adr_docs_table Set qtty = 0 Where id_doc=:id_doc',
                      'Delete From RS_adr_docs_table Where id_doc=:id_doc and is_plan = "False"')
        try:
            for el in query_text:
                get_query_result(el, ({'id_doc': id_doc}))
        except Exception as e:
            return {'result': False, 'error': e.args[0]}

        return {'result': True, 'error': ''}

    def get_data_to_send(self):
        data = []

        q = f'''SELECT id_doc
                FROM {self.docs_table_name} 
                WHERE verified = 1  AND (sent = 0 OR sent IS NULL)
            '''
        res = self.provider.sql_query(q)

        for row in res:
            id_doc = row['id_doc']

            doc_data = {
                'id_doc': id_doc,
            }

            fields = ['id_doc', 'id_good', 'id_properties', 'id_series', 'id_unit', 'qtty', 'qtty_plan', 'table_type']
            q = '''
                SELECT {}
                FROM RS_adr_docs_table 
                WHERE id_doc = ? AND (sent = 0 OR sent IS NULL)
            '''.format(','.join(fields))

            goods = self.provider.sql_query(q, id_doc)
            doc_data['RS_adr_docs_table'] = goods
            data.append(doc_data)

        return data

class FlowDocService(DocService):

    def __init__(self, doc_id=''):
        self.doc_id = doc_id
        self.docs_table_name = 'RS_docs'
        self.details_table_name = 'RS_docs_table'
        self.isAdr = False
        self.sql_text = ''
        self.sql_params = None
        self.debug = False
        self.provider = SqlQueryProvider(self.docs_table_name, sql_class=sqlClass())

    def get_doc_view_data(self, doc_type='', doc_status='') -> list:
        fields = [
            f'{self.docs_table_name}.id_doc',
            f'{self.docs_table_name}.doc_type',
            f'{self.docs_table_name}.doc_n',
            f'{self.docs_table_name}.doc_date',
            f'{self.docs_table_name}.id_warehouse',
            f'ifnull(RS_warehouses.name,"") as RS_warehouse',
            f'ifnull({self.docs_table_name}.verified, 0) as verified',
            f'ifnull({self.docs_table_name}.sent, 0) as sent',
            f'{self.docs_table_name}.add_mark_selection',
        ]

        if self.docs_table_name == 'RS_docs':
            fields.append(f'{self.docs_table_name}.id_countragents')
            fields.append(f'ifnull(RS_countragents.full_name, "") as RS_countragent')

        query_text = 'SELECT ' + ',\n'.join(fields)

        joins = f'''FROM {self.docs_table_name}
            LEFT JOIN RS_warehouses as RS_warehouses
                ON RS_warehouses.id = {self.docs_table_name}.id_warehouse
        '''

        if self.docs_table_name == 'RS_docs':
            joins += f'''
            LEFT JOIN RS_countragents as RS_countragents
                ON RS_countragents.id = {self.docs_table_name}.id_countragents
                '''
        where = []
        where.append( f'''{self.docs_table_name}.id_doc not in (SELECT distinct
                id_doc
                From 
                {self.details_table_name}
                ) ''')

        if doc_status:
            if doc_status == "Выгружен":
                where.append(" sent=1 AND verified=1")
            elif doc_status == "К выгрузке":
                where.append(" ifnull(verified,0)=1 AND ifnull(sent,0)=0")
            elif doc_status == "К выполнению":
                where.append(" ifnull(verified,0)=0 AND ifnull(sent,0)=0")

        if not doc_type or doc_type == "Все":
            args_tuple = None
        else:
            args_tuple = (doc_type,)
            if not doc_status or doc_status == "Все":
                where.append('doc_type=?')
            else:
                where.append(' doc_type=?')
        where_text = f'WHERE ' + ' AND '.join(where)
        query_text = f'''
            {query_text}
            {joins}
            {where_text}
            ORDER BY {self.docs_table_name}.doc_date
        '''

        result = self._get_query_result(query_text, args_tuple, return_dict=True)
        return result


    def get_flow_table_data(self):
        query_text = '''WITH temp_q as (SELECT
                        RS_barc_flow.barcode,
                        RS_barcodes.id_good as id_good,
                        RS_barcodes.id_property as id_property,
                        1 as qtty

                        FROM RS_barc_flow
                        LEFT JOIN RS_barcodes
                            ON RS_barcodes.barcode = RS_barc_flow.barcode
                        WHERE RS_barc_flow.id_doc = ?)

                        SELECT temp_q.barcode, temp_q.id_good, temp_q.id_property,
                        RS_goods.name as name, 
                        sum(qtty) as qtty
                        FROM temp_q
                        LEFT JOIN RS_goods
                          ON RS_goods.id = temp_q.id_good
                        GROUP BY temp_q.barcode'''

        return self._get_query_result(query_text, (self.doc_id,), True)
    
    def get_offline_flow_table_data(self):
        query_text = '''SELECT
                            RS_barc_flow.barcode,
                            RS_barcodes.id_good as id_good,
                            RS_barcodes.id_property as id_property,
                            RS_barc_flow.qtty as qtty,
                            RS_goods.name as name
                        FROM RS_barc_flow
                        LEFT JOIN RS_barcodes
                            ON RS_barcodes.barcode = RS_barc_flow.barcode
                        LEFT JOIN RS_goods
                            ON RS_goods.id = RS_barcodes.id_good
                        WHERE RS_barc_flow.id_doc = ?
                        '''

        return self._get_query_result(query_text, (self.doc_id,), True)

    def get_barcode_qtty(self, barcode) -> float:
        query_text = '''SELECT qtty FROM RS_barc_flow WHERE id_doc = :id_doc AND barcode = :barcode'''
        res = self._get_query_result(query_text, {'id_doc': self.doc_id, 'barcode': barcode})
        if res:
            return float(res[0][0])
        else:
            return None 

    def add_barcode_one_qtty(self, barcode):
        query_text = '''INSERT INTO RS_barc_flow (id_doc, barcode, qtty) VALUES (:id_doc, :barcode, :qtty)'''
        self._get_query_result(query_text, {'id_doc': self.doc_id, 'barcode': barcode, 'qtty': 1})

    def update_barcode_qtty(self, barcode, qtty: float):
        query_text = '''UPDATE RS_barc_flow SET qtty = :qtty WHERE id_doc = :id_doc AND barcode = :barcode'''
        self._get_query_result(query_text, {'id_doc': self.doc_id, 'barcode': barcode, 'qtty': qtty})

    def insert_barcode(self, barcode):
        query_text = '''INSERT INTO RS_barc_flow (id_doc, barcode) VALUES (:id_doc, :barcode)'''
        self._get_query_result(query_text, {'id_doc': self.doc_id, 'barcode': barcode})

    def get_data_for_ticket_printing(self, barcode):
        query_text = '''WITH temp_q as (SELECT
                        RS_barc_flow.barcode,
                        RS_barcodes.id_good as id_good,
                        RS_barcodes.id_property as id_property,
                        1 as qtty

                        FROM RS_barc_flow
                        LEFT JOIN RS_barcodes
                            ON RS_barcodes.barcode = RS_barc_flow.barcode
                        WHERE RS_barc_flow.id_doc=? AND RS_barc_flow.barcode = ?)

                        SELECT temp_q.barcode, temp_q.id_good, temp_q.id_property,
                        RS_goods.name as name, 
                        RS_properties.name as Prop_name,
                        sum(qtty) as qtty
                        FROM temp_q
                        LEFT JOIN RS_goods
                          ON RS_goods.id = temp_q.id_good
                      LEFT JOIN RS_properties
                      ON RS_properties.id = temp_q.id_property    
                      GROUP BY temp_q.barcode
                      '''
        return self._get_query_result(query_text, (self.doc_id, barcode), True)


class GoodsService(DbService):
    def __init__(self, item_id=''):
        super().__init__()
        self.item_id = item_id
        self.provider = SqlQueryProvider(table_name="RS_goods", sql_class=sqlClass())

    def get_type_name_by_id(self, id):
        query_text = f"SELECT name FROM RS_types_goods WHERE id ='{id}'"
        return self._get_query_result(query_text, return_dict=True)

    def get_goods_list_data(self, goods_type='', item_id='') -> list:
        query_text = f"""
            SELECT
            RS_goods.id,
            ifnull(RS_goods.code, '—') as code,
            RS_goods.name,
            RS_goods.art,
            ifnull(RS_units.name,'—') as unit,
            ifnull(RS_types_goods.name, '—') as type_good,
            ifnull(RS_goods.description,'—') as description
            
            FROM RS_goods
            LEFT JOIN RS_types_goods
            ON RS_types_goods.id = RS_goods.type_good
            LEFT JOIN RS_units
            ON RS_units.id = RS_goods.unit
            """
        where = '' if not goods_type else 'WHERE RS_goods.type_good=?'
        if where == '' and item_id:
            where += 'WHERE RS_goods.id=?'

        query_text = f'''
                    {query_text}
                    {where}
                    ORDER BY RS_goods.id
                '''

        if goods_type:
            args = goods_type
        elif item_id:
            args = item_id
        else:
            args = None

        result = self._sql_query(query_text, args)
        return result

    def get_all_goods_types_data(self):
        query_text = 'SELECT id,name FROM RS_types_goods'
        self.provider.table_name = 'RS_types_goods'
        return self._sql_query(query_text, '')

    def get_values_from_barcode(self, identify_field: str, identify_value: str) -> list:
        query_text = f"""
                    SELECT
                    RS_barcodes.barcode,
                    RS_barcodes.id_good,
                    RS_properties.name as property,
                    ifnull(RS_series.name, '') as series,
                    ifnull(RS_units.name, '') as unit
                    

                    FROM RS_barcodes
                    LEFT JOIN RS_properties
                    ON RS_properties.id = RS_barcodes.id_property
                    LEFT JOIN RS_units
                    ON RS_units.id = RS_barcodes.id_unit
                    LEFT JOIN RS_series
                    ON RS_series.id = RS_barcodes.id_series
                    
                    WHERE {identify_field} = '{identify_value}'
                    """

        return self._sql_query(query_text, '')

    def get_values_by_field(self, table_name, field, field_value):
        self.provider.table_name = table_name
        return self.provider.select({field: field_value})

    def get_query_with_arg_list(self, table_name, value, field, table_string_id):
        query_text = f"""SELECT ifnull({value}, '-') as {value} FROM {table_name} WHERE {field} in ({table_string_id})"""
        # self.provider.table_name = table_name
        # return self._sql_query(query_text, table_name=table_name, params='')
        return query_text

    def get_select_data(self, table_name):
        query_text = f'SELECT * FROM {table_name}'
        self.provider.table_name = table_name
        return self._sql_query(query_text, '')


class DbCreator(DbService):
    def __init__(self):
        super().__init__()

    def create_tables(self):
        import database_init_queryes
        # Создаем таблицы если их нет
        schema = database_init_queryes.database_shema()
        for el in schema:
            get_query_result(el)

    def drop_all_tables(self):
        tables = self.get_all_tables()

        for table in tables:
            self._sql_query(f'DROP TABLE {table}')


    def get_all_tables(self):
        q = '''
            SELECT 
                name 
            FROM 
                sqlite_master
            WHERE 
                type='table' AND 
                name NOT LIKE 'sqlite_%'
        '''
        tables = self._sql_query(q)

        return [table['name'] for table in tables]


class ErrorService:
    @staticmethod
    def get_all_errors(date_sort):
        sort = "DESC" if not date_sort or date_sort == "Новые" else "ASC"
        return get_query_result(f"SELECT * FROM Error_log ORDER BY timestamp {sort}")

    @staticmethod
    def clear():
        return get_query_result("DELETE FROM Error_log")


class SqlQueryProvider:
    def __init__(self, table_name='', sql_class=sqlClass(), debug=False):
        self.table_name = table_name
        # self.sql = sql_class
        self.sql = self
        self.sql_text = ''
        self.sql_params = None
        self.debug = debug

    @property
    def table_name(self):
        if self._table_name:
            return self._table_name
        else:
            raise ValueError('table_name must be specified')

    @table_name.setter
    def table_name(self, v):
        self._table_name = v

    def create(self, data):
        if not data:
            return

        query_data = self._convert_query_data(data)

        return self._exec_create(
            columns=query_data['columns'],
            params=query_data['params']
        )

    def replace(self, data):
        if not data:
            return

        query_data = self._convert_query_data(data)

        return self._exec_replace(
            columns=query_data['columns'],
            params=query_data['params']
        )

    def update(self, data, _filter=None):
        if not data:
            return

        where = None
        filter_data = []
        if _filter:
            where = list(_filter)
            filter_data = list(_filter.values())

        query_data = self._convert_query_data(data, filter_data=filter_data)

        return self._exec_update(
            columns=query_data['columns'],
            params=query_data['params'],
            where=where
        )

    def delete(self, _filter=None):
        where = None
        filter_data = []
        if _filter:
            where = list(_filter)
            filter_data = list(_filter.values())

        query_data = self._convert_query_data({}, filter_data=filter_data)

        return self._exec_delete(
            params=query_data['params'],
            where=where
        )

    def select(self, _filter=None) -> list:
        where = None
        params = ''
        if _filter:
            where = list(_filter)
            params = [str(v) for v in _filter.values()]

        return self._exec_select(
            params=params,
            where=where,
        )

    def _exec_create(self, columns, params):
        str_values = ','.join('?' * len(columns))
        str_keys = ', '.join([f'{name}' for name in columns])

        q = f'INSERT INTO {self.table_name} ({str_keys}) VALUES ({str_values})'

        params = json.dumps(params, ensure_ascii=False)
        return self.sql_exec_many(q, params)

    def _exec_replace(self, columns, params):
        str_columns = ', '.join(columns)
        str_values = ','.join('?' * len(columns))

        q = f'REPLACE INTO {self.table_name} ({str_columns}) VALUES ({str_values})'

        params = json.dumps(params, ensure_ascii=False)
        return self.sql_exec_many(q, params)

    def _exec_update(self, columns, params, where=None):
        if where:
            str_where = ' and '.join([f'{key}=?' for key in where])
        else:
            str_where = 'true'

        str_values = ', '.join([f'{name}=?' for name in columns])

        q = f'UPDATE {self.table_name} SET {str_values} WHERE {str_where}'

        params = json.dumps(params, ensure_ascii=False)
        return self.sql_exec_many(q, params)

    def _exec_delete(self, params, where=None):
        if where:
            str_where = ' and '.join([f'{key}=?' for key in where])
        else:
            str_where = 'true'

        q = f'DELETE FROM {self.table_name} WHERE {str_where}'

        params = json.dumps(params, ensure_ascii=False)
        return self.sql_exec_many(q, params)

    def _exec_select(self, params, where=None):
        if where:
            str_where = ' and '.join([f'{key}=?' for key in where])
        else:
            str_where = 'true'

        q = f'SELECT * FROM {self.table_name} WHERE {str_where}'

        params = ', '.join(params)
        return self.sql_query(q, params)

    def sql_exec_many(self, q, params):
        self.sql_text = q
        self.sql_params = params

        if not self.debug:
            return self.sql.SQLExecMany(q, params)

    def sql_exec(self, q, params):
        self.sql_text = q
        self.sql_params = params

        if not self.debug:
            return self.sql.SQLExec(q, params=params)

    def sql_query(self, q, params: str = '') -> List[dict]:
        self.sql_text = q
        self.sql_params = params

        if not self.debug:
            result = self.sql.SQLQuery(q, params)
            return json.loads(result)

    @staticmethod
    def _convert_query_data(data, filter_data=None):
        columns = []
        params = []
        if not filter_data:
            filter_data = []

        if isinstance(data, list):
            columns = list(data[0])
            for row in data:
                params.append([v for v in row.values()] + filter_data)
        elif isinstance(data, dict):
            columns = list(data)
            params = [[v for v in data.values()] + filter_data]
        else:
            ValueError(f'data must be list or dict, not {type(data)}')

        return {'columns': columns, 'params': params}

    @staticmethod
    def convert_sql_params(sql_query, params_dict):
        import re
        param_values = []
        def replace_named_param(match):
            param_name = match.group(1)

            param_values.append(params_dict[param_name])

            return "?"
        new_query = re.sub(r':(\w+)'    , replace_named_param, sql_query)

        return new_query, param_values

    # методы ниже добавлены для временного решения проблемы SQLProvider на 9 андроиде
    def SQLExec(self, q, params):
        self.sql_text = q
        self.sql_params = params

        if params:
            return json.dumps(get_query_result(q, tuple(params.split(','))))
        else:
            return json.dumps(get_query_result(q))

    def SQLExecMany(self, q, params):
        self.sql_text = q
        self.sql_params = params

        return bulk_query(q, json.loads(params))

    def SQLQuery(self, q, params):
        self.sql_text = q
        self.sql_params = params

        if params:
            return json.dumps(get_query_result(q, tuple(params.split(',')), return_dict=True))
        else:
            return json.dumps(get_query_result(q, return_dict=True))

