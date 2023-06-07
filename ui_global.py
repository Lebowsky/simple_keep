import collections
from datetime import datetime
import sqlite3
from sqlite3 import Error
import ui_barcodes
import os
import ui_form_data
import threading
import queue

query_list = queue.Queue()
# Вот таким незатейливым методом определяем, мы запустились на компе или на ТСД **
# Ну и в зависимости от, используем базу ****
if os.path.exists('//data/data/ru.travelfood.simple_ui/databases/'): #локально
    db_path = '//data/data/ru.travelfood.simple_ui/databases/SimpleKeep'  # rightscan'
else:
    db_path = 'rightscan5.db'  # D:\PythonProjects\RightScan\SUI_noPony\

conn = None

def text_to_bool(val):
    pass

# Функция получает строки маркировки документа по значению маркировки
def find_barcode_in_marking_codes_table(self, struct_barcode: list) -> collections.Iterable:
    query_text = ui_form_data.get_query_mark_find_in_doc()
    args_dict = {}
    args_dict['GTIN'] = struct_barcode['GTIN']
    args_dict['Series'] = struct_barcode['SERIAL']
    args_dict['id_doc'] = self.id_doc

    res = get_query_result(query_text, args_dict, True)
    return res


def find_barcode_in_barcode_table(barcode: str) -> collections.Iterable:
    query_text = ui_form_data.get_barcode_query()
    res = get_query_result(query_text, (barcode,), True)
    return res


# Сравнивает количество-план товара в документе и количество марок, по этому товару там же.
# Возвращает True, если количество марок меньше плана
def check_mark_code_compliance(el_dict: dict, id_doc, gtin):
    query_text = ui_form_data.get_mark_qtty_conformity()
    args_dict = {}
    args_dict['idDoc'] = id_doc
    args_dict['barcode'] = '01' + gtin + '%'
    args_dict['id_good'] = el_dict['id_good']
    args_dict['id_properties'] = el_dict['id_property']
    args_dict['id_series'] = el_dict['id_series']
    #args_dict['id_unit'] = el_dict['id_unit']
    args_dict['approved'] = '1'
    res = get_query_result(query_text, args_dict)
    if res:
        if res[0][0] > 0:
            return True
        elif res[0][0] == 0:
            return False
        else:
            return True
    return True


def check_barcode_compliance(el_dict: dict, id_doc):
    # 1 Такой товар в принципе есть в документе

    query_text = ui_form_data.get_plan_good_from_doc()
    args_dict = {}
    args_dict['idDoc'] = id_doc
    args_dict['id_good'] = el_dict['id_good']
    args_dict['id_properties'] = el_dict['id_property']
    args_dict['id_series'] = el_dict['id_series']
    #args_dict['id_unit'] = el_dict['id_unit']

    res = get_query_result(query_text, args_dict, True)

    return res


def check_adr_barcode_compliance(el_dict: dict, id_doc):
    # 1 Такой товар в принципе есть в документе

    query_text =  '''
    SELECT ifnull(qtty_plan,0) as qtty_plan,
    ifnull(qtty,0) as qtty, id_good
    FROM RS_adr_docs_table
    WHERE 
    id_doc = :idDoc 
    AND id_good = :id_good
    AND id_properties = :id_properties
    AND id_series = :id_series
    AND id_cell = :id_cell or id_cell = "" OR id_cell is Null
    '''
    args_dict = {}
    args_dict['idDoc'] = id_doc
    args_dict['id_good'] = el_dict['id_good']
    args_dict['id_properties'] = el_dict['id_property']
    args_dict['id_series'] = el_dict['id_series']
    args_dict['id_cell'] = el_dict['id_cell']
    #args_dict['id_unit'] = el_dict['id_unit']

    res = get_query_result(query_text, args_dict, True)

    return res
#


def get_query_result(query_text: object, args: object = "", return_dict=False) -> list:
    # **********************

    # global conn
    # get_database_connection()
    try:
        conn = sqlite3.connect(db_path)

    except Error:

        raise ValueError('No connection with database')

    cursor = conn.cursor()
    try:
        if args:
            cursor.execute(query_text, args)
        else:
            cursor.execute(query_text)
    except Exception as e:
        raise e


    # Если надо - возвращаем не результат запроса, а словарь с импортированным результатом
    if return_dict:
        res = [dict(line) for line in
               [zip([column[0] for column in cursor.description], row) for row in cursor.fetchall()]]
    else:
        res = cursor.fetchall()
    conn.commit()
    conn.close()
    return res


def execute_script(query_text):
    # global conn  # = None
    # get_database_connection()
    try:
        conn = sqlite3.connect(db_path)

    except Error:
        raise ValueError('No connection with database')

    cursor = conn.cursor()
    try:
        cursor.executescript(query_text)
        conn.commit()
    except sqlite3.Error as er:
        raise ValueError(er)
    conn.close()


def bulk_query_replace(query_text: str, args: object = "") -> object:
    # **********************
    # global conn
    # get_database_connection()
    conn = None
    try:
        conn = sqlite3.connect(db_path)

    except Error:
        raise ValueError('No connection with database')

    cursor = conn.cursor()
    try:
        if args:
            cursor.executemany(query_text, args)

        conn.commit()
    except sqlite3.Error as er:
        raise ValueError(er)

    res = cursor.fetchall()

    conn.close()
    return res


def get_name_list(str_entty):
    query = "SELECT name FROM " + str_entty
    res = get_query_result(query)
    list_el = []
    # list_el.append(name for name in res)
    for el in res:
        list_el.append(el[0])
    return ";".join(list_el)


def get_by_name(fld, table):
    query = "SELECT id FROM " + table + ' WHERE name = ?'
    res = get_query_result(query, (fld,))

    if len(res) == 0:
        return ""
    else:
        return res[0][0]


def get_constants(need_const=''):
    sql_text = 'Select * from RS_constants'
    res = get_query_result(sql_text)

    # инициализируем константы
    if not res:  # len(res) == 0:
        get_query_result(
            'INSERT INTO RS_constants (use_series, use_properties, use_mark, add_if_not_in_plan, path, delete_files, reserved, allow_overscan) VALUES (?,?,?,?,?,?,?,?)',
            ('0', '0', '0', '0', '//storage/emulated/0/Android/data/ru.travelfood.simple_ui/', '0',
             '0', '0'))  # //storage/emulated/0/download/

        res = get_query_result(sql_text)

    else:  # len(res)>0:
        if need_const:
            ls = ['id', 'use_series', 'use_properties', 'use_mark', 'add_if_not_in_plan', 'path', 'delete_files',
                  'reserved', 'allow_overscan', 'release']
            x = ls.index(need_const)

            if x > 0:
                return res[0][x]
        else:
            return res[0]



def put_constants(args):
    sql_update_query = """Update RS_constants set use_series = ?, use_properties = ?, use_mark = ?, add_if_not_in_plan=?, path = ?,
     delete_files = ?, allow_overscan = ? """
    res = get_query_result(sql_update_query, args)


def Id_to_HEX(guid):
    x1 = guid[19:23]
    x2 = guid[24: 36]
    x3 = guid[14: 18]
    x4 = guid[9:13]
    x5 = guid[0: 8]

    str_guid = x1 + x2 + x3 + x4 + x5
    return int(str_guid, 16)



#
class Rs_doc():
    id_doc = ''  # str)
    id_str = ''  # str)
    qtty = ''  # str)

    def update_doc_str(self, price=0):
        query = """
        UPDATE RS_docs_table
        SET qtty=?, price=?
        Where id=? """
        res = get_query_result(query, (self.qtty, price, self.id_str))
        return res

    def delete_doc(self):
        query_doc_table = 'DELETE FROM RS_docs_table WHERE id_doc = ?'
        get_query_result(query_doc_table, (self.id_doc,))
        query_doc_table = 'DELETE FROM RS_docs_barcodes WHERE id_doc = ?'
        get_query_result(query_doc_table, (self.id_doc,))
        query_doc = 'DELETE FROM RS_docs WHERE id_doc = ?'
        res = get_query_result(query_doc, (self.id_doc,))

        return res
    def clear_barcode_data(self):
        query_text = ('Update RS_docs_barcodes Set approved = 0 Where id_doc=:id_doc',
        'Delete From RS_docs_barcodes Where  id_doc=:id_doc And is_plan = 0',
        'Update RS_docs_table Set qtty = 0 Where id_doc=:id_doc',
        'Delete From RS_docs_table Where id_doc=:id_doc and is_plan = "False"')
        for el in query_text:
            get_query_result(el, ({'id_doc':self.id_doc}))

    def mark_for_upload(self):
        query = """
        UPDATE RS_docs_table
        SET sent=1
        Where id=? """
        res = get_query_result(query, (self.id_doc))

        return res

    def mark_verified(self, key):
        query = """
                UPDATE RS_docs
                SET verified=?
                Where id_doc=? """
        res = get_query_result(query, (int(key), self.id_doc))

    def find_barcode_in_table(self, search_value: str, func_compared='=?') -> object:

        query = '''
                 SELECT
                 RS_barcodes.id_good,
                 RS_barcodes.id_property,
                 RS_barcodes.id_series,
                 RS_barcodes.id_unit,
                 RS_docs_table.id,
                 RS_docs_table.qtty        
                 FROM RS_barcodes
                 Left join RS_docs_table ON
                 RS_docs_table.id_good= RS_barcodes.id_good and
                 RS_docs_table.id_properties= RS_barcodes.id_property and
                 RS_docs_table.id_unit= RS_barcodes.id_unit And
                 RS_docs_table.id_doc=?
                 where barcode ''' + func_compared
        # query = query + func_compared

        return get_query_result(query, (self.id_doc, search_value), True)

    def find_barcode_in_mark_table(self, search_value: str, func_compared='=?') -> object:
        query = '''
                        SELECT
                        RS_marking_codes.id_good,
                        RS_marking_codes.id_property,
                        RS_marking_codes.id_series,
                        RS_marking_codes.id_unit,
                        RS_docs_table.id,
                        RS_docs_table.qtty        
                        FROM RS_marking_codes
                        Left join RS_docs_table ON
                        RS_docs_table.id_good= RS_marking_codes.id_good and
                        RS_docs_table.id_properties= RS_marking_codes.id_property and
                        RS_docs_table.id_unit= RS_marking_codes.id_unit And
                        RS_docs_table.id_doc=?
                        where mark_code  ''' + func_compared
        # query = query + func_compared

        return get_query_result(query, (self.id_doc, search_value), True)

    def update_doc_table_data(self, elem_for_add: dict, qtty=1):
        # Сначала определим, есть ли в списке товаров документа наш товар:
        qtext = 'Select * from RS_docs_table Where id_doc=? and id_good = ? and id_properties = ? and id_series = ? ' #and id_unit = ?
        args = (self.id_doc, elem_for_add['id_good'], elem_for_add['id_property'], elem_for_add['id_series']) #,elem_for_add['id_unit']
        res = get_query_result(qtext, args, True)
        if res:  # Нашли строки документа, добавляем количество

            el = res[0]
            # if el['qtty']+qtty == 0:
            #     qtext = 'DELETE FROM RS_docs_table  WHERE id = ?'
            #     get_query_result(qtext, (el['id'],))
            # else:
            qtext = 'UPDATE RS_docs_table SET qtty=qtty+?, last_updated = ?, sent = 0  WHERE id = ?'
            get_query_result(qtext, (qtty,  datetime.now().strftime("%Y-%m-%d %H:%M:%S"), el['id']))
        else:  # Такой строки нет, надо добавить
            qtext = 'REPLACE INTO RS_docs_table(id_doc, id_good, id_properties,id_series, id_unit, qtty, price, id_price, is_plan, sent) VALUES (?,?,?,?,?,?,?,?,?,?)'
            get_query_result(qtext, (
                self.id_doc, elem_for_add['id_good'], elem_for_add['id_property'], elem_for_add['id_series'],
                elem_for_add.get('id_unit'), qtty, 0, '', 'False', 0))

        return res

    # Фугкция добавляет строку в маркировку документа на основании баркода (dataMatrix)
    def add_marked_codes_in_doc(self, barcode_info):
        qtext = 'SELECT * FROM RS_marking_codes Where mark_code =?'
        q_doc_text = 'REPLACE INTO RS_docs_barcodes (id_doc, id_barcode, barcode_from_scanner, is_plan, approved) VALUES (?,?,?,?,?)'
        # Ищем код маркировки в таблице RS_marking_codes по GTIN и SERIAL
        res = get_query_result(qtext, ('01' + barcode_info['GTIN'] + '21' + barcode_info['SERIAL'],), True)
        if res:
            # Нашли такой баркод в списке маркировки, заполняем строку маркировки документа

            get_query_result(q_doc_text, (self.id_doc, res[0]['id'], barcode_info['FullBarcode'], '0', '1'), True)
            return res[0]
        else:  # Не нашли - пробуем искать по GTIN в таблице баркодов
            res = self.find_barcode_in_mark_table(self, '01' + barcode_info['GTIN'] + '%', 'Like ?')
            if res:  # Нашли по GTIN, заполняем документ
                el = res[0]
                # Сначала заполним таблицу RS_marking_codes
                qtext = 'REPLACE INTO RS_marking_codes (id, mark_code, id_good, id_property, id_series, id_unit) VALUES (?,?,?,?,?,?)'
                mark_code = '01' + barcode_info['GTIN'] + '21' + barcode_info['SERIAL']
                get_query_result(qtext, (
                    mark_code, mark_code, el['id_good'], el['id_property'], el['id_series'], el['id_unit']))
                # И теперь таблицу документа со ссылкой на RS_marking_codes
                get_query_result(q_doc_text, (self.id_doc, mark_code, barcode_info['FullBarcode'], '0', '1'))
                el['mark_code'] = mark_code
                return el
            else:
                return None


    def add_new_barcode_in_doc_barcodes_table(self, el, barcode_info):
        query_text = '''
        Insert Into RS_docs_barcodes (
        id_doc,
        id_good,
        id_property,
        id_series,
        id_unit,
        barcode_from_scanner,
        approved ,
        GTIN,
        Series) VALUES (?,?,?,?,?,?,?,?,?)'''
        args = (self.id_doc, el['id_good'],el['id_property'],el['id_series'],el['id_unit'],barcode_info['FullCode'],'1', barcode_info['GTIN'], barcode_info['SERIAL'])
        get_query_result(query_text, args)



    # Есть план по количеству  - have_qtty_plan
    # Есть план по списку товаров have_zero_plan
    # КОнтроль планов в документе - control
    # Есть план по маркируемой продукции have_mark_plan
    def process_the_barcode(self, barcode, have_qtty_plan = False, have_zero_plan = False, control = False, have_mark_plan = False,
                            elem = None): # add_if_not_found=False, add_if_not_in_plan=False):
        # Получим структуру баркода
        if barcode[0] == chr(29) and len(barcode) > 31:  # Remove first GS1 char from barcode
            barcode = barcode[1:]
        barcode_info = ui_barcodes.parse_barcode(barcode)
        if barcode_info.__contains__('ERROR'):
            return {'Error': 'Invalid Barcode', 'Descr': 'Неверный штрихкод',
                    'Barcode': barcode_info, 'doc_info': self.id_doc}
        # ... и найдем по нему все что есть в базе
        shema = barcode_info['SCHEME']
        if shema in ['EAN13', 'UNKNOWN']:
            search_value = barcode_info['BARCODE']
        elif shema == 'GS1':
            search_value = barcode_info['GTIN']
        else:  # ******************Сюда можно добавить новые виды штрихкодов ********************
            search_value = barcode_info['BARCODE']

        res = find_barcode_in_barcode_table(search_value)  # Ищет баркод или ГТИИН по общей таблице штрихкодов. Возвращает товар, его вид, характеристику серию итп.
        if not len(res) == 0:
            elem = res[0] #Берем первый результат. В правильном списке штрихкодов не может быть повторений
        else:
            return {'Error': 'NotFound', 'Descr': 'Штрихкод не найден в базе', 'Barcode': barcode}

        use_mark = get_constants('use_mark') == 'true' and elem['use_mark'] == 1

        # Проверяем маркировку
        if use_mark:
            if shema == 'GS1':
                el_marked = None
                # Используем маркировку и товар маркируется
                # Нашли в документе GTIN + серия
                res = find_barcode_in_marking_codes_table(self, barcode_info)

                if res:
                    el_marked = res[0] #Выбираем первую строку из списка (если в таблице штрихкодов порядок, в рес всегда только одна строка)
                else:
                    # Не нашли, проверяем есть ли в документе план и контроль
                    if have_mark_plan and control: #ЕстьПланКОдовМаркировки и контроль
                        return {'Error': 'NotFound', 'Descr': 'Марка не найдена в документе',
                                'Barcode': barcode_info, 'doc_info': self.id_doc}

                # ************

                if el_marked and el_marked['id_good']:  # нашли строку по полному совпадению GTIN и серия, ссылка на товар

                    if el_marked['approved'] == '1':  # Такая марка уже была отсканирована
                        return {'Error': 'AlreadyScanned', 'Descr': 'Такая марка уже была отсканирована',
                                'Barcode': barcode_info, 'doc_info': el_marked}

                # ******************************


            else:
                return {'Error': 'NotValidBarcode',
                        'Descr': 'Товар подлежит маркировке, а по нему отсканирован обычный штрихкод',
                        'Barcode': barcode}

        #Товар в таблице документа (Товар найден в документе)
        res = check_barcode_compliance(elem, self.id_doc)  #Получаем строку таблицы товары документа
        if res: #Товар найден в документе
            if have_qtty_plan: #Есть план по количеству
                if res[0]['qtty_plan'] <= res[0]['qtty']: #Количество товара в документе уже набрано, и мы превышаем план
                    if control:
                        return {'Result': 'Количество план превышено, больше товар в данный документ добавить нельзя',
                                'Error': 'QuantityPlanReached',
                                'barcode': barcode, 'Descr': 'Количество план превышено, больше товар в данный документ добавить нельзя'}

        else: #Товар не найден в документе
            if have_zero_plan and control:
                return {'Result': 'В данный документ нельзя добавить товар не из списка',
                        'Error': 'Zero_plan_error',
                        'barcode': barcode,
                        'Descr': 'В данный документ нельзя добавить товар не из списка'}


        # Блок добавления товара в документ
        if use_mark:
            # Добавляем товар в таблицу маркировки
            if el_marked and el_marked['id_good']: #Товар был найден, только обновляем уже найденную строку
                query_text = 'Update  RS_docs_barcodes SET approved=?, barcode_from_scanner=? Where id=?'
                get_query_result(query_text, ('1', barcode, int(el_marked['id'])))
            else: #Добавляем новую строку в таблицу баркодов документа
                self.add_new_barcode_in_doc_barcodes_table(self, elem , barcode_info)


        # Обновляем таблицу товары
        self.update_doc_table_data(self, elem, 1)

        return {'Result': 'Марка добавлена в документ', 'Error': None,
                        'barcode': barcode_info['GTIN'] + barcode_info['SERIAL']}


    def add(self, args):
        query = 'INSERT INTO RS_docs(id_doc, doc_type, doc_n, doc_date, id_countragents, id_warehouse, verified, sent) VALUES (?,?,?,?,?,?,0,0)'
        res = get_query_result(query, args)

    def get_new_id(self):
        query = 'select max_id_doc from RS_constants'
        res = get_query_result(query)
        if len(res) == 0:
            return '1'
        else:
            val = res[0][0]
            if val is None:
                return '1'
            else:
                query = 'UPDATE RS_constants SET max_id_doc = ?'
                get_query_result(query, (int(val) + 1,))
                return str(int(val) + 1)

class Rs_adr_doc():
    id_doc = ''  # str)
    id_str = ''  # str)
    qtty = ''  # str)

    def update_doc_str(self):
        query = """
        UPDATE RS_adr_docs_table
        SET qtty=?
        Where id=? """
        res = get_query_result(query, (self.qtty, self.id_str))
        return res


    def clear_barcode_data(self):
        query_text = ('Update RS_adr_docs_table Set qtty = 0 Where id_doc=:id_doc',
        'Delete From RS_adr_docs_table Where id_doc=:id_doc and is_plan = "False"')
        for el in query_text:
            get_query_result(el, ({'id_doc':self.id_doc}))


    def delete_doc(self):
        query_doc_table = 'DELETE FROM RS_adr_docs_table WHERE id_doc = ?'
        get_query_result(query_doc_table, (self.id_doc,))
        # query_doc_table = 'DELETE FROM RS_docs_barcodes WHERE id_doc = ?'
        # get_query_result(query_doc_table, (self.id_doc,))
        query_doc = 'DELETE FROM RS_adr_docs WHERE id_doc = ?'
        res = get_query_result(query_doc, (self.id_doc,))

        return res
    # def clear_barcode_data(self):
    #     query_text = ('Update RS_docs_barcodes Set approved = 0 Where id_doc=:id_doc',
    #     'Delete From RS_docs_barcodes Where  id_doc=:id_doc And is_plan = 0',
    #     'Update RS_docs_table Set qtty = 0 Where id_doc=:id_doc',
    #     'Delete From RS_docs_table Where id_doc=:id_doc and is_plan = "False"')
    #     for el in query_text:
    #         get_query_result(el, ({'id_doc':self.id_doc}))

    def mark_for_upload(self):
        query = """
        UPDATE RS_adr_docs_table
        SET sent=1
        Where id=? """
        res = get_query_result(query, (self.id_doc))

        return res

    def mark_verified(self, key):
        query = """
                UPDATE RS_adr_docs
                SET verified=?
                Where id_doc=? """
        res = get_query_result(query, (int(key), self.id_doc))

    def find_barcode_in_table(self, search_value: str, func_compared='=?') -> object:

        query = '''
                 SELECT
                 RS_barcodes.id_good,
                 RS_barcodes.id_property,
                 RS_barcodes.id_series,
                 RS_barcodes.id_unit,
                 RS_docs_adr_table.id,
                 RS_docs_adr_table.qtty        
                 FROM RS_barcodes
                 Left join RS_docs_adr_table ON
                 RS_docs_adr_table.id_good= RS_barcodes.id_good and
                 RS_docs_adr_table.id_properties= RS_barcodes.id_property and
                 RS_docs_adr_table.id_unit= RS_barcodes.id_unit And
                 RS_docs_adr_table.id_doc=?
                 where barcode ''' + func_compared
        # query = query + func_compared

        return get_query_result(query, (self.id_doc, search_value), True)

    # def find_barcode_in_mark_table(self, search_value: str, func_compared='=?') -> object:
    #     query = '''
    #                     SELECT
    #                     RS_marking_codes.id_good,
    #                     RS_marking_codes.id_property,
    #                     RS_marking_codes.id_series,
    #                     RS_marking_codes.id_unit,
    #                     RS_docs_table.id,
    #                     RS_docs_table.qtty
    #                     FROM RS_marking_codes
    #                     Left join RS_docs_table ON
    #                     RS_docs_table.id_good= RS_marking_codes.id_good and
    #                     RS_docs_table.id_properties= RS_marking_codes.id_property and
    #                     RS_docs_table.id_unit= RS_marking_codes.id_unit And
    #                     RS_docs_table.id_doc=?
    #                     where mark_code  ''' + func_compared
        # query = query + func_compared

        return get_query_result(query, (self.id_doc, search_value), True)

    def update_doc_table_data(self, elem_for_add: dict, qtty=1, cell_id = None, table_type = 'out'):
        #Ищем ячейку по имени, нам нужен ID
        # res  = get_query_result('Select id From RS_cells Where name = ?',(cell_name,))
        #
        # cell_id = res[0][0] if res else None

        # Сначала определим, есть ли в списке товаров документа наш товар:
        qtext = 'Select * from RS_adr_docs_table Where id_doc=? and id_good = ? and id_properties = ? and id_series = ?  and (id_cell=?  OR id_cell= "" OR id_cell is Null)'  #and id_unit = ?
        args = (self.id_doc, elem_for_add['id_good'], elem_for_add['id_property'], elem_for_add['id_series'], cell_id) #,elem_for_add['id_unit']
        res = get_query_result(qtext, args, True)
        if res:  # Нашли строки документа, добавляем количество

            el = res[0]
            # if el['qtty']+qtty == 0:
            #     qtext = 'DELETE FROM RS_docs_table  WHERE id = ?'
            #     get_query_result(qtext, (el['id'],))
            # else:
            qtext = 'UPDATE RS_adr_docs_table SET qtty=qtty+?, last_updated = ?, id_cell = ?  WHERE id = ?'
            get_query_result(qtext, (qtty,  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),cell_id, el['id']))
        else:  # Такой строки нет, надо добавить
            qtext = 'REPLACE INTO RS_adr_docs_table(id_doc, id_good, id_properties,id_series, id_unit, qtty, is_plan, id_cell, table_type) VALUES (?,?,?,?,?,?,?,?,?)'
            get_query_result(qtext, (
                self.id_doc, elem_for_add['id_good'], elem_for_add['id_property'], elem_for_add['id_series'],
                elem_for_add['id_unit'], qtty, 'False',cell_id, table_type))

        return res


    # Есть план по количеству  - have_qtty_plan
    # Есть план по списку товаров have_zero_plan
    # КОнтроль планов в документе - control
    # Есть план по маркируемой продукции have_mark_plan
    def process_the_barcode(self, barcode, have_qtty_plan = False, have_zero_plan = False, control = False, cell_id = None): # add_if_not_found=False, add_if_not_in_plan=False):
        # Получим структуру баркода
        if barcode[0] == chr(29) and len(barcode) > 31:  # Remove first GS1 char from barcode
            barcode = barcode[1:]
        barcode_info = ui_barcodes.parse_barcode(barcode)
        if barcode_info.__contains__('ERROR'):
            return {'Error': 'Invalid Barcode', 'Descr': 'Неверный штрихкод',
                    'Barcode': barcode_info, 'doc_info': self.id_doc}
        # ... и найдем по нему все что есть в базе
        shema = barcode_info['SCHEME']
        if shema in ['EAN13', 'UNKNOWN']:
            search_value = barcode_info['BARCODE']
        elif shema == 'GS1':
            search_value = barcode_info['GTIN']
        else:  # ******************Сюда можно добавить новые виды штрихкодов ********************
            search_value = barcode_info['BARCODE']

        res = find_barcode_in_barcode_table(search_value)  # Ищет баркод или ГТИИН по общей таблице штрихкодов. Возвращает товар, его вид, характеристику серию итп.
        if not len(res) == 0:
            elem = res[0] #Берем первый результат. В правильном списке штрихкодов не может быть повторений
        else:
            return {'Error': 'NotFound', 'Descr': 'Штрихкод не найден в базе', 'Barcode': barcode}

        elem['id_cell'] = cell_id

        #Товар в таблице документа (Товар найден в документе)
        res = check_adr_barcode_compliance(elem, self.id_doc)  #Получаем строку таблицы товары документа
        if res: #Товар найден в документе
            if have_qtty_plan: #Есть план по количеству
                if res[0]['qtty_plan'] <= res[0]['qtty']: #Количество товара в документе уже набрано, и мы превышаем план
                    if control:
                        return {'Result': 'Количество план превышено, больше товар в данный документ добавить нельзя',
                                'Error': 'QuantityPlanReached',
                                'barcode': barcode, 'Descr': 'Количество план превышено, больше товар в данный документ добавить нельзя'}

        else: #Товар не найден в документе
            if have_zero_plan and control:
                return {'Result': 'В данный документ нельзя добавить товар не из списка',
                        'Error': 'Zero_plan_error',
                        'barcode': barcode,
                        'Descr': 'В данный документ нельзя добавить товар не из списка'}


        # Обновляем таблицу товары
        self.update_doc_table_data(self, elem, 1, cell_id)

        return {'Result': 'Марка добавлена в документ', 'Error': None,
                        'barcode': barcode_info['GTIN'] + barcode_info['SERIAL']}


    def add(self, args):
        query = 'INSERT INTO RS_adr_docs(id_doc, doc_type, doc_n, doc_date, id_warehouse, verified, sent) VALUES (?,?,?,?,?,0,0)'
        res = get_query_result(query, args)

    def get_new_id(self):
        query = 'select max_id_doc from RS_constants'
        res = get_query_result(query)
        if len(res) == 0:
            return '1'
        else:
            val = res[0][0]
            if val is None:
                return '1'
            else:
                query = 'UPDATE RS_constants SET max_id_doc = ?'
                get_query_result(query, (int(val) + 1,))
                return str(int(val) + 1)


    def find_cell(self, barcode):
        qtext = '''Select * from RS_cells WHere RS_cells.barcode = ?'''
        res = get_query_result(qtext, (barcode, ), True)
        result = None
        if res:
            result = res[0]

        return result


def execute_query(q_index, q_text, args, in_dict):
    if query_list.empty():
        start_queue =True
    query_list.put({'q_index':q_index, 'q_text':q_text, 'args':args, 'in_dict':in_dict})
    while True:
        if start_queue:
            get_query_result()


def write_error_on_log(Err_value):
    if Err_value:
        qtext = 'Insert into Error_log(log) Values(?)'
        get_query_result(qtext, (Err_value,))





