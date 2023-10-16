import json
from typing import Union

from ui_global import get_query_result, bulk_query


class SimpleUtilites:
    def urovo_set_lock_trigger(self, bol: bool):
        pass

    def urovo_open_scanner(self):
        pass

    def urovo_start_decode(self):
        pass

    def urovo_stop_decode(self):
        pass

    @staticmethod
    def get_temp_dir():
        return './'

    @staticmethod
    def get_temp_file(extension: str) -> str:
        """Генерирует файл с указанным расширением и возвращает путь к файлу."""
        pass

    @staticmethod
    def deleteCache():
        pass

    @staticmethod
    def write_socket(
            ip: str,
            port: int,
            data: Union[str, bytes],
            handlers: str
    ) -> bool:
        """Отправка данных на принтер WiFi. Возвращает True при успешной отправке.
        ip - IP-адрес принтера
        port - порт принтера.
        data: строка(UTF-8) или байт-массив данных.
        handlers - строка-массив обработчиков в случае неудачи
         """
        pass


class ImportUtils:
    def __init__(self):
        self.views = {'btn_barcodes': self.get_btn_barcodes}

    def getView(self, view):
        return self.views[view]()

    def get_btn_barcodes(self):
        return BtnBarcodes()


class BtnBarcodes:
    def setBackground(self, background):
        self.background = background

    def setElevation(self, elevation):
        self.elevation = elevation


class SimpleSQLProvider:
    def __init__(self):
        self.sql_text = ''
        self.sql_params = None

    def SQLExec(self, q, params):
        self.sql_text = q
        self.sql_params = params

        if params:
            return json.dumps(get_query_result(q, tuple(params.split(','))))
        else:
            return json.dumps(get_query_result(q))

    def SQLExecMany(self, q, params):
        self.sql_text = q
        self.sql_params = params

        bulk_query(q, json.loads(params))

    def SQLQuery(self, q, params):
        self.sql_text = q
        self.sql_params = params

        if params:
            return json.dumps(get_query_result(q, tuple(params.split(',')), return_dict=True))
        else:
            return json.dumps(get_query_result(q, return_dict=True))


class SimpleBluetooth:
    def __init__(self):
        pass

    def get_device(self, mac: str):
        """Получение устройства по mac адресу.
         Возвращает android.bluetooth.BluetoothDevice."""
        pass

    def write_data(self, data: Union[str, int, bytes], handlers: str):
        """Отправка данных.
        data – данные в виде строки, целого числа или массива байтов.
        handlers – строка с обработчиками в случае неудачи."""
        pass

    def connect_to_client(self, device, handlers: str) -> bool:
        """Подключение к устройству.
         device - android.bluetooth.BluetoothDevice.
         handlers - строка с обработчиками в случае неудачи."""
        pass

    def close_socket(self):
        """Отключение от устройства."""
        pass

    def begin_listen_for_data(self, handlers: str):
        """Подключает массив обработчиков на события устройства.
         Обработчики должны быть обязательно pythonbytes."""
        pass

    def stop_listen(self):
        """Отключение подписки на события устройства."""
        pass

