from dataclasses import dataclass

from db_services import BarcodeService
from ui_utils import BarcodeParser
from datetime import datetime, timedelta
from java import jclass

noClass = jclass("ru.travelfood.simple_ui.NoSQL")
rs_settings = noClass("rs_settings")


class BarcodeWorker:
    def __init__(self, id_doc, **kwargs):
        self.id_doc = id_doc
        self.control = kwargs.get('control', False)
        self.have_mark_plan = kwargs.get('have_mark_plan', False)
        self.have_qtty_plan = kwargs.get('have_qtty_plan', False)
        self.have_zero_plan = kwargs.get('have_zero_plan', False)
        self.use_scanning_queue = kwargs.get('use_scanning_queue', False)
        self.barcode_info = None
        self.document_row = None
        self.db_service = BarcodeService()
        self.process_result = self.ProcessTheBarcodeResult()
        self.user_tmz = 0
        self.barcode_data = {}
        self.mark_update_data = {}
        self.docs_table_update_data = {}
        self.queue_update_data = {}
        self.group_scan = kwargs.get('group_scan', False)

    def process_the_barcode(self, barcode):
        self.process_result.barcode = barcode
        self.barcode_info = BarcodeParser(barcode).parse(as_dict=False)

        if self.barcode_info.error:
            self._set_process_result_info('invalid_barcode')
            return self.process_result

        self.barcode_data = self._get_barcode_data()

        if self.barcode_data:
            self._check_use_series()
            self.check_barcode()
            self.update_document_barcode_data()
        else:
            self._set_process_result_info('not_found')

        return self.process_result

    def _check_use_series(self):
        if int(self.barcode_data.get('use_series', 0)):
            self._set_process_result_info('use_series')

    def _get_barcode_data(self):
        barcode_data = self.db_service.get_barcode_data(
            id_doc=self.id_doc,
            barcode_info=self.barcode_info
        )
        return barcode_data or {}

    def check_barcode(self):
        if self.process_result.error:
            return
        if self._use_mark():
            self._check_mark_in_document()
        self._check_barcode_in_document()

    def _check_mark_in_document(self):
        if self.barcode_info.scheme == 'GS1':
            if self.barcode_data['mark_id']:
                if self.barcode_data['approved'] == '1':
                    self._set_process_result_info('mark_already_scanned')
                else:
                    self._insert_mark_data()
            else:
                if self.have_mark_plan and self.control:
                    self._set_process_result_info('mark_not_found')
                else:
                    self._insert_mark_data()
        else:
            self._set_process_result_info('not_valid_barcode')

    def _check_barcode_in_document(self):
        if self.process_result.error:
            return

        new_device_qtty = self.barcode_data['d_qtty'] + self.barcode_data['ratio']
        new_overall_qtty = self.barcode_data['qtty'] + self.barcode_data['ratio']

        if self.barcode_data['row_key']:
            if self.have_qtty_plan and self.control and self.barcode_data['qtty_plan'] < \
                    max(new_device_qtty, new_overall_qtty):
                self._set_process_result_info('quantity_plan_reached')

        elif self.have_zero_plan and self.control:
            self._set_process_result_info('zero_plan_error')

        if not self.process_result.error:
            if self.use_scanning_queue:
                self._insert_queue_data()
                self._insert_doc_table_data(new_device_qtty)
            else:
                self._insert_doc_table_data(new_device_qtty)

    def _insert_mark_data(self):
        self.mark_update_data = {
            'id_doc': self.id_doc,
            'id_good': self.barcode_data['id_good'],
            'id_property': self.barcode_data['id_property'],
            'id_series': self.barcode_data['id_series'],
            'id_unit': self.barcode_data['id_unit'],
            'barcode_from_scanner': self.barcode_info.barcode,
            'approved': '1',
            'gtin': self.barcode_info.gtin,
            'series': self.barcode_info.serial,
            'mark_code': self.barcode_info.barcode
        }

        if self.barcode_data['mark_id']:
            self.mark_update_data['id'] = self.barcode_data['mark_id']

    def _insert_doc_table_data(self, qty):

        self.docs_table_update_data = {
            'id_doc': self.id_doc,
            'id_good': self.barcode_data['id_good'],
            'id_properties': self.barcode_data['id_property'],
            'id_series': self.barcode_data['id_series'],
            'id_unit': self.barcode_data['id_unit'],
            'qtty': self.barcode_data['qtty'],
            'd_qtty': float(qty),
            'qtty_plan': self.barcode_data['qtty_plan'],
            'last_updated': (datetime.now() - timedelta(hours=self.user_tmz)).strftime("%Y-%m-%d %H:%M:%S"),
            'id_cell': '',
            'price': self.barcode_data['price'],
            'id_price': self.barcode_data['id_price']
        }

        if not self.group_scan:
            self.docs_table_update_data['qtty'] = float(qty)

        if self.barcode_data['row_key']:
            self.docs_table_update_data['id'] = self.barcode_data['row_key']

    def _insert_queue_data(self):
        self.queue_update_data = {
            "id_doc": self.id_doc,
            "id_good": self.barcode_data['id_good'],
            "id_properties": self.barcode_data['id_property'],
            "id_series": self.barcode_data['id_series'],
            "id_unit": self.barcode_data['id_unit'],
            "id_cell": '',
            "d_qtty": self.barcode_data['ratio'],
            'row_key': self.barcode_data['row_key'],
            'sent': False,
            'price': self.barcode_data['price'],
            'id_price': self.barcode_data['id_price']
        }

    def update_document_barcode_data(self):
        if self.process_result.error:
            return

        if self.mark_update_data:
            self.db_service.replace_or_create_table(table_name="RS_docs_barcodes", docs_table_update_data=self.mark_update_data)

        if self.docs_table_update_data:
            self.db_service.replace_or_create_table(table_name="RS_docs_table", docs_table_update_data=self.docs_table_update_data)

        if self.queue_update_data:
            self.db_service.insert_no_sql(self.queue_update_data)

        if self._use_mark():
            self._set_process_result_info('success_mark')
        else:
            self._set_process_result_info('success_barcode')

    def _use_mark(self):
        return rs_settings.get('use_mark') == 'true' and self.barcode_data.get('use_mark', False)

    def _set_process_result_info(self, info_key):
        ratio = getattr(self.barcode_data, 'ratio', 0)

        info_data = {
            'invalid_barcode': {
                'error': 'Invalid barcode',
                'description': 'Неверный штрихкод',
            },
            'not_found': {
                'error': 'Not found',
                'description': 'Штрихкод не найден в базе',
            },
            'mark_not_found': {
                'error': 'Not found',
                'description': 'Марка не найдена в документе',
            },
            'not_valid_barcode': {
                'error': 'Not valid barcode',
                'description': 'Товар подлежит маркировке, отсканирован неверный штрихкод маркировки',
            },
            'mark_already_scanned': {
                'error': 'Already scanned',
                'description': 'Такая марка уже была отсканирована',
            },
            'zero_plan_error': {
                'error': 'Zero plan error',
                'description': 'В данный документ нельзя добавить товар не из списка',
            },
            'quantity_plan_reached': {
                'error': 'Quantity plan reached',
                'description': 'Количество план будет превышено при добавлении {} единиц товара'.format(ratio),
            },
            'success_barcode': {
                'error': '',
                'description': 'Товар добавлен в документ'
            },
            'success_mark': {
                'error': '',
                'description': 'Марка добавлена в документ'
            },
            'use_series': {
                'error': 'use_series',
                'description': 'Для товара необходимо отсканировать серии',
            }
        }

        if info_data.get(info_key):
            self.process_result.error = info_data[info_key]['error']
            self.process_result.description = info_data[info_key]['description']
            self.process_result.row_key = self.barcode_data.get('row_key', 0)
            self.process_result.barcode_data = self.barcode_data

    def parse(self, barcode: str):
        return BarcodeParser(barcode).parse()

    @dataclass
    class ProcessTheBarcodeResult:
        error: str = ''
        description: str = ''
        barcode: str = ''
        row_key: str = ''
        barcode_data = None


class BarcodeAdrWorker(BarcodeWorker):
    def __init__(self, id_doc, **kwargs):
        super().__init__(id_doc, **kwargs)
        self.is_adr_doc = True
        self.id_cell = kwargs.get('id_cell', '')
        self.table_type = kwargs.get('table_type', '')

    def _get_barcode_data(self):
        barcode_data = self.db_service.get_barcode_data(
            id_doc=self.id_doc,
            barcode_info=self.barcode_info,
            is_adr_doc=self.is_adr_doc,
            id_cell=self.id_cell,
            table_type=self.table_type
        )

        return barcode_data or {}

    def _check_mark_in_document(self):
        pass

    def _insert_mark_data(self):
        pass

    def _insert_doc_table_data(self, qty):

        self.docs_table_update_data = {
            'id_doc': self.id_doc,
            'id_good': self.barcode_data['id_good'],
            'id_properties': self.barcode_data['id_property'],
            'id_series': self.barcode_data['id_series'],
            'id_unit': self.barcode_data['id_unit'],
            'qtty': float(qty),
            'qtty_plan': self.barcode_data['qtty_plan'],
            'last_updated': (datetime.now() - timedelta(hours=self.user_tmz)).strftime("%Y-%m-%d %H:%M:%S"),
            'id_cell': self.id_cell,
            'table_type': self.table_type,
        }

        if self.barcode_data['row_key']:
            self.docs_table_update_data['id'] = self.barcode_data['row_key']

    def _insert_queue_data(self):
        pass

    def update_document_barcode_data(self):
        if self.process_result.error:
            return

        if self.docs_table_update_data:
            self.db_service.replace_or_create_table(
                table_name="RS_adr_docs_table",
                docs_table_update_data=self.docs_table_update_data)

        self._set_process_result_info('success_barcode')
