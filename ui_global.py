from typing import List
import sqlite3
from sqlite3 import Error
import os
import ui_form_data
import queue



query_list = queue.Queue()
# Вот таким незатейливым методом определяем, мы запустились на компе или на ТСД **
# Ну и в зависимости от, используем базу ****
if os.path.exists('//data/data/ru.travelfood.simple_ui/databases/'): #локально
    db_path = '//data/data/ru.travelfood.simple_ui/databases/SimpleKeep'  # rightscan'
else:
    db_path = file_abs_path = os.path.abspath('./SimpleKeep.db')  # D:\PythonProjects\RightScan\SUI_noPony\

conn = None



def find_barcode_in_marking_codes_table(self, struct_barcode: list):
    """Функция получает строки маркировки документа по значению маркировки"""

    query_text = ui_form_data.get_query_mark_find_in_doc()
    args_dict = {}
    args_dict['GTIN'] = struct_barcode['GTIN']
    args_dict['Series'] = struct_barcode['SERIAL']
    args_dict['id_doc'] = self.id_doc

    res = get_query_result(query_text, args_dict, True)
    return res


def find_barcode_in_barcode_table(barcode: str):
    query_text = ui_form_data.get_barcode_query()
    res = get_query_result(query_text, (barcode,), True)
    return res


def check_barcode_compliance(el_dict: dict, id_doc):
    """ 1 Такой товар в принципе есть в документе """

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
    """ 1 Такой товар в принципе есть в документе """

    query_text =  '''
    SELECT ifnull(qtty_plan,0) as qtty_plan,
    ifnull(qtty,0) as qtty, id_good, id_cell, id, use_series
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


def get_query_result(query_text: str, args = "", return_dict=False) -> list:
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

def bulk_query(q: str, args: List[tuple]):
    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.Error:
        raise ValueError('No connection with database')

    cursor = conn.cursor()

    try:
        cursor.executemany(q, args)
        conn.commit()
    except sqlite3.Error as er:
        raise ValueError(er)

    conn.close()





