import json
from typing import Callable
from functools import wraps

from java import jclass
from ui_global import Rs_doc, find_barcode_in_barcode_table
from db_services import DocService

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

    def toast(self, text, add_to_log=False):
        self.hash_map.put('toast', str(text))
        if add_to_log:
            self.error_log(text)

    def notification(self, text, title=None, add_to_log=False):
        notification_id = rs_settings.get("notification_id") + 1 if rs_settings.get("notification_id") else 1
        if title is None:
            title = self.get_current_screen()
        self.hash_map.put("basic_notification", json.dumps([{'number': notification_id,
                                                             'title': title, 'message': text}]))
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

    def run_event_async(self, method_name):
        self['RunEvent'] = json.dumps(self._get_event(method_name, True))

    def _get_event(self, method_name, async_action=False):
        evt = [{
            'action': 'runasync' if async_action else 'run',
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

    def put(self, key, value, to_json=False):
        if to_json:
            self.hash_map.put(key, json.dumps(value))
        else:
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
        return self['current_screen_name']

    def get_current_process(self):
        return self['current_process_name']

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


def format_doc_date(date_string):
    new_date_string = date_string[8:10] + "." + date_string[5:7] + "." + date_string[0:4] + " " + \
                      date_string[11:13] + ":" + date_string[14:16] + ":" + date_string[17:19]
    return new_date_string