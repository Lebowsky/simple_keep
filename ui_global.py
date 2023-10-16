from typing import List
import sqlite3
from sqlite3 import Error
import os
import queue



query_list = queue.Queue()
# Вот таким незатейливым методом определяем, мы запустились на компе или на ТСД **
# Ну и в зависимости от, используем базу ****
if os.path.exists('//data/data/ru.travelfood.simple_ui/databases/'): #локально
    db_path = '//data/data/ru.travelfood.simple_ui/databases/SimpleKeep'  # rightscan'
else:
    db_path = file_abs_path = os.path.abspath('./SimpleKeep.db')  # D:\PythonProjects\RightScan\SUI_noPony\

conn = None



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





