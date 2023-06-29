import requests
import json
from dataclasses import dataclass, fields
from requests.auth import HTTPBasicAuth
from typing import Optional


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
        self.http_answer: Optional[HsService.HttpAnswer] = None

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
                    answer['data'] = json_data['data']
            else:
                answer['format'] = None
        elif answer['status_code'] == 401:
            print(answer)
            answer['error_pool'] = answer['reason']
        else:
            answer['error_pool'] = answer.get('text')

        self.http_answer = self._create_http_answer(answer)
        return answer

    def reset_exchange(self, **kwargs):
        self._hs = 'reset_exchange'
        self._method = requests.post
        answer = self._send_request(kwargs)
        return answer

    def create_messages(self):
        pass

    def communication_test(self, **kwargs) -> dict:
        self._hs = 'communication_test'
        self._method = requests.get
        answer = self._send_request(kwargs)
        self.http_answer = self._create_http_answer(answer)
        return answer

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

        answer = self._send_request(kwargs)
        self.http_answer = self._create_http_answer(answer)
        return answer

    def _send_request(self, kwargs) -> dict:
        answer = {'empty': True}
        try:
            r = self._method(f'{self.url}/simple_accounting/{self._hs}?android_id={self.android_id}',
                             auth=self.auth,
                             headers=self.headers,
                             params=self.params,
                             **kwargs)

            answer['status_code'] = r.status_code
            answer['url'] = r.url
            answer['reason'] = r.reason
            answer['text'] = r.text.encode("utf-8")

            if r.status_code == 200:
                answer['empty'] = False
            else:
                answer['Error'] = r.reason
                answer['reason'] = r.reason
        except Exception as e:
            raise e
            # answer['Error'] = e.args[0]

        return answer

    def _create_http_answer(self, answer: dict):
        answer_data = {
            'status_code': answer.get('status_code'),
            'url': answer.get('url'),
        }

        if answer_data['status_code'] == 200:
            answer_data['data'] = answer.get('data')
        else:
            answer_data['error_text'] = answer.get('Error') or answer.get('error')
            if answer_data['status_code'] == 401:
                answer_data['unauthorized'] = True
            elif answer_data['status_code'] == 403:
                error_text = ''
                if answer.get('text'):
                    try:
                        json_result = json.loads(answer['text'])
                        error_text = json_result.get('error')
                    except Exception as e:
                        error_text = answer['text'].decode()

                answer_data['error_text'] = error_text
                answer_data['forbidden'] = True

        return self.HttpAnswer(**answer_data)

    @dataclass
    class HttpAnswer:
        url: str
        status_code: int
        error_text: Optional[str] = ''
        data: Optional = None
        unauthorized: bool = False
        forbidden: bool = False
        error: bool = False


class DebugService:
    def __init__(self, ip_host, port=2444):
        self.ip_host = ip_host
        self.port = port
        self.url = f'http://{self.ip_host}:{self.port}'
        self._hs = ''
        self._method = requests.post

    def export_database(self, file):
        self._hs = 'post'
        return self._send_request({'files': {'Rightscan': file}})

    def export_log(self, data):
        self._hs = 'unload_log'
        return self._send_request({'json': json.dumps(data)})

    def _send_request(self, kwargs) -> dict:
        answer = {'empty': True}
        try:
            r = self._method(f'{self.url}/{self._hs}', **kwargs)

            answer['status_code'] = r.status_code
            if r.status_code == 200:
                answer['empty'] = False
                answer['text'] = r.text.encode("utf-8")
                answer['reason'] = r.reason
            else:
                answer['Error'] = r.text
        except Exception as e:
            raise e

        return answer
