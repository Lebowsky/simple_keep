import json
import re
import socket
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, Union, List, Dict, Literal, Optional, Tuple
from java import jclass


noClass = jclass("ru.travelfood.simple_ui.NoSQL")
rs_settings = noClass("rs_settings")


class HashMap:
    """
        Класс-декоратор для удобной работы с hashMap. Также можно добавить дополнительную логику.
    """

    def __init__(self, hash_map=None, debug: bool = False):
        self.listener = None
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

    @property
    def listener(self):
        return self['listener']

    @listener.setter
    def listener(self, v):
        pass

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

    def put_data(self, data: dict, fill_none=False, default=''):
        if data:
            for key, value in data.items():
                if value is None and fill_none:
                    value = default

                self[key] = value

    def containsKey(self, key):
        return self.hash_map.containsKey(key)

    def key_set(self) -> str:
        return self.hash_map.keySet()

    def keys(self) -> List[str]:
        keys = str(self.key_set())
        return keys[1:len(keys)-1].split(', ')

    def items(self) -> List[Tuple[str, Optional[str]]]:
        return [(key, self[key]) for key in self.keys()]

    def show_items(
            self,
            only: Optional[List[str]] = None,
            exclude: Optional[List[str]] = None,
            is_value_exists: bool = False,
    ) -> None:
        text = 'Список элементов HashMap: \n'
        if is_value_exists:
            text += 'True если есть любое значение \n'
        hashmap_keys = self.keys()
        items = self.items()
        if only:
            items = [item for item in items if item[0] in only]
            for key in only:
                if key not in hashmap_keys:
                    items.append((key, 'Нет ключа'))
        if exclude:
            items = [item for item in items if item[0] not in exclude]

        for key, value in items:
            value = value if not is_value_exists else value is not None
            text += f'{key}: {value}\n'
        self.toast(text)


    def remove(self, key):
        self.hash_map.remove(key)

    def delete(self, key):
        self.hash_map.remove(key)

    def add_to_cv_list(
            self,
            element: Union[str, dict],
            cv_list: Literal['green_list', 'yellow_list', 'red_list', 'gray_list',
                             'blue_list', 'hidden_list', 'object_info_list',
                             'stop_listener_list', 'object_caption_list',
                             'object_detector_mode'],
            _dict: bool = False
    ) -> None:
        """ Добавляет в cv-список элемент, или создает новый список с этим элементом.
            object_info_list - Информация об объекте (снизу). [{'object': object_id: str, 'info': value}]
            object_detector_mode - Режим детектора. [{'object_id': object_id: int, 'mode': barcode|ocr|stop}]
            object_caption_list - Информация об объекте (сверху). [{'object': object_id: str, 'caption': value}]
            stop_listener_list - Блокирует выполние обработчиков для объектов в списке
        """

        if _dict:
            lst = self.get(cv_list, from_json=True) or []
            if element not in lst:
                lst.append(element)
                self.put(cv_list, json.dumps(lst, ensure_ascii=False))

        else:
            lst = self.get(cv_list)
            lst = lst.split(';') if lst else []
            if element not in lst:
                lst.append(element)
                self.put(cv_list, ';'.join(lst))

    def remove_from_cv_list(
        self,
        element: Union[str, dict],
        cv_list: Literal['green_list', 'yellow_list', 'red_list', 'gray_list',
                         'blue_list', 'hidden_list', 'object_info_list',
                         'stop_listener_list', 'object_caption_list',
                         'object_detector_mode'],
        _dict: bool = False
    ):
        """Удаляет из cv-списка"""
        if _dict:
            lst = self.get(cv_list, from_json=True) or []
            try:
                lst.remove(element)
                self.put(cv_list, json.dumps(lst, ensure_ascii=False))
            except ValueError:
                pass
        else:
            lst = self.get(cv_list)
            lst = lst.split(';') if lst else []
            if element in lst:
                lst.remove(element)
                self.put(cv_list, ';'.join(lst))

    def set_vision_settings(
            self,
            values_list: str,
            type_rec: str = 'Text',
            NumberRecognition: bool = False,
            DateRecognition: bool = False,
            PlateNumberRecognition: bool = False,
            min_length: int = 1,
            max_length: int = 20,
            result_var: str = 'ocr_result',
            mesure_qty: int = 1,
            min_freq: int = 1,
            query: str = '',
            control_field: str = '',
            cursor: Optional[list] = None,
            count_objects: int = 0,
            ReplaceO: bool = False,
            ToUpcase: bool = False,
    ):
        """query - SQL запрос для варианта поиска по SQL-таблице с одинм параметром(в который передается распознанный текст )
                Например: select * from SW_Goods where product_number like  ?
           control_field - поле таблицы по которому проверяется OCR , условно Артикул (несмотря на то, что в query оно скорее всего также участвует)
           cursor - Массив  с объектами {"field":<поле таблицы>,"var":<переменная результат>}
           values_list - Режим поиска по списку, либо обработчиком ("~")
           mesure_qty - Количество измерений плотности вероятности (норм. распределение)
           min_freq - Вероятность (в процентах от 0 до 100 для удобства ввода)
           min_length - Минимальная длина текста
           max_length - Максимальная длина текста
           count_objects - Для NumberRecognition количество циклов измерений для решения комбинаторной задачи. Чем больше циклов тем больше точность
           ReplaceO - Заменить буквы О на 0 (нули)
           ToUpcase - Преобразование в верхний регистр
           PlateNumberRecognition - Российские номера (только для ActiveCV)
           NumberRecognition - Распознавание чисел
           DateRecognition - Распознавние дат
           result_field  для распознвания дат и номеров, туда помещается результаты особым образом (смотря что ищем)"""
        if cursor is None:
            cursor = []
        settings = {
            "TypeRecognition": type_rec,
            "NumberRecognition": NumberRecognition,
            "DateRecognition": DateRecognition,
            "PlateNumberRecognition": PlateNumberRecognition,
            "min_length": min_length,
            "max_length": max_length,
            "values_list": values_list,
            "result_var": result_var,
            "mesure_qty": mesure_qty,
            "min_freq": min_freq,
            "query": query,
            "control_field": control_field,
            "cursor": cursor,
            "count_objects": count_objects,
            "ReplaceO": ReplaceO,
            "ToUpcase": ToUpcase
        }
        self.hash_map.put("SetVisionSettings", json.dumps(settings))

    def show_screen(self, name, data=None):
        self.put('ShowScreen', name)
        if data:
            self.put_data(data)

    def show_process_result(self, process, screen, data: dict = None):
        if process and screen:
            self.hash_map.put('ShowProcessResult', f'{process}|{screen}')

            if data:
                self.put_data(data)

    def switch_process_screen(self, process: str, screen: Optional[str] = None):
        process_screen = f'{process}|{screen}' if screen else process
        self.hash_map.put('SwitchProcessScreen', process_screen)

    def show_dialog(self, listener, title='', buttons=None, dialog_layout=None):
        self.put("ShowDialog", listener)
        
        if dialog_layout:
            self.put('ShowDialogLayout', dialog_layout)

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

    def get_parent_screen(self):
        return self['parent_screen'] if self.containsKey('parent_screen') else ''

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

    def back_screen(self):
        self['BackScreen'] = ''

    def no_refresh(self):
        self['NoRefresh'] = ''


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
                    self.barcode_info.nhrn = barcode[4:10]
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


class DateFormat:

    @staticmethod
    def get_now_nosql_format() -> str:
        utc_date = datetime.utcnow()
        return utc_date.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def get_table_view_format(date: str, user_tmz_offset=None) -> str:
        user_tmz_offset = user_tmz_offset or rs_settings.get('user_tmz_offset')
        timezone_offset = timedelta(hours=int(user_tmz_offset))
        dt_date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        return str(dt_date + timezone_offset)


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
