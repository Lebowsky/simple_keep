import db_services
from ru.travelfood.simple_ui import SimpleUtilites as suClass

import ui_barcodes
import ui_csv
import ui_global
import ui_form_data
import ui_models
import socket
import json
import requests
import database_init_queryes
import os
from PIL import Image
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
importlib.reload(database_init_queryes)
importlib.reload(http_exchange)
importlib.reload(ui_utils)
importlib.reload(db_services)
importlib.reload(widgets)
importlib.reload(ui_models)


def create_screen(hash_map):
    screen_params = {
        'hash_map': hash_map,
        'rs_settings': rs_settings
    }
    screen = ui_models.ScreensFactory.create_screen(**screen_params)
    if not screen:
        screen = ui_models.MockScreen(hash_map, rs_settings)

    return screen

# =============== Main events =================

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


@HashMap()
def timer_update(hashMap,  _files=None, _data=None):
    timer = ui_models.Timer(hashMap, rs_settings)
    timer.timer_on_start()
    # url = get_http_settings(hashMap)

    #url = 'http://192.168.1.77/NSI/hs/simple_accounting/data'

    # hashMap.put('toast', 'Обмен') #url)
    # result = http_exchange.timer_server_load_data(url)
    # new_docs_list = result['new_docs_list']
    # if len(result) > 0:
    #     hashMap.put("basic_notification", json.dumps([{'number': 1, 'title': "Добавлены документы:",
    #                                                        'message': str(result)}]))

    # if len(new_docs_list) > 0:
    #     hashMap.put("basic_notification", json.dumps([{'number': 1, 'title': "Добавлены документы",
    #                                                    'message': str(new_docs_list)}]))
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

    # qtext = '''SELECT id_doc FROM RS_docs WHERE verified = 1  and (sent <> 1 or sent is null)
    #             UNION
    #             SELECT id_doc FROM RS_adr_docs WHERE verified = 1  and (sent <> 1 or sent is null)'''
    # res  = ui_global.get_query_result(qtext,None,True)
    #
    # if res:
    #     doc_list = []
    #     for el in res:
    #         doc_list.append('"'+ el['id_doc']+'"')
    #     doc_in_str = ','.join(doc_list)
    #     #htpparams = {'username':hashMap.get('onlineUser'), 'password':hashMap.get('onlinePass'), 'url':url}
    #     answer = http_exchange.post_changes_to_server(doc_in_str , url)
    #     if answer.get('Error') is not None:
    #         ui_global.write_error_on_log(str(answer.get('Error')))
    #     else:
    #
    #         qtext = f'UPDATE RS_docs SET sent = 1  WHERE id_doc in ({doc_in_str}) '
    #         ui_global.get_query_result(qtext)
    #
    #         qtext = f'UPDATE RS_adr_docs SET sent = 1  WHERE id_doc in ({doc_in_str}) '
    #         ui_global.get_query_result(qtext)

    # return hashMap


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


def on_close_app(hashMap, _files=None, _data=None):
    suClass.deleteCache()
    return hashMap

# ^^^^^^^^^^^^^^^^^ Main events ^^^^^^^^^^^^^^^^^


# =============== Documents =================


@HashMap()
def tiles_on_start(hash_map: HashMap):
    screen = create_screen(hash_map)
    screen.on_start()


@HashMap()
def tiles_on_input(hash_map: HashMap):
    screen = create_screen(hash_map)
    screen.on_input()


@HashMap()
def docs_on_start(hash_map: HashMap):
    screen = create_screen(hash_map)
    screen.on_start()


@HashMap()
def docs_on_select(hash_map: HashMap):
    screen = create_screen(hash_map)
    screen.on_input()


@HashMap()
def doc_details_on_start(hash_map: HashMap):
    screen: ui_models.GroupScanDocDetailsScreen = create_screen(hash_map)
    screen.on_start()


@HashMap()
def doc_details_listener(hash_map: HashMap):
    screen = create_screen(hash_map)
    screen.on_input()


@HashMap()
def doc_details_barcode_scanned(hash_map: HashMap):
    screen = ui_models.GroupScanDocDetailsScreen(hash_map, rs_settings)
    screen.post_barcode_scanned(get_http_settings(hash_map))


def elem_on_start(hashMap, _files=None, _data=None):
    hashMap.put('mm_local', '')
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


def elem_viev_on_start(hashMap, _files=None, _data=None):
    hashMap.put('mm_local', '')
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

# ^^^^^^^^^^^^^^^^^ Documents ^^^^^^^^^^^^^^^^^

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

# =============== Goods =================


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


def get_name_by_id(table_name, record_id):

    query = ui_global.get_query_result(
        "SELECT name FROM " + table_name.strip('"\'') + " where id = '" + record_id + "'")
    if type(query) == "str":
        return str(query).split("'")[1]
    else:
        return str(query[0]).split("'")[1]


def fill_empty_values(hashMap, names_list=dict(), value=""):

    for k, v in names_list.items():

        if v is None or v == "None":
            v = ''
        if len(v) == 0:
            hashMap.put(k, value)
        else:
            hashMap.put(k, v)

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
        barcode_cards = ui_form_data.barcode_cards
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


# ^^^^^^^^^^^^^^^^^ Goods ^^^^^^^^^^^^^^^^^


# =============== Settings =================

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


@HashMap()
def settings_errors_on_start(hash_map: HashMap):

    screen = create_screen(hash_map)
    screen.on_start()




@HashMap()
def settings_errors_on_click(hash_map: HashMap):

    screen = create_screen(hash_map)
    screen.on_input()


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


# ^^^^^^^^^^^^^^^^^ Settings ^^^^^^^^^^^^^^^^^


# =============== Debug =================


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


