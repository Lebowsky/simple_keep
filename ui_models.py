from abc import ABC, abstractmethod

from ui_utils import HashMap
from db_services import DocService
import widgets


class Screen(ABC):
    def __init__(self, hash_map: HashMap):
        self.hash_map: HashMap = hash_map
        self.name: str

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


class DocsListScreen(Screen):
    def __init__(self, hash_map: HashMap,  rs_settings):
        super().__init__(hash_map)
        self.listener = self.hash_map['listener']
        self.event = self.hash_map['event']
        self.rs_settings = rs_settings
        self.service = DocService()
        self.name = ''
        self.screen_values = {}

    def on_start(self) -> None:
        pass

    def on_input(self) -> None:
        pass

    def on_post_start(self):
        pass

    def show(self):
        self._validate_screen_values()
        self.hash_map.show_screen(self.name)

    def _validate_screen_values(self):
        for key, value in self.screen_values.items():
            if value is None:
                raise ValueError(f'For key {key} must be set value not None')

    def _layout_action(self) -> None:
        layout_listener = self.hash_map['layout_listener']
        card_data = self.hash_map.get_json("card_data")

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
    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.name = 'Документы'
        self.screen_values = {
            'docCards': hash_map['docCards'],
            'doc_type_select': hash_map['doc_type_select']
        }

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
            id_doc = ''
            if self._doc_delete(id_doc):
                self.hash_map.toast('Документ успешно удалён')
                self.hash_map.refresh_screen()
            else:
                self.hash_map.toast('Ошибка удаления документа')

        elif self._is_result_positive('Подтвердите действие'):
            self.hash_map.show_screen('Документ товары', self._get_selected_card_put_data())

        elif self.listener == 'ON_BACK_PRESSED':
            self.hash_map.show_screen('ShowScreen', 'Плитки')

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


class Tiles(Screen):
    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map)
        self.listener = self.hash_map['listener']
        self.rs_settings = rs_settings
        self.name = 'Плитки'
        self.db_service = DocService()

    def on_start(self) -> None:
        small_tile = self._get_doc_tiles(self.rs_settings)
        res = self.db_service.get_docs_stat()

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
                "start_screen": "Документы",
                "start_process": "",
                'key': el['docType']
            }

            tiles['tiles'][rows - 1].append(tile)

        # hashMap.put("tiles", json.dumps(x, ensure_ascii=False).encode('utf8').decode())
        self.hash_map.put('tiles', to_json=True)

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


