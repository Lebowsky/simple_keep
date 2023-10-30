from typing import Optional, Callable, Union
from dataclasses import dataclass
from tiny_db_services import LoggerService

import requests
import json
from requests.auth import HTTPBasicAuth
from base64 import b64encode


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

        # Кодирование credentials для базовой аутентификации
        user_pass = f"{self.username}:{self.password}".encode("utf-8")
        encoded_credentials = b64encode(user_pass).decode("utf-8")
        self.headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'
        }

        self.http_answer: Optional[HsService.HttpAnswer] = None
        self.logger_service = LoggerService()

    def get_templates(self, **kwargs):
        self._hs = 'label_templates'
        self._method = requests.get
        answer = self._send_request(kwargs)
        if answer['status_code'] == 200:
            answer['data'] = json.loads(answer['text'])
            #return json_data
        elif answer['status_code'] == 401:
            answer['error_pool'] = answer['reason']
        else:
            answer['error_pool'] = answer.get('text')

        return answer

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

    def get_document_lines(self, id_doc: str, **kwargs) -> 'HttpAnswer':
        self._hs = 'document_lines'
        self._method = requests.get
        self.params['id_doc'] = id_doc
        answer = self._send_request(kwargs)

        if answer['status_code'] == 200:
            json_data = json.loads(answer.get('text'))
            answer['data'] = json_data

        self.http_answer = self._create_http_answer(answer)
        return self.http_answer

    def send_document_lines(self, id_doc, data, **kwargs):
        if not data:
            return {'empty': True}

        kwargs['data'] = data if isinstance(data, str) else json.dumps(data)

        self._hs = 'document_lines'
        self._method = requests.post
        self.params['id_doc'] = id_doc

        answer = self._send_request(kwargs)
        if answer['status_code'] == 200:
            json_data = json.loads(answer.get('text'))
            answer['data'] = json_data

        self.http_answer = self._create_http_answer(answer)

        return self.http_answer

    def send_all_document_lines(self, id_doc, data, **kwargs):
        if not data:
            return {'empty': True}

        kwargs['data'] = data if isinstance(data, str) else json.dumps(data)

        self._hs = 'document_lines_rewrite'
        self._method = requests.post
        self.params['id_doc'] = id_doc

        answer = self._send_request(kwargs)
        if answer['status_code'] == 200:
            json_data = json.loads(answer.get('text'))
            answer['data'] = json_data

        self.http_answer = self._create_http_answer(answer)

        return self.http_answer

    def reset_exchange(self, **kwargs):
        self._hs = 'reset_exchange'
        self._method = requests.post
        answer = self._send_request(kwargs)
        self.http_answer = self._create_http_answer(answer)
        return answer

    def create_messages(self):
        pass

    def communication_test(self, **kwargs) -> dict:
        self._hs = 'communication_test'
        self._method = requests.get
        answer = self._send_request(kwargs)
        self.http_answer = self._create_http_answer(answer)
        return answer

    def get_balances_goods(self, id_warehouse=False, id_cell=False, id_good=False, **kwargs):
        self._method = requests.get
        params = {}
        if id_good:
            params['id_good'] = id_good
        if id_cell:
            self._hs = 'good_balances/cells'
            params['id_cell'] = id_cell
        else:
            self._hs = 'good_balances/warehouses'
            if id_warehouse:
                params['id_warehouse'] = id_warehouse
        self.params = params
        answer = self._send_request(kwargs)

        if answer['status_code'] == 200:
            json_data = json.loads(answer.get('text'))
            answer['data'] = json_data

        self.http_answer = self._create_http_answer(answer)
        return self.http_answer

    def get_prices_goods(self, id_good, id_property=False, id_unit=False, id_price_type=False, **kwargs):
        self._method = requests.get
        self._hs = 'good_prices'
        params = {'id_good': id_good}
        if id_property:
            params['id_property'] = id_property
        if id_unit:
            params['id_unit'] = id_unit
        if id_price_type:
            params['id_price_type'] = id_price_type

        self.params = params
        answer = self._send_request(kwargs)

        if answer['status_code'] == 200:
            json_data = json.loads(answer.get('text'))
            answer['data'] = json_data

        self.http_answer = self._create_http_answer(answer)
        return self.http_answer

    def send_documents(self, data, **kwargs) -> dict:
        if not data:
            return {'empty': True}

        kwargs['data'] = data if isinstance(data, str) else json.dumps(data)
        self._hs = 'documents'
        self._method = requests.post

        answer = self._send_request(kwargs)
        self.http_answer = self._create_http_answer(answer)
        return answer

    def send_data(self, data, **kwargs) -> 'HttpAnswer':
        kwargs['data'] = data if isinstance(data, str) else json.dumps(data)
        self._hs = 'documents'
        self._method = requests.post

        answer = self._send_request(kwargs)
        self.http_answer = self._create_http_answer(answer)
        return self.http_answer

    def send_barcodes(self, data: list, **kwargs) -> 'HttpAnswer':
        """
        :param data: dict ('barcode', 'id_good', 'id_property', 'id_unit')
        :param kwargs: requests post params
        :return: HttpAnswer
        """
        kwargs['data'] = data if isinstance(data, str) else json.dumps(data)
        self._hs = 'barcodes'
        self._method = requests.post

        answer = self._send_request(kwargs)
        self.http_answer = self._create_http_answer(answer)
        return self.http_answer
   
    def _send_request(self, kwargs) -> dict:
        answer = {'empty': True}
        try:
            r = self._method(f'{self.url}/simple_accounting/{self._hs}?android_id={self.android_id}',
                            headers=self.headers,
                            params=self.params,
                            **kwargs)
            
            answer['status_code'] = r.status_code
            answer['url'] = r.url
            answer['reason'] = r.reason
            answer['text'] = r.text.encode("utf-8")

            try:
                answer['json'] = r.json()
            except requests.exceptions.JSONDecodeError:
                answer['json'] = {}

            if r.status_code == 200:
                answer['empty'] = False
            else:
                answer['Error'] = r.reason
                self.logger_service.write_to_log(f"Received non-200 status code {r.status_code}. Reason: {r.reason}", error_type='HTTP Error')

        except Exception as e:
            answer['Error'] = str(e)
            LoggerService().write_to_log(f"Request to {self.url} failed with error: {str(e)}", error_type='Connection Error')
            raise e  

        return answer

    def _create_http_answer(self, answer: dict):
        answer_data = {
            'status_code': answer.get('status_code'),
            'url': answer.get('url'),
            'json': answer.get('json')
        }

        if answer_data['status_code'] == 200:
            answer_data['data'] = answer.get('data')
        else:
            answer_data['error'] = True
            answer_data['error_text'] = answer.get('Error') or answer.get('error')
            if answer_data['status_code'] == 401:
                answer_data['unauthorized'] = True
            elif answer_data['status_code'] == 403:
                answer_data['forbidden'] = True

            if answer.get('text'):
                try:
                    json_result = json.loads(answer['text'])
                    error_text = json_result.get('error')
                except Exception as e:
                    error_text = answer['text'].decode()

                answer_data['error_text'] = error_text

        return self.HttpAnswer(**answer_data)

    def get_method_by_path(self, path) -> Union[Callable, None]:
        methods = {
            'barcodes': self.send_barcodes,
            'documents': self.send_documents
        }

        return methods.get(path)

    def write_error_to_log(self, error_text, **kwargs):
        self.logger_service.write_to_log(error_text=error_text,
                                         error_type="HS_service",
                                         **kwargs)

    @dataclass
    class HttpAnswer:
        url: str
        status_code: int
        json: Optional = None
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
        return self._send_request({'files': {'SimpleKeep.db': file}})

    def export_file(self, file_name, file):
        self._hs = 'post'
        return self._send_request({'files': {file_name: file}})

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
