import json

import ui_csv
import os
import ui_global
import ui_form_data
import ui_models

from new_handlers import *


def delete_barcode_screen_start(hashMap, _files=None, _data=None):
    # Находим ID документа
    barcode_data = json.loads(hashMap.get('barcode'))['barcode']
    # Найдем нужные поля запросом к базе
    qtext = ui_form_data.get_markcode_query()
    args = {'id_doc': hashMap.get('id_doc'),
            'GTIN': barcode_data['GTIN'], 'Series': barcode_data['SERIAL']}

    res = ui_global.get_query_result(qtext, args, True)

    hashMap.put('currentStr', json.dumps(res[0]))
    hashMap.put("CurStr", str(res[0]['CurStr']))
    hashMap.put("good", res[0]['good_name'])
    hashMap.put("'code_art'", res[0]['good_code'])
    hashMap.put("unit_name", str(res[0]['unit']))
    hashMap.put('barcode_value', '01' + barcode_data['GTIN'] + '21' + barcode_data['SERIAL'])

    return hashMap


def delete_barcode_screen_click(hashMap, _files=None, _data=None):
    listener = hashMap.get("listener")
    if listener == "btn_barcode_cancel":

        hashMap.put("ShowScreen", "Документ товары")

    elif listener == "btn_barcode_delete":
        doc = ui_global.Rs_doc
        doc.id_doc = hashMap.get('id_doc')
        current_barcode_str = int(hashMap.get("CurStr"))
        el = json.loads(hashMap.get('currentStr'))

        # doc.id_str = int(current_elem['key'])
        # doc.qtty = float(hashMap.get('qtty'))
        # doc.update_doc_str(doc, hashMap.get('price'))
        query_text = 'Update  RS_docs_barcodes SET approved=? Where id=?'
        ui_global.get_query_result(query_text, ('0', current_barcode_str))
        doc.update_doc_table_data(doc, el, -1)

        hashMap.put("ShowScreen", "Документ товары")

    elif listener == "BACK_BUTTON":
        hashMap.put("ShowScreen", "Документ товары")
    elif listener == 'ON_BACK_PRESSED':
        hashMap.put("ShowScreen", "Документ товары")

    return hashMap

def read_file(hashMap, imageBytes):
    listener = hashMap.get("listener") or 'None'
    #hashMap.put('toast', listener)
    if listener == 'None':

        filename = suClass.get_temp_dir() + os.sep + "test_file.FILE"
        #hashMap.put('toast','Начали загрузку')
        hashMap.put('toast', filename)
        hashMap.put("beep", "")
        with open(filename, 'wb') as f:
            f.write(imageBytes)

        res = ui_csv.load_from_csv(filename, 'test_file.FILE')

        if res == 200:
            hashMap.put('toast','Данные файла успешно загружены.')
        else:
            hashMap.put('toast','Ошибка! Неверный файл загрузки.')
        # screen: ui_models.CSV = ui_models.CSV(hashMap)
        # screen.on_load_file(imageBytes)

    return hashMap




def new_doc_on_start(hashMap, _files=None, _data=None):
    if hashMap.get('doc_type_select') == None:
        # Заполним поле фильтра по виду документов
        result = ui_global.get_query_result(ui_form_data.get_doc_type_query())
        doc_type_list = ['Все']
        for record in result:
            doc_type_list.append(record[0])
        hashMap.put('doc_type_select', ';'.join(doc_type_list))

    if hashMap.get('countragent') == None:
        #fld_countragent = ui_global.get_name_list('RS_countragents')

        hashMap.put('countragent', 'Контрагент')  #fld_countragent

    if hashMap.get('warehouse') == None:
        #fld_countragent = ui_global.get_name_list('RS_warehouses')
        hashMap.put('warehouse', 'Склад') #doc_warehouse

    if not hashMap.containsKey('doc_date'):
        hashMap.put('doc_date', '01.01.2022')

    return hashMap


@HashMap()
def new_doc_on_select(hashMap, _files=None, _data=None):
    new_doc_id = ui_models.DocumentsDocsListScreen(hashMap, rs_settings).get_new_doc_id()
    listener = hashMap.get("listener")
    type = hashMap.get('doc_type_click')
    if not type:
        type = 'Приход'
    fld_number = hashMap.get('fld_number')

    if listener == "btn_ok":
        if not fld_number:

            id = new_doc_id
            # id = (f'{id:04}')
            # id = "{0:0>4}".format(id)
        else:
            id = fld_number

        try:
            ui_global.Rs_doc.add('01',(id,
                                        type,
                                        id,  # hashMap.get('fld_number')
                                        hashMap.get('fld_data'),
                                        ui_global.get_by_name(hashMap.get('countragent'), 'RS_countragents'),
                                        ui_global.get_by_name(hashMap.get('warehouse'), 'RS_warehouses')))
            hashMap.put('ShowScreen', 'Документы')
        except:
            hashMap.put('toast', 'Номер документа неуникален!')


    elif listener == 'btn_cancel':
        hashMap.put('ShowScreen', 'Документы')
    elif listener == 'fld_data':
        hashMap.put('doc_date', hashMap.get('fld_data'))
    elif listener == 'ON_BACK_PRESSED':
        hashMap.put("ShowScreen", "Документы")
    elif listener =='btn_select_warehouse':
        hashMap.put('table_for_select', 'RS_warehouses')  # Таблица для выбора значения
        hashMap.put('SetResultListener', 'select_cell_value')
        hashMap.put('filter_fields', 'name')
        hashMap.put('ShowProcessResult', 'Универсальный справочник|Справочник')
    elif listener == 'btn_select_countragent':
        hashMap.put('table_for_select', 'RS_countragents')  # Таблица для выбора значения
        hashMap.put('SetResultListener', 'select_cell_value')
        hashMap.put('filter_fields', 'name;full_name;inn;kpp')
        hashMap.put('ShowProcessResult', 'Универсальный справочник|Справочник')

    elif listener == 'select_cell_value':
        if hashMap.get('table_for_select') == 'RS_countragents':
            hashMap.put('countragent', hashMap.get('current_name')) #fld_countragent
        elif hashMap.get('table_for_select') == 'RS_warehouses':
            hashMap.put('warehouse', hashMap.get('current_name'))  # fld_countragent
    return hashMap
