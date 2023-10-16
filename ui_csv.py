import csv
import os
#import re

import ui_barcodes
import ui_global
from datetime import datetime

class Query_text_storage:
    RS_goods = 'REPLACE INTO RS_goods (  id, code, art, name, unit, type_good, description) VALUES (?,?,?,?,?,?,?)'
    RS_properties = 'REPLACE INTO RS_properties (  id , id_owner, name) VALUES '
    RS_units = 'REPLACE INTO RS_units (  id,id_owner, code, name, nominator, denominator, int_reduction) VALUES (?,?,?,?,?,?,?)'
    RS_types_goods = 'REPLACE INTO RS_types_goods (  id, name, use_mark) VALUES (?,?, ?)'
    RS_series = 'REPLACE INTO RS_series (  id, name, best_before, type_goods, number, production_date) VALUES'
    RS_countragents = 'REPLACE INTO RS_countragents (  id, name, full_name, inn, kpp) VALUES '
    RS_warehouses = 'REPLACE INTO RS_warehouses (  id, name) VALUES (?,?)'
    RS_price_types = 'REPLACE INTO RS_price_types (id, name) VALUES (?,?)'
    RS_barcodes = 'REPLACE INTO RS_barcodes (barcode, id_good, id_property, id_series, id_unit, ratio) VALUES (?,?,?,?,?,?)'
    RS_marking_codes = 'REPLACE INTO RS_marking_codes (id, mark_code, id_good, id_property, id_series, id_unit) VALUES (?,?,?,?,?,?)'
    RS_prices = 'REPLACE INTO RS_prices (id_price_types, id_goods, id_properties, price, id_unit) VALUES '
    RS_docs = 'REPLACE INTO RS_docs (id_doc, doc_type, doc_n, doc_date, id_countragents, id_warehouse, control) VALUES (?,?,?,?,?,?,?)'
    RS_docs_table = 'REPLACE INTO RS_docs_table (id_doc, id_good, id_properties, id_series, id_unit, qtty, qtty_plan, price, id_price) VALUES (?,?,?,?,?,?,?,?,?)'
    RS_docs_barcodes = 'REPLACE INTO RS_docs_barcodes (id_doc, id_good, id_property, id_series, id_unit, GTIN, Series, is_plan) VALUES (?,?,?,?,?,?,?,?)'

def get_query_text_export():
    old_q =  '''
       SELECT 
        '0' AS GTIN,
        RS_marking.id_good,
        RS_marking.name, 
        1 as DeclaredQuantity,
        CASE approved
            WHEN '1' THEN 1
            ELSE 0
        END AS CurrentQuantity,
        barcode_from_scanner as Марка,
        RS_marking.mark_code AS МаркаИСМП,
        RS_marking.id_property as Инвойс,
        'Чужой' as Принадлежность 

        FROM RS_docs_barcodes 

        LEFT JOIN (SELECT 
                    RS_marking_codes.id AS id_barcode,
                    RS_marking_codes.mark_code AS mark_code,
                    id_good,
                    id_property,
                    id_series,
                    id_unit,
                    RS_goods.name,
                    RS_goods.code

                    FROM RS_marking_codes
                    LEFT JOIN RS_goods 
                    ON RS_goods.id  = RS_marking_codes.id_good
                    WHERE RS_marking_codes.id IN 
                        (SELECT id_barcode FROM RS_docs_barcodes 
                        WHERE RS_docs_barcodes.id_doc = :id_doc)) AS RS_marking
        ON RS_docs_barcodes.id = RS_marking.id_barcode  

        WHERE RS_docs_barcodes.id_doc = :id_doc
'''
    return '''
    SELECT 
    RS_docs_barcodes.GTIN,
    RS_docs_barcodes.id_good as id_good,
    RS_goods.name as Name,
    1 as DeclaredQuantity,
    RS_docs_barcodes.id_property, 
    CASE approved
            WHEN '1' THEN 1
            ELSE 0
        END AS CurrentQuantity,
    RS_docs_barcodes.barcode_from_scanner as mark,
    RS_docs_barcodes.Series as Series,
    'Чужой' as Owner
    
    FROM RS_docs_barcodes
    
    LEFT JOIN RS_goods
    ON RS_docs_barcodes.id_good = RS_goods.id
    WHERE RS_docs_barcodes.id_doc = ?
    '''

def normalize_gtin(gtin: str) -> str:
    a = len(gtin)
    if a > 14:
        return gtin[:-14]
    else:
        return '0' * (14 - a) + gtin


def load_from_csv(path='', file=''):
    with open(path, 'r', newline='', encoding='utf-8') as csvfile:

        my_reader = csv.reader(csvfile, dialect='excel', delimiter=';', quotechar='"')
        for row in my_reader:
            is_doc = True if row[0] == '#{Document}' else False

            is_goods = True if row[0] == 'GTIN' else False
            break

        # re.fullmatch(r'\d{13}', barcode).string == barcode:
    current_date = datetime.now().strftime("%d-%m-%Y")
    # file = file + (" " * 15) #чтобы не натыкаться на out of range в текстовом имени - добавим 15 пробелов
    if is_doc:  # file[:6] == 'doc_in':
        # Загружаем документы
        with open(path, 'r', newline='', encoding='utf-8') as csvfile:

            my_reader = csv.reader(csvfile, dialect='excel', delimiter=';', quotechar='"')

            rs_doc_data = []
            rs_doc_table_data = []
            rs_doc_barcode = []
            rs_marking_codes = []
            rs_properties = []
            temp_doc_n = ''
            temp_good = ''
            doc_num = ui_global.Rs_doc.get_new_id('')
            for row in my_reader:
                if my_reader.line_num > 5:  # Заголовки таблицы

                    if temp_good != row[0]:
                        #id_doc, id_good, id_properties, id_series, id_unit, qtty, qtty_plan, price, id_price
                        rs_doc_table_data.append(
                            (doc_num, row[0], '', '', row[1] + row[0], int(row[7]), int(row[6]), '', ''))
                        curr_count = rs_doc_table_data.__len__() - 1
                        temp_good = row[0]
                    else:
                        # добавим количество в строку, для этого преобразуем ее в Лист, поменяем количество и засунем обратно в кортеж
                        lst = list(rs_doc_table_data[curr_count])
                        lst[6] = int(lst[6]) + int(row[6])
                        rs_doc_table_data[curr_count] = tuple(lst)
                        # rs_doc_table_data[curr_count][6]=int(rs_doc_table_data[curr_count][6]) + int(row[6])
                    if row[5]:
                        # id_doc, id_good, id_properties, id_series, id_unit, GTIN, Series, is_plan
                        rs_doc_barcode.append((doc_num,row[0], '', '',row[1] + row[0], row[2], row[5][-13:], '1'))
                        # RS_marking_codes(id, mark_code, id_good, id_property, id_series, id_unit) VALUES(?, ?, ?, ?, ?, ?)
                        rs_marking_codes.append((row[5], row[5], row[0], '', '', row[1] + row[0]))

                elif my_reader.line_num == 3:
                    if row[0]:
                        doc_num = row[0]

                    rs_doc_data.append((doc_num, 'Инвойс', doc_num, current_date, '001', '001', get_status(row[6])))
                elif my_reader.line_num == 5:
                    list_headers = row.copy()

        # Заполняем таблицы
        ui_global.bulk_query_replace(Query_text_storage.RS_docs, rs_doc_data)
        ui_global.bulk_query_replace(Query_text_storage.RS_docs_table, rs_doc_table_data)
        ui_global.bulk_query_replace(Query_text_storage.RS_docs_barcodes, rs_doc_barcode)
        ui_global.bulk_query_replace(Query_text_storage.RS_marking_codes, rs_marking_codes)

        # По документам, где есть запланированные марки, добавим признак
        qtext = 'SELECT id_doc, COUNT(is_plan) as is_plan FROM RS_docs_barcodes WHERE is_plan = "1" '
        res = ui_global.get_query_result(qtext, '', True)
        qtext = 'UPDATE RS_docs SET add_mark_selection = ? WHERE id_doc = ?'
        # ---
        for el in res:
            if el['is_plan'] > 0:
                ui_global.get_query_result(qtext, (1, el['id_doc']))
            else:
                ui_global.get_query_result(qtext, (0, el['id_doc']))
        return 200




    if is_goods:  # elif file[:10] == 'PARFUM-ALL':
        # Добавим тип товара для всех таблиц
        qtext = 'REPLACE INTO RS_types_goods (  id, name, use_mark) VALUES (?,?,?)'
        ui_global.get_query_result(qtext, ('001', 'Товар', 1))

        with open(path, 'r', newline='', encoding='utf-8') as csvfile:

            my_reader = csv.reader(csvfile, dialect='excel', delimiter=';', quotechar='"')

            rs_goods_data = []
            rs_barcodes_data = []
            rs_units_data = []
            # RS_warehouses(  id, name)
            rs_warehouses = [['001', 'Основной']]
            # RS_types_goods (  id, name)
            rs_types_goods_data = [['001', 'Товар', 1]]
            part_count = 1000

            for row in my_reader:
                if my_reader.line_num == 1:  # Заголовки таблицы
                    list_headers = row.copy()
                else:  # заполняем таблицы параметров запроса к SQL
                    #   id, co de, art, name, unit, type_good, description
                    rs_goods_data.append((row[2], row[3], row[5], row[4], row[1], 'Товар', row[15]))
                    #   id, id_owner, code, name, nominator, denominator, int_reduction
                    rs_units_data.append((row[1] + row[2], row[2], row[1], row[1], 1, 1, row[1]))
                    # barcode, id_good, id_property, id_series, id_unit
                    gtin = normalize_gtin(row[0])
                    #barcode, id_good, id_property, id_series, id_unit, ratio
                    rs_barcodes_data.append((gtin, row[2], '', '', row[1] + row[2],1))

                # Каждые 1000 строк записываем в базу
                if my_reader.line_num == part_count:
                    part_count += 1000
                    ui_global.bulk_query_replace(Query_text_storage.RS_goods, rs_goods_data)
                    ui_global.bulk_query_replace(Query_text_storage.RS_units, rs_units_data)
                    ui_global.bulk_query_replace(Query_text_storage.RS_barcodes, rs_barcodes_data)
                    rs_goods_data = []
                    rs_barcodes_data = []
                    rs_units_data = []

        ui_global.bulk_query_replace(Query_text_storage.RS_warehouses, rs_warehouses)
        ui_global.bulk_query_replace(Query_text_storage.RS_types_goods, rs_types_goods_data)
        ui_global.bulk_query_replace(Query_text_storage.RS_goods, rs_goods_data)
        ui_global.bulk_query_replace(Query_text_storage.RS_units, rs_units_data)
        ui_global.bulk_query_replace(Query_text_storage.RS_barcodes, rs_barcodes_data)

        return 200

    return 404

def get_status(value):
    if value in ('true', 'True', 1):
        return 1
    else:
        return 0

def list_folder(path: str, delete_files: bool):
    # try:
    aa = 0
    total = 0
    for file in os.listdir(path):
        total += 1
        if file.endswith(".csv"):
            filename = file + (" " * 15)  # чтобы не натыкаться на out of range в текстовом имени - добавим 15 пробелов
            if filename[:6] == 'doc_in' or filename[:14] == 'initial_dicts_':
                aa += 1
                ans = load_from_csv(path + file, file)
                if ans == 200 and delete_files == 'true':
                    os.remove(path + file)

    return 'Загрузка завершена, загружено ' + str(aa) + ' файлов из ' + str(total)
    # except:
    #   return 'Ошибка при загрузке файла'


def export_csv(path, IP, AndroidID):
    docs = ui_global.get_query_result('SELECT id_doc, doc_n from RS_docs Where sent <> 1')
    count = 0
    doc_list = []
    qtext = get_query_text_export()
    for doc_item in docs:
        res = ui_global.get_query_result(qtext, (doc_item[0],), True)
        count += 1
        doc_list.append(path + os.sep +  'doc_out_' + doc_item[1] + '.csv')
        with open(path + os.sep + 'doc_out_' + doc_item[1] + '.csv', 'w', newline='', encoding='utf-8') as csvfile:
            my_reader = csv.writer(csvfile, dialect='excel', delimiter=';', quotechar='"')
            my_reader.writerow(('Name', 'UserName', 'DeviceId', 'DeviceIP'))
            my_reader.writerow(('Приход на склад ' + doc_item[1], 'Москва1', AndroidID, IP))
            my_reader.writerow(('GTIN', 'КодВУчетнойСистеме', 'Наименование', 'DeclaredQuantity', 'CurrentQuantity',
                                'Коробка', 'Марка', 'МаркаИСМП', 'Инвойс', 'Принадлежность'))
            for el in res:
                # gtin = ui_barcodes.parse_barcode(el['МаркаИСМП'])
                # el['GTIN'] = gtin['GTIN']
                my_reader.writerow((
                    el['GTIN'], el['id_good'], el['Name'], el['DeclaredQuantity'], el['CurrentQuantity'], '',
                    el['mark'], '01' + el['GTIN'] + '21' + el['Series'], el['id_property'], el['Owner']))

    return doc_list #было str(count) + ' документов'
# export_csv('ОбменТСД/НА/') #'


# open_files_net('', 'D:/PythonProjects/RightScan/SUImain/ОбменТСД/НА/initial_dicts_01.csv', 'initial_dicts_01.csv')
# open_files_net('', 'D:/PythonProjects/RightScan/SUImain/ОбменТСД/НА/doc_1.csv','doc_1.csv')
