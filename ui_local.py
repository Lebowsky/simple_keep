from pony.orm import Database, Required, PrimaryKey, Optional
import datetime
import sqlite3
from sqlite3 import Error
import ui_barcodes

# import ui_global

db = Database()
db_path = 'D:\PythonProjects\RightScan\SUImain\SimpleWMS.db'
db.bind(provider='sqlite', filename=db_path, create_db=True)


# Штрихкоды barcode, id_good, id_property, id_unit
class RS_barcodes(db.Entity):
    barcode = Required(str)  # , lenght=200)
    id_good = Required(str)  # , lenght=36)
    id_property = Optional(str)  # , lenght=36)
    id_series = Optional(str)
    id_unit = Optional(str)  # , lenght=36)

# Номенклатура
class RS_goods(db.Entity):
    id_elem = PrimaryKey(str)  # , lenght=36)
    code = Required(str)
    name = Optional(str)
    art = Optional(str)
    unit = Optional(str)
    type_good = Optional(str)  # Вид номенклатуры


# Характеристики номенклатуры
class RS_properties(db.Entity):
    id_elem = Required(str)  # , lenght=36)
    id_owner = Required(str)  # , lenght=36)  # id Номенклатуры
    name = Optional(str)


# Упаковки Единицы измерения
class RS_units(db.Entity):
    id_elem = PrimaryKey(str)
    id_owner = Required(str)  # , lenght=36)  # id Номенклатуры
    code = Required(str)
    name = Optional(str)
    nominator = Required(int)  # Числитель
    denominator = Required(int)  # Знаменатель
    int_reduction = Optional(str)  # Международное сокращение


# Виды номенклатуры
class RS_types_goods(db.Entity):
    id_elem = PrimaryKey(str)  # , lenght=36)
    name = Optional(str)


# Серии номенклатуры
class RS_series(db.Entity):
    id_elem = PrimaryKey(str)
    name = Optional(str)
    best_before = Optional(str)  # Годен до
    type_goods = Optional(str)  # Вид номенклатуры (id RS_types_goods )
    number = Optional(str)
    production_date = Optional(str)  # Дата производства


# Контрагенты
class RS_countragents(db.Entity):
    id_elem = PrimaryKey(str)
    name = Optional(str)
    full_name = Optional(str)
    inn = Optional(str)
    kpp = Optional(str)


# Склады
class RS_warehouses(db.Entity):
    id_elem = PrimaryKey(str)
    name = Optional(str)


# Классификатор единиц измерения
class RS_classifier_units(db.Entity):
    id_elem = PrimaryKey(str)  # , lenght=36)
    code = Required(str)
    name = Required(str)


# Виды цен номенклатуры
class RS_price_types(db.Entity):
    id = PrimaryKey(str)
    name = Required(str)

#Цены номенклатуры
class RS_prices(db.Entity):
    id_price_types = Required(str)
    id_goods = Required(str)
    id_properties = Optional(str)
    price = Optional(float)
    id_unit = Optional(str)


# Все документы списком
class RS_docs(db.Entity):
    # id_doc, doc_type, doc_n, doc_data, good_id, good_mame, ed_izm, qtty, qtty_fact
    id_doc = PrimaryKey(str)
    doc_type = Required(str)
    doc_n = Required(str)
    doc_data = Required(str)
    id_countragents = Optional(str)
    id_warehouse = Optional(str)
    verified = Optional(int, sql_default=0)
    sent = Optional(int, sql_default=0)
    created_at = Optional(datetime.datetime, sql_default='CURRENT_TIMESTAMP')


# Табличная часть документов
class RS_docs_table(db.Entity):
    id_doc = Required(str)
    id_good = Optional(str)
    id_properties = Optional(str)
    id_series = Optional(str)
    id_unit = Optional(str)
    qtty = Optional(float, sql_default=0)
    qtty_plan = Optional(float, sql_default=0)
    price = Optional(float, sql_default=0)
    id_price = Optional(str)
    sent = Optional(int, sql_default=0)


class RS_constants(db.Entity):
    use_series = Required(str, sql_default='true')
    use_properties = Required(str, sql_default='true')
    reserved = Optional(str)


# Описание объектов базы и их изменение
class Rs_doc():
    id_doc = Optional(str)
    id_str = Optional(str)
    qtty = Optional(float)

    def update_doc_str(self, price=0):
        query = """
        UPDATE RS_docs_table
        SET qtty=?, price=?
        Where id=? """
        res = get_query_result(query, (self.qtty, price,  self.id_str))
        return res

    def delete_doc(self):
        query_doc_table = 'DELETE FROM RS_docs_table WHERE id_doc = ?'
        get_query_result(query_doc_table, (self.id_doc,))
        query_doc = 'DELETE FROM RS_docs WHERE id_doc = ?'
        res = get_query_result(query_doc, (self.id_doc,))

        return res

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
        #query = query + func_compared


        return get_query_result(query, (self.id_doc, search_value))


    def find_barcode_on_doc(self, barcode):
        #Получим структуру баркода
        barcode_info = ui_barcodes.parse_barcode(barcode)
        #... и найдем по нему все что есть в базе
        #
        barinfo = barcode_info['BARCODE']
        shema = barcode_info['BARCODE']['SCHEME']
        search_value =''
        if shema == 'EAN13':
            search_value = barcode_info['BARCODE']['BARCODE']
            res = self.find_barcode_in_table(self, search_value)
        elif shema == 'GS1':

            search_value = '01' + barcode_info['BARCODE']['GTIN'] +'21'+ barcode_info['BARCODE']['SERIAL']
            res = self.find_barcode_in_table(self, search_value)



        if not len(res) == 0:
            elem = res[0]
        else: #Ничего не нашли, пробуем искать только по GTIN
            search_value = '01'+barcode_info['BARCODE']['GTIN']+'21%'

            res = self.find_barcode_in_table(self, search_value, ' LIKE ?')
            if not len(res)==0:

                elem = res[0]
            else: #Такого товара в базе нет
                return None

        if elem[3]==None:
            query='REPLACE INTO RS_docs_table(id_doc, id_good, id_properties,id_series, id_unit, qtty, price, id_price) VALUES (?,?,?,?,?,?,?,?)'
            get_query_result(query, (self.id_doc, elem[0], elem[1],'',elem[2],1,0,''))
        else:
            query='UPDATE RS_docs_table SET qtty=qtty+? WHERE id = ?'
            get_query_result(query, (1,elem[3]))
        return res


    def add(self, args):
        query = 'INSERT INTO RS_docs(id_doc, doc_type, doc_n, doc_data, id_countragents, id_warehouse, verified, sent) VALUES (?,?,?,?,?,?,1,1)'
        res = get_query_result(query, args)

def init():
    db.generate_mapping(create_tables=True)
    res = get_constants()
    param = 'true'
    # инициализируем константы
    if len(res) == 0:
        get_query_result(
            'INSERT INTO RS_constants (use_series, use_properties, use_mark, reserved) VALUES (' + param + ',' + param + ',' + param + ',' + param + ')')  # ,('true','true', 'nest')) #


def get_query_result(query_text, args=""):
    # **********************

    conn = None
    try:
        conn = sqlite3.connect(db_path)

    except Error:
        raise ValueError('No connection with database')

    cursor = conn.cursor()
    if args:
        cursor.execute(query_text, args)
    else:
        cursor.execute(query_text)

    res = cursor.fetchall()
    conn.commit()
    conn.close()
    return res


def get_name_list(str_entty):
    query = "SELECT name FROM " + str_entty
    res = get_query_result(query)
    list_el=[]
    for el in res:
        list_el.append(el[0])
    return ";".join(list_el)


def get_by_name(fld, table):
    query = "SELECT id_elem FROM " + table + ' WHERE name = ?'
    res = get_query_result(query, (fld,))

    if len(res)==0:
        return ""
    else:
        return res[0][0]

def get_constants(need_const=''):
    sql_text = 'Select * from RS_constants'
    res = get_query_result(sql_text)
    if need_const == '':
        return res
    else:
        return res[0]


def put_constants(args):
    sql_update_query = """Update RS_constants set use_series = ?, use_properties = ?, use_mark = ? """
    res = get_query_result(sql_update_query, args)


