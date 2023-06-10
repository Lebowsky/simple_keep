from abc import ABC, abstractmethod

from ui_utils import HashMap
from db_services import DocService
import widgets


class Screen(ABC):
    screen_name: str
    process_name: str

    def __init__(self, hash_map: HashMap):
        self.hash_map: HashMap = hash_map
        self.screen_values = {}

    @abstractmethod
    def on_start(self):
        pass

    @abstractmethod
    def on_input(self):
        pass

    @abstractmethod
    def on_post_start(self):
        pass

    @abstractmethod
    def show(self):
        pass

    def toast(self, text):
        self.hash_map.toast(text)

    def __str__(self):
        return f'{self.process_name} / {self.screen_name}'

    def _validate_screen_values(self):
        for key, value in self.screen_values.items():
            if value is None:
                raise ValueError(f'For key {key} must be set value not None')


class Tiles(Screen):
    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map)
        self.listener = self.hash_map['listener']
        self.rs_settings = rs_settings
        self.name = 'Плитки'
        self.db_service = DocService()
        self.screen_name = self.hash_map.get_current_screen()
        self.process_name = self.hash_map.get_current_process()

    def on_start(self) -> None:
        small_tile = self._get_doc_tiles(self.rs_settings)
        res = self.db_service.get_docs_stat()
        next_screen_name = 'Документы'

        tiles = {
            'tiles': [[]],
            'background_color': '#f5f5f5'
        }

        rows = 1
        columns = 1
        for el in res:
            if el['docType'] is None:
                continue

            if columns % 3 == 0:
                rows += 1
                columns = 0
                tiles['tiles'].append([])
            columns += 1
            tile = {
                "layout": small_tile,
                "data": {
                    "docName": el['docType'],
                    'QttyOfDocs': '{}/{}'.format(el['count'], el['verified']),
                    'count_verified': '{}/{}'.format(
                        el['count_verified'] + el['count_unverified'],
                        el['count_unverified']),
                    'qtty_plan_verified': '{}/{}'.format(
                        el['qtty_plan_verified'] + el['qtty_plan_unverified'],
                        el['qtty_plan_unverified'])
                },
                "height": "wrap_content",
                "color": '#FFFFFF',
                "start_screen": f"{next_screen_name}",
                "start_process": "",
                'key': el['docType']
            }

            tiles['tiles'][rows - 1].append(tile)

        self.hash_map.put('tiles', tiles, to_json=True)

    def on_input(self) -> None:
        if self.listener == 'ON_BACK_PRESSED':
            self.hash_map.put('FinishProcess', '')

    def on_post_start(self):
        pass

    def show(self):
        self.hash_map.show_screen(self.name)

    def _get_doc_tiles(self, settings_global):

        small_tile = {
            "type": "LinearLayout",
            "orientation": "vertical",
            "height": "wrap_content",
            "width": "match_parent",
            "autoSizeTextType": "uniform",
            "weight": "0",
            "Elements": [
                {
                    "type": "TextView",
                    "show_by_condition": "",
                    "Value": "@docName",
                    "NoRefresh": False,
                    "document_type": "",
                    "mask": "",
                    "Variable": "",
                    "TextSize": settings_global.get('titleDocTypeCardTextSize'),  # "25",
                    "TextColor": "#000000",
                    "TextBold": False,
                    "TextItalic": False,
                    "BackgroundColor": "",
                    "width": "match_parent",
                    "height": "wrap_content",
                    "weight": 0,
                    "gravity_horizontal": "center"
                },
                {
                    "type": "LinearLayout",
                    "orientation": "horizontal",
                    "height": "wrap_content",
                    "width": "match_parent",
                    "weight": "1",
                    "Elements": [
                        {
                            "type": "TextView",
                            "show_by_condition": "",
                            "Value": "@QttyOfDocs",
                            "NoRefresh": False,
                            "document_type": "",
                            "mask": "",
                            "Variable": "",
                            "TextSize": settings_global.get('DocTypeCardTextSize'),
                            "TextColor": "#333333",
                            "TextBold": False,
                            "TextItalic": False,
                            "BackgroundColor": "FFCC99",
                            "width": "wrap_content",
                            "height": "wrap_content",
                            "weight": 0
                        }
                    ]
                },
                {
                    "type": "LinearLayout",
                    "orientation": "horizontal",
                    "height": "wrap_content",
                    "width": "match_parent",
                    "weight": "1",
                    "Elements": [
                        {
                            "type": "TextView",
                            "show_by_condition": "",
                            "Value": "Строк: ",
                            "NoRefresh": False,
                            "document_type": "",
                            "mask": "",
                            "Variable": "",
                            "TextSize": settings_global.get('DocTypeCardTextSize'),  # "15",
                            "TextColor": "#333333",
                            "TextBold": False,
                            "TextItalic": False,
                            "BackgroundColor": "FFCC99",
                            "width": "wrap_content",
                            "height": "wrap_content",
                            "weight": 0
                        },
                        {
                            "type": "TextView",
                            "show_by_condition": "",
                            "Value": "@count_verified",
                            "NoRefresh": False,
                            "document_type": "",
                            "mask": "",
                            "Variable": "",
                            "TextSize": settings_global.get('DocTypeCardTextSize'),
                            "TextColor": "#333333",
                            "TextBold": False,
                            "TextItalic": False,
                            "BackgroundColor": "FFCC99",
                            "width": "wrap_content",
                            "height": "wrap_content",
                            "weight": 0
                        }
                    ]
                },
                {
                    "type": "LinearLayout",
                    "orientation": "horizontal",
                    "height": "wrap_content",
                    "width": "match_parent",
                    "weight": "1",
                    "Elements": [
                        {
                            "type": "TextView",
                            "show_by_condition": "",
                            "Value": "Товаров: ",
                            "NoRefresh": False,
                            "document_type": "",
                            "mask": "",
                            "Variable": "",
                            "TextSize": settings_global.get('DocTypeCardTextSize'),
                            "TextColor": "#333333",
                            "TextBold": False,
                            "TextItalic": False,
                            "BackgroundColor": "FFCC99",
                            "width": "wrap_content",
                            "height": "wrap_content",
                            "weight": 0
                        },
                        {
                            "type": "TextView",
                            "show_by_condition": "",
                            "Value": "@qtty_plan_verified",
                            "NoRefresh": False,
                            "document_type": "",
                            "mask": "",
                            "Variable": "",
                            "TextSize": settings_global.get('DocTypeCardTextSize'),
                            "TextColor": "#333333",
                            "TextBold": False,
                            "TextItalic": False,
                            "BackgroundColor": "FFCC99",
                            "width": "wrap_content",
                            "height": "wrap_content",
                            "weight": 0
                        }
                    ]
                }

            ]
        }

        return small_tile


class DocsListScreen(Screen):
    def __init__(self, hash_map: HashMap,  rs_settings):
        super().__init__(hash_map)
        self.listener = self.hash_map['listener']
        self.event = self.hash_map['event']
        self.rs_settings = rs_settings
        self.service = DocService()
        self.screen_values = {}

    def on_start(self) -> None:
        pass

    def on_input(self) -> None:
        pass

    def on_post_start(self):
        pass

    def show(self, args=None):
        self._validate_screen_values()
        self.hash_map.show_screen(self.screen_name, args)

    def _layout_action(self) -> None:
        layout_listener = self.hash_map['layout_listener']


        if layout_listener == 'Удалить':
            self.hash_map.show_dialog(
                listener='confirm_delete',
                title='Удалить документ с устройства?'
            )

    def _is_result_positive(self, listener) -> bool:
        return self.listener == listener and self.event == 'onResultPositive'

    def _get_doc_list_data(self, doc_type='') -> list:
        if doc_type and doc_type != 'Все':
            results = self.service.get_doc_view_data(doc_type)
        else:
            results = self.service.get_doc_view_data()

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

        return table_data

    def _get_selected_card(self):
        current_str = self.hash_map.get("selected_card_position")
        jlist = self.hash_map.get_json("docCards")
        selected_card = jlist['customcards']['cardsdata'][int(current_str)]

        return selected_card

    def _get_selected_card_put_data(self, put_data=None):
        card_data = self._get_selected_card()

        put_data = put_data or {}
        put_data['id_doc'] = card_data['key']
        put_data['doc_type'] = card_data['type']
        put_data['doc_n'] = card_data['number']
        put_data['doc_date'] = card_data['data']
        put_data['warehouse'] = card_data['warehouse']
        put_data['countragent'] = card_data['countragent']

        return put_data

    def _set_doc_verified(self, id_doc, value=True):
        service = DocService(id_doc)
        value = str(int(value))

        try:
            service.set_doc_value('verified', value)
        except Exception as e:
            self.hash_map.error_log(e.args[0])

    def _doc_delete(self, id_doc):
        service = DocService(id_doc)
        result = True

        try:
            service.delete_doc(id_doc)
        except Exception as e:
            self.hash_map.error_log(e.args[0])
            result = False

        return result


class DocsListGroupScanScreen(DocsListScreen):
    screen_name = 'Документы'
    process_name = 'Групповая обработка'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)

    def on_start(self):
        doc_types = self.service.get_doc_types()
        self.hash_map['doc_type_select'] = ';'.join(['Все'] + doc_types)

        doc_type = self.hash_map['selected_tile_key'] or self.hash_map['doc_type_click']

        if doc_type:
            list_data = self._get_doc_list_data(doc_type)
            self.hash_map['doc_type_click'] = doc_type
            self.hash_map['selected_tile_key'] = ''
        else:
            list_data = self._get_doc_list_data()

        doc_cards = self._get_doc_cards_view(list_data)
        self.hash_map['docCards'] = doc_cards.to_json()

    def on_input(self):
        if self.listener == "CardsClick":
            self.hash_map.show_dialog('Подтвердите действие')

        elif self.listener == 'LayoutAction':
            self._layout_action()

        elif self._is_result_positive('confirm_delete'):
            card_data = self.hash_map.get_json("card_data")
            id_doc = card_data['key']

            if self._doc_delete(id_doc):
                self.hash_map.toast('Документ успешно удалён')
                self.on_start()
            else:
                self.hash_map.toast('Ошибка удаления документа')

        elif self._is_result_positive('Подтвердите действие'):
            screen_name = 'Документ товары'
            screen = ScreensFactory.create_screen(
                screen_name,
                self.process_name,
                hash_map=self.hash_map,
                rs_settings=self.rs_settings)

            screen.show(args=self._get_selected_card_put_data())
            # self.hash_map.show_screen('Документ товары', )

        elif self.listener == 'ON_BACK_PRESSED':
            self.hash_map.show_screen('Плитки')

    def _get_doc_cards_view(self, table_data):
        title_text_size = self.rs_settings.get("TitleTextSize")
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')
        card_date_text_size = self.rs_settings.get('CardDateTextSize')

        doc_cards = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.TextView(
                        weight=8,
                        width='match_parent',
                        Value='@type',
                        gravity_horizontal='right',
                        TextSize=title_text_size,
                    ),
                    widgets.PopupMenuButton(
                        weight=2,
                        Value='Удалить',
                        Variable="menu_delete"
                    ),
                    orientation='horizontal',
                    width='match_parent'
                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@number',
                        TextBold=True,
                        TextSize=card_title_text_size
                    )
                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@countragent',
                        TextSize=card_date_text_size
                    ),
                    widgets.TextView(
                        Value='@warehouse',
                        TextSize=card_date_text_size
                    )
                ),
                width="match_parent"
            ),
            options=widgets.Options().options,
            cardsdata=table_data
        )

        return doc_cards


class DocDetailsScreen(Screen):
    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map)
        self.listener = self.hash_map['listener']
        self.event = self.hash_map['event']
        self.service = DocService()
        self.rs_settings = rs_settings

    def on_start(self) -> None:
        pass

    def on_input(self) -> None:
        pass

    def on_post_start(self):
        pass

    def show(self):
        self._validate_screen_values()
        self.hash_map.show_screen(self.screen_name)


class DocDetailsGroupScanScreen(DocDetailsScreen):
    screen_name = 'Документ товары'
    process_name = 'Групповая обработка'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.screen_values = {
            'id_doc': hash_map['id_doc'],
            'doc_type': hash_map['doc_type'],
            'doc_n': hash_map['doc_n'],
            'doc_date': hash_map['doc_date'],
            'warehouse': hash_map['warehouse'],
            'countragent': hash_map['countragent'],
            'test': None
        }

    def on_start(self) -> None:
        pass
    #     self.hash_map.put('SetTitle', self.hash_map["doc_type"])
    #     id_doc = self.hash_map['id_doc']
    #     use_series = self.rs_settings.get('use_series')
    #     use_properties = self.rs_settings.get('use_properties')
    #
    #     doc_detail_list = ui_form_data.get_doc_detail_cards(use_series, use_properties, rs_settings)
    #     doc_detail_list['customcards']['cardsdata'] = []
    #
    #     if hashMap.get('view') == "cards":
    #         hashMap.put('Show_card_view', "-1")
    #         # doc_detail_list = ui_form_data.get_doc_detail_cards(use_series, use_properties, rs_settings)
    #         doc_detail_list = ui_tables_structure.get_doc_detail_cards_mod(use_series, use_properties, rs_settings)
    #
    #         doc_detail_list['customcards']['cardsdata'] = []
    #     else:
    #         hashMap.put('Show_table_view', "-1")
    #         doc_detail_list = ui_tables_structure.get_doc_detail_table_head()
    #         doc_detail_list["customtable"]["tabledata"] = [{}]
    #
    #     jlist = json.loads(hashMap.get('docCards'))
    #
    #     elem_n = jlist['customcards']['cardsdata']
    #
    #     for el in elem_n:
    #         if el['key'] == id_doc:
    #             hashMap.put('add_mark_selection',
    #                         str(el['add_mark_selection'] if el['add_mark_selection'] else '0'))
    #     #    current_elem = jlist['customcards']['cardsdata'][int(current_str)-1]
    #
    #     query_text = ui_form_data.get_doc_details_query()
    #
    #     results = ui_global.get_query_result(query_text, (id_doc,), True)
    #     row_filter = True if hashMap.get('rows_filter') == '1' else False
    #     if results:
    #         hashMap.put('id_doc', str(results[0]['id_doc']))
    #         for record in results:
    #             pic = '#f02a' if record['IsDone'] != 0 else '#f00c'
    #             if record['qtty'] == 0 and record['qtty_plan'] == 0:
    #                 pic = ''
    #             if row_filter and record['qtty'] == record['qtty_plan']:
    #                 continue
    #             product_row = {
    #                 'key': str(record['id']),
    #                 'good_name': str(record['good_name']),
    #                 'id_good': str(record['id_good']),
    #                 'id_properties': str(record['id_properties']),
    #                 'properties_name': str(record['properties_name']),
    #                 'id_series': str(record['id_series']),
    #                 'series_name': str(record['series_name']),
    #                 'id_unit': str(record['id_unit']),
    #                 'units_name': str(record['units_name']),
    #                 'code_art': str(record['code']),
    #                 'art': str(record['art']),
    #                 'qtty': str(record['qtty'] if record['qtty'] is not None else 0),
    #                 'qtty_plan': str(record['qtty_plan'] if record['qtty_plan'] is not None else 0),
    #                 'price': str(record['price'] if record['price'] is not None else 0),
    #                 'price_name': str(record['price_name']),
    #                 'picture': pic
    #             }
    #
    #             good_info = ""
    #             if product_row['art'] != "None":
    #                 good_info += product_row['art'] + " "
    #             if product_row['properties_name'] != "None":
    #                 good_info += "(" + product_row['properties_name'] + ") "
    #             if product_row['series_name'] != "None":
    #                 good_info += product_row['series_name']
    #             if product_row['units_name'] != "None":
    #                 good_info += ", " + product_row['units_name']
    #             product_row['good_info'] = good_info
    #
    #             if hashMap.get('view') == "cards":
    #                 doc_detail_list['customcards']['cardsdata'].append(product_row)
    #             else:
    #                 product_row['_layout'] = ui_tables_structure.get_doc_detail_table_body_layout(use_series,
    #                                                                                               use_properties,
    #                                                                                               rs_settings)
    #
    #                 if float(product_row['qtty_plan']) > float(product_row['qtty']):
    #                     product_row['_layout']["BackgroundColor"] = "#FBE9E7"
    #
    #                 if hashMap.get("added_goods"):
    #                     added_goods_dict = json.loads(hashMap.get("added_goods"))
    #                     if str(results[0]['id_doc']) in added_goods_dict.keys():
    #                         if str(record['id_good']) in added_goods_dict[str(results[0]['id_doc'])][0]:
    #                             if str(record['id_properties']) in added_goods_dict[str(results[0]['id_doc'])][
    #                                 1] or not str(record['id_properties']):
    #                                 product_row['_layout']["BackgroundColor"] = "#F0F8FF"
    #
    #                 if float(product_row['qtty_plan']) == float(product_row['qtty']):
    #                     product_row['_layout']["BackgroundColor"] = "#FFFFFF"
    #
    #                 if float(product_row['qtty_plan']) < float(product_row['qtty']):
    #                     product_row['_layout']["BackgroundColor"] = "#FFF9C4"
    #
    #                 doc_detail_list['customtable']['tabledata'].append(product_row)
    #
    #         # Признак, have_qtty_plan ЕстьПланПОКОличеству  -  Истина когда сумма колонки Qtty_plan > 0
    #         # Признак  have_mark_plan "ЕстьПланКОдовМаркировки – Истина, когда количество строк табл. RS_docs_barcodes с заданным id_doc и is_plan  больше нуля.
    #         # Признак have_zero_plan "Есть строки товара в документе" Истина, когда есть заполненные строки товаров в документе
    #         # Признак "Контролировать"  - признак для документа, надо ли контролировать
    #
    #         qtext = ui_form_data.get_qtty_string_count_query()
    #         res = ui_global.get_query_result(qtext, {'id_doc': id_doc})
    #         if not res:
    #             have_qtty_plan = False
    #             have_zero_plan = False
    #         else:
    #             have_zero_plan = res[0][0] > 0  # В документе есть строки
    #             if have_zero_plan:
    #                 have_qtty_plan = res[0][1] > 0  # В документе есть колво план
    #             else:
    #                 have_qtty_plan = False
    #         # Есть ли в документе план по кодам маркировки
    #         qtext = ui_form_data.get_have_mark_codes_query()
    #         res = ui_global.get_query_result(qtext, {'id_doc': id_doc, 'is_plan': '1'})
    #         if not res:
    #             have_mark_plan = False
    #
    #         else:
    #             have_mark_plan = res[0][0] > 0
    #     else:
    #         have_qtty_plan = False
    #         have_zero_plan = False
    #         have_mark_plan = False
    #
    #     hashMap.put('have_qtty_plan', str(have_qtty_plan))
    #     hashMap.put('have_zero_plan', str(have_zero_plan))
    #     hashMap.put('have_mark_plan', str(have_mark_plan))
    #     res = ui_global.get_query_result('SELECT control from RS_docs  WHERE id_doc = ?', (id_doc,))
    #     # Есть ли контроль плана в документе
    #     if res:
    #         if res[0][0]:
    #             if res[0][0] in falseValueList:
    #                 control = 'False'
    #             else:
    #                 control = 'True'
    #
    #             # control = res[0][0] #'True'
    #         else:
    #             control = 'False'
    #     else:
    #         control = 'False'
    #
    #     hashMap.put('control', control)
    #     if hashMap.get("view") == "cards":
    #         hashMap.put("doc_goods_cards", json.dumps(doc_detail_list))
    #     else:
    #         hashMap.put("doc_goods_table", json.dumps(doc_detail_list))
    #
    # def on_start_old(self):
    #     id_doc = hash_map.get('id_doc')
    #
    #     use_series = rs_settings.get('use_series')
    #     use_properties = rs_settings.get('use_properties')
    #
    #     add_labels = [
    #         key for key, value in
    #         {'series_name': use_series, 'properties_name': use_properties}.items()
    #         if str(value) in ['1', 'true']
    #     ]
    #
    #     hash_map.put('use_properties', use_properties)
    #
    #     query_text = ui_form_data.get_doc_details_query()
    #     doc_details = ui_global.get_query_result(query_text, (id_doc,), True)
    #     cards_data = []
    #     have_zero_plan = False
    #
    #     if doc_details:
    #         for record in doc_details:
    #             pic = '#f02a' if record['IsDone'] != 0 else '#f00c'
    #             if record['qtty'] == 0 and record['qtty_plan'] == 0:
    #                 pic = ''
    #
    #             cards_data.append({
    #                 'key': str(record['id']),
    #                 'good_name': str(record['good_name']),
    #                 'id_good': str(record['id_good']),
    #                 'id_properties': str(record['id_properties']),
    #                 'properties_name': str(record['properties_name'] or ''),
    #                 'id_series': str(record['id_series']),
    #                 'series_name': str(record['series_name'] or ''),
    #                 'id_unit': str(record['id_unit']),
    #                 'units_name': str(record['units_name'] or ''),
    #                 'code_art': 'Код: ' + str(record['code']),
    #
    #                 'qtty': str(record['qtty'] if record['qtty'] is not None else 0),
    #                 'qtty_plan': str(record['qtty_plan'] if record['qtty_plan'] is not None else 0),
    #                 'price': str(record['price'] if record['price'] is not None else 0),
    #                 'price_name': str(record['price_name'] or ''),
    #                 'picture': pic
    #             })
    #             have_zero_plan = True
    #
    #     doc_goods = ui_form_data.get_doc_detail_cards_new(rs_settings, cards_data, add_labels=add_labels)
    #     hash_map.put("doc_goods_cards", doc_goods)
    #
    #     have_qtty_plan = sum([item['qtty_plan'] or 0 for item in doc_details]) > 0
    #
    #     qtext = ui_form_data.get_have_mark_codes_query()
    #     res = list(ui_global.get_query_result(qtext, {'id_doc': id_doc, 'is_plan': '1'}))
    #     have_mark_plan = res and res[0][0] > 0
    #
    #     res = list(ui_global.get_query_result('SELECT control from RS_docs  WHERE id_doc = ?', (id_doc,)))
    #     control = res and res[0][0] not in (0, '0', 'false', 'False', None)
    #
    #     hash_map.put('have_zero_plan', str(have_zero_plan))
    #     hash_map.put('have_qtty_plan', str(have_qtty_plan))
    #     hash_map.put('have_mark_plan', str(have_mark_plan))
    #     hash_map.put('control', str(control))

    def on_input(self) -> None:
        pass
        # listener = hash_map['listener']
        #
        # if listener == "CardsClick":
        #     pass
        # elif listener == "btn_barcodes":
        #     # hash_map.show_dialog('ВвестиШтрихкод')
        #     hash_map.put('ShowDialog', 'ВвестиШтрихкод')
        # elif listener == 'barcode' or (listener == 'ВвестиШтрихкод' and hash_map.get("event") == "onResultPositive"):
        #     doc = ui_global.Rs_doc()
        #     doc.id_doc = hash_map.get('id_doc')
        #
        #     if hash_map.get("event") == "onResultPositive":
        #         barcode = hash_map.get('fld_barcode')
        #     else:
        #         barcode = hash_map.get('barcode_camera')
        #
        #     if not barcode.strip():
        #         hash_map.show_dialog("ВвестиШтрихкод")
        #         return
        #
        #     have_qtty_plan = hash_map.get('have_qtty_plan')
        #     have_zero_plan = hash_map.get('have_zero_plan')
        #     have_mark_plan = hash_map.get('have_mark_plan')
        #     control = hash_map.get('control')
        #     res = doc.process_the_barcode(
        #         doc,
        #         barcode,
        #         eval(have_qtty_plan),
        #         eval(have_zero_plan),
        #         eval(control),
        #         eval(have_mark_plan),
        #         rs_settings.get('use_mark'))
        #     if res is None:
        #         hash_map.put('scanned_barcode', barcode)
        #         hash_map.put('ShowScreen', 'Ошибка сканера')
        #     elif res['Error']:
        #         if res['Error'] == 'AlreadyScanned':
        #             hash_map.put('barcode', json.dumps({'barcode': res['Barcode'], 'doc_info': res['doc_info']}))
        #             hash_map.put('ShowScreen', 'Удаление штрихкода')
        #         elif res['Error'] == 'QuantityPlanReached':
        #             hash_map.put('toast', res['Descr'])
        #         elif res['Error'] == 'Zero_plan_error':
        #             hash_map.put('toast', res['Descr'])
        #         else:
        #             hash_map.put('toast', res['Descr'])
        #     else:
        #         highlight_added_good(hash_map, barcode)
        #         hash_map.put('toast', 'Товар добавлен в документ')
        #         hash_map.put('barcode_scanned', 'true')
        #
        # elif listener in ['ON_BACK_PRESSED', 'BACK_BUTTON']:
        #     hash_map.put("ShowScreen", "Документы")


def on_post_start(self):
        pass


class ScreensFactory:
    screens = [
        DocsListGroupScanScreen,
        DocDetailsGroupScanScreen
    ]

    @staticmethod
    def create_screen(name, process, **kwargs):
        for item in ScreensFactory.screens:
            if getattr(item, 'screen_name') == name and getattr(item, 'process_name') == process:
                return item(**kwargs)
