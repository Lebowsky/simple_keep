import requests
import json
from requests.auth import HTTPBasicAuth

import ui_utils


class HsService:
    def __init__(self, http_params):
        self.url = http_params['url']
        self.username = http_params['user']
        self.password = http_params['pass']
        self.android_id = http_params['android_id']
        self.device_model = http_params['device_model']
        self.user_name = http_params['user_name']
        self.params = {'user_name': self.user_name, 'device_model': self.device_model}
        self._hs = ''
        self._method = requests.get

        self.auth = HTTPBasicAuth(self.username, self.password)
        self.headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}

    def get_data(self, **kwargs) -> dict:
        self._hs = 'data'
        self._method = requests.get
        answer = self._send_request(kwargs)

        if answer['status_code'] == 200:
            json_data = json.loads(answer['text'])
            format_data = json_data.get('format')

            if format_data:
                answer['format'] = format_data
                if 'is_ok' == format_data and json_data.get('batch'):
                    # Наш запрос принят, но вернуть пока нечего. Данные или готовятся или их нет
                    answer['batch'] = json_data.get('batch')

                elif format_data == 'is_data':
                    # Парсим, параметр data содержит список словарей с данными запроса
                    res_for_sql = ui_utils.json_to_sqlite_query(json_data['data'])
                    if res_for_sql:
                        answer['res_for_sql'] = res_for_sql
            else:
                answer['format'] = None
        elif answer['status_code'] == 401:
            answer['error_pool'] = answer['reason']
        else:
            answer['error_pool'] = answer['text']

        return answer

    def reset_exchange(self):
        pass

    def create_messages(self):
        pass

    def communication_test(self, **kwargs) -> dict:
        self._hs = 'communication_test'
        self._method = requests.get
        return self._send_request(kwargs)

    def get_balances_goods(self, warehouses=False, cells=False):
        pass

    def get_prices_goods(self):
        pass

    def send_documents(self, data, **kwargs) -> dict:
        if not data:
            return {'empty': True}

        kwargs['data'] = data if isinstance(data, str) else json.dumps(data)
        self._hs = 'documents'
        self._method = requests.post

        return self._send_request(kwargs)

    def _send_request(self, kwargs) -> dict:
        answer = {'empty': True}
        try:
            r = self._method(f'{self.url}/simple_accounting/{self._hs}?android_id={self.android_id}',
                             auth=self.auth,
                             headers=self.headers,
                             params=self.params,
                             **kwargs)

            answer['status_code'] = r.status_code
            if r.status_code == 200:
                answer['empty'] = False
                answer['text'] = r.text.encode("utf-8")
                answer['reason'] =  r.reason
            else:
                answer['Error'] = r.text
        except Exception as e:
            answer['Error'] = e.args[0]

        return answer
