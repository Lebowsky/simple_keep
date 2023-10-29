import re
from abc import ABC, abstractmethod
import json
from json.decoder import JSONDecodeError
import os
from pathlib import Path
import time
from datetime import datetime
from typing import Dict, List, Callable, Union
import db_services
import hs_services
from printing_factory import PrintService
import db_models
from ui_utils import HashMap, get_ip_address
from barcode_workers import BarcodeWorker
from db_services import DocService, GoodsService, BarcodeService, TimerService
from tiny_db_services import ScanningQueueService, ExchangeQueueBuffer, LoggerService, DateFormat, NoSQLProvider
from hs_services import HsService
import static_data
from ru.travelfood.simple_ui import SimpleUtilites as suClass
import widgets
import ui_global

from java import jclass

noClass = jclass("ru.travelfood.simple_ui.NoSQL")
current_screen: 'Screen' = None
next_screen: 'Screen' = None
_rs_settings = noClass("rs_settings")

class Screen(ABC):
    screen_name: str
    process_name: str

    def __init__(self, hash_map: HashMap, rs_settings=_rs_settings, **kwargs):
        self.hash_map: HashMap = hash_map
        self.screen_values = {}
        self.rs_settings = rs_settings
        self.event: str = self.hash_map['event']
        self.is_finish_process = False
        self.parent_screen = kwargs.get('parent')
        self.on_start_handlers: List[Callable] = []
        self.init_params = {}
        self.result_handler: Union[Callable, None] = None
        self.result_process = None

    @abstractmethod
    def on_start(self):
        pass

    @abstractmethod
    def on_input(self):
        pass

    def on_post_start(self):
        return self.hash_map.remove(f'{self.__class__.__name__}_init')

    def show(self, args=None):
        set_next_screen(self)
        self.hash_map.put_data(args)
        self._init_screen_values()
        self._validate_screen_values()
        self.init_screen()
        self.hash_map.show_screen(self.screen_name)

    def show_process_result(self, result_handler=None, args=None):
        set_next_screen(self)
        if self.parent_screen:
            self.parent_screen.result_handler = result_handler
        self.hash_map.put_data(args)
        self._init_screen_values()
        self._validate_screen_values()
        self.init_screen()
        self.hash_map.show_process_result(self.process_name, self.screen_name)

    def init_screen(self):
        self.hash_map.put(f'{self.__class__.__name__}_init')
        return self

    def refresh_screen(self, hash_map: HashMap):
        hash_map.refresh_screen()

    @property
    def listener(self):
        if self.hash_map['event'] == 'onResult' and self.result_handler:
            self.result_handler(self.result_process)

        return self.hash_map.listener

    @listener.setter
    def listener(self, v):
        pass

    def _clear_screen_values(self):
        for key in self.screen_values:
            self.hash_map.remove(key)

    def toast(self, text):
        self.hash_map.toast(text)

    def _is_result_positive(self, listener) -> bool:
        return self.listener == listener and self.event == 'onResultPositive'

    def _is_result_negative(self, listener) -> bool:
        return self.listener == listener and self.event == 'onResultNegative'

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

    def _listener_not_implemented(self):
        raise NotImplementedError (f'listener {self.listener} not implemented')

    def _is_init_handler(self):
        return self.hash_map.containsKey(f'{self.__class__.__name__}_init')

    def _init_screen_values(self):
        for k in self.screen_values:
            self.screen_values[k] = self.hash_map[k]

    def _finish_process(self):
        self.is_finish_process = True
        self.hash_map.finish_process()

    def _finish_process_result(self, result=None):
        self.is_finish_process = True

        if self.parent_screen:
            self.parent_screen.hash_map = self.hash_map
            self.parent_screen.result_process = result
            set_next_screen(self.parent_screen)
        self.hash_map.finish_process_result()

    def _back_screen(self):
        if self.parent_screen:
            self.parent_screen.hash_map = self.hash_map
            set_next_screen(self.parent_screen)
        self.hash_map.back_screen()

    def _get_selected_card_data(self, remove=True):
        selected_card_data = self.hash_map.get_json('selected_card_data')
        if remove:
            self.hash_map.remove('selected_card_data')

        return selected_card_data

    def _run_on_start_handlers(self):
        for handler in self.on_start_handlers:
            handler()
            self.on_start_handlers.remove(handler)

    @staticmethod
    def _format_quantity(qtty):
        if float(qtty) % 1 == 0:
            return int(float(qtty))
        else:
            return round(qtty, 3)

    @staticmethod
    def _format_date(date_str: str, default=None):
        try:
            return datetime.fromisoformat(date_str).strftime('%m-%d-%Y %H:%M:%S')
        except ValueError:
            if not default is None:
                return default
            return date_str

    def _get_doc_title(self, **kwargs) -> str:
        doc_date = kwargs.get('doc_date', '')
        doc_n = kwargs.get('doc_n', '')
        doc_title = '{} № {} от {}'.format(
                kwargs.get('doc_type', ''),
                self._format_doc_number(doc_n) if doc_n else '',
                self._format_date(doc_date) if doc_date else ''
            )
        return doc_title

    @staticmethod
    def _format_doc_number(num: str) -> str:
        prefix, number = num.split('-')
        modified_number = str(int(number))
        return f"{prefix}-{modified_number}"


class SimpleFileBrowser(Screen):
    screen_name = 'Список файлов'
    process_name = 'Проводник'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.debug_host_ip = rs_settings.get('debug_host_ip')
        self.hs_service = hs_services.DebugService(ip_host=self.hash_map.get('ip_host') or self.debug_host_ip)  # '192.168.1.77'

    def on_start(self):
        current_dir = self.hash_map.get('current_dir') or suClass.get_temp_dir()
        list_data = self.get_all_files_from_patch(current_dir)
        doc_cards = self._get_doc_cards_view(list_data)
        self.hash_map.put('current_dir', current_dir)
        self.hash_map['file_browser_cards'] = doc_cards.to_json()
        self.hash_map.put('return_selected_data')

    def on_input(self):
        current_directory = Path(self.hash_map.get('current_dir'))
        if self.listener == 'ON_BACK_PRESSED':
            self.hash_map.finish_process()

        elif self.listener == 'btn_get_up':
            if not os.access(current_directory.parent, os.R_OK):
                self.hash_map.toast('Доступ запрещён')
                return
            self.hash_map['current_dir'] = current_directory.parent

        elif self.listener == 'CardsClick':
            current_elem = json.loads(self.hash_map.get("selected_card_data"))
            if current_elem['file_type'] == 'Folder':
                new_dir = Path(current_directory, current_elem['file_name'])
                if os.access(new_dir, os.R_OK):
                    self.hash_map['current_dir'] = new_dir

        elif self.listener == 'LayoutAction':
            self._layout_action()

    def _get_doc_cards_view(self, table_data: List[Dict]):
        for row in table_data:
            if row['file_type'] != 'File':
                row['_layout'] = self._get_layout(is_file=False)
            elif row['extension'] == '.htm':
                row['_layout'] = self._get_layout(is_htm=True)
        doc_cards = widgets.CustomCards(
            self._get_layout(),
            options=widgets.Options().options,
            cardsdata=table_data,
        )

        return doc_cards

    def _get_layout(self, is_file: bool = True, is_htm: bool = False):
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')
        card_date_text_size = self.rs_settings.get('CardDateTextSize')
        popup_values = ['Инфо']
        if is_file:
            popup_values.append('Передать на ББ')
            if is_htm:
                popup_values.append('Шаблон печати')
        layout = widgets.LinearLayout(
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@picture',
                    TextBold=False,
                    TextSize=card_title_text_size,
                    weight=0
                ),
                widgets.TextView(
                    Value='@file_name',
                    TextBold=True,
                    TextSize=card_title_text_size,
                    weight=1
                ),
                widgets.PopupMenuButton(
                    Value=';'.join(popup_values),
                    Variable="sent",
                    weight=0,
                ),
                width="match_parent",
                orientation="horizontal",
            ),
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@file_size',
                    TextSize=card_date_text_size
                ),
                widgets.TextView(
                    Value='@creation_time',
                    TextSize=card_date_text_size
                ),
                width="match_parent",
            ),

            width="match_parent"
        )
        return layout

    @staticmethod
    def get_all_files_from_patch(directory: str) -> List[Dict]:
        files_info = []
        # Walk through the folder and its subdirectories
        directory_path = Path(directory)
        for file in directory_path.iterdir():
            pic = ('#f15b' if file.is_file() else
                   '#f0c1' if file.is_symlink() else '#f07b')
            file_type = ("File" if file.is_file() else
                         "SymLink" if file.is_symlink() else "Folder")
            formatted_creation_time = time.strftime(
                '%Y-%m-%d %H:%M:%S',
                time.localtime(int(file.stat().st_ctime))
            )
            file_info = {
                'picture': pic,
                'file_type': file_type,
                'file_name': file.name,
                'full_path': str(directory_path.joinpath(file.name)),
                'file_size': f'{file.stat().st_size / 1024:.2f} KB',
                'creation_time': formatted_creation_time,
                'extension': file.suffix
            }
            files_info.append(file_info)

        return files_info

    def _layout_action(self):
        listener = self.hash_map.get('layout_listener')
        selected_card: dict = json.loads(self.hash_map.get('card_data'))
        if listener == 'Передать на ББ':
            self._copy_file(Path(selected_card['full_path']))
        elif listener == 'Инфо':
            selected_card.pop('_layout', None)
            self.hash_map.toast(str(selected_card))
        elif listener == 'Шаблон печати':
            print_nosql = noClass("print_nosql")
            print_nosql.put('lable_file_name', selected_card.get('file_name'), True)
            print_nosql.put('lable_full_path', selected_card.get('full_path'), True)
            print_nosql.put('from_file_browser', True, True)
            self.hash_map.show_process_result('Print', 'PrintTemplates1CParameters')

    def _copy_file(self, file: Path):
        ip_host = self.hash_map.get('ip_host') or self.rs_settings.get('debug_host_ip') # '192.168.1.77'
        with open(file, 'rb') as f:
            # send_service = self.hs_service(ip_host)
            res = self.hs_service.export_file(file.name, f)

            if res['status_code'] == 200:
                self.hash_map.toast(f'Файл {file.name} успешно выгружен')
            else:
                self.hash_map.toast('Ошибка соединения')


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

    @staticmethod
    def _get_tile_data(tile_element):
        count_verified = tile_element['count_verified'] or 0
        count_unverified = tile_element['count_unverified'] or 0
        qtty_plan_verified = tile_element['qtty_plan_verified'] or 0
        qtty_plan_unverified = tile_element['qtty_plan_unverified'] or 0

        return {
            "docName": tile_element['docType'],
            'QttyOfDocs': '{}/{}'.format(tile_element['count'], tile_element['verified']),
            'count_verified': '{}/{}'.format(
                count_verified + count_unverified,
                count_unverified),
            'qtty_plan_verified': '{}/{}'.format(
                qtty_plan_verified + qtty_plan_unverified,
                qtty_plan_unverified)
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
        self.db_service = db_services.DocListService(is_group_scan=True)
        self.screen_name = self.hash_map.get_current_screen()
        self.process_name = self.hash_map.get_current_process()

    def on_start(self) -> None:
        if not self._check_connection():
            tiles = self._get_message_tile("Отсутствует соединение с сервером", text_color="#ff0000")
            self.hash_map.put('tiles', tiles, to_json=True)
            self.hash_map.refresh_screen()
            self.hash_map['check_connection'] = False
            return

        self.hash_map['check_connection'] = True

        data = self._get_docs_stat()

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
            self._back_screen()

    def on_post_start(self):
        pass

    def show(self, args=None):
        self.hash_map.show_screen(self.screen_name, args)

    def _check_connection(self):
        if (self.rs_settings.get('offline_mode') or
                self.hash_map.containsKey('check_connection')):
            return True

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

    def _get_docs_stat(self):
        return self.db_service.get_docs_stat()

    def _back_screen(self):
        MainEvents.start_timer(self.hash_map)
        self._finish_process()

class DocumentsTiles(GroupScanTiles):
    screen_name = 'Плитки'
    process_name = 'Документы'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.db_service = db_services.DocListService()

    def on_start(self):
        super().on_start()

    def _check_connection(self):
        return True

    def _get_docs_stat(self):
        return self.db_service.get_docs_stat()


# ^^^^^^^^^^^^^^^^^^^^^ Tiles ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== DocsList =============================


class DocsListScreen(Screen):
    def __init__(self, hash_map: HashMap, **kwargs):
        super().__init__(hash_map, **kwargs)
        self.db_service = db_services.DocListService()
        self.service = DocService()
        self.screen_values = {}
        self.popup_menu_data = ''
        self.queue_service = ScanningQueueService()

    def on_start(self) -> None:
        doc_types = self.service.get_doc_types()
        self.hash_map['doc_type_select'] = ';'.join(['Все'] + doc_types)
        self.hash_map['doc_status_select'] = 'Все;К выполнению;Выгружен;К выгрузке'

        doc_type = self.hash_map['selected_tile_key'] or self.hash_map['doc_type_click']
        doc_status = self.hash_map['selected_doc_status']
        self.hash_map['doc_type_click'] = doc_type
        self.hash_map['selected_tile_key'] = ''
        list_data = self._get_doc_list_data(doc_type, doc_status)

        prepared_data = self._prepare_table_data(list_data)
        self.hash_map['return_selected_data'] = ''
        doc_cards = self._get_doc_cards_view(prepared_data, self.popup_menu_data)
        self.hash_map['docCards'] = doc_cards.to_json()

    def on_input(self) -> None:
        super().on_input()
        if self.listener == "doc_status_click":
            # self.hash_map['selected_doc_status'] = self.hash_map["doc_status_click"]
            self._doc_status_click()

        elif self.listener == 'LayoutAction':
            self._layout_action()

        elif self._is_result_positive('confirm_delete'):
            self.confirm_delete_doc_listener()

        elif self.listener == 'ON_BACK_PRESSED':
            self._back_screen()

        elif self._is_result_positive('confirm_resend_doc'):
            self._resend_doc()

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

    def _back_screen(self):
        self.hash_map.show_screen('Плитки')

    def _doc_status_click(self):
        self.hash_map['selected_doc_status'] = self.hash_map["doc_status_click"]
        self.current_status = self.hash_map["doc_status_click"]

    def _resend_doc(self):
        id_doc = self.get_id_doc()
        self.service.doc_id = id_doc
        doc_data = self.service.get_doc_data_to_resend()

        if doc_data:
            http_service = hs_services.HsService(http_params=self.get_http_settings())
            try:
                answer = http_service.send_data(doc_data)
            except Exception as e:
                http_service.write_error_to_log(error_text=e,
                                                error_info='Ошибка выгрузки документа')
                return

            if answer.error:
                http_service.write_error_to_log(error_text=answer.error_text,
                                                error_info='Ошибка выгрузки документа')
            else:
                self.service.doc_id = id_doc
                self.service.set_doc_values(verified=1, sent=1)
                self.toast('Документ отправлен повторно')
        else:
            self.toast('Нет данных для отправки')
            return

    def _get_doc_list_data(self, doc_type, doc_status) -> list:
        results = self.db_service.get_docs_view_data(doc_type, doc_status)
        return results

    def _prepare_table_data(self, list_data):
        table_data = []
        for record in list_data:
            doc_status = ''

            if record['verified'] and record['sent']:
                doc_status = 'Выгружен'
            elif record['verified']:
                doc_status = 'К выгрузке'
            elif not (record['verified'] and record['sent']):
                doc_status = 'К выполнению'

            doc_title = self._get_doc_title(
                doc_type=self.hash_map.get('doc_type') or '',
                doc_n=self.hash_map.get('doc_n') or '',
                doc_date=self.hash_map.get('doc_date') or ''
            )

            table_data.append({
                'key': record['id_doc'],
                'type': record['doc_type'],
                'number': record['doc_n'],
                'doc_title': doc_title,
                'data': self._format_date(record['doc_date']),
                'warehouse': record['RS_warehouse'],
                'countragent': record['RS_countragent'],
                'add_mark_selection': record['add_mark_selection'],
                'status': doc_status,
                'is_group_scan': record['is_group_scan']
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

    def _get_selected_card_put_data(self, put_data=None):
        card_data = self.hash_map.get("selected_card_data", from_json=True)

        put_data = put_data or {}
        put_data['id_doc'] = card_data['key']
        put_data['doc_type'] = card_data['type']
        put_data['doc_n'] = card_data['number']
        put_data['doc_date'] = card_data['data']
        put_data['warehouse'] = card_data['warehouse']
        put_data['countragent'] = card_data['countragent']
        put_data['doc_title'] = self._get_doc_title(**put_data)

        return put_data

    def _set_doc_verified(self, id_doc, value=True):
        # service = DocService(id_doc)
        value = str(int(value))

        try:
            self.service.set_doc_value('verified', value)
        except Exception as e:
            self.hash_map.error_log(e.args[0])

    def doc_delete(self, id_doc):

        result = True

        try:
            self.service.delete_doc(id_doc)
            self.queue_service.remove_doc_lines(id_doc)
        except Exception as e:
            self.hash_map.error_log(e.args[0])
            result = False

        return result

    def get_docs_count(self, doc_type=''):
        doc_type = '' if not doc_type or doc_type == 'Все' else doc_type
        return self.service.get_docs_count(doc_type)

    def _clear_barcode_data(self, id_doc):
        return self.service.clear_barcode_data(id_doc)

    def confirm_delete_doc_listener(self):
        card_data = self.hash_map.get_json("card_data")
        id_doc = card_data['key']
        doc_type = self.hash_map['doc_type_click']

        if self.doc_delete(id_doc):
            docs_count = self.get_docs_count(doc_type=doc_type)
            self.hash_map.toast('Документ успешно удалён')
            if docs_count:
                self.on_start()
            else:
                self.hash_map.show_screen('Плитки')
        else:
            self.hash_map.toast('Ошибка удаления документа')

    def get_id_doc(self):
        card_data = self.hash_map.get_json("card_data") or {}
        id_doc = card_data.get('key') or self.hash_map['selected_card_key']
        return id_doc

    def get_doc_number(self):
        card_data = self.hash_map.get_json("card_data") or {}
        doc_number = card_data.get('number')
        return doc_number


class GroupScanDocsListScreen(DocsListScreen):
    screen_name = 'Документы'
    process_name = 'Групповая обработка'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map)
        self.db_service = db_services.DocListService(is_group_scan=True)
        self.service.is_group_scan = True
        self.popup_menu_data = ';'.join(
            ['Удалить', ])  #'Очистить данные пересчета'

    def on_start(self):
        super().on_start()
        self.hash_map.stop_timers(bs_hash_map=True)

    def on_input(self):
        super().on_input()
        if self.listener == "CardsClick":
            current_mode = "оффлайн" if self.rs_settings.get('offline_mode') else "онлайн"
            warning_msg = " Документ не будет доступен в других процессах."
            msg = (f"Вы открываете документ групповую обработку документа "
                   f"в {current_mode.upper()} режиме.")
            if self.hash_map.get_json('selected_card_data')['is_group_scan'] == '0':
                msg += warning_msg
            self.hash_map.put('msg', msg)

            layout = '''{
                                    "type": "LinearLayout",
                                    "Variable": "",
                                    "orientation": "horizontal",
                                    "height": "wrap_content",
                                    "width": "match_parent",
                                    "weight": "0",
                                    "Elements": [
                                        {
                                            "Value": "@msg",
                                            "Variable": "msg",
                                            "height": "wrap_content",
                                            "width": "match_parent",
                                            "weight": "0",
                                            "type": "TextView"
                                        }
                                    ]
                                }'''

            self.hash_map.show_dialog('open_doc_confirmation',
                                      title="Подтвердите действие", dialog_layout=layout)

            selected_card_key = self.hash_map['selected_card_key']
            self.hash_map['id_doc'] = selected_card_key

        elif self._is_result_positive('open_doc_confirmation'):
            id_doc = self.hash_map['id_doc']
            self.service.doc_id = id_doc
            if self.hash_map.get_json('selected_card_data')['is_group_scan'] == '0':
                self.service.reset_doc_tables_qtty()
            self.service.set_doc_value('verified', 1)
            self.service.set_doc_value('is_group_scan', '1')

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
            self.queue_service.remove_doc_lines(id_doc)
            if res.get('result'):
                self.toast('Данные пересчета и маркировки очищены')
                self.service.set_doc_status_to_upload(id_doc)
            else:
                self.toast('При очистке данных пересчета возникла ошибка.')
                self.hash_map.error_log(res.get('error'))

    def _back_screen(self):

        super()._back_screen()


class DocumentsDocsListScreen(DocsListScreen):
    screen_name = 'Документы'
    process_name = 'Документы'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map)
        self.service.docs_table_name = 'RS_docs'
        self.popup_menu_data = ';'.join(
            ['Удалить', 'Очистить данные пересчета', 'Отправить повторно'])

    def on_start(self):
        super().on_start()

    def on_input(self):
        super().on_input()

        if self.listener == "CardsClick":
            id_doc = self.get_id_doc()
            self.hash_map['id_doc'] = id_doc
            # id_doc = self.hash_map['selected_card_key']
            self.service.doc_id = id_doc

            noClass('articles_ocr_ncl').delete('finded_articles')
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
            self.queue_service.remove_doc_lines(id_doc)
            if res.get('result'):
                self.toast('Данные пересчета и маркировки очищены')
                self.service.set_doc_status_to_upload(id_doc)
            else:
                self.toast('При очистке данных пересчета возникла ошибка.')
                self.hash_map.error_log(res.get('error'))

    def get_id_doc(self):
        card_data = self.hash_map.get_json("card_data") or {}
        id_doc = card_data.get('key') or self.hash_map['selected_card_key']
        return id_doc


class DocsOfflineListScreen(DocsListScreen):
    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map)
        self.popup_menu_data = ';'.join(
            ['Удалить', 'Очистить данные пересчета'])


# ^^^^^^^^^^^^^^^^^^^^^ DocsList ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== DocDetails =============================


class DocDetailsScreen(Screen):
    def __init__(self, hash_map, rs_settings=None):
        super().__init__(hash_map)
        self.barcode_worker = None
        self.id_doc = self.hash_map['id_doc']
        self.service = DocService(self.id_doc)
        self.items_on_page = 20
        self.queue_service = ScanningQueueService()
        self.doc_rows = None
        self.table_data = []

    def on_start(self) -> None:
        pass

    def on_input(self) -> None:

        listener = self.listener

        if listener == "next_page":
            self._next_page()
        elif listener == 'previous_page':
            self._previous_page()

        elif listener == 'items_on_page_click':
            self._set_items_on_page()

        elif listener == 'btn_rows_filter_on':
            self.hash_map.put('current_first_element_number', '0')
            self.hash_map.put('current_page', '1')
            self.hash_map.put('rows_filter', '1')
            self.hash_map.refresh_screen()

        elif listener == 'btn_rows_filter_off':
            self.hash_map.remove('rows_filter')
            self.hash_map.put('SearchString', '')
            self.hash_map.refresh_screen()

        elif listener == "Search":
            self.hash_map.put('current_first_element_number', '0')
            self.hash_map.put('current_page', '1')
            self._on_start()
            self.hash_map.refresh_screen()
        elif listener == 'btn_barcodes':
            self._show_dialog_input_barcode()

    def on_post_start(self):
        pass

    def _on_start(self):
        self._set_visibility_on_start()
        self.hash_map.put('SetTitle', self.hash_map["doc_type"])

        have_qtty_plan = False
        have_zero_plan = False
        have_mark_plan = False

        last_scanned_details = self._get_doc_details_data(last_scanned=True)
        last_scanned_data = self._prepare_table_data(last_scanned_details)
        last_scanned_item = last_scanned_data[1] if len(last_scanned_data) >= 2 else None
        doc_details = self._get_doc_details_data()
        table_data = self._prepare_table_data(doc_details)
        if table_data and last_scanned_item:
            table_data.insert(1, last_scanned_item)
            if self.hash_map.get('current_page') == '1':
                table_data.pop(1)
            table_data[1] = last_scanned_item
        self.table_data = table_data
        table_view = self._get_doc_table_view(table_data=table_data)

        self.hash_map['items_on_page_select'] = '20;40;60'
        if self.hash_map.get_bool('highlight'):
            self.hash_map.put('highlight', False)
            # self.enable_highlight(table_view.customtable)
            # self.hash_map.run_event_async('highlight_scanned_item')

        if doc_details:
            self.hash_map['table_lines_qtty'] = len(doc_details)
            have_qtty_plan = sum(
                [self._format_to_float(str(item['qtty_plan'])) for item in doc_details if item['qtty_plan']]) > 0
            # have_zero_plan = not have_qtty_plan
            have_zero_plan = True
            have_mark_plan = self._get_have_mark_plan()

        self.hash_map['have_qtty_plan'] = have_qtty_plan
        self.hash_map['have_zero_plan'] = have_zero_plan
        self.hash_map['have_mark_plan'] = have_mark_plan

        control = self.service.get_doc_value('control', self.id_doc) not in (0, '0', 'false', 'False', None)
        self.hash_map['control'] = control

        self.hash_map['return_selected_data'] = ''
        self.hash_map.put("doc_goods_table", table_view.to_json())

    def _item_barcode_scanned(self):
        id_doc = self.hash_map.get('id_doc')

        self.hash_map.put("SearchString", "")
        if self.hash_map.get("event") == "onResultPositive":
            barcode = self.hash_map.get('fld_barcode')
        else:
            barcode = self.hash_map.get('barcode_camera')

        if not barcode:
            return {}

        self.barcode_worker = BarcodeWorker(id_doc=self.id_doc,
                                            **self._get_barcode_process_params(),
                                            use_scanning_queue=True)
        result = self.barcode_worker.process_the_barcode(barcode)
        if result.error:
            self._process_error_scan_barcode(result)
            return result.error

    def _get_barcode_process_params(self):
        return {
            'have_qtty_plan': self.hash_map.get_bool('have_qtty_plan'),
            'have_zero_plan': self.hash_map.get_bool('have_zero_plan'),
            'have_mark_plan': self.hash_map.get_bool('have_mark_plan'),
            'control': self.hash_map.get_bool('control')
        }

    def _process_error_scan_barcode(self, scan_result):
        if scan_result.error == 'use_series':
            self.on_start_handlers.append(
                lambda: self._open_series_screen(scan_result.row_key)
            )
        else:
            self.hash_map.toast(scan_result.description)
            self.hash_map.playsound('error')

    def _set_visibility_on_start(self):
        _vars = ['warehouse', 'countragent']

        for v in _vars:
            name = f'Show_{v}'
            self.hash_map[name] = '1' if self.hash_map[v] else '-1'

        allow_fact_input = self.rs_settings.get('allow_fact_input')
        self.hash_map.put("Show_fact_qtty_input", '1' if allow_fact_input else '-1')
        self.hash_map.put("Show_fact_qtty_note", '-1' if allow_fact_input else '1')

    def _get_doc_details_data(self, last_scanned=False):
        self._check_previous_page()
        first_element = int(self.hash_map.get('current_first_element_number'))
        row_filters = self.hash_map.get('rows_filter')
        search_string = self.hash_map.get('SearchString') if self.hash_map.get('SearchString') else None
        finded_articles = noClass('articles_ocr_ncl').get('finded_articles')
        data = self.service.get_doc_details_data(
            id_doc=self.id_doc,
            first_elem=0 if last_scanned else first_element,
            items_on_page=1 if last_scanned else self.items_on_page,
            articles_list=json.loads(finded_articles) if finded_articles else None,
            row_filters=row_filters,
            search_string=search_string
        )
        self.doc_rows = self.service.get_doc_details_rows_count(
            id_doc=self.id_doc,
            articles_list=json.loads(finded_articles) if finded_articles else None,
            row_filters=row_filters,
            search_string=search_string
        )

        if not last_scanned:
            self._check_next_page(len(data))
        return data

    def _next_page(self):
        first_element = int(self.hash_map.get('current_first_element_number')) + self.items_on_page
        self.hash_map.put('current_first_element_number', str(first_element))
        current_page = int(self.hash_map.get('current_page')) + 1 or 1
        self.hash_map.put('current_page', str(current_page))

    def _previous_page(self):
        first_element = int(self.hash_map.get('current_first_element_number')) - self.items_on_page
        self.hash_map.put('current_first_element_number', str(first_element))
        current_page = int(self.hash_map.get('current_page')) - 1 or 1
        self.hash_map.put('current_page', str(current_page))

    def _check_previous_page(self):
        if self.hash_map.get('current_first_element_number'):
            first_element = int(self.hash_map.get('current_first_element_number'))
            if first_element > 0:
                self.hash_map.put("Show_previous_page", "1")
                return
        self.hash_map.put('current_first_element_number', '0')
        self.hash_map.put('current_page', '1')
        self.hash_map.put("Show_previous_page", "0")

    def _check_next_page(self, elems_count):
        if not self.hash_map.containsKey('current_first_element_number'):
            self.hash_map.put('current_first_element_number', '0')
        page_elems_sum = int(self.hash_map.get('current_first_element_number')) + self.items_on_page
        if page_elems_sum < self.doc_rows:
            self.hash_map.put("Show_next_page", "1")
        else:
            self.hash_map.put("Show_next_page", "0")

        if self.hash_map.get('Show_previous_page') == '0' and self.hash_map.get('Show_next_page') == '0':
            self.hash_map.put("Show_pagination_controls", "-1")
        else:
            self.hash_map.put("Show_pagination_controls", "1")

    def _set_items_on_page(self):
        value = self.hash_map.get('items_on_page_click')
        self.items_on_page = int(value)
        new_page = int(self.hash_map.get('current_first_element_number'))//self.items_on_page + 1
        self.hash_map.put('current_page', new_page)
        new_current_first = self.items_on_page * (new_page - 1)
        self.hash_map.put('current_first_element_number', str(new_current_first))

    def _prepare_table_data(self, doc_details):
        table_data = [{}]
        row_filter = self.hash_map.get_bool('rows_filter')

        for record in doc_details:
            if row_filter and record['d_qtty'] == record['qtty_plan']:
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
                'use_series': str(record['use_series'])
            }

            props = [
                '{} '.format(product_row['art']) if product_row['art'] else '',
                '({}) '.format(product_row['properties_name']) if product_row['properties_name'] else '',
                '{}'.format(product_row['series_name']) if product_row['series_name'] else '',
                ', {}'.format(product_row['units_name']) if product_row['units_name'] else '',
            ]
            product_row['good_info'] = ''.join(props)

            for key in ['qtty', 'd_qtty', 'qtty_plan']:
                value = self._format_to_float(str(record.get(key, 0.0) or 0.0))
                product_row[key] = str(int(value)) if value.is_integer() else value

            use_series = bool(int(product_row.get('use_series', 0)))
            product_row['_layout'] = self._get_doc_table_row_view(use_series)
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
            options=widgets.Options(override_search=True).options,
            tabledata=table_data
        )

        return table_view

    def _get_doc_table_row_view(self, use_series=False, use_mark=False):
        row_view = widgets.LinearLayout(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.LinearLayout(
                        widgets.LinearLayout(
                            widgets.LinearLayout(
                                widgets.Picture(
                                    Value=static_data.sn_icon_green if use_series else None,
                                    width=16,
                                    height=12,
                                ),
                                widgets.Picture(
                                    Value=static_data.mark_green if use_mark else None,
                                    width=16,
                                    height=12,
                                ),
                                orientation='horizontal',
                                Padding = 16
                            ),
                            self.TextView('@good_name'),
                            width='match_parent',
                            orientation='horizontal',

                        ),
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
                    Value='@d_qtty',
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
        qtty, qtty_plan = float(product_row['d_qtty']), float(product_row['qtty_plan'])
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

    def scan_error_sound(self):
        if self.hash_map.get('scan_error') and self.hash_map.get('scan_error') != "None":
            if self.hash_map.get('scan_error') in ['QuantityPlanReached', 'AlreadyScanned', 'Zero_plan_error']:
                self.hash_map.playsound('warning')
            else:
                self.hash_map.playsound('error')
        self.hash_map.refresh_screen()

    def _format_to_float(self, value: str):
        return float(value.replace(u'\xa0', u'').replace(',', '.') or '0.0')

    def _get_have_mark_plan(self):
        count = self.service.get_count_mark_codes(id_doc=self.id_doc)
        return count > 0

    def _open_series_screen(self, doc_row_key):
        screen_values = {
            'doc_row_id': doc_row_key,
            'title': 'Серии',
            'use_adr_docs_tables': '0'
        }

        screen = create_screen(
            self.hash_map,
            SeriesSelectScreen,
            screen_values=screen_values
        )
        screen.parent_screen = self
        screen.show()

    def _show_dialog_input_barcode(self, title="Введите штрихкод товара"):
        self.hash_map['fld_barcode'] = ''
        layout = '''{
            "type": "LinearLayout",
            "Variable": "",
            "orientation": "horizontal",
            "height": "wrap_content",
            "width": "match_parent",
            "weight": "0",
            "Elements": [
                {
                    "Value": "@fld_barcode",
                    "Variable": "fld_barcode",
                    "height": "wrap_content",
                    "width": "match_parent",
                    "weight": "0",
                    "type": "EditTextNumeric"
                }
            ]
        }'''
        self.hash_map.show_dialog('modal_dialog_input_barcode',
                                  title=title,
                                  dialog_layout=layout)

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
        self.db_service = db_services.BarcodeService()
        self.queue_service = ScanningQueueService()
        self.screen_values = {}

    def on_start(self):
        super()._on_start()
        if not self.hash_map.get('stop_sync_doc') and \
                not self.rs_settings.get('offline_mode'):
            self._sync_doc()
        self.hash_map.put('stop_sync_doc', 'true')

    def on_input(self) -> None:
        super().on_input()
        listeners = {
            'barcode': lambda: self._group_barcode_scanned(self.hash_map.get('barcode_camera')),
            'btn_barcodes': lambda: self._show_dialog_input_barcode(),
            'ON_BACK_PRESSED': self.go_back,
            'sync_doc': self._sync_doc,
            'send_all_scan_lines': self.send_all_scan_lines_call_handler,
            'CardsClick': self._cards_click
        }
        if self.listener in listeners:
            listeners[self.listener]()
        elif self._is_result_positive('modal_dialog_input_barcode'):
            self._group_barcode_scanned(self.hash_map.get('fld_barcode'))

    def _group_barcode_scanned(self, barcode):
        if not barcode:
            return

        self.barcode_worker = BarcodeWorker(id_doc=self.id_doc,
                                            **self._get_barcode_process_params(),
                                            use_scanning_queue=True,
                                            group_scan=True)
        result = self.barcode_worker.process_the_barcode(barcode)

        if result.error:
            self._process_error_scan_barcode(result)
            return result.error

        if not self.hash_map.get_bool('send_document_lines_running') and \
                not self.rs_settings.get('offline_mode'):
            self.hash_map.run_event_async('send_post_lines_data',
                                          post_execute_method='after_send_post_lines_data')
            self.hash_map.put('send_document_lines_running', True)

    def go_back(self):
        self.hash_map.remove('stop_sync_doc')
        self.hash_map.show_screen('Документы')

    def send_post_lines_data(self, sent=None):
        send_data = self.queue_service.get_document_lines(self.id_doc, sent=sent)
        validated_send_data = list(
            (dict((key, value) for key, value in d.items()
                if key not in ['row_key', 'sent'])
                for d in send_data)
        )
        if not validated_send_data:
            validated_send_data = [{}]

        if sent is False:
            http_result = self.hs_service.send_document_lines(self.id_doc, validated_send_data, timeout=8)
        else:
            http_result = self.hs_service.send_all_document_lines(self.id_doc, validated_send_data, timeout=8)

        if http_result.status_code != 200:
            self.hs_service.write_error_to_log(
                error_text="response status code != 200",
                error_info='Ошибка соединения при отправке данных группового '
                    'сканирования товара')
            return
        if not http_result.data.get('data'):
            return

        for element in http_result.data['data']:
            table_line = self.db_service.get_table_line('RS_docs_table', filters={
                'id_doc': element['id_doc'],
                'id_good': element['id_good'],
                'id_properties': element['id_properties'],
                'id_unit': element['id_unit']})
            if table_line:
                table_line['qtty'] = element['qtty']
                table_line['sent'] = 1
                self.db_service.replace_or_create_table('RS_docs_table', table_line)
            else:
                new_table_line = self.create_new_table_line(element)
                self.db_service.replace_or_create_table('RS_docs_table', new_table_line)

        self.queue_service.update_sent_lines(send_data)
        self.hash_map.put('send_document_lines_running', False)
        self.hash_map.refresh_screen()
        self.on_start()

    def after_send_data(self):
        if self.queue_service.has_unsent_lines(self.id_doc) and self._check_connection():
            self.hash_map.run_event_async('send_post_lines_data',
                                          post_execute_method='after_send_post_lines_data')

    @staticmethod
    def create_new_table_line(element):
        new_table_line = element
        del new_table_line['table_type']
        new_table_line.update({'d_qtty': new_table_line['qtty'],
                               'id_series': '', 'id_price': '', 'sent': 1,
                               'qtty_plan': None})
        return new_table_line

    def _get_barcode_process_params(self):
        return {
            'have_qtty_plan': self.hash_map.get_bool('have_qtty_plan'),
            'have_zero_plan': self.hash_map.get_bool('have_zero_plan'),
            'have_mark_plan': self.hash_map.get_bool('have_mark_plan'),
            'control': self.hash_map.get_bool('control')
        }

    def _process_error_scan_barcode(self, scan_result):
        self.hash_map.toast(scan_result.description)
        self.hash_map.playsound('error')

    def _get_doc_table_view(self, table_data):
        table_view = widgets.CustomTable(
            widgets.LinearLayout(
                self.LinearLayout(
                    self.TextView('Название'),
                    weight=4
                ),
                self.LinearLayout(
                    self.TextView('План'),
                    weight=2
                ),
                self.LinearLayout(
                    self.TextView('Факт устройства'),
                    weight=2
                ),
                self.LinearLayout(
                    self.TextView('Общий факт'),
                    weight=2
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

    def _get_doc_table_row_view(self, use_series=False, use_mark=False):
        row_view = widgets.LinearLayout(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.LinearLayout(
                        widgets.LinearLayout(
                            widgets.LinearLayout(
                                widgets.Picture(
                                    Value=static_data.sn_icon_green if use_series else None,
                                    width=16,
                                    height=12,
                                ),
                                widgets.Picture(
                                    Value=static_data.mark_green if use_mark else None,
                                    width=16,
                                    height=12,
                                ),
                                orientation='horizontal',
                                Padding = 16
                            ),
                            self.TextView('@good_name'),
                            width='match_parent',
                            orientation='horizontal',
                        ),
                        width='match_parent',
                    ),
                    width='match_parent',
                    orientation='horizontal',
                    StrokeWidth=1
                ),
                width='match_parent',
                weight=4,
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
                weight=2,
                StrokeWidth=1
            ),
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@d_qtty',
                    TextSize=15,
                    width='match_parent',
                ),
                width='match_parent',
                height='match_parent',
                weight=2,
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
                weight=2,
                StrokeWidth=1
            ),
            orientation='horizontal',
            width='match_parent',
            BackgroundColor='#FFFFFF'
        )

        return row_view

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

    def _sync_doc(self):
        if self._check_connection():
            self.hash_map.run_event_progress('send_post_lines_data')
        else:
            self.toast('Нет соединения с сервером 1С')

    def send_all_scan_lines_call_handler(self):
        if self._check_connection():
            self.hash_map.run_event_progress('send_all_scan_lines')
        else:
            self.toast('Нет соединения с сервером 1С')

    def send_all_scan_lines_run(self):
        self.send_post_lines_data()

    def send_unsent_lines_run(self):
        self.send_post_lines_data(sent=False)

    def _cards_click(self):
        current_elem = json.loads(self.hash_map.get('selected_card_data'))
        self.hash_map.put('id_good', current_elem['id_good'])
        if len(self.table_data) == 2:
            first_element_page = self.table_data[1]['key']
            first_element_list = first_element_page
        elif len(self.table_data) > 2:
            first_element_page = self.table_data[1]['key']
            first_element_list = self.table_data[2]['key']
        else:
            return

        table_index_data = self.service.get_table_index_data(
            self.id_doc, first_element_page, first_element_list
        )
        screen = GroupScanItemScreen(
            self.hash_map,
            id_doc=self.id_doc,
            table_index_data=table_index_data,
            doc_row_id=int(self.hash_map['selected_card_key']),
            control=self.hash_map['control']
        )
        screen.parent_screen = self
        screen.show()


class DocumentsDocDetailScreen(DocDetailsScreen):
    screen_name = 'Документ товары'
    process_name = 'Документы'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.db_service = db_services.BarcodeService()

    def on_start(self) -> None:
        super()._on_start()
        self._set_visibility_on_start()

    def on_input(self) -> None:
        super().on_input()
        listener = self.hash_map['listener']
        id_doc = self.hash_map.get('id_doc')

        if listener == "CardsClick":
            selected_card_data = self.hash_map.get_json('selected_card_data')
            if not selected_card_data:
                return
            if (noClass('articles_ocr_ncl').get('finded_articles')
                    and not self.rs_settings.get('allow_fact_input')):
                data = {
                    'sent': 0,
                    'd_qtty': float(selected_card_data['qtty']) + 1.0,
                    'qtty': float(selected_card_data['qtty']) + 1.0,
                }
                row_id = int(selected_card_data['key'])
                self.service.update_doc_table_row(data=data, row_id=row_id)
                noClass('articles_ocr_ncl').delete('finded_articles')
                self.hash_map.toast(
                    f'Артикул: {selected_card_data["art"]}\n'
                    f'{selected_card_data["good_name"]}\n'
                    f'{selected_card_data["properties_name"]}\n'
                    f'Количество увеличено на 1')
                return

            self.hash_map.remove('doc_goods_table')
            self._open_goods_select_screen(
                int(self.hash_map['selected_card_key'])
            )

        elif listener == 'barcode' or self._is_result_positive('modal_dialog_input_barcode'):
            noClass('articles_ocr_ncl').delete('finded_articles')
            res = self._item_barcode_scanned()
            # TODO с результатом обработку

        elif listener == 'btn_goods_ocr':
            articles = self.service.get_all_articles_in_document()
            if not articles:
                self.hash_map.toast('В документе отстутствуют артикулы')
                return
            self._set_vision_settings(articles=articles)
            self.hash_map.put('RunCV', 'OcrArticleRecognition')

        elif listener == 'ActiveCV':
            if not noClass('articles_ocr_ncl').get('button_manage_articles'):
                return
            noClass('articles_ocr_ncl').delete('button_manage_articles')
            finded_articles = noClass('articles_ocr_ncl').get('finded_articles')
            if finded_articles is None:
                self.hash_map.toast('Артикулы не найдены')
                return
        elif listener in ['ON_BACK_PRESSED', 'BACK_BUTTON']:
            if noClass('articles_ocr_ncl').get('finded_articles'):
                noClass('articles_ocr_ncl').delete('finded_articles')
                return
            self.hash_map.remove('rows_filter')
            self.hash_map.put('current_first_element_number', '0')
            self.hash_map.put('items_on_page_click', '')
            self.hash_map.put("SearchString", "")
            self.hash_map.put("ShowScreen", "Документы")

        elif self._is_result_positive('confirm_verified'):
            id_doc = self.hash_map['id_doc']
            self.service.mark_verified()
            self.hash_map.put("SearchString", "")
            self.hash_map.show_screen("Документы")

        elif listener == 'btn_doc_mark_verified':
            self.hash_map.show_dialog('confirm_verified', 'Завершить документ?', ['Да', 'Нет'])

    def _set_vision_settings(self, articles: List[str]):
        settings = {
            "values_list": ';'.join(articles),
            "min_length": len(min(articles, key=len)),
            "max_length": len(max(articles, key=len)),
        }
        noClass('articles_ocr_ncl').put('articles_ocr_settings', json.dumps(settings), True)

    def _open_series_screen(self, doc_row_key):
        screen_values = {
            'doc_row_id': doc_row_key,
            'title': 'Серии',
            'use_adr_docs_tables': '0'
        }

        screen = create_screen(
            self.hash_map,
            SeriesSelectScreen,
            screen_values=screen_values
        )
        screen.show()

    def _open_goods_select_screen(self, doc_row_id):
        if len(self.table_data) == 2:
            first_element_page = self.table_data[1]['key']
            first_element_list = first_element_page
        elif len(self.table_data) > 2:
            first_element_page = self.table_data[1]['key']
            first_element_list = self.table_data[2]['key']
        else:
            return

        table_index_data = self.service.get_table_index_data(
            self.id_doc, first_element_page, first_element_list
        )

        screen = GoodsSelectScreen(
            self.hash_map,
            id_doc=self.id_doc,
            table_index_data=table_index_data,
            doc_row_id=doc_row_id,
            control=self.hash_map['control']
        )
        screen.show()

    def _set_visibility_on_start(self):
        finded_articles = '-1' if noClass('articles_ocr_ncl').get('finded_articles') else '1'
        self.hash_map.put('Show_btn_doc_mark_verified', finded_articles)
        self.hash_map.put('Show_doc_date', finded_articles)
        self.hash_map.put('Show_warehouse', finded_articles)
        self.hash_map.put('Show_countragent', finded_articles)
        self.hash_map.put('Show_finded_by_article', str(-int(finded_articles)))


# ^^^^^^^^^^^^^^^^^^^^^ DocDetails ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== Goods select =============================


class BaseGoodSelect(Screen):
    def __init__(self, hash_map: HashMap, **kwargs):
        super().__init__(hash_map, **kwargs)
        self.id_doc = ''
        self.doc_row_id = ''
        self.service = DocService(self.id_doc)
        self.allow_fact_input = self.rs_settings.get('allow_fact_input') or False
        self.current_toast_message = ''
        self.hash_map_keys = ['item_name', 'article', 'property', 'price', 'unit', 'qtty_plan', 'qtty']
        self.screen_data = {}
        self.delta = 0.0
        self.new_qty = 0.0
        self.control = kwargs.get('control', False)
        self.is_group_scan = False
        self.use_series = False

    def init_screen(self):
        self._set_delta(reset=True)
        self.use_series = int(self.screen_data.get('use_series', 0))

    def on_start(self):
        self._set_visibility()
        self.hash_map['new_qtty'] = self._format_quantity(self.new_qty)

    def on_input(self):
        listeners = {
            'btn_print': self.print_ticket,
            'barcode': self._process_the_barcode,
            'btn_doc_good_barcode': self._open_register_barcode_screen,
            'btn_series_show': self._open_series_screen,
            'btn_input_qtty': self._show_dialog_qtty,
            'btn_marks_show': self._open_marks_screen,
            'btn_to_series': self._open_series_screen,
        }
        if self.listener in listeners:
            listeners[self.listener]()
        elif self.listener in ['btn_ok', "btn_cancel", 'BACK_BUTTON', 'ON_BACK_PRESSED']:
            self._save_and_close()
        elif self._is_result_positive('modal_dialog_input_qtty'):
            self._set_qty_result()
        elif 'ops' in self.listener:
            self._ops_listener()

        self.hash_map.no_refresh()

    def _ops_listener(self):
        set_value = float(self.listener[4:])
        self._set_delta(set_value)

    def _save_and_close(self):
        if self._check_qty_control():
            self._update_doc_table_qty(self.new_qty)
            self._set_delta(reset=True)

            self.service.set_doc_status_to_upload(self.id_doc)
            self._back_screen()

    def _check_qty_control(self):
        if self.new_qty < 0:
            self.hash_map.toast('Итоговое количество меньше 0')
            self.hash_map.playsound('error')
            self._set_delta(reset=True)
            return False

        if self.control and self.new_qty > self.screen_data['qtty_plan']:
            self.toast('Количество план в документе превышено')
            self.hash_map.playsound('error')
            self._set_delta(reset=True)
            return False

        return True

    def _update_doc_table_qty(self, qty):
        update_data = {
            'sent': 0,
            'qtty': float(qty) if qty else 0,
        }
        self._update_doc_table_row(data=update_data, row_id=self.doc_row_id)

    def _process_the_barcode(self):
        self._listener_not_implemented()

    def _get_float_value(self, value) -> float:
        if value and re.match("(^\d*\.?\d*$)", value):
            return float(value)
        else:
            return 0.0

    def _set_delta(self, value: float = 0.0, reset: bool = False):
        if reset:
            self.delta = 0
            self.new_qty = self.screen_data['qtty']
        else:
            self.delta = value
            self.new_qty += self.delta

        self.hash_map['new_qtty'] = self._format_quantity(self.new_qty)

    def _set_result_qtty(self, delta):
        new_qtty = float(self.hash_map.get('qtty') or 0) + delta
        new_qtty = str(self._format_quantity(new_qtty))
        self.hash_map.put('new_qtty', new_qtty)

    def _back_screen(self):
        self.hash_map.show_screen("Документ товары")

    def print_ticket(self):
        barcode = db_services.BarcodeService().get_barcode_from_doc_table(str(self.doc_row_id))

        data = {'Номенклатура': 'item_name',
                'Артикул': 'article',
                'Характеристика': 'property',
                'Цена': 'price',
                'ЕдИзм': 'unit',
                'Ключ': 'key',
                'Валюта': 'price_type'}

        for key in data:
            data[key] = self.hash_map.get(data[key])
        data['barcode'] = barcode if barcode else '0000000000000'
        PrintService(self.hash_map).print(data)

    def _open_series_screen(self):
        screen = SeriesSelectScreen(
            hash_map=self.hash_map,
            doc_row_id=self.doc_row_id,
            parent=self,
            is_group_scan=self.is_group_scan
        )
        screen.show_process_result()

    def _open_register_barcode_screen(self):
        init_data = {
            'item_id': self.screen_data.get('item_id', ''),
            'property_id': self.screen_data.get('property_id', ''),
            'unit_id': self.screen_data.get('unit_id', '')
        }
        screen = BarcodeRegistrationScreen(self.hash_map, **init_data)
        screen.parent_screen = self
        screen.show_process_result(init_data)

    def _open_marks_screen(self):
        table_data = self._get_marks_data(self.doc_row_id)
        if not table_data:
            self.toast('У текущего товара нет марок в документе.')
            return

        screen_args = {
            'title': 'Марки товара',
            'table_data': json.dumps(table_data),
            'table_header': json.dumps({'mark_code': 'Марка'}),
            'enumerate': True
        }
        screen = ShowItemsScreen(self.hash_map, self.rs_settings)
        screen.parent_screen = self
        screen.show_process_result(screen_args)

    def _get_marks_data(self, doc_row_id):
        return self.service.get_marks_data(self.id_doc, doc_row_id)

    def _update_doc_table_row(self, data: Dict, row_id):
        update_data = {
            'sent': 0,
            'd_qtty': float(data['qtty']),
            'qtty': float(data['qtty']),
        }

        self.service.update_doc_table_row(data=update_data, row_id=row_id)
        self.service.set_doc_status_to_upload(self.hash_map.get('id_doc'))

    def _show_dialog_qtty(self):
        if self.hash_map.get('use_series') == "1":
            self._open_series_screen()
            return

        self.hash_map['delta'] = 0.0
        self.hash_map['FocusField'] = 'delta'
        layout = '''{
            "type": "LinearLayout",
            "Variable": "",
            "orientation": "horizontal",
            "height": "wrap_content",
            "width": "match_parent",
            "weight": "0",
            "Elements": [
                {
                    "Value": "@delta",
                    "Variable": "delta",
                    "height": "wrap_content",
                    "width": "match_parent",
                    "weight": "0",
                    "type": "EditTextNumeric"
                    
                }
            ]
        }'''
        self.hash_map.show_dialog(
            'modal_dialog_input_qtty',
            title=f"Введите количество для добавления:",
            dialog_layout=layout
        )

    def _set_qty_result(self):
        self._set_delta(self._get_float_value(self.hash_map['delta']))

    def _set_visibility(self):
        allow_fact_input = self.allow_fact_input and not int(self.use_series)
        self.hash_map.put("Show_fact_qtty_input", '1' if allow_fact_input else '-1')
        self.hash_map.put("Show_fact_qtty_note", '-1' if allow_fact_input else '1')

        self.hash_map['Show_btn_to_series'] = int(self.use_series)


class GoodsSelectScreen(BaseGoodSelect):
    screen_name = 'Товар выбор'
    process_name = 'Документы'

    def __init__(
            self,
            hash_map: HashMap,
            id_doc,
            doc_row_id,
            table_index_data,
            **kwargs
    ):
        super().__init__(hash_map, **kwargs)
        self.id_doc = id_doc
        self.table_index_data: list = table_index_data
        self.allow_fact_input = self.rs_settings.get('allow_fact_input') or False
        self.doc_row_id = doc_row_id
        self.current_index = 0

    def init_screen(self):
        self.current_index = self.table_index_data.index(self.doc_row_id)
        self._update_hash_map_keys()
        super().init_screen()

    def on_start(self):
        super().on_start()

    def on_input(self):
        listeners = {
            'btn_next_good': lambda: self._goods_selector('next'),
            'btn_previous_good': lambda: self._goods_selector("previous"),
        }
        if self.listener in listeners:
            listeners[self.listener]()
        else:
            super().on_input()

    def _update_hash_map_keys(self):
        self._init_screen_data()
        self.hash_map.put_data({
            key: self._format_quantity(self.screen_data.get(key, 0))
            if key in ['qtty_plan', 'qtty'] else self.screen_data.get(key, '')
            for key in self.hash_map_keys
        })
        self.hash_map['item_position'] = f'{self.current_index+1} / {len(self.table_index_data)}'

    def _init_screen_data(self):
        self.doc_row_id = self.table_index_data[self.current_index]
        self.screen_data = self.service.get_doc_row_data(self.doc_row_id)

    def _goods_selector(self, action, index=None):
        if not self._check_qty_control():
            return

        self._update_doc_table_qty(self.new_qty)

        if action == 'next':
            new_index = self.current_index+1 if (self.current_index+1 < len(self.table_index_data)) else 0
            self.current_index = new_index
        elif action == 'previous':
            new_index = len(self.table_index_data)-1 if (self.current_index-1 < 0) else self.current_index-1
            self.current_index = new_index
        elif action == 'index' and not index is None:
            self.current_index = index

        self._update_hash_map_keys()
        self._set_visibility()
        self._set_delta(reset=True)

    def _process_the_barcode(self):
        barcode = self.hash_map.get('barcode_good_select')

        if not barcode:
            return

        res = self.service.get_doc_row_by_barcode(barcode)
        if res:
            index = self.table_index_data.index(res['id'])
            if self.current_index != index:
                self._goods_selector(action='index', index=index)

            if not int(self.screen_data['use_series']):
                self._set_delta(res['ratio'])
            self._set_visibility()
        else:
            self.hash_map.playsound('error')
            self.hash_map.toast(self.current_toast_message or f'Штрихкод не найден в документе!')


class GroupScanItemScreen(GoodsSelectScreen):
    screen_name = 'Товар выбор'
    process_name = 'Групповая обработка'

    def __init__(self, hash_map, **kwargs):
        super().__init__(hash_map, **kwargs)
        self.is_group_scan = True

    def init_screen(self):
        self.service.is_group_scan = True
        super().init_screen()

    def on_start(self):
        super().on_start()

    def on_input(self):
        super().on_input()

    def _process_the_barcode(self):
        super()._process_the_barcode()

    def _update_doc_table_row(self, data: Dict, row_id):
        update_data = {
            'sent': 0,
            'd_qtty': data['qtty'],
        }
        self.service.update_doc_table_row(data=update_data, row_id=row_id)
        self.service.set_doc_status_to_upload(self.hash_map.get('id_doc'))
        self._add_new_qty_to_queue()

    def _save_and_close(self):
        super()._save_and_close()
        self.hash_map.remove('stop_sync_doc')

    def _add_new_qty_to_queue(self):
        total_delta = float(self.new_qty) - self.screen_data['qtty']
        if total_delta == 0:
            return

        insert_to_queue = {
            "id_doc": self.screen_data.get('id_doc'),
            "id_good": self.screen_data.get("item_id"),
            "id_properties": self.screen_data.get("property_id"),
            "id_series": '',
            "id_unit": self.screen_data.get("unit_id"),
            "id_cell": "",
            "d_qtty": total_delta,
            'row_key': self.doc_row_id,
            "sent": False,
            "price": self.screen_data.get("price"),
            "id_price": ""
        }

        barcode_worker = BarcodeWorker(self.hash_map.get("id_doc"))
        barcode_worker.queue_update_data = insert_to_queue
        barcode_worker.update_document_barcode_data()


class BarcodeRegistrationScreen(Screen):
    screen_name = 'BarcodeRegistration'
    process_name = 'BarcodeRegistration'

    def __init__(self, hash_map: HashMap, **kwargs):
        super().__init__(hash_map)
        self.service = BarcodeService()
        self.goods_service = GoodsService()
        self.init_values = {
            'item_id': kwargs.get('item_id', ''),
            'property_id': kwargs.get('property_id', ''),
            'unit_id': kwargs.get('unit_id', ''),
        }
        self.title = 'Регистрация штрихкода'
        self.db_tables_matching = {
            'property_select': 'RS_properties',
            'unit_select': 'RS_units',
            'RS_properties': 'property_id',
            'RS_units': 'unit_id',
        }
        self.screen_data = {}
        self.hash_map_keys = ['scanned_barcode', 'property_select', 'unit_select', 'barcodes_data']

    def init_screen(self):
        init_data = self.goods_service.get_item_data_by_condition(**self.init_values)
        self.screen_data = self.init_values

        if init_data:
            self.hash_map['scanned_barcode'] = ''
            self.hash_map['item_name'] = init_data['name']
            self.hash_map['property_select'] = init_data['property']
            self.hash_map['unit_select'] = init_data['unit']

            self._fill_barcodes_table()

    def on_start(self):
        self.hash_map.set_title(self.title)

    def on_input(self):
        listeners = {
            'property_select': self._select_item,
            'unit_select': self._select_item,
            'barcode': self._barcode_scanned,
            'btn_ok': self._handle_ok,
            'ON_BACK_PRESSED': self._finish_process,
            'BACK_BUTTON': self._finish_process,
        }
        if self.listener in listeners:
            listeners[self.listener]()

        self.hash_map.no_refresh()

    def _select_item(self):
        hash_map_key = self.listener
        table_name = self.db_tables_matching[hash_map_key]
        screen_data_key = self.db_tables_matching[table_name]

        screen = SelectItemScreen(
            self.hash_map,
            table_name=table_name,
            parent=self
        )
        screen.show(
            result_handler=lambda result: self._select_item_result(
                result=result,
                hash_map_key=hash_map_key,
                screen_data_key=screen_data_key
            )
        )

    def _select_item_result(self, result, hash_map_key, screen_data_key):
        self.hash_map[hash_map_key] = result.get('name', '-')
        self.screen_data[screen_data_key] = result.get('id', '')
        self._fill_barcodes_table()
        self.hash_map.refresh_screen()

    def _barcode_scanned(self):
        scanned_barcode = self.hash_map.get("barcode")
        self._check_barcode(scanned_barcode)

    def _handle_ok(self):
        scanned_barcode = self.hash_map.get("scanned_barcode")
        if not scanned_barcode:
            self.hash_map.toast("Штрихкод не отсканирован")
        elif self._check_barcode(scanned_barcode):

            barcode_data = {
                "id_good": self.screen_data['item_id'],
                "barcode": scanned_barcode,
                "id_property": self.screen_data.get("property_id", ''),
                "id_unit": self.screen_data.get("unit_id", ''),
            }

            self._save_barcode(barcode_data)
            self._fill_barcodes_table()
            self.hash_map.refresh_screen()

    def _save_barcode(self, barcode_data):
        self.service.add_barcode(barcode_data)

        buffer = ExchangeQueueBuffer('barcodes')
        buffer.save_data_to_send(barcode_data, pk='barcode')

    def _check_barcode(self, barcode):
        barcode_data = self.goods_service.get_values_from_barcode("barcode", barcode)

        if barcode_data:
            self.hash_map.playsound('error')
            self.hash_map.toast(f'Штрихкод {barcode} присутствует в базе данных')
            self.hash_map['scanned_barcode'] = ''
            return False
        else:
            self.hash_map['scanned_barcode'] = barcode

        return True

    def _fill_barcodes_table(self):
        barcodes_data = self.service.get_barcodes_by_data(self.screen_data)
        table_data = self._prepare_table_data(barcodes_data)
        self.hash_map['barcodes_data'] = self._get_barcodes_table_view(table_data).to_json()

    def _prepare_table_data(self, barcodes_data):
        table_data = [{'_layout': self._get_table_header()}, *barcodes_data]
        return table_data

    def _get_table_header(self):
        return widgets.LinearLayout(
                self.LinearLayout(
                    self.TextView('Штрихкод'),
                    weight=1,
                ),
                self.LinearLayout(
                    self.TextView('Характеристика'),
                    weight=1,
                ),
                self.LinearLayout(
                    self.TextView('Упаковка'),
                    weight=1
                ),
                orientation='horizontal',
                height="match_parent",
                width="match_parent",
                BackgroundColor='#FFFFFF'
            )

    @staticmethod
    def _get_barcodes_table_view(table_data):
        table_view = widgets.CustomTable(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@barcode',
                        TextSize=15,
                        width='match_parent',
                        TextBold = True
                        ),
                    weight=1,
                    width='match_parent',
                    height='match_parent',
                    StrokeWidth=1
                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@property',
                        TextSize=15,
                        width='match_parent'
                        ),
                    weight=1,
                    width='match_parent',
                    height='match_parent',
                    StrokeWidth=1
                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@unit',
                        TextSize=15,
                        width='match_parent'
                        ),
                    weight=1,
                    width='match_parent',
                    height='match_parent',
                    StrokeWidth=1
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

    def _finish_process(self):
        for key in self.hash_map_keys:
            self.hash_map.remove(key)
        self._finish_process_result()


# ^^^^^^^^^^^^^^^^^^^^^ Goods select ^^^^^^^^^^^^^^^^^^^^^^^^^^^^


# ==================== Goods(Process) =============================

class GoodsListScreen(Screen):
    screen_name = 'Товары список'
    process_name = 'Товары'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = GoodsService()

    def on_start(self) -> None:
        cards_data = self._get_goods_list_data(self.hash_map.get('selected_goods_type'))
        goods_cards = self._get_goods_cards_view(cards_data)
        self.hash_map['goods_cards'] = goods_cards.to_json()
        self.hash_map['return_selected_data'] = ""

    def on_input(self):
        listener = self.listener
        if listener == "CardsClick":
            screen_values = {'item_id': self.hash_map['selected_card_key']}
            ItemCard(self.hash_map, self.rs_settings).show(args=screen_values)
        elif listener == "select_goods_type":
            self.hash_map.show_screen("Выбор категории товаров")
        elif listener == "ON_BACK_PRESSED":
            self.hash_map.put("FinishProcess", "")
        elif listener == 'barcode':
            self._identify_barcode_goods()

        self.hash_map.no_refresh()

    def _get_goods_list_data(self, selected_good_type=None) -> list:
        results = self.service.get_goods_list_data(selected_good_type)
        cards_data = []
        for record in results:
            single_card_data = {
                'key': record['id'],
                'code': record['code'],
                'name': record['name'],
                'art': record['art'] if record['art'] else "—",
                'unit': record['unit'] if record['unit'] else "—",
                'type_good': record['type_good'],
                'description': record['description'] if record['description'] else "—"
            }
            cards_data.append(single_card_data)

        return cards_data

    def _get_goods_cards_view(self, cards_data):
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')
        card_text_size = self.rs_settings.get('CardTextSize')

        goods_cards = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@name',
                    width='match_parent',
                    gravity_horizontal='left',
                    TextSize=card_title_text_size,
                    TextColor='#7A005C'
                ),
                widgets.TextView(
                    Value='@code',
                    TextSize=card_text_size,
                ),
                widgets.TextView(
                    Value='@art',
                    TextSize=card_text_size,
                ),
                widgets.TextView(
                    Value='@unit',
                    TextSize=card_text_size,
                ),
                widgets.TextView(
                    Value='@type_good',
                    TextSize=card_text_size,
                ),

                orientation='vertical',
                width='match_parent',
            ),
            options=widgets.Options().options,
            cardsdata=cards_data
        )

        return goods_cards

    def _identify_barcode_goods(self):
        if self.hash_map.get('barcode'):
            barcode = self.hash_map.get('barcode')
            values = self.service.get_values_from_barcode("barcode", barcode)
            if values:
                self.hash_map['item_id'] = values[0]['id_good']
                ItemCard(self.hash_map, self.rs_settings).show()
            else:
                self.toast('Товар не распознан по штрихкоду')
                self.hash_map.playsound('error')


class SelectGoodsType(Screen):
    screen_name = 'Выбор категории товаров'
    process_name = 'Товары'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = GoodsService()

    def on_start(self):
        goods_types_data = self._get_goods_types_data()
        goods_types_cards = self._get_goods_types_cards_view(goods_types_data)
        self.hash_map['goods_types_cards'] = goods_types_cards.to_json()
        self.hash_map['return_selected_data'] = ""

    def on_input(self):
        listener = self.listener
        if listener == "CardsClick":
            card_data = self.hash_map.get("selected_card_data", from_json=True)
            type_id = card_data['key']
            type_name = card_data['name']
            self.hash_map.put('select_goods_type', type_name)
            self.hash_map.put('selected_goods_type', type_id)
            self.hash_map.put("ShowScreen", "Товары список")
        elif listener == "ON_BACK_PRESSED":
            self.hash_map.put('select_goods_type', "")
            self.hash_map.put('selected_goods_type', "")
            self.hash_map.put("BackScreen", "")

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _get_goods_types_data(self):
        goods_types_data_result = self.service.get_all_goods_types_data()
        goods_types_data = []
        for record in goods_types_data_result:
            single_card_data = {
                'key': record['id'],
                'name': record['name'],
            }
            goods_types_data.append(single_card_data)
        return goods_types_data

    def _get_goods_types_cards_view(self, goods_types_data):
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')

        type_cards = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@name',
                    width='match_parent',
                    gravity_horizontal='left',
                    TextSize=card_title_text_size,
                    TextColor='#000000'
                ),

                orientation='vertical',
                width='match_parent',
            ),
            options=widgets.Options().options,
            cardsdata=goods_types_data
        )

        return type_cards


class ItemCard(Screen):
    screen_name = 'Карточка товара'
    process_name = 'Товары'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.screen_values = {
            'item_id': self.hash_map['item_id'],
        }
        self.service = GoodsService()

    def on_start(self):
        self.init_screen()

    def on_input(self):
        listeners = {
            'ON_BACK_PRESSED': self._back_screen,
            'CardsClick': self._print_ticket,
            'btn_print': self._print_ticket,
            'to_prices': self._to_prices,
            'to_balances': self._to_balances,
            'btn_item_good_barcode': self._handle_barcode_register,

        }
        if self.listener in listeners:
            listeners[self.listener]()

        self.hash_map.no_refresh()

    def on_post_start(self):
        item_properties = self.service.get_values_from_barcode("id_good", self.screen_values['item_id'])

        if item_properties:
            variants_cards_data = self._get_variants_cards_data(item_properties)
            variants_cards = self._get_variants_cards_view(variants_cards_data)
            self.hash_map['barcode_cards'] = variants_cards.to_json()
            self.hash_map.put("load_info", "")
        else:
            self.hash_map.put("load_info", "Данные о характеристиках отсутствуют")

    def init_screen(self):
        super().init_screen()
        item_data = self.service.get_item_data_by_id(self.screen_values['item_id'])
        if not item_data:
            return
        put_data = {
            "good_name": item_data['name'],
            "good_art": item_data['art'] if item_data['art'] else "—",
            "good_code": item_data['code'],
            "good_descr": item_data['description'] if item_data['description'] else "—",
            "good_type": item_data['type_good'],
        }
        self.hash_map.put_data(put_data)

    def _back_screen(self):
        self._clear_screen_values()
        self.hash_map.remove('barcode_cards')
        self.hash_map.show_screen(self.hash_map['parent_screen'])

    def _to_balances(self):
        from sm_services import GoodsBalancesItemCard
        dict_data = {
            'input_item_id': self.hash_map.get('item_id'),
            'item_art_input': self.hash_map.get('good_art'),
            'selected_object_name': f'{self.hash_map.get("good_name")}, {self.hash_map.get("good_code")}',
            'object_name': self.hash_map.get('good_name'),
            "return_to_item_card": "true",
        }
        screen = GoodsBalancesItemCard(self.hash_map, parent=self, screen_data=dict_data)
        screen.show_process_result()

    def _to_prices(self):
        from sm_services import GoodsPricesItemCard
        dict_data = {
            'input_good_id': self.hash_map.get('item_id'),
            'input_good_art': self.hash_map.get('good_art'),
            'prices_object_name': f'{self.hash_map.get("good_name")}, {self.hash_map.get("good_code")}',
            "return_to_item_card": "true",
            'object_name': self.hash_map.get('good_name'),
        }
        screen = GoodsPricesItemCard(self.hash_map, parent=self, screen_data=dict_data)
        screen.show_process_result()

    def _handle_barcode_register(self):
        init_data = {
            'item_id': self.hash_map.get('item_id'),
            'property_id': '',
            'unit_id': ''
        }
        BarcodeRegistrationScreen(self.hash_map, **init_data).show_process_result(init_data)

    @staticmethod
    def _get_variants_cards_data(item_properties):
        variants_cards_data = []
        for i, element in enumerate(item_properties):
            variants_cards_data.append(
                {
                    "key": str(i),
                    "barcode": element['barcode'],
                    "properties": element['property'] if element['property'] else "",
                    "unit": element['unit'],
                    "series": element['series']
                }
            )
        return variants_cards_data

    def _get_variants_cards_view(self, cards_data):
        card_title_text_size = self.rs_settings.get('CardTitleTextSize') if self.rs_settings.get(
            'CardTitleTextSize') else 20
        card_text_size = self.rs_settings.get('CardTextSize') if self.rs_settings.get('CardTextSize') else 15

        variants_cards = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@properties',
                        width='match_parent',
                        gravity_horizontal='center',
                        TextSize=card_title_text_size,
                        TextColor='#000000'
                    ),
                    orientation='horizontal',
                    width='match_parent',
                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@unit',
                        width='match_parent',
                        gravity_horizontal='left',
                        TextSize=card_text_size,
                        TextColor='#000000',
                        weight=1
                    ),
                    widgets.TextView(
                        Value='@barcode',
                        width='match_parent',
                        gravity_horizontal='left',
                        TextSize=card_text_size,
                        TextColor='#000000',
                        weight=1
                    ),
                    orientation='horizontal',
                    width='match_parent',
                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@series',
                        width='match_parent',
                        gravity_horizontal='center',
                        TextSize=card_text_size,
                        TextColor='#000000'
                    ),
                    orientation='horizontal',
                    width='match_parent',
                ),
                orientation='vertical',
                width='match_parent',
            ),
            options=widgets.Options().options,
            cardsdata=cards_data
        )
        return variants_cards

    def _print_ticket(self):
        current_card = self._get_selected_card_data()
        data_dict = {
            'barcode': current_card.get('barcode', '0000000000000'),
            'Номенклатура': self.hash_map.get('good_name'),
            'Характеристика': current_card.get('properties', ''),
            'Упаковка': current_card.get('unit', '')
        }
        PrintService(self.hash_map).print(data_dict)

    def _get_selected_card_data(self) -> dict:
        result = {}
        card_key = self.hash_map.get('selected_card_key')
        cards = self.hash_map.get_json("barcode_cards")

        if card_key and cards:
            result = cards['customcards']['cardsdata'][int(card_key)]

        return result

class ItemCardOfflineScreen(ItemCard):

    def _to_prices(self):
        self.hash_map.show_dialog('prices_not_available_modal', title='В этом продукте запрос цен недоступен')

    def _to_balances(self):
        self.hash_map.show_dialog('balances_not_available_modal', title='В этом продукте запрос остатков недоступен')

    def _print_ticket(self):
        self.hash_map.show_dialog('print_ticket_not_available_modal', title='В этом продукте печать недоступна')

# ^^^^^^^^^^^^^^^^^^^^^ Goods(Process) ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== Series =============================


class SeriesSelectScreen(Screen):
    process_name = 'SeriesProcess'
    screen_name = 'SeriesSelectScreen'

    def __init__(self, hash_map: HashMap, doc_row_id, **kwargs):
        super().__init__(hash_map, **kwargs)
        self.doc_row_id = doc_row_id
        self.use_adr_docs_tables = kwargs.get('use_adr_docs_tables', False)
        self.db_service = None
        self.screen_data = {}
        self.hash_map_keys = ['qtty', 'qtty_plan', 'price', 'item_name', 'article', 'property', 'unit']
        self.format_cards_data = {
            'best_before': lambda value: f'годен до: {self._format_date(value)}' if value else '',
            'production_date': lambda value: f'дата произв.: {self._format_date(value)}' if value else '',
            'qtty': lambda value: f'кол-во: {self._format_quantity(value)}' if value else '',
        }
        self.series_barcode_data = {}
        self.total_qty = 0
        self.series_item_data_to_save = None
        self.series_count = 0
        self.is_group_scan = kwargs.get('is_group_scan', False)
        self.use_series = False

    def init_screen(self):
        if self.db_service is None:
            self.db_service = db_services.SeriesService(self.doc_row_id)
            self.db_service.is_group_scan = self.is_group_scan

        self.screen_data = self.db_service.get_screen_data(self.doc_row_id)
        self.total_qty = self.screen_data['qtty']
        self.use_series = bool(self.screen_data['use_series'])
        self._update_total_qty()
        self._update_hash_map_keys()
        self._update_series_cards()

        self.hash_map.put('return_selected_data')

    def on_start(self):
        self.hash_map.set_title('Выбор серии')
        self._save_new_series_item()
        self._set_vision_settings()

    def on_input(self):
        listeners = {
            'CardsClick': self._cards_click,
            'btn_add_series': self._add_new_series,
            'barcode': self._barcode_listener,
            'vision': self._vision_listener,
            'vision_cancel': lambda: noClass('ocr_nosql_counter').destroy(),
            'btn_print': self._print_ticket,
            'btn_series_add_barcode': self._btn_add_barcode,
            'btn_ocr_serial_template_settings': self._osr_settings,
            'LayoutAction': self._layout_action,
            'ON_BACK_PRESSED': self._back_screen,
            'BACK_BUTTON': self._back_screen,
        }

        if self.listener in listeners:
            listeners[self.listener]()
        elif self._is_result_positive('confirm_delete'):
            self._delete_series_item()

    def show(self, args=None):
        self.show_process_result(args)

    def _update_hash_map_keys(self):
        self.hash_map.put_data({
            key: self._format_quantity(self.screen_data.get(key, 0))
            if key in ['qtty_plan', 'qtty'] else self.screen_data.get(key, '')
            for key in self.hash_map_keys
        })

    def _update_series_cards(self):
        series_data = self.db_service.get_series_data(self.doc_row_id)
        if series_data:
            self.series_barcode_data = {
                row['number']: row for row in series_data if row['number']
            }
            self.series_count = len(series_data)
            self.use_series =  bool(self.series_count) or self.use_series

            doc_cards = self._get_doc_cards_view(self._prepare_table_data(series_data))
            self.hash_map['series_cards'] = doc_cards.to_json()
            self.hash_map.put('Show_empty_series', '-1')
        else:
            self.hash_map['series_cards'] = ''
            self.hash_map.put('Show_empty_series', '1')

    def _cards_click(self):
        card_data = self._get_selected_card_data()
        series_item_data = self._get_series_item_data_by_number(card_data['number'])
        self._open_series_item_screen(series_item_data)

    def _add_new_series(self):
        series_item_data = self._get_series_item_data_by_number()
        series_item_data['qtty'] = 1 if self.series_count else max(self.total_qty, 1)
        self._open_series_item_screen(series_item_data)

    def _barcode_listener(self):
        barcode = self.hash_map['barcode']
        self._add_series_item_on_scanning(barcode)

    def _vision_listener(self):
        number = noClass('ocr_nosql').get('ocr_result')
        if number:
            noClass('ocr_nosql').delete('ocr_result')
            self._add_series_item_on_scanning(number)
            noClass('ocr_nosql_counter').destroy()

    def _osr_settings(self):
        noClass('ocr_nosql').put('show_process_result', True, True)
        self.hash_map.show_process_result('OcrTextRecognition',
                                          'SerialNumberOCRSettings')

    def _add_series_item_on_scanning(self, number):
        """
        # По номеру ищем серию, инициализируем данные для записи в БД,
        # количество новой серии считаем по количеству товара если нет серий на этом этапе
        # при событии on_start данные должны сохраниться в БД
        """

        series_item_qtty = 1 if self.series_count else max(self.total_qty, 1)
        series_item_data = self._get_series_item_data_by_number(number)
        series_item_data['qtty'] += series_item_qtty

        self.series_item_data_to_save = series_item_data

    def _get_series_item_data_by_number(self, number=''):
        series_item_data = self.series_barcode_data.get(number)
        if not series_item_data:
            news_series_item_data = {**self.screen_data}
            news_series_item_data.update({'name': number, 'number': number, 'qtty': 0})
            series_item_data = db_models.SeriesItemModel(**news_series_item_data).dict()

        return series_item_data

    def _save_new_series_item(self):
        """
        Метод для добавления новой или обновления существующей серии.
        Вызывается в событии on_start для обработки ситуации когда данные для записи добавлены из другого экрана.
        """

        if self.series_item_data_to_save:
            self.db_service.update_series_item_data(
                db_models.SeriesItemModel(**self.series_item_data_to_save)
                .dict(by_alias=True, exclude_none=True)
            )
            self.series_item_data_to_save = None
            self._update_series_cards()
            self._update_total_qty()

    def _update_total_qty(self):
        self.total_qty = self.db_service.get_total_qtty(**self.screen_data)
        self.hash_map['qtty'] = self._format_quantity(self.total_qty)
        self.db_service.update_total_qty(
            qty=self.total_qty,
            row_id=self.doc_row_id,
            use_series=int(self.use_series)
        )

    def _open_series_item_screen(self, series_item_data):
        screen = SeriesItem(
            self.hash_map,
            parent=self,
            series_item_data=series_item_data
        )
        screen.show()

    def _layout_action(self):
        layout_listener = self.hash_map.get('layout_listener')

        if layout_listener == 'Удалить':
            self.hash_map.show_dialog(
                listener='confirm_delete',
                title='Удалить серию?'
            )

    def _back_screen(self):
        self._update_total_qty()
        if self.parent_screen:
            self.parent_screen.new_qty = self.total_qty
            self.parent_screen.use_series = self.use_series
        self._finish_process()

    def _finish_process(self):
        super()._finish_process_result()

    def _prepare_table_data(self, series_data: List[dict]):
        table_data = [self._format_row_data(row_data) for row_data in series_data]
        return table_data

    def _format_row_data(self, row_data: dict):
        return {k: self.format_cards_data[k](v) if k in self.format_cards_data else v
                for k,v in row_data.items()}

    def _get_doc_cards_view(self, table_data):

        title_text_size = self.rs_settings.get("TitleTextSize")
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')
        card_date_text_size = self.rs_settings.get('CardDateTextSize')

        doc_cards = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@name',
                        width='match_parent',
                        gravity_horizontal='left',
                        weight=2
                    ),
                    widgets.TextView(
                        Value='@best_before',
                        TextSize=title_text_size,
                    ),
                    widgets.PopupMenuButton(
                        Value='Удалить',
                        Variable="menu_delete",
                    ),

                    orientation='horizontal',
                    width='match_parent',
                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@qtty',
                        TextBold=True,
                        TextSize=card_title_text_size
                    ),
                    widgets.TextView(
                        Value='@number',
                        TextBold=True,
                        TextSize=card_title_text_size,
                        TextColor='#0f03fc'
                    ),
                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value=' ',
                        width='match_parent',
                        gravity_horizontal='left',
                        weight=2
                    ),
                    widgets.TextView(
                        Value='@production_date',
                        TextSize=title_text_size,
                    ),

                    orientation='horizontal',
                    width='match_parent',

                ),
                width="match_parent"
            ),
            options=widgets.Options().options,
            cardsdata=table_data
        )

        return doc_cards

    def _delete_series_item(self):
        series_id = self.hash_map.get('card_data', from_json=True)['id']
        self.db_service.delete_series_item(int(series_id))
        self._update_series_cards()
        self._update_total_qty()

    def _set_vision_settings(self) -> None:
        serial_ocr_settings = noClass('ocr_nosql').get('serial_ocr_settings')
        if serial_ocr_settings:
            serial_ocr_settings = json.loads(serial_ocr_settings)
            self.hash_map.set_vision_settings(**serial_ocr_settings)
            noClass('ocr_nosql').put('from_screen', 'SeriesSelectScreen', True)

    def _print_ticket(self):
        # Получим первый баркод документа
        barcode = db_services.BarcodeService().get_barcode_from_doc_table(self.screen_values['doc_row_id'])
        data = {
            'Документ': 'doc_title',
            'Номенклатура': 'item_name',
            'Артикул': 'article',
            'Характеристика': 'property',
            'Цена': 'price',
            'ЕдИзм': 'unit',
            'Ключ': 'key',
        }
        for key in data:
            data[key] = self.hash_map.get(data[key])
        data['barcode'] = barcode if barcode else '0000000000000'
        PrintService(self.hash_map).print(data)

    def _btn_add_barcode(self):
        init_data = {
            'item_id':  self.screen_data.get('id_good', ''),
            'property_id':  self.screen_data.get('id_properties', ''),
            'unit_id':  self.screen_data.get('id_unit', '')
        }
        BarcodeRegistrationScreen(self.hash_map, **init_data).show_process_result(init_data)


class SeriesItem(Screen):
    process_name = 'SeriesProcess'
    screen_name = 'FillingSeriesScreen'

    def __init__(self, hash_map: HashMap, series_item_data=None, **kwargs):
        super().__init__(hash_map, **kwargs)
        self.screen_data = series_item_data or {}
        self.hash_map_keys = [
            'name', 'number', 'production_date', 'best_before', 'FillingSeriesScreen_qtty'
        ]
        self.data_to_save = None
        self.series_barcode_data = kwargs.get('series_barcode_data', {})
        self.is_new_item = kwargs.get('is_new_item', False)

    def init_screen(self):
        put_data = {
            'name': self.screen_data.get('name',''),
            'number': self.screen_data.get('number',''),
            'production_date': self.screen_data.get('production_date',''),
            'best_before': self.screen_data.get('best_before',''),
            'FillingSeriesScreen_qtty': self._str_to_int(self.screen_data.get('qtty',''))
        }

        self.hash_map.put_data(put_data)

    def on_start(self):
        pass

    def on_input(self):
        listeners = {
            'btn_save': self._btn_save_handler,
            'ON_BACK_PRESSED': self._back_screen,
            'BACK_BUTTON': self._back_screen,
        }
        if self.listener in listeners:
            listeners[self.listener]()

    def _btn_save_handler(self):
        """
        Обработчик проверяет валидность данных и формирует структуру для записи в БД
        подразумевается что запись в БД происходит в родительском классе
        """
        data_to_save = {**self.screen_data}
        data_to_save.update(
            {
                'qtty': self._get_qty(),
                'name': self.hash_map.get('name'),
                'best_before': self._format_date(self.hash_map.get('best_before'), default=''),
                'number': self.hash_map.get('number'),
                'production_date': self._format_date(self.hash_map.get('production_date'), default=''),
            }
        )

        if self._check_save_data(data_to_save):
            self.data_to_save = db_models.SeriesItemModel(**data_to_save).dict()
            if self.parent_screen:
                self.parent_screen.series_item_data_to_save = self.data_to_save
            self._back_screen()

    def _get_qty(self):
        return int(float(self.hash_map.get('FillingSeriesScreen_qtty')) or 0)

    def _check_save_data(self, data):
        series_number = data['number']

        if not data['name']:
            data['name'] = series_number

        if not bool(data['number'].strip()):
            self.hash_map.playsound('warning')
            self.toast('Не заполнен номер серии')
            return False

        if data['qtty'] <= 0:
            self.hash_map.playsound('warning')
            self.toast('Введите количество')
            return False

        if self.is_new_item and data['number'] in self.series_barcode_data:
            self.hash_map.playsound('warning')
            self.toast(f'Серия с номером с таким номером уже есть в документе')
            return False

        return True

    def _back_screen(self):
        for k in self.hash_map_keys:
            self.hash_map.remove(k)
        super()._back_screen()

    @staticmethod
    def _format_date(date_str, default=''):
        def _is_valid_date_format():
            pattern = r"^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.\d{4}$"
            return bool(re.match(pattern, date_str))

        if _is_valid_date_format():
            return date_str
        else:
            return default


    @staticmethod
    def _str_to_int(value: str) -> int:
        try:
            return int(float(value))
        except ValueError:
            return 0


# ^^^^^^^^^^^^^^^^^^^^^ Series ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== SelectItemScreen =============================

class SelectItemScreen(Screen):
    process_name = 'SelectItemProcess'
    screen_name = 'SelectItemScreen'

    def __init__(self, hash_map: HashMap, table_name, **kwargs):
        super().__init__(hash_map, **kwargs)

        self.table_name = table_name
        self.fields: List[str] = kwargs.get('fields', ['name'])
        self.result_listener = kwargs.get('result_listener', 'select_success')
        self.return_value_key = kwargs.get('return_value_key', 'selected_card')
        self.title = kwargs.get('title', 'Выбор значения')
        self.selected_card_data = {}
        self.db_service = db_services.SelectItemService(self.table_name)

    def on_start(self):
        self.hash_map.set_title(self.title)

    def on_input(self):
        listeners = {
            'CardsClick': self._cards_click,
            'ON_BACK_PRESSED': self._back_screen,
        }
        if self.listener in listeners:
            listeners[self.listener]()

        self.hash_map.no_refresh()

    def init_screen(self):
        self.db_service = db_services.SelectItemService(self.table_name)
        cards_data = self.db_service.get_select_data()
        cards = self._get_cards(cards_data)

        self.hash_map['SelectItemScreen_items_cards'] = cards.to_json()
        self.hash_map.put('return_selected_data')

    def show(self, result_handler=None, args=None):
        self.hash_map['SetResultListener'] = self.result_listener
        self.show_process_result(result_handler=result_handler)

    def _get_cards(self, cards_data):
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')
        card_text_size = self.rs_settings.get('CardTextSize')

        fields_views = []
        for field in self.fields:
            fields_views.append(
                widgets.LinearLayout(
                    widgets.TextView(
                        Value=f'@{field}',
                        width='match_parent',
                        gravity_horizontal='center',
                        TextSize=card_title_text_size,
                        TextColor='#000000',
                    ),
                    orientation='horizontal',
                    width='match_parent',
                )
            )

        cards = widgets.CustomCards(
            widgets.LinearLayout(
                *fields_views,
                width='match_parent',
            ),
            options=widgets.Options().options,
            cardsdata=cards_data
        )
        return cards

    def _cards_click(self):
        self.selected_card_data = self.hash_map.get('selected_card_data', from_json=True)
        self.hash_map.put(self.return_value_key, self.selected_card_data, to_json=True)
        self._finish_process()

    def _back_screen(self):
        self.hash_map.remove(self.return_value_key)
        self._finish_process()

    def _finish_process(self):
        self.hash_map.remove('SelectItemScreen_items_cards')
        self._finish_process_result(result=dict({'table_name': self.table_name}, **self.selected_card_data or {}))


class ShowItemsScreen(Screen):
    process_name = 'SelectItemProcess'
    screen_name = 'ShowItemsScreen'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.init_params = ['title', 'table_data', 'table_header', 'enumerate']
        self.enumerate=True
        self.table_data = []
        self.fields = []
        self.table_header = {}
        self.text_size = 15
        self.header_text_size = 15

    def init_screen(self):
        self.hash_map.set_title(self.hash_map['title'] or 'Список')
        self.enumerate = self.hash_map.get_bool('enumerate')
        self.table_data = self.hash_map.get_json('table_data')
        self.table_header = self.hash_map.get_json('table_header')

        if not self.table_data:
            raise ValueError ('table_data not initialized')

        if not self.table_header:
            self.table_header = {key: key for key in next(iter(self.table_data)).keys()}

        table_data = self._prepare_table_data()
        self.hash_map['items_table'] = self._get_table_view(table_data)

    def on_start(self):
        self.init_screen()

    def on_input(self):
        listeners = {
            'ON_BACK_PRESSED': self._back_screen,
        }
        if self.listener in listeners:
            listeners[self.listener]()

        self.hash_map.no_refresh()

    def _prepare_table_data(self):
        self.fields = list(self.table_header.keys())
        table_header_layout = {'_layout': self._get_table_header_view()}

        if self.enumerate:
            table_data = [dict(**{'pos': 'N'}, **self.table_header, **table_header_layout)]
            table_data += [dict(**{'pos': pos}, **row) for pos, row in enumerate(self.table_data, start=1)]
            return table_data
        else:
            table_data = [dict(**self.table_header, **table_header_layout)] + self.table_data
            return table_data

    def _get_table_header_view(self):
        return self._get_fields_layout(is_header=True)

    def _get_fields_layout(self, is_header=False, background_color='#FBE9E7', weight=1):
        if is_header:
            background_color = '#FFFFFF'
            text_size = self.header_text_size
        else:
            text_size = self.text_size

        if not self.table_data:
            return

        fields_layout = widgets.LinearLayout(
            orientation='horizontal',
            width='match_parent',
            BackgroundColor=background_color,
        )

        if self.enumerate:
            pos_layout = self._get_column_view(value='pos', text_size=text_size, weight=weight)
            fields_layout.append(pos_layout)

        fields_layout.append(
            widgets.LinearLayout(
                *[self._get_column_view(value=field, text_size=text_size, weight=weight) for field in self.fields],
                width='match_parent',
                orientation='horizontal',
                weight=8
            )
        )

        return fields_layout

    def _get_column_view(self, value, text_size=20, weight=1):
        return widgets.LinearLayout(
            widgets.TextView(
                Value=f'@{value}',
                gravity_horizontal='center',
                TextSize=text_size,
                width='match_parent'
            ),
            width='match_parent',
            height='match_parent',
            weight=weight,
            StrokeWidth=1,
        )

    def _get_table_view(self, table_data):
        table_view = widgets.CustomTable(
            widgets.LinearLayout(
                self._get_fields_layout(),
                width='match_parent',
            ),
            options=widgets.Options().options,
            tabledata=table_data
        )

        return table_view.to_json()

    def _back_screen(self):
        self._finish_process()


class ShowMarksScreen(ShowItemsScreen):
    process_name = 'SelectItemProcess'
    screen_name = 'ShowMarksScreen'

    def __init__(self, hash_map: HashMap, table_name, **kwargs):
        super().__init__(hash_map, table_name, **kwargs)

    def on_start(self):
        super().on_start()

    def on_input(self):
        super().on_input()

    def _prepare_table_data(self):
        self.fields = list(self.table_header.keys())
        table_header_layout = {'_layout': self._get_table_header_view()}

        if self.enumerate:
            table_data = [dict(**{'pos': 'N'}, **{'img': None}, **self.table_header, **table_header_layout)]
            table_data += [dict(**{'pos': pos}, **{'img': self._get_image_for_row(row)}, **row) for pos, row in enumerate(self.table_data, start=1)]
            return table_data
        else:
            table_data = [dict(**self.table_header, **table_header_layout)] + self.table_data
        return table_data

    def _get_image_for_row(self, row_data):
        if row_data.get("approved") == "1":
            return static_data.mark_green
        elif row_data.get("approved") == "0":
            return static_data.mark_pink
        return None

    def _get_fields_layout(self, is_header=False, background_color='#FFFFFF', weight=1):
        if is_header:
            background_color = '#FFFFFF'
            text_size = self.header_text_size
            text_bold = True
        else:
            text_size = self.text_size
            text_bold = False

        text_size = self.text_size

        fields_layout = widgets.LinearLayout(
            orientation='horizontal',
            width='match_parent',
            BackgroundColor=background_color,
        )

        if self.enumerate:
            pos_layout = self._get_column_view(value='pos', text_size=text_size, weight=weight, text_bold=text_bold)
            fields_layout.append(pos_layout)

        # Вставляем изображение после колонки 'pos' и перед остальными колонками
        if not is_header:
            img = '@img'
        else:
            img = None
        img_layout = self._get_image_column_view(value=img, width=16, height=12, weight=1)
        fields_layout.append(img_layout)

        fields_layout.append(
            widgets.LinearLayout(
                *[self._get_column_view(value=field, text_size=text_size, weight=weight, text_bold=text_bold) for field in self.fields],
                width='match_parent',
                orientation='horizontal',
                weight=7
            )
        )

        return fields_layout

    def _get_image_column_view(self, value, width, height, weight):
        return widgets.LinearLayout(
            widgets.Picture(
                Value=value,
                width=width,
                height=height,
                weight=weight
            ),
            width='match_parent',
            height='match_parent',
            weight=1,
            StrokeWidth=1,
        )

    def _get_column_view(self, value, text_size=20, weight=1, text_bold=False):
        return widgets.LinearLayout(
            widgets.TextView(
                Value=f'@{value}',
                gravity_horizontal='center',
                TextSize=text_size,
                width='match_parent',
                TextBold=text_bold
            ),
            width='match_parent',
            height='match_parent',
            weight=weight,
            StrokeWidth=1,
        )

# ^^^^^^^^^^^^^^^^^^^^^ SelectItemScreen ^^^^^^^^^^^^^^^^^^^^^^^^^^^^



# ==================== Settings =============================

class SettingsScreen(Screen):
    screen_name = 'Настройки и обмен'
    process_name = 'Параметры'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.db_service = db_services.DocService()

    def on_start(self):
        settings_keys = [
            'use_mark',
            'allow_fact_input',
            'add_if_not_in_plan',
            'path',
            'allow_overscan',
            'offline_mode'
        ]

        put_data = {key: self.rs_settings.get(key) for key in settings_keys}
        put_data['ip_adr'] = self._get_ip_address()

        self.hash_map.put_data(put_data)

    def on_input(self):
        self._update_rs_settings()

        listeners = {
            'btn_http_settings': lambda: self._show_screen('Настройки http соединения'),
            'btn_size': lambda: self._show_screen('Настройки Шрифтов'),
            'btn_sound_settings': lambda: self._show_screen('Настройка звука'),
            'btn_documents_settings': lambda: self._show_screen('Настройки документов'),
            'btn_ocr_recognition_settings': lambda: self.hash_map.switch_process_screen('OcrTextRecognition'),
            'btn_print_settings': lambda: self.hash_map.switch_process_screen('Print'),
            'btn_test_barcode': lambda: self._show_screen('Тест сканера'),
            'btn_err_log': lambda: self._show_screen('Ошибки'),
            'btn_upload_docs': self._upload_docs,
            'btn_timer': self._load_docs,
            'ON_BACK_PRESSED': lambda: self.hash_map.put('FinishProcess', ''),
        }
        if self.listener in listeners:
            listeners[self.listener]()

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _upload_docs(self):
        if self._check_http_settings():
            timer = Timer(self.hash_map)
            timer.upload_data()
        else:
            self.toast('Не заданы настройки соединения')

    def _load_docs(self):
        if self._check_http_settings():
            timer = Timer(self.hash_map)
            timer.timer_on_start()
        else:
            self.toast('Не заданы настройки соединения')

    def _update_rs_settings(self) -> None:
        use_mark = self.hash_map.get('use_mark') or 'false'
        path = self.hash_map.get('path') or '//storage/emulated/0/Android/data/ru.travelfood.simple_ui/'
        allow_fact_input = self.hash_map.get_bool('allow_fact_input') or False
        offline_mode = self.hash_map.get_bool('offline_mode') or False

        self.rs_settings.put('use_mark', use_mark, True)
        self.rs_settings.put('path', path, True)
        self.rs_settings.put('allow_fact_input', allow_fact_input, True)
        self.rs_settings.put('offline_mode', offline_mode, True)

    def _show_screen(self, screen_name) -> None:
        self.hash_map.show_screen(screen_name)

    def _get_http_settings(self) -> dict:
        http_settings = {
            'url': self.rs_settings.get("URL"),
            'user': self.rs_settings.get('USER'),
            'pass': self.rs_settings.get('PASS'),
            'device_model': self.hash_map['DEVICE_MODEL'],
            'android_id': self.hash_map['ANDROID_ID'],
            'user_name': self.rs_settings.get('user_name')}
        return http_settings

    @staticmethod
    def _get_ip_address() -> str:
        res = get_ip_address()
        if res:
            return res
        else:
            return 'нет сети'

    def _check_http_settings(self) -> bool:
        http = self._get_http_settings()
        return all([http.get('url'), http.get('user'), http.get('pass')])


class FontSizeSettingsScreen(Screen):
    screen_name = 'Настройки Шрифтов'
    process_name = 'Параметры'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)

    def on_start(self):
        put_data = {}
        fields_data = {
            'TitleTextSize': 'Размер заголовка',
            'CardTitleTextSize': 'Размер заголовка карточки',
            "CardDateTextSize": 'Данные карточки',
            'CardTextSize': 'Размер текста элементов',
            'GoodsCardTitleTextSize': 'Заголовок товара',
            'goodsTextSize': 'Товар',
            'SeriesPropertiesTextSize': 'Серии свойства',
            'DocTypeCardTextSize': 'Тип документа',
            'titleDocTypeCardTextSize': 'Название документа в карточке'
        }

        for field, hint in fields_data.items():
            put_data[field] = widgets.ModernField(
                hint=hint,
                default_text=self.rs_settings.get(field) or ''
            ).to_json()

        self.hash_map.put_data(put_data)

    def on_input(self):
        if self.listener == 'btn_on_save':
            save_data = {
                'TitleTextSize': self.hash_map['TitleTextSize'],
                'CardTitleTextSize': self.hash_map['CardTitleTextSize'],
                'CardTextSize': self.hash_map['CardTextSize'],
                'CardDateTextSize': self.hash_map['CardDateTextSize'],
                'GoodsCardTitleTextSize': self.hash_map['GoodsCardTitleTextSize'],
                'goodsTextSize': self.hash_map['goodsTextSize'],
                'SeriesPropertiesTextSize': self.hash_map['SeriesPropertiesTextSize'],
                'DocTypeCardTextSize': self.hash_map['DocTypeCardTextSize'],
                'titleDocTypeCardTextSize': self.hash_map['titleDocTypeCardTextSize'],
            }

            for k, v in save_data.items():
                self.rs_settings.put(k, v, True)

            self.hash_map.show_screen('Настройки и обмен')

        elif self.listener == 'btn_on_cancel' or self.listener == 'ON_BACK_PRESSED':
            self.hash_map.put('BackScreen', '')

        self.hash_map['noRefresh'] = ''

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass


class BarcodeTestScreen(Screen):
    screen_name = 'Тест сканера'
    process_name = 'Параметры'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.scanner_list = self._get_scanner_list()

    def on_start(self):
        hardware_scanner = self.rs_settings.get('hardware_scanner') or 'не выбран'
        self._prepare_screen_load_settings(hardware_scanner)
        self._switch_scanner_settings_visibility()
        self._switch_scanner_edit_view(hardware_scanner)

    def on_input(self):
        listeners = {
            'barcode': self._barcode_scanned,
            'ON_BACK_PRESSED': self._back_screen,
            'BACK_BUTTON': self._back_screen,
            'device_value': self._fill_scan_settings,
            'use_hardware_scanner': self._switch_scanner_settings_visibility,
            'btn_save_handmade_settings': self.save_scan_settings
        }
        if self.listener in listeners:
            listeners[self.listener]()

    def _back_screen(self):
        self.hash_map.put('BackScreen', '')

    def _get_scanner_list(self) -> dict:
        return {'не выбран': {'IntentScanner': 'false', 'IntentScannerMessage': "", 'IntentScannerVariable': "",
                                  'IntentScannerLength': ""},
                    'Ручной ввод': {'IntentScanner': 'false', 'IntentScannerMessage': "", 'IntentScannerVariable': "",
                                    'IntentScannerLength': ""},
                    'Urovo': {'IntentScanner': 'true', 'IntentScannerMessage': "android.intent.ACTION_DECODE_DATA",
                              'IntentScannerVariable': "barcode_string", 'IntentScannerLength': "barcode"},
                    'Atol': {'IntentScanner': 'true',
                             'IntentScannerMessage': "com.xcheng.scanner.action.BARCODE_DECODING_BROADCAST",
                             'IntentScannerVariable': "EXTRA_BARCODE_DECODING_DATA", 'IntentScannerLength': "EXTRA_BARCODE_DECODING_SYMBOLE"},
                    'iData': {'IntentScanner': 'true',
                             'IntentScannerMessage': "android.intent.action.SCANRESULT",
                             'IntentScannerVariable': "value", 'IntentScannerLength': "length"},
                    'Mindeo': {'IntentScanner': 'true',
                             'IntentScannerMessage': "com.android.scanner.broadcast",
                             'IntentScannerVariable': "scandata", 'IntentScannerLength': "scandata_array"},
                    'POS': {'IntentScanner': 'true',
                             'IntentScannerMessage': "com.xcheng.scanner.action.BARCODE_DECIDING_BROADCAST",
                             'IntentScannerVariable': "EXTRA_BARCODE_DECODING_DATA", 'IntentScannerLength': "EXTRA_BARCODE_DECODING_SYMBOLE"},
                    'Meferi': {'IntentScanner': 'true',
                             'IntentScannerMessage': "android.intent.action.MEF_ACTION",
                             'IntentScannerVariable': "android.intent.extra.MEF_DATA1", 'IntentScannerLength': "android.intent.extra.MEF_DATA2"}
                             }

    def _prepare_screen_load_settings(self, hardware_scanner):
        keys = list(self.scanner_list.keys())
        self.hash_map['device_list'] = ';'.join(keys)
        use_hardware_scanner = self.rs_settings.get('use_hardware_scanner') or False
        self.hash_map['use_hardware_scanner'] = str(use_hardware_scanner).lower()
        self.hash_map['device_value'] = hardware_scanner
        if hardware_scanner == 'Ручной ввод':
            handmade_settings = self.rs_settings.get('handmade_hardware_scanner_options')
            if handmade_settings:
                self.scanner_list['Ручной ввод'] = json.loads(handmade_settings)

    def _barcode_scanned(self):
        barcode = self.hash_map.get('barcode_camera')
        if not barcode:
            return
        barcode_parser = BarcodeWorker(id_doc='')
        result = barcode_parser.parse(barcode)
        fields_count = 7
        keys_list = ['ERROR', 'GTIN', 'SERIAL', 'FullCode', 'BARCODE', 'SCHEME', 'EXPIRY', 'BATCH', 'NHRN', 'CHECK',
                     'WEIGHT', 'PPN']
        values = [f'{key}: {result[key]}' for key in keys_list if result.get(key) is not None]
        put_data = {
            f'fld_{i + 1}': values[i] if len(values) > i else ''
            for i in range(0, fields_count)
        }
        self.hash_map.put_data(put_data)

    def _fill_scan_settings(self, use_hardware_scan: bool = True):
        if use_hardware_scan:
            current_model = self.scanner_list.get(self.hash_map['device_value'])
        else:
            current_model = self.scanner_list.get('не выбран')
        # Закидываем в настройки
        self.hash_map.put('SetSettingsJSON', current_model, to_json=True)
        self.rs_settings.put('hardware_scanner', self.hash_map['device_value'], True)
        self.rs_settings.put('use_hardware_scanner', str(use_hardware_scan).lower(), True)
        # Записываем значения в переменные экрана
        for i in current_model.keys():
            self.hash_map[i] = current_model[i]

    def _switch_scanner_settings_visibility(self):
        if self.hash_map.get_bool('use_hardware_scanner'):
            self.hash_map['Show_scan_layout'] = '1'
            self._fill_scan_settings(True)
        else:
            self.hash_map['Show_scan_layout'] = '-1'
            self._fill_scan_settings(False)

    def _switch_scanner_edit_view(self, model):
        switcher = -1 if model == 'Ручной ввод' else 1
        self.hash_map['Show_scan_layout_view'] = str(switcher)
        self.hash_map['Show_scan_layout_edit'] = str(switcher * -1)

    def _form_scan_parameters(self):
        if self.hash_map['device_value'] == 'Ручной ввод':
            params = {'IntentScanner': 'true',
                      'IntentScannerMessage': self.hash_map['IntentScannerMessage'],
                      'IntentScannerVariable': self.hash_map['IntentScannerVariable'],
                      'IntentScannerLength': self.hash_map['IntentScannerLength']
                      }
        else:
            params = self.scanner_list.get(self.hash_map['device_value'])
        return params

    def save_scan_settings(self):
        self.rs_settings.put('handmade_hardware_scanner_options', json.dumps(self._form_scan_parameters()), True)


class HttpSettingsScreen(Screen):
    screen_name = 'Настройки http соединения'
    process_name = 'Параметры'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.hs_service = None
        self.input_cache = {}

    def on_start(self) -> None:
        self.hash_map['btn_test_connection'] = 'Тест соединения'
        http_settings = self._get_http_settings()

        put_data = {
            'url': self._get_modern_field(hint='Адрес сервера', default_text=http_settings['url'] or ''),
            'user': self._get_modern_field(hint='Пользователь', default_text=http_settings['user'] or ''),
            'pass': self._get_modern_field(hint='Пароль', default_text=http_settings['pass'] or '', password=True),
            'user_name': self._get_modern_field(hint='Ваше имя для идентификации в 1С',
                                                default_text=http_settings['user_name'] or ''),
        }
        self.hash_map.put_data(put_data)

    def on_input(self) -> None:
        self.input_cache['url'] = self.hash_map.get('url', '')
        self.input_cache['user'] = self.hash_map.get('user', '')
        self.input_cache['pass'] = self.hash_map.get('pass', '')
        self.input_cache['user_name'] = self.hash_map.get('user_name', '')

        listeners = {
            'btn_test_connection': self._test_connection,
            'btn_save': self._save_settings,
            'barcode': self._barcode_scanned,
            'btn_cancel': self._back_screen,
            'ON_BACK_PRESSED': self._back_screen,
        }
        if self.listener in listeners:
            listeners[self.listener]()

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _test_connection(self):
        self.hs_service = hs_services.HsService(self._get_http_settings())

        if self._check_http_settings():
            self.hs_service.communication_test(timeout=3)
            result = self.hs_service.http_answer

            if result.unauthorized:
                self.hash_map.toast('Ошибка авторизации сервера 1С')
            elif result.forbidden:
                self.toast('Запрос на авторизацию принят')
            elif result.error:
                self.toast('Ошибка соединения. Подробнее в логе ошибок')
                self.hash_map.playsound('error')
            else:
                self.toast('Соединение установлено')
                self.hash_map.playsound('success')

        else:
            self.toast("Не указаны настройки HTTP подключения к серверу")
            self.hash_map.playsound('error')

    def _save_settings(self):
        self.rs_settings.put('URL', self.hash_map['url'], True)
        self.rs_settings.put('USER', self.hash_map['user'], True)
        self.rs_settings.put('PASS', self.hash_map['pass'], True)
        self.rs_settings.put('user_name', self.hash_map['user_name'], True)

        self._back_screen()

    def _barcode_scanned(self):
        barcode = self.hash_map.get('barcode_camera2')
        try:
            barc_struct = json.loads(barcode)

            self.rs_settings.put('URL', barc_struct.get('url'), True)
            self.rs_settings.put('USER', barc_struct.get('user'), True)
            self.rs_settings.put('PASS', barc_struct.get('pass'), True)
            self.rs_settings.put('user_name', barc_struct.get('user_name'), True)

            self.hash_map.put('url', self._get_modern_field(hint='url', default_text=barc_struct.get('url')))
            self.hash_map.put('user', self._get_modern_field(hint='user', default_text=barc_struct.get('user')))
            self.hash_map.put('pass', self._get_modern_field(hint='pass', default_text=barc_struct.get('pass')))
            self.hash_map.put('user_name',
                              self._get_modern_field(hint='user_name', default_text=barc_struct.get('user_name')))

            # Явно обновить input_cache новыми значениями
            self.input_cache['url'] = barc_struct.get('url', '')
            self.input_cache['user'] = barc_struct.get('user', '')
            self.input_cache['pass'] = barc_struct.get('pass', '')
            self.input_cache['user_name'] = barc_struct.get('user_name', '')

        except (JSONDecodeError, AttributeError) as e:
            self.toast('Неверный формат QR-кода')

    def _back_screen(self):
        self.hash_map.put('BackScreen', '')

    def _get_modern_field(self, **data):
        return widgets.ModernField(**data).to_json()

    def _check_http_settings(self) -> bool:
        http = self._get_http_settings()
        return all([http.get('url'), http.get('user'), http.get('pass')])

    def _get_http_settings(self):
        return {
            'url': self.input_cache.get('url', self.rs_settings.get("URL")),
            'user': self.input_cache.get('user', self.rs_settings.get('USER')),
            'pass': self.input_cache.get('pass', self.rs_settings.get('PASS')),
            'device_model': self.hash_map['DEVICE_MODEL'],
            'android_id': self.hash_map['ANDROID_ID'],
            'user_name': self.input_cache.get('user_name', self.rs_settings.get('user_name'))
    }


class SoundSettings(Screen):
    screen_name = 'Настройка звука'
    process_name = 'Параметры'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.events = {'success': 'Сигнал удачного события', 'warning': 'Сигнал предупреждения',
                       'error': 'Сигнал ошибки'}

    def on_start(self):
        self._init_sounds()
        events_data = self._get_events_data()
        events_cards = self._get_event_cards_view(events_data, popup_menu_data='1;2;3;4;5;6;7;8;9;10;11;12;13;14;15')
        self.hash_map.put('event_cards', events_cards.to_json())

    def on_input(self):
        if self.listener == 'save_btn':
            self.rs_settings.put('success_signal', self.hash_map.get("current_success_signal"), True)
            self.rs_settings.put('warning_signal', self.hash_map.get("current_warning_signal"), True)
            self.rs_settings.put('error_signal', self.hash_map.get("current_error_signal"), True)
            self.hash_map.show_screen('Настройки и обмен')
            # self.hash_map.finish_process()

        elif self.listener == 'btn_on_cancel' or self.listener == 'ON_BACK_PRESSED':
            self.hash_map.put('current_success_signal', '')
            self.hash_map.put('current_warning_signal', '')
            self.hash_map.put('current_error_signal', '')
            self.hash_map.show_screen('Настройки и обмен')

        elif self.listener == 'CardsClick':
            selected_event = self.hash_map.get('selected_card_key')
            self.hash_map.playsound(event=selected_event,
                                    sound_val=self.hash_map.get(f'current_{selected_event}_signal'))

        elif self.listener == 'LayoutAction':
            self._layout_action()

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _init_sounds(self):
        # for key, val in self.events.items():
        #     if not self.hash_map.get(f'current_{key}_signal'):
        #         self.hash_map.put(f'current_{key}_signal', self.rs_settings.get(f'{event}_signal' or "6"))

        if not self.hash_map.get('current_success_signal'):
            self.hash_map.put('current_success_signal', self.rs_settings.get('success_signal'))
        if not self.hash_map.get('current_warning_signal'):
            self.hash_map.put('current_warning_signal', self.rs_settings.get('warning_signal'))
        if not self.hash_map.get('current_error_signal'):
            self.hash_map.put('current_error_signal', self.rs_settings.get('error_signal'))

    def _get_events_data(self):
        data = []
        for key, val in self.events.items():
            event = {
                'key': key,
                'event_name': val,
                'selected_value': self.hash_map.get(f'current_{key}_signal')
            }
            data.append(event)
        return data

    def _get_event_cards_view(self, events_data, popup_menu_data):
        title_text_size = self.rs_settings.get("TitleTextSize")
        card_title_text_size = self.rs_settings.get("CardTitleTextSize")
        doc_cards = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@event_name',
                        TextBold=True,
                        TextSize=title_text_size,
                        gravity_horizontal='center',
                        width='match_parent',
                    ),
                    orientation='horizontal',
                    width='match_parent',
                    gravity_horizontal='center',
                    weight=0
                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@selected_value',
                        TextSize=28,
                        gravity_horizontal='center',
                        weight=1,
                    ),
                    widgets.PopupMenuButton(
                        Value=popup_menu_data,
                        Variable="menu_select_sound",
                        gravity_horizontal='center',
                        weight=1
                    ),
                    widgets.TextView(
                        Value="Прослушать",
                        gravity_horizontal='center',
                        TextSize=card_title_text_size,
                        weight=1
                    ),

                    orientation='horizontal',
                    width='match_parent',

                ),

                width="match_parent",
                orientation='vertical',
                gravity_horizontal='center',
                gravity_vertical="center",
            ),
            options=widgets.Options().options,
            cardsdata=events_data
        )

        return doc_cards

    def _layout_action(self):
        layout_listener = self.hash_map.get('layout_listener')
        current_key = self.hash_map.get_json("card_data")['key']
        self.hash_map.put(f'current_{current_key}_signal', layout_listener)


class DocumentsSettings(Screen):
    screen_name = 'Настройки документов'
    process_name = 'Параметры'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)

    def on_start(self):
        if not self.hash_map.containsKey('doc_settings_on_start'):
            self.hash_map.put('doc_settings_on_start', 'true')
            self._init_old_doc_delete_settings()

    def on_input(self):
        if self.listener == 'save_btn':
            del_docs_flag = self.hash_map.get('doc_settings_confirm_delete_old_docs')
            del_docs_flag = True if del_docs_flag == 'true' else False
            if not del_docs_flag:
                self.rs_settings.put('delete_old_docs', False, True)
                self.rs_settings.delete('doc_delete_settings_days')
            else:
                days = self.hash_map.get('doc_delete_settings_days')
                if not days or days == '0' or not days.isdigit():
                    self.hash_map.playsound('error')
                    self.hash_map.toast('Укажите корректное количество дней'
                                        ' для настройки удаления старых документов')
                    return
                if days >= '9999':
                    self.hash_map.playsound('error')
                    self.hash_map.toast('Количество дней превышает 9999')
                    return
                self.rs_settings.put('delete_old_docs', True, True)
                self.rs_settings.put('doc_delete_settings_days', days, True)

            self.hash_map.toast('Настройки сохранены')
            self.hash_map.delete('doc_settings_on_start')
            self.hash_map.show_screen('Настройки и обмен')

        elif self.listener == 'ON_BACK_PRESSED':
            self.hash_map.delete('doc_settings_on_start')
            self.hash_map.show_screen('Настройки и обмен')

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _init_old_doc_delete_settings(self):
        current_days_value = self.rs_settings.get('doc_delete_settings_days')
        init_days = str(current_days_value) if current_days_value is not None else '1'
        self.hash_map.put('doc_delete_settings_days', init_days)

        flag = self.rs_settings.get('delete_old_docs')
        init_flag = str(flag).lower() if flag is not None else 'false'
        self.hash_map.put('doc_settings_confirm_delete_old_docs', init_flag)


class ErrorLogScreen(Screen):
    screen_name = 'Ошибки'
    process_name = 'Параметры'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = LoggerService()
        self.screen_values = {}
        self.desc_sort = True

    def on_start(self) -> None:
        errors_table_data = self.service.get_all_errors(self.desc_sort)
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
            self.desc_sort = not self.desc_sort

    def on_post_start(self):
        pass

    def show(self, args=None):
        self._validate_screen_values()
        self.hash_map.show_screen(self.screen_name, args)

    def _get_errors_table_rows(self, errors_table_data):
        table_data = [{}]
        i = 1
        for record in errors_table_data:
            error_row = {"key": i, "message": record['error_text'],
                         "time": DateFormat().get_table_view_format(record['timestamp']),
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
                StrokeWidth=1
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
            'btn_fill_ratio': self._fill_ratio,
            'btn_copy_base': self._copy_base,
            'btn_unload_log': self._unload_log,
            'btn_templates': self.open_templates_screen,
            'ON_BACK_PRESSED': self._on_back_pressed
        }
        if self.listener in listeners:
            listeners[self.listener]()

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _fill_ratio(self):
        qtext = '''
        UPDATE RS_barcodes
        SET ratio = COALESCE((
            SELECT RS_units.nominator / RS_units.denominator
            FROM RS_units
            WHERE RS_units.id = RS_barcodes.id_unit
        ), 1)'''

        res = ui_global.get_query_result(qtext)
        self.hash_map.toast('Таблица баркодов заполнена значениями из единиц измерения')

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
    def _on_back_pressed(self):
        ip_host = self.hash_map['ip_host']
        self.rs_settings.put('debug_host_ip', ip_host, True)
        self.hash_map.put('FinishProcess', '')

    def open_templates_screen(self):
        self.hash_map.show_process_result('Print', 'TemplatesList')


# ^^^^^^^^^^^^^^^^^^^^^ Debug settings ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== Services =============================


class Timer:
    def __init__(self, hash_map: HashMap):
        self.hash_map = hash_map
        self.rs_settings = _rs_settings
        self.http_settings = self._get_http_settings()
        self.db_service = DocService()
        self.http_service = HsService(self.http_settings)

    def timer_on_start(self):
        if not self._check_connection():
            return

        self._load_docs()
        self.upload_data()
        self._upload_buffer_data()

    def _put_notification(self, text, title=None):
        self.hash_map.notification(text, title)

    def _get_http_settings(self):
        http_settings = {
            'url': self.rs_settings.get("URL"),
            'user': self.rs_settings.get('USER'),
            'pass': self.rs_settings.get('PASS'),
            'device_model': self.rs_settings.get('device_model'),
            'android_id': self.rs_settings.get('android_id'),
            'user_name': self.rs_settings.get('user_name')}
        return http_settings

    def _load_docs(self):
        if not self._check_http_settings():
            return

        try:
            docs_data = self.http_service.get_data()
            data = docs_data.get('data')
            if not data:
                return

            service = db_services.TimerService()
            new_documents = service.get_new_load_docs(data)
            service.save_load_data(data)
            # self.db_service.update_data_from_json(docs_data['data']) Старый вариант обмена.

            if new_documents:
                notify_text = self._get_notify_text(new_documents)
                self._put_notification(text=notify_text, title="Загружены документы:")

        except Exception as e:
            self.http_service.write_error_to_log(error_text=e.args[0],
                                               error_info='Ошибка загрузки документов')

    def upload_data(self):
        if not self._check_http_settings():
            return

        service = TimerService()
        data = service.get_data_to_send()

        if not data:
            return

        try:
            answer = self.http_service.send_data(data)
        except Exception as e:
            self.http_service.write_error_to_log(
                error_text=e,
                error_info='Ошибка выгрузки документов'
            )
            return

        if answer.error:
            self.http_service.write_error_to_log(error_text=answer.error_text,
                                               error_info='Ошибка выгрузки документов')
        else:
            docs_list_string = ', '.join([f"'{d['id_doc']}'" for d in data])
            self.db_service.update_uploaded_docs_status(docs_list_string)

    def _upload_buffer_data(self):
        # Имя таблицы очереди (имя метода в url http-сервиса)
        buffer_tables = [
            'barcodes',
            'documents'
        ]

        for buffer_table in buffer_tables:
            buffer_service = ExchangeQueueBuffer(buffer_table)
            data_to_send = buffer_service.get_data_to_send()

            method = self.http_service.get_method_by_path(buffer_table)
            if data_to_send and method:
                res = method(data_to_send)

                if not res.error:
                    buffer_service.remove_sent_data(data_to_send)

    def _check_http_settings(self) -> bool:
        http = self._get_http_settings()
        return all([http.get('url'), http.get('user'), http.get('pass')])

    @staticmethod
    def _get_notify_text(new_documents):
        doc_titles = [
            '{} № {} от {}'.format(item['doc_type'], item['doc_n'], item['doc_date'])
            for item in new_documents.values()]
        return ", ".join(doc_titles)

    def _check_connection(self):
        hs_service = hs_services.HsService(self._get_http_settings())
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

class WebServiceSyncCommand:
    def __init__(self, hash_map: HashMap):
        self.hash_map = hash_map
        self.listener = self.hash_map.listener

    def on_service_request(self):
        listeners = {
            'barcodes': self._get_barcodes_data,
            'hash_map': self._get_hash_map,
            'hash_map_size': self._get_hash_map_size,
            'rs_settings': self._get_rs_settings,
            'scanning_queue': self._get_scanning_queue
        }
        if self.listener in listeners:
            listeners[self.listener]()

    def _get_barcodes_data(self):
        buffer_service = ExchangeQueueBuffer('barcodes')
        data_to_send = buffer_service.get_data_to_send()
        headers = [{'key': 'Content-Type', 'value': 'application/json'}]
        self.hash_map.put('WSResponseHeaders', headers, to_json=True)
        self.hash_map.put('WSResponse', data_to_send, to_json=True)

    def _get_hash_map(self):
        process_map = self.hash_map.get_json('process_map')

        body = self.hash_map.get_json('ws_body')
        if body:
            response = process_map.get(body['item'])

            headers = [{'key': 'Content-Type', 'value': 'application/json'}]
            self.hash_map.put('WSResponseHeaders', headers, to_json=True)
            self.hash_map.put('WSResponse', response)

    def _get_hash_map_size(self):
        import sys
        process_map = self.hash_map.get_json('process_map') or {}

        headers = [{'key': 'Content-Type', 'value': 'application/json'}]
        self.hash_map.put('WSResponseHeaders', headers, to_json=True)

        resp = {key: round(sys.getsizeof(v) / 1024, 3) for key, v  in process_map.items()}
        resp['total'] = round(sum(resp.values()), 3)

        resp_sorted = {k: v for k, v in sorted(resp.items(), key=lambda item: item[1], reverse=True)}

        self.hash_map.put('WSResponse', resp_sorted, to_json=True)

    def _get_rs_settings(self):

        provider = NoSQLProvider('rs_settings')

        response = json.dumps({item[0]: item[1] for item in provider.items()})

        headers = [{'key': 'Content-Type', 'value': 'application/json'}]
        self.hash_map.put('WSResponseHeaders', headers, to_json=True)
        self.hash_map.put('WSResponse', response)

    def _get_scanning_queue(self):
        service = ScanningQueueService()
        queue = service.provider.get_all()

        response = json.dumps(queue)

        headers = [{'key': 'Content-Type', 'value': 'application/json'}]
        self.hash_map.put('WSResponseHeaders', headers, to_json=True)
        self.hash_map.put('WSResponse', response)

# ^^^^^^^^^^^^^^^^^^^^^ Services ^^^^^^^^^^^^^^^^^^^^^^^^^^^^


# ==================== Main events =============================


class MainEvents:
    def __init__(self, hash_map: HashMap):
        self.hash_map = hash_map
        self.rs_settings = _rs_settings

    def app_on_start(self):
        MainEvents.start_timer(self.hash_map)

        # TODO Обработчики обновления!
        release = self.rs_settings.get('Release') or ''
        toast = 'Готов к работе'

        current_release = self.hash_map['_configurationVersion']



        if current_release is None:
            toast = 'Не удалось определить версию конфигурации'

        if current_release and release != current_release:
            # import version_control
            # result_list = version_control.run_releases(release, current_release)
            # for elem in result_list:
            #     if not elem['result']:
            #         pass
            self.hash_map.put('InstallConfiguration', '')
            self.rs_settings.put('Release', current_release, True)
            toast = f'Выполнено обновление на версию {current_release}'

        if self.rs_settings.get('delete_old_docs') is True:
            deleted_docs = self._delete_old_docs()
            if deleted_docs:
                self.hash_map.notification(
                    text=f'Удалены документы: ({len(deleted_docs)})',
                    title='Очистка неактуальных данных')

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
            'signal_num': 5,
            'use_mark': 'false',
            'add_if_not_in_plan': 'false',
            'path': '',
            'success_signal': 7,
            'warning_signal': 8,
            'error_signal': 5,
            'allow_overscan': 'false',
            "path_to_databases": "./",
            'sqlite_name': 'SimpleKeep',
            'log_name': 'log.json',
            'allow_fact_input': False,
            'offline_mode': False,
            'delete_old_docs': False,
            'user_tmz_offset': self.hash_map.get("TMZ")
        }

        if os.path.exists('//data/data/ru.travelfood.simple_ui/databases/'):
            rs_default_settings['path_to_databases'] = '//data/data/ru.travelfood.simple_ui/databases'
        else:
            rs_default_settings['path_to_databases'] = "./"

        for k, v in rs_default_settings.items():
            if self.rs_settings.get(k) is None:
                self.rs_settings.put(k, v, True)

        self.rs_settings.put('device_model', self.hash_map['DEVICE_MODEL'], True)
        self.rs_settings.put('android_id', self.hash_map['ANDROID_ID'], True)

        self._create_tables()

        self.hash_map["SQLConnectDatabase"] = "SimpleKeep"
        self.hash_map.toast(toast)

    def on_sql_error(self):
        sql_error = self.hash_map['SQLError']
        if sql_error:
            service = db_services.DocService()
            service.write_error_on_log(
                error_type="SQL_Error",
                error_text=sql_error,
                error_info=''
                )

    def _create_tables(self):
        service = db_services.DbCreator()
        service.create_tables()

    def _delete_old_docs(self) -> list:
        days = int(self.rs_settings.get('doc_delete_settings_days'))
        service = db_services.DocService()
        return service.delete_old_docs(days)

    @staticmethod
    def start_timer(hash_map: HashMap):
        hash_map.start_timers('timer_update', period=15000, bs_hash_map=True)


# ^^^^^^^^^^^^^^^^^^^^^ Main events ^^^^^^^^^^^^^^^^^^^^^^^^^^^^


class ScreensFactory:
    screens = [GoodsSelectScreen,
               GroupScanTiles,
               DocumentsTiles,
               GroupScanDocsListScreen,
               DocumentsDocsListScreen,
               GroupScanDocDetailsScreen,
               DocumentsDocDetailScreen,
               ErrorLogScreen,
               DebugSettingsScreen,
               HttpSettingsScreen,
               SettingsScreen,
               GoodsListScreen,
               SelectGoodsType,
               ItemCard,
               FontSizeSettingsScreen,
               BarcodeTestScreen,
               SoundSettings,
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
    screen_name = 'Mock'
    process_name = 'Mock'

    def on_start(self):
        pass

    def on_input(self):
        pass

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass


def set_current_screen(screen):
    global current_screen
    current_screen = screen
    return current_screen

def set_next_screen(screen):
    global next_screen
    next_screen = screen
    return next_screen

def create_screen(hash_map: HashMap, screen_class=None, screen_values=None):
    """
    Метод для получения модели соответствующей текущему процессу и экрану.
    Если модель не реализована возвращает заглушку
    Реализован синглтон через глобальную переменную current_screen, для сохренения состояния текущего экрана
    """
    global current_screen, next_screen

    screen_params = {
        'hash_map': hash_map,
        'rs_settings': _rs_settings
    }
    if screen_class is None:
        screen_class = ScreensFactory.get_screen_class(**screen_params)

    if not screen_class:
        current_screen = MockScreen(**screen_params)
    elif type(current_screen) is not screen_class:
        if type(next_screen) is screen_class:
            current_screen = next_screen
            next_screen = None
            current_screen.hash_map = hash_map
        else:
            if screen_values:
                hash_map.put_data(screen_values)
            current_screen = screen_class(**screen_params)
    else:
        current_screen.hash_map = hash_map
        current_screen.listener = hash_map['listener']
        current_screen.event = hash_map['event']

    if current_screen.is_finish_process:
        finish_screen = current_screen
        current_screen = None
        return finish_screen

    return current_screen

