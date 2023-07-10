from abc import ABC, abstractmethod
import json
import os

import db_services
import hs_services
from ui_utils import HashMap, RsDoc
from db_services import DocService, ErrorService
from hs_services import HsService
import http_exchange
from http_exchange import post_changes_to_server
from PIL import Image
import widgets
import ui_global


class Screen(ABC):
    screen_name: str
    process_name: str

    def __init__(self, hash_map: HashMap, rs_settings):
        self.hash_map: HashMap = hash_map
        self.screen_values = {}
        self.rs_settings = rs_settings
        self.listener = self.hash_map['listener']
        self.event: str = self.hash_map['event']

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

    def _is_result_positive(self, listener) -> bool:
        return self.listener == listener and self.event == 'onResultPositive'

    def __str__(self):
        return f'{self.process_name} / {self.screen_name}'

    def _validate_screen_values(self):
        for key, value in self.screen_values.items():
            if value is None:
                raise ValueError(f'Process: {self.process_name}, screen: {self.screen_name}.'
                                 f'For key {key} must be set value not None')

    def get_http_settings(self):
        http_settings = {
            'url': self.rs_settings.get("URL"),
            'user': self.rs_settings.get('USER'),
            'pass': self.rs_settings.get('PASS'),
            'device_model': self.hash_map['DEVICE_MODEL'],
            'android_id': self.hash_map['ANDROID_ID'],
            'user_name': self.rs_settings.get('user_name')}
        return http_settings

    def put_notification(self, text, title=None):
        self.hash_map.notification(text, title)


# ==================== Tiles =============================

class Tiles(Screen):
    def on_start(self):
        pass

    def on_input(self):
        pass

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _get_tile_row(self, layout, tile_element, start_screen='Документы'):
        tile = {
            "layout": layout,
            "data": self._get_tile_data(tile_element),
            "height": "wrap_content",
            "color": '#FFFFFF',
            "start_screen": f"{start_screen}",
            "start_process": "",
            'key': tile_element['docType']
        }
        return tile

    @staticmethod
    def _get_tile_data(tile_element):
        return {
            "docName": tile_element['docType'],
            'QttyOfDocs': '{}/{}'.format(tile_element['count'], tile_element['verified']),
            'count_verified': '{}/{}'.format(
                tile_element['count_verified'] + tile_element['count_unverified'],
                tile_element['count_unverified']),
            'qtty_plan_verified': '{}/{}'.format(
                tile_element['qtty_plan_verified'] + tile_element['qtty_plan_unverified'],
                tile_element['qtty_plan_unverified'])
        }

    def _get_tile_view(self) -> widgets.LinearLayout:
        tiles_view = widgets.LinearLayout(
            widgets.TextView(
                Value='@docName',
                TextSize=self.rs_settings.get('titleDocTypeCardTextSize'),
                TextColor='#000000',
                width='match_parent',
                weight=0
            ),
            widgets.LinearLayout(
                self.TextView('@QttyOfDocs', self.rs_settings),
                orientation='horizontal',
                width="match_parent",
                weight=1
            ),
            widgets.LinearLayout(
                self.TextView('Строк: ', self.rs_settings),
                self.TextView('@count_verified', self.rs_settings),
                orientation='horizontal',
                width="match_parent",
                weight=1
            ),
            widgets.LinearLayout(
                self.TextView('Товаров: ', self.rs_settings),
                self.TextView('@qtty_plan_verified', self.rs_settings),
                orientation='horizontal',
                width="match_parent",
                weight=1
            ),
            width='match_parent',
            autoSizeTextType='uniform',
            weight=0
        )

        return tiles_view

    class TextView(widgets.TextView):
        def __init__(self, value, rs_settings):
            super().__init__()
            self.TextSize = rs_settings.get('DocTypeCardTextSize')
            self.TextColor = '#333333'
            self.BackgroundColor = 'FFCC99'
            self.weight = 0
            self.Value = value


class GroupScanTiles(Tiles):
    screen_name = 'Плитки'
    process_name = 'Групповая обработка'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.db_service = DocService()
        self.screen_name = self.hash_map.get_current_screen()
        self.process_name = self.hash_map.get_current_process()

    def on_start(self) -> None:
        if not self._check_connection():
            tiles = self._get_message_tile("Отсутствует соединение с сервером", text_color="#ff0000")
            self.hash_map.put('tiles', tiles, to_json=True)
            self.hash_map.refresh_screen()
            return
        data = self.db_service.get_docs_stat()
        if data:
            layout = json.loads(self._get_tile_view().to_json())

            tiles_list = [self._get_tile_row(layout, item) for item in data]

            # split list by two element in row
            count_row_elements = 2
            tiles = {
                'tiles': [
                    tiles_list[i:i + count_row_elements]
                    for i in range(0, len(tiles_list), count_row_elements)
                ],
                'background_color': '#f5f5f5'

            }
        else:
            tiles = self._get_message_tile("Нет загруженных документов")

        self.hash_map.put('tiles', tiles, to_json=True)
        self.hash_map.refresh_screen()

    def on_input(self) -> None:
        super().on_input()
        if self.listener == 'ON_BACK_PRESSED':
            self.hash_map.put('FinishProcess', '')

    def on_post_start(self):
        pass

    def show(self, args=None):
        self.hash_map.show_screen(self.screen_name, args)

    def _check_connection(self):
        hs_service = hs_services.HsService(self.get_http_settings())
        try:
            hs_service.communication_test(timeout=1)
            answer = hs_service.http_answer
        except Exception as e:
            answer = hs_service.HttpAnswer(
                error=True,
                error_text=str(e.args[0]),
                status_code=404,
                url=hs_service.url)

        return not answer.error

    def _get_message_tile(self, message, text_color='#000000'):
        tile_view = widgets.LinearLayout(
            widgets.TextView(
                Value='@no_data',
                TextSize=self.rs_settings.get('titleDocTypeCardTextSize'),
                TextColor=text_color,
                height='match_parent',
                width='match_parent',
                weight=0,
                gravity_horizontal="center",
                gravity_vertical="center",
                StrokeWidth=0,
                BackgroundColor="#ffffff",
                Padding=0

            ),
            width='match_parent',
            autoSizeTextType='uniform',
            weight=0,
            height='match_parent',
            gravity_horizontal="center",
            gravity_vertical="center",
            StrokeWidth=3,
            BackgroundColor="#ffffff",
            Padding=0
        )

        layout = json.loads(tile_view.to_json())

        tiles_list = [{
            "layout": layout,
            "data": {"no_data": message},
            "height": "wrap_content",
            "color": '#ffffff',
            "start_screen": "",
            "start_process": "",
            'StrokeWidth': '',
        }]

        count_row_elements = 1
        tiles = {
            'tiles': [tiles_list],
            'background_color': '#ffffff',
            'StrokeWidth': '',
            'height': ''

        }

        return tiles


class DocumentsTiles(GroupScanTiles):
    screen_name = 'Плитки'
    process_name = 'Документы'

    def _check_connection(self):
        return True


# ^^^^^^^^^^^^^^^^^^^^^ Tiles ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== DocsList =============================


class DocsListScreen(Screen):
    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = DocService()
        self.screen_values = {}

    def on_start(self) -> None:
        doc_types = self.service.get_doc_types()
        self.hash_map['doc_type_select'] = ';'.join(['Все'] + doc_types)
        self.hash_map['doc_status_select'] = 'Все;К выполнению;Выгружен;К выгрузке'

        doc_type = self.hash_map['selected_tile_key'] or self.hash_map['doc_type_click']
        doc_status = self.hash_map['selected_doc_status']
        self.hash_map['doc_type_click'] = doc_type
        self.hash_map['selected_tile_key'] = ''
        list_data = self._get_doc_list_data(doc_type, doc_status)
        if self.process_name == "Групповая обработка":
            doc_cards = self._get_doc_cards_view(list_data, 'Удалить')
        # elif self.process_name == "Документы":     #******* При таком выражении существует вероятность что doc_cards никогдла не заполнится
        else:
            doc_cards = self._get_doc_cards_view(list_data,
                                                 popup_menu_data='Удалить;Очистить данные пересчета;Отправить повторно')
        self.hash_map['docCards'] = doc_cards.to_json()

    def on_input(self) -> None:
        super().on_input()
        if self.listener == "doc_status_click":
            self.hash_map['selected_doc_status'] = self.hash_map["doc_status_click"]

        elif self.listener == 'LayoutAction':
            self._layout_action()

        elif self._is_result_positive('confirm_delete'):
            self.confirm_delete_doc_listener()

        elif self.listener == 'ON_BACK_PRESSED':
            self.hash_map.show_screen('Плитки')

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
        elif layout_listener == 'Очистить данные пересчета':
            self.hash_map.show_dialog(
                listener='confirm_clear_barcode_data',
                title='Очистить данные пересчета?'
            )
        elif layout_listener == 'Отправить повторно':
            self.hash_map.show_dialog(
                listener='confirm_resend_doc',
                title='Отправить документ повторно?'
            )

    def _get_doc_list_data(self, doc_type='', doc_status='') -> list:
        results = self.service.get_doc_view_data(doc_type, doc_status)
        table_data = []

        for record in results:
            doc_status = ''

            if record['verified'] and record['sent']:
                doc_status = 'Выгружен'
            elif record['verified']:
                doc_status = 'К выгрузке'
            elif not (record['verified'] and record['sent']):
                doc_status = 'К выполнению'

            table_data.append({
                'key': record['id_doc'],
                'type': record['doc_type'],
                'number': record['doc_n'],
                'data': record['doc_date'],
                'warehouse': record['RS_warehouse'],
                'countragent': record['RS_countragent'],
                'add_mark_selection': record['add_mark_selection'],
                'status': doc_status
            })

        return table_data

    def _get_doc_cards_view(self, table_data, popup_menu_data):
        title_text_size = self.rs_settings.get("TitleTextSize")
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')
        card_date_text_size = self.rs_settings.get('CardDateTextSize')

        doc_cards = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@status',
                        width='match_parent',
                        gravity_horizontal='left',
                        weight=2
                    ),
                    widgets.TextView(
                        Value='@type',
                        TextSize=title_text_size,
                    ),
                    widgets.PopupMenuButton(
                        Value=popup_menu_data,
                        Variable="menu_delete",
                    ),

                    orientation='horizontal',
                    width='match_parent',

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

    def _get_docs_count(self, doc_type=''):
        doc_type = '' if not doc_type or doc_type == 'Все' else doc_type
        return self.service.get_docs_count(doc_type)

    def _clear_barcode_data(self, id_doc):
        return self.service.clear_barcode_data(id_doc)

    def confirm_delete_doc_listener(self):
        card_data = self.hash_map.get_json("card_data")
        id_doc = card_data['key']
        doc_type = self.hash_map['doc_type_click']

        if self._doc_delete(id_doc):
            docs_count = self._get_docs_count(doc_type=doc_type)
            self.hash_map.toast('Документ успешно удалён')
            if docs_count:
                self.on_start()
            else:
                self.hash_map.show_screen('Плитки')
        else:
            self.hash_map.toast('Ошибка удаления документа')


class GroupScanDocsListScreen(DocsListScreen):
    screen_name = 'Документы'
    process_name = 'Групповая обработка'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)

    def on_start(self):
        super().on_start()

    def on_input(self):
        super().on_input()
        if self.listener == "CardsClick":
            self.hash_map.show_dialog('Подтвердите действие')
            selected_card_key = self.hash_map['selected_card_key']
            self.hash_map['id_doc'] = selected_card_key

        elif self._is_result_positive('Подтвердите действие'):
            id_doc = self.hash_map['id_doc']
            self.service.doc_id = id_doc
            self.service.set_doc_value('verified', 1)

            screen_name = 'Документ товары'
            screen = ScreensFactory.create_screen(
                screen_name=screen_name,
                process=self.process_name,
                hash_map=self.hash_map,
                rs_settings=self.rs_settings)

            screen.show(args=self._get_selected_card_put_data())


class DocumentsDocsListScreen(DocsListScreen):
    screen_name = 'Документы'
    process_name = 'Документы'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service.docs_table_name = 'RS_docs'

    def on_start(self):
        super().on_start()

    def on_input(self):
        super().on_input()
        if self.listener == "CardsClick":
            id_doc = self.get_id_doc()
            self.hash_map['id_doc'] = id_doc
            self.service.doc_id = id_doc

            screen_name = 'Документ товары'
            screen = ScreensFactory.create_screen(
                screen_name=screen_name,
                process=self.process_name,
                hash_map=self.hash_map,
                rs_settings=self.rs_settings)

            screen.show(args=self._get_selected_card_put_data())

        elif self._is_result_positive('confirm_clear_barcode_data'):
            id_doc = self.get_id_doc()
            res = self._clear_barcode_data(id_doc)
            if res.get('result'):
                self.toast('Данные пересчета и маркировки очищены')
            else:
                self.toast('При очистке данных пересчета возникла ошибка.')
                self.hash_map.error_log(res.get('error'))

        elif self._is_result_positive('confirm_resend_doc'):
            id_doc = self.get_id_doc()
            http_params = self.get_http_settings()
            answer = post_changes_to_server(f"'{id_doc}'", http_params)
            if answer.get('Error') is not None:
                ui_global.write_error_on_log(f'Ошибка повторной отправки документа {self.get_doc_number()}: '
                                             f'{str(answer.get("Error"))}')
                self.put_notification(text=f'Ошибка при отправке документа {self.get_doc_number()}, '
                                           f'подробнее в логе ошибок.')
                self.toast('Не удалось отправить документ повторно')
            else:
                self.service.doc_id = id_doc
                self.service.set_doc_value('sent', 1)
                self.toast('Документ отправлен повторно')

    def get_id_doc(self):
        card_data = self.hash_map.get_json("card_data") or {}
        id_doc = card_data.get('key') or self.hash_map['selected_card_key']
        return id_doc

    def get_doc_number(self):
        card_data = self.hash_map.get_json("card_data") or {}
        doc_number = card_data.get('number')
        return doc_number


# ^^^^^^^^^^^^^^^^^^^^^ DocsList ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== DocDetails =============================


class DocDetailsScreen(Screen):
    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.rs_settings = rs_settings
        self.id_doc = self.hash_map['id_doc']
        self.service = DocService(self.id_doc)

    def on_start(self) -> None:
        pass

    def on_input(self) -> None:
        pass

    def on_post_start(self):
        pass

    def show(self, args=None):
        self.hash_map.show_screen(self.screen_name, args)
        self._validate_screen_values()

    def _on_start(self):
        self._set_visibility_on_start()
        self.hash_map.put('SetTitle', self.hash_map["doc_type"])

        have_qtty_plan = False
        have_zero_plan = False
        have_mark_plan = False

        doc_details = self._get_doc_details_data()
        table_data = self._prepare_table_data(doc_details)
        table_view = self._get_doc_table_view(table_data=table_data)

        if self.hash_map.get_bool('highlight'):
            self.hash_map.put('highlight', False)
            # self.enable_highlight(table_view.customtable)
            # self.hash_map.run_event_async('highlight_scanned_item')

        if doc_details:
            self.hash_map['table_lines_qtty'] = len(doc_details)
            have_zero_plan = True
            have_qtty_plan = sum([item['qtty_plan'] for item in doc_details if item['qtty_plan']]) > 0

        self.hash_map['have_qtty_plan'] = have_qtty_plan
        self.hash_map['have_zero_plan'] = have_zero_plan
        self.hash_map['have_mark_plan'] = have_mark_plan

        control = self.service.get_doc_value('control', self.id_doc) not in (0, '0', 'false', 'False', None)
        self.hash_map['control'] = control

        self.hash_map.put("doc_goods_table", table_view.to_json())

    def _barcode_scanned(self):
        id_doc = self.hash_map.get('id_doc')
        doc = RsDoc(id_doc)
        if self.hash_map.get("event") == "onResultPositive":
            barcode = self.hash_map.get('fld_barcode')
        else:
            barcode = self.hash_map.get('barcode_camera')

        if not barcode:
            return

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
            self.hash_map.put('beep_duration ', self.rs_settings.get('beep_duration'))
            self.hash_map.put("beep", self.rs_settings.get('signal_num'))
            if res['Error'] == 'AlreadyScanned':
                self.hash_map.put('barcode', json.dumps({'barcode': res['Barcode'], 'doc_info': res['doc_info']}))
                self.hash_map.show_screen('Удаление штрихкода')
            elif res['Error'] == 'QuantityPlanReached':
                self.hash_map.put('Error_description', 'Количество план в документе превышено')
                self.hash_map.show_screen('Ошибка превышения плана')
                self.hash_map.show_dialog(listener='Ошибка превышения плана',
                                          title='Количество план в документе превышено')
                # self.hash_map.toast('toast', res['Descr'])
            elif res['Error'] == 'Zero_plan_error':
                self.hash_map.toast(res['Descr'])
            else:
                self.hash_map.toast(res['Descr'])
        else:
            # self.hash_map.toast('Товар добавлен в документ')
            self.hash_map.put('highlight', True)
            self.hash_map.put('barcode_scanned', True)
        return res

    def _set_visibility_on_start(self):
        _vars = ['warehouse', 'countragent']

        for v in _vars:
            name = f'Show_{v}'
            self.hash_map[name] = '1' if self.hash_map[v] else '-1'
        # TODO rework this
        if self.rs_settings.get('allow_fact_input') == 'true':
            self.hash_map.put("Show_fact_qtty_input", "1")
            self.hash_map.put("Show_fact_qtty_note", "-1")
        else:
            self.hash_map.put("Show_fact_qtty_input", "-1")
            self.hash_map.put("Show_fact_qtty_note", "1")

    def _get_doc_details_data(self):
        return self.service.get_doc_details_data(self.id_doc)

    def _prepare_table_data(self, doc_details):
        table_data = [{}]
        row_filter = self.hash_map.get_bool('rows_filter')

        for record in doc_details:
            if row_filter and record['qtty'] == record['qtty_plan']:
                continue

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
                'price': str(record['price'] if record['price'] is not None else 0),
                'price_name': str(record['price_name'] or ''),
                'picture': pic,
            }

            props = [
                '{} '.format(product_row['art']) if product_row['art'] else '',
                '({}) '.format(product_row['properties_name']) if product_row['properties_name'] else '',
                '{}'.format(product_row['series_name']) if product_row['series_name'] else '',
                ', {}'.format(product_row['units_name']) if product_row['units_name'] else '',
            ]
            product_row['good_info'] = ''.join(props)
            if record['qtty'] is not None:
                product_row['qtty'] = str(int(record['qtty']) if record['qtty'].is_integer() else record['qtty'])
            else:
                product_row['qtty'] = "0"
            if record['qtty_plan'] is not None:
                product_row['qtty_plan'] = str(int(record['qtty_plan']) if record['qtty_plan'].is_integer()
                                               else record['qtty_plan'])
            else:
                product_row['qtty_plan'] = "0"

            product_row['_layout'] = self._get_doc_table_row_view()
            self._set_background_row_color(product_row)

            if self._added_goods_has_key(product_row['key']):
                table_data.insert(1, product_row)
            else:
                table_data.append(product_row)

        return table_data

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

    def _set_background_row_color(self, product_row):
        background_color = '#FFFFFF'
        qtty, qtty_plan = float(product_row['qtty']), float(product_row['qtty_plan'])

        if qtty_plan > qtty:
            background_color = "#FBE9E7"

        elif qtty_plan < qtty:
            background_color = "#FFF9C4"

        product_row['_layout'].BackgroundColor = background_color

    def _added_goods_has_key(self, key):
        added_goods = self.hash_map.get_json('added_goods')
        result = False

        if added_goods:
            added_goods_doc = added_goods.get(self.id_doc, [])
            result = str(key) in [str(item) for item in added_goods_doc]
            self.toast(result)

        return result

    @staticmethod
    def enable_highlight(customtable):
        customtable['tabledata'][1]['_layout'].BackgroundColor = '#F0F8FF'

    def disable_highlight(self):
        self._on_start()
        self.hash_map.refresh_screen()

    def _fill_none_values(self, data, keys, default=''):
        none_list = [None, 'None']
        for key in keys:
            data[key] = default if data[key] in none_list else data[key]

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


class GroupScanDocDetailsScreen(DocDetailsScreen):
    screen_name = 'Документ товары'
    process_name = 'Групповая обработка'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.hs_service = hs_services.HsService(self.get_http_settings())
        self.screen_values = {
            'id_doc': hash_map['id_doc'],
            'doc_type': hash_map['doc_type'],
            'doc_n': hash_map['doc_n'],
            'doc_date': hash_map['doc_date'],
            'warehouse': hash_map['warehouse'],
            'countragent': hash_map['countragent'],
        }

    def on_start(self) -> None:
        super()._on_start()

    def on_input(self) -> None:
        super().on_input()
        listener = self.hash_map['listener']

        if listener == "CardsClick":
            pass

        elif listener == 'barcode':
            self._run_progress_barcode_scanning()

        elif self._is_result_positive('ВвестиШтрихкод'):
            self._update_document_data()
            self._barcode_scanned()
            self.hash_map.run_event_async('doc_details_barcode_scanned')

        elif listener == 'btn_barcodes':
            self.hash_map.show_dialog('ВвестиШтрихкод')

        elif listener in ['ON_BACK_PRESSED', 'BACK_BUTTON']:
            self.hash_map.put("ShowScreen", "Документы")

        elif listener == 'btn_rows_filter_on':
            self.hash_map.put('rows_filter', '1')
            self.hash_map.refresh_screen()

        elif listener == 'btn_rows_filter_off':
            self.hash_map.remove('rows_filter')
            self.hash_map.refresh_screen()

    def _run_progress_barcode_scanning(self):
        self.hash_map.run_event_progress('doc_details_before_process_barcode')

    def before_process_barcode(self):
        if self._check_connection():
            self._update_document_data()
            self._barcode_scanned()
            self.post_barcode_scanned(self.get_http_settings())
            # self.hash_map.run_event_async('doc_details_barcode_scanned')
        else:
            self.hash_map.beep('70')
            self.hash_map.show_dialog('Отсутствует соединение с сервером')

    def _update_document_data(self):
        docs_data = self._get_update_current_doc_data()
        if docs_data:
            try:
                self.service.update_data_from_json(docs_data)
            except Exception as e:
                self.service.write_error_on_log(f'Ошибка записи документа:  {e}')

    def _get_update_current_doc_data(self):
        hs_service = HsService(self.get_http_settings())
        hs_service.get_data()
        answer = hs_service.http_answer

        if answer.unauthorized:
            self.hash_map.toast('Ошибка авторизации сервера 1С')
        elif answer.forbidden:
            self.hash_map.notification(answer.error_text, title='Ошибка обмена')
            self.hash_map.toast(answer.error_text)
        elif answer.error:
            self.service.write_error_on_log(f'Ошибка загрузки документа:  {answer.error_text}')
        else:
            return answer

    def post_barcode_scanned(self, http_settings):
        if self.hash_map.get_bool('barcode_scanned'):
            answer = None
            try:
                answer = self._post_goods_to_server()
            except Exception as e:
                self.service.write_error_on_log(e.args[0])

            if answer and answer.get('Error') is not None:
                self.hash_map.error_log(answer.get('Error'))

            doc_details = self._get_doc_details_data()
            table_data = self._prepare_table_data(doc_details)
            table_view = self._get_doc_table_view(table_data=table_data)
            self.hash_map.put("doc_goods_table", table_view.to_json())
            self.hash_map.refresh_screen()

    def _post_goods_to_server(self):
        res = self.service.get_last_edited_goods(to_json=False)
        hs_service = HsService(self.get_http_settings())

        if isinstance(res, dict) and res.get('Error'):
            answer = {'empty': True, 'Error': res.get('Error')}
            return answer
        elif res:
            hs_service.send_documents(res)
            answer = hs_service.http_answer
            if answer.error:
                self.service.write_error_on_log(answer.error_text)
            else:
                try:
                    self.service.update_sent_data(res)
                except Exception as e:
                    self.service.write_error_on_log(e.args[0])

        # пока что отключил дополнительный get-запрос, проверяем производительность

        # docs_data = hs_service.get_data()
        #
        # if docs_data.get('data'):
        #     try:
        #         self.service.update_data_from_json(docs_data['data'])
        #     except Exception as e:
        #         self.service.write_error_on_log(e.args[0])

    def _check_connection(self):
        try:
            self.hs_service.communication_test(timeout=1)
            answer = self.hs_service.http_answer
        except Exception as e:
            answer = self.hs_service.HttpAnswer(
                error=True,
                error_text=str(e.args[0]),
                status_code=404,
                url=self.hs_service.url)

        return not answer.error


class DocumentsDocDetailScreen(DocDetailsScreen):
    screen_name = 'Документ товары'
    process_name = 'Документы'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)

    def on_start(self) -> None:
        super()._on_start()

    def on_input(self) -> None:
        super().on_input()
        listener = self.hash_map['listener']
        id_doc = self.hash_map.get('id_doc')

        if listener == "CardsClick":
            selected_card_key = self.hash_map['selected_card_key']
            doc_goods_table = self.hash_map.get_json('doc_goods_table')
            table_data = doc_goods_table['customtable']['tabledata']

            current_elem = None
            current_elem_filter = [item for item in table_data if item.get('key') == selected_card_key]

            if current_elem_filter:
                current_elem = current_elem_filter[0]

            current_str = self.hash_map["selected_card_position"]
            table_lines_qtty = self.hash_map['table_lines_qtty']

            # текущий элемент не найден или это заголовок таблицы
            if current_elem is None or 'good_name' not in current_elem:
                return

            title = '{} № {} от {}'.format(self.hash_map['doc_type'], self.hash_map['doc_n'], self.hash_map['doc_date'])
            put_data = {
                'Doc_data': title,
                'Good': current_elem['good_name'],
                'good_art': current_elem['art'],
                'good_sn': current_elem['series_name'],
                'good_property': current_elem['properties_name'],
                'good_price': current_elem['price'],
                'good_unit': current_elem['units_name'],
                'good_str': f'{current_str} / {table_lines_qtty}',
                'qtty_plan': current_elem['qtty_plan'],
                'good_plan': current_elem['qtty_plan'],
                'key': current_elem['key'],
                'price': current_elem['price'],
                'price_type': current_elem['price_name'],
                'qtty': current_elem['qtty'] if current_elem['qtty'] and float(current_elem['qtty']) != 0 else '',
            }
            self._fill_none_values(
                put_data,
                ('good_art', 'good_sn', 'good_property', 'good_price', 'good_plan'),
                default='отсутствует')

            self.hash_map.put_data(put_data)

            # Формируем таблицу QR кодов------------------

            args = {
                'id_doc': id_doc,
                'id_good': current_elem['id_good'],
                'id_property': current_elem['id_properties'],
                'id_series': current_elem['id_series'],
                'id_unit': current_elem['id_unit'],
            }
            res = self._get_doc_barcode_data(args)

            # TODO Переделать через виджеты
            cards = self._get_barcode_card()

            # Формируем список карточек баркодов
            cards['customcards']['cardsdata'] = []
            for el in res:
                picture = '#f00c' if el['approved'] in ['True', 'true', '1'] else ''
                row = {
                    'barcode': el['mark_code'],
                    'picture': picture
                }
                cards['customcards']['cardsdata'].append(row)

            self.hash_map.put('barcode_cards', cards, to_json=True)
            self.hash_map.show_screen("Товар выбор")

        elif listener == 'barcode' or self._is_result_positive('ВвестиШтрихкод'):
            res = self._barcode_scanned()
            if res.get('key'):
                self.service.update_rs_docs_table_sent_status(res.get('key'))
                self.service.set_doc_status_to_upload(id_doc)

        elif listener == 'btn_barcodes':
            self.hash_map.show_dialog('ВвестиШтрихкод')

        elif listener in ['ON_BACK_PRESSED', 'BACK_BUTTON']:
            self.hash_map.put("ShowScreen", "Документы")

        elif self._is_result_positive('confirm_verified'):
            id_doc = self.hash_map['id_doc']
            doc = RsDoc(id_doc)
            doc.mark_verified(1)
            self.hash_map.show_screen("Документы")

        elif listener == 'btn_doc_mark_verified':
            self.hash_map.show_dialog('confirm_verified', 'Завершить документ?', ['Да', 'Нет'])

        elif listener == 'btn_rows_filter_on':
            self.hash_map.put('rows_filter', '1')
            self.hash_map.refresh_screen()

        elif listener == 'btn_rows_filter_off':
            self.hash_map.remove('rows_filter')
            self.hash_map.refresh_screen()

    def _get_barcode_card(self):
        # TODO Переделать через виджеты

        ls = {"customcards": {
            "options": {
                "search_enabled": False,
                "save_position": True
            },
            "layout": {
                "type": "LinearLayout",
                "orientation": "vertical",
                "height": "match_parent",
                "width": "match_parent",
                "weight": "0",
                "Elements": [
                    {
                        "type": "LinearLayout",
                        "orientation": "horizontal",
                        "height": "match_parent",
                        "width": "match_parent",
                        "weight": "0",
                        "Elements": [
                            {"type": "TextView",
                             "height": "wrap_content",
                             "width": "match_parent",
                             "weight": "1",
                             "Value": "@barcode",
                             "TextSize": self.rs_settings.get('goodsTextSize'),
                             "Variable": ""
                             },
                            {
                                "type": "TextView",
                                "show_by_condition": "",
                                "Value": "@picture",
                                "TextColor": "#DB7093",
                                "BackgroundColor": "#FFFFFF",
                                "Variable": "btn_tst1",
                                "NoRefresh": False,
                                "document_type": "",
                                "cardCornerRadius": "15dp",
                                "weight": "1",
                                "mask": ""
                            }]
                    }
                ]
            }}
        }
        return ls

    def _get_doc_barcode_data(self, args):
        return self.service.get_doc_barcode_data(args)


# ^^^^^^^^^^^^^^^^^^^^^ DocDetails ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== Goods select =============================


class GoodsSelectScreen(Screen):
    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = DocService()

    def on_start(self):
        pass

    def on_input(self):
        listener = self.listener
        # self.toast(listener)
        if listener == "btn_ok":
            # получим текущую строку документа
            current_str = self.hash_map.get("selected_card_position")
            # Если строка не существует, создадим ее
            doc = ui_global.Rs_doc
            doc.id_doc = self.hash_map.get('id_doc')

            selected_card_key = self.hash_map['selected_card_key']
            doc_goods_table = self.hash_map.get_json('doc_goods_table')
            table_data = doc_goods_table['customtable']['tabledata']

            current_elem = None
            current_elem_filter = [item for item in table_data if item.get('key') == selected_card_key]

            if current_elem_filter:
                current_elem = current_elem_filter[0]

            doc.id_str = int(current_elem['key'])
            qtty = self.hash_map.get('qtty')

            if qtty != current_elem['qtty']:
                self.service.update_rs_docs_table_sent_status(self.hash_map.get("selected_card_key"))
                self.service.set_doc_status_to_upload(doc.id_doc)

            doc.qtty = float(qtty) if qtty else 0
            doc.update_doc_str(doc, self.hash_map.get('price'))  # (doc, )
            self.hash_map.put("ShowScreen", "Документ товары")

        elif listener in ["btn_cancel", 'BACK_BUTTON', 'ON_BACK_PRESSED']:
            self.hash_map.show_screen("Документ товары")

        elif listener == "photo":
            # Можно вообще этого не делать-оставлять как есть. Это для примера.
            image_file = str(
                self.hash_map.get("photo_path"))  # "переменная"+"_path" - сюда помещается путь к полученной фотографии

            image = Image.open(image_file)

            # сразу сделаем фотку - квадратной - это простой вариант. Можно сделать например отдельо миниатюры для списка, это немного сложнее
            im = image.resize((500, 500))
            im.save(image_file)

            jphotoarr = json.loads(hashMap.get("photoGallery"))
            self.hash_map.put("photoGallery", jphotoarr, to_json=True)

        elif listener == "gallery_change":  # пользователь может удалить фото из галереи. Новый массив надо поместить к документу
            if self.hash_map.containsKey("photoGallery"):  # эти 2 обработчика - аналогичные, просто для разных событий
                jphotoarr = json.loads(hashMap.get("photoGallery"))
                self.hash_map.put("photoGallery", jphotoarr, to_json=True)

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def get_doc(self):
        pass


# ^^^^^^^^^^^^^^^^^^^^^ Goods select ^^^^^^^^^^^^^^^^^^^^^^^^^^^^


# ==================== Settings =============================


class HttpSettingsScreen(Screen):
    screen_name = 'Настройки http соединения'
    process_name = 'Параметры'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)

    def on_start(self) -> None:
        self.hash_map['btn_test_connection'] = 'Тест соединения'
        http_settings = self.get_http_settings()
        put_data = {
            'url': widgets.ModernField(hint='Адрес сервера', default_text=http_settings['url'] or '').to_json(),
            'user': widgets.ModernField(hint='Пользователь', default_text=http_settings['user'] or '').to_json(),
            'pass': widgets.ModernField(hint='Пароль', default_text=http_settings['pass'] or '',
                                        password=True).to_json(),
            'user_name': widgets.ModernField(hint='Ваше имя для идентификации в 1С',
                                             default_text=http_settings['user_name'] or '').to_json(),
        }
        self.hash_map.put_data(put_data)

    def on_input(self) -> None:
        pass

        # if listener == 'btn_save':
        #     hashMap.toast('saved')
        #     hashMap.toast(hashMap.get('pass'))
        #     rs_settings.put('url', hashMap.get('url'), True)
        #     rs_settings.put('user', hashMap.get('user'), True)
        #     rs_settings.put('pass', hashMap.get('pass'), True)
        #     rs_settings.put('user_name', hashMap.get('user_name'), True)
        #
        #     hashMap.put('url', ui_form_data.ModernField(hint='url', default_text=rs_settings.get('url')).to_json())
        #     hashMap.put('user', ui_form_data.ModernField(hint='user', default_text=rs_settings.get('user')).to_json())
        #     hashMap.put('pass', ui_form_data.ModernField(hint='pass', default_text=rs_settings.get('pass')).to_json())
        #     hashMap.put('user_name',
        #                 ui_form_data.ModernField(hint='user_name', default_text=rs_settings.get('user_name')).to_json())
        #
        #     # hashMap.put('ShowScreen', 'Настройки и обмен')
        # elif listener == 'btn_cancel':
        #     hashMap.put('ShowScreen', 'Настройки и обмен')
        # elif listener == 'ON_BACK_PRESSED':
        #     hashMap.put('ShowScreen', 'Настройки и обмен')
        # elif listener == 'barcode':
        #     barcode = hashMap.get('barcode_camera2')
        #     try:
        #         barc_struct = json.loads(barcode)
        #
        #         rs_settings.put('url', barc_struct.get('url'), True)
        #         rs_settings.put('user', barc_struct.get('user'), True)
        #         rs_settings.put('pass', barc_struct.get('pass'), True)
        #         rs_settings.put('user_name', barc_struct.get('user_name'), True)
        #
        #         hashMap.put('url', ui_form_data.ModernField(hint='url', default_text=barc_struct.get('url')).to_json())
        #         hashMap.put('user',
        #                     ui_form_data.ModernField(hint='user', default_text=barc_struct.get('user')).to_json())
        #         hashMap.put('pass',
        #                     ui_form_data.ModernField(hint='pass', default_text=barc_struct.get('pass')).to_json())
        #         hashMap.put('user_name', ui_form_data.ModernField(hint='user_name',
        #                                                           default_text=barc_struct.get('user_name')).to_json())
        #     except:
        #         hashMap.put('toast', 'неверный формат QR-кода')
        # elif listener == 'btn_test_connection':
        #     # /communication_test
        #     http = get_http_settings(hashMap)
        #     r = requests.get(http['url'] + '/simple_accounting/communication_test?android_id=' + http['android_id'],
        #                      auth=HTTPBasicAuth(http['user'], http['pass']),
        #                      headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'},
        #                      params={'user_name': http['user_name'], 'device_model': http['device_model']})
        #     if r.status_code == 200:
        #         hashMap.put('btn_test_connection', 'Соединение установлено')
        #         hashMap.put('toast', 'Соединение установлено')
        #     else:
        #         hashMap.put('btn_test_connection', 'Тест соединения')
        #         hashMap.put('toast', 'Не удалось установить соединение')
        #
        # elif listener == 'timer_is_disabled':
        #     rs_settings.put('timer_is_disabled', hashMap['timer_is_disabled'], True)
        #
        # return hashMap

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def get_modern_field(self, **data):
        return widgets.ModernField(**data).to_json()


class ErrorLogScreen(Screen):
    screen_name = 'Ошибки'
    process_name = 'Параметры'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = ErrorService()
        self.screen_values = {}

    def on_start(self) -> None:
        date_sort = self.hash_map['selected_date_sort']
        errors_table_data = self.service.get_all_errors(date_sort)
        table_raws = self._get_errors_table_rows(errors_table_data)
        table_view = self._get_errors_table_view(table_raws)
        self.hash_map.put("error_log_table", table_view.to_json())
        self.hash_map['date_sort_select'] = 'Новые;Cтарые'

    def on_input(self) -> None:
        super().on_input()

        if self.listener == "btn_clear_err":
            self.service.clear()
        if self.listener == 'ON_BACK_PRESSED':
            self.hash_map.put("ShowScreen", "Настройки и обмен")

        elif self.listener == "date_sort_click":
            self.hash_map['selected_date_sort'] = self.hash_map["date_sort_click"]

    def on_post_start(self):
        pass

    def show(self, args=None):
        self._validate_screen_values()
        self.hash_map.show_screen(self.screen_name, args)

    def _get_errors_table_rows(self, errors_table_data):
        table_data = [{}]
        i = 1
        for record in errors_table_data:
            error_row = {"key": i, "message": record[0], "time": record[1],
                         '_layout': self._get_errors_table_row_layout()}
            table_data.append(error_row)
            i += 1

        return table_data

    def _get_errors_table_view(self, table_rows):
        table_view = widgets.CustomTable(
            widgets.LinearLayout(
                self.LinearLayout(
                    self.TextView('Время'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('Сообщение'),
                    weight=3
                ),
                orientation='horizontal',
                height="match_parent",
                width="match_parent",
                BackgroundColor='#FFFFFF'
            ),
            options=widgets.Options().options,
            tabledata=table_rows
        )
        return table_view

    def _get_errors_table_row_layout(self):
        row_view = widgets.LinearLayout(
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@time',
                    TextSize=15,
                    width='match_parent'
                ),
                width='match_parent',
                height='wrap_content',
                weight=1,
                StrokeWidth=0
            ),
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@message',
                    TextSize=15,
                    width='match_parent',
                ),
                width='match_parent',
                height='wrap_content',
                weight=3,
            ),
            orientation='horizontal',
            width='match_parent',
            BackgroundColor='#FFFFFF',
            height='wrap_content',
            StrokeWidth=1
        )

        return row_view

    class LinearLayout(widgets.LinearLayout):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.orientation = 'vertical'
            self.height = "match_parent"
            self.width = "match_parent"
            self.StrokeWidth = 1

    class TextView(widgets.TextView):
        def __init__(self, value):
            super().__init__()
            self.TextSize = '15'
            self.TextBold = True
            self.width = 'match_parent'
            self.Value = value


# ^^^^^^^^^^^^^^^^^^^^^ Settings ^^^^^^^^^^^^^^^^^^^^^^^^^^^^


# ==================== Debug settings =============================


class DebugSettingsScreen(Screen):
    process_name = 'Отладка'
    screen_name = 'Отладочный экран'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.hs_service = hs_services.DebugService

    def on_start(self):
        debug_host_ip = self.rs_settings.get('debug_host_ip') or self.hash_map['ip_host']
        self.hash_map.put(
            'ip_host',
            {'hint': 'IP-адрес для выгрузки базы/лога', 'default_text': debug_host_ip or ''},
            to_json=True)

    def on_input(self):
        listeners = {
            'btn_copy_base': self._copy_base,
            'btn_unload_log': self._unload_log,
            'btn_local_files': self._local_files,
            'ON_BACK_PRESSED': self._on_back_pressed
        }
        if self.listener in listeners:
            listeners[self.listener]()

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _copy_base(self):
        ip_host = self.hash_map['ip_host']
        path_to_databases = self.rs_settings.get('path_to_databases')
        base_name = self.rs_settings.get('sqlite_name')
        file_path = os.path.join(path_to_databases, base_name)

        if os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                res = self.hs_service(ip_host).export_database(f)

                if res['status_code'] == 200:
                    self.hash_map.toast('База SQLite успешно выгружена')
                else:
                    self.hash_map.toast('Ошибка соединения')
        else:
            self.hash_map.toast('Файл не найден')

    def _unload_log(self):
        ip_host = self.hash_map['ip_host']

        path_to_databases = self.rs_settings.get('path_to_databases')
        base_name = self.rs_settings.get('log_name')
        file_path = os.path.join(path_to_databases, base_name)

        # TODO Здесь нужно будет вызывать класс-сервис для взаимодействия с TinyDB
        from tinydb import TinyDB

        db = TinyDB(file_path)
        data = db.all()

        res = self.hs_service(ip_host).export_log(data)
        if res['status_code'] == 200:
            self.hash_map.toast('Лог успешно выгружен')
        else:
            self.hash_map.toast('Ошибка соединения')

    def _local_files(self):
        import ui_csv

        path = self.hash_map['path']
        delete_files = self.hash_map['delete_files']

        if not delete_files:
            delete_files = '0'
        if not path:
            path = '//storage/emulated/0/download/'

        ret_text = ui_csv.list_folder(path, delete_files)

        self.hash_map.toast(ret_text)

    def _on_back_pressed(self):
        ip_host = self.hash_map['ip_host']
        self.rs_settings.put('debug_host_ip', ip_host, True)
        self.hash_map.put('FinishProcess', '')


# ^^^^^^^^^^^^^^^^^^^^^ Debug settings ^^^^^^^^^^^^^^^^^^^^^^^^^^^^


# ==================== Timer =============================


class Timer:
    def __init__(self, hash_map: HashMap, rs_settings):
        self.hash_map = hash_map
        self.rs_settings = rs_settings
        self.http_settings = self._get_http_settings()
        self.db_service = DocService()
        self.http_service = HsService(self.http_settings)

    def timer_on_start(self):
        self.load_docs()
        self.upload_docs()

    def save_data_to_db(self, data: dict):
        # TODO доделать через пони
        if not data:
            return

        table_list = [
            'RS_countragents',
            'RS_warehouses',
            'RS_cells',
            'RS_types_goods',
            'RS_classifier_units',
            'RS_goods',
            'RS_properties',
            'RS_series',
            'RS_units',
            'RS_price_types',
            'RS_prices',
            'RS_barcodes',
        ]

        for table_name in table_list:
            table = data.get(table_name, {})
            service = self.db_service(None, table_name=table_name)
            for item_data in table:
                service.update(item_data)

    def put_notification(self, text, title=None):
        self.hash_map.notification(text, title)

    def _get_http_settings(self):
        http_settings = {
            'url': self.rs_settings.get("URL"),
            'user': self.rs_settings.get('USER'),
            'pass': self.rs_settings.get('PASS'),
            'device_model': self.hash_map['DEVICE_MODEL'],
            'android_id': self.hash_map['ANDROID_ID'],
            'user_name': self.rs_settings.get('user_name')}
        return http_settings

    def load_docs(self):
        if all([self.http_settings.get('url'), self.http_settings.get('user'), self.http_settings.get('pass')]):
            try:
                docs_data = self.http_service.get_data()
                if docs_data.get('data'):
                    existing_docs = self.db_service.get_existing_docs()
                    self.db_service.update_data_from_json(docs_data['data'])
                    docs_after_load = self.db_service.get_existing_docs()
                    diff = [f'{x[1]}: {x[0]}' for x in docs_after_load if x not in existing_docs]
                    if diff:
                        self.hash_map.toast(str(diff))
                        self.put_notification(text=", ".join(diff), title="Загружены документы:")

            except Exception as e:
                self.db_service.write_error_on_log(f'Ошибка загрузки документов: {e}')

    def upload_docs(self):
        if all([self.http_settings.get('url'), self.http_settings.get('user'), self.http_settings.get('pass')]):

            try:
                docs_goods_formatted_list = self.db_service.get_docs_and_goods_for_upload()
                if docs_goods_formatted_list:
                    answer = self.http_service.send_documents(docs_goods_formatted_list)
                    if answer:
                        if answer.get('Error') is not None:
                            self.put_notification(text='Ошибка при отправке документов')
                            err_text = answer.get('text').decode('utf-8')
                            error = answer.get("Error") or ''
                            self.db_service.write_error_on_log(f'Ошибка выгрузки документов: {err_text}\n{error}')
                        else:
                            docs_list_string = ', '.join([f"'{d['id_doc']}'" for d in docs_goods_formatted_list])
                            self.db_service.update_uploaded_docs_status(docs_list_string)
            except Exception as e:
                self.db_service.write_error_on_log(f'Ошибка выгрузки документов: {e}')


# ^^^^^^^^^^^^^^^^^^^^^ Timer ^^^^^^^^^^^^^^^^^^^^^^^^^^^^


# ==================== Main events =============================


class MainEvents:
    def __init__(self, hash_map: HashMap, rs_settings):
        self.hash_map = hash_map
        self.rs_settings = rs_settings

    def app_before_on_start(self):
        self.hash_map.put('getJSONConfiguration', '')

    def app_on_start(self):
        # TODO Обработчики обновления!
        release = self.rs_settings.get('Release') or ''
        toast = 'Готов к работе'
        current_release = self.hash_map['_configurationVersion']

        if current_release is None:
            toast = 'Не удалось определить версию конфигурации'

        if current_release and release != current_release:
            self.hash_map.put('UpdateConfigurations', '')
            self.rs_settings.put('Release', current_release, True)
            toast = f'Выполнено обновление на версию {current_release}'

        self._create_tables()

        rs_default_settings = {
            'TitleTextSize': 18,
            'titleDocTypeCardTextSize': 18,
            'CardTitleTextSize': 20,
            'CardDateTextSize': 10,
            'CardTextSize': 15,
            'GoodsCardTitleTextSize': 18,
            'goodsTextSize': 18,
            'SeriesPropertiesTextSize': 16,
            'DocTypeCardTextSize': 15,
            'signal_num': 83,
            'beep_duration': 1000,
            'use_mark': 'false',
            'add_if_not_in_plan': 'false',
            'path': '',
            'delete_files': 'false',
            'allow_overscan': 'false',
            'path_to_databases': '//data/data/ru.travelfood.simple_ui/databases',
            'sqlite_name': 'SimpleKeep',
            'log_name': 'log.json',
            'timer_is_disabled': False,
            'allow_fact_input': 'false'
        }

        for k, v in rs_default_settings.items():
            if self.rs_settings.get(k) is None:
                self.rs_settings.put(k, v, True)

        self.hash_map.toast(toast)


    def on_sql_error(self):
        sql_error = self.hash_map['SQLError']
        if sql_error:
            service = db_services.DocService()
            service.write_error_on_log(f'SQL_Error: {sql_error}')

    def put_notification(self):
        self.hash_map['_configuration'] = ''
        qtext = '''
        SELECT 
            doc_type, 
            count(id_doc) as count, 
            max(created_at) as dt 
        FROM RS_docs 
        WHERE created_at > ? 
        GROUP BY doc_type 
        '''

        last_date = self.rs_settings.get('lastDate')
        if not last_date:
            last_date = '2020-01-01 00:00:00'

        res = ui_global.get_query_result(qtext, (last_date,), True)

        doc_list = ''
        if res:
            for el in res:
                doc_list = doc_list + (' ' + el['doc_type'] + ': ' + str(el['count']))

            self.hash_map.put(
                'basic_notification',
                json.dumps([{'number': 1, 'title': 'Новые документы', 'message': doc_list}]))

            qtext = 'SELECT max(created_at) as dt FROM RS_docs'
            res2 = ui_global.get_query_result(qtext)

            self.rs_settings.put('lastDate', res2[0][0], True)
            self.hash_map.toast(last_date)

    def _create_tables(self):
        service = db_services.DbCreator()
        service.create_tables()


# ^^^^^^^^^^^^^^^^^^^^^ Main events ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

class ScreensFactory:
    screens = [
        GroupScanTiles,
        DocumentsTiles,
        GroupScanDocsListScreen,
        DocumentsDocsListScreen,
        GroupScanDocDetailsScreen,
        DocumentsDocDetailScreen,
        ErrorLogScreen,
        DebugSettingsScreen,
        HttpSettingsScreen
    ]

    @staticmethod
    def get_screen_class(screen_name=None, process=None, **kwargs):
        if not screen_name:
            screen_name = kwargs['hash_map'].get_current_screen()
        if not process:
            process = kwargs['hash_map'].get_current_process()

        for item in ScreensFactory.screens:
            if getattr(item, 'screen_name') == screen_name and getattr(item, 'process_name') == process:
                return item

    @staticmethod
    def create_screen(screen_name=None, process=None, **kwargs):
        if not screen_name:
            screen_name = kwargs['hash_map'].get_current_screen()
        if not process:
            process = kwargs['hash_map'].get_current_process()

        screen_class = ScreensFactory.get_screen_class(screen_name, process)
        return screen_class(**kwargs)


class MockScreen(Screen):
    def on_start(self):
        pass

    def on_input(self):
        pass

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass
