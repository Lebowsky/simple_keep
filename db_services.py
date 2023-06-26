import json

from ui_global import get_query_result


class DocService:
    def __init__(self, doc_id=''):
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

    def json_to_sqlite_query(self, data, docs=None):
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
                        barc_struct = self.parse_barcode(row[col])
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

    def get_doc_value(self, key, id_doc):
        query = f'SELECT {key} from RS_docs  WHERE id_doc = ?'
        res = self._get_query_result(query, (id_doc,), True)
        if res:
            return res[0][key]

    def get_doc_types(self) -> list:
        query = 'SELECT DISTINCT doc_type from RS_docs'
        doc_types = [rec[0] for rec in self._get_query_result(query)]
        return doc_types

    def get_doc_view_data(self, doc_type='', doc_status='') -> list:
        query_text = '''
            SELECT RS_docs.id_doc,
                RS_docs.doc_type,
                RS_docs.doc_n,
                RS_docs.doc_date,
                RS_docs.id_countragents,
                RS_docs.id_warehouse,
                ifnull(RS_countragents.full_name,'') as RS_countragent,
                ifnull(RS_warehouses.name,'') as RS_warehouse,
                ifnull(RS_docs.verified, 0) as verified,
                ifnull(RS_docs.sent, 0) as sent,
                RS_docs.add_mark_selection

            FROM RS_docs
            LEFT JOIN RS_countragents as RS_countragents
                ON RS_countragents.id = RS_docs.id_countragents
            LEFT JOIN RS_warehouses as RS_warehouses
                ON RS_warehouses.id=RS_docs.id_warehouse
        '''

        if doc_status:
            if doc_status == "Выгружен":
                where = "WHERE sent=1 AND verified=1"
            elif doc_status == "К выгрузке":
                where = "WHERE ifnull(verified,0)=1 AND ifnull(sent,0)=0"
            elif doc_status == "К выполнению":
                where = "WHERE ifnull(verified,0)=0 AND ifnull(sent,0)=0"
            elif doc_status == "Все":
                where = ""

        if not doc_type or doc_type == "Все":
            args_tuple = None
            if not doc_status or doc_status == "Все":
                where = ''

        else:
            args_tuple = (doc_type,)
            if not doc_status or doc_status == "Все":
                where = 'WHERE doc_type=?'
            else:
                where += ' AND doc_type=?'

        query_text = f'''
            {query_text}
            {where}
            ORDER BY RS_docs.doc_date
        '''

        result = self._get_query_result(query_text, args_tuple, return_dict=True)
        return result

    def delete_doc(self, id_doc):
        query_doc = 'DELETE FROM RS_docs WHERE id_doc = ?'
        res = self._get_query_result(query_doc, (id_doc,))

        return res

    def get_docs_stat(self):
        query = '''
        WITH tmp AS (
            SELECT 
                doc_type,
                RS_docs.id_doc,
                1 as doc_Count,
                IFNULL(RS_docs.sent,0) as sent,
                IFNULL(verified,0) as verified, 
                CASE WHEN IFNULL(verified,0)=0 THEN 
                    COUNT(RS_docs_table.id)
                ELSE 
                    0 
                END as count_verified,
                CASE WHEN IFNULL(verified,0)=1 THEN 
                    count(RS_docs_table.id)
                ELSE 
                    0 
                END as count_unverified,
                CASE WHEN IFNULL(verified,0)=0 THEN
                     SUM(RS_docs_table.qtty_plan)
                ELSE 
                    0 
                END as qtty_plan_verified,
                CASE WHEN IFNULL(verified,0)=1 THEN 
                    SUM(RS_docs_table.qtty_plan)
                ELSE 
                    0 
                END as qtty_plan_unverified
            FROM RS_docs
            LEFT JOIN RS_docs_table 
                ON RS_docs_table.id_doc = RS_docs.id_doc
            GROUP BY RS_docs.id_doc
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
        query = """
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
            RS_docs_table.qtty_plan - RS_docs_table.qtty as IsDone
            FROM RS_docs_table 

            LEFT JOIN RS_goods 
            ON RS_goods.id=RS_docs_table.id_good
            LEFT JOIN RS_properties
            ON RS_properties.id = RS_docs_table.id_properties
            LEFT JOIN RS_series
            ON RS_series.id = RS_docs_table.id_series
            LEFT JOIN RS_units
            ON RS_units.id=RS_docs_table.id_unit
            LEFT JOIN RS_price_types
            ON RS_price_types.id = RS_docs_table.id_price
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
        query = 'SELECT COUNT(*) AS docs_count FROM RS_docs'
        args = None

        if doc_type:
            query = '\n'.join([query, 'WHERE doc_type = ?'])
            args = (doc_type,)

        res = self._get_query_result(query, args, True)
        if res:
            return res[0].get('docs_count', 0)
        return 0

    @staticmethod
    def get_existing_docs_names_list():
        query_text = "SELECT doc_n FROM RS_docs"
        res = get_query_result(query_text)
        return res

    @staticmethod
    def write_error_on_log(Err_value):
        if Err_value:
            qtext = 'Insert into Error_log(log) Values(?)'
            get_query_result(qtext, (Err_value,))


class DbCreator:
    def create_tables(self):
        import database_init_queryes
        # Создаем таблицы если их нет
        schema = database_init_queryes.database_shema()
        for el in schema:
            get_query_result(el)


class DbService:
    def __init__(self, _db_session, table_name):
        import db_models
        self.db_session = db_models.db_session
        self.table_name = table_name
        self.model = ModelsFactory().create(self.table_name)

    def get(self, _filter):
        with self.db_session:
            # return self.model.select(**_filter)[:] or None
            return self.model.get(**_filter)

    def create(self, data):
        with self.db_session:
            return self.model(**data)

    def update(self, data, _filter=None):
        with self.db_session:
            if _filter:
                obj = self.get(_filter)
            else:
                pk = self.model.get_pk()
                if not data.get(pk):
                    raise ValueError(f'data: {data} has not constraint key {pk}')
                else:
                    obj = self.get({pk: data[pk]})

            if obj:
                obj.set(**data)
            else:
                obj = self.model(**data)

            return obj

    def delete(self, _filter):
        with self.db_session:
            obj = self.get(_filter)
            if obj:
                return obj.delete()


class DocDbService(DbService):
    def __init__(self, _db_session):
        super().__init__(_db_session, 'RS_docs')

    def get(self, _filter, to_dict=False):
        with self.db_session:
            if to_dict:
                import db_models
                return self.model.get(**_filter).to_dict(with_collections=True, related_objects=True)
            #only=None, exclude=None, with_collections=False, with_lazy=False, related_objects=False
            else:
                return self.model.get(**_filter)

    def update(self, _filter, data: dict):
        with self.db_session:
            doc = self.get(_filter)

            if data.get('goods'):
                goods_service = DbService(self.db_session, 'RS_docs_table')
                goods = []
                for row in data['goods']:
                    item = goods_service.create(row)
                    goods.append(item)

                data['goods'] = goods

            if doc:
                doc.set(**data)
            else:
                self.model(**data)

            return doc


class ModelsFactory:
    def __init__(self):
        import db_models
        self.models = {model._table_: model for model in db_models.models}

    def create(self, table_name):
        return self.models.get(table_name)


class ErrorService:
    @staticmethod
    def get_all_errors(date_sort):
        sort = "DESC" if not date_sort or date_sort == "Новые" else "ASC"
        return get_query_result(f"SELECT * FROM Error_log ORDER BY timestamp {sort}")

    @staticmethod
    def clear():
        return get_query_result("DELETE FROM Error_log")
