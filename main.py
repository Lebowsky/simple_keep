import db_services
from ru.travelfood.simple_ui import SimpleUtilites as suClass

import ui_barcodes
import ui_csv
import ui_global
import ui_form_data
import ui_form_data2 as ui_tables_structure
import ui_models
import socket
import json
import requests
import database_init_queryes
import os
from PIL import Image
from datetime import datetime
import importlib

import widgets
# from rs_settings import RSSettings
from java import jclass
import http_exchange
from requests.auth import HTTPBasicAuth
import ui_utils
from ui_utils import HashMap
from ru.travelfood.simple_ui import ImportUtils as iuClass
# from android.graphics.drawable import GradientDrawable as GradientDrawable
# from android.graphics import Color

noClass = jclass("ru.travelfood.simple_ui.NoSQL")
rs_settings = noClass("rs_settings")

importlib.reload(ui_csv)
importlib.reload(ui_global)
importlib.reload(ui_form_data)
importlib.reload(ui_tables_structure)
importlib.reload(database_init_queryes)
importlib.reload(http_exchange)
importlib.reload(ui_utils)
importlib.reload(db_services)
importlib.reload(widgets)
importlib.reload(ui_models)

# =============== Group Scan =================


def create_screen(hash_map):
    screen_params = {
        'hash_map': hash_map,
        'rs_settings': rs_settings
    }
    screen = ui_models.ScreensFactory.create_screen(**screen_params)
    if not screen:
        screen = ui_models.MockScreen(hash_map)

    return screen


@HashMap()
def tiles_on_start_group_scan(hash_map: HashMap):
    screen = create_screen(hash_map)
    screen.on_start()


@HashMap()
def tiles_on_input_group_scan(hash_map: HashMap):
    screen = create_screen(hash_map)
    screen.on_input()


@HashMap()
def docs_on_start_group_scan(hash_map: HashMap):
    screen = create_screen(hash_map)
    screen.on_start()


@HashMap()
def docs_on_select_group_scan(hash_map: HashMap):
    screen = create_screen(hash_map)
    screen.on_input()


@HashMap()
def doc_details_on_start_group_scan(hash_map: HashMap):
    screen = create_screen(hash_map)
    screen.on_start()


@HashMap()
def doc_details_listener_group_scan(hash_map: HashMap):
    screen = create_screen(hash_map)
    screen.on_input()


@HashMap()
def doc_details_barcode_scanned(hash_map: HashMap):
    if hash_map.get_bool('barcode_scanned'):
        doc = ui_global.Rs_doc
        doc.id_doc = hash_map.get('id_doc')

        answer = http_exchange.post_goods_to_server(doc.id_doc, get_http_settings(hash_map))

        if answer and answer.get('Error') is not None:
            hash_map.debug(answer.get('Error'))

        # doc_details_on_start_group_scan(hash_map)
        # hash_map.refresh_screen()

# ^^^^^^^^^^^^^^^^^ Group Scan ^^^^^^^^^^^^^^^^^

# -----
# 0100608940553886215,iPGSQpBt!&B
def settings_on_start(hashMap, _files=None, _data=None):
    # hashMap.put('toast','обновились')
    #app_on_start(hashMap)
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
    #res = ui_global.get_constants()
    #if res:
        # hashMap.put('use_series', str(res[1]))
        # hashMap.put('use_properties', str(res[2]))
    hashMap.put('use_mark', rs_settings.get('use_mark'))  #str(res[3]))
    hashMap.put('allow_fact_input', rs_settings.get('allow_fact_input'))  #str(res[3]))
    hashMap.put('add_if_not_in_plan',rs_settings.get('add_if_not_in_plan'))  # str(res[4]))
    hashMap.put('path',rs_settings.get('path') ) # str(res[5]))
    hashMap.put('delete_files',rs_settings.get('delete_files'))  # str(res[6]))
    hashMap.put('allow_overscan',rs_settings.get('allow_overscan'))  # str(res[9]))

    if not hashMap.containsKey('ip_host'):
        hashMap.put('ip_host', '192.168.1.77')

    return hashMap


def debug_on_start(hashMap, _files=None, _data=None):
    if not hashMap.containsKey('ip_host'):
        hashMap.put('ip_host', '192.168.1.77')
    return hashMap


    hashMap.put('use_mark', rs_settings.get('use_mark')) #str(res[3]))
    hashMap.put('add_if_not_in_plan', rs_settings.get('add_if_not_in_plan')) #str(res[4]))
    hashMap.put('path', rs_settings.get('path')) #str(res[5]))
    hashMap.put('delete_files', rs_settings.get('delete_files')) #str(res[6]))
    hashMap.put('allow_overscan', rs_settings.get('allow_overscan')) #str(res[9]))

def debug_listener(hashMap, _files=None, _data=None):
    delete_files = rs_settings.get('delete_files')
    if delete_files is None: delete_files = 'false'

    listener = hashMap.get('listener')

    if listener == 'btn_copy_base':
        ip_host = hashMap.get('ip_host')
        ip_host = '10.24.24.20'
        if os.path.isfile('//data/data/ru.travelfood.simple_ui/databases/SimpleKeep'): #Keep'):
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
        if not delete_files:
            delete_files = '0'
        if not path: path = '//storage/emulated/0/download/'

        ret_text = ui_csv.list_folder(path, delete_files)

        hashMap.put('toast', ret_text)
    return hashMap


def settings_on_click(hashMap, _files=None, _data=None):
    #Использовать маркировку
    use_mark = hashMap.get('use_mark')
    if use_mark is None: use_mark = 'false'

    path = hashMap.get('path')
    if path is None: path = '//storage/emulated/0/Android/data/ru.travelfood.simple_ui/'  # '//storage/emulated/0/download/'

    allow_fact_input = hashMap.get('allow_fact_input')
    if allow_fact_input is None: allow_fact_input = 'false'

    # ui_global.get_query_result('Update RS_docs SET control = ?',(allow_overscan,))  #В таблицы документов записываем новое значение контроля
    #ui_global.put_constants(
    rs_settings.put('use_mark',use_mark, True) #, path))
    rs_settings.put('path', path, True)
    rs_settings.put('allow_fact_input', allow_fact_input, True)  # , path))

    listener = hashMap.get('listener')

    if listener == 'btn_export':

        ui_csv.export_csv(path, hashMap.get('ip_adr'), hashMap.get('ANDROID_ID'))
        hashMap.put('toast', 'Данные выгружены')

    elif listener == 'ON_BACK_PRESSED':

        hashMap.put('FinishProcess', '')

    # elif listener == 'btn_files_list':
    #     hashMap.put('ShowScreen', 'СписокФайлов')
    elif listener == 'btn_conf_version':
        conf = json.loads(hashMap.get('_configuration '))

    elif listener == 'btn_size':
        hashMap.put('ShowScreen', 'Настройки Шрифтов')
    elif listener == 'btn_test_barcode':
        hashMap.put('ShowScreen', 'Тест сканера')
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
        qtext = '''SELECT id_doc FROM RS_docs WHERE verified = '1'
                    UNION
                    SELECT id_doc FROM RS_adr_docs WHERE verified = '1' '''
        res = ui_global.get_query_result(qtext, None, True)

        if res:
            doc_list = []
            for el in res:
                doc_list.append('"' + el['id_doc'] + '"')
            doc_in_str = ','.join(doc_list)
            # htpparams = {'username':hashMap.get('onlineUser'), 'password':hashMap.get('onlinePass'), 'url':url}
            answer = http_exchange.post_changes_to_server(doc_in_str, url)
            if answer.get('Error') is not None:
                ui_global.write_error_on_log(str(answer.get('Error')))

            qtext = f'UPDATE RS_docs SET sent = 1  WHERE id_doc in ({doc_in_str}) '
            ui_global.get_query_result(qtext, (doc_in_str,), False)
    elif listener == 'btn_timer':
        try:
            timer_update(hashMap)
        except Exception as e:
            hashMap.put('toast',str(e))
    elif listener == 'btn_sound_settings':
        hashMap.put('ShowScreen','Настройка звука')
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


def refill_docs_list_new(_filter=''):
    query_text = ui_form_data.get_doc_query(_filter)

    if _filter == '' or _filter == 'Все':
        results = ui_global.get_query_result(query_text, return_dict=True)
    else:
        results = ui_global.get_query_result(query_text, (_filter,), return_dict=True)

    table_data = []

    for record in results:
        table_data.append({
            'key': record['id_doc'],
            'type': record['doc_type'],
            'number': record['doc_n'],
            'data': record['doc_date'],
            'warehouse': record['RS_warehouse'],
            'countragent': record['RS_countragent'],
            'add_mark_selection': record['add_mark_selection']
        })

    return ui_form_data.get_doc_card_new(rs_settings, table_data)


def docs_on_start(hashMap, _files=None, _data=None):
    # Заполним поле фильтра по виду документов
    hashMap.put("SetTitle", "Документы")
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

    if hashMap.get('doc_goods_table'):
        hashMap.put("doc_goods_table", None)

    if hashMap.get("warehouse"):
        hashMap.put("Show_warehouse", "1")
    else:
        hashMap.put("Show_warehouse", "-1")
    if hashMap.get("countragent"):
        hashMap.put("Show_countragent", "1")
    else:
        hashMap.put("Show_countragent", "-1")

    if rs_settings.get('allow_fact_input') == 'true':
        hashMap.put("Show_fact_qtty_input", "1")
        hashMap.put("Show_fact_qtty_note", "-1")
    else:
        hashMap.put("Show_fact_qtty_input", "-1")
        hashMap.put("Show_fact_qtty_note", "1")


    hashMap.put('SetTitle', hashMap.get("doc_type"))

    id_doc = hashMap.get('id_doc')
    falseValueList = (0,'0','false','False',None)
    # Формируем таблицу карточек и запрос к базе
    #res = ui_global.get_constants()
    use_series = rs_settings.get('use_series') #res[1]
    use_properties = rs_settings.get('use_series') #res[2]
    hashMap.put('use_properties', rs_settings.get('use_series')) #res[2])
    doc_detail_list = ui_form_data.get_doc_detail_cards(use_series, use_properties,rs_settings)
    doc_detail_list['customcards']['cardsdata'] = []

    if hashMap.get('view') == "cards":
        hashMap.put('Show_card_view', "-1")
        # doc_detail_list = ui_form_data.get_doc_detail_cards(use_series, use_properties, rs_settings)
        doc_detail_list = ui_tables_structure.get_doc_detail_cards_mod(use_series, use_properties, rs_settings)

        doc_detail_list['customcards']['cardsdata'] = []
    else:
        hashMap.put('Show_table_view', "-1")
        doc_detail_list = ui_tables_structure.get_doc_detail_table_head()
        doc_detail_list["customtable"]["tabledata"] = [{}]

    jlist = json.loads(hashMap.get('docCards'))

    elem_n = jlist['customcards']['cardsdata']

    for el in elem_n:
        if el['key'] == id_doc:
            hashMap.put('add_mark_selection',
                        str(el['add_mark_selection'] if el['add_mark_selection'] else '0'))
    #    current_elem = jlist['customcards']['cardsdata'][int(current_str)-1]

    query_text = ui_form_data.get_doc_details_query()

    results = ui_global.get_query_result(query_text, (id_doc,), True)
    row_filter = True if hashMap.get('rows_filter') == '1' else False
    if results:
        hashMap.put('id_doc', str(results[0]['id_doc']))
        for record in results:
            pic = '#f02a' if record['IsDone'] != 0 else '#f00c'
            if record['qtty'] == 0 and record['qtty_plan'] == 0:
                pic = ''
            if row_filter and record['qtty'] == record['qtty_plan']:
                continue
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
                'code_art': str(record['code']),
                'art': str(record['art']),
                'qtty': str(record['qtty'] if record['qtty'] is not None else 0),
                'qtty_plan': str(record['qtty_plan'] if record['qtty_plan'] is not None else 0),
                'price': str(record['price'] if record['price'] is not None else 0),
                'price_name': str(record['price_name']),
                'picture': pic
            }

            good_info = ""
            if product_row['art'] != "None":
                good_info += product_row['art']
            if product_row['properties_name'] != "None":
                good_info += "(" + product_row['properties_name'] + ")"
            if product_row['series_name'] != "None":
                good_info += product_row['series_name']
            if product_row['units_name'] != "None":
                good_info += ", " + product_row['units_name']
            product_row['good_info'] = good_info

            if hashMap.get('view') == "cards":
                doc_detail_list['customcards']['cardsdata'].append(product_row)
            else:
                product_row['_layout'] = ui_tables_structure.get_doc_detail_table_body_layout(use_series, use_properties, rs_settings)

                if float(product_row['qtty_plan']) > float(product_row['qtty']):
                    product_row['_layout']["BackgroundColor"] = "#FBE9E7"

                if hashMap.get("added_goods"):
                    added_goods_dict = json.loads(hashMap.get("added_goods"))
                    if str(results[0]['id_doc']) in added_goods_dict.keys():
                        if str(record['id_good']) in added_goods_dict[str(results[0]['id_doc'])][0]:
                            if str(record['id_properties']) in added_goods_dict[str(results[0]['id_doc'])][1] or not str(record['id_properties']):
                                product_row['_layout']["BackgroundColor"] = "#F0F8FF"

                if float(product_row['qtty_plan']) == float(product_row['qtty']):
                    product_row['_layout']["BackgroundColor"] = "#FFFFFF"

                if float(product_row['qtty_plan']) < float(product_row['qtty']):
                    product_row['_layout']["BackgroundColor"] = "#FFF9C4"

                doc_detail_list['customtable']['tabledata'].append(product_row)

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

        hashMap.put("table_lines_qtty", str(len(results)))
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
    if hashMap.get("view") == "cards":
        hashMap.put("doc_goods_cards", json.dumps(doc_detail_list))
    else:
        hashMap.put("doc_goods_table", json.dumps(doc_detail_list))

    return hashMap


def highlight_added_good(hashMap, barcode):

    good_query = ui_global.get_query_result("SELECT id_good,id_property FROM RS_barcodes where barcode = '" +
                                               barcode + "'")
    id_doc = hashMap.get('id_doc')

    if len(good_query) > 0:
        good_id = good_query[0][0]
        good_property_id = good_query[0][1]

        if hashMap.get("added_goods"):
            added_goods_dict = json.loads(hashMap.get("added_goods"))
            if id_doc in added_goods_dict.keys():
                if good_id not in added_goods_dict[id_doc][0]:
                    added_goods_dict[id_doc][0].append(good_id)
                if good_property_id:
                    if good_property_id not in added_goods_dict[id_doc][1]:
                        added_goods_dict[id_doc][1].append(good_property_id)

            else:
                added_goods_dict[id_doc] = [[good_id], [good_property_id]]

        else:
            added_goods_dict = {id_doc: [[good_id], [good_property_id]]}
        hashMap.put("added_goods", str(added_goods_dict).replace("'", '"'))

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


def doc_details_on_load(hashMap, _files=None, _data=None):

    barcode_btn = iuClass.getView("btn_barcodes")
    shape_2 = GradientDrawable()  # Создаем форму
    shape_2.setShape(GradientDrawable.RECTANGLE)
    shape_2.setCornerRadius(50)
    shape_2.setColor(Color.WHITE)
    barcode_btn.setBackground(shape_2)
    barcode_btn.setElevation(15)
    return hashMap


def doc_adr_details_on_start(hashMap, _files=None, _data=None):
    id_doc = hashMap.get('id_doc')
    current_cell = hashMap.get('current_cell_id')

    falseValueList = (0,'0','false','False',None)
    # Формируем таблицу карточек и запрос к базе
    use_series = rs_settings.get('use_series')  #res[1]
    use_properties = rs_settings.get('use_properties')#res[2]
    hashMap.put('use_properties', use_properties)
    #doc_detail_list = ui_form_data.get_doc_detail_cards(use_series, use_properties,rs_settings, True)

    doc_detail_list = widgets.CustomCards(
                      widgets.LinearLayout(widgets.TextView(Value='@good_name', TextSize= rs_settings.get('GoodsCardTitleTextSize'), TextBold = True, weight = 1),
                             widgets.PopupMenuButton(Value = "Удалить строку"),
                             widgets.LinearLayout(
                                 widgets.TextView(TextBold = True, weight = 1, Value='@code_art'),
                                 widgets.TextView(TextBold = False, weight = 1, Value = '@art'),
                                 orientation="horizontal"),
                                 widgets.LinearLayout(
                                     widgets.TextView(Value = 'План', TextSize = rs_settings.get('goodsTextSize')),
                                     widgets.TextView(Value='@qtty_plan'),
                                     widgets.TextView(Value='Факт'),
                                     widgets.TextView(Value='@qtty'),
                                     #widgets.TextView(Value = '@'),
                                     widgets.TextView(Value = 'Цена'),
                                     widgets.TextView(Value = '@price'),
                                     widgets.TextView(Value = '@picture'),
                                 orientation="horizontal"),orientation="vertical"),options = widgets.Options())

    #doc_detail_list['customcards']['cardsdata'] = []

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
        params = {'id_doc':id_doc, 'table_type':table_type_filter, 'EmptyString':'', 'NullValue':'<пустое значение>'}

    results = ui_global.get_query_result(query_text, params, True)
    row_filter = True if hashMap.get('rows_filter') == '1' else False

    if results:
        hashMap.put('id_doc', str(results[0]['id_doc']))
        current_cell =''
        for record in results:
            if row_filter and record['qtty'] == record['qtty_plan']:
                continue
            pic = '#f02a' if record['IsDone'] != 0 else '#f00c'
            if record['qtty'] == 0 and record['qtty_plan'] == 0:
                pic = ''

            if current_cell != record['cell_name']:
                c = {"group": record['cell_name']}
                #doc_detail_list['customcards']['cardsdata'].append(c)
                doc_detail_list.customcards['cardsdata'].append(c)
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

#            doc_detail_list['customcards']['cardsdata'].append(product_row)
            doc_detail_list.customcards['cardsdata'].append(product_row)

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
    #    hashMap.put("doc_goods", json.dumps(doc_detail_list))
    hashMap.put("doc_goods", doc_detail_list.to_json())

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

        hashMap.put("ShowScreen", "Товар выбор")

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
            hashMap.put('beep_duration ', rs_settings.get('beep_duration'))
            hashMap.put("beep", rs_settings.get('signal_num'))
            hashMap.put('toast', 'Не найдена ячейка')
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
                                      , eval(have_qtty_plan), eval(have_zero_plan), eval(control),  hashMap.get('current_cell_id'))
        if res == None:
            hashMap.put('scanned_barcode', barcode)
            # suClass.urovo_set_lock_trigger(True)
            hashMap.put('ShowScreen', 'Ошибка сканера')
            # hashMap.put('toast',
            #             'Штрих код не зарегистрирован в базе данных. Проверьте товар или выполните обмен данными')
        elif res['Error']:
            hashMap.put('beep_duration ', rs_settings.get('beep_duration'))
            hashMap.put("beep", rs_settings.get('signal_num'))
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
        hashMap.remove('SearchString')
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
        # current_str = int(hashMap.get("selected_card_position"))
        # jlist = json.loads(hashMap.get("doc_goods"))
        # current_elem = jlist['customcards']['cardsdata'][current_str]
        # if current_elem.get('group'):
        #     current_elem = jlist['customcards']['cardsdata'][current_str+1]
        #
        current_key = hashMap.get("key")
        if layout_listener == 'Удалить строку':

            if current_key: #current_elem['key']:
                ui_global.get_query_result('DELETE FROM RS_adr_docs_table WHERE id = ?', (current_key, )) #current_elem['key'],))
                hashMap.put('RefreshScreen','')
        elif layout_listener == 'Изменить ячейку':

            hashMap.remove('SearchString')
            hashMap.put('table_for_select', 'RS_cells')  # Таблица для выбора значения
            hashMap.put('SetResultListener', 'select_cell_value_for_card')
            hashMap.put('filter_fields', 'name;barcode')
            hashMap.put('ShowProcessResult', 'Универсальный справочник|Справочник')

    elif listener == 'select_cell_value_for_card':
        current_key = hashMap.get("key")
        if current_key:
            ui_global.get_query_result('Update RS_adr_docs_table SET id_cell = ? Where id = ?', (hashMap.get('current_id'), current_key))
            hashMap.put('RefreshScreen','')

    elif listener == 'btn_add_string':

        hashMap.put("Doc_data",
                    hashMap.get('doc_type') + ' №' + hashMap.get('doc_n') +
                    ' от' + hashMap.get('doc_date'))
        hashMap.put("Good", '')
        hashMap.put("properties", '')
        hashMap.put("qtty_plan", '')

        hashMap.put("ShowScreen", "Товар")

    elif listener == 'btn_rows_filter_on':
        hashMap.put('rows_filter', '1')
        hashMap.put('RefreshScreen','')
    elif listener == 'btn_rows_filter_off':
        hashMap.remove('rows_filter')
        hashMap.put('RefreshScreen','')

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


def docs_on_select(hashMap, _files=None, _data=None):
    listener = hashMap.get("listener")

    if listener == "CardsClick":
        # Находим ID документа
        current_str = hashMap.get("selected_card_position")
        jlist = json.loads(hashMap.get("docCards"))
        cards_data = jlist['customcards']['cardsdata']
        for element in cards_data:
            if "key" in element:
                if element["key"] == hashMap.get("selected_card_key"):
                    current_doc = element
        # current_doc = jlist['customcards']['cardsdata'][int(current_str)]

        # id_doc = current_doc['key']
        hashMap.put('id_doc', current_doc['key'])
        hashMap.put('doc_type', current_doc['type'])
        hashMap.put('doc_n', current_doc['number'])
        hashMap.put('doc_date', ui_utils.format_doc_date(current_doc['data']))
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


@HashMap()
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
        current_elem = get_current_elem_doc_goods(hashMap, current_str)

        if 'good_name' in current_elem:  # в таблице первая карточка - заголовок таблицы без полей

            hashMap.put("Doc_data",
                        hashMap.get('doc_type') + ' №' + hashMap.get('doc_n') +
                        ' от ' + hashMap.get('doc_date'))
            hashMap.put("Good", current_elem['good_name'])
            hashMap.put('good_art', str(current_elem['art']))
            hashMap.put('good_sn', str(current_elem['series_name']))
            hashMap.put('good_property', str(current_elem['properties_name']))
            hashMap.put('good_price', str(current_elem['price']))
            hashMap.put('good_unit', str(current_elem['units_name']))
            hashMap.put('good_str', str(current_str) + "/" + hashMap.get('table_lines_qtty'))

            fill_empty_values(hashMap, {'good_art': str(current_elem['art']),
                                        'good_sn': str(current_elem['series_name']),
                                        'good_property': str(current_elem['properties_name']),
                                        'good_price': str(current_elem['price']),
                                        'good_plan': str(current_elem['qtty_plan'])}, value="отсутствует")

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

            hashMap.put("ShowScreen", "Товар выбор")

    elif listener == 'btn_add_string':

        hashMap.put("Doc_data",
                    hashMap.get('doc_type') + ' №' + hashMap.get('doc_n') +
                    ' от ' + hashMap.get('doc_date'))
        hashMap.put("Good", '')
        hashMap.put("properties", '')
        hashMap.put("qtty_plan", '')

        hashMap.put("ShowScreen", "Товар")

    elif listener == "BACK_BUTTON":
        hashMap.put("ShowScreen", "Документы")
    elif listener == "btn_barcodes":
        hashMap.show_dialog('ВвестиШтрихкод')

    elif listener == 'confirm_verified' and hashMap.get("event") == "onResultPositive":
        doc = ui_global.Rs_doc()
        doc.id_doc = hashMap.get('id_doc')
        doc.mark_verified(1)
        hashMap.put("ShowScreen", "Документы")

    elif listener == 'barcode' or (listener == 'ВвестиШтрихкод' and hashMap.get("event") == "onResultPositive"):
        doc = ui_global.Rs_doc
        doc.id_doc = hashMap.get('id_doc')
        if hashMap.get("event") == "onResultPositive":
            barcode = hashMap.get('fld_barcode')
            if not barcode.strip():
                hashMap.put("ShowDialog", "ВвестиШтрихкод")
                return hashMap
        else:
            barcode = hashMap.get('barcode_camera')

        have_qtty_plan = hashMap.get('have_qtty_plan')
        have_zero_plan = hashMap.get('have_zero_plan')
        have_mark_plan = hashMap.get('have_mark_plan')
        control = hashMap.get('control')

        res = doc.process_the_barcode(
            doc,
            barcode,
            eval(have_qtty_plan),
            eval(have_zero_plan),
            eval(control),
            eval(have_mark_plan),
            rs_settings.get('use_mark'),
            user_tmz=int(hashMap.get("TMZ"))
        )
        if res is None:
            hashMap.put('scanned_barcode', barcode)
            # suClass.urovo_set_lock_trigger(True)
            hashMap.put('ShowScreen', 'Ошибка сканера')
            # hashMap.put('toast',
            #             'Штрих код не зарегистрирован в базе данных. Проверьте товар или выполните обмен данными')
        elif res['Error']:
            hashMap.put('beep_duration ', rs_settings.get('beep_duration'))
            hashMap.put("beep", rs_settings.get('signal_num'))
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
            highlight_added_good(hashMap, barcode)
            hashMap.put('toast', 'Товар добавлен в документ')
            hashMap.put('barcode_scanned', 'true')

    elif listener == 'btn_doc_mark_verified':
        hashMap.show_dialog('confirm_verified', 'Завершить документ?', ['Да', 'Нет'])

    elif listener == 'ON_BACK_PRESSED':
        hashMap.put("ShowScreen", "Документы")
    elif listener == 'LayoutAction':
        layout_listener = hashMap.get('layout_listener')
        if layout_listener == 'Удалить строку':
            current_elem = json.loads(hashMap.get("card_data"))
            id_str = current_elem['key']
            qtext = 'DELETE FROM RS_docs_table WHERE id=?'
            ui_global.get_query_result(qtext, (id_str,))
    elif listener == 'btn_rows_filter_on':
        hashMap.put('rows_filter', '1')
        hashMap.put('RefreshScreen','')
    elif listener == 'btn_rows_filter_off':
        hashMap.remove('rows_filter')
        hashMap.put('RefreshScreen','')
    elif listener == 'card_view':
        hashMap.put('view', 'cards')
        hashMap.put('doc_goods_table', '')
        hashMap.put("Show_card_view", "-1")
        hashMap.put('RefreshScreen', '')
    elif listener == 'table_view':
        hashMap.put('view', 'table')
        hashMap.put('doc_goods_cards', '')
        hashMap.put("Show_table_view", "-1")
        hashMap.put('RefreshScreen', '')

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


def adr_elem_on_start(hashMap, _files=None, _data=None):
    hashMap.put('mm_local', '')
    return hashMap

def elem_on_start(hashMap, _files=None, _data=None):
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


def adr_elem_viev_on_start(hashMap, _files=None, _data=None):
    hashMap.put('mm_local', '')
    return hashMap

def elem_viev_on_start(hashMap, _files=None, _data=None):
    hashMap.put('mm_local', '')
    return hashMap


def adr_elem_viev_on_click(hashMap, _files=None, _data=None):
    listener = hashMap.get("listener")

    if listener == "btn_ok":
        # получим текущую строку документа
        current_str = hashMap.get("selected_card_position")
        doc = ui_global.Rs_adr_doc
        if not current_str == '0':
            current_elem = get_current_elem_doc_goods(hashMap, current_str)
            key = int(current_elem['key'])
            doc.id_str = int(current_elem['key'])
        # ... и запишем ее в базу
        qtty = hashMap.get('qtty')
        doc.qtty = float(qtty) if qtty else 0

        doc.update_doc_str(doc) #(doc, )
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


def elem_viev_on_click(hashMap, _files=None, _data=None):
    listener = hashMap.get("listener")

    if listener == "btn_ok":
        # получим текущую строку документа
        current_str = hashMap.get("selected_card_position")
        #Если строка не существует, создадим ее
        doc = ui_global.Rs_doc
        doc.id_doc = hashMap.get('id_doc')
        # if current_str =='0':
        #     pass
            #jlist['customcards']['cardsdata']
        #else:
        current_elem = get_current_elem_doc_goods(hashMap, current_str)
        doc.id_str = int(current_elem['key'])
        # ... и запишем ее в базу

        qtty = hashMap.get('qtty')
        doc.qtty = float(qtty) if qtty else 0

        doc.update_doc_str(doc, hashMap.get('price'))  # (doc, )

        remove_added_good_highlight(hashMap, str(current_elem['id_good']), str(current_elem['id_properties']))

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


def prices_on_start(hashMap, _files=None, _data=None):
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


def prices_on_input(hashMap, _files=None, _data=None):
    if hashMap.get('listener') == "get_prices_btn":
        get_prices(hashMap)
    if hashMap.get('listener') == "price_type_select":
        hashMap.put("ShowScreen", 'Выбор типа цены')
    if hashMap.get('listener') == "property_select":
        get_good_by_art(hashMap)
        if hashMap.get('input_good_id'):
            hashMap.put("ShowScreen", 'Выбор характеристик')
    if hashMap.get('listener') == "unit_select":
        get_good_by_art(hashMap)
        if hashMap.get('input_good_id'):
            hashMap.put("ShowScreen", 'Выбор упаковки')
    if hashMap.get('listener') == "barcode":
        identify_barcode_prices(hashMap)
    if hashMap.get('listener') == "ON_BACK_PRESSED":
        kill_price_tables(hashMap)
        if hashMap.get('return_to_good_card'):
            hashMap.put("FinishProcessResult", "")
        else:
            hashMap.put("FinishProcess", "")
    return hashMap


def price_types_on_input(hashMap, _files=None, _data=None):

    if hashMap.get('listener') == 'CardsClick':
        selected_price_type_id = hashMap.get("selected_card_key")
        selected_price_type_name = ui_global.get_query_result("SELECT name FROM RS_price_types where id = '" +
                                                              selected_price_type_id + "'")
        hashMap.put('selected_price_type_id', str(selected_price_type_id))
        hashMap.put("price_type_select", str(selected_price_type_name[0]).split("'")[1])
        hashMap.put("BackScreen", "")
        return hashMap

    if hashMap.get('listener') == 'back_to_prices' or 'ON_BACK_PRESSED':
        back_to_prices(hashMap)
    return hashMap


def properties_on_input(hashMap, _files=None, _data=None):
    if hashMap.get('listener') == 'CardsClick':
        selected_property_id = hashMap.get("selected_card_key")
        selected_property_name = ui_global.get_query_result("SELECT name FROM RS_properties where id = '" +
                                                            selected_property_id + "'")

        hashMap.put('selected_property_id', str(selected_property_id))
        hashMap.put("property_select", str(selected_property_name[0]).split("'")[1])
        hashMap.put("BackScreen", "")
        return hashMap
    if hashMap.get('listener') == 'back_to_prices' or 'ON_BACK_PRESSED':
        back_to_prices(hashMap)

    return hashMap


def units_on_input(hashMap, _files=None, _data=None):
    if hashMap.get('listener') == 'CardsClick':
        selected_unit_id = hashMap.get("selected_card_key")
        selected_unit_name = ui_global.get_query_result("SELECT name FROM RS_units where id = '" +
                                                        selected_unit_id + "'")
        hashMap.put('selected_unit_id', str(selected_unit_id))
        hashMap.put("unit_select", str(selected_unit_name[0]).split("'")[1])
        hashMap.put("BackScreen", "")
        return hashMap
    if hashMap.get('listener') == 'back_to_prices' or 'ON_BACK_PRESSED':
        back_to_prices(hashMap)
    return hashMap


def prices_tables_on_input(hashMap, _files=None, _data=None):
    if hashMap.get('listener') == 'show_filters':
        hashMap.put("ShowScreen", "Проверка цен")

    if hashMap.get('listener') == 'ON_BACK_PRESSED':
        if not hashMap.get("return_to_good_card"):
            hashMap.put('property_id', '')
            hashMap.put('barcode', '')

        if hashMap.get("return_to_good_card"):
            hashMap.put("BackScreen", '')
        else:
            hashMap.put('selected_good_id', '')

            if hashMap.get("current_screen_name") == "Таблица остатков":
                kill_remains_tables(hashMap)
                hashMap.put('ShowScreen', 'Проверить остатки')
            elif hashMap.get("current_screen_name") == "Таблица цен":
                kill_price_tables(hashMap)
                hashMap.put('ShowScreen', 'Проверка цен')
    if hashMap.get('listener') == 'barcode':
        identify_barcode_prices(hashMap)

    return hashMap


def identify_barcode_prices(hashMap, _files=None, _data=None):
    if hashMap.get('barcode'):
        hashMap.put('barcode_info', str(hashMap.get('barcode')))
        hashMap.put('property_select', '')
        hashMap.put('selected_property_id', '')

        barcode = hashMap.get('barcode')
        barcode_good_query = ui_global.get_query_result(
            "SELECT id_good,id_property FROM RS_barcodes where barcode = '" + barcode + "'")

        if barcode_good_query[0][0]:
            good_id = barcode_good_query[0][0]
            hashMap.put('input_good_id', barcode_good_query[0][0])

            if len(good_id) > 0:
                good_query = ui_global.get_query_result(
                    "SELECT name,art,type_good FROM RS_goods where id = '" + good_id + "'")

                if good_query[0][0]:
                    hashMap.put('prices_object_name', good_query[0][0])
                if good_query[0][1]:
                    hashMap.put('input_good_art', good_query[0][1])
                if good_query[0][2]:
                    hashMap.put('good_type_id', good_query[0][2])
                hashMap.put('prices_error_msg', "")

        if barcode_good_query[0][1]:
            hashMap.put('property_id', barcode_good_query[0][1])
        else:
            hashMap.put('prices_error_msg', "Штрихкод не распознан")
    get_prices(hashMap)


def back_to_prices(hashMap, _files=None, _data=None):
    if hashMap.get('current_screen_name') == "Выбор типа цены":
        hashMap.put('selected_price_type_id', '')
        hashMap.put('selected_price_type_name', '')
        hashMap.put('price_type_select', '')

    if hashMap.get('current_screen_name') == "Выбор характеристик":
        hashMap.put('selected_property_id', '')
        hashMap.put('selected_property_name', '')
        hashMap.put("property_select", '')

    if hashMap.get('current_screen_name') == "Выбор упаковки":
        hashMap.put('selected_unit_id', "")
        hashMap.put('selected_unit_name', '')
        hashMap.put("unit_select", "")
    hashMap.put("BackScreen", "")
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
        if not type or type=='Все':
            hashMap.put('toast','Укажите тип документа')
            return hashMap

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
    if rs_settings.get('TitleTextSize') is None:
        rs_settings.put("TitleTextSize", "18", True)
    if rs_settings.get('titleDocTypeCardTextSize') is None:
        rs_settings.put("titleDocTypeCardTextSize", "18", True)
    if rs_settings.get('CardTitleTextSize') is None:
        rs_settings.put("CardTitleTextSize", "20", True)
    if rs_settings.get('CardDateTextSize') is None:
        rs_settings.put("CardDateTextSize", "10", True)
    if rs_settings.get('CardTextSize') is None:
        rs_settings.put("CardTextSize", "15", True)
    if rs_settings.get('GoodsCardTitleTextSize') is None:
        rs_settings.put("GoodsCardTitleTextSize", "18", True)
    if rs_settings.get('goodsTextSize') is None:
        rs_settings.put("goodsTextSize", "18", True)
    if rs_settings.get('SeriesPropertiesTextSize') is None:
        rs_settings.put("SeriesPropertiesTextSize", "16", True)
    if rs_settings.get('DocTypeCardTextSize') is None:
        rs_settings.put("DocTypeCardTextSize", "15", True)
    if rs_settings.get('signal_num') is None:
        rs_settings.put('signal_num', '83', True)
    if rs_settings.get('beep_duration') is None:
        rs_settings.put('beep_duration', '1000', True)
    if rs_settings.get('use_mark')  is None:
        rs_settings.put('use_mark', 'false', True)
    if rs_settings.get('add_if_not_in_plan')  is None:
        rs_settings.put('add_if_not_in_plan', 'false', True)
    if rs_settings.get('path')  is None:
        rs_settings.put('path', '', True)
    if rs_settings.get('delete_files')  is None:
        rs_settings.put('delete_files', 'false', True)
    if rs_settings.get('allow_overscan')  is None:
        rs_settings.put('allow_overscan', 'false', True)


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


def font_size_settings_listener(hashMap, _files=None, _data=None):
    listener = hashMap.get('listener')
    if listener == 'btn_on_save':  # or hashMap.get('event')=='Input'

        rs_settings.put("TitleTextSize", hashMap.get("TitleTextSize"), True)
        rs_settings.put("CardTitleTextSize", hashMap.get("CardTitleTextSize"), True)
        rs_settings.put("CardTextSize", hashMap.get("CardTextSize"), True)
        rs_settings.put("CardDateTextSize", hashMap.get("CardDateTextSize"), True)
        rs_settings.put("GoodsCardTitleTextSize", hashMap.get("GoodsCardTitleTextSize"), True)
        rs_settings.put("goodsTextSize", hashMap.get("goodsTextSize"), True)
        rs_settings.put("SeriesPropertiesTextSize", hashMap.get("SeriesPropertiesTextSize"), True)
        rs_settings.put("DocTypeCardTextSize", hashMap.get("DocTypeCardTextSize"), True)
        rs_settings.put("titleDocTypeCardTextSize", hashMap.get("titleDocTypeCardTextSize"), True)
        hashMap.put('ShowScreen', 'Настройки и обмен')
        #params.put("signal_num", hashMap.get("signal_num"), True)
    elif listener == 'btn_on_cancel' or listener == 'ON_BACK_PRESSED':
        hashMap.put('ShowScreen', 'Настройки и обмен')

    return hashMap


def font_sizes_on_start(hashMap, _files=None, _data=None):

    # Словарик названий и имен размеров шрифтов
    ss = {
        'TitleTextSize': 'Размер заголовка',
        'CardTitleTextSize': 'Размер заголовка карточки',
        "CardDateTextSize": 'Данные карточки',
        'CardTextSize':'Размер текста элементов',
        'GoodsCardTitleTextSize': 'Заголовок товара',
        'goodsTextSize': 'Товар',
        'SeriesPropertiesTextSize': 'Серии свойства',
        'DocTypeCardTextSize': 'Тип документа',
        'titleDocTypeCardTextSize':'Название документа в карточке'}  #,       'signal_num': "Номер сигнала"

    hashMap.put('TitleTextSize',  ui_form_data.ModernField(hint='Размер заголовка', default_text=rs_settings.get('TitleTextSize'), password=False).to_json()) #  )
    hashMap.put('CardTitleTextSize',
                ui_form_data.ModernField(hint='Размер заголовка карточки', default_text=rs_settings.get('CardTitleTextSize'),
                                         password=False).to_json())  # )
    #"CardDateTextSize": 'Данные карточки',
    hashMap.put('CardDateTextSize',
                ui_form_data.ModernField(hint='Данные карточки', default_text=rs_settings.get('CardDateTextSize'),
                                         password=False).to_json())  # )
    #'CardTextSize':'Размер текста элементов',
    hashMap.put('CardTextSize',
                ui_form_data.ModernField(hint='Размер текста элементов', default_text=rs_settings.get('CardTextSize'),
                                         password=False).to_json())  # )
    #'GoodsCardTitleTextSize': 'Заголовок товара',
    hashMap.put('GoodsCardTitleTextSize',
                ui_form_data.ModernField(hint='Заголовок товара', default_text=rs_settings.get('GoodsCardTitleTextSize'),
                                         password=False).to_json())  # )
    #'goodsTextSize': 'Товар',
    hashMap.put('goodsTextSize',
                ui_form_data.ModernField(hint='Товар', default_text=rs_settings.get('goodsTextSize'),
                                         password=False).to_json())  # )
    #'SeriesPropertiesTextSize': 'Серии свойства',
    hashMap.put('SeriesPropertiesTextSize',
                ui_form_data.ModernField(hint='Серии свойства', default_text=rs_settings.get('SeriesPropertiesTextSize'),
                                         password=False).to_json())  # )
    #'DocTypeCardTextSize': 'Тип документа',
    hashMap.put('DocTypeCardTextSize',
                ui_form_data.ModernField(hint='Тип документа', default_text=rs_settings.get('DocTypeCardTextSize'),
                                         password=False).to_json())  # )
    #'titleDocTypeCardTextSize':'Название документа в карточке'
    hashMap.put('titleDocTypeCardTextSize',
                ui_form_data.ModernField(hint='Название документа в карточке', default_text=rs_settings.get('titleDocTypeCardTextSize'),
                                         password=False).to_json())  # )

    return hashMap


def sound_settings_on_start(hashMap, _files=None, _data=None):
    # ss = {'signal_num': "Номер сигнала",
    #       'beep_duration':'Длительность(мс)'}  # ,

    hashMap.put('signal_num_card',
                ui_form_data.ModernField(hint='Номер сигнала', default_text=rs_settings.get('signal_num'),
                                         password=False).to_json())  # )
    hashMap.put('beep_duration_card',
                ui_form_data.ModernField(hint='Длительность(мс)', default_text=rs_settings.get('beep_duration'),
                                         password=False).to_json())  # )
    #fields_from_settings(hashMap, ss)

    return hashMap

def sound_settings_listener(hashMap, _files=None, _data=None):
    listener = hashMap.get('listener')
    if listener == 'btn_on_save':  # or hashMap.get('event') == 'Input'

        rs_settings.put('signal_num', hashMap.get("signal_num_value"), True)
        rs_settings.put('beep_duration', hashMap.get('beep_duration_value'), True)
        hashMap.put('ShowScreen', 'Настройки и обмен')

    elif listener == 'btn_on_cancel' or listener == 'ON_BACK_PRESSED':
        hashMap.put('ShowScreen', 'Настройки и обмен')
    elif listener == 'btn_test_sound':
        rs_settings.put('signal_num', hashMap.get("signal_num_value"), True)
        rs_settings.put('beep_duration', hashMap.get('beep_duration_value'), True)
        hashMap.put('beep_duration', hashMap.get("beep_duration_value"))
        hashMap.put('beep', hashMap.get('signal_num_value'))

        # hashMap.put('beep_duration', str(rs_settings.get('beep_duration')))
        # hashMap.put("beep", str(rs_settings.get('signal_num')))

        # hashMap.put('beep_duration', '83')
        # hashMap.put("beep", '1000')

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

    # hashMap.put('toast', 'Обмен') #url)
    result = http_exchange.timer_server_load_data(url)
    # if result.get('Error'):
    #     hashMap.put('error_log', )


    # try:
    #     result = http_exchange.server_load_data(url)
    # except:
    #     raise 'Ошибка запроса к HTTP'
    # if result['status_code'] ==200:
    #     if result.get('batch') is not None:
    #         rs_settings.put('batch', result.get('batch'),True)
    #         rs_settings.put('number_of_received','0', True)
    #
    #     if result.get('res_for_sql') is not None:
    #
    #         if rs_settings.get('batch') is not None:  #Мы выполняем пакет загрузки, данные разбиты на несколько файлов, их количество в batch
    #             number_of_received = 0 if rs_settings.get('number_of_received')== 'not found' else int(rs_settings.get('number_of_received'))
    #             total_received = int(rs_settings.get('batch'))
    #             number_of_received =+1
    #         else:
    #             total_received = None
    #
    #         sql_error = False
    #         error_pool = []
    #         for key in result['res_for_sql']:
    #             try:
    #                 ui_global.get_query_result(key)
    #                 # return 'ok'
    #             except Exception as e:
    #                 sql_error = True
    #                 error_pool.append(e.args[0])
    #
    #
    #         if total_received:
    #             hashMap.put('toast', 'Идет загрузка большого объема данных. Получено '+ str(number_of_received*50000) + 'из, примерно '+ str(total_received*50000))
    #             rs_settings.put('number_of_received',str(number_of_received), True)
    #
    #         if sql_error:
    #             rs_settings.put('error_log', str(error_pool), True)
    #             hashMap.put('toast', 'При загрузке были ошибки. Проверьте их в настройках (кнопка посмотреть ошибки)')
    #     if hashMap.get('current_screen_name') == 'Документы':
    #         hashMap.put('toast', 'Документы')
    #         #docs_on_start(hashMap)
    #     #tiles_on_start(hashMap)
    #         docs_adr_on_start(hashMap)
    #         hashMap.put('RefreshScreen','')
    #
    # else:
    #
    #     hashMap.put('toast', str(result['error_pool']))

    qtext = '''SELECT id_doc FROM RS_docs WHERE verified = 1  and (sent <> 1 or sent is null)
                UNION
                SELECT id_doc FROM RS_adr_docs WHERE verified = 1  and (sent <> 1 or sent is null)'''
    res  = ui_global.get_query_result(qtext,None,True)

    if res:
        doc_list = []
        for el in res:
            doc_list.append('"'+ el['id_doc']+'"')
        doc_in_str = ','.join(doc_list)
        #htpparams = {'username':hashMap.get('onlineUser'), 'password':hashMap.get('onlinePass'), 'url':url}
        answer = http_exchange.post_changes_to_server(doc_in_str , url)
        if answer.get('Error') is not None:
            ui_global.write_error_on_log(str(answer.get('Error')))
        else:

            qtext = f'UPDATE RS_docs SET sent = 1  WHERE id_doc in ({doc_in_str}) '
            ui_global.get_query_result(qtext)

            qtext = f'UPDATE RS_adr_docs SET sent = 1  WHERE id_doc in ({doc_in_str}) '
            ui_global.get_query_result(qtext)

    return hashMap


def settings_errors_on_start(hashMap,  _files=None, _data=None):

    filter_value = ''
    filter_fields = ('log',)
    hashMap.put('cards', get_table_cards('Error_log', filter_fields, filter_value))

    return hashMap

def settings_errors_on_click(hashMap,  _files=None, _data=None):
    listener = hashMap.get('listener')
    if listener == 'ON_BACK_PRESSED':
        hashMap.put('ShowScreen', 'Настройки и обмен')
        #hashMap.put('FinishProcess', '')

    elif listener == 'btn_clear_err':
        rs_settings.put('error_log','')
        hashMap.put('error_log','')
        hashMap.put('RefreshScreen','')


    elif listener == "CardsClick":
        pass


    elif listener == 'LayoutAction':
        layout_listener = hashMap.get('layout_listener')
        # Находим ID документа
        current_card = json.loads(hashMap.get("current_card"))

    elif listener == 'Search':
        filter_value = hashMap.get('SearchString')
        if len(filter_value) > 2:
            filter_fields = hashMap.get('filter_fields').split(';')
            hashMap.put('cards', get_table_cards(hashMap.get('table_for_select'), filter_fields, filter_value))

            hashMap.put('RefreshScreen', '')
        # universal_cards_on_start(hashMap)

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
        hashMap.put('user_name',ui_form_data.ModernField(hint='user_name', default_text=http_settings['user_name'], password=False).to_json())
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
            hashMap.put('toast', 'Соединение установлено')
        else:
            hashMap.put('btn_test_connection', 'Тест соединения')
            hashMap.put('toast', 'Не удалось установить соединение')

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


# Литвиненко Олег. Создание таблиц по запросу остатков и цен. 16.05.2023

def open_wh_list_on_start(hashMap, _files=None, _data=None):

    j = ui_tables_structure.wh_list_cards

    j["customcards"]["cardsdata"] = []

    query_text = "SELECT * FROM RS_warehouses"
    results = ui_global.get_query_result(query_text)

    for record in results:
        c = {"key": str(record[0]), "name": str(record[1])}
        j["customcards"]["cardsdata"].append(c)

    if not hashMap.containsKey("wh_cards"):
        hashMap.put("wh_cards", json.dumps(j, ensure_ascii=False).encode('utf8').decode())

    return hashMap


def open_cell_list_on_start(hashMap, _files=None, _data=None):

    identify_input_text(hashMap)

    good_id = hashMap.get("selected_good_id")

    if not good_id:
        hashMap.put("toast", "Не выбран товар")
        hashMap.put("ShowScreen", "Проверить остатки")

    """else:

        hashMap.put("cards_loading", "Загружается список ячеек...")"""

    return hashMap


def get_good_cells(hashMap, _files=None, _data=None):
    good_id = hashMap.get("selected_good_id")

    http = get_http_settings(hashMap)
    get_remains_url = http['url'] + '/simple_accounting/good_balances/cells?'
    params = {'android_id': http['android_id'], "id_good": good_id}
    r = requests.get(get_remains_url,
                     auth=HTTPBasicAuth(http['user'], http['pass']),
                     headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'},
                     params=params)

    json_response = json.loads(r.text.encode("utf-8"))

    j = ui_tables_structure.cell_list_cards
    j["customcards"]["cardsdata"] = []
    if len(json_response) > 0:

        appended_cell_id_list = []
        for record in json_response:
            if record["id_cell"] not in appended_cell_id_list:
                if not hashMap.get("property_id") or \
                        record['id_property'] == hashMap.get("property_id"):
                    c = {"key": record["id_cell"], "name": get_name_by_field("RS_cells", 'id', record["id_cell"])}
                    j["customcards"]["cardsdata"].append(c)
                    appended_cell_id_list.append(record["id_cell"])

        appended_cell_id_list.clear()

        if not hashMap.containsKey("cell_cards"):
            hashMap.put("cell_cards", json.dumps(j, ensure_ascii=False).encode('utf8').decode())
        else:
            if not hashMap.get("cell_cards"):
                hashMap.put("cell_cards", json.dumps(j, ensure_ascii=False).encode('utf8').decode())
                hashMap.put("cards_loading", "")
    else:
        hashMap.put("cell_select", "Не размещен в ячейках")
        hashMap.put("ShowScreen", "Проверить остатки")

    hashMap.put("RefreshScreen", "")

    return hashMap


def cell_list_on_input(hashMap, _files=None, _data=None):
    if hashMap.get('listener') == 'CardsClick':
        selected_cell_id = hashMap.get("selected_card_key")
        current_str = hashMap.get("selected_card_position")
        jlist = json.loads(hashMap.get("cell_cards"))
        current_elem = jlist['customcards']['cardsdata'][int(current_str)]
        selected_cell_name = current_elem["name"]

        hashMap.put('selected_cell_id', selected_cell_id)
        hashMap.put("cell_select", selected_cell_name)
        hashMap.put("selected_cell_name", selected_cell_name)
        hashMap.put("cell_cards", "")
        hashMap.put("BackScreen", "")
        return hashMap
    if hashMap.get('listener') == 'back_to_remains' or 'ON_BACK_PRESSED':
        back_to_remains(hashMap)

    return hashMap


def get_remains(hashMap, _files=None, _data=None):

    http = get_http_settings(hashMap)

    if not (hashMap.get('barcode') or hashMap.get('wh_select') or hashMap.get('cell_input')
            or hashMap.get('selected_cell_id') or hashMap.get('selected_good_id')):
        hashMap.put('goods_custom_table', '')
        hashMap.put('object_name', '')
        hashMap.put('cell_name', '')
        hashMap.put('error_msg', "Должен быть выбран склад, товар или ячейка")

    if hashMap.get('good_art_input') or hashMap.get('cell_input') and not hashMap("selected_good_id"):
        identify_input_text(hashMap)

    if hashMap.get("error_msg"):
        hashMap.put("Show_error_msg", "1")
    else:
        hashMap.put("Show_error_msg", "-1")

    if hashMap.get('selected_cell_id'):

        get_remains_url = http['url'] + '/simple_accounting/good_balances/cells?'

        params = {'android_id': http['android_id'], 'id_cell': hashMap.get('selected_cell_id')}

        goods_custom_table = ui_tables_structure.goods_custom_table_cell

        tbody_layout = ui_tables_structure.tbody_remains_layout_cell

        if not hashMap.get("selected_cell_name"):
            hashMap.put('selected_cell_name', hashMap.get('cell_input'))
        hashMap.put('Show_selected_cell_name', '1')
        hashMap.put('Show_selected_wh_name', '-1')

        if hashMap.get('selected_good_id'):
            params['id_good'] = hashMap.get('selected_good_id')
            hashMap.put('selected_object_name', hashMap.get('object_name') + ", " + hashMap.get('good_code'))
            hashMap.put('Show_selected_object_name', '1')
        else:
            hashMap.put('Show_selected_object_name', '-1')

        if hashMap.get('barcode_info') and hashMap.get("barcode_info") != hashMap.get('selected_cell_name'):
            hashMap.put('Show_barcode_info', '1')
        else:
            hashMap.put('Show_barcode_info', '-1')

        hashMap.put('Show_selected_cell_name', '1')

        r = requests.get(get_remains_url,
                         auth=HTTPBasicAuth(http['user'], http['pass']),
                         headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'},
                         params=params)

        json_response = json.loads(r.text.encode("utf-8"))

        if len(json_response) < 1:
            hashMap.put("no_data", "Нет данных")
            hashMap.put("Show_no_data", "1")
        else:
            hashMap.put("Show_no_data", "-1")

        values = 0
        for element in json_response:
            if element["id_property"]:
                values += 1

        if values == 0:
            goods_custom_table['customtable']['layout']['Elements'].pop(3)
            tbody_layout['Elements'].pop(3)

        if hashMap.get('selected_good_id'):
            goods_custom_table['customtable']['layout']['Elements'].pop(1)
            tbody_layout['Elements'].pop(1)

        goods_custom_table['customtable']['layout']['Elements'].pop(0)
        tbody_layout['Elements'].pop(0)

        goods_custom_table["customtable"]["tabledata"] = [{}]

        i = 0
        for element in json_response:

            c = {"key": str(i), "item": get_name_by_id("RS_goods", element["id_good"]),
                 "quantity": element['qtty'], '_layout': tbody_layout,
                 'cell': get_name_by_id("RS_cells", element["id_cell"])}

            if element["id_property"] is None:
                c['properties'] = ''
            else:
                c['properties'] = get_name_by_field("RS_properties", 'id', element["id_property"])
            if hashMap.get('property_id'):
                if element["id_property"] == hashMap.get('property_id'):
                    goods_custom_table["customtable"]["tabledata"].append(c)
                    i += 1
            else:
                goods_custom_table["customtable"]["tabledata"].append(c)
                i += 1

    else:

        if hashMap.get('selected_good_id') or hashMap.get('selected_warehouse_id'):

            get_remains_url = http['url'] + '/simple_accounting/good_balances/warehouses?'

            params = {'android_id': http['android_id']}

            goods_custom_table = ui_tables_structure.goods_custom_table_wh

            tbody_layout = ui_tables_structure.tbody_remains_layout_wh

            if hashMap.get('selected_good_id'):
                params['id_good'] = hashMap.get('selected_good_id')
                hashMap.put('selected_object_name', hashMap.get('object_name') + ", " + hashMap.get('good_code'))
                hashMap.put('Show_selected_object_name', '1')
            else:
                hashMap.put('Show_selected_object_name', '-1')

            if hashMap.get('selected_warehouse_id'):
                params['id_warehouse'] = hashMap.get('selected_warehouse_id')
                hashMap.put('selected_wh_name', hashMap.get('wh_select'))
                hashMap.put('Show_selected_wh_name', '1')
            else:
                hashMap.put('Show_selected_wh_name', '-1')

            if hashMap.get('barcode_info'):
                hashMap.put('Show_barcode_info', '1')
            else:
                hashMap.put('Show_barcode_info', '-1')

            hashMap.put('Show_selected_cell_name', '-1')

            r = requests.get(get_remains_url,
                             auth=HTTPBasicAuth(http['user'], http['pass']),
                             headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'},
                             params=params)

            json_response = json.loads(r.text.encode("utf-8"))

            if len(json_response) < 1:
                hashMap.put("no_data", "Нет данных")
                hashMap.put("Show_no_data", "1")
            else:
                hashMap.put("Show_no_data", "-1")

            values = 0
            for element in json_response:
                if element["id_property"]:
                    values += 1

            if values == 0:
                goods_custom_table['customtable']['layout']['Elements'].pop(3)
                tbody_layout['Elements'].pop(3)

            if hashMap.get('selected_good_id'):
                goods_custom_table['customtable']['layout']['Elements'].pop(1)
                tbody_layout['Elements'].pop(1)

            if hashMap.get('selected_warehouse_id'):
                goods_custom_table['customtable']['layout']['Elements'].pop(0)
                tbody_layout['Elements'].pop(0)

            goods_custom_table["customtable"]["tabledata"] = [{}]

            i = 0

            for element in json_response:

                c = {"key": str(i), "item": get_name_by_id("RS_goods", element["id_good"]),
                     "quantity": element['qtty'], '_layout': tbody_layout,
                     'warehouse': get_name_by_id("RS_warehouses", element["id_warehouse"])}

                if element["id_property"] is None:
                    c['properties'] = ''
                else:
                    c['properties'] = get_name_by_field("RS_properties", 'id', element["id_property"])
                if hashMap.get('property_id'):
                    if element["id_property"] == hashMap.get('property_id'):
                        goods_custom_table["customtable"]["tabledata"].append(c)
                        i += 1
                else:
                    goods_custom_table["customtable"]["tabledata"].append(c)
                    i += 1

        else:
            return hashMap

    if not hashMap.get("return_to_good_card"):
        hashMap.put('barcode', '')

    if len(goods_custom_table["customtable"]["tabledata"]) < 1:
        hashMap.put('error_msg', "Товар не найден")
        hashMap.put('Show_error_msg', '1')

    hashMap.put("property_id", "")

    hashMap.put("goods_custom_table", json.dumps(goods_custom_table))

    hashMap.put("ShowScreen", "Таблица остатков")

    return hashMap


def identify_input_text(hashMap):

    if hashMap.get('good_art_input'):
        good_art_input = hashMap.get('good_art_input')

    cell_input = hashMap.get('cell_input')

    if good_art_input and not hashMap.get('return_to_good_card'):

        good_name = ui_global.get_query_result("SELECT name FROM RS_goods where art = '" + good_art_input + "'")

        if len(good_name) > 0:

            good_query = ui_global.get_query_result("SELECT id,code FROM RS_goods where art = '" + good_art_input + "'")
            hashMap.put('selected_good_id', good_query[0][0])
            hashMap.put('good_code', good_query[0][1])
            hashMap.put('object_name', str(good_name).split("'")[1])
            hashMap.put('error_msg', "")
            # hashMap.put('good_art_input', hashMap.get('good_art_input'))

        else:
            hashMap.put('error_msg', " Товар с артикулом " + "'" + good_art_input + "'" + " не найден")
            # hashMap.put('object_name', "")

    if cell_input:

        cell_id = ui_global.get_query_result("SELECT id FROM RS_cells where name = '" + cell_input + "'")

        if len(cell_id) > 0:
            hashMap.put('selected_cell_id', str(cell_id).split("'")[1])
            hashMap.put('cell_name', cell_input)
            # hashMap.put('error_msg', "")

        else:
            if hashMap.get('error_msg'):
                hashMap.put('error_msg', hashMap.get('error_msg') + "\n" + " Ячейка c именем " + "'" +
                            cell_input + "'" + " не найдена")
            else:
                hashMap.put('error_msg', " Ячейка c именем " + "'" + cell_input + "'" + " не найдена")
            # hashMap.put('cell_name', "")

    return hashMap


def identify_barcode_remains(hashMap, _files=None, _data=None):

    hashMap.put('barcode_info', str(hashMap.get('barcode')))
    hashMap.put("cell_cards", "")


    if hashMap.get('barcode'):
        barcode = hashMap.get('barcode')

        barcode_query = ui_global.get_query_result("SELECT id_good,id_property FROM RS_barcodes where barcode = '" + barcode + "'")

        if len(barcode_query) > 0:
            if barcode_query[0][0]:
                good_id = barcode_query[0][0]
                hashMap.put('selected_good_id', str(good_id))

                good_query = ui_global.get_query_result("SELECT name,art,code FROM RS_goods where id = '" + good_id + "'")
                if good_query[0][0]:

                    hashMap.put('object_name', good_query[0][0])
                else:
                    hashMap.put("object_name", "")
                if good_query[0][1]:

                    hashMap.put('good_art_input', str(good_query[0][1]))
                else:
                    hashMap.put('good_art_input', "")
                if good_query[0][2]:
                    hashMap.put("good_code", good_query[0][2])
                else:
                    hashMap.put("good_code", "")

                hashMap.put('error_msg', "")

            if barcode_query[0][1]:
                property_id = barcode_query[0][1]
                hashMap.put('property_id', property_id)

        else:

            cell_id = ui_global.get_query_result("SELECT id FROM RS_cells where barcode = '" + barcode + "'")

            if len(cell_id) > 0:

                cell_name = ui_global.get_query_result("SELECT name FROM RS_cells where id = '" + str(cell_id).split("'")[1] + "'")

                hashMap.put('selected_cell_id', str(cell_id).split("'")[1])
                hashMap.put('selected_cell_name', str(cell_name).split("'")[1])
                hashMap.put('error_msg', "")
            else:
                hashMap.put('object_name', "")
                hashMap.put('error_msg', "Штрихкод не распознан")

    get_remains(hashMap)

    return hashMap


def back_to_remains(hashMap, _files=None, _data=None):
    hashMap.put('wh_select', '')
    hashMap.put('cell_select', '')
    hashMap.put('cell_cards', '')
    hashMap.put('selected_cell_name', '')
    hashMap.put('selected_cell_id', '')
    hashMap.put('selected_warehouse_id', '')
    hashMap.put("BackScreen", "")

    return hashMap


def price_types_list_on_start(hashMap, _files=None, _data=None):

    j = ui_tables_structure.price_types_list_cards

    j["customcards"]["cardsdata"] = []

    query_text = "SELECT * FROM RS_price_types"
    results = ui_global.get_query_result(query_text)

    for record in results:
        c = {"key": str(record[0]), "name": str(record[1])}
        j["customcards"]["cardsdata"].append(c)

    if not hashMap.containsKey("price_type_cards"):
        hashMap.put("price_type_cards", json.dumps(j, ensure_ascii=False).encode('utf8').decode())

    return hashMap


def property_list_on_start(hashMap, _files=None, _data=None):

    j = ui_tables_structure.property_list_cards

    j["customcards"]["cardsdata"] = []

    if hashMap.get("good_type_id"):
        good_type = hashMap.get('good_type_id')
    else:
        good_type_query_text = "SELECT type_good FROM RS_goods WHERE id = '" + hashMap.get('input_good_id') + "'"
        good_type_query = ui_global.get_query_result(good_type_query_text)
        if len(good_type_query) > 0:
            good_type = good_type_query[0][0]

    personal_properties_query_text = "SELECT * FROM RS_properties WHERE id_owner = '" + good_type + "'"
    results = ui_global.get_query_result(personal_properties_query_text)

    if not len(results) > 0:
        type_properties_query_text = "SELECT * FROM RS_properties WHERE id_owner = '" + hashMap.get(
            'input_good_id') + "'"
        results = ui_global.get_query_result(type_properties_query_text)

    if len(results) > 0:
        for record in results:
            if record[0] and record[2]:
                c = {"key": str(record[0]), "name": str(record[2])}
                j["customcards"]["cardsdata"].append(c)

        # if not hashMap.containsKey("property_cards"):
        hashMap.put("property_cards", json.dumps(j, ensure_ascii=False).encode('utf8').decode())
    else:
        hashMap.put("toast", "Для данного товара нет характеристик")
        hashMap.put("ShowScreen", "Проверка цен")

    return hashMap


def unit_list_on_start(hashMap, _files=None, _data=None):

    j = ui_tables_structure.unit_list_cards

    j["customcards"]["cardsdata"] = []

    query_text = "SELECT * FROM RS_units WHERE id_owner = '" + hashMap.get('input_good_id') + "'"
    results = ui_global.get_query_result(query_text)

    if len(results) > 0:
        for record in results:
            c = {"key": str(record[0]), "name": str(record[3])}
            j["customcards"]["cardsdata"].append(c)

        if not hashMap.containsKey("unit_cards"):
            hashMap.put("unit_cards", json.dumps(j, ensure_ascii=False).encode('utf8').decode())

    else:
        hashMap.put("toast", "Для данного товара нет выбора упаковки")
        hashMap.put("ShowScreen", "Проверка цен")


    return hashMap


def get_prices(hashMap, _files=None, _data=None):

    http = get_http_settings(hashMap)

    prices_custom_table = ui_tables_structure.prices_custom_table

    tbody_layout = ui_tables_structure.tbody_prices_layout

    get_good_by_art(hashMap)

    if hashMap.get('barcode_info'):
        hashMap.put('Show_barcode_info', '1')
    else:
        hashMap.put('Show_barcode_info', '-1')

    hashMap.put("no_data", "")

    if hashMap.get('input_good_id'):  # Если найден соответствующий товар

        get_prices_url = http['url'] + '/simple_accounting/good_prices?'

        params = {'android_id': http['android_id'], 'id_good': hashMap.get('input_good_id')}

        if hashMap.get('selected_property_id'):
            params['id_property'] = hashMap.get('selected_property_id')

        if hashMap.get('property_id'):  # От Штрих-кода
            params['id_property'] = hashMap.get('property_id')

        if hashMap.get('selected_unit_id'):
            params['id_unit'] = hashMap.get('selected_unit_id')

        if hashMap.get('selected_price_type_id'):
            params['id_price_type'] = hashMap.get('selected_price_type_id')

        r = requests.get(get_prices_url,
                         auth=HTTPBasicAuth(http['user'], http['pass']),
                         headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'},
                         params=params)

        json_prices = json.loads(r.text.encode("utf-8"))

        if len(json_prices) < 1:
            hashMap.put("no_data", "Нет данных")

        unit_values = 0
        property_values = 0
        for element in json_prices:
            if element["id_unit"]:
                unit_values += 1
            if element['id_property']:
                property_values += 1

        if unit_values == 0:
            prices_custom_table['customtable']['layout']['Elements'].pop(4)
            tbody_layout['Elements'].pop(4)

        if property_values == 0:
            prices_custom_table['customtable']['layout']['Elements'].pop(1)
            tbody_layout['Elements'].pop(1)

        prices_custom_table['customtable']['layout']['Elements'].pop(0)
        tbody_layout['Elements'].pop(0)

        prices_custom_table["customtable"]["tabledata"] = [{}]

        i = 0

        for element in json_prices:

            c = {"key": str(i), "good": element["id_good"], "property": element["id_property"],
                 "price": element['price'], "price_type": element['id_price_type'], "unit": element["id_unit"],
                 '_layout': tbody_layout}

            if element['id_good']:
                c['good'] = get_name_by_id("RS_goods", element["id_good"])
            else:
                c['good'] = ""

            if element['id_unit']:
                c['unit'] = get_name_by_id("RS_units", element["id_unit"])
            else:
                c['unit'] = ""

            if element['id_price_type']:
                c['price_type'] = get_name_by_id("RS_price_types", element["id_price_type"])
            else:
                c['price_type'] = ""

            if element["id_property"]:  # Похоже обращение не к той таблице
                try:
                    c['property'] = get_name_by_id("RS_properties", element["id_property"])
                except IndexError:
                    c['property'] = element["id_property"]
            else:
                c['property'] = ""

            prices_custom_table["customtable"]["tabledata"].append(c)

            i += 1

        hashMap.put('prices_custom_table', json.dumps(prices_custom_table))

        hashMap.put('prices_error_msg', "")
        hashMap.put("ShowScreen", "Таблица цен")

    else:
        if hashMap.get('input_good_art'):
            hashMap.put('prices_error_msg', "Не найден соответствующий товар")
        else:
            hashMap.put('prices_error_msg', "Не указан товар")

    hashMap.put('property_id', "")

    return hashMap


def get_good_by_art(hashMap):

    # hashMap.put('input_value', hashMap.get('input_good_id'))

    if not hashMap.get('input_good_id'):

        if len(hashMap.get('input_good_art')) > 0:

            good_id_query = ui_global.get_query_result("SELECT id FROM RS_goods where art = '" +
                                                       hashMap.get('input_good_art') + "'")

            good_name_query = ui_global.get_query_result("SELECT name,code,type_good FROM RS_goods where art = '" +
                                                         hashMap.get('input_good_art') + "'")

            if len(good_id_query) > 0:
                good_id = str(good_id_query).split("'")[1]
                good_name = good_name_query[0][0]
                good_code = good_name_query[0][1]
                good_type_id = good_name_query[0][2]
                hashMap.put("input_good_id", good_id)
                hashMap.put("prices_object_name", good_name + ", " + good_code)
                hashMap.put('good_code', good_code)
                hashMap.put('good_type_id', good_type_id)
        else:
            hashMap.put('prices_error_msg', "Товар не выбран")
    return hashMap


def get_name_by_id(table_name, record_id):

    query = ui_global.get_query_result(
        "SELECT name FROM " + table_name.strip('"\'') + " where id = '" + record_id + "'")
    if type(query) == "str":
        return str(query).split("'")[1]
    else:
        return str(query[0]).split("'")[1]


def kill_remains_tables(hashMap, _files=None, _data=None):
    hashMap.put('wh_select', '')
    hashMap.put('good_art_input', '')
    hashMap.put('cell_input', '')
    hashMap.put('cell_name', '')
    hashMap.put('cell_select', '')
    hashMap.put('object_name', '')
    hashMap.put('error_msg', '')
    hashMap.put('goods_custom_table', '')
    hashMap.put('selected_cell_id', '')
    hashMap.put('selected_cell_name', '')
    hashMap.put('good_code', '')
    hashMap.put('selected_object_name', '')
    hashMap.put('selected_wh_name', '')
    hashMap.put('selected_warehouse_id', '')
    hashMap.put('barcode_info', '')
    if not hashMap.get("return_to_good_card"):
        hashMap.put('barcode', '')

    return hashMap


def kill_price_tables(hashMap, _files=None, _data=None):
    hashMap.put('input_good_art', '')
    hashMap.put('prices_object_name', '')
    hashMap.put('selected_price_type_id', '')
    hashMap.put('selected_price_type_name', '')
    hashMap.put('price_type_select', '')
    hashMap.put('selected_property_id', '')
    hashMap.put('selected_property_name', '')
    hashMap.put("property_select", '')
    hashMap.put('selected_unit_id', "")
    hashMap.put('selected_unit_name', '')
    hashMap.put("unit_select", "")
    hashMap.put('prices_custom_table', '')
    hashMap.put('input_good_id', '')
    if not hashMap.get("return_to_good_card"):
        hashMap.put('barcode', '')
    hashMap.put('good_code', '')
    hashMap.put('barcode_info', '')

    return hashMap


def goods_on_start(hashMap, _files=None, _data=None):

    filter_fields = []
    filter_value = ''

    if hashMap.get('type_id'):
        filter_fields.append('type_good')
        filter_value = hashMap.get('type_id')

    goods_cards_json = get_table_cards('RS_goods', filter_fields, filter_value, exclude_list=['description'],
                                       no_label=True)
    goods_cards = modify_cards(json.loads(goods_cards_json), hide_name=True, title_color="#7A005C",
                               replace_blank=True, disable_override_search=True)
    hashMap.put('goods_cards', json.dumps(goods_cards))

    return hashMap


def goods_on_input(hashMap, _files=None, _data=None):
    if hashMap.get("listener") == "CardsClick":
        hashMap.put('selected_good_id', hashMap.get("selected_card_key"))
        hashMap.put('barcode', '')
        hashMap.put("ShowScreen", "Карточка товара")
    if hashMap.get('listener') == 'select_goods_type':
        hashMap.put('ShowScreen', "Выбор")
    if hashMap.get('listener') == 'barcode':
        identify_barcode_goods(hashMap)
    if hashMap.get('listener') == 'ON_BACK_PRESSED':
        hashMap.put('FinishProcess', '')
    return hashMap


def identify_barcode_goods(hashMap, _files=None, _data=None):
    if hashMap.get('barcode'):
        barcode = hashMap.get('barcode')

        good_id = ui_global.get_query_result("SELECT id_good FROM RS_barcodes where barcode = '" + barcode + "'")

        properties_query = ui_global.get_query_result(
            "SELECT id_property FROM RS_barcodes where barcode = '" + barcode + "'")

        if properties_query:
            property_id = str(properties_query).split("'")[1]
            hashMap.put('property_id', property_id)

        if len(good_id) > 0:
            hashMap.put('selected_good_id', str(good_id).split("'")[1])

            hashMap.put('ShowScreen', 'Карточка товара')
        else:
            hashMap.put('error_txt', 'Товар не распознан по штрихкоду')

    return hashMap


def good_card_on_start(hashMap, _files=None, _data=None):

    hashMap.put("Show_buttons", "-1")  # Пока спрятали переход к процессам "остатки" и "цены"

    if hashMap.get('selected_good_id'):
        selected_good_id = hashMap.get('selected_good_id')

        result_rs_goods = ui_global.get_query_result("SELECT name,art,code,type_good,description FROM RS_goods where id = '" + selected_good_id + "'")

        good_name = result_rs_goods[0][0]
        good_art = result_rs_goods[0][1]
        good_code = result_rs_goods[0][2]
        good_type_id = result_rs_goods[0][3]
        good_descr = result_rs_goods[0][4]

        good_type = get_name_by_id('RS_types_goods', good_type_id)

        fill_empty_values(hashMap, {"good_name": good_name, "good_art": good_art, "good_code": good_code,
                                    "good_descr": good_descr, "good_type": good_type}, value="отсутствует")

    return hashMap


def good_card_on_input(hashMap,  _files=None, _data=None):

    if hashMap.get('listener') == 'ON_BACK_PRESSED':
        if hashMap.get('barcode'):
            hashMap.put('barcode', '')
        if hashMap.get('barcode_cards'):
            hashMap.put('barcode_cards', '')
        if hashMap.get('return_to_good_card'):
            hashMap.put('return_to_good_card', '')
        if hashMap.get('selected_good_id'):
            hashMap.put('selected_good_id', '')
        if hashMap.get('property_id'):
            hashMap.put('property_id', '')
        hashMap.put("ShowScreen", "Товары список")
    if hashMap.get("listener") == "TilesClick":
        hashMap.put('toast', str(hashMap.get('selected_tile_key')))
    if hashMap.get('listener') == 'to_prices':
        hashMap.put('input_good_id', hashMap.get('selected_good_id'))  # selected_good_id input_good_id
        hashMap.put('input_good_art', hashMap.get('good_art'))
        hashMap.put('prices_object_name', hashMap.get('good_name') + ", " + hashMap.get('good_code'))
        hashMap.put("return_to_good_card", "true")
        hashMap.put('property_id', hashMap.get('property_id'))
        hashMap.put('ShowProcessResult', 'Цены|Проверка цен')
    if hashMap.get('listener') == 'to_remains':
        hashMap.put('good_art_input', hashMap.get('good_art'))
        hashMap.put("return_to_good_card", "true")
        hashMap.put('selected_object_name', hashMap.get('good_name') + ", " + hashMap.get('good_code'))
        hashMap.put('object_name', hashMap.get('good_name'))
        hashMap.put('property_id', hashMap.get('property_id'))
        hashMap.put('SetResultListener', 'onStart')
        hashMap.put('ShowProcessResult', 'Остатки|Проверить остатки')
    return hashMap


def price_tables_on_start(hashMap,  _files=None, _data=None):
    if hashMap.get('parent_screen') == "Товары список":
        hashMap.put('current_screen_name', "Товары список")

    return hashMap


def get_good_variants(hashMap, _files=None, _data=None):
    selected_good_id = hashMap.get("selected_good_id")
    barcode = hashMap.get('barcode')

    if barcode:
        goods_barcode = ui_global.get_query_result(
            "SELECT barcode,id_property,id_series,id_unit FROM RS_barcodes WHERE barcode = '" + barcode +
            "'")

    elif selected_good_id:
        goods_barcode = ui_global.get_query_result(
            "SELECT barcode,id_property,id_series,id_unit FROM RS_barcodes WHERE id_good = '" + selected_good_id +
            "'")

    if len(goods_barcode) > 0:
        barcode_cards = ui_tables_structure.barcode_cards
        barcode_cards["customcards"]["cardsdata"] = []
        i = 0
        for element in goods_barcode:
            c = {"key": str(i), "barcode": element[0], "properties": element[1], "unit": element[3],
                 "series": element[2]}

            if element[1]:
                c['properties'] = get_name_by_field("RS_properties", "id", element[1])
            if element[3]:
                c['unit'] = get_name_by_field("RS_units", "id", element[3])

            barcode_cards["customcards"]["cardsdata"].append(c)
            i += 1
        hashMap.put("barcode_cards", json.dumps(barcode_cards))
        hashMap.put("load_info", "")
    else:
        hashMap.put("load_info", "Данные о характеристиках отсутствуют")

    return hashMap


def fill_empty_values(hashMap, names_list=dict(), value=""):

    for k, v in names_list.items():

        if v is None or v == "None":
            v = ''
        if len(v) == 0:
            hashMap.put(k, value)
        else:
            hashMap.put(k, v)

    return hashMap


def remains_on_start(hashMap, _files=None, _data=None):

    return hashMap


def modify_cards(j, hide_name=False, title_color='', replace_blank=False, disable_override_search=False):
    cards_layout_elements = j['customcards']['layout']['Elements'][0]['Elements'][0]['Elements']

    if disable_override_search:
        j['customcards']['options']['override_search'] = False

    for element in cards_layout_elements:
        if element['Value'] == '@name':
            if cards_layout_elements.index(element) == 0:
                element['gravity_horizontal'] = "left"
                if title_color:
                    element["TextColor"] = title_color
                # element['Value'] = str(0)
            else:
                if hide_name:

                    # element["show_by_condition"] = "True"
                    del cards_layout_elements[cards_layout_elements.index(element)]

    if replace_blank:
        cards_data = j['customcards']['cardsdata']

        for element in cards_data:
            for key, val in element.items():
                if val == 'None' or val == "":
                    element[key] = "—"

    return j


def get_name_by_field(table_name, field, field_value):

    query = ui_global.get_query_result(
        "SELECT name FROM " + table_name.strip('"\'') + " WHERE " + field + '=' + "'" + field_value + "'")
    try:
        if type(query) == "str":
            return str(query).split("'")[1]
        else:
            return str(query[0]).split("'")[1]
    except IndexError:
        return field_value


def good_types_on_start(hashMap, _files=None, _data=None):

    cards_json = get_table_cards('RS_types_goods', exclude_list=['use_mark'], no_label=True)

    cards = modify_cards(json.loads(cards_json), hide_name=True, disable_override_search=True)

    hashMap.put('cards', json.dumps(cards))

    # hashMap.put('cards', cards_json)

    return hashMap


def good_types_on_click(hashMap, _files=None, _data=None):
    listener = hashMap.get("listener")

    if listener == "CardsClick":

        selected_type_id = hashMap.get('selected_card_key')

        hashMap.put('type_id', str(selected_type_id))

        selected_type_name = get_name_by_field("RS_types_goods", "id", selected_type_id)

        hashMap.put('select_goods_type', selected_type_name)

        hashMap.put("ShowScreen", "Товары список")

    elif listener == 'ON_BACK_PRESSED':
        hashMap.put('type_id', '')
        hashMap.put('type_name', '')
        hashMap.put("ShowScreen", "Товары список")

    return hashMap


def remains_on_input(hashMap, _files=None, _data=None):
    if hashMap.get('listener') == 'wh_select':
        hashMap.put("ShowScreen", "Выбор склада")
    if hashMap.get('listener') == 'cell_select':
        hashMap.put("ShowScreen", "Выбор ячейки")
    if hashMap.get('listener') == 'get_remains_btn':
        get_remains(hashMap)
    if hashMap.get('listener') == 'barcode':
        identify_barcode_remains(hashMap)
    if hashMap.get('listener') == 'ON_BACK_PRESSED':
        kill_remains_tables(hashMap)
        if hashMap.get('return_to_good_card'):
            hashMap.put("FinishProcessResult", "")
            hashMap.put("ShowScreen", "Карточка товара")
        else:
            hashMap.put("FinishProcess", "")
    return hashMap


def warehouse_on_input(hashMap, _files=None, _data=None):
    if hashMap.get('listener') == 'CardsClick':
        selected_wh_id = hashMap.get("selected_card_key")
        selected_wh_name = ui_global.get_query_result(
            "SELECT name FROM RS_warehouses where id = '" + selected_wh_id + "'")
        hashMap.put('selected_warehouse_id', str(selected_wh_id))
        hashMap.put("wh_select", str(selected_wh_name[0]).split("'")[1])
        hashMap.put('error_msg', '')
        hashMap.put("BackScreen", "")
        return hashMap
    if hashMap.get('listener') == 'back_to_remains' or 'ON_BACK_PRESSED':
        back_to_remains(hashMap)
    return hashMap


def remains_tables_on_input(hashMap, _files=None, _data=None):
    if hashMap.get('listener') == 'show_filters':
        hashMap.put("ShowScreen", "Проверить остатки")
    if hashMap.get('listener') == 'ON_BACK_PRESSED':
        if not hashMap.get("return_to_good_card"):
            hashMap.put('property_id', '')
            hashMap.put('barcode', '')

        if hashMap.get("return_to_good_card"):
            hashMap.put("BackScreen", '')
        else:
            hashMap.put('selected_good_id', '')

            if hashMap.get("current_screen_name") == "Таблица остатков":
                kill_remains_tables(hashMap)
                hashMap.put('ShowScreen', 'Проверить остатки')
            elif hashMap.get("current_screen_name") == "Таблица цен":
                kill_price_tables(hashMap)
                hashMap.put('ShowScreen', 'Проверка цен')
    if hashMap.get('listener') == 'barcode':
        identify_barcode_remains(hashMap)
    if hashMap.get('listener') == "CardsClick":
        hashMap.put("toast", str(hashMap.get("selected_card_position")))
    return hashMap


def on_close_app(hashMap, _files=None, _data=None):
    suClass.deleteCache()
    return hashMap