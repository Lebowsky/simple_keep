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

    def on_input(self):
        if self.listener == "CardsClick":
            args = self._get_selected_card_put_data()
            self.hash_map.show_screen('ПотокШтрихкодовДокумента', args)
            # screen: FlowDocDetailsScreen = FlowDocDetailsScreen(self.hash_map, self.rs_settings)
            # screen.show(args=args)
        elif self.listener == "ON_BACK_PRESSED":
            self.hash_map.show_screen('Плитки')  # finish_process()
        elif self.listener == 'doc_type_click':
            self.hash_map.refresh_screen()
        elif self._is_result_positive('confirm_clear_barcode_data'):
            id_doc = self.get_id_doc()
            res = self._clear_barcode_data(id_doc)
            self.service.set_doc_status_to_upload(id_doc)
            if res.get('result'):
                self.toast('Все штрихкоды удалены из документа')
            else:
                self.toast('При очистке данных возникла ошибка.')
                self.hash_map.error_log(res.get('error'))

        super().on_input()


class FlowDocDetailsScreen(DocDetailsScreen):
    screen_name = 'ПотокШтрихкодовДокумента'
    process_name = 'Сбор ШК'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = db_services.FlowDocService(self.id_doc)

    def show(self, args=None):
        self.hash_map.show_screen(self.screen_name, args)

    def on_start(self):
        self._barcode_flow_on_start()
        self._set_vision_settings()

    def on_input(self):
        listener = self.hash_map.get('listener')
        if listener == "CardsClick":
            current_str = self.hash_map.get("selected_card_position")
            jlist = json.loads(self.hash_map.get("doc_barc_flow"))
            current_elem = jlist['customtable']['tabledata'][int(current_str)]
            data = {'barcode': current_elem['barcode'],
                    'Номенклатура': current_elem['name'],
                    'qtty': current_elem['qtty'], 'Характеристика': ''}

            PrintService.print(self.hash_map, data)

        elif listener == "BACK_BUTTON":
            self.hash_map.remove('rows_filter')
            self.hash_map.put("SearchString", "")
            self.hash_map.finish_process()

        elif listener == 'btn_barcodes':
            self._show_dialog_input_barcode()

        elif listener == 'barcode':
            barcode = self.hash_map.get('barcode_camera')
            self.service.add_barcode_to_database(barcode)
            self.service.set_doc_status_to_upload(self.id_doc)
            self.service.set_barc_flow_status()

        elif self._is_result_positive('modal_dialog_input_barcode'):
            barcode = self.hash_map.get('fld_barcode')
            self.service.add_barcode_to_database(barcode)
            self.service.set_doc_status_to_upload(self.id_doc)

        elif self._is_result_positive('confirm_verified'):
            self.service.mark_verified()
            self.hash_map.show_screen("Документы")

        elif listener == 'btn_doc_mark_verified':
            self.hash_map.show_dialog('confirm_verified',
                                      'Завершить документ?',
                                      ['Да', 'Нет'])

        elif listener == 'ON_BACK_PRESSED':
            self.hash_map.show_screen("Документы")

        elif listener == 'vision_cancel':
            SerialNumberOCRSettings.ocr_nosql_counter.destroy()

        elif listener == 'vision':
            SerialNumberOCRSettings.ocr_nosql_counter.destroy()

        elif listener == 'ПечатьПревью':
            self.hash_map.put('RefreshScreen', '')

        elif listener == 'btn_ocr_serial_template_settings':
            ocr_nosql = SerialNumberOCRSettings.ocr_nosql
            ocr_nosql.put('show_process_result', True, True)
            self.hash_map.show_process_result('OcrTextRecognition', 'SerialNumberOCRSettings')

    def _barcode_flow_on_start(self):

        id_doc = self.hash_map.get('id_doc')
        falseValueList = (0, '0', 'false', 'False', None)
        # Формируем таблицу карточек и запрос к базе

        doc_details = self.service.get_flow_table_data()
        table_data = self._prepare_table_data(doc_details)
        table_view = self._get_doc_table_view(table_data=table_data)

        if doc_details:
            # hashMap.put('id_doc', str(results[0]['id_doc']))

            # Признак, have_qtty_plan ЕстьПланПОКОличеству  -  Истина когда сумма колонки Qtty_plan > 0
            # Признак  have_mark_plan "ЕстьПланКОдовМаркировки – Истина, когда количество строк табл. RS_docs_barcodes с заданным id_doc и is_plan  больше нуля.
            # Признак have_zero_plan "Есть строки товара в документе" Истина, когда есть заполненные строки товаров в документе
            # Признак "Контролировать"  - признак для документа, надо ли контролировать

            qtext = '''
                SELECT distinct count(id) as col_str,
                sum(ifnull(qtty_plan,0)) as qtty_plan
                from RS_docs_table Where id_doc = :id_doc'''
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
            qtext = '''
                SELECT distinct count(id) as col_str
                from RS_docs_barcodes Where id_doc = :id_doc AND is_plan = :is_plan'''
            res = ui_global.get_query_result(qtext, {'id_doc': id_doc, 'is_plan': '1'})
            if not res:
                have_mark_plan = False

            else:
                have_mark_plan = res[0][0] > 0
        else:
            have_qtty_plan = False
            have_zero_plan = False
            have_mark_plan = False

        self.hash_map.put('have_qtty_plan', str(have_qtty_plan))
        self.hash_map.put('have_zero_plan', str(have_zero_plan))
        self.hash_map.put('have_mark_plan', str(have_mark_plan))
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

    def _get_doc_table_row_view(self):
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

            product_row = {'key': str(record['barcode']), 'barcode': str(record['barcode']),
                           'name': record['name'] if record['name'] is not None else '-нет данных-',
                           'qtty': str(record['qtty']),
                           '_layout': self._get_doc_table_row_view()}

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
