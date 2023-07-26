import json
import socket
import requests
from requests.auth import HTTPBasicAuth
import os
from PIL import Image

import ui_barcodes
import ui_csv
import ui_global
import ui_form_data
import http_exchange
from new_handlers import *



# ********************* Старое адресное хранение
# Todo Переписать это по новой классовой схеме и удалить из кода

def adr_elem_on_start(hashMap, _files=None, _data=None):
    hashMap.put('mm_local', '')
    return hashMap


def adr_elem_on_click(hashMap, _files=None, _data=None):
    listener = hashMap.get("listener")


    if listener == "btn_ok":
        # # получим текущую строку документа
        # current_str = hashMap.get("selected_card_position")
        doc = ui_global.Rs_adr_doc
        doc.id_doc = hashMap.get('id_doc')
        # if not current_str == '0':
        #     jlist = json.loads(hashMap.get("doc_goods"))
        #     current_elem = jlist['customcards']['cardsdata'][int(current_str)]
        #     key = int(current_elem['key'])
        #     doc.id_str = int(current_elem['key'])
        # ... и запишем ее в базу
        qtty = hashMap.get('qtty')
        doc.qtty = float(qtty) if qtty else 0
        elem_for_add ={'id_good':hashMap.get('Good_id'), 'id_property':hashMap.get('properties_id'), 'id_series':hashMap.get('series_id'), 'id_unit': hashMap.get('unit_id')}

        doc.update_doc_table_data(doc, elem_for_add, qtty, hashMap.get('current_cell_name'),hashMap.get('table_type_filter')) #(doc, )

        hashMap.put("ShowScreen", "Документ товары")

    elif listener == "btn_cancel":

        hashMap.put("ShowScreen", "Документ товары")
    elif listener == "BACK_BUTTON":
        hashMap.put("ShowScreen", "Документ товары")
    elif listener == "":
        hashMap.put("qtty", str(float(hashMap.get('qtty'))))
    elif listener == 'ON_BACK_PRESSED':
        hashMap.put("ShowScreen", "Документ товары")

    elif listener == "btn_good_select":
        hashMap.remove('SearchString')
        hashMap.put('table_for_select', 'RS_goods')  # Таблица для выбора значения
        hashMap.put('SetResultListener', 'select_goods_value')
        hashMap.put('filter_fields', 'name;art')
        hashMap.put('ShowProcessResult', 'Универсальный справочник|Справочник')
    #--
    elif listener == "select_goods_value":
        hashMap.put('Good', hashMap.get('current_name'))
        hashMap.put('Good_id', hashMap.get('current_id'))
        # При выборе товара заполним единицу измерения по умолчанию
        qtext = '''Select RS_goods.unit as unit_id, 
                    RS_units.name 
                    From RS_goods
                      Left Join RS_units on RS_units.id_owner = RS_goods.id and RS_units.id = RS_goods.unit 
                    WHERE RS_goods.id = ?'''
        res = ui_global.get_query_result(qtext, (hashMap.get('current_id'),))
        if res:
            hashMap.put('unit_id', res[0][0])
            hashMap.put('unit', res[0][1])

    elif listener == "btn_properties":
        hashMap.put('SearchString', hashMap.get('current_id'))
        hashMap.put('table_for_select', 'RS_properties')  # Таблица для выбора значения
        hashMap.put('SetResultListener', 'select_properties_value')
        hashMap.put('filter_fields', 'name;id_owner')
        hashMap.put('ShowProcessResult', 'Универсальный справочник|Справочник')
    # --
    elif listener == 'select_properties_value':
        hashMap.put('properties', hashMap.get('current_name'))
        hashMap.put('properties_id', hashMap.get('current_id'))

    elif listener == "btn_series":
        hashMap.put('table_for_select', 'RS_series')  # Таблица для выбора значения
        hashMap.put('SetResultListener', 'select_series_value')
        hashMap.put('filter_fields', 'name; id_owner')
        hashMap.put('ShowProcessResult', 'Универсальный справочник|Справочник')
        #__
    elif listener == 'select_series_value':
        hashMap.put('series', hashMap.get('current_name'))
        hashMap.put('series_id', hashMap.get('current_id'))

    elif listener == "btn_unit":
        hashMap.put('SearchString', hashMap.get('Good_id'))
        hashMap.put('table_for_select', 'RS_units')  # Таблица для выбора значения
        hashMap.put('SetResultListener', 'select_unit_value')
        hashMap.put('filter_fields', 'name;id_owner')
        hashMap.put('ShowProcessResult', 'Универсальный справочник|Справочник')
        #__
    elif listener == 'select_unit_value':
        hashMap.put('unit', hashMap.get('current_name'))
        hashMap.put('unit_id', hashMap.get('current_id'))
    #btn_select_cell
    elif listener == "btn_select_cell":
        hashMap.put('SearchString', '')
        hashMap.put('table_for_select', 'RS_cells')  # Таблица для выбора значения
        hashMap.put('SetResultListener', 'select_cell_value')
        hashMap.put('filter_fields', 'name;barcode')
        hashMap.put('ShowProcessResult', 'Универсальный справочник|Справочник')
        #__
    elif listener == 'select_cell_value':
        hashMap.put('current_cell_name', hashMap.get('current_name'))
        hashMap.put('current_cell_id', hashMap.get('current_id'))

    elif listener == "photo":

        # Можно вообще этого не делать-оставлять как есть. Это для примера.
        image_file = str(
            hashMap.get("photo_path"))  # "переменная"+"_path" - сюда помещается путь к полученной фотографии

        image = Image.open(image_file)

        # сразу сделаем фотку - квадратной - это простой вариант. Можно сделать например отдельо миниатюры для списка, это немного сложнее
        im = image.resize((500, 500))
        im.save(image_file)

        jphotoarr = json.loads(hashMap.get("photoGallery"))
        hashMap.put("photoGallery", json.dumps(jphotoarr))
        # hashMap.put("toast",json.dumps(jphotoarr))

    elif listener == "gallery_change":  # пользователь может удалить фото из галереи. Новый массив надо поместить к документу

        if hashMap.containsKey("photoGallery"):  # эти 2 обработчика - аналогичные, просто для разных событий
            jphotoarr = json.loads(hashMap.get("photoGallery"))
            hashMap.put("photoGallery", json.dumps(jphotoarr))
            # hashMap.put("toast","#2"+json.dumps(jphotoarr))

    return hashMap


def new_adr_doc_on_start(hashMap, _files=None, _data=None):
    if hashMap.get('doc_adr_type_select') == None:
        # Заполним поле фильтра по виду документов
        doc_type_list = ['Отбор', 'Размещение', 'Перемещение']
        hashMap.put('doc_adr_type_select', ';'.join(doc_type_list))


    if hashMap.get('warehouse') == None:
        #fld_countragent = ui_global.get_name_list('RS_warehouses')
        hashMap.put('warehouse', 'Склад') #doc_warehouse

    if not hashMap.containsKey('doc_date'):
        hashMap.put('doc_date', '01.01.2022')

    return hashMap


def new_adr_doc_on_select(hashMap, _files=None, _data=None):
    listener = hashMap.get("listener")
    type = hashMap.get('doc_type_click')
    if not type or type=='Все':
        type = 'Отбор'
    fld_number = hashMap.get('fld_number')

    if listener == "btn_ok":
        if not fld_number:

            id = ui_global.Rs_adr_doc.get_new_id(1)
            # id = (f'{id:04}')
            # id = "{0:0>4}".format(id)
        else:
            id = fld_number

        try:
            ui_global.Rs_adr_doc.add('01', (id,
                                        type,
                                        id,  # hashMap.get('fld_number')
                                        hashMap.get('fld_data'),
                                        ui_global.get_by_name(hashMap.get('doc_warehouse'), 'RS_warehouses')))
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
    elif listener == 'select_cell_value':
        if hashMap.get('table_for_select') == 'RS_warehouses':
            hashMap.put('warehouse', hashMap.get('current_name'))  # fld_countragent

    return hashMap


@HashMap()
def doc_details_before_process_barcode(hash_map):
    """ Обработчик для синхронного запроса и обновления данных после сканирования и перед обработкой ШК"""

    screen = ui_models.GroupScanDocDetailsScreen(hash_map, rs_settings)
    screen.before_process_barcode()

@HashMap()
def doc_details_barcode_scanned(hash_map: HashMap):
    """ Обработчик для асинхронной отправки и получения данных после сканирования ШК"""

    screen = ui_models.GroupScanDocDetailsScreen(hash_map, rs_settings)
    screen.post_barcode_scanned(get_http_settings(hash_map))


@HashMap()
def highlight_scanned_item(hash_map: HashMap):
    """ Обработчик для отмены раскраски отсканированного товара """

    # time.sleep(2)
    screen = ui_models.DocDetailsScreen(hash_map, rs_settings)
    screen.disable_highlight()


@HashMap()
def elem_on_start(hash_map):
    # Режим работы с мультимедиа и файлами по ссылкам (флаг mm_local)
    hash_map['mm_local'] = ''


def elem_on_click(hashMap, _files=None, _data=None):
    listener = hashMap.get("listener")

    if listener == "btn_ok":
        # получим текущую строку документа
        current_str = hashMap.get("selected_card_position")
        #Если строка не существует, создадим ее
        doc = ui_global.Rs_doc
        doc.id_doc = hashMap.get('id_doc')
        # if current_str =='0':
        #     pass
        #     #jlist['customcards']['cardsdata']
        # else:
        #     jlist = json.loads(hashMap.get("doc_goods"))
        #     current_elem = jlist['customcards']['cardsdata'][int(current_str)]
        #     key = int(current_elem['key'])
        #     doc.id_str = int(current_elem['key'])
        # ... и запишем ее в базу

        qtty = hashMap.get('qtty')
        doc.qtty = float(qtty) if qtty else 0
        elem_for_add = {'id_good': hashMap.get('Good_id'), 'id_property': hashMap.get('properties_id'),
                        'id_series': hashMap.get('series_id'),'id_unit': hashMap.get('unit_id')}
        doc.update_doc_table_data(doc, elem_for_add, qtty)  # (doc, )

        hashMap.put("ShowScreen", "Документ товары")

    elif listener == "btn_cancel":

        hashMap.put("ShowScreen", "Документ товары")
    elif listener == "BACK_BUTTON":
        hashMap.put("ShowScreen", "Документ товары")
    elif listener == "":
        hashMap.put("qtty", str(float(hashMap.get('qtty'))))
    elif listener == 'ON_BACK_PRESSED':
        hashMap.put("ShowScreen", "Документ товары")

    elif listener == "btn_good_select":
        hashMap.remove('SearchString')
        hashMap.put('table_for_select', 'RS_goods')  # Таблица для выбора значения
        hashMap.put('SetResultListener', 'select_goods_value')
        hashMap.put('filter_fields', 'name')
        hashMap.put('ShowProcessResult', 'Универсальный справочник|Справочник')
    #--
    elif listener == "select_goods_value":
        hashMap.put('Good', hashMap.get('current_name'))
        hashMap.put('Good_id', hashMap.get('current_id'))
        #При выборе товара заполним единицу измерения по умолчанию
        qtext = '''Select RS_goods.unit as unit_id, 
                    RS_units.name 
                    From RS_goods
                      Left Join RS_units on RS_units.id_owner = RS_goods.id and RS_units.id = RS_goods.unit 
                    WHERE RS_goods.id = ?'''
        res =  ui_global.get_query_result(qtext, (hashMap.get('current_id'),))
        if res:

            hashMap.put('unit_id', res[0][0])
            hashMap.put('unit', res[0][1])

    elif listener == "btn_properties":

        hashMap.put('SearchString', hashMap.get('Good_id'))
        hashMap.put('table_for_select', 'RS_properties')  # Таблица для выбора значения
        hashMap.put('SetResultListener', 'select_properties_value')
        hashMap.put('filter_fields', 'name;id_owner')
        hashMap.put('ShowProcessResult', 'Универсальный справочник|Справочник')
    # --
    elif listener == 'select_properties_value':
        hashMap.put('properties', hashMap.get('current_name'))

    elif listener == "btn_series":
        hashMap.put('table_for_select', 'RS_series')  # Таблица для выбора значения
        hashMap.put('SetResultListener', 'select_series_value')
        hashMap.put('filter_fields', 'name')
        hashMap.put('ShowProcessResult', 'Универсальный справочник|Справочник')
        #__
    elif listener == 'select_series_value':
        hashMap.put('series', hashMap.get('current_name'))
    elif listener == "btn_unit":
        hashMap.put('table_for_select', 'RS_units')  # Таблица для выбора значения
        hashMap.put('SetResultListener', 'select_unit_value')
        hashMap.put('filter_fields', 'name;id_owner')
        hashMap.put('ShowProcessResult', 'Универсальный справочник|Справочник')
        #__
    elif listener == 'select_unit_value':
        hashMap.put('unit', hashMap.get('current_name'))
        hashMap.put('unit_id', hashMap.get('current_id'))

    elif listener == "photo":

        # Можно вообще этого не делать-оставлять как есть. Это для примера.
        image_file = str(
            hashMap.get("photo_path"))  # "переменная"+"_path" - сюда помещается путь к полученной фотографии

        image = Image.open(image_file)

        # сразу сделаем фотку - квадратной - это простой вариант. Можно сделать например отдельо миниатюры для списка, это немного сложнее
        im = image.resize((500, 500))
        im.save(image_file)

        jphotoarr = json.loads(hashMap.get("photoGallery"))
        hashMap.put("photoGallery", json.dumps(jphotoarr))
        # hashMap.put("toast",json.dumps(jphotoarr))

    elif listener == "gallery_change":  # пользователь может удалить фото из галереи. Новый массив надо поместить к документу

        if hashMap.containsKey("photoGallery"):  # эти 2 обработчика - аналогичные, просто для разных событий
            jphotoarr = json.loads(hashMap.get("photoGallery"))
            hashMap.put("photoGallery", json.dumps(jphotoarr))
            # hashMap.put("toast","#2"+json.dumps(jphotoarr))

    return hashMap


def remove_added_good_highlight(hashMap, good_id=None, property_id=None):
    if hashMap.get("added_goods"):
        id_doc = hashMap.get('id_doc')
        added_goods_dict = json.loads(hashMap.get("added_goods"))
        if id_doc in added_goods_dict.keys():
            if good_id in added_goods_dict[id_doc][0]:
                added_goods_dict[id_doc][0].remove(good_id)
            """if property_id in added_goods_dict[good_id][1]:
                added_goods_dict[good_id][1].remove(property_id)"""
            hashMap.put("added_goods", str(added_goods_dict).replace("'", '"'))
            if len(added_goods_dict[id_doc][0]) == 0:
                del added_goods_dict[id_doc]
    return hashMap


def get_current_elem_doc_goods(hashMap, current_str):

    if hashMap.get('view') == "cards":
        jlist = json.loads(hashMap.get("doc_goods_cards"))
        cards_data = jlist['customcards']['cardsdata']
    else:
        jlist = json.loads(hashMap.get("doc_goods_table"))
        cards_data = jlist['customtable']['tabledata']
    for element in cards_data:
        if "key" in element:
            if element["key"] == hashMap.get("selected_card_key"):
                current_elem = element
    return current_elem


def doc_barcodes_on_start(hashMap, _files=None, _data=None):
    doc_detail_list = ui_form_data.get_barcode_card(rs_settings)
    query_text = ui_form_data.get_barcode_query()
    id_doc = hashMap.get('id_doc')
    results = ui_global.get_query_result(query_text, (id_doc,))

    for record in results:
        product_row = {
            'key': str(record[0]),
            'barcode_value': str(record[3]),
            'ratio':str(record[6]),
            'approved': str(record[4])

        }

        doc_detail_list['customcards']['cardsdata'].append(product_row)

    hashMap.put("barc_cards", json.dumps(doc_detail_list))

    return hashMap


def doc_barcodes_listener(hashMap, _files=None, _data=None):
    if hashMap.get('listener') == 'ON_BACK_PRESSED':
        hashMap.put("ShowScreen", "Документ товары")
    return hashMap


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


def barcode_error_screen_listener(hashMap, _files=None, _data=None):
    if hashMap.get('listener') == 'ON_BACK_PRESSED':
        # suClass.urovo_set_lock_trigger(False)
        hashMap.put("ShowScreen", "Документ товары")
    elif hashMap.get('listener') == 'btn_continue_scan':
        # suClass.urovo_set_lock_trigger(False)
        hashMap.put("ShowScreen", "Документ товары")
    return hashMap

def plan_excess_error_screen_listener(hashMap, _files=None, _data=None):
    if hashMap.get('listener') == 'ON_BACK_PRESSED':
        # suClass.urovo_set_lock_trigger(False)
        hashMap.put("ShowScreen", "Документ товары")
    elif hashMap.get('listener') == 'btn_continue_scan':
        # suClass.urovo_set_lock_trigger(False)
        hashMap.put("ShowScreen", "Документ товары")
    return hashMap
def barcode_flow_on_start(hashMap, _files=None, _data=None):
    id_doc = hashMap.get('id_doc')
    falseValueList = (0, '0', 'false', 'False', None)
    # Формируем таблицу карточек и запрос к базе

    doc_detail_list = ui_form_data.doc_barc_flow_card(rs_settings)
    doc_detail_list['customcards']['cardsdata'] = []


    query_text = ui_form_data.get_doc_barc_flow_query()

    results = ui_global.get_query_result(query_text, (id_doc,), True)

    if results:
        # hashMap.put('id_doc', str(results[0]['id_doc']))
        for record in results:
            pic = '#f00c'

            product_row = {
                'key': str(record['barcode']),
                'barcode': str(record['barcode']),

            }

            doc_detail_list['customcards']['cardsdata'].append(product_row)

        # Признак, have_qtty_plan ЕстьПланПОКОличеству  -  Истина когда сумма колонки Qtty_plan > 0
        # Признак  have_mark_plan "ЕстьПланКОдовМаркировки – Истина, когда количество строк табл. RS_docs_barcodes с заданным id_doc и is_plan  больше нуля.
        # Признак have_zero_plan "Есть строки товара в документе" Истина, когда есть заполненные строки товаров в документе
        # Признак "Контролировать"  - признак для документа, надо ли контролировать

        qtext = ui_form_data.get_qtty_string_count_query()
        res = ui_global.get_query_result(qtext, {'id_doc': id_doc})
        if not res:
            have_qtty_plan = False
            have_zero_plan = False
        else:
            have_zero_plan = res[0][0] > 0  # В документе есть строки
            if have_zero_plan:
                have_qtty_plan = res[0][1] > 0  # В документе есть колво план
            else:
                have_qtty_plan = False
        # Есть ли в документе план по кодам маркировки
        qtext = ui_form_data.get_have_mark_codes_query()
        res = ui_global.get_query_result(qtext, {'id_doc': id_doc, 'is_plan': '1'})
        if not res:
            have_mark_plan = False

        else:
            have_mark_plan = res[0][0] > 0
    else:
        have_qtty_plan = False
        have_zero_plan = False
        have_mark_plan = False

    hashMap.put('have_qtty_plan', str(have_qtty_plan))
    hashMap.put('have_zero_plan', str(have_zero_plan))
    hashMap.put('have_mark_plan', str(have_mark_plan))
    res = ui_global.get_query_result('SELECT control from RS_docs  WHERE id_doc = ?', (id_doc,))
    # Есть ли контроль плана в документе
    if res:
        if res[0][0]:
            if res[0][0] in falseValueList:
                control = 'False'
            else:
                control = 'True'

            # control = res[0][0] #'True'
        else:
            control = 'False'
    else:
        control = 'False'

    hashMap.put('control', control)
    hashMap.put("doc_barc_flow", json.dumps(doc_detail_list))

    if True in (have_qtty_plan, have_zero_plan, have_mark_plan, control):
        hashMap.put('toast', 'Данный документ содержит плановые строки. Список штрихкодов в него поместить нельзя')
        hashMap.put('ShowScreen','Документы')

    return hashMap


def barcode_flow_listener(hashMap,  _files=None, _data=None):
    listener = hashMap.get('listener')
    if listener == "CardsClick":

        pass

    elif listener == "BACK_BUTTON":
        hashMap.put("ShowScreen", "Документы")
    elif listener == "btn_barcodes":
        pass
        #hashMap.put("ShowDialog", "ВвестиШтрихкод")

    # elif hashMap.get("event") == "onResultPositive":

    elif listener == 'barcode' or hashMap.get("event") == "onResultPositive":
        doc = ui_global.Rs_doc
        doc.id_doc = hashMap.get('id_doc')
        if hashMap.get("event") == "onResultPositive":
            barcode = hashMap.get('fld_barcode')
        else:
            barcode = hashMap.get('barcode_camera')

        have_qtty_plan = hashMap.get('have_qtty_plan')
        have_zero_plan = hashMap.get('have_zero_plan')
        have_mark_plan = hashMap.get('have_mark_plan')
        control = hashMap.get('control')

        if barcode:
            qtext = '''
            INSERT INTO RS_barc_flow (id_doc, barcode) VALUES (?,?)
            '''
            ui_global.get_query_result(qtext,(doc.id_doc, barcode))

    elif listener == 'btn_doc_mark_verified':
        doc = ui_global.Rs_doc
        doc.id_doc = hashMap.get('id_doc')
        doc.mark_verified(doc, 1)
        hashMap.put("ShowScreen", "Документы")

    elif listener == 'ON_BACK_PRESSED':
        hashMap.put("ShowScreen", "Документы")

    return hashMap



# =============== Universal cards =================


def universal_cards_on_start(hashMap, _files=None, _data=None):
    filter_value =hashMap.get('SearchString')
    if filter_value:
       filter_fields = hashMap.get('filter_fields').split(';')
    else:
        filter_fields = list()
    hashMap.put('cards', get_table_cards(hashMap.get('table_for_select'),filter_fields,filter_value))

    return hashMap


def universal_cards_listener(hashMap, _files=None, _data=None):

    listener = hashMap.get("listener")

    if listener == "CardsClick":
        current_str = hashMap.get("selected_card_position")
        jlist = json.loads(hashMap.get("cards"))
        current_elem = jlist['customcards']['cardsdata'][int(current_str)]
        hashMap.remove('SearchString')
        hashMap.put('current_id',current_elem['key'])
        hashMap.put('current_name', current_elem['name'])
        hashMap.put('FinishProcessResult', '')


    elif listener == 'LayoutAction':
        layout_listener = hashMap.get('layout_listener')
        # Находим ID документа
        current_card = json.loads(hashMap.get("current_card"))


    elif listener == 'ON_BACK_PRESSED':
        hashMap.remove('SearchString')
        hashMap.put('current_id', '')
        hashMap.put('FinishProcessResult', '')
    elif listener == 'Search':
        filter_value = hashMap.get('SearchString')
        if len(filter_value) > 2:
            filter_fields = hashMap.get('filter_fields').split(';')
            hashMap.put('cards', get_table_cards(hashMap.get('table_for_select'), filter_fields, filter_value))

            hashMap.put('RefreshScreen','')
        #universal_cards_on_start(hashMap)

    return hashMap


class UniversalCard:
    def __init__(self, table_name: str, filter_fields=list(), filter_value='', exclude_list=list(),no_label=False, struct_view:list = list()):
        self.table_name = table_name
        self.filter_fields = filter_fields
        self.filter_value = filter_value
        self.exclude_list = exclude_list
        self.no_label = no_label
        self.struct_view = struct_view

        res = ui_global.get_query_result(f"PRAGMA table_info({table_name})")
        self.fields = [f[1] for f in res]
        # Словарь русских имен полей
        self.aliases = ui_form_data.fields_alias_dict()
        # Словарь полей-ссылок на таблицы
        self.tables_dict = ui_form_data.table_names_dict()
        self.card_elem = ui_form_data.get_elem_dict(24)
        self.cards = ui_form_data.get_universal_card()
        self.gorizontal_layout = {"layout": {
            "type": "LinearLayout",
            "orientation": "gorizontal",
            "height": "match_parent",
            "width": "match_parent",
            "weight": "0",

            "Elements": []}}

    def get_query_by_table_name(self):
        qfield_text = []
        left_joins_list = []
        for el in self.fields:
            link_table_name = self.tables_dict.get(el)
            qfield_text.append(self.table_name + '.' + el)
            #qtext = 'Select ' + ','.join(qfield_text) + f' FROM {self.table_name} ' + ' '.join(left_joins_list)
            # Если есть фильтры/отборы - добавим их в запрос
            if link_table_name:
                # Это ссылка на таблицу
                qfield_text.append(link_table_name + f'.name as {link_table_name}_name')
                left_joins_list.append(f'''
                    LEFT JOIN {link_table_name}
                    ON {link_table_name}.id = {self.table_name}.{el}
                    ''')
        qtext = 'Select ' + ','.join(qfield_text) + f' FROM {self.table_name} ' + ' '.join(left_joins_list)
        # Если есть фильтры/отборы - добавим их в запрос
        if self.filter_value:
            # conditions = [f"{field} LIKE '%{filter_value}%'" for field in filter_fields]
            conditions = [f"{self.table_name}.{field} LIKE '%{self.filter_value}%'" for field in self.filter_fields]
            qtext = qtext + f" WHERE {' OR '.join(conditions)}"
        return qtext

    def form_card_struct(self):
        #qfield_text = []
        card_elem = self.card_elem
        cards = self.cards
        for el in self.fields:
            if el not in self.exclude_list:
                link_table_name = self.tables_dict.get(el)
                #qfield_text.append(self.table_name + '.' + el)

                # Дополним выходную структуру полями таблицы:
                aliases_elem = self.aliases.get(el)
                if aliases_elem:  # Для этого поля предусмотрена настройка
                    if not aliases_elem['name'] == 'key':  # Для ключа настройки не нужны
                        if not self.no_label:
                            # добавим описание поля:...
                            card_elem['Value'] = aliases_elem['name']
                            card_elem['TextSize'] = rs_settings.get('CardDateTextSize')  # aliases_elem['text_size']
                            card_elem['TextBold'] = False
                            cards['customcards']['layout']['Elements'][0]['Elements'][0]['Elements'].append(
                                card_elem.copy())

                        # Теперь само поле:
                        card_elem['Value'] = '@' + el
                        card_elem['TextSize'] = rs_settings.get(aliases_elem['text_size'])
                        card_elem['TextBold'] = aliases_elem['TextBold']
                else:  # Иначе просто добавим его со стандартными настройками
                    card_elem['Value'] = '@' + el
                    # Добавим поле в карточки
            cards['customcards']['layout']['Elements'][0]['Elements'][0]['Elements'].append(card_elem.copy())

    def form_card_struct_from_ready_sruct(self):
        temp_struct = ('code','name',('art','timestamp'),'full_name')
        json_structure = []

        for item in temp_struct:
            if isinstance(item, list):
                nested_structure = []
                for nested_item in item:
                    nested_structure.append(nested_item)
                json_structure.append(nested_structure)
            else:
                json_structure.append(item)

        return json.dumps(json_structure, indent=4)


# ^^^^^^^^^^^^^^^^^ Universal cards ^^^^^^^^^^^^^^^^^


# =============== Settings =================

def file_list_on_start(hashMap, _files=None, _data=None):
    tx = ''

    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk("."):
        path = root.split(os.sep)
        print((len(path) - 1) * '---', os.path.basename(root))
        for file in files:
            print(len(path) * '---', file)

    hashMap.put('files_list', tx)
    return hashMap





@HashMap()
def http_settings_on_click_(hashMap,  _files=None, _data=None):
    listener = hashMap.get('listener')
    if listener == 'btn_save':
        if not all([hashMap.get('url'), hashMap.get('user'), hashMap.get('pass')]):
            hashMap.put("toast", "Не указаны настройки HTTP подключения к серверу")
        rs_settings.put('URL', hashMap.get('url'), True)
        rs_settings.put('USER', hashMap.get('user'), True)
        rs_settings.put('PASS', hashMap.get('pass'), True)
        rs_settings.put('user_name', hashMap.get('user_name'), True)
        hashMap.put('ShowScreen', 'Настройки и обмен')
    elif listener == 'btn_cancel':
        hashMap.put('ShowScreen', 'Настройки и обмен')
    elif listener == 'ON_BACK_PRESSED':
        hashMap.put('ShowScreen', 'Настройки и обмен')
    elif listener == 'barcode':
        barcode = hashMap.get('barcode_camera2')
        try:
            barc_struct = json.loads(barcode)

            rs_settings.put('URL', barc_struct.get('url'), True)
            rs_settings.put('USER', barc_struct.get('user'), True)
            rs_settings.put('PASS', barc_struct.get('pass'), True)
            rs_settings.put('user_name', barc_struct.get('user_name'), True)

            hashMap.put('url', ui_form_data.ModernField(hint='url', default_text=barc_struct.get('url')).to_json())
            hashMap.put('user', ui_form_data.ModernField(hint='user', default_text=barc_struct.get('user')).to_json())
            hashMap.put('pass', ui_form_data.ModernField(hint='pass', default_text=barc_struct.get('pass')).to_json())
            hashMap.put('user_name', ui_form_data.ModernField(hint='user_name', default_text=barc_struct.get('user_name')).to_json())
        except:
            hashMap.put('toast', 'неверный формат QR-кода')
    elif listener == 'btn_test_connection':
        #/communication_test
        http = get_http_settings(hashMap)
        if not all([http.get('url'), http.get('user'), http.get('pass')]):
            hashMap.put("toast", "Не указаны настройки HTTP подключения к серверу")
            return hashMap
        else:
            r = requests.get(http['url'] + '/simple_accounting/communication_test?android_id=' + http['android_id'], auth=HTTPBasicAuth(http['user'], http['pass']),
                 headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'},
                 params={'user_name': http['user_name'], 'device_model': http['device_model']})
            if r.status_code == 200:
                hashMap.put('btn_test_connection', 'Соединение установлено')
                hashMap.put('toast', 'Соединение установлено')
            elif r.status_code == 403:
                hashMap.put('btn_test_connection', 'Тест соединения')
                hashMap.put("toast", "Запрос на авторизацию принят")
            else:
                hashMap.put('btn_test_connection', 'Тест соединения')
                hashMap.put('toast', 'Не удалось установить соединение')

    return hashMap


# ^^^^^^^^^^^^^^^^^ Settings ^^^^^^^^^^^^^^^^^


# =============== Debug =================

@HashMap()
def debug_on_start(hash_map: HashMap):
    screen: ui_models.DebugSettingsScreen = create_screen(hash_map)
    screen.on_start()


@HashMap()
def debug_listener(hash_map, _files=None, _data=None):
    screen: ui_models.DebugSettingsScreen = create_screen(hash_map)
    screen.on_input()


def test_screen_input(hashMap,  _files=None, _data=None):
    if hashMap.get('listener') == 'btn_ok' or 'ON_BACK_PRESSED':
        hashMap.put('FinishProcess','')
    return hashMap
# ^^^^^^^^^^^^^^^^^ Debug ^^^^^^^^^^^^^^^^^


def get_http_settings(hashMap):
    http_settings = {
    'url' : rs_settings.get("URL"),
    'user' : rs_settings.get('USER'),
    'pass' : rs_settings.get('PASS'),
    'device_model' : hashMap.get('DEVICE_MODEL'),
    'android_id':hashMap.get('ANDROID_ID'),
    'user_name': rs_settings.get('user_name')}
    return http_settings


# Добавлен параметр "no_label"
def get_table_cards(table_name: str, filter_fields=list(), filter_value='', exclude_list=list(), no_label=False, struct_view:list = list()):
    # Получим список полей таблицы
    # table_name = 'RS_goods'
    res = ui_global.get_query_result(f"PRAGMA table_info({table_name})")
    fields = [f[1] for f in res]
    # Словарь русских имен полей
    aliases = ui_form_data.fields_alias_dict()
    # Словарь полей-ссылок на таблицы
    tables_dict = ui_form_data.table_names_dict()

    # Создадим запрос к таблице. Ссылочные поля заменим на наименование из связанных таблиц
    card_elem = ui_form_data.get_elem_dict(24)
    cards = ui_form_data.get_universal_card()

    qfield_text = []
    left_joins_list = []
    for el in fields:
        if el not in exclude_list:
            link_table_name = tables_dict.get(el)
            qfield_text.append(table_name + '.' + el)

            # Дополним выходную структуру полями таблицы:
            aliases_elem = aliases.get(el)
            if aliases_elem:  # Для этого поля предусмотрена настройка
                if not aliases_elem['name'] == 'key':  # Для ключа настройки не нужны
                    if not no_label:
                        # добавим описание поля:...
                        card_elem['Value'] = aliases_elem['name']
                        card_elem['TextSize'] = rs_settings.get('CardDateTextSize')  # aliases_elem['text_size']
                        card_elem['TextBold'] = False
                        cards['customcards']['layout']['Elements'][0]['Elements'][0]['Elements'].append(card_elem.copy())

                    # Теперь само поле:
                    card_elem['Value'] = '@' + el
                    card_elem['TextSize'] = rs_settings.get(aliases_elem['text_size'])
                    card_elem['TextBold'] = aliases_elem['TextBold']
            else:  # Иначе просто добавим его со стандартными настройками
                card_elem['Value'] = '@' + el

            if link_table_name:
                # Это ссылка на таблицу
                qfield_text.append(link_table_name + f'.name as {link_table_name}_name')
                left_joins_list.append(f'''
                    LEFT JOIN {link_table_name}
                    ON {link_table_name}.id = {table_name}.{el}
                    ''')
                card_elem[
                    'Value'] = f'@{link_table_name}_name'  # Так как поле ссылочное - переименуем его как в запросе

            # Добавим поле в карточки
            cards['customcards']['layout']['Elements'][0]['Elements'][0]['Elements'].append(card_elem.copy())

    qtext = 'Select ' + ','.join(qfield_text) + f' FROM {table_name} ' + ' '.join(left_joins_list)
    # Если есть фильтры/отборы - добавим их в запрос
    if filter_value:
        # conditions = [f"{field} LIKE '%{filter_value}%'" for field in filter_fields]
        conditions = [f"{table_name}.{field} LIKE '%{filter_value}%'" for field in filter_fields]
        qtext = qtext + f" WHERE {' OR '.join(conditions)}"
    res_query = ui_global.get_query_result(qtext, None, True)
    # settings_global.get

    cards['customcards']['cardsdata'] = []

    for i in res_query:
        product_row = {}
        for x in i:
            if x == 'id':
                product_row['key'] = str(i[x])
            else:
                product_row[x] = str(i[x])

        cards['customcards']['cardsdata'].append(product_row)

    return json.dumps(cards)

@HashMap()
def debug_barcode_error_screen_listener(hash_map: HashMap):
    hash_map.show_screen(listener='Ошибка превышения плана', title='Количество план в документе превышено')
