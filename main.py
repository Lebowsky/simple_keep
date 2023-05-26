from ru.travelfood.simple_ui import SimpleUtilites as suClass

import ui_barcodes
import ui_csv
import ui_global
import ui_form_data
import socket
import json
import requests
import database_init_queryes
import os
from PIL import Image
import importlib
# from rs_settings import RSSettings
from java import jclass
import http_exchange
from requests.auth import HTTPBasicAuth

noClass = jclass("ru.travelfood.simple_ui.NoSQL")
rs_settings = noClass("rs_settings")

importlib.reload(ui_csv)
importlib.reload(ui_global)
importlib.reload(ui_form_data)
importlib.reload(database_init_queryes)


# -----
# 0100608940553886215,iPGSQpBt!&B
def settings_on_start(hashMap, _files=None, _data=None):
    # hashMap.put('toast','обновились')
    app_on_start(hashMap)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        aa = (s.getsockname()[0])
        # aa = hashMap.get('ip_adr')
        hashMap.put('ip_adr', aa)
        # hashMap.put('toast', aa)
    except:
        hashMap.put('ip_adr', 'нет сети')
    # app_on_start(hashMap)
    # Значения констант и настроек
    res = ui_global.get_constants()
    if res:
        hashMap.put('use_series', str(res[1]))
        hashMap.put('use_properties', str(res[2]))
        hashMap.put('use_mark', str(res[3]))
        hashMap.put('add_if_not_in_plan', str(res[4]))
        hashMap.put('path', str(res[5]))
        hashMap.put('delete_files', str(res[6]))
        hashMap.put('allow_overscan', str(res[9]))

    if not hashMap.containsKey('ip_host'):
        hashMap.put('ip_host', '192.168.1.77')

    return hashMap


def settings_on_click(hashMap, _files=None, _data=None):
    use_series = hashMap.get('use_series')
    use_properties = hashMap.get('use_properties')
    use_mark = hashMap.get('use_mark')
    delete_files = hashMap.get('delete_files')
    add_if_not_in_plan = hashMap.get('add_if_not_in_plan')
    allow_overscan = hashMap.get('allow_overscan')
    path = hashMap.get('path')

    if use_series is None: use_series = 'false'
    if use_properties is None: use_properties = 'false'
    if use_mark is None: use_mark = 'false'
    if add_if_not_in_plan is None: add_if_not_in_plan = 'false'
    if path is None: path = '//storage/emulated/0/Android/data/ru.travelfood.simple_ui/'  # '//storage/emulated/0/download/'
    if delete_files is None: delete_files = 'false'
    if allow_overscan is None: allow_overscan = 'false'
    # ui_global.get_query_result('Update RS_docs SET control = ?',(allow_overscan,))  #В таблицы документов записываем новое значение контроля
    ui_global.put_constants(
        (use_series, use_properties, use_mark, add_if_not_in_plan, path, delete_files, allow_overscan))
    listener = hashMap.get('listener')
    if listener == 'btn_copy_base':
        ip_host = hashMap.get('ip_host')
        if os.path.isfile('//data/data/ru.travelfood.simple_ui/databases/SimpleKeep'):
            with open('//data/data/ru.travelfood.simple_ui/databases/SimpleKeep', 'rb') as f:  # rightscan
                r = requests.post('http://' + ip_host + ':2444/post', files={'Rightscan': f})  # rightscan
            if r.status_code == 200:
                hashMap.put('toast', 'База SQLite успешно выгружена')
            else:
                hashMap.put('toast', 'Ошибка соединения')
        else:
            hashMap.put('toast', 'Файл не найден')

    elif listener == 'btn_local_files':
        # path = hashMap.get('localpath')
        path = hashMap.get('path')
        delete_files = hashMap.get('delete_files')
        if not delete_files: delete_files = '0'
        if not path: path = '//storage/emulated/0/download/'

        ret_text = ui_csv.list_folder(path, delete_files)

        hashMap.put('toast', ret_text)
    elif listener == 'btn_export':

        ui_csv.export_csv(path, hashMap.get('ip_adr'), hashMap.get('ANDROID_ID'))
        hashMap.put('toast', 'Данные выгружены')

    elif listener == 'ON_BACK_PRESSED':

        hashMap.put('FinishProcess', '')

    elif listener == 'btn_files_list':
        hashMap.put('ShowScreen', 'СписокФайлов')
    elif listener == 'btn_conf_version':
        conf = json.loads(hashMap.get('_configuration '))

    elif listener == 'btn_size':
        hashMap.put('ShowScreen', 'Настройки Шрифтов')
    elif listener == 'btn_test_barcode':
        hashMap.put('ShowScreen', 'Тест штрихкода')
    elif listener == 'btn_load_data':
        # http = get_http_settings(hashMap)
        # result = http_exchange.server_load_data(http)
        timer_update(hashMap, _files=None, _data=None)
        # if not result == 'ok':
        #     hashMap.put('toast',result)
    elif listener == 'btn_err_log':
        hashMap.put('ShowScreen', 'Ошибки')
    elif listener == 'btn_http_settings':
        hashMap.put('ShowScreen', 'Настройки http соединения')
    elif listener == 'bnt_clear_tables':
        qtext = '''
        SELECT name FROM sqlite_master WHERE type='table'
        '''
        res = ui_global.get_query_result(qtext)
        for el in res:
            del_text = 'DELETE FROM ' + el[0]
            ui_global.get_query_result(del_text)
    elif listener == 'btn_upload_docs':
        url = get_http_settings(hashMap)
        qtext = '''SELECT id_doc FROM RS_docs WHERE verified = 1'''
        res = ui_global.get_query_result(qtext, None, True)

        if res:
            doc_list = []
            for el in res:
                doc_list.append('"' + el['id_doc'] + '"')
            doc_in_str = ','.join(doc_list)
            # htpparams = {'username':hashMap.get('onlineUser'), 'password':hashMap.get('onlinePass'), 'url':url}
            answer = http_exchange.post_changes_to_server(doc_in_str, url)
            if answer.get('Error') is not None:
                rs_settings.put('error_log', str(answer.get('Error')), True)

            qtext = f'UPDATE RS_docs SET sent = 1  WHERE id_doc in ({doc_in_str}) '
            ui_global.get_query_result(qtext, (doc_in_str,), False)
    elif listener == 'btn_timer':
        timer_update(hashMap)

    return hashMap


def goods_on_start(hashMap, _files=None, _data=None):
    # hashMap.put("mm_local", "")
    # hashMap.put("mm_compression", "70")
    # hashMap.put("mm_size", "65")

    list = ui_form_data.get_goods_card(rs_settings)
    list['customcards']['cardsdata'] = []
    query_text = ui_form_data.get_goods_query()

    results = ui_global.get_query_result(query_text)

    for record in results:
        product_row = {
            'key': str(record[0]),
            'GTIN': str(record[0]),
            'name': str(record[3]),
            'code': str(record[1]),
            'type_name': str(record[5]),
            'unit_name': str(record[7])
        }
        list['customcards']['cardsdata'].append(product_row)
    # **********************
    hashMap.put("goods_cards", json.dumps(list))

    """hashMap.put('table_for_select', 'RS_goods')  # Таблица для выбора значения
    hashMap.put('SetResultListener', 'select_cell_value')
    hashMap.put('filter_fields', 'name;full_name;inn;kpp')
    hashMap.put('ShowProcessResult', 'Универсальный справочник|Справочник')"""


    return hashMap


# Заполнение списка документов
def refill_docs_list(filter=''):
    doc_list = ui_form_data.get_doc_card(rs_settings)
    doc_list['customcards']['cardsdata'] = []

    query_text = ui_form_data.get_doc_query(filter)

    if filter == '' or filter == 'Все':
        results = ui_global.get_query_result(query_text)
    else:
        results = ui_global.get_query_result(query_text, (filter,))

    for record in results:
        if record[8] == 1:
            completed = 'true'
        else:
            completed = 'false'
        product_row = {
            'completed': completed,
            'type': str(record[1]),
            'number': str(record[2]),
            'data': str(record[3]),
            'key': record[0],
            'warehouse': record[7],
            'countragent': record[6],
            'add_mark_selection': record[10]
        }
        doc_list['customcards']['cardsdata'].append(product_row)

    return json.dumps(doc_list)


def docs_on_start(hashMap, _files=None, _data=None):
    # Заполним поле фильтра по виду документов
    result = ui_global.get_query_result(ui_form_data.get_doc_type_query())
    if hashMap.get('doc_type_select') == None:
        doc_type_list = ['Все']
        for record in result:
            doc_type_list.append(record[0])
        hashMap.put('doc_type_select', ';'.join(doc_type_list))

    # hashMap.put('doc_type_click', 'Все')
    # Если Вызов экрана из меню плиток - обработаем
    if hashMap.containsKey('selected_tile_key'):
        tile_key = hashMap.get('selected_tile_key')
        if tile_key:
            hashMap.put('doc_type_click', tile_key)
            hashMap.put('selected_tile_key', '')
    # Перезаполним список документов
    if hashMap.get('doc_type_click') == None:
        ls = refill_docs_list()
    else:
        ls = refill_docs_list(hashMap.get('doc_type_click'))
    hashMap.put("docCards", ls)

    return hashMap


def doc_details_on_start(hashMap, _files=None, _data=None):
    id_doc = hashMap.get('id_doc')
    falseValueList = (0,'0','false','False',None)
    # Формируем таблицу карточек и запрос к базе
    res = ui_global.get_constants()
    use_series = res[1]
    use_properties = res[2]
    hashMap.put('use_properties', res[2])
    doc_detail_list = ui_form_data.get_doc_detail_cards(use_series, use_properties,rs_settings)
    doc_detail_list['customcards']['cardsdata'] = []

    # Получаем теекущий документ
    current_str = hashMap.get("selected_card_position")
    jlist = json.loads(hashMap.get('docCards'))

    elem_n = jlist['customcards']['cardsdata']

    for el in elem_n:
        if el['key'] == id_doc:
            hashMap.put('add_mark_selection',
                        str(el['add_mark_selection'] if el['add_mark_selection'] else '0'))
    #    current_elem = jlist['customcards']['cardsdata'][int(current_str)-1]

    query_text = ui_form_data.get_doc_details_query()

    results = ui_global.get_query_result(query_text, (id_doc,), True)

    if results:
        hashMap.put('id_doc', str(results[0]['id_doc']))
        for record in results:
            pic = '#f02a' if record['IsDone'] != 0 else '#f00c'
            if record['qtty'] == 0 and record['qtty_plan'] == 0:
                pic = ''
            product_row = {
                'key': str(record['id']),
                'good_name': str(record['good_name']),
                'id_good': str(record['id_good']),
                'id_properties': str(record['id_properties']),
                'properties_name': str(record['properties_name']),
                'id_series': str(record['id_series']),
                'series_name': str(record['series_name']),
                'id_unit': str(record['id_unit']),
                'units_name': str(record['units_name']),
                'code_art': 'Код: ' + str(record['code']),

                'qtty': str(record['qtty'] if record['qtty'] is not None else 0),
                'qtty_plan': str(record['qtty_plan'] if record['qtty_plan'] is not None else 0),
                'price': str(record['price'] if record['price'] is not None else 0),
                'price_name': str(record['price_name']),
                'picture': pic
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
    hashMap.put("doc_goods", json.dumps(doc_detail_list))

    return hashMap


def doc_adr_details_on_start(hashMap, _files=None, _data=None):
    id_doc = hashMap.get('id_doc')
    current_cell = hashMap.get('current_cell_id')

    falseValueList = (0,'0','false','False',None)
    # Формируем таблицу карточек и запрос к базе
    res = ui_global.get_constants()
    use_series = res[1]
    use_properties = res[2]
    hashMap.put('use_properties', res[2])
    doc_detail_list = ui_form_data.get_doc_detail_cards(use_series, use_properties,rs_settings, True)
    doc_detail_list['customcards']['cardsdata'] = []

    # Получаем теекущий документ
    current_str = hashMap.get("selected_card_position")
    jlist = json.loads(hashMap.get('docAdrCards'))

    elem_n = jlist['customcards']['cardsdata']

    for el in elem_n:
        if el['key'] == id_doc:
            hashMap.put('add_mark_selection',
                        str(el['add_mark_selection'] if el['add_mark_selection'] else '0'))
    #    current_elem = jlist['customcards']['cardsdata'][int(current_str)-1]

    query_text = ui_form_data.get_doc_details_query(True, True if current_cell else False)
    table_type_filter = hashMap.get('table_type_filter') if hashMap.get('table_type_filter') else 'out'
    if current_cell:
        params = (id_doc, table_type_filter, current_cell)
    else:
        params = (id_doc, table_type_filter)

    results = ui_global.get_query_result(query_text, params, True)

    if results:
        hashMap.put('id_doc', str(results[0]['id_doc']))
        current_cell =''
        for record in results:
            pic = '#f02a' if record['IsDone'] != 0 else '#f00c'
            if record['qtty'] == 0 and record['qtty_plan'] == 0:
                pic = ''

            if current_cell != record['cell_name']:
                c = {"group": record['cell_name']}
                doc_detail_list['customcards']['cardsdata'].append(c)
                current_cell = record['cell_name']

            product_row = {
                'key': str(record['id']),
                'good_name': str(record['good_name']),
                'id_good': str(record['id_good']),
                'id_properties': str(record['id_properties']),
                'properties_name': str(record['properties_name']),
                'id_series': str(record['id_series']),
                'series_name': str(record['series_name']),
                'id_unit': str(record['id_unit']),
                'units_name': str(record['units_name']),
                'code_art': 'Код: ' + str(record['code']),
                'cell_name': str(record['cell_name']),
                'id_cell': str(record['id_cell']),

                'qtty': str(record['qtty'] if record['qtty'] is not None else 0),
                'qtty_plan': str(record['qtty_plan'] if record['qtty_plan'] is not None else 0),
                'picture': pic
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
    hashMap.put("doc_goods", json.dumps(doc_detail_list))

    return hashMap


def doc_adr_details_listener(hashMap, _files=None, _data=None):
    # Находим ID документа
    # current_str = hashMap.get("selected_card_position")
    # current_card_list = hashMap.get("doc_goods")
    # jl = jlist['customcards']['cardsdata']
    # if not current_card_list == None:
    #     jlist = json.loads(current_card_list)
    #     current_elem = jlist['customcards']['cardsdata'][int(current_str)-1]
    # else:
    #     current_elem = None
    listener = hashMap.get('listener')
    if listener == "CardsClick":

        # Находим ID документа
        current_str = hashMap.get("selected_card_position")
        jlist = json.loads(hashMap.get("doc_goods"))
        current_elem = jlist['customcards']['cardsdata'][int(current_str)]
        hashMap.put("Doc_data",
                    hashMap.get('doc_type') + ' №' + hashMap.get('doc_n') +
                    ' от' + hashMap.get('doc_date'))
        hashMap.put("current_cell_name", 'Ячейка: ' +  current_elem['cell_name'])
        hashMap.put('id_cell', current_elem['id_cell'])
        hashMap.put("Good", current_elem['good_name'])
        hashMap.put("qtty_plan", str(current_elem['qtty_plan']))
        if not current_elem['qtty']:  # or float(current_elem['qtty']) == 0:
            hashMap.put("qtty", '')
        else:
            if float(current_elem['qtty']) == 0:
                hashMap.put("qtty", '')
            else:
                hashMap.put("qtty", str(current_elem['qtty']))
        hashMap.put('key', current_elem['key'])

        hashMap.put("ShowScreen", "Товар")

    elif listener == "BACK_BUTTON":
        hashMap.put("ShowScreen", "Документы")
    elif listener == "btn_barcodes":

        hashMap.put("ShowDialog", "ВвестиШтрихкод")

    # elif hashMap.get("event") == "onResultPositive":

    elif listener == 'barcode' or hashMap.get("event") == "onResultPositive":
        current_cell = hashMap.get('current_cell')

        doc = ui_global.Rs_adr_doc
        doc.id_doc = hashMap.get('id_doc')
        if hashMap.get("event") == "onResultPositive":
            barcode = hashMap.get('fld_barcode')
        else:
            barcode = hashMap.get('barcode_camera')

        doc_cell = doc.find_cell(doc, barcode)
        if not current_cell and not doc_cell:
            hashMap.put('toast', 'До сканирования товаров необходимо отсканировать или указать ячейку')
            return hashMap

        if doc_cell:
            hashMap.put('current_cell', doc_cell['name'])
            hashMap.put('current_cell_id', doc_cell['id'])
            return hashMap


        have_qtty_plan = hashMap.get('have_qtty_plan')
        have_zero_plan = hashMap.get('have_zero_plan')
        have_mark_plan = hashMap.get('have_mark_plan')
        control = hashMap.get('control')
        res = doc.process_the_barcode(doc, barcode
                                      , eval(have_qtty_plan), eval(have_zero_plan), eval(control),  current_cell)
        if res == None:
            hashMap.put('scanned_barcode', barcode)
            # suClass.urovo_set_lock_trigger(True)
            hashMap.put('ShowScreen', 'Ошибка сканера')
            # hashMap.put('toast',
            #             'Штрих код не зарегистрирован в базе данных. Проверьте товар или выполните обмен данными')
        elif res['Error']:
            if res['Error'] == 'AlreadyScanned':

                hashMap.put('barcode', json.dumps({'barcode': res['Barcode'], 'doc_info': res['doc_info']}))
                hashMap.put('ShowScreen', 'Удаление штрихкода')
            elif res['Error'] == 'QuantityPlanReached':
                hashMap.put('toast', res['Descr'])
            elif res['Error'] == 'Zero_plan_error':
                hashMap.put('toast', res['Descr'])
            else:
                hashMap.put('toast', res['Descr'] )  #+ ' '+ res['Barcode']
        else:
            hashMap.put('toast', 'Товар добавлен в документ')
            # ---------------------------------------------------------
    elif listener == 'btn_doc_mark_verified':
        doc = ui_global.Rs_adr_doc
        doc.id_doc = hashMap.get('id_doc')
        doc.mark_verified(doc, 1)
        hashMap.put("ShowScreen", "Документы")

    elif listener == 'ON_BACK_PRESSED':
        if hashMap.get('current_cell_id'):
            hashMap.remove('current_cell')
            hashMap.remove('current_cell_id')
        else:
            hashMap.put("ShowScreen", "Документы")

    elif listener == 'btn_clear_cell':
        hashMap.remove('current_cell')
        hashMap.remove('current_cell_id')

    elif listener == 'btn_select_cell': #Кнопка выбрать ячейку

        hashMap.remove('current_cell')
        hashMap.remove('current_cell_id')

        hashMap.put('table_for_select', 'RS_cells') #Таблица для выбора значения
        hashMap.put('SetResultListener', 'select_cell_value')
        hashMap.put('filter_fields','name;barcode')
        hashMap.put('ShowProcessResult','Универсальный справочник|Справочник')

    elif listener == 'select_cell_value':
        if hashMap.get('current_id'):
            hashMap.put('current_cell_id',hashMap.get('current_id'))
            hashMap.put('current_cell', hashMap.get('current_name'))

    elif listener =='LayoutAction':
        layout_listener = hashMap.get('layout_listener')
        # Находим ID строки
        current_str = int(hashMap.get("selected_card_position"))
        jlist = json.loads(hashMap.get("doc_goods"))
        current_elem = jlist['customcards']['cardsdata'][current_str]
        if current_elem.get('group'):
            current_elem = jlist['customcards']['cardsdata'][current_str+1]
        #
        if layout_listener == 'Удалить строку':

            if current_elem['key']:
                ui_global.get_query_result('DELETE FROM RS_adr_docs_table WHERE id = ?', (current_elem['key'],))
        elif layout_listener == 'Изменить ячейку':
            pass

    return hashMap


def docs_on_select(hashMap, _files=None, _data=None):
    listener = hashMap.get("listener")

    if listener == "CardsClick":
        # Находим ID документа
        current_str = hashMap.get("selected_card_position")
        jlist = json.loads(hashMap.get("docCards"))
        current_doc = jlist['customcards']['cardsdata'][int(current_str)]

        # id_doc = current_doc['key']
        hashMap.put('id_doc', current_doc['key'])
        hashMap.put('doc_type', current_doc['type'])
        hashMap.put('doc_n', current_doc['number'])
        hashMap.put('doc_date', current_doc['data'])
        hashMap.put('warehouse', current_doc['warehouse'])
        hashMap.put('countragent', current_doc['countragent'])

        hashMap.put("ShowScreen", "Документ товары")

    elif listener == "doc_type_click":
        ls = refill_docs_list(hashMap.get('doc_type_click'))
        hashMap.put('docCards', ls)
        hashMap.put('ShowScreen', 'Документы')
    elif listener == 'LayoutAction':
        layout_listener = hashMap.get('layout_listener')
        # Находим ID документа
        current_doc = json.loads(hashMap.get("card_data"))
        doc = ui_global.Rs_doc
        doc.id_doc = current_doc['key']

        if layout_listener == 'CheckBox1':
            if current_doc['completed'] == 'false':
                doc.mark_verified(doc, 1)
            else:
                doc.mark_verified(doc, 0)

        elif layout_listener == 'Подтвердить':
            doc.mark_verified(doc, 1)
            hashMap.put('ShowScreen', 'Документы')
        elif layout_listener == 'Очистить данные пересчета':
            doc.clear_barcode_data(doc)
            hashMap.put('toast', 'Данные пересчета и маркировки очищены')
        elif layout_listener == 'Удалить':
            doc.delete_doc(doc)
            hashMap.put('ShowScreen', 'Документы')
        elif layout_listener == 'Сканировать штрихкоды потоком':

            # id_doc = current_doc['key']
            hashMap.put('id_doc', current_doc['key'])
            hashMap.put('doc_type', current_doc['type'])
            hashMap.put('doc_n', current_doc['number'])
            hashMap.put('doc_date', current_doc['data'])
            hashMap.put('warehouse', current_doc['warehouse'])
            hashMap.put('countragent', current_doc['countragent'])

            hashMap.put('ShowScreen','ПотокШтрихкодовДокумента')
    elif listener == "btn_add_doc":
        hashMap.put('ShowScreen', 'Новый документ')

    elif listener == 'ON_BACK_PRESSED':
        hashMap.put('ShowScreen', 'Плитки')
        # hashMap.put('FinishProcess', '')

        # hashMap.put('ShowScreen', 'Новый документ')
    return hashMap


def doc_details_listener(hashMap, _files=None, _data=None):
    # Находим ID документа
    # current_str = hashMap.get("selected_card_position")
    # current_card_list = hashMap.get("doc_goods")
    # jl = jlist['customcards']['cardsdata']
    # if not current_card_list == None:
    #     jlist = json.loads(current_card_list)
    #     current_elem = jlist['customcards']['cardsdata'][int(current_str)-1]
    # else:
    #     current_elem = None
    listener = hashMap.get('listener')
    if listener == "CardsClick":

        # Находим ID документа
        current_str = hashMap.get("selected_card_position")
        jlist = json.loads(hashMap.get("doc_goods"))
        current_elem = jlist['customcards']['cardsdata'][int(current_str)]
        hashMap.put("Doc_data",
                    hashMap.get('doc_type') + ' №' + hashMap.get('doc_n') +
                    ' от' + hashMap.get('doc_date'))
        hashMap.put("Good", current_elem['good_name'])
        hashMap.put("qtty_plan", str(current_elem['qtty_plan']))
        if not current_elem['qtty']:  # or float(current_elem['qtty']) == 0:
            hashMap.put("qtty", '')
        else:
            if float(current_elem['qtty']) == 0:
                hashMap.put("qtty", '')
            else:
                hashMap.put("qtty", str(current_elem['qtty']))
        hashMap.put('key', current_elem['key'])
        hashMap.put('price', current_elem['price'])
        hashMap.put('price_type', current_elem['price_name'])
        # Формируем таблицу QR кодов------------------
        query_text = ui_form_data.get_doc_barcode_query()
        args = dict(id_good=current_elem['id_good'], id_property=current_elem['id_properties'],
                    id_series=current_elem['id_series'], id_unit=current_elem['id_unit'], id_doc=hashMap.get('id_doc'))

        cards = ui_form_data.get_barcode_card(rs_settings)
        res = ui_global.get_query_result(query_text, args, True)
        # Формируем список карточек баркодов
        cards['customcards']['cardsdata'] = []
        for el in res:
            # barcode_data = ui_barcodes.get_gtin_serial_from_datamatrix(el['barcode'])
            if el['approved'] == 'True' or el['approved'] == '1' or el['approved'] == 'true':
                picture = '#f00c'
            else:
                picture = ''
            row = {
                'barcode': el['mark_code'],
                'picture': picture
            }
            cards['customcards']['cardsdata'].append(row)
        hashMap.put("barcode_cards", json.dumps(cards))

        hashMap.put("ShowScreen", "Товар")

    elif listener == "BACK_BUTTON":
        hashMap.put("ShowScreen", "Документы")
    elif listener == "btn_barcodes":

        hashMap.put("ShowDialog", "ВвестиШтрихкод")

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
        res = doc.process_the_barcode(doc, barcode
                                      , eval(have_qtty_plan), eval(have_zero_plan), eval(control), eval(have_mark_plan))
        if res == None:
            hashMap.put('scanned_barcode', barcode)
            # suClass.urovo_set_lock_trigger(True)
            hashMap.put('ShowScreen', 'Ошибка сканера')
            # hashMap.put('toast',
            #             'Штрих код не зарегистрирован в базе данных. Проверьте товар или выполните обмен данными')
        elif res['Error']:
            if res['Error'] == 'AlreadyScanned':

                hashMap.put('barcode', json.dumps({'barcode': res['Barcode'], 'doc_info': res['doc_info']}))
                hashMap.put('ShowScreen', 'Удаление штрихкода')
            elif res['Error'] == 'QuantityPlanReached':
                hashMap.put('toast', res['Descr'])
            elif res['Error'] == 'Zero_plan_error':
                hashMap.put('toast', res['Descr'])
            else:
                hashMap.put('toast', res['Descr'] )  #+ ' '+ res['Barcode']
        else:
            hashMap.put('toast', 'Товар добавлен в документ')
        # hashMap.put('toast','1')
        #-------------------------------------------------- Временно
        url = get_http_settings(hashMap)
        qtext = '''SELECT id_doc FROM RS_docs WHERE verified = 1'''
        res = ui_global.get_query_result(qtext, None, True)

        if res:
            doc_list = []
            for el in res:
                doc_list.append('"' + el['id_doc'] + '"')
            doc_in_str = ','.join(doc_list)
            # htpparams = {'username':hashMap.get('onlineUser'), 'password':hashMap.get('onlinePass'), 'url':url}
            answer = http_exchange.post_changes_to_server(doc_in_str, url)
            if answer.get('Error') is not None:
                rs_settings.put('error_log', str(answer.get('Error')), True)

            qtext = f'UPDATE RS_docs SET sent = 1  WHERE id_doc in ({doc_in_str}) '
            ui_global.get_query_result(qtext, None, False)
        # ---------------------------------------------------------
    elif listener == 'btn_doc_mark_verified':
        doc = ui_global.Rs_doc
        doc.id_doc = hashMap.get('id_doc')
        doc.mark_verified(doc, 1)
        hashMap.put("ShowScreen", "Документы")

    elif listener == 'ON_BACK_PRESSED':
        hashMap.put("ShowScreen", "Документы")

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


def elem_on_start(hashMap, _files=None, _data=None):
    hashMap.put('mm_local', '')
    return hashMap


def elem_on_click(hashMap, _files=None, _data=None):
    listener = hashMap.get("listener")
    if listener == "btn_ok":
        # получим текущую строку документа
        current_str = hashMap.get("selected_card_position")
        jlist = json.loads(hashMap.get("doc_goods"))
        current_elem = jlist['customcards']['cardsdata'][int(current_str)]
        key = int(current_elem['key'])
        # ... и запишем ее в базу

        doc = ui_global.Rs_doc
        doc.id_str = int(current_elem['key'])
        qtty = hashMap.get('qtty')
        doc.qtty = float(qtty) if qtty else 0
        doc.update_doc_str(doc, hashMap.get('price'))

        hashMap.put("ShowScreen", "Документ товары")
    elif listener == "btn_cancel":

        hashMap.put("ShowScreen", "Документ товары")
    elif listener == "BACK_BUTTON":
        hashMap.put("ShowScreen", "Документ товары")
    elif listener == "":
        hashMap.put("qtty", str(float(hashMap.get('qtty'))))
    elif listener == 'ON_BACK_PRESSED':
        hashMap.put("ShowScreen", "Документ товары")

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


def goods_on_click(hashMap, _files=None, _data=None):
    listener = hashMap.get("listener")

    if listener == "CardsClick":
        # Находим ID документа
        current_str = hashMap.get("selected_card_position")
        jlist = json.loads(hashMap.get("goods_cards"))
        current_good = jlist['customcards']['cardsdata'][int(current_str)]

        # id_doc = current_doc['key']
        hashMap.put('id_good', current_good['key'])
        hashMap.put('name', current_good['name'])
        hashMap.put('code', current_good['code'])
        hashMap.put('type_name', current_good['type_name'])
        #        hashMap.put('unit_name', current_good['unit_name'])

        hashMap.put("ShowScreen", "Цены товара")

    elif listener == 'ON_BACK_PRESSED':

        hashMap.put('FinishProcess', '')

    return hashMap


def price_on_start(hashMap, _files=None, _data=None):
    id_good = hashMap.get('id_good')
    # Формируем таблицу карточек и запрос к базе
    goods_price_list = ui_form_data.get_price_card(rs_settings)
    goods_price_list['customcards']['cardsdata'] = []

    query_text = ui_form_data.get_price_query()

    results = ui_global.get_query_result(query_text, (id_good,))
    for record in results:
        product_row = {
            'key': str(record[0]),
            'good_name': str(record[3]),
            # 'id_properties': str(record[3]),
            'properties_name': str(record[5]),
            # 'id_series': str(record[5]),
            'series_name': str(record[7])}
    return hashMap


def price_on_click(hashMap, _files=None, _data=None):
    if hashMap.get('listener') == 'ON_BACK_PRESSED':
        hashMap.put("ShowScreen", "Товары список")
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


def new_doc_on_select(hashMap, _files=None, _data=None):
    listener = hashMap.get("listener")
    type = hashMap.get('doc_type_click')
    if not type:
        type = 'Приход'
    fld_number = hashMap.get('fld_number')

    if listener == "btn_ok":
        if not fld_number:

            id = ui_global.Rs_doc.get_new_id(1)
            # id = (f'{id:04}')
            # id = "{0:0>4}".format(id)
        else:
            id = fld_number

        try:
            ui_global.Rs_doc.add('01', (id,
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


def doc_barcodes_on_start(hashMap, _files=None, _data=None):
    doc_detail_list = ui_form_data.get_barcode_card(rs_settings)
    query_text = ui_form_data.get_barcode_query()
    id_doc = hashMap.get('id_doc')
    results = ui_global.get_query_result(query_text, (id_doc,))

    for record in results:
        product_row = {
            'key': str(record[0]),
            'barcode_value': str(record[3]),
            'approved': str(record[4])

        }

        doc_detail_list['customcards']['cardsdata'].append(product_row)

    hashMap.put("barc_cards", json.dumps(doc_detail_list))

    return hashMap


def doc_barcodes_listener(hashMap, _files=None, _data=None):
    if hashMap.get('listener') == 'ON_BACK_PRESSED':
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


def tiles_on_start(hashMap, _files=None, _data=None):
    small_tile = ui_form_data.get_doc_tiles(rs_settings)
    qtext = ui_form_data.get_docs_stat_query()
    res = ui_global.get_query_result(qtext, None, True)

    x = {'tiles': [[]], "background_color": "#f5f5f5"}

    # x['tiles':[0][0]]=1
    rows = 1
    columns = 1
    for el in res:
        if el['docType']==None:
            continue
        if columns % 3 == 0:
            rows += 1
            columns = 0
            x['tiles'].append([])
        columns += 1

        tile = {

            "layout": small_tile,
            "data": {
                "docName": el['docType'],
                'QttyOfDocs': str(el['count']) + '/' + str(el['verified']),
                # 'QttyOfDocsIncompleted':el['count'] - el['verified']
                'count_verified': str(el['count_verified']+el['count_unverified']) + '/' + str(el['count_unverified']),
                'qtty_plan_verified': str(el['qtty_plan_verified']+el['qtty_plan_unverified']) + '/' + str(el['qtty_plan_unverified']),

            },
            "height": "wrap_content",
            "color": '#FFFFFF',  # "#FFCC99",
            "start_screen": "Документы",

            "start_process": "",
            'key': el['docType']
        }

        x['tiles'][rows - 1].append(tile)

    hashMap.put("tiles", json.dumps(x, ensure_ascii=False).encode('utf8').decode())
    return hashMap


def tiles_on_select(hashMap, _files=None, _data=None):
    listener = hashMap.get("listener")

    if listener == "CardsClick":
        pass
    elif listener == 'ON_BACK_PRESSED':

        hashMap.put('FinishProcess', '')
    return hashMap


def app_on_start(hashMap, _files=None, _data=None):
    # hashMap.put('InstallConfiguration', '')
    # hashMap.put('UpdateMenu', '')
    # hashMap.put('toast', 'Конфа установлена!!!')
    shema = database_init_queryes.database_shema()
    for el in shema:
        res = ui_global.get_query_result(el)


        # for parameter_name, value in parameters.items():
        #     set_params.put(parameter_name,value)
    if rs_settings.get('TitleTextSize') == None:
        rs_settings.put("TitleTextSize", "18", True)
        rs_settings.put("titleDocTypeCardTextSize", "18", True)
        rs_settings.put("CardTitleTextSize", "20", True)
        rs_settings.put("CardDateTextSize", "10", True)
        rs_settings.put("CardTextSize", "15", True)
        rs_settings.put("GoodsCardTitleTextSize", "18", True)
        rs_settings.put("goodsTextSize", "18", True)
        rs_settings.put("SeriesPropertiesTextSize", "16", True)
        rs_settings.put("DocTypeCardTextSize", "15", True)

    hashMap.put('toast', 'Готов к работе')

    # Проверим, свопадают ли текущий релиз конфы и запись о нем в БД, если нет - то надо выполнить процедуру обновления
    # if not ui_global.get_constants('release') == hashMap.get('release'):
    # update_proc.update_on_release(current_release)
    # ui_global.get_query_result('Update RS_constants set release = ?',(hashMap.get('release'),))

    return hashMap


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


def event_service(hashMap, _files=None, _data=None):
    # hashMap.put('_configuration','')
    hashMap.put('ws_body', hashMap.get('ANDROID_ID'))

    return hashMap


def put_notification(hashMap, _files=None, _data=None):
    hashMap.put('_configuration','')
    qtext = 'SELECT doc_type, count(id_doc) as count, max(created_at) as dt FROM RS_docs WHERE created_at>? GROUP BY doc_type'
    lastDate = rs_settings.get('lastDate')
    if not lastDate:
        lastDate = '2020-01-01 00:00:00'  # one_month_ago.strftime('%Y-%m-%d-%H-%M-%S')
    res = ui_global.get_query_result(qtext,(lastDate,),True)
    DocList = ''
    if res:
        for el in res:
            DocList = DocList + (' ' + el['doc_type'] + ': ' + str(el['count']))

        hashMap.put('basic_notification', json.dumps([{'number':1, 'title':'Новые документы', 'message': DocList }]))
        qtext = 'SELECT max(created_at) as dt FROM RS_docs'
        res2 = ui_global.get_query_result(qtext)

        rs_settings.put('lastDate',res2[0][0],True)
        hashMap.put('toast',lastDate)

    return hashMap

def btn_on_save(hashMap, _files=None, _data=None):
   # params = json.loads(rs_settings.getallkeys())  # RSSettings()
    params = rs_settings
    params.put("TitleTextSize", hashMap.get("TitleTextSize"),True)
    params.put("CardTitleTextSize", hashMap.get("CardTitleTextSize"),True)
    params.put("CardTextSize", hashMap.get("CardTextSize"), True)
    params.put("CardDateTextSize", hashMap.get("CardDateTextSize"),True)
    params.put("GoodsCardTitleTextSize", hashMap.get("GoodsCardTitleTextSize"),True)
    params.put("goodsTextSize", hashMap.get("goodsTextSize"),True)
    params.put("SeriesPropertiesTextSize", hashMap.get("SeriesPropertiesTextSize"),True)
    params.put("DocTypeCardTextSize", hashMap.get("DocTypeCardTextSize"),True)
    params.put("titleDocTypeCardTextSize", hashMap.get("titleDocTypeCardTextSize"), True)
    return hashMap


def btn_on_cancel(hashMap, _files=None, _data=None):
    hashMap.put('ShowScreen', 'Настройки и обмен')
    return hashMap


def font_sizes_on_start(hashMap, _files=None, _data=None):
    params = json.loads(rs_settings.getallkeys())
    # Словарик названий и имен размеров шрифтов
    ss = {
        'TitleTextSize': 'Размер заголовка',
        'CardTitleTextSize': 'Размер заголовка карточки',
        "CardDateTextSize": 'Данные карточки',
        "GoodsCardTitleTextSize": 'Заголовок товара',
        'titleDocTypeCardTextSize':'Название документа в карточке',
        "goodsTextSize": 'Товар',
        "SeriesPropertiesTextSize": 'Серии свойства',
        "DocTypeCardTextSize": 'Тип документа'}

    for parameter_name in params:  # .items():
        hashMap.put(parameter_name, json.dumps(
            {
                "hint": parameter_name, #str(ss[parameter_name]),
                "default_text": str(rs_settings.get(parameter_name))
            }
        ))
    return hashMap

def test_barcode_listener(hashMap, _files=None, _data=None):
    if hashMap.get('listener')=='barcode' or hashMap.get("event") == "onResultPositive":
        if hashMap.get("event") == "onResultPositive":
            barcode = hashMap.get('fld_barcode')
        else:
            barcode = hashMap.get('barcode_camera')
        barc = ui_barcodes.parse_barcode(barcode)
        keys_list = ['ERROR','GTIN','SERIAL','FullCode', 'BARCODE', 'SCHEME', 'EXPIRY', 'BATCH', 'NHRN', 'CHECK', 'WEIGHT', 'PPN']
        x=1
        for i in keys_list:
            res_value =  barc.get(i,None)
            if res_value:
                hashMap.put('fld_'+str(x),str(i)+': '+ res_value)
                x+=1
        #Если заполнено менее 5 полей, сотрем остальные прошлые значения
        while x<=7:
            hashMap.put('fld_' + str(x), '')
            x+=1

    elif hashMap.get('listener') == "BACK_BUTTON" or 'ON_BACK_PRESSED':
        hashMap.put("ShowScreen", "Настройки и обмен")

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


def timer_update(hashMap,  _files=None, _data=None):
    url = get_http_settings(hashMap)
    #url = 'http://192.168.1.77/NSI/hs/simple_accounting/data'

    #hashMap.put('toast', 'Обмен') #url)
    try:
        result = http_exchange.server_load_data(url)
    except:
        raise 'Ошибка запроса к HTTP'
    if result['status_code'] ==200:
        if result.get('batch') is not None:
            rs_settings.put('batch', result.get('batch'),True)
            rs_settings.put('number_of_received','0', True)

        if result.get('res_for_sql') is not None:

            if rs_settings.get('batch') is not None:  #Мы выполняем пакет загрузки, данные разбиты на несколько файлов, их количество в batch
                number_of_received = int(rs_settings.get('number_of_received'))
                total_received = int(rs_settings.get('batch'))
                number_of_received =+1
            else:
                total_received = None

            sql_error = False
            error_pool = []
            for key in result['res_for_sql']:
                try:
                    ui_global.get_query_result(key)
                    # return 'ok'
                except Exception as e:
                    sql_error = True
                    error_pool.append(e.args[0])


            if total_received:
                hashMap.put('toast', 'Идет загрузка большого объема данных. Получено '+ str(number_of_received*50000) + 'из, примерно '+ str(total_received*50000))
                rs_settings.put('number_of_received',str(number_of_received), True)

            if sql_error:
                rs_settings.put('error_log', str(error_pool), True)
                hashMap.put('toast', 'При загрузке были ошибки. Проверьте их в настройках (кнопка посмотреть ошибки)')
        #docs_on_start(hashMap)
        #tiles_on_start(hashMap)
        #hashMap.put('RefreshScreen','')

    else:

        hashMap.put('toast', str(result['error_pool']))

    qtext = '''SELECT id_doc FROM RS_docs WHERE verified = '1'  and (sent <> '1' or sent is null)'''
    res  = ui_global.get_query_result(qtext,None,True)

    if res:
        doc_list = []
        for el in res:
            doc_list.append('"'+ el['id_doc']+'"')
        doc_in_str = ','.join(doc_list)
        #htpparams = {'username':hashMap.get('onlineUser'), 'password':hashMap.get('onlinePass'), 'url':url}
        answer = http_exchange.post_changes_to_server(doc_in_str , url)
        if answer.get('Error') is not None:
            rs_settings.put('error_log', str(answer.get('Error')), True)

        qtext = 'UPDATE RS_docs SET sent = 1  WHERE id_doc in (?) '
        ui_global.get_query_result(qtext,(doc_in_str,) , False)

    return hashMap


def settings_errors_on_start(hashMap,  _files=None, _data=None):
    err = rs_settings.get('error_log')
    hashMap.put('error_log', err)
    return hashMap

def settings_errors_on_click(hashMap,  _files=None, _data=None):
    listener = hashMap.get('listener')
    if listener == 'ON_BACK_PRESSED':
        hashMap.put('ShowScreen', 'Настройки и обмен')
        #hashMap.put('FinishProcess', '')

    elif listener == 'btn_clear_err':
        pass
    return hashMap


def get_http_settings(hashMap):
    http_settings = {
    'url' : rs_settings.get("URL"),
    'user' : rs_settings.get('USER'),
    'pass' : rs_settings.get('PASS'),
    'device_model' : hashMap.get('DEVICE_MODEL'),
    'android_id':hashMap.get('ANDROID_ID'),
    'user_name': rs_settings.get('user_name')}
    return http_settings

def http_settings_on_start(hashMap,  _files=None, _data=None):
    url = hashMap.get('url')
    hashMap.put('btn_test_connection', 'Тест соединения')
    if url == '' or 'not found':  #Обновляем только если ранее не установлены
        http_settings = get_http_settings(hashMap)
        hashMap.put('url',  ui_form_data.ModernField(hint='url', default_text=http_settings['url'], password=False).to_json()) #  )
        hashMap.put('user', ui_form_data.ModernField(hint='user', default_text=http_settings['user'], password=False).to_json())
        hashMap.put('pass', ui_form_data.ModernField(hint='pass', default_text=http_settings['pass'], password=True).to_json())
        hashMap.put('user_name',
                    ui_form_data.ModernField(hint='user_name', default_text=http_settings['user_name'], password=False).to_json())
    return hashMap


def http_settings_on_click(hashMap,  _files=None, _data=None):
    listener = hashMap.get('listener')
    if listener == 'btn_save':
        rs_settings.put('URL', hashMap.get('url'),True)
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
        r = requests.get(http['url'] + '/simple_accounting/communication_test?android_id=' + http['android_id'], auth=HTTPBasicAuth(http['user'], http['pass']),
             headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'},
             params={'user_name': http['user_name'], 'device_model': http['device_model']})
        if r.status_code == 200:
            hashMap.put('btn_test_connection', 'Соединение установлено')
        else:
            hashMap.put('btn_test_connection', r.reason)

    return hashMap

# Заполнение списка документов
def refill_adr_docs_list(filter=''):
    doc_list = ui_form_data.get_doc_card(rs_settings, ';Открыть отбор;Открыть размещение')
    doc_list['customcards']['cardsdata'] = []

    query_text = ui_form_data.get_adr_doc_query(filter)

    if filter == None or filter == '' or filter == 'Все':
        results = ui_global.get_query_result(query_text)
    else:
        results = ui_global.get_query_result(query_text, (filter,))

    for record in results:
        completed = 'true' if record[6] == 1 else 'false'
        add_mark_selection = 'true' if record[8] == 1 else 'false'

        product_row = {
            'completed': completed,
            'type': str(record[1]),
            'number': str(record[2]),
            'data': str(record[3]),
            'key': record[0],
            'warehouse': record[5],
            'add_mark_selection': add_mark_selection
        }
        doc_list['customcards']['cardsdata'].append(product_row)

    return json.dumps(doc_list)


def docs_adr_on_start(hashMap, _files=None, _data=None):
    # Заполним поле фильтра по виду документов
    doc_type_list = ['Все','Отбор','Размещение','Перемещение']
    hashMap.put('doc_adr_type_select', ';'.join(doc_type_list))

    #hashMap.put('fld_number','1')

    # hashMap.put('doc_type_click', 'Все')
    # Если Вызов экрана из меню плиток - обработаем

    # Перезаполним список документов
    if hashMap.get('doc_adr_type_click') == None:
        ls = refill_adr_docs_list()
    else:
        ls = refill_adr_docs_list(hashMap.get('doc_adr_type_click'))
    hashMap.put("docAdrCards", ls)

    return hashMap

def open_adr_doc_table(hashMap, filter = ''):
    # Находим ID документа
    current_str = hashMap.get("selected_card_position")
    jlist = json.loads(hashMap.get("docAdrCards"))
    current_doc = jlist['customcards']['cardsdata'][int(current_str)]

    # id_doc = current_doc['key']
    hashMap.put('id_doc', current_doc['key'])
    hashMap.put('doc_type', current_doc['type'])
    hashMap.put('doc_n', current_doc['number'])
    hashMap.put('doc_date', current_doc['data'])
    hashMap.put('warehouse', current_doc['warehouse'])
    filter = 'in'  if current_doc['type'] == 'Размещение' else 'out'
    if filter:
        hashMap.put('table_type_filter', filter)



def docs_adr_on_select(hashMap, _files=None, _data=None):
        listener = hashMap.get("listener")

        if listener == "CardsClick":
           open_adr_doc_table(hashMap)
           hashMap.put("ShowScreen", "Документ товары")

        elif listener == "doc_adr_type_click":

            ls = refill_adr_docs_list(hashMap.get('doc_adr_type_click'))
            hashMap.put('docCards', ls)
            hashMap.put('ShowScreen', 'Документы')
        elif listener == 'LayoutAction':
            layout_listener = hashMap.get('layout_listener')
            # Находим ID документа
            current_doc = json.loads(hashMap.get("card_data"))
            doc = ui_global.Rs_adr_doc
            doc.id_doc = current_doc['key']

            if layout_listener == 'CheckBox1':
                if current_doc['completed'] == 'false':
                    doc.mark_verified(doc, 1)
                else:
                    doc.mark_verified(doc, 0)

            elif layout_listener == 'Подтвердить':
                doc.mark_verified(doc, 1)
                hashMap.put('ShowScreen', 'Документы')
            elif layout_listener == 'Очистить данные пересчета':
                doc.clear_barcode_data(doc)
                hashMap.put('toast', 'Данные пересчета и маркировки очищены')
            elif layout_listener == 'Удалить':
                doc.delete_doc(doc)
                hashMap.put('ShowScreen', 'Документы')
            elif layout_listener == 'Удалить':
                doc.delete_doc(doc)
            elif layout_listener == 'Открыть отбор':
                open_adr_doc_table(hashMap, 'out')
                hashMap.put("ShowScreen", "Документ товары")
            elif layout_listener == 'Открыть размещение':
                open_adr_doc_table(hashMap, 'in')
                hashMap.put("ShowScreen", "Документ товары")

        elif listener == "btn_add_doc":
            hashMap.put('ShowScreen', 'Новый документ')

        elif listener == 'ON_BACK_PRESSED':

            hashMap.put('FinishProcess', '')

            # hashMap.put('ShowScreen', 'Новый документ')
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
    if not type:
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

def universal_cards_on_start(hashMap, _files=None, _data=None):
    #filter_value =hashMap.get('SearchString')
    #if filter_value:
    #    filter_fields = hashMap.get('filter_fields').split(';')
    #else:
    #filter_fields = list()
    hashMap.put('cards', get_table_cards(hashMap.get('table_for_select')))

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


def get_table_cards(table_name: str, filter_fields=list(), filter_value=''):
    # Получим список полей таблицы
    #table_name = 'RS_goods'
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
        link_table_name = tables_dict.get(el)
        qfield_text.append(table_name + '.' + el)

        # Дополним выходную структуру полями таблицы:
        aliases_elem = aliases.get(el)
        if aliases_elem: #Для этого поля предусмотрена настройка
            if not aliases_elem['name'] == 'key':  #Для ключа настройки не нужны
                #добавим описание поля:...
                card_elem['Value'] = aliases_elem['name']
                card_elem['TextSize'] = rs_settings.get('CardDateTextSize') # aliases_elem['text_size']
                card_elem['TextBold'] = False
                cards['customcards']['layout']['Elements'][0]['Elements'][0]['Elements'].append(card_elem.copy())

                #Теперь само поле:
                card_elem['Value'] = '@' + el
                card_elem['TextSize'] = rs_settings.get(aliases_elem['text_size'])
                card_elem['TextBold'] = aliases_elem['TextBold']
        else:  #Иначе просто добавим его со стандатртными настройками
            card_elem['Value'] = '@' + el

        if link_table_name:
            # Это ссылка на таблицу
            qfield_text.append(link_table_name + f'.name as {link_table_name}_name')
            left_joins_list.append(f'''
                LEFT JOIN {link_table_name}
                ON {link_table_name}.id = {table_name}.{el}
                ''')
            card_elem['Value'] = f'@{link_table_name}_name'  # Так как поле ссылочное - переименуем его как в запросе

        # Добавим поле в карточки
        cards['customcards']['layout']['Elements'][0]['Elements'][0]['Elements'].append(card_elem.copy())

    qtext = 'Select ' + ','.join(qfield_text) + f' FROM {table_name} ' + ' '.join(left_joins_list)
    #Если есть фильтры/отборы - добавим их в запрос
    if filter_value:
        conditions = [f"{field} LIKE '%{filter_value}%'" for field in filter_fields]
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