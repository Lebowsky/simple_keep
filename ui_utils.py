import json
import re
from dataclasses import dataclass, asdict
from typing import Callable, Union, List, Dict, Optional
from functools import wraps
import socket


from java import jclass
from ui_global import Rs_doc, find_barcode_in_barcode_table
from ui_barcodes import parse_barcode
from db_services import DocService, BarcodeService

noClass = jclass("ru.travelfood.simple_ui.NoSQL")
rs_settings = noClass("rs_settings")


# Класс-декоратор для удобной работы с hashMap. Также можно добавить дополнительную логику.
class HashMap:
    def __init__(self, hash_map=None, debug: bool = False):
        self.hash_map = hash_map
        self.debug_mode = debug

    def __call__(self, func: Callable[..., None]):
        @wraps(func)
        def wrapper(hashMap, *args, **kwargs):
            self.init(hashMap)
            func(self)
            return hashMap

        return wrapper

    def init(self, hashMap):
        self.hash_map = hashMap

    def finish_process(self):
        self.hash_map.put('FinishProcess', '')

    def finish_process_result(self):
        self.hash_map.put('FinishProcessResult', '')

    def show_process_result(self, process, screen):
        if process and screen:
            self.hash_map.put('ShowProcessResult', f'{process}|{screen}')


    def set_result_listener(self, listener):
        if listener and isinstance(listener, str):
            self.hash_map.put('SetResultListener', listener)

    def toast(self, text, add_to_log=False):
        self.hash_map.put('toast', str(text))
        if add_to_log:
            self.error_log(text)

    def notification(self, text, title=None, add_to_log=False):
        notification_id = rs_settings.get("notification_id") + 1 if rs_settings.get("notification_id") else 1
        if title is None:
            title = self.get_current_screen()

        self.hash_map.put(
            "basic_notification",
            json.dumps([{'number': notification_id, 'title': str(title), 'message': text}])
        )

        rs_settings.put("notification_id", notification_id, True)
        if add_to_log:
            self.error_log(text)

    def debug(self, text):
        if self.debug_mode:
            self.toast(text, add_to_log=True)

    def refresh_screen(self):
        self.hash_map.put('RefreshScreen', '')

    def run_event(self, method_name):
        self['RunEvent'] = json.dumps(self._get_event(method_name))

    def run_event_async(self, method_name, post_execute_method=None):
        run_event = self._get_event(method_name, 'runasync')
        if post_execute_method:
            run_event[0]['postExecute'] = json.dumps(self._get_event(post_execute_method))
        self['RunEvent'] = json.dumps(run_event)

    def run_event_progress(self, method_name):
        self['RunEvent'] = json.dumps(self._get_event(method_name, 'runprogress'))


    def beep(self, tone=''):
        self.hash_map.put('beep', str(tone))

    def playsound(self, event: str, sound_val: str = ''):
        if not sound_val:
            sound = rs_settings.get(f'{event}_signal')
        else:
            sound = sound_val
        self.hash_map.put(f'playsound_{sound}', "")

    def _get_event(self, method_name, action=None):
        """
        :param method_name: handlers name
        :param action: run|runasync|runprogress

        :return: event dict
        """

        evt = [{
            'action': action if action else 'run',
            'type': 'python',
            'method': method_name,
        }]

        return evt

    def error_log(self, err_data):
        try:
            err_data = json.dumps(err_data, ensure_ascii=False, indent=2)
        except:
            err_data = str(err_data)

        rs_settings.put('error_log', err_data, True)

    def __getitem__(self, item):
        return self.get(item, False)

    def __setitem__(self, key, value):
        self.put(key, value, False)

    def get(self, item, from_json=False):
        if from_json:
            return json.loads(self.hash_map.get(item)) if self.hash_map.get(item) else None
        else:
            return self.hash_map.get(item)

    def get_json(self, item):
        return json.loads(self.hash_map.get(item)) if self.hash_map.get(item) else None

    def get_bool(self, item):
        value = str(self.hash_map.get(item)).lower() not in ('0', 'false', 'none')
        return value

    def put(self, key, value: Union[str, List, Dict, bool] = '', to_json=False):
        if to_json:
            self.hash_map.put(key, json.dumps(value))
        else:
            if isinstance(value, bool):
                value = str(value).lower()
            self.hash_map.put(key, str(value))

    def put_data(self, data: dict):
        for key, value in data.items():
            self[key] = value

    def containsKey(self, key):
        return self.hash_map.containsKey(key)

    def remove(self, key):
        self.hash_map.remove(key)

    def delete(self, key):
        self.hash_map.remove(key)

    def export(self) -> list:
        return self.hash_map.export()

    def to_json(self):
        return json.dumps(self.export(), indent=4, ensure_ascii=False).encode('utf8').decode()

    def show_screen(self, name, data=None):
        self.put('ShowScreen', name)
        if data:
            self.put_data(data)

    def show_dialog(self, listener, title='', buttons=None):
        self.put("ShowDialog", listener)

        if title or buttons:
            dialog_style = {
                'title': title or listener,
                'yes': 'Ок',
                'no': 'Отмена'
            }
            if buttons and len(buttons) > 1:
                dialog_style['yes'] = buttons[0]
                dialog_style['no'] = buttons[1]

            self.put('ShowDialogStyle', dialog_style)

    def get_current_screen(self):

        return self['current_screen_name'] if self.containsKey('current_screen_name') else ''

    def get_current_process(self):
        return self['current_process_name']

    def set_title(self, title):
        self['SetTitle'] = title

    def run_py_thread_progress(self, handlers_name: str):
        """
        Запускает асинхронное фоновое выполнение скрипта c блокирующим прогресс-баром, который блокирует UI-поток.
        В качестве аргумента - имя функции-хендлера.
        """

        self['RunPyThreadProgressDef'] = handlers_name

    def sql_exec(self, query, params=''):
        self._put_sql('SQLExec', query, params)

    def sql_exec_many(self, query, params=None):
        params = params or []
        self._put_sql('SQLExecMany', query, params)

    def sql_query(self, query, params=''):
        self._put_sql('SQLQuery', query, params)

    def _put_sql(self, sql_type, query, params):
        self.put(
            sql_type,
            {"query": query, 'params': params},
            to_json=True
        )


class RsDoc(Rs_doc):
    def __init__(self, id_doc):
        self.id_doc = id_doc

    def update_doc_str(self, price=0):
        pass

    def delete_doc(self):
        pass

    def clear_barcode_data(self):
        pass

    def mark_for_upload(self):
        pass

    def mark_verified(self, key):
        super().mark_verified(key)

    def find_barcode_in_table(self, search_value, func_compared='=?') -> dict:
        result = super().find_barcode_in_table(search_value, func_compared)
        if result:
            return result[0]
        else:
            return {}

    def find_barcode_in_mark_table(self, search_value: str, func_compared='=?'):
        pass

    def update_doc_table_data(self, elem_for_add: dict, qtty=1, user_tmz=0):
        pass

    def add_marked_codes_in_doc(self, barcode_info):
        pass

    def add_new_barcode_in_doc_barcodes_table(self, el, barcode_info):
        pass

    def process_the_barcode(
            self,
            barcode,
            have_qtty_plan=False,
            have_zero_plan=False,
            control=False,
            have_mark_plan=False,
            elem=None,
            use_mark_setting='false',
            user_tmz=0):

        Rs_doc.id_doc = self.id_doc
        result = Rs_doc.process_the_barcode(
            Rs_doc, barcode, have_qtty_plan, have_zero_plan, control, have_mark_plan, elem, use_mark_setting, user_tmz
        )
        if not result.get('Error'):
            service = DocService(self.id_doc)
            service.set_doc_value('sent', 0)

            res = self.find_barcode_in_table(barcode)
            if res.get('id'):
                result['key'] = res['id']

        return result

    def add(self, args):
        pass

    def get_new_id(self):
        pass

    def find_barcode_in_barcode_table(self, barcode):
        return find_barcode_in_barcode_table(barcode)


class BarcodeWorker:
    def __init__(self, id_doc='', **kwargs):
        self.id_doc = id_doc
        self.control = kwargs.get('control', False)
        self.have_mark_plan = kwargs.get('have_mark_plan', False)
        self.have_qtty_plan = kwargs.get('have_qtty_plan', False)
        self.have_zero_plan = kwargs.get('have_zero_plan', False)
        self.barcode_info = None
        self.barcode_data = {}
        self.document_row = None
        self.db_service = BarcodeService()
        self.process_result = self.ProcessTheBarcodeResult()


    def process_the_barcode(self, barcode):
        self.process_result.barcode = barcode
        self.barcode_info = BarcodeParser(barcode).parse(as_dict=False)

        if self.barcode_info.error:
            self._set_process_result_info('invalid_barcode')
            return self.process_result

        if self.barcode_info.scheme == 'GS1':
            search_value = self.barcode_info.gtin
        else:
            search_value = self.barcode_info.barcode

        self.barcode_data = self.get_barcode_data(search_value)

        if self.barcode_data:
            self.check_barcode_in_document()
            self.update_document_barcode_data()

        return self.process_result

    def get_barcode_data(self, barcode):
        barcode_data = self.db_service.get_barcode_data(barcode)

        if barcode_data:
            return barcode_data
        else:
            self._set_process_result_info('not_found')


    def check_barcode_in_document(self):
        if self.process_result.error:
            return

        if self._use_mark():
            self._check_mark_in_document()

        self._check_barcode_in_document()

    def update_document_barcode_data(self):
        if self.process_result.error:
            return

        if self.document_row_data:
            self.db_service.update_document_row_data(self.document_row_data)
        else:
            self.db_service.add_document_row(self.barcode_data)


    def _check_mark_in_document(self):
        if self.barcode_info.scheme == 'GS1':
            mark_data = self.db_service.get_mark_data(
                id_doc=self.id_doc, gtin=self.barcode_info.gtin, series=self.barcode_info.serial
            )
            if mark_data:
                if mark_data['approved'] == '1':
                    self._set_process_result_info('mark_already_scanned')
                else:
                    self.db_service.set_approve_mark(
                        _id=mark_data['id'],
                        barcode=self.barcode_info.barcode
                    )
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

        self.document_row_data = self.get_document_row_by_barcode()
        if self.document_row_data and self.have_qtty_plan:
            if self.document_row_data['qtty_plan'] > self.document_row_data['qtty'] + self.barcode_data['ratio']:
                self._set_process_result_info('quantity_plan_reached')

        elif self.have_zero_plan and self.control:
            self._set_process_result_info('zero_plan_error')

    def _insert_mark_data(self):
        self.db_service.insert_mark_data(
            id_doc=self.id_doc,
            id_good=self.barcode_data['id_good'],
            id_property=self.barcode_data['id_property'],
            id_series=self.barcode_data['id_series'],
            id_unit=self.barcode_data['id_unit'],
            barcode_from_scanner=self.barcode_info.barcode,
            approved='1',
            gtin=self.barcode_info.gtin,
            series=self.barcode_info.serial,
            ratio=1
        )

    def _use_mark(self):
        return rs_settings.get('use_mark') == 'true'

    def _set_process_result_info(self, info_key):
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
                'description': 'Количество план будет превышено при добавлении {} единиц товара'.format(
                    str(self.barcode_data.get('ratio', 0))
                ),
            }
        }
        # {'Result': 'Марка добавлена в документ', 'Error': None,
        #  'barcode': barcode_info['GTIN'] + barcode_info['SERIAL']}

        if info_data.get(info_key):
            self.process_result.error = info_data[info_key]['error']
            self.process_result.description = info_data[info_key]['description']

    def get_document_row_by_barcode(self):
        row_data = self.db_service.get_document_row_by_barcode(
            self.id_doc, self.barcode_info.barcode)
        if row_data:
            return row_data[0]

    def parse(self, barcode: str):
        return BarcodeParser(barcode).parse()
        # return {'SCHEME': 'EAN13', 'BARCODE': barcode, 'GTIN': barcode, 'SERIAL': ''}

    @dataclass
    class ProcessTheBarcodeResult:
        error: str = ''
        description: str = ''
        barcode: str = ''
        row_key: str = ''



class BarcodeParser:
    def __init__(self, barcode):
        self.barcode = barcode
        self.barcode_info = BarcodeParser.BarcodeInfo(barcode=barcode)
        self.macro_05 = f'[)>{chr(30)}05'
        self.macro_06 = f'[)>{chr(30)}06'
        self.gs1_separator = chr(29)
        self.identifier = ']d2'

    def parse(self, as_dict=True):
        if self.is_valid_ean13(self.barcode):
            self.barcode_info.scheme = 'EAN13'
            self.barcode_info.gtin = self.barcode

        elif len(self.barcode) == 29:
            self.barcode_info.scheme = 'GS1'
            self.barcode_info.gtin = self.barcode[0:14]
            self.barcode_info.serial = self.barcode[14:21]
            self.barcode_info.mrc = self.barcode[21:25]
            self.barcode_info.check = self.barcode[25:29]

        elif self.gs1_separator in self.barcode or '<GS>' in self.barcode:
            self.barcode_info.scheme = 'GS1'
            self.check_datamatrix(self.barcode)

        else:
            self.barcode_info.scheme = 'UNKNOWN'
            self.barcode_info.gtin = self.barcode

        if as_dict:
            return self.barcode_info.dict()
        else:
            return self.barcode_info

    @staticmethod
    def is_valid_ean13(code):
        pattern = r'^\d{13}$'
        if not re.match(pattern, code):
            return False

        factors = [1, 3] * 6
        checksum = sum(int(code[i]) * factors[i] for i in range(12))
        checksum = (10 - (checksum % 10)) % 10

        return checksum == int(code[-1])


    def check_datamatrix(self, barcode):
        barcode = self.clear_identifier(barcode)
        self.check_gs1_gtin(barcode)


    def check_gs1_gtin(self, barcode: str):
        if self.gs1_separator in barcode:
            while barcode:
                if barcode[:2] == '01':
                    self.barcode_info.gtin = barcode[2:16]
                    if len(barcode) > 16:
                        barcode = barcode[16:]
                    else:
                        barcode = None

                elif barcode[:3] == chr(29) + '01':
                    self.barcode_info.gtin = barcode[3:17]
                    if len(barcode) > 17:
                        barcode = barcode[17:]
                    else:
                        barcode = None

                elif barcode[:2] == '17':
                    self.barcode_info.expiry = barcode[2:8]
                    if len(barcode) > 8:
                        barcode = barcode[8:]
                    else:
                        barcode = None

                elif barcode[:2] == '10':
                    if chr(29) in barcode:
                        index = barcode.index(chr(29))
                        self.barcode_info.batch = barcode[2:index]
                        barcode = barcode[index + 1:]
                    else:
                        self.barcode_info.batch = barcode[2:]
                        barcode = None

                elif barcode[:2] == '21':
                    if chr(29) in barcode:
                        index = barcode.index(chr(29))
                        self.barcode_info.serial = barcode[2:index]
                        barcode = barcode[index + 1:]
                    else:
                        self.barcode_info.serial = barcode[2:]
                        barcode = None

                elif barcode[:2] == '91':
                    if chr(29) in barcode:
                        index = barcode.index(chr(29))

                        self.barcode_info.nhrn = barcode[2:index]
                        barcode = barcode[index + 1:]
                    else:
                        self.barcode_info.nhrn = barcode[2:6]
                        barcode = None

                elif barcode[:2] == '93':  # Молочка, вода
                    self.barcode_info.check = barcode[2:6]
                    barcode = barcode[7:]

                elif barcode[:2] == '92':  # Далее следует код проверки, 44 символа
                    # if len(barcode[2:])==44:
                    self.barcode_info.check = barcode[2:]
                    barcode = None

                elif barcode[:4] == '8005':  # Табак, Блок
                    self.barcode_info.nhrn = barcode[5:11]
                    barcode = barcode[11:]

                elif barcode[:4] == '3103':  # Молочка с Весом
                    self.barcode_info.weight = barcode[4:]
                    barcode = None

                else:
                    self.barcode_info.error = 'INVALID BARCODE'
                    return
        else:
            self.barcode_info.error = 'No GS Separator'

        # if ('GTIN' , 'BATCH' , 'EXPIRY' , 'SERIAL') in result.keys():
        #     if gtin_check(result['GTIN']) == False and expiry_date_check(result['EXPIRY']) == False:
        #         return {'ERROR': 'INVALID GTIN & EXPIRY DATE', 'BARCODE': result}
        #     elif expiry_date_check(result['EXPIRY']) == False:
        #         return {'ERROR': 'INVALID EXPIRY DATE', 'BARCODE': result}
        #     elif gtin_check(result['GTIN']) == False:
        #         return {'ERROR': 'INVALID GTIN', 'BARCODE': result}
        #     else:
        #         return result
        # else:
        #     return {'ERROR': 'INCOMPLETE DATA', 'BARCODE': result}

    def clear_identifier(self, barcode):
        """
        Most barcode scanners prepend ']d2' identifier for the GS1 datamatrix.
        This section removes the identifier.
        """

        if barcode[:3] == self.identifier:
            barcode = barcode[3:]

        return barcode

    @dataclass
    class BarcodeInfo:
        barcode: str = ''
        scheme: str = ''
        serial: str = ''
        gtin: str = ''
        error: str = ''
        mrc: str = ''
        check: str = ''
        full_code: str = ''
        expiry: str = ''
        batch: str = ''
        nhrn: str = ''
        weight: str = ''

        def dict(self):
            return {k.upper(): str(v) for k, v in asdict(self).items() if v}


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    except Exception as e:
        ip_address = None
    finally:
        s.close()

    return ip_address
