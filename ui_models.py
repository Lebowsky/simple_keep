from abc import ABC, abstractmethod
import json

from ui_utils import HashMap, RsDoc
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
    def show(self, args=None):
        pass

    def toast(self, text):
        self.hash_map.toast(text)

    def __str__(self):
        return f'{self.process_name} / {self.screen_name}'

    def _validate_screen_values(self):
        for key, value in self.screen_values.items():
            if value is None:
                raise ValueError(f'Process: {self.process_name}, screen: {self.screen_name}.'
                                 f'For key {key} must be set value not None')


class Tiles(Screen):
    screen_name = 'Плитки'
    process_name = 'Групповая обработка'

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
        super().on_input()
        if self.listener == 'ON_BACK_PRESSED':
            self.hash_map.put('FinishProcess', '')

    def on_post_start(self):
        pass

    def show(self, args=None):
        self.hash_map.show_screen(self.name, args)

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
        super().on_input()

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
        super().on_input()
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
                screen_name=screen_name,
                process=self.process_name,
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

    def show(self, args=None):
        self.hash_map.show_screen(self.screen_name, args)
        self._validate_screen_values()


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
        }

    def on_start(self) -> None:
        self._set_visibility_on_start()
        self.hash_map.put('SetTitle', self.hash_map["doc_type"])
        id_doc = self.hash_map['id_doc']

        service = DocService()

        have_qtty_plan = False
        have_zero_plan = False
        have_mark_plan = False

        doc_details = service.get_doc_details_data(id_doc)
        table_data = [{}]

        if doc_details:
            for record in doc_details:
                pic = '#f02a' if record['IsDone'] != 0 else '#f00c'
                if record['qtty'] == 0 and record['qtty_plan'] == 0:
                    pic = ''

                product_row = {
                    'key': str(record['id']),
                    'good_name': str(record['good_name']),
                    'id_good': str(record['id_good']),
                    'id_properties': str(record['id_properties']),
                    'properties_name': str(record['properties_name'] or ''),
                    'id_series': str(record['id_series']),
                    'series_name': str(record['series_name'] or ''),
                    'id_unit': str(record['id_unit']),
                    'units_name': str(record['units_name'] or ''),
                    'code_art': 'Код: ' + str(record['code']),
                    'art': str(record['art']),
                    'qtty': str(record['qtty'] if record['qtty'] is not None else 0),
                    'qtty_plan': str(record['qtty_plan'] if record['qtty_plan'] is not None else 0),
                    'price': str(record['price'] if record['price'] is not None else 0),
                    'price_name': str(record['price_name'] or ''),
                    'picture': pic
                }

                props = [
                    '{} '.format(product_row['art']) if product_row['art'] else '',
                    '({}) }'.format(product_row['properties_name']) if product_row['properties_name'] else '',
                    '{}'.format(product_row['series_name']) if product_row['series_name'] else '',
                    ', {}'.format(product_row['units_name']) if product_row['units_name'] else ''
                ]
                product_row['good_info'] = ''.join(props)

                product_row['_layout'] = self._get_doc_table_row_view()
                self._set_background_row_color(product_row, id_doc)
                table_data.append(product_row)

            have_zero_plan = True
            have_qtty_plan = sum([item['qtty_plan'] for item in doc_details if item['qtty_plan']]) > 0

        self.hash_map['have_qtty_plan'] = have_qtty_plan
        self.hash_map['have_zero_plan'] = have_zero_plan
        self.hash_map['have_mark_plan'] = have_mark_plan

        control = service.get_doc_value('control', id_doc) not in (0, '0', 'false', 'False', None)
        self.hash_map['control'] = control

        table_view = self._get_doc_table_view(table_data=table_data)
        self.hash_map.put("doc_goods_table", table_view.to_json())

    def on_input(self) -> None:
        super().on_input()
        listener = self.hash_map['listener']
        id_doc = self.hash_map.get('id_doc')

        if listener == "CardsClick":
            pass
        elif listener == 'barcode':
            doc = RsDoc(id_doc)
            barcode = self.hash_map.get('barcode_camera')

            have_qtty_plan = self.hash_map.get_bool('have_qtty_plan')
            have_zero_plan = self.hash_map.get_bool('have_zero_plan')
            have_mark_plan = self.hash_map.get_bool('have_mark_plan')
            control = self.hash_map.get_bool('control')

            res = doc.process_the_barcode(
                barcode,
                have_qtty_plan,
                have_zero_plan,
                control,
                have_mark_plan,
                use_mark_setting=self.rs_settings.get('use_mark'))
            if res is None:
                self.hash_map.put('scanned_barcode', barcode)
                self.hash_map.show_screen('Ошибка сканера')
            elif res['Error']:
                if res['Error'] == 'AlreadyScanned':
                    self.hash_map.put('barcode', json.dumps({'barcode': res['Barcode'], 'doc_info': res['doc_info']}))
                    self.hash_map.show_screen('Удаление штрихкода')
                elif res['Error'] == 'QuantityPlanReached':
                    self.hash_map.toast('toast', res['Descr'])
                elif res['Error'] == 'Zero_plan_error':
                    self.hash_map.toast(res['Descr'])
                else:
                    self.hash_map.toast(res['Descr'])
            else:
                self._add_scanned_row(id_doc, res.get('key'))
                self.hash_map.toast('Товар добавлен в документ')
                self.hash_map.put('barcode_scanned', 'true')

        elif listener in ['ON_BACK_PRESSED', 'BACK_BUTTON']:
            self.hash_map.put("ShowScreen", "Документы")

    def _get_doc_table_view(self, table_data):
        table_view = widgets.CustomTable(
            widgets.LinearLayout(
                self.LinearLayout(
                    self.TextView('Название'),
                    weight=3
                ),
                self.LinearLayout(
                    self.TextView('План'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('Факт'),
                    weight=1
                ),
                orientation='horizontal',
                height="match_parent",
                width="match_parent",
                BackgroundColor='#FFFFFF'
            ),
            options=widgets.Options().options,
            tabledata=table_data
        )

        return table_view

    def _get_doc_table_row_view(self):
        row_view = widgets.LinearLayout(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.LinearLayout(
                        self.TextView('@good_name'),
                        widgets.TextView(
                            Value='@good_info',
                            TextSize=15,
                            width='match_parent'
                        ),
                        width='match_parent',
                    ),
                    width='match_parent',
                    orientation='horizontal',
                    StrokeWidth=1
                ),
                width='match_parent',
                weight=3,
                StrokeWidth=1
            ),
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@qtty_plan',
                    TextSize=15,
                    width='match_parent',
                ),
                width='match_parent',
                height='match_parent',
                weight=1,
                StrokeWidth=1
            ),
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@qtty',
                    TextSize=15,
                    width='match_parent'
                ),
                width='match_parent',
                height='match_parent',
                weight=1,
                StrokeWidth=1
            ),
            orientation='horizontal',
            width='match_parent',
            BackgroundColor='#FFFFFF'
        )

        return row_view

    def _set_visibility_on_start(self):
        _vars = ['warehouse', 'countragent']

        for v in _vars:
            name = f'Show_{v}'
            self.hash_map[name] = '1' if self.hash_map[v] else '-1'

    def _set_background_row_color(self, product_row, id_doc):
        background_color = '#FFFFFF'
        qtty, qtty_plan = float(product_row['qtty']), float(product_row['qtty_plan'])

        if qtty_plan > qtty:
            if self._added_goods_has_key(self.hash_map.get_json('added_goods'), id_doc, product_row['key']):
                background_color = '#F0F8FF'
            else:
                background_color = "#FBE9E7"

        elif qtty_plan < qtty:
            background_color = "#FFF9C4"

        product_row['_layout'].BackgroundColor = background_color

    def _added_goods_has_key(self, added_goods, id_doc, key):
        result = False
        if added_goods:
            added_goods_doc = added_goods.get(id_doc, [])
            result = str(key) in [str(item) for item in added_goods_doc]

        return result

    def _add_scanned_row(self, id_doc, row_key):
        if not row_key:
            raise ValueError(f'Row key must be set not {row_key}')

        added_goods = self.hash_map.get_json('added_goods') or {}
        added_goods_doc = added_goods.get(id_doc, [row_key])
        if row_key not in added_goods_doc:
            added_goods_doc.append(row_key)

        added_goods[id_doc] = added_goods_doc

        self.hash_map.put('added_goods', added_goods, to_json=True)


    class TextView(widgets.TextView):
        def __init__(self, value):
            super().__init__()
            self.TextSize = '15'
            self.TextBold = True
            self.width = 'match_parent'
            self.Value = value

    class LinearLayout(widgets.LinearLayout):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.orientation = 'horizontal'
            self.height = "match_parent"
            self.width = "match_parent"
            self.StrokeWidth = 1


class ScreensFactory:
    screens = [
        Tiles,
        DocsListGroupScanScreen,
        DocDetailsGroupScanScreen
    ]

    @staticmethod
    def create_screen(screen_name=None, process=None, **kwargs):
        if not screen_name:
            screen_name = kwargs['hash_map'].get_current_screen()
        if not process:
            process = kwargs['hash_map'].get_current_process()

        for item in ScreensFactory.screens:
            if getattr(item, 'screen_name') == screen_name and getattr(item, 'process_name') == process:
                return item(**kwargs)

