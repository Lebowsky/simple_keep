from typing import Dict

import db_services
import widgets
import ui_models
from printing_factory import PrintService
from ui_utils import HashMap
from barcode_workers import BarcodeAdrWorker


class AdrDocsListScreen(ui_models.DocsListScreen):
    screen_name = 'Документы'
    process_name = 'Адресное хранение'

    def __init__(self, hash_map: HashMap, rs_settings=None):
        super().__init__(hash_map)

        self.service = db_services.AdrDocService()
        self.screen_values = {}
        self.doc_types = ('Все', 'Отбор', 'Размещение', 'Перемещение')
        self.doc_statuses = ('Все', 'К выполнению', 'Выгружен', 'К выгрузке')
        self.popup_menu_data = ('Удалить', 'Очистить данные пересчета', 'Отправить повторно')
        self.current_status = 'Все'
        self.current_doc_type = 'Все'
        self.list_data_key = 'documents_list'

    def init_screen(self):
        self.hash_map['doc_adr_type_select'] = ';'.join(self.doc_types)
        self.hash_map['doc_status_select'] = ';'.join(self.doc_statuses)
        self._fill_table_data()

    def on_start(self) -> None:
        self._fill_table_data()

    def on_input(self) -> None:
        listeners = {
            'CardsClick': self._cards_click,
            'doc_adr_type_click': self._doc_type_select,
            'confirm_clear_barcode_data': lambda: self._clear_barcode_data(self.get_id_doc()),
        }
        if self.listener in listeners:
            listeners[self.listener]()
        else:
            super().on_input()

    def _cards_click(self):
        self.hash_map.remove(self.list_data_key)
        id_doc = self.hash_map['selected_card_key']
        AdrDocDetailsScreen(self.hash_map, id_doc=id_doc).show()
        self.hash_map.no_refresh()

    def _doc_type_select(self):
        self.current_doc_type = self.hash_map['doc_adr_type_click']

    def _back_screen(self):
        self._finish_process()

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

    def _fill_table_data(self):
        list_data = self._get_doc_list_data(self.current_doc_type, self.current_status)
        prepared_data = self._prepare_table_data(list_data)
        doc_cards = self._get_doc_cards_view(
            prepared_data,
            popup_menu_data=';'.join(self.popup_menu_data)
        )
        self.hash_map[self.list_data_key] = doc_cards.to_json()

    def _get_doc_list_data(self, doc_type, doc_status) -> list:
        doc_type = '' if doc_type == "Все" else doc_type
        doc_status = '' if doc_status == 'Все' else doc_status

        docs_data = self.service.get_doc_view_data(doc_type, doc_status)
        return docs_data

    def _prepare_table_data(self, list_data) -> list:
        table_data = []
        for record in list_data:
            doc_status = ''

            if record['verified'] and record['sent']:
                doc_status = 'Выгружен'
            elif record['verified']:
                doc_status = 'К выгрузке'
            elif not (record['verified'] and record['sent']):
                doc_status = 'К выполнению'

            doc_title = '{} от {}'.format(
                record['doc_n'], self._format_date(record['doc_date']))

            table_data.append({
                'key': record['id_doc'],
                'doc_type': record['doc_type'],
                'doc_title': doc_title,
                'doc_n': record['doc_n'],
                'doc_date': self._format_date(record['doc_date']),
                'warehouse': record['warehouse'],
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
                        Value='@doc_type',
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
                        Value='@doc_n',
                        TextBold=True,
                        TextSize=card_title_text_size
                    )
                ),
                widgets.LinearLayout(

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

    def _doc_delete(self, id_doc):
        result = True
        try:
            self.service.delete_adr_doc(id_doc)
        except Exception as e:
            self.hash_map.error_log(e.args[0])
            result = False

        return result

    def _get_selected_card_put_data(self, put_data=None):
        card_data = self._get_selected_card_data()

        table_type = 'out' if card_data['doc_type'] in ['Отбор', 'Перемещение'] else 'in'

        put_data = put_data or {}
        put_data['id_doc'] = card_data['key']
        put_data['doc_type'] = card_data['doc_type']
        put_data['table_type'] = table_type
        put_data['doc_n'] = card_data['doc_n']
        put_data['doc_date'] = card_data['doc_date']
        put_data['doc_title'] = card_data['doc_title']
        put_data['warehouse'] = card_data['warehouse']

        return put_data

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
                self._finish_process()
        else:
            self.hash_map.toast('Ошибка удаления документа')

    def _clear_barcode_data(self, id_doc):
        id_doc = self.hash_map.get_json('card_data').get('key') if self.hash_map['card_data'] else ''
        return self.service.clear_barcode_data(id_doc)

    def get_id_doc(self):
        id_doc = self.hash_map['selected_card_key']
        return id_doc


class AdrDocDetailsScreen(ui_models.DocDetailsScreen):
    screen_name = 'Документ товары'
    process_name = 'Адресное хранение'

    def __init__(self, hash_map, id_doc, rs_settings=None):
        super().__init__(hash_map=hash_map)
        self.tables_types = 'Отбор;Размещение'
        self.id_doc = id_doc
        self.service = None
        self.current_cell = ''
        self.current_cell_id = ''
        self.table_type = ''
        self.doc_type = ''
        self.doc_title = ''
        self.doc_data = {}
        self.list_data_key = 'doc_goods_table'
        self.screen_data = {}
        self.hash_map_keys = []

    def init_screen(self):
        self.service = db_services.AdrDocService(id_doc=self.id_doc)
        self.doc_data = self.service.get_doc_data_by_id()

        self.doc_type = self.doc_data['doc_type']
        self.table_type = self._get_table_type_from_name(self.doc_type)
        self.service.table_type = self.table_type

        self.doc_title = self._get_doc_title(**self.doc_data)
        self.doc_data['tables_type'] = self.tables_types
        self.doc_data['table_type'] = self.doc_data['doc_type']
        self.doc_data['doc_title'] = self.doc_title

        self.hash_map.put_data(self.doc_data, fill_none=True)
        self.hash_map.put('return_selected_data')
        self._set_current_cell()

    def on_start(self):
        super()._on_start()

    def on_input(self) -> None:
        listeners = {
            'CardsClick': self._cards_click,
            'btn_barcodes': lambda: self.hash_map.show_dialog(listener="ВвестиШтрихкод"),
            'barcode': lambda: self._barcode_listener(self.hash_map.get('barcode_camera')),
            'btn_doc_mark_verified': self._doc_mark_verified,
            'btn_select_cell': self._select_cell,
            'cell_select_success': self._select_cell_result,
            'btn_clear_cell': self._clear_cell,
            'table_type': self._table_type_selected,
            'ON_BACK_PRESSED': self._back_screen,
            'BACK_BUTTON': self._back_screen,
        }

        if self.listener in listeners:
            listeners[self.listener]()
        elif self._is_result_positive('ВвестиШтрихкод'):
            self._barcode_listener(self.hash_map['fld_barcode'])
        super().on_input()

    def _cards_click(self):
        selected_card_data = self._get_selected_card_data()
        if not selected_card_data:
            return

        self.hash_map.remove(self.list_data_key)
        if selected_card_data.get('use_series') == '1':
            self._open_series_screen(selected_card_data['key'])
        else:
            self._open_select_goods_screen(data=selected_card_data)

        self.hash_map.no_refresh()

    def _barcode_listener(self, barcode):
        if self._update_current_cell(barcode):
            return

        barcode_process_params = self._get_barcode_process_params()
        barcode_process_params['is_adr_doc'] = True
        barcode_process_params['id_cell'] = self.current_cell_id
        barcode_process_params['table_type'] = self.table_type

        self.barcode_worker = BarcodeAdrWorker(
            id_doc=self.id_doc,
            **barcode_process_params,
            use_scanning_queue=False
        )

        result = self.barcode_worker.process_the_barcode(barcode)
        if result.error:
            self._process_error_scan_barcode(result)
            return result.error

    def _update_current_cell(self, barcode):
        current_cell = self.current_cell_id
        doc_cell = self.service.find_cell(barcode)

        if doc_cell and current_cell != doc_cell:
            self._set_current_cell(doc_cell['name'], doc_cell['id'])
            return True

        if not self.current_cell_id:
            self.hash_map.playsound('warning')
            self.hash_map.put('toast', 'Не найдена ячейка')
            return True

    def _process_error_scan_barcode(self, scan_result):
        if scan_result.error == 'use_series':
            self._open_series_screen(scan_result.row_key)
            self.hash_map.playsound('warning')
        else:
            self.hash_map.toast(scan_result.description)
            self.hash_map.playsound('error')

    def _doc_mark_verified(self):
        self.service.mark_verified()
        self._set_current_cell()
        self.hash_map.put("SearchString", "")
        AdrDocsListScreen(self.hash_map).show()

    def _select_cell(self):
        self.hash_map.put("SearchString", "")
        self._open_select_cell_screen()

    def _open_select_cell_screen(self):
        screen = ui_models.SelectItemScreen(
            self.hash_map,
            table_name='RS_cells',
            result_listener='cell_select_success'
        )
        screen.parent_screen = self
        screen.show()

    def _select_cell_result(self):
        selected_cell = self.hash_map.get_json('selected_card')
        if selected_cell:
            self._set_current_cell(selected_cell.get('name'), selected_cell.get('id'))
            self.hash_map.remove('selected_card')
        else:
            self._set_current_cell()

    def _clear_cell(self):
        self._set_current_cell()
        self.hash_map.refresh_screen()

    def _table_type_selected(self):
        self.table_type = self._get_table_type_from_name(self.hash_map['table_type'])
        self.service.table_type = self.table_type
        self.hash_map.refresh_screen()

    def _back_screen(self):
        self.hash_map.put("SearchString", "")

        if self.current_cell_id:
            self._set_current_cell()
            self.hash_map.refresh_screen()
        else:
            self.hash_map.remove('return_selected_data')
            AdrDocsListScreen(self.hash_map).show()

    def _open_series_screen(self, doc_row_key):
        self.hash_map['use_adr_docs_tables'] = True
        screen_values = {
            'doc_row_id': doc_row_key,
            'title': 'Серии',
        }

        screen = ui_models.SeriesSelectScreen(self.hash_map)
        screen.parent_screen = self
        screen.show_process_result(screen_values)

    def _open_select_goods_screen(self, data):
        doc_row_id = self.hash_map['selected_card_key']
        screen = AdrGoodsSelectScreen(self.hash_map, doc_row_id=doc_row_id)
        screen.show()

    def _get_doc_details_data(self, last_scanned=False):
        super()._check_previous_page()
        first_element = int(self.hash_map.get('current_first_element_number'))
        row_filters = self.hash_map.get('rows_filter')
        search_string = self.hash_map.get('SearchString') if self.hash_map.get('SearchString') else None

        data = self.service.get_doc_details_data(
            id_doc=self.id_doc,
            cell=self.current_cell_id,
            first_elem=0 if last_scanned else first_element,
            items_on_page=1 if last_scanned else self.items_on_page,
            row_filters=row_filters,
            search_string=search_string
        )
        self.doc_rows = self.service.get_doc_details_rows_count(
            id_doc=self.id_doc,
            row_filters=row_filters,
            search_string=search_string
        )

        if not last_scanned:
            super()._check_next_page(len(data))

        return data

    @staticmethod
    def _get_table_type_from_name(_val):
        return 'in' if _val == 'Размещение' else 'out'

    def _prepare_table_data(self, doc_details):
        # TODO добавить группировку по ячейкам
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
                'cell': str(record['cell_name']),
                'id_cell': str(record['id_cell']),
                'good_name': str(record['good_name']),
                'id_good': str(record['id_good']),
                'id_property': str(record['id_properties']),
                'properties_name': str(record['properties_name'] or ''),
                'id_series': str(record['id_series']),
                'series_name': str(record['series_name'] or ''),
                'id_unit': str(record['id_unit']),
                'units_name': str(record['units_name'] or ''),
                'code_art': 'Код: ' + str(record['code']),
                'art': str(record['art']),
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
                    self.TextView('Ячейка'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('Название'),
                    weight=2
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
                widgets.TextView(
                    Value='@cell',
                    TextSize=15,
                    width='match_parent',
                ),
                width='match_parent',
                height='match_parent',
                weight=1,
                StrokeWidth=1
            ),
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
                weight=2,
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
        pass

    def _set_background_row_color(self, product_row):
        background_color = '#FFFFFF'
        qtty, qtty_plan = float(product_row['qtty']), float(product_row['qtty_plan'])
        if qtty_plan > qtty:
            background_color = "#FBE9E7"

        elif qtty_plan < qtty:
            background_color = "#FFF9C4"

        setattr(product_row['_layout'], 'BackgroundColor', background_color)

    def _set_current_cell(self, current_cell='- не выбрано -', current_cell_id=''):
        self.current_cell, self.current_cell_id = current_cell, current_cell_id
        self.hash_map['current_cell'] = current_cell
        if current_cell_id:
            self.hash_map['Show_btn_clear_cell'] = 1
        else:
            self.hash_map['Show_btn_clear_cell'] = -1


class AdrGoodsSelectScreen(ui_models.BaseGoodSelect):
    screen_name = 'Товар выбор'
    process_name = 'Адресное хранение'

    def __init__(self, hash_map: HashMap, doc_row_id, rs_settings=None):
        super().__init__(hash_map)
        self.service = db_services.AdrDocService()
        self.doc_row_id = doc_row_id

    def init_screen(self):
        self.screen_data = self.service.get_doc_row_data(self.doc_row_id)

        self.hash_map.put_data({
            key: self._format_quantity(self.screen_data.get(key, 0))
            if key in ['qtty_plan', 'qtty'] else self.screen_data.get(key, '')
            for key in self.hash_map_keys
        })
        self._set_visibility()

    def on_start(self):
        super().on_start()

    def on_input(self):
        listeners = {
            'btn_series_show': lambda: self._open_series_screen(),
            'btn_doc_good_barcode': self._open_barcode_register_screen,
            'btn_print': self._print_ticket
        }

        if self.listener in listeners:
            listeners[self.listener]()
        else:
            super().on_input()

    def _back_screen(self):
        screen = AdrDocDetailsScreen(self.hash_map, self.screen_data['id_doc'])
        screen.show()

    def _open_series_screen(self, doc_row_id=''):
        self.hash_map['use_adr_docs_tables'] = True
        screen_values = {
            'doc_row_id': self.doc_row_id,
            'title': 'Серии',
        }
        screen = ui_models.SeriesSelectScreen(self.hash_map)
        screen.parent_screen = self
        screen.show_process_result(screen_values)

    def _open_barcode_register_screen(self):
        init_data = {
            'item_id': self.screen_data['item_id'],
            'property_id': self.screen_data['property_id'],
            'unit_id': self.screen_data['unit_id']
        }
        self.hash_map.put_data(init_data)

        screen = ui_models.BarcodeRegistrationScreen(self.hash_map, self.rs_settings)
        screen.parent_screen = self
        screen.show_process_result()

    def _print_ticket(self):
        barcode = db_services.BarcodeService().get_barcode_from_doc_table(self.hash_map.get('key'))

        data = {
            'Номенклатура': 'item_name',
            'Артикул': 'article',
            'Характеристика': 'property',
            'ЕдИзм': 'unit',
        }

        for key in data:
            data[key] = self.hash_map.get(data[key])

        data['barcode'] = barcode if barcode else '0000000000000'
        PrintService.print(self.hash_map, data)

    def _update_doc_table_row(self, data: Dict, row_id=''):
        if not self.hash_map.get('delta'):
            return

        update_data = {
            'sent': 0,
            'qtty': float(data['qtty']),
        }

        self.service.update_doc_table_row(data=update_data, row_id=self.doc_row_id)
        self.service.set_doc_status_to_upload(self.screen_data['id_doc'])

    def _handle_found_barcode(self, res, id_good, id_property, id_unit):
        is_current_position = all((
            self.screen_data['item_id'] == res['id_good'],
            self.screen_data['property_id'] == res['id_property'],
            self.screen_data['unit_id'] == res['id_unit']
        ))

        if is_current_position:
            if self.screen_data['use_series'] == "1":
                self._open_series_screen(self.hash_map['key'])
            else:
                self._set_delta(res['ratio'])
            return True

        self.current_toast_message = 'Штрихкод не соответствует текущей позиции'

        return False