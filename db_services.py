import json

from ui_global import get_query_result


class DocService:
    def __init__(self, doc_id=''):
        self.doc_id = doc_id
        self.docs_table_name = 'RS_docs'
        self.details_table_name = 'RS_docs_table'
        self.isAdr = False

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
                        row[col] = docs.get(row['id_doc'], False)

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
        query_doc = f'DELETE FROM {self.docs_table_name} WHERE id_doc = ?'
        res = self._get_query_result(query_doc, (id_doc,))

        return res

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

    def get_doc_details_data(self, id_doc) -> list:
        query = f"""
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
            RS_docs_table.qtty_plan -RS_docs_table.qtty as IsDone
            
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

            WHERE id_doc = $arg1
            ORDER BY RS_docs_table.last_updated DESC 
            """
        res = self._get_query_result(query, (id_doc,), return_dict=True)
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
                      'Delete From RS_docs_table Where id_doc=:id_doc and is_plan = "False"')
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

    @staticmethod
    def get_existing_docs():
        query_text = "SELECT doc_n,doc_type FROM RS_docs"
        res = get_query_result(query_text)
        return res

    @staticmethod
    def write_error_on_log(Err_value):
        if Err_value:
            qtext = 'Insert into Error_log(log) Values(?)'
            get_query_result(qtext, (Err_value,))

    def get_docs_and_goods_for_upload(self):
        query_docs = '''SELECT * FROM RS_docs WHERE verified = 1  and (sent <> 1 or sent is null)'''
        query_goods = '''SELECT * FROM RS_docs_table WHERE sent = 0'''
        try:
            res_docs = get_query_result(query_docs, None, True)
            res_goods = get_query_result(query_goods, None, True)
        except Exception as e:
            raise e
        if not res_goods:
            return None
        return self.form_data_for_request(res_docs, res_goods, False)

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

    @staticmethod
    def set_doc_status_to_upload(doc_id):
        qtext = f"UPDATE RS_docs SET sent = 0, verified = 0  WHERE id_doc = '{doc_id}'"
        get_query_result(qtext)


class AdrDocService(DocService):
    def __init__(self):
        self.docs_table_name = 'RS_Adr_docs'
        self.details_table_name = 'RS_adr_docs_table'
        self.isAdr = True

    def get_current_cell(self):
        pass

    def get_doc_details_data(self, id_doc) -> list:
        query_text = '''SELECT
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
            
            '''

        if self.curCell:
            query_text = query_text + '''
             and (id_cell=:current_cell OR id_cell="" OR id_cell is Null)
            '''

        query_text = query_text + ' ORDER BY RS_cells.name, RS_adr_docs_table.last_updated DESC'
        res = self._get_query_result(query_text, (id_doc,), return_dict=True)
        return res


class GoodsService:
    def __init__(self, item_id=''):
        self.item_id = item_id

    def get_type_name_by_id(self, id):
        query_text = f"SELECT name FROM RS_types_goods WHERE id ='{id}'"
        return self._get_query_result(query_text, return_dict=True)

    def get_goods_list_data(self, goods_type='') -> list:
        query_text = f"""
            SELECT
            RS_goods.id,
            ifnull(RS_goods.code, '—') as code,
            RS_goods.name,
            RS_goods.art,
            ifnull(RS_units.name,'-') as unit,
            ifnull(RS_types_goods.name, '—') as type_good,
            ifnull(RS_goods.description,'-') as description
            
            FROM RS_goods
            LEFT JOIN RS_types_goods
            ON RS_types_goods.id = RS_goods.type_good
            LEFT JOIN RS_units
            ON RS_units.id = RS_goods.unit
            """
        where = '' if not goods_type else 'WHERE RS_goods.type_good=?'

        query_text = f'''
                    {query_text}
                    {where}
                    ORDER BY RS_goods.id
                '''

        args = (goods_type,) if goods_type else None

        result = self._get_query_result(query_text, args, return_dict=True)
        return result

    def get_all_goods_types_data(self):
        query_text_all_types = 'SELECT id,name FROM RS_types_goods'
        return self._get_query_result(query_text_all_types, return_dict=True)

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

        return self._get_query_result(query_text, return_dict=True)

    def get_name_by_field(self, table_name, field, field_value):
        query_text = f"SELECT name FROM {table_name} WHERE {field} = '{field_value}'"
        return self._get_query_result(query_text, return_dict=True)[0]['name']

    @staticmethod
    def _get_query_result(query_text, args=None, return_dict=False):
        return get_query_result(query_text, args=args, return_dict=return_dict)


class DbCreator:
    def create_tables(self):
        import database_init_queryes
        # Создаем таблицы если их нет
        schema = database_init_queryes.database_shema()
        for el in schema:
            get_query_result(el)


class ErrorService:
    @staticmethod
    def get_all_errors(date_sort):
        sort = "DESC" if not date_sort or date_sort == "Новые" else "ASC"
        return get_query_result(f"SELECT * FROM Error_log ORDER BY timestamp {sort}")

    @staticmethod
    def clear():
        return get_query_result("DELETE FROM Error_log")


