import json

import db_services
import ui_global
import widgets
from db_services import DocService
from printing_factory import PrintService
from ui_models import Tiles, DocsListScreen, DocDetailsScreen, SerialNumberOCRSettings
from ui_utils import HashMap


class FlowTilesScreen(Tiles):
    screen_name = 'Плитки'
    process_name = 'Сбор ШК'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.db_service = DocService(is_barc_flow=True)

    def on_start(self) -> None:

        data = self.db_service.get_doc_flow_stat()
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
                self.TextView('@barc_count', self.rs_settings),
                orientation='horizontal',
                width="match_parent",
                weight=1
            ),

            width='match_parent',
            autoSizeTextType='uniform',
            weight=0
        )

        return tiles_view

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
        count_verified = tile_element['verified'] or 0
        barc_count = tile_element['barc_count'] or 0

        return {
            "docName": tile_element['docType'],
            'QttyOfDocs': '{}/{}'.format(tile_element['count'], tile_element['verified']),
            'count_verified': str(count_verified),
            'barc_count': str(barc_count)
        }


class FlowDocScreen(DocsListScreen):
    screen_name = 'Документы'
    process_name = 'Сбор ШК'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = db_services.FlowDocService()
        self.service.docs_table_name = 'RS_docs'
        self.popup_menu_data = 'Удалить;Очистить данные пересчета'

    def on_start(self):
        super().on_start()

    def on_input(self) -> None:
        listeners = {
            'CardsClick': lambda: FlowDocDetailsScreen(self.hash_map).show(self._get_selected_card_put_data()),
            'ON_BACK_PRESSED': lambda: self.hash_map.show_screen('Плитки'),
            'doc_type_click': lambda: self.hash_map.refresh_screen(),
            'confirm_clear_barcode_data': self._handle_clear_barcode_data
        }

        listener_func = listeners.get(self.listener)
        if listener_func:
            listener_func()

        super().on_input()

    def _handle_clear_barcode_data(self):
        id_doc = self.get_id_doc()
        res = self._clear_barcode_data(id_doc)
        self.service.set_doc_status_to_upload(id_doc)
        if res.get('result'):
            self.toast('Все штрихкоды удалены из документа')
        else:
            self.toast('При очистке данных возникла ошибка.')
            self.hash_map.error_log(res.get('error'))


class FlowDocDetailsScreen(DocDetailsScreen):
    screen_name = 'ПотокШтрихкодовДокумента'
    process_name = 'Сбор ШК'

    def __init__(self, hash_map: HashMap, rs_settings=None):
        super().__init__(hash_map, rs_settings)
        self.service = db_services.FlowDocService(self.id_doc)

    def show(self, args=None):
        self.hash_map.show_screen(self.screen_name, args)

    def on_start(self):
        self._barcode_flow_on_start()
        self._set_vision_settings()

    def on_input(self) -> None:
        listeners = {
            'CardsClick': self._handle_cards_click,
            'BACK_BUTTON': self._handle_back_button,
            'btn_barcodes': self._show_dialog_input_barcode,
            'barcode': self._handle_barcode_camera,
            'modal_dialog_input_barcode': self._handle_dialog_input_barcode,
            'confirm_verified': self._handle_confirm_verified,
            'btn_doc_mark_verified': lambda: self.hash_map.show_dialog('confirm_verified', 'Завершить документ?', ['Да', 'Нет']),
            'ON_BACK_PRESSED': lambda: self.hash_map.show_screen("Документы"),
            'vision_cancel':  lambda: SerialNumberOCRSettings.ocr_nosql_counter.destroy(),
            'vision': lambda: SerialNumberOCRSettings.ocr_nosql_counter.destroy(),
            'ПечатьПревью': lambda: self.hash_map.put('RefreshScreen', ''),
            'btn_ocr_serial_template_settings': self._handle_ocr_serial_template_settings
        }

        listener_func = listeners.get(self.hash_map.get('listener'))
        if listener_func:
            listener_func()

    def _handle_cards_click(self):
        current_elem = self._get_selected_card_data() 
        data = {
            'barcode': current_elem['barcode'],
            'Номенклатура': current_elem['name'],
            'qtty': current_elem['qtty'], 
            'Характеристика': ''
        }
        PrintService.print(self.hash_map, data)

    def _handle_back_button(self):
        self.hash_map.remove('rows_filter')
        self.hash_map.put("SearchString", "")
        self.hash_map.finish_process()

    def _handle_barcode_camera(self):
        barcode = self.hash_map.get('barcode_camera')
        self.service.add_barcode_to_database(barcode)
        self.service.set_doc_status_to_upload(self.id_doc)
        self.service.set_barc_flow_status()

    def _handle_dialog_input_barcode(self):
        barcode = self.hash_map.get('fld_barcode')
        self.service.add_barcode_to_database(barcode)
        self.service.set_doc_status_to_upload(self.id_doc)

    def _handle_confirm_verified(self):
        self.service.mark_verified()
        self.hash_map.show_screen("Документы")   

    def _handle_ocr_serial_template_settings(self):
        ocr_nosql = SerialNumberOCRSettings.ocr_nosql
        ocr_nosql.put('show_process_result', True, True)
        self.hash_map.show_process_result('OcrTextRecognition', 'SerialNumberOCRSettings')
        screen = SerialNumberOCRSettings(self.hash_map, None)
        screen.parent_screen = self
        screen.show_process_result()

    def _barcode_flow_on_start(self):
        id_doc = self.hash_map.get('id_doc')

        doc_details = self.service.get_flow_table_data()
        table_data = self._prepare_table_data(doc_details)
        table_view = self._get_doc_table_view(table_data=table_data)

        have_qtty_plan, have_zero_plan = self.service.get_quantity_plan_data(id_doc)
        have_mark_plan = self.service.get_mark_plan_data(id_doc)
        control = self.service.get_control_data(id_doc)

        self.hash_map.put('have_qtty_plan', str(have_qtty_plan))
        self.hash_map.put('have_zero_plan', str(have_zero_plan))
        self.hash_map.put('have_mark_plan', str(have_mark_plan))
        self.hash_map.put('control', control)
        self.hash_map.put("doc_barc_flow", table_view.to_json())

        if True in (have_qtty_plan, have_zero_plan, have_mark_plan, control):
            self.hash_map.put('toast',
                            'Данный документ содержит плановые строки. Список штрихкодов в него поместить нельзя')
            self.hash_map.put('ShowScreen', 'Документы')

    def on_post_start(self):
        pass

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
                        self.TextView('@barcode'),
                        widgets.TextView(
                            Value='@name',
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

    def _prepare_table_data(self, doc_details):

        if self.hash_map.get("event") == "onResultPositive":
            barcode = str(self.hash_map.get('fld_barcode'))
        else:
            barcode = str(self.hash_map.get('barcode_camera'))

        if barcode:
            doc_details = self._sort_table_by_barcode(doc_details, barcode)

        table_data = [{}]
        # self.hash_map.toast(self.hash_map.get('added_goods'))

        for record in doc_details:
            use_series = bool(record.get('use_series', 0))
            product_row = {'key': str(record['barcode']), 'barcode': str(record['barcode']),
                           'name': record['name'] if record['name'] is not None else '-нет данных-',
                           'qtty': str(record['qtty']),
                           '_layout': self._get_doc_table_row_view(use_series)}

            product_row['_layout'].BackgroundColor = '#FFFFFF' if record['name'] is not None else "#FBE9E7"

            # это не работает судя по всему потому что нет в hash_map ключа added_goods
            if self._added_goods_has_key(product_row['key']):
                table_data.insert(1, product_row)
            else:
                table_data.append(product_row)

        return table_data

    def _sort_table_by_barcode(self, table, barcode):

        for i, row in enumerate(table):
            if str(row.get('barcode')) == barcode:
                del table[i]
                table.insert(0, row)
                break

        return table

    def _set_vision_settings(self) -> None:
        ocr_nosql = SerialNumberOCRSettings.ocr_nosql
        serial_ocr_settings = ocr_nosql.get('serial_ocr_settings')
        if serial_ocr_settings:
            serial_ocr_settings = json.loads(serial_ocr_settings)
            self.hash_map.set_vision_settings(**serial_ocr_settings)
            ocr_nosql.put('from_screen', 'FlowDocDetailsScreen', True)
