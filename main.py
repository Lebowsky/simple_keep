import json
import requests
from requests.auth import HTTPBasicAuth
import os

import ui_global
import ui_form_data

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


def barcode_error_screen_listener(hashMap, _files=None, _data=None):
    if hashMap.get('listener') == 'ON_BACK_PRESSED':
        # suClass.urovo_set_lock_trigger(False)
        hashMap.put("ShowScreen", "Документ товары")
    elif hashMap.get('listener') == 'btn_continue_scan':
        # suClass.urovo_set_lock_trigger(False)
        hashMap.put("ShowScreen", "Документ товары")
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

# ^^^^^^^^^^^^^^^^^ Universal cards ^^^^^^^^^^^^^^^^^