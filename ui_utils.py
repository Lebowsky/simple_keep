import json
from typing import Callable
from functools import wraps

from java import jclass

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

    def show_dialog(self, listener, title='', buttons=None):
        self.put("ShowDialog", listener)

        if title:
            dialog_style = {
                'title': title or listener,
                'yes': 'Ок',
                'no': 'Отмена'
            }
            if buttons and len(buttons) > 1:
                dialog_style['yes'] = buttons[0]
                dialog_style['no'] = buttons[1]

            self.put('ShowDialogStyle', dialog_style)



def parse_barcode(val):
    if len(val) < 21:
        return {'GTIN': '', 'Series': ''}

    val.replace('(01)','01')
    val.replace('(21)', '21')

    if val[:2] == '01':
        GTIN = val[2:16]
        Series = val[18:]
    else:
        GTIN = val[:14]
        Series = val[14:]

    return {'GTIN': GTIN, 'Series': Series}
