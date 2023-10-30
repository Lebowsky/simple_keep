import base64
import json
import os
import re
import shutil
from datetime import datetime
from typing import List, Tuple, Dict
from db_services import DocService, GoodsService, FlowDocService
from hs_services import HsService
from ru.travelfood.simple_ui import SimpleUtilites as suClass
from printing_factory import HTMLDocument, PrintService, ZPLConstructor, bt
from tiny_db_services import NoSQLProvider
from ui_models import Screen, SelectItemScreen
import widgets
from ui_utils import HashMap, create_file, resize_image
from java import jclass
noClass = jclass("ru.travelfood.simple_ui.NoSQL")
ocr_nosql = NoSQLProvider("ocr_nosql")
ocr_nosql_counter = NoSQLProvider("ocr_nosql_counter")
articles_ocr_ncl = NoSQLProvider('articles_ocr_ncl')
print_nosql = NoSQLProvider("print_nosql")

# ==================== Printing screens =============================


class PrintScreenMixin(Screen):
    def __init__(self, hash_map: HashMap):
        super().__init__(hash_map)
        self.hash_map = hash_map
        self.title = ''
        self.print_nosql = print_nosql

    def on_start(self):
        self.hash_map.set_title(self.title)
        self._set_screen_values()

    def _on_input(self, listeners):
        if self.listener in listeners:
            listeners[self.listener]()
        else:
            super().on_input()

    def _set_screen_values(self):
        for value_name, value in self.screen_values.items():
            hash_map_value = self.hash_map.get(value_name)
            if hash_map_value:
                new_value = hash_map_value
                if self._is_float(new_value):
                    new_value = str(int(float(new_value)))
            else:
                nosql_key = self.__class__.__name__ + '_ScreenValues'
                nosql = self.print_nosql.get(nosql_key, from_json=True)
                new_value = nosql[value_name] if nosql and value_name in nosql else value
            self.hash_map.put(value_name, new_value)

    def _save_screen_values(self):
        screen_values = {name: self.hash_map.get(name) or value
                         for name, value in self.screen_values.items()}
        nosql_key = self.__class__.__name__ + '_ScreenValues'
        self.print_nosql.put(nosql_key, screen_values, to_json=True)

    def _set_default_screen_values(self):
        for value_name, value in self.screen_values.items():
            self.hash_map[value_name] = value

    def _delete_screen_values(self, with_nosql: bool = False):
        for value_name, value in self.screen_values.items():
            self.hash_map.delete(value_name)
        if with_nosql:
            self.print_nosql.delete(self.__class__.__name__ + '_ScreenValues')

    def _is_float(self, value: str):
        return '.' in value and value.replace('.', '', 1).isdecimal()

    def _get_dialog_layout(self, input_type: str, value: str, variable: str):
        input_types = {
            'text': "EditTextText",
            'numeric': "EditTextNumeric",
            'spinner': 'SpinnerLayout'
        }
        layout = {
            "type": "LinearLayout",
            "Variable": "",
            "orientation": "horizontal",
            "height": "wrap_content",
            "width": "match_parent",
            "weight": "0",
            "Elements": [
                {
                    "Value": value,
                    "Variable": variable,
                    "height": "wrap_content",
                    "width": "match_parent",
                    "weight": "0",
                    "type":  input_types[input_type]
                }
            ]
        }
        return layout

    class TextView(widgets.TextView):
        def __init__(self, value):
            super().__init__()
            self.TextSize = '15'
            self.TextBold = True
            self.width = 'match_parent'
            self.Value = value

    class LinearLayout(widgets.LinearLayout):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.orientation = 'horizontal'
            self.height = "match_parent"
            self.width = "match_parent"
            self.StrokeWidth = 1


class PrintSettings(PrintScreenMixin):
    screen_name = 'PrintSettings'
    process_name = 'Print'

    def __init__(self, hash_map: HashMap):
        super().__init__(hash_map)
        self.title = 'Настройки печати'
        self.screen_values = {
            'check_box_bluetooth_print': 'false',
            'check_box_wifi_print': 'false',
            'check_box_template_1c': 'false',
            'check_box_template_zpl': 'false',
        }

    def on_start(self):
        super().on_start()

    def on_input(self):
        listeners = {
            'btn_bluetooth_printer_settings': self._bluetooth_printer_settings,
            'btn_wifi_printer_settings': self._wifi_printer_settings,
            'btn_label_templates_1c': self._label_templates_settings_1c,
            'btn_label_templates_zpl': self._label_templates_settings_zpl,
            'check_box_bluetooth_print': self._manage_check_box_input,
            'check_box_wifi_print': self._manage_check_box_input,
            'check_box_template_1c': self._manage_check_box_input,
            'check_box_template_zpl': self._manage_check_box_input,
            'ON_BACK_PRESSED': self._on_back_pressed,
        }
        self._on_input(listeners)

    def _bluetooth_printer_settings(self):
        self._delete_screen_values()
        self.hash_map.show_screen('PrintBluetooth')

    def _wifi_printer_settings(self):
        self._delete_screen_values()
        self.hash_map.show_screen('PrintWiFi')

    def _label_templates_settings_1c(self):
        self._delete_screen_values()
        self.hash_map.show_screen('PrintTemplates1C')

    def _label_templates_settings_zpl(self):
        self._delete_screen_values()
        self.hash_map.show_screen('PrintTemplatesZPL')

    def _manage_check_box_input(self):
        listener = self.listener
        if listener == 'check_box_bluetooth_print':
            check_box_bluetooth = self.hash_map.get('check_box_bluetooth_print')
            if check_box_bluetooth == 'false':
                self.print_nosql.delete('print_through')
            elif check_box_bluetooth == 'true':
                self.hash_map.put('check_box_wifi_print', 'false')
                self.print_nosql.put('print_through', 'BT')

        elif listener == 'check_box_wifi_print':
            check_box_wifi = self.hash_map.get('check_box_wifi_print')
            if check_box_wifi == 'false':
                self.print_nosql.delete('print_through')
            elif check_box_wifi == 'true':
                self.hash_map.put('check_box_bluetooth_print', 'false')
                self.print_nosql.put('print_through', 'WiFi')

        elif listener == 'check_box_template_1c':
            check_box_template_1c = self.hash_map.get('check_box_template_1c')
            if check_box_template_1c == 'false':
                self.print_nosql.delete('print_template_type')
            elif check_box_template_1c == 'true':
                self.hash_map.put('check_box_template_zpl', 'false')
                self.print_nosql.put('print_template_type', '1C')

        elif listener == 'check_box_template_zpl':
            check_box_template_zpl = self.hash_map.get('check_box_template_zpl')
            if check_box_template_zpl == 'false':
                self.print_nosql.delete('print_template_type')
            elif check_box_template_zpl == 'true':
                self.hash_map.put('check_box_template_1c', 'false')
                self.print_nosql.put('print_template_type', 'ZPL')

        through = self.print_nosql.get('print_through') or 'Не указано'
        template_type = self.print_nosql.get('print_template_type') or 'Не указано'
        self.hash_map.toast(f'Печать через: {through}. Шаблон печати: {template_type}')
        self._save_screen_values()

    def _on_back_pressed(self):
        self.hash_map.switch_process_screen('Параметры')


class PrintBluetooth(PrintScreenMixin):
    screen_name = 'PrintBluetooth'
    process_name = 'Print'

    def __init__(self, hash_map: HashMap):
        super().__init__(hash_map)
        self.title = 'Настройка Bluetooth'
        self.screen_values = {
            "default_printer": 'Не выбран'
        }

    def on_start(self):
        super().on_start()

    def on_input(self):
        listeners = {
            'btn_show_connected': self._show_connected,
            'btn_start_scan': self._start_scan,
            'btn_stop_scan': self._stop_scan,
            'btn_test_print': self._test_print,
            'CardsClick': self._cards_click,
            'btn_bt_disconnect': self._bt_disconnect,
            'ON_BACK_PRESSED': self._on_back_pressed,
        }
        self._on_input(listeners)

    def _show_connected(self):
        devices = self.hash_map.get("BTResult")
        devices = json.loads(devices) if devices else []
        bt_devices_cards = {"cards": []}

        for device in devices:
            card = {"key": device.get("address"),
                    "items": [
                        {
                            "key": "Устройство",
                            "value": device.get("name"),
                            "size": "15",
                            "color": "#1b31c2",
                            "caption_size": "12",
                            "caption_color": "#1b31c2"
                        },
                        {
                            "key": "MAC",
                            "value": device.get("address"),
                            "size": "15",
                            "color": "#131e61",
                            "caption_size": "12",
                            "caption_color": "#1b31c2"
                        },
                        {
                            "key": "state",
                            "value": device.get("state"),
                            "size": "15",
                            "color": "#131e61",
                            "caption_size": "12",
                            "caption_color": "#1b31c2"
                        }
                    ]}

            bt_devices_cards["cards"].append(card)

        self.hash_map.put("bluetooth_devices_cards", json.dumps(bt_devices_cards))

    def _start_scan(self):
        bt_discover_handlers = [
            {
                "action": "run",
                "type": "set",
                "method": "beep;toast=@BTDiscoverResult",
                "postExecute": "",
            }
        ]
        self.hash_map.put("BTStartScan")
        self.hash_map.put("BTDiscoverHandlers", json.dumps(bt_discover_handlers))
        self.hash_map.put("scanning")
        self.hash_map.toast('Сканирование')

    def _stop_scan(self):
        if self.hash_map.containsKey("scanning"):
            self.hash_map.put('BTStopScan')
            self.hash_map.delete("scanning")
            self.hash_map.toast('Сканирование остановлено')

    def _test_print(self):
        if not self.print_nosql.get('default_printer'):
            self.hash_map.toast('Нет подключенных принтеров')
            return
        zpl = '^XA^CFA,30^FO10,50^FDTest^FS^BY3,2,120^FO10,150^BC^FD12345678^FS^XZ'
        sent, result = PrintService(self.hash_map).print_bt(zpl)
        self.hash_map.toast(result)

    def _bt_disconnect(self):
        if not self.print_nosql.get('default_printer'):
            self.hash_map.toast('Нет подключенных принтеров')
            return
        try:
            self.hash_map.delete('default_printer')
            self.print_nosql.delete('default_printer')
            self.hash_map.toast('Принтер отключен')
            self._save_screen_values()
            bt.close_socket()
        except Exception as e:
            pass

    def _cards_click(self):
        if self.print_nosql.get("default_printer"):
            self._bt_disconnect()
            return
        bt_handlers = [{"action": "run", "type": "python", "method": "bluetooth_error"}]

        mac = self.hash_map.get("selected_card_key")
        device = bt.get_device(mac)
        if device is None:
            self.hash_map.toast("Не получилось подключиться к устройству")
            return
        connected = bt.connect_to_client(device, json.dumps(bt_handlers))
        if not connected:
            self.hash_map.toast("Устройство не является принтером")
            return
        self.print_nosql.put("default_printer", mac)
        self.hash_map.put("default_printer", mac)
        self._save_screen_values()
        self.hash_map.beep()
        self.hash_map.toast('Успешно')

    def _on_back_pressed(self):
        self._delete_screen_values()
        self.hash_map.show_screen('PrintSettings')


class PrintWiFi(PrintScreenMixin):
    screen_name = 'PrintWiFi'
    process_name = 'Print'

    def __init__(self, hash_map: HashMap):
        super().__init__(hash_map)
        self.print_nosql = NoSQLProvider("print_nosql")
        self.title = 'Настройка WiFi'
        self.screen_values = {
            'wi_fi_ip': '',
            'info_wifi_current_ip': '',
        }

    def on_start(self):
        super().on_start()

    def on_input(self):
        listeners = {
            'btn_wifi_save_ip': self._wi_fi_save_ip,
            'btn_wifi_delete_ip': self._wi_fi_delete_ip,
            'btn_test_wi_fi': self._wi_fi_test_print,
            'ON_BACK_PRESSED': self._on_back_pressed,
        }
        self._on_input(listeners)

    def _wi_fi_save_ip(self):
        ip = self.hash_map.get('wi_fi_ip')
        if not PrintService.valide_ip(ip):
            self.hash_map.toast('Неверный формат IP')
            return
        self.hash_map.put('info_wifi_current_ip', ip)
        self._save_screen_values()
        self.print_nosql.put('current_wi_fi_printer_ip', ip)
        self.hash_map.beep()
        self.hash_map.toast('IP принтера записан')

    def _wi_fi_delete_ip(self):
        self._delete_screen_values(with_nosql=True)
        self.print_nosql.delete('current_wi_fi_printer_ip')
        self.hash_map.toast('IP принтера удалён')

    def _wi_fi_test_print(self):
        ip = self.print_nosql.get('current_wi_fi_printer_ip')
        if not ip:
            self.hash_map.toast('Не указан ip')
            return
        zpl = '^XA^CFA,30^FO10,50^FDTest^FS^BY3,2,120^FO10,150^BC^FD12345678^FS^XZ'
        self.print_nosql.put('wifi_data_to_print', zpl)
        self.hash_map.run_event_async('print_wifi')
        self.hash_map.toast('Тест ZPL')

    def _on_back_pressed(self):
        self._delete_screen_values()
        self.hash_map.show_screen('PrintSettings')


class PrintTemplates1C(PrintScreenMixin):
    screen_name = 'PrintTemplates1C'
    process_name = 'Print'

    def __init__(self, hash_map: HashMap):
        super().__init__(hash_map)
        self.hs_service = HsService(self.get_http_settings())
        self.title = 'Настройка шаблона 1C'
        self.screen_values = {
            'current_1c_template_name': 'Нет',
            'preview_template_image': ''
        }

    def on_start(self):
        super().on_start()
        self._refresh_preview()

    def on_input(self):
        listeners = {
            'btn_get_labels': self._get_labels,
            'btn_select_label_template': self._select_label_template,
            'btn_delete_template_settings': self._delete_template_settings,
            'btn_label_template_size_settings': self._label_template_size_settings,
            'btn_zpl_template_redirect': self._zpl_template_redirect,
            'ON_BACK_PRESSED': self._on_back_pressed,
        }
        self._on_input(listeners)

    def _refresh_preview(self):
        path_to_preview_image = self.print_nosql.get('preview_template_image')
        if not path_to_preview_image or not os.path.isfile(path_to_preview_image):
            self.print_nosql.delete('preview_template_image')
            return
        temp_preview = self.print_nosql.get('preview_template_image_temp')
        path = temp_preview if temp_preview else path_to_preview_image
        self.hash_map.put('preview_template_image', '~' + path)

    def _get_labels(self):
        try:
            answer = self.hs_service.get_templates()
            if answer['status_code'] != 200:
                reason = answer['error_pool']
                raise Exception(f'Ошибка соединения с сервером: {reason}')

            output_folder = os.path.join(suClass.get_temp_dir(), 'labels')

            os.makedirs(output_folder, exist_ok=True)

            data_list = answer['data']
            self.hash_map.toast(f'data_list:{type(data_list)}, {data_list}')

            for data_dict in data_list:
                file_name = self._correct_filename(data_dict['name']) + '.htm'
                file_path = os.path.join(output_folder, file_name)

                try:
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(base64.b64decode(data_dict['html']).decode('utf-8'))
                except Exception as e:
                    self.hash_map.toast(f'Ошибка сохранения файла {file_path}: {str(e)}')
                    raise Exception(f'Ошибка сохранения файла {file_path}: {str(e)}')
            self.print_nosql.put('label_templates_dir', output_folder, True)
            self.hash_map.toast('Шаблоны загружены')
        except Exception as e:
            self.hash_map.toast(str(e))

    def _correct_filename(self, filename):
        illegal_chars = ['<', '>', ':', '"',"'", '/', '\\', '|', '?', '*', "<", ">", '\x00']
        for char in illegal_chars:
            filename = filename.replace(char, '')
        return filename

    def _select_label_template(self):
        self._delete_screen_values()
        self.hash_map.show_screen('TemplatesList')

    def _delete_template_settings(self):
        self.print_nosql.delete('barcode_width')
        self.print_nosql.delete('barcode_height')
        self.print_nosql.delete('matching_table')
        self.print_nosql.delete('barcode_type')
        self.print_nosql.delete('current_1c_template_name')
        self.print_nosql.delete('current_1c_template_path')
        self.print_nosql.delete('preview_template_image_temp', with_file=True)
        self.print_nosql.delete('preview_template_image', with_file=True)
        self.hash_map.delete('preview_template_image_temp')
        self.hash_map.delete('preview_template_image')
        self.hash_map.delete('current_1c_template_name')

    def _label_template_size_settings(self):
        if not self.print_nosql.get('current_1c_template_path'):
            self.hash_map.toast('Сначала нужно выбрать шаблон')
            return
        self._delete_screen_values()
        self.hash_map.show_screen('PrintTemplates1CSizes')

    def _zpl_template_redirect(self):
        self.hash_map.show_screen('PrintTemplatesZPL')

    def _on_back_pressed(self):
        self._delete_screen_values()
        self.hash_map.show_screen('PrintSettings')


class TemplatesList(PrintScreenMixin):
    screen_name = 'TemplatesList'
    process_name = 'Print'

    def __init__(self, hash_map: HashMap):
        super().__init__(hash_map)

    def on_start(self):
        self._show_templates_cards()

    def on_input(self):
        listeners = {
            'CardsClick': self._cards_click,
            'ON_BACK_PRESSED': self._on_back_pressed,
        }
        self._on_input(listeners)

    def _show_templates_cards(self):
        list_data = self.get_all_files_from_patch()
        doc_cards = self._get_doc_cards_view(list_data)
        self.hash_map.put('templates_cards', doc_cards.to_json())
        self.hash_map.put('return_selected_data')

    def _cards_click(self):
        selected_card_data = self.hash_map.get('selected_card_data', from_json=True)
        self.print_nosql.put('lable_full_path', selected_card_data.get('full_path'))

        self.hash_map.delete('selected_card_data')
        self.hash_map.delete('return_selected_data')
        self.hash_map.delete('templates_cards')
        self.hash_map.show_screen('PrintTemplates1CParameters')

    def _get_doc_cards_view(self, table_data):
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')
        card_date_text_size = self.rs_settings.get('CardDateTextSize')

        doc_cards = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@file_name',
                        TextBold=True,
                        TextSize=card_title_text_size
                    ),
                    orientation="horizontal"
                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@file_size',
                        TextSize=card_date_text_size
                    ),
                    widgets.TextView(
                        Value='@creation_time',
                        TextSize=card_date_text_size
                    )
                ),
                width="match_parent"
            ),
            options=widgets.Options().options,
            cardsdata=table_data
        )

        return doc_cards

    def get_all_files_from_patch(self):
        templates_dir = self.print_nosql.get('label_templates_dir')
        folder_path = templates_dir or os.path.join(suClass.get_temp_dir(), 'labels')

        html_files_info = []

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.htm'):  # and mask in file:
                    file_path = os.path.join(root, file)
                    file_size_bytes = os.path.getsize(file_path)
                    file_size_kb = file_size_bytes / 1024  # Convert bytes to kilobytes
                    creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    formatted_creation_time = creation_time.strftime(
                        '%Y-%m-%d %H:%M:%S')  # Format datetime for user eyes ))

                    file_info = {
                        'full_path': file_path,
                        'file_name': file,
                        'file_size': f'{file_size_kb:.2f} KB',  # Format file size with 2 decimal places
                        'creation_time': formatted_creation_time
                    }
                    html_files_info.append(file_info)
        return html_files_info

    def _on_back_pressed(self):
        self.hash_map.delete('return_selected_data')
        self.hash_map.show_screen('PrintTemplates1C')


class PrintTemplates1CParameters(PrintScreenMixin):
    screen_name = 'PrintTemplates1CParameters'
    process_name = 'Print'

    def __init__(self, hash_map: HashMap):
        super().__init__(hash_map)
        self.title = 'Параметры шаблона 1C'
        self.barcode_types = ('ean13', 'code39', 'code128', 'qr-code', 'datamatrix')
        self.screen_values = {
            'barcode_width': '50',
            'barcode_height': '50',
            'barcode_left': '0',
            'barcode_right': '50',
            'barcode_up': '0',
            'barcode_down': '0',
            'barcode_type': 'ean13',
            'matching_table': '',
            'barcode_types': ';'.join(self.barcode_types),
            'return_selected_data': ''
        }

    def on_start(self):
        super().on_start()
        self._fill_match_table()
        self._refresh_html()

    def on_input(self):
        listeners = {
            'CardsClick': self._cards_click,
            'btn_save': self._save_template,
            'btn_default': self._set_default_screen_values,
            'ON_BACK_PRESSED': self._on_back_pressed,
        }
        self._on_input(listeners)

        if self._is_result_positive('MatchingTableDialog'):
            self._matching_table_result_positive()

    def _fill_match_table(self):
        table_data = self._get_matching_table_data()
        table_view = self._get_matching_table_view(table_data=table_data)
        self.hash_map.put('matching_table', table_view.to_json())

    def _get_matching_table_data(self):
        matching_table = self.hash_map.get('matching_table', from_json=True)
        if matching_table:
            tabledata = matching_table['customtable']['tabledata']
            data = [{'key': elem['key'], 'value': elem['value']} for elem in tabledata]
            return data
        head_of_table = {'key': 'Ключ', 'value': 'Значение'}
        template_variables = self._get_template_variables()
        data = [{'key': elem, 'value': elem} for elem in template_variables]
        return [head_of_table] + data

    def _get_matching_table_view(self, table_data):
        table_view = widgets.CustomTable(
            widgets.LinearLayout(
                self.LinearLayout(
                    self.TextView('@key'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('@value'),
                    weight=1
                ),

                orientation='horizontal',
                height="match_parent",
                width="match_parent",
                BackgroundColor='#FFFFFF'
            ),
            options=widgets.Options().options,
            tabledata=table_data
        )

        return table_view

    def _get_template_variables(self):
        lable_full_path = self.print_nosql.get('lable_full_path')
        return HTMLDocument.find_template_variables(lable_full_path)

    def _refresh_html(self):
        lable_full_path = self.print_nosql.get('lable_full_path')
        table_data = self._get_matching_table_data()[1:]
        data_for_printing = {item['key']: item['value'] for item in table_data}
        data_for_printing.update(barcode='123123123123')
        barcode_parameters = self._get_barcode_parameters()
        html = HTMLDocument.create_html(data_for_printing, barcode_parameters, lable_full_path)
        self.hash_map.put('html', html)

    def _cards_click(self):
        card_position = self.hash_map.get('selected_card_position')
        if card_position == '0':
            return
        selected_card_data = self.hash_map.get("selected_card_data", from_json=True)
        matching_table_options = ';'.join(self._get_template_variables())
        self.hash_map.put('matching_table_options', matching_table_options)
        layout = self._get_dialog_layout(
            'spinner', '@matching_table_options', 'matching_table_selected_option')
        self.hash_map.put('matching_table_selected_option', selected_card_data['value'])
        self.hash_map.show_dialog(listener='MatchingTableDialog',
                                  title=selected_card_data['key'],
                                  buttons=['Да', 'Нет'],
                                  dialog_layout=json.dumps(layout))

    def _save_template(self):
        matching_table = self.hash_map.get("matching_table", from_json=True)
        tabledata = matching_table['customtable']['tabledata'][1:]
        self.print_nosql.put('matching_table', json.dumps(tabledata))

        lable_full_path = self.print_nosql.get('lable_full_path')
        self.print_nosql.put('current_1c_template_path', lable_full_path)
        current_1c_template_name = os.path.split(lable_full_path)[1]
        self.print_nosql.put('current_1c_template_name', current_1c_template_name)

        self.print_nosql.put('barcode_parameters', json.dumps(self._get_barcode_parameters()))

        self._create_preview_image()
        self.print_nosql.delete('saved_print_template_sizes')
        self.hash_map.show_screen('PrintTemplates1C')

    def _create_preview_image(self):
        self.print_nosql.delete('preview_template_image_temp', with_file=True)
        self.print_nosql.delete('preview_template_image', with_file=True)
        img_path = create_file(
            ext='png', file_name='preview_label_template_image', folder='temp')
        self.print_nosql.put('preview_template_image', img_path)
        post_exec_handler = {
            "action": 'run',
            "type": "python",
            "method": 'print_templates_1c_parameters_post_exec',
        }

        html = self.hash_map.get('html')
        self.hash_map.html2png(
            html,
            'runprogress',
            post_exec_handlers=[post_exec_handler],
            file_path=img_path
        )
        self.hash_map.show_screen('PrintTemplates1C')

    def _matching_table_result_positive(self):
        matching_table = self.hash_map.get("matching_table", from_json=True)
        card_position = int(self.hash_map.get('selected_card_position'))
        current_elem = matching_table['customtable']['tabledata'][card_position]
        current_elem['value'] = self.hash_map.get('matching_table_selected_option')
        self.hash_map.put("matching_table",
                          json.dumps(matching_table, ensure_ascii=False))

    def _get_barcode_parameters(self):
        return {value: self.hash_map.get(value) for value in self.screen_values}

    def print_templates_1c_parameters_post_exec(self):
        img_path = self.print_nosql.get('preview_template_image')
        # resize_image(img_path, ratio=2.2)

    def _on_back_pressed(self):
        self._delete_screen_values()
        self.hash_map.show_screen('TemplatesList')


class PrintTemplates1CSizes(PrintScreenMixin):
    screen_name = 'PrintTemplates1CSizes'
    process_name = 'Print'

    def __init__(self, hash_map: HashMap):
        super().__init__(hash_map)
        self.title = 'Размеры шаблона 1C'
        self.screen_values = {
            'print_template_width': '50',
            'print_template_height': '50',
            'print_image_width': '50',
            'print_image_height': '50',
            'print_template_dpmm': '8',
            'print_template_ll': '400',
            'print_template_pw': '1000',
            'print_template_x_origin': '0',
            'print_template_y_origin': '0',
        }

    def on_start(self):
        super().on_start()
        self._refresh_image()

    def on_input(self):
        listeners = {
            'btn_save_template_sizes': self._save_template_sizes,
            'btn_delete_print_template': self._delete_print_template,
            'btn_default_template_sizes': self._set_default_screen_values,
            'btn_sent_to_print': self._sent_to_print,
            'ON_BACK_PRESSED': self._on_back_pressed,
        }
        self._on_input(listeners)

    def _sent_to_print(self):
        self.hash_map.toast('Отправлено на печать')
        zpl_data = self.print_nosql.get('zpldata')
        PrintService(self.hash_map).print_zpl(zpl_data)

    def _refresh_image(self):
        path_to_img = self.print_nosql.get('preview_template_image')
        template_sizes = self._get_template_sizes()
        zpl_data = PrintService(self.hash_map).make_zpl_from_label(path_to_img=path_to_img,
                                                    **template_sizes)
        self.print_nosql.put('zpldata', zpl_data)
        sended, response = PrintService(self.hash_map).zpl_to_png_from_api(zpl_data=zpl_data,
                                                            **template_sizes)
        if not sended:
            self.hash_map.toast('Error: ' + response)
            return

        path, ext = os.path.splitext(path_to_img)
        preview_path = path + '_preview' + ext
        with open(preview_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        self.print_nosql.put('preview_template_image_temp', preview_path)
        self.hash_map.put('print_image_sizes', '~' + preview_path)

    def _save_template_sizes(self):
        self._save_screen_values()
        template = self._get_template_sizes()
        self.print_nosql.put('saved_print_template_sizes', json.dumps(template))
        self.hash_map.toast('Шаблон сохранён')

    def _delete_print_template(self):
        self.print_nosql.delete('saved_print_template_sizes')
        self.hash_map.toast('Шаблон удалён')

    def _get_template_sizes(self):
        return {value: int(self.hash_map.get(value)) for value in self.screen_values}

    def _on_back_pressed(self):
        self.hash_map.put('print_image_sizes')
        self._delete_screen_values()
        self.hash_map.show_screen('PrintTemplates1C')


class PrintTemplatesZPL(PrintScreenMixin):
    screen_name = 'PrintTemplatesZPL'
    process_name = 'Print'

    def __init__(self, hash_map: HashMap):
        super().__init__(hash_map)
        self.title = 'Шаблон ZPL'
        self.screen_values = {
            'zpl_template_from_string_dpmm': '8',
            'zpl_template_from_string_width': '50',
            'zpl_template_from_string_height': '50',
            'zpl_template_from_string': ''
        }

    def on_start(self):
        super().on_start()
        self._refresh_image()

    def on_input(self):
        listeners = {
            'btn_zpl_template_from_string_print': self._print_zpl_dialog,
            'btn_zpl_constructor_redirect': self._zpl_constructor_redirect,
            'btn_template_from_string_make_default': self._make_template_default,
            'ON_BACK_PRESSED': self._on_back_pressed,
        }
        self._on_input(listeners)

        if self._is_result_positive('print_template_dialog'):
            self._print_template_dialog_on_result_positive()

    def _refresh_image(self):
        zpl = self.hash_map.get('zpl_template_from_string')
        if not zpl:
            return
        zpl = PrintService(self.hash_map).add_ascii_zpl(zpl)
        width = int(self.hash_map.get('zpl_template_from_string_width'))
        height = int(self.hash_map.get('zpl_template_from_string_height'))
        dpmm = int(self.hash_map.get('zpl_template_from_string_dpmm'))
        sended, response = PrintService(self.hash_map).zpl_to_png_from_api(zpl, dpmm, width, height)
        if not sended:
            return
        file_path = create_file(
            'png', folder='zpl_templates', file_name='zpl_template_from_string')
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(response, f)
        resize_image(path_to_image=file_path, ratio=2.2)
        self.hash_map.put('zpl_template_from_string_image', '~' + file_path)

    def _print_zpl_dialog(self):
        if not self.hash_map.get('zpl_template_from_string'):
            self.hash_map.toast('Не указан шаблон ZPL')
            return
        layout = self._get_dialog_layout(
            input_type='numeric',
            value="@zpl_preview_zpl_print_count",
            variable="zpl_preview_zpl_print_count"
        )
        self.hash_map.show_dialog(
            'print_template_dialog',
            title='Укажите количество',
            buttons=['Печать', 'Отмена'],
            dialog_layout=json.dumps(layout)
        )

    def _make_template_default(self):
        zpl_template = self.hash_map.get('zpl_template_from_string')
        if not zpl_template:
            self.hash_map.toast('Не указан ZPL')
            return
        self.print_nosql.put('default_zpl_template_from_string', zpl_template)
        self.print_nosql.delete('default_zpl_template_path')
        self._save_screen_values()
        self.hash_map.toast('Шаблон zpl установлен по умолчанию')

    def _zpl_constructor_redirect(self):
        self.hash_map.show_screen('PrintTemplatesZPLConstructor')

    def _print_template_dialog_on_result_positive(self):
        self.hash_map.delete('ShowDialogLayout')
        count = self.hash_map.get('zpl_preview_zpl_print_count')
        zpl = self.hash_map.get('zpl_template_from_string')
        if not count or count == '0':
            self.hash_map.toast('Не указано количество копий для печати')
            return
        zpl = PrintService(self.hash_map).add_ascii_zpl(zpl)
        zpl *= int(float(count))
        PrintService(self.hash_map).print_zpl(zpl)

    def _on_back_pressed(self):
        self.hash_map.show_screen('PrintSettings')


class PrintTemplatesZPLConstructor(PrintScreenMixin):
    screen_name = 'PrintTemplatesZPLConstructor'
    process_name = 'Print'

    def __init__(self, hash_map: HashMap):
        super().__init__(hash_map)
        self.title = 'Настройка шаблона ZPL'
        self.screen_values = {
            'zpl_preview_dpmm': '8',
            'zpl_preview_label_width': '50',
            'zpl_preview_label_height': '50',
            'zpl_preview_current_element_x': '0',
            'zpl_preview_current_element_y': '0',
        }

    def on_start(self):
        super().on_start()
        self._set_visibility()
        self._set_template_data()

    def on_input(self):
        if self.listener == 'ON_BACK_PRESSED':
            if self.hash_map.get('current_zpl_element'):
                self.hash_map.delete('current_zpl_element')
                self.hash_map.delete("zpl_preview_current_element_x")
                self.hash_map.delete("zpl_preview_current_element_y")
                return
            self.hash_map.show_screen('PrintTemplatesZPL')

        elif self.listener == 'btn_zpl_preview_save_template':
            self.save_template()

        elif self.listener == 'btn_zpl_preview_delete_template':
            self.delete_template_dialog()

        elif self.listener == 'btn_zpl_preview_print_zpl':
            self.print_zpl_dialog()

        elif self.listener == 'btn_zpl_preview_create_template':
            self.create_template_dialog()

        elif self.listener == 'btn_zpl_preview_select_template':
            self.select_template_dialog()

        elif self.listener == 'btn_zpl_preview_save_as':
            current_template = self.hash_map.get('current_zpl_template')
            if not current_template:
                self.hash_map.toast('Не выбран шаблон')
                return
            current_template = json.loads(current_template)
            path_to_tamplate = current_template['file_path']
            template_name = current_template['name'] + '.json'
            self.hash_map.put('SaveExternalFile', json.dumps({"path": path_to_tamplate, "default": template_name}))

        elif self.listener == 'btn_zpl_preview_make_default_zpl_template':
            current_template = self.hash_map.get('current_zpl_template')
            if not current_template:
                self.hash_map.toast('Не выбран шаблон')
                return
            current_template = json.loads(current_template)
            path_to_tamplate = current_template['file_path']
            self.print_nosql.put('default_zpl_template_path', path_to_tamplate)
            self.print_nosql.delete('default_zpl_template_from_string')
            self.hash_map.toast('Шаблон ' + current_template['name'] + ' сделан основным')

        elif self.listener == 'btn_zpl_preview_add_element':
            self.add_element_dialog()

        elif self.listener == 'btn_zpl_preview_save_current_element':
            self.hash_map.delete("current_zpl_element")
            self.hash_map.delete("zpl_preview_current_element_x")
            self.hash_map.delete("zpl_preview_current_element_y")

        elif self._is_result_positive('print_template_dialog'):
            self.hash_map.delete('ShowDialogLayout')
            count = self.hash_map.get('zpl_preview_zpl_print_count')
            if not count:
                self.hash_map.toast('Не указано количество копий для печати')
                return
            current_template = json.loads(self.hash_map.get('current_zpl_template'))
            zpl_data = ZPLConstructor(
                width=current_template['label_width'],
                height=current_template['label_height'],
                dpmm=current_template['dpmm'],
                hash_map=self.hash_map
            ).get_zpl(current_template)
            zpl_data *= int(count)
            PrintService(self.hash_map).print_zpl(zpl_data)

        elif self._is_result_positive('delete_template_dialog'):
            self.hash_map.delete('ShowDialogLayout')
            if not self._current_template_exists():
                return
            current_template = json.loads(self.hash_map.get('current_zpl_template'))
            os.remove(current_template['file_path'])
            self.hash_map.delete('current_zpl_template')
            self.hash_map.delete('zpl_preview')
            self.hash_map.delete('zpl_preview_table')
            self.hash_map.delete("current_zpl_element")
            self.hash_map.delete('zpl_preview_current_element_x')
            self.hash_map.delete('zpl_preview_current_element_y')
            self.hash_map.toast(f'Шаблон {current_template["name"]} удалён')

        elif self._is_result_positive('create_template_dialog'):
            self.hash_map.delete('ShowDialogLayout')
            template_name = self.hash_map.get('zpl_preview_create_template_name')
            file_path = create_file('json', 'zpl_templates', template_name)
            empty_template = self._get_empty_template(template_name, file_path)
            with open(file_path, 'w') as f:
                json.dump(empty_template, f)
            self.hash_map.put('current_zpl_template', json.dumps(empty_template, ensure_ascii=False))
            self.hash_map.toast('Шаблон создан')
            self.hash_map.delete("current_zpl_element")
            self.hash_map.delete('zpl_preview_current_element_x')
            self.hash_map.delete('zpl_preview_current_element_y')

        elif self._is_result_positive('select_template_dialog'):
            self.hash_map.delete('ShowDialogLayout')
            file_name = self.hash_map.get('zpl_preview_selected_template_name')
            existing_templates = self._get_existing_templates()
            for template in existing_templates:
                if file_name == os.path.split(template)[1]:
                    with open(template, 'r') as f:
                        template_data = f.read()
                    self.hash_map.put('current_zpl_template', template_data)
                    break
            self.hash_map.delete("current_zpl_element")

        elif self._is_result_positive('add_element_dialog'):
            self.hash_map.delete('ShowDialogLayout')
            current_template = json.loads(self.hash_map.get('current_zpl_template'))
            selected_element = self.hash_map.get('zpl_preview_selected_element')
            current_element = ZPLConstructor(
                width=current_template['label_width'],
                height=current_template['label_height'],
                dpmm=current_template['dpmm'],
                hash_map=self.hash_map
            ).get_element(selected_element)
            self.hash_map.put('current_zpl_element', json.dumps(current_element, ensure_ascii=False))
            current_template['elements'].append(current_element)
            self.hash_map.put('current_zpl_template', json.dumps(current_template, ensure_ascii=False))
            self.hash_map.put('zpl_preview_current_element_params',
                              json.dumps(current_element['params'], ensure_ascii=False))

        elif self.listener == 'CardsClick':
            self.cards_click()
        elif self.listener == 'LayoutAction':
            self._layout_action()
        elif self._is_result_positive('parameter_input'):
            input_value = self.hash_map.get('current_element_input_value')
            card_position = int(self.hash_map.get('selected_card_position'))
            current_zpl_element = json.loads(self.hash_map.get('current_zpl_element'))
            params_table = self.hash_map.get('current_element_params_table',
                                             from_json=True)
            params_data = params_table['customtable']['tabledata'][card_position]
            selected_parameter = params_data['parameter']
            allowed_params = ZPLConstructor.allowed_elements[current_zpl_element['type']]
            for allowed_parameter in allowed_params:
                if allowed_parameter == selected_parameter:
                    if type(allowed_params[allowed_parameter]) is int:
                        input_value = int(float(input_value))
            for parameter in current_zpl_element['params']:
                if parameter == selected_parameter:
                    current_zpl_element['params'][parameter] = input_value
            self.hash_map.put('current_zpl_element', json.dumps(current_zpl_element, ensure_ascii=False))
            self.hash_map.put('zpl_preview_current_element_params', json.dumps(current_zpl_element['params'], ensure_ascii=False))

    def _set_visibility(self):
        if self.hash_map.get('current_zpl_template'):
            self.hash_map.put('Show_zpl_preview_create_template_data', '-1')
            self.hash_map.put('Show_zpl_preview_table', '1')
        else:
            self.hash_map.put('Show_zpl_preview_create_template_data', '1')
            self.hash_map.put('Show_zpl_preview_table', '-1')
        if self.hash_map.get('current_zpl_element'):
            self.hash_map.put('Show_zpl_preview_table', '-1')
            self.hash_map.put('Show_zpl_current_element_params', '1')
        else:
            self.hash_map.put('Show_zpl_current_element_params', '-1')

    def _set_template_data(self):
        if not self.hash_map.get('current_zpl_template'):
            template_path = self.print_nosql.get('default_zpl_template_path')
            if template_path:
                if os.path.isfile(template_path):
                    with open(template_path, 'r') as f:
                        template = f.read()
                        self.hash_map.put('current_zpl_template', template)
                        self.hash_map.toast('Загружен zpl шаблон по умолчанию')
                else:
                    self.print_nosql.delete('default_zpl_template_path')
                    self.hash_map.toast('Не удалось загрузить шаблон по умолчанию')

        current_zpl_template = self.hash_map.get('current_zpl_template')
        if current_zpl_template:
            current_zpl_template = json.loads(current_zpl_template)
            if self.hash_map.get('current_zpl_element'):
                self._update_current_zpl_element()
            self._refresh_image()
            self.hash_map.put('zpl_preview_table', self.get_template_table().to_json())
            self.hash_map.put('zpl_current_template_name', current_zpl_template['name'])

    def _refresh_image(self):
        current_template = json.loads(self.hash_map.get('current_zpl_template'))
        zpl = ZPLConstructor(
            width=current_template['label_width'],
            height=current_template['label_height'],
            dpmm=current_template['dpmm'],
            hash_map=self.hash_map
        ).get_zpl(current_template)

        sended, response = PrintService(self.hash_map).zpl_to_png_from_api(
            zpl_data=zpl,
            print_template_dpmm=int(self.hash_map.get('zpl_preview_dpmm')),
            print_template_width=int(self.hash_map.get('zpl_preview_label_width')),
            print_template_height=int(self.hash_map.get('zpl_preview_label_height')),
        )
        file_path = create_file('png', folder='zpl_templates', file_name='zpl_preview')
        if sended:
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(response, f)
            resize_image(path_to_image=file_path, ratio=2.2)
            self.hash_map.put('zpl_preview', '~' + file_path)

    def _get_template_table_data(self):
        head_of_table = {
            'id': 'id',
            'type': 'Тип',
            'x': 'X',
            'y': 'Y',
            'params': 'Параметры',
            '_layout': self._get_table_head_layout()
        }
        current_template: dict = json.loads(self.hash_map.get('current_zpl_template'))
        elements: list = current_template['elements']
        for index, element in enumerate(elements, 1):
            element['id'] = str(index)
            element['params'] = str(element['params'])
        return [head_of_table] + elements

    def _get_table_head_layout(self):
        layout = widgets.LinearLayout(
                self.LinearLayout(
                    self.TextView('@type'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('@x'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('@y'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('@params'),
                    weight=2
                ),
                widgets.PopupMenuButton(
                    Value=';'.join(['Добавить']),
                    Variable="menu_delete",
                ),
                orientation='horizontal',
                height="match_parent",
                width="match_parent",
                BackgroundColor='#FFFFFF'
            )
        return layout

    def _get_template_table_view(self, table_data: List):
        table_view = widgets.CustomTable(
            widgets.LinearLayout(
                self.LinearLayout(
                    self.TextView('@type'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('@x'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('@y'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('@params'),
                    weight=2
                ),
                widgets.PopupMenuButton(
                    Value=';'.join(['Изменить', 'Удалить']),
                    Variable="menu_delete",
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

    def get_template_table(self):
        table_data = self._get_template_table_data()
        table_view = self._get_template_table_view(table_data)
        return table_view

    def print_zpl_dialog(self):
        if not self._current_template_exists():
            return

        layout = self._get_dialog_layout(
            input_type='numeric',
            value="@zpl_preview_zpl_print_count",
            variable="zpl_preview_zpl_print_count"
        )
        self.hash_map.show_dialog(
            'print_template_dialog',
            title='Укажите количество',
            buttons=['Печать', 'Отмена'],
            dialog_layout=json.dumps(layout)
        )

    def save_template(self):
        if self._current_template_exists():
            current_template = json.loads(self.hash_map.get('current_zpl_template'))
            with open(current_template['file_path'], 'w') as f:
                json.dump(current_template, f)
            self.hash_map.toast('Шаблон сохранён')

    def delete_template_dialog(self):
        if self._current_template_exists():
            current_template = json.loads(self.hash_map.get('current_zpl_template'))
            self.hash_map.show_dialog(
                'delete_template_dialog',
                title=f'Удаление шаблона {current_template["name"]}',
                buttons=['Подтвердить', 'Отмена'],
            )

    def create_template_dialog(self):
        layout = self._get_dialog_layout(
            input_type='text',
            value='@zpl_preview_create_template_name',
            variable='zpl_preview_create_template_name'
        )
        self.hash_map.show_dialog(
            'create_template_dialog',
            title='Укажите название шаблона',
            buttons=['Создать', 'Отмена'],
            dialog_layout=json.dumps(layout)
        )

    def _get_existing_templates(self):
        import glob
        zpl_templates_dir = os.path.join(suClass.get_temp_dir(), 'zpl_templates')
        return glob.glob(f"{zpl_templates_dir}/*.json")

    def select_template_dialog(self):
        layout = self._get_dialog_layout(
            input_type='spinner',
            value='@zpl_preview_select_template_names',
            variable='zpl_preview_selected_template_name'
        )
        templates = self._get_existing_templates()
        template_names = ';'.join(os.path.split(template)[1] for template in templates)
        self.hash_map.put('zpl_preview_select_template_names', template_names)
        self.hash_map.show_dialog(
            'select_template_dialog',
            title='Укажите название шаблона',
            buttons=['Выбрать', 'Отмена'],
            dialog_layout=json.dumps(layout)
        )

    def add_element_dialog(self):
        layout = self._get_dialog_layout(
            input_type='spinner',
            value='@zpl_preview_select_elements',
            variable='zpl_preview_selected_element'
        )
        allowed_elements = ';'.join(ZPLConstructor.allowed_elements.keys())
        self.hash_map.put('zpl_preview_select_elements', allowed_elements)
        self.hash_map.show_dialog(
            'add_element_dialog',
            title='Выберите элемент',
            buttons=['Выбрать', 'Отмена'],
            dialog_layout=json.dumps(layout)
        )

    def _get_empty_template(self, template_name: str, file_path: str):
        empty_template = {
            'name': template_name,
            'file_path': file_path,
            'label_width': int(self.hash_map.get('zpl_preview_label_width')),
            'label_height': int(self.hash_map.get('zpl_preview_label_height')),
            'dpmm': int(self.hash_map.get('zpl_preview_dpmm')),
            'elements': []
        }
        return empty_template

    def _layout_action(self):
        layout_listener = self.hash_map['layout_listener']
        if layout_listener == 'Удалить':
            selected_element_data = json.loads(self.hash_map.get('card_data'))
            current_template = json.loads(self.hash_map.get('current_zpl_template'))
            for element in current_template['elements']:
                if element['uuid'] == selected_element_data['uuid']:
                    current_template['elements'].remove(element)
                    break
            self.hash_map.put('current_zpl_template', json.dumps(current_template, ensure_ascii=True))
        elif layout_listener == 'Изменить':
            selected_element_data = json.loads(self.hash_map.get('card_data'))
            current_template = json.loads(self.hash_map.get('current_zpl_template'))
            for element in current_template['elements']:
                if element['uuid'] == selected_element_data['uuid']:
                    self.hash_map.put("zpl_preview_current_element_x", str(element['x']))
                    self.hash_map.put("zpl_preview_current_element_y", str(element['y']))
                    self.hash_map.put("zpl_preview_current_element_params", json.dumps(element['params']))
                    self.hash_map.put('current_zpl_element', json.dumps(element, ensure_ascii=False))
                    break

        elif layout_listener == 'Добавить':
            self.add_element_dialog()

    def _update_current_zpl_element(self):
        current_zpl_element = json.loads(self.hash_map.get('current_zpl_element'))
        current_element_x = self.hash_map.get('zpl_preview_current_element_x')
        current_element_y = self.hash_map.get('zpl_preview_current_element_y')
        current_element_params = self.hash_map.get('zpl_preview_current_element_params')

        current_zpl_element['x'] = int(current_element_x)
        current_zpl_element['y'] = int(current_element_y)
        current_zpl_element['params'] = json.loads(current_element_params)

        self.hash_map.put('current_zpl_element', json.dumps(current_zpl_element, ensure_ascii=False))

        current_template = self.hash_map.get('current_zpl_template', from_json=True)
        for element in current_template['elements']:
            if element['uuid'] == current_zpl_element['uuid']:
                element['x'] = int(current_element_x)
                element['y'] = int(current_element_y)
                element['params'] = json.loads(current_element_params)
                break
        self.hash_map.put('current_zpl_template', json.dumps(current_template, ensure_ascii=False))
        params_table = self.get_current_element_params_table()
        self.hash_map.put('current_element_params_table', params_table.to_json())

    def get_current_element_params_data(self):
        current_zpl_element = json.loads(self.hash_map.get('current_zpl_element'))
        params = current_zpl_element['params']
        params_list = [{'parameter': parameter, 'value': params[parameter]} for parameter in params]
        return [{'parameter': 'Параметр', 'value': 'Значение'}] + params_list

    def get_current_element_params_table_view(self, params_data: List):
        table_view = widgets.CustomTable(
            widgets.LinearLayout(
                self.LinearLayout(
                    self.TextView('@parameter'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('@value'),
                    weight=1
                ),
                orientation='horizontal',
                height="match_parent",
                width="match_parent",
                BackgroundColor='#FFFFFF'
            ),

            options=widgets.Options(override_search=True).options,
            tabledata=params_data
        )

        return table_view

    def get_current_element_params_table(self):
        params_data = self.get_current_element_params_data()
        view = self.get_current_element_params_table_view(params_data)
        return view

    def cards_click(self):
        card_position = int(self.hash_map.get('selected_card_position'))
        if not self.hash_map.get('current_zpl_element') or card_position == 0:
            return
        current_element = self.hash_map.get('current_zpl_element', from_json=True)
        params_table = self.hash_map.get('current_element_params_table', from_json=True)
        params_data = params_table['customtable']['tabledata'][card_position]
        parameter = params_data['parameter']
        allowed_params = ZPLConstructor.allowed_elements[current_element['type']]
        for allowed_parameter in allowed_params:
            if allowed_parameter == parameter:
                input_type = 'text' if isinstance(allowed_params[allowed_parameter], str) else 'numeric'
                dialog_layout = self._get_dialog_layout(
                    input_type=input_type,
                    value='@current_element_input_value',
                    variable='current_element_input_value'
                )
                self.hash_map.show_dialog(
                    listener='parameter_input',
                    title=current_element['type'].capitalize() + '. ' + parameter.capitalize(),
                    dialog_layout=json.dumps(dialog_layout)
                )
                self.hash_map.put('current_element_input_value', params_data['value'])

    def _current_template_exists(self):
        current_template = self.hash_map.get('current_zpl_template')
        if not current_template:
            self.hash_map.toast('Не выбран шаблон')
            return False
        return True


# ^^^^^^^^^^^^^^^^^^^^^ Printing screens ^^^^^^^^^^^^^^^^^^^^^^^^^^^^


# ==================== OCR =============================


class ActiveCVArticleRecognition(Screen):
    screen_name = 'NextStepActiveCV'
    process_name = 'OcrArticleRecognition'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.id_doc = self.hash_map['id_doc']
        self.service = DocService(self.id_doc)

    def on_start(self):
        articles_ocr_ncl.delete('finded_articles')
        self._set_vision_settings()
        self.hash_map.put('art_info', 'Найденные артикулы: ')

    def on_input(self):
        if self.listener == 'Обработать':
            articles_ocr_ncl.put('button_manage_articles', True)
            self.hash_map.finish_process()

    def on_object_detected(self):
        self.hash_map.beep()
        current_object = self.hash_map.get('current_object')
        finded_articles = articles_ocr_ncl.get('finded_articles')
        finded_articles = json.loads(finded_articles) if finded_articles else []
        if current_object not in finded_articles:
            finded_articles.append(current_object)
            self.hash_map.put(
                'art_info', 'Найденные артикулы: ' + ';'.join(finded_articles))
            articles_ocr_ncl.put('finded_articles', json.dumps(finded_articles))

        good_name = self.get_good_info(current_object)
        self.hash_map.add_to_cv_list(
            {'object': str(current_object),
             'info': f'Товар: <big>{good_name}</big>'},
            'object_info_list', _dict=True)

    def get_good_info(self, article: str) -> str:
        query = ('SELECT RS_goods.name as name'
                 ' FROM RS_docs_table'
                 ' LEFT JOIN RS_goods ON RS_docs_table.id_good = RS_goods.id'
                 ' WHERE RS_docs_table.id_doc = ? AND RS_goods.art = ?')
        goods = self.service.provider.sql_query(query, f'{self.id_doc},{article}')
        return goods[0]['name'] if goods else 'Не найдено'

    def _set_vision_settings(self):
        settings = articles_ocr_ncl.get('articles_ocr_settings')
        self.hash_map.set_vision_settings(**json.loads(settings))


class SerialNumberOCRSettings(Screen):
    screen_name = 'SerialNumberOCRSettings'
    process_name = 'OcrTextRecognition'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.screen_title = 'Шаблон распознавания S/N'
        self.screen_values = {
            'ocr_serial_template_min_rec_amount': '5',
            'ocr_serial_template_num_amount': '10',
            'ocr_serial_template_prefix': 'SN',
            'ocr_serial_template_continuous_recognition': 'false',
            'ocr_serial_template_use_prefix': 'true',
            'ocr_serial_current_template': ""
        }

    def on_start(self):
        self.hash_map.set_title(self.screen_title)
        self._set_screen_values()

    def on_input(self):
        if self.listener == 'btn_save_ocr_settings':
            is_valid, error = self._validate_ocr_settings()
            if not is_valid:
                self.hash_map.toast(error)
                return
            self._save_template_patterns()
            self._save_template_settings()
            self._set_vision_settings()
            self.hash_map.toast('Шаблон сохранён')
            if ocr_nosql.get('show_process_result'):
                ocr_nosql.delete('show_process_result')
                self.hash_map.finish_process_result()
        elif self.listener == 'ON_BACK_PRESSED':
            if ocr_nosql.get('show_process_result'):
                ocr_nosql.delete('show_process_result')
                self.hash_map.finish_process_result()
            else:
                self.hash_map.switch_process_screen('Параметры')

    def _set_screen_values(self):
        for value_name, value in self.screen_values.items():
            new_value = self.hash_map.get(value_name) or ocr_nosql.get(value_name) or value
            self.hash_map.put(value_name, new_value)

    def _save_template_settings(self):
        for value_name in self.screen_values:
            ocr_nosql.put(value_name, self.hash_map.get(value_name), True)

    def _save_template_patterns(self):
        num_amount = self.hash_map.get('ocr_serial_template_num_amount')
        prefix = self.hash_map.get('ocr_serial_template_prefix')
        use_prefix = self.hash_map.get('ocr_serial_template_use_prefix')
        if use_prefix == 'true':
            patterns = [rf'^{prefix}', rf'([^\doO])(\d{{{num_amount}}})$']
        else:
            patterns = [rf'\d{{{num_amount}}}']
        current_template = (f'Текущий шаблон: {prefix if use_prefix == "true" else ""}'
                            f'{"*" * int(num_amount)}')
        self.hash_map.put('ocr_serial_current_template', current_template)
        ocr_nosql.put('ocr_serial_template_patterns', json.dumps(patterns), True)

    def _set_vision_settings(self) -> None:
        """Устанавливает настройки для кнопки распознавания текста"""
        num_amount = int(ocr_nosql.get('ocr_serial_template_num_amount') or '10')
        use_prefix = ocr_nosql.get('ocr_serial_template_use_prefix')
        if use_prefix == 'true':
            prefix = ocr_nosql.get('ocr_serial_template_prefix')
            min_length = num_amount + len(prefix)
            max_length = min_length + 2
        else:
            min_length, max_length = num_amount, num_amount
        values_list = ("~[{\"action\":\"run\",\"type\":\"python\","
                       "\"method\":\"serial_key_recognition_ocr\"}]")
        rec_settings = dict(
            values_list=values_list,
            max_length=max_length,
            min_length=min_length,
        )
        ocr_nosql.put('serial_ocr_settings', json.dumps(rec_settings), True)

    def _validate_ocr_settings(self) -> Tuple[bool, str]:
        """Валидация данных введенных в диалоге ШаблонРаспознавания"""
        min_rec_amount = self.hash_map.get('ocr_serial_template_min_rec_amount')
        num_amount = self.hash_map.get('ocr_serial_template_num_amount')
        prefix: str = self.hash_map.get('ocr_serial_template_prefix')
        use_prefix = self.hash_map.get('ocr_serial_template_use_prefix')
        if not min_rec_amount.isdigit() or int(min_rec_amount) == 0:
            error = ('Укажите корректное минимальное количество'
                    ' обнаружений серийного номера')
            return False, error
        if not num_amount.isdigit():
            error = 'Количество цифр в шаблоне не корректно'
            return False, error
        if not 1 < int(num_amount) < 21:
            error = 'Количество цифр в шаблоне должно быть в интервале от 2 до 20'
            return False, error
        if prefix.isspace() and use_prefix == 'true':
            error = 'Не указан префикс'
            return False, error
        if prefix != prefix.strip():
            error = 'Пробелы в начале или в конце префикса'
            return False, error
        return True, ''

    @staticmethod
    def serial_key_recognition_ocr(hash_map: HashMap) -> None:
        """Находит в переданной из OCR строке серийный номер, по заданному шаблону"""
        ocr_text = hash_map.get("ocr_text")
        use_prefix = ocr_nosql.get('ocr_serial_template_use_prefix')
        num_amount = int(ocr_nosql.get('ocr_serial_template_num_amount')) or 10
        patterns = ocr_nosql.get('ocr_serial_template_patterns')
        patterns = json.loads(patterns) if patterns else [rf'\d{{{num_amount}}}']
        for pattern in patterns:
            match_num = re.search(pattern, ocr_text)
            if not match_num:
                return
        result = match_num.group(2) if use_prefix == 'true' else match_num.group()
        min_rec_amount = int(ocr_nosql.get('ocr_serial_template_min_rec_amount'))
        result_in_memory = ocr_nosql_counter.get(result)
        if result_in_memory is None:
            ocr_nosql_counter.put(result, 1)
        elif result_in_memory < min_rec_amount:
            ocr_nosql_counter.put(result, result_in_memory + 1)
        elif result_in_memory == min_rec_amount:
            ocr_nosql_counter.put(result, result_in_memory + 1)
            from_screen = ocr_nosql.get('from_screen')
            if from_screen == 'FlowDocDetailsScreen':
                hash_map.toast(ocr_nosql.get('id_doc'))
                FlowDocService(ocr_nosql.get('id_doc')).add_barcode_to_database(result)
            elif from_screen == 'SeriesSelectScreen':
                hash_map.put("ocr_result", result)
                ocr_nosql.put('ocr_result', result)
                return
            hash_map.beep()
            hash_map.toast('Серийный номер: ' + result)
            if ocr_nosql.get('ocr_serial_template_continuous_recognition') == 'false':
                hash_map.put("ocr_result", result)
                return
            for serial in ocr_nosql_counter.keys():
                if ocr_nosql_counter.get(serial) < min_rec_amount:
                    ocr_nosql_counter.put(serial, 0)


# ^^^^^^^^^^^^^^^^^^^^^ OCR ^^^^^^^^^^^^^^^^^^^^^^^^^^^^


# ==================== GoodsBalances =============================

class GoodsBalancesItemCard(Screen):
    screen_name = 'CheckBalance'
    process_name = 'Balance'

    def __init__(self, hash_map, screen_data: Dict, **kwargs):
        super().__init__(hash_map, **kwargs)
        self.service = GoodsService()
        self.hs_service = HsService(self.get_http_settings())
        self.table_type = 'warehouses'
        self.screen_data = screen_data

    def init_screen(self):
        self._update_hash_map_keys()

    def _update_hash_map_keys(self):
        self.hash_map.put_data({key: value for key, value in self.screen_data.items()})

    def on_start(self):
        self._set_visibility_on_start(
            [
                'error_msg',
                'selected_object_name',
                'selected_cell_name',
                'selected_wh_name',
                'item_barcode'
            ]
        )
        if not self.hash_map.get('balances_table'):
            self.hash_map.put("Show_get_balances_controls", "1")
            self.hash_map.put("Show_show_filters", "-1")

        if self.hash_map.get_bool('new_art'):
            self._check_item_variants()

    def on_input(self):
        listeners = {
            'wh_select': self._select_wh,
            'wh_select_success': self._select_wh_result,
            'get_balance_btn': self._get_balances,
            'barcode': self._identify_barcode_balances,
            'CardsClick': self._card_click(),
            'show_filters': self._show_filters,
            'ON_BACK_PRESSED': self._on_back_pressed,
        }
        if self.listener in listeners:
            listeners[self.listener]()
        else:
            super().on_input()

        if self._is_result_positive('Выберите вариант товара:'):
            self.hash_map.put("Show_get_balances_controls", "1")

    def _get_balances(self):
        if (self.hash_map.get('item_art_input') != self.hash_map.get('good_art')
                and not self.hash_map.get_bool('variant_selected')):

            self.hash_map.put('new_art', True)
            self.validate_input()

        raw_balances_data = self._get_balances_data()
        balances_data = self._prepare_table_data(raw_balances_data)
        balances_table = self._get_balances_table_view(balances_data)

        self.hash_map.put_data({
                'balances_table': balances_table.to_json(),
                'Show_get_balances_controls': '-1',
                'Show_show_filters': '1',
                'property_id': '',
                'from_barcode': False,
                'item_code': '',
                'variant_selected': False
            })

    def _select_wh(self):
        SelectItemScreen(
            self.hash_map,
            table_name='RS_warehouses',
            result_listener='wh_select_success',
            title='Выберите склад',
            parent=self
        ).show()

    def _select_wh_result(self):
        selected_wh = self.result_process
        self.hash_map['wh_select'] = selected_wh.get('name') if selected_wh else ''

    def validate_input(self):
        self._process_input_item_art()
        self._process_input_cell()

        if not (self.hash_map.get('item_art_input') or self.hash_map.get('cell_input') or self.hash_map.get('wh_select')
                or self.hash_map.get('selected_cell_id')):

            self.hash_map.put_data({
                    'balances_tables': '',
                    'object_name': '',
                    'cell_name': '',
                    'error_msg': "Должен быть выбран склад, товар или ячейка"
                })

    def _process_input_item_art(self):
        item_art_input = self.hash_map.get('item_art_input')

        if self.hash_map.get('item_art_input'):
            item_values_result = self.service.get_values_by_field(
                table_name='RS_goods', field='art',
                field_value=item_art_input
            )
            if item_values_result:
                self.hash_map.put_data(
                    {
                        'object_name': item_values_result[0]['name'],
                        'input_item_id': item_values_result[0]['id'],
                        'selected_object_name': f'{item_values_result[0]["name"]}, {item_values_result[0]["code"]}',
                        'item_code': item_values_result[0]['code'],
                        'error_msg': '',
                        'item_art_input': self.hash_map.get('item_art_input'),
                        'item_barcode': ''
                    }
                )

            else:
                if item_art_input != '—' and self.hash_map.get('return_to_item_card'):
                    self.hash_map.put('error_msg', f" Товар с артикулом '{item_art_input}'  не найден")
        else:
            self.hash_map.put('input_item_id', '')
            self.hash_map.put('object_name', '')
            self.hash_map.put('selected_object_name', '')

    def _process_input_cell(self):
        if self.hash_map.get('cell_input'):
            cell_values_result = self.service.get_values_by_field(
                table_name='RS_cells',
                field='name',
                field_value=self.hash_map.get('cell_input')
            )

            if cell_values_result:
                self.table_type = 'cells'
                self.hash_map.put('selected_cell_id', cell_values_result[0]['id'])
                self.hash_map.put('cell_name', self.hash_map.get('cell_input'))

            else:
                current_error = f"{self.hash_map['error_msg']}\n" if self.hash_map['error_msg'] else ''
                error_text = '{}Ячейка c именем {} не найдена'.format(
                    current_error, self.hash_map['cell_input']
                )
                self.hash_map['error_msg'] = error_text
        else:
            self.hash_map.put('selected_cell_id', '')
            self.hash_map.put('cell_name', '')
            self.hash_map.put('selected_cell_name', '')

    def _identify_barcode_balances(self):
        no_data = False
        barcode_data = self.service.get_values_by_field(
            table_name="RS_barcodes",
            field='barcode',
            field_value=self.hash_map.get('barcode')
        )

        if barcode_data:
            self.hash_map.put('item_barcode', self.hash_map.get('barcode'))

            if barcode_data[0].get('id_property'):
                self.hash_map.put('property_id', barcode_data[0].get('id_property'))

            if barcode_data[0].get('id_good'):
                item_id = barcode_data[0]['id_good']

                item_data = self.service.get_values_by_field(
                    table_name="RS_goods",
                    field='id',
                    field_value=item_id
                )

                if item_data[0]:
                    self.hash_map.put('input_item_id', item_id)
                    if item_data[0]['art']:
                        self.hash_map.put('item_art_input', item_data[0]['art'])
                    else:
                        self.hash_map.put('item_art_input', '—')
                    self.hash_map.put('selected_object_name', f'{item_data[0]["name"]},  {item_data[0]["code"]}')
                    self.hash_map.put('error_msg', "")
            self.hash_map.put('from_barcode', True)

        else:
            self.hash_map.put('item_barcode', '')
            cell_data = self.service.get_values_by_field(
                table_name="RS_cells", field='barcode',
                field_value=self.hash_map.get('barcode')
            )

            if cell_data:
                self.hash_map.put('selected_cell_id', cell_data[0]['id'])
                self.hash_map.put('selected_cell_name', cell_data[0]['name'])
                self.hash_map.put('cell_input', cell_data[0]['name'])
                self.hash_map.put('error_msg', "")
            else:
                no_data = True
                self.hash_map.put('object_name', "")
                self.hash_map.put('error_msg', "Штрихкод не распознан")
        if not no_data:
            self._get_balances()

    def _reset_balances_tables(self):
        vars_list = ['wh_select', 'input_item_id', 'cell_input', 'cell_name', 'object_name', 'error_msg',
                     'balances_table', 'barcode', 'selected_cell_id', 'property_id', 'selected_object_name',
                     'selected_wh_id', 'item_barcode', 'selected_wh_name', 'selected_cell_name']
        dict_data = {var: "" for var in vars_list}
        self.hash_map.put_data(dict_data)

    def _set_visibility_on_start(self, elements):
        for v in elements:
            name = f'Show_{v}'
            self.hash_map[name] = '1' if self.hash_map[v] else '-1'

    def _get_balances_data(self):
        data = self.hs_service.get_balances_goods(
            id_good=self.hash_map.get('input_item_id'),
            id_cell=self.hash_map.get('selected_cell_id'),
            id_warehouse=self.hash_map.get('selected_wh_id')
        ).data

        return data

    def _prepare_table_data(self, raw_balances_data):
        table_data = [{}]
        for el in raw_balances_data:
            storage_name = str(el['name_warehouse']) if self.table_type == 'warehouses' else str(el['name_cell'])

            item_layout = self._get_item_table_row_view({
                'storage_name_len': len(storage_name),
                'item_name_len': len(el['name_good'])
            })

            table_row = {
                'key': str(el['id_good']),
                'item_name': str(el['name_good']),
                'storage_name': storage_name,
                'qtty': str(el['qtty']),
                'properties': str(el['name_property'] or '—'),
                '_layout': item_layout
            }

            if self.hash_map.get('property_id'):
                if self.hash_map.get('property_id') == str(el['id_property']):
                    table_data.append(table_row)
            else:
                table_data.append(table_row)

        return table_data

    def _get_balances_table_view(self, data):
        table_view = widgets.CustomTable(
            widgets.LinearLayout(
                self.LinearLayout(
                    self.TextView('Склад') if self.table_type == 'warehouses' else self.TextView('Ячейка'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('Товар'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('Количество'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('Характеристики'),
                    weight=1
                ),
                orientation='horizontal',
                height="match_parent",
                width="match_parent",
                BackgroundColor='#F0F8FF'
            ),

            options=widgets.Options().options,
            tabledata=data
        )

        return table_view

    def _get_item_table_row_view(self, row_data):
        row_view = widgets.LinearLayout(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.LinearLayout(
                        widgets.TextView(
                            Value='@storage_name',
                            TextSize=15,
                            width='match_parent'
                        ),
                        width='match_parent',
                        height='wrap_content'

                    ),
                    width='match_parent',
                    height='match_parent',
                    orientation='horizontal',
                    StrokeWidth=1
                ),
                width='match_parent',
                height='match_parent' if row_data['storage_name_len'] < row_data['item_name_len'] else 'wrap_content',
                weight=1,
                StrokeWidth=1
            ),
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@item_name',
                    TextSize=15,
                    width='match_parent',
                ),
                width='match_parent',
                height='match_parent' if row_data['item_name_len'] < row_data['storage_name_len'] else 'wrap_content',
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
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@properties',
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
            BackgroundColor='#F0F8FF',
        )

        return row_view

    def _check_item_variants(self):
        item_art_input = self.hash_map.get('item_art_input')
        if item_art_input:
            item_values_result = self.service.get_values_by_field(
                table_name='RS_goods', field='art',
                field_value=item_art_input
            )

            if item_values_result:
                if len(item_values_result) > 1:
                    self.hash_map.put('return_selected_data', '')
                    card_title_text_size = self.rs_settings.get('CardTitleTextSize') if self.rs_settings.get(
                        'CardTitleTextSize') else 18

                    variants_cards = widgets.CustomCards(
                        widgets.LinearLayout(
                            widgets.LinearLayout(
                                widgets.TextView(
                                    Value='@name',
                                    width='match_parent',
                                    gravity_horizontal='center',
                                    TextSize=card_title_text_size,
                                    TextColor='#000000'
                                ),
                                orientation='horizontal',
                                width='match_parent',
                            )),
                        options=widgets.Options().options,
                        cardsdata=item_values_result
                    )
                    self.hash_map['item_variants'] = variants_cards.to_json()

                    self.hash_map.show_dialog(
                        listener='Выберите вариант товара:',
                        buttons=['Выбрать', 'Отмена']
                    )

    def _card_click(self):
        card_data = self.hash_map.get('selected_card_data', from_json=True)
        self.hash_map.put_data(
            {
                'selected_object_name': f"{card_data['name']}, {card_data['code']}",
                "input_item_id": card_data['id'], 'item_code': card_data['code'],
                'variant_selected': True
            }
        )
        self.hash_map.remove('new_art')

    def _show_filters(self):
        self.hash_map.put("Show_get_balances_controls", "1")
        self.hash_map.put("Show_show_filters", "-1")

    def _on_back_pressed(self):
        self._reset_balances_tables()
        if self.hash_map.get('return_to_item_card'):
            self.hash_map.put('noRefresh', '')
            self.hash_map.put("FinishProcessResult", "")
        else:
            self.hash_map.put("FinishProcess", "")

    class TextView(widgets.TextView):
        def __init__(self, value):
            super().__init__()
            self.TextSize = '15'
            self.TextBold = True
            self.width = 'match_parent'
            self.Value = value

    class LinearLayout(widgets.LinearLayout):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.orientation = 'horizontal'
            self.height = "match_parent"
            self.width = "match_parent"
            self.StrokeWidth = 1

# ^^^^^^^^^^^^^^^^^^^^^ GoodsBalances ^^^^^^^^^^^^^^^^^^^^^^^^^^^^


# ==================== GoodsPrices =============================

class GoodsPricesItemCard(Screen):
    screen_name = 'CheckPrices'
    process_name = 'Prices'

    def __init__(self, hash_map, screen_data: Dict, **kwargs):
        super().__init__(hash_map, **kwargs)
        self.hash_map_keys = ['input_good_id', 'input_good_art', 'prices_object_name',
                              "return_to_item_card", 'object_name']
        self.screen_data = screen_data
        self.hs_service = HsService(self.get_http_settings())
        self.service = GoodsService()

    def init_screen(self):
        self._update_hash_map_keys()

    def _update_hash_map_keys(self):
        self.hash_map.put_data({key: value for key, value in self.screen_data.items()})

    def on_start(self):
        self._set_visibility_on_start(
            ['prices_error_msg', 'prices_object_name', 'selected_price_type_name',
            'selected_property_name', 'selected_unit_name', 'barcode_info'])

        if not self.hash_map.get('prices_table'):
            self.hash_map.put("Show_get_prices_controls", "1")
            self.hash_map.put("Show_show_filters", "-1")

    def on_input(self):
        listeners = {
            'price_type_select': self._select_item,
            'property_select': self._select_item,
            'unit_select': self._select_item,
            'price_type_select_success': lambda: self._select_item_result('price_type_select'),
            'property_select_success': lambda: self._select_item_result('property_select'),
            'unit_select_success': lambda: self._select_item_result('unit_select'),
            'get_prices_btn': self._get_prices,
            'barcode': self._identify_barcode_prices,
            'show_filters': self._show_filters,
            'ON_BACK_PRESSED': self._on_back_pressed,
        }
        if self.listener in listeners:
            listeners[self.listener]()
        else:
            super().on_input()

    def _select_item(self):
        item_tables = {
            'price_type_select': 'RS_price_types',
            'property_select': 'RS_properties',
            'unit_select': 'RS_units',
        }
        item_type = self.listener

        SelectItemScreen(
            self.hash_map,
            table_name=item_tables[item_type],
            result_listener=f'{item_type}_success',
            parent=self
        ).show()

    def _select_item_result(self, field_name):
        selected_item = self.result_process
        self.hash_map[field_name] = selected_item.get('name') if selected_item else ''

    def _get_prices(self):
        self._validate_input()
        raw_prices_data = self._get_prices_data()
        prices_data = self._prepare_table_data(raw_prices_data)
        prices_table = self._get_prices_table_view(prices_data)
        self.hash_map.put('prices_table', prices_table.to_json())
        self.hash_map.put("Show_get_prices_controls", "-1")
        self.hash_map.put("Show_show_filters", "1")

    def _validate_input(self):
        self._process_input_good_art()
        if not self.hash_map.get('input_good_art'):
            self.hash_map.put('prices_tables', '')
            self.hash_map.put('prices_object_name', '')
            self.hash_map.put('prices_error_msg', "Должен быть выбран товар")
        else:
            self.hash_map.delete('prices_error_msg')

    def _process_input_good_art(self):
        item_art_input = self.hash_map.get('input_good_art')
        put_data = {
            'input_good_id': '',
            'prices_object_name': '',
            'error_msg': ''
        }

        if item_art_input:
            item_values_result = self.service.get_values_by_field(
                table_name='RS_goods', field='art', field_value=item_art_input)[0]

            if item_values_result:
                put_data = {
                    'input_good_id': item_values_result['id'],
                    'good_code': item_values_result['code'],
                    'prices_object_name': f'{item_values_result["name"]},'
                                          f' {item_values_result["code"]}'
                }
            else:
                if item_art_input != '—' and self.hash_map.get('return_to_item_card'):
                    self.hash_map.put('error_msg',
                                      f" Товар с артикулом '{item_art_input}' не найден")

        self.hash_map.put_data(put_data)

    def _identify_barcode_prices(self):
        self.hash_map.put('barcode_info', str(self.hash_map.get('barcode')))
        self.hash_map.put('prices_object_name', '')

        barcode_data = self.service.get_values_by_field(table_name="RS_barcodes", field='barcode',
                                                        field_value=self.hash_map.get('barcode'))
        if not barcode_data:
            self.hash_map.put('object_name', "")
            self.hash_map.put('error_msg', "Штрихкод не распознан")
            return
        barcode_data = barcode_data[0]
        if barcode_data.get('id_property'):
            self.hash_map.put('selected_property_id', barcode_data.get('id_property'))
            selected_property_name = self.service.get_values_by_field(table_name='RS_properties', field='id',
                                                                      field_value=barcode_data.get(
                                                                          'id_property'))
            if selected_property_name:
                self.hash_map.put('selected_property_name', selected_property_name[0].get('name'))
        else:
            self.hash_map.put('selected_property_id', '')
            self.hash_map.put('selected_property_name', '')

        if barcode_data.get('id_good'):
            item_id = barcode_data['id_good']

            item_data = self.service.get_values_by_field(table_name="RS_goods", field='id', field_value=item_id)
            if item_data:

                self.hash_map.put('input_good_id', item_id)
                if item_data[0]['art']:
                    self.hash_map.put('input_good_art', item_data[0]['art'])
                else:
                    self.hash_map.put('input_good_art', '—')
                self.hash_map.put('prices_object_name', item_data[0]['name'])
                self.hash_map.put('error_msg', "")


        self._get_prices()

    def _set_visibility_on_start(self, elements):
        for v in elements:
            name = f'Show_{v}'
            self.hash_map[name] = '1' if self.hash_map[v] else '-1'

    def _get_prices_data(self):
        if not self.hash_map.get('property_select'):
            self.hash_map.put('selected_property_id', '')
            self.hash_map.put('selected_property_name', '')

        data = self.hs_service.get_prices_goods(id_good=self.hash_map.get('input_good_id'),
                                                id_property=self.hash_map.get('selected_property_id'),
                                                id_unit=self.hash_map.get('selected_unit_id'),
                                                id_price_type=self.hash_map.get('selected_price_type_id')).data
        return data

    def _prepare_table_data(self, raw_balances_data):

        table_data = [{}]
        for el in raw_balances_data:
            table_row = {'key': str(el['id_good']),
                         'price_type': str(el['name_price_type']),
                         'price': str(el['price']),
                         'unit': str(el['name_unit']) or '—',
                         'properties': str(el['name_property'] or '—'),
                         '_layout': self._get_item_table_row_view(el)}
            table_data.append(table_row)

        return table_data

    def _get_prices_table_view(self, data):
        table_view = widgets.CustomTable(
            widgets.LinearLayout(
                self.LinearLayout(
                    self.TextView('Тип цены'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('Характеристики'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('Цена'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('Упаковка'),
                    weight=1
                ),
                orientation='horizontal',
                height="match_parent",
                width="match_parent",
                BackgroundColor='#F0F8FF'
            ),

            options=widgets.Options().options,
            tabledata=data
        )

        return table_view

    def _get_item_table_row_view(self, row_data):

        row_view = widgets.LinearLayout(
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@price_type',
                    TextSize=15,
                    width='match_parent'
                ),
                width='match_parent',
                height='match_parent',
                weight=1,
                StrokeWidth=1
            ),
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@properties',
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
                    Value='@price',
                    TextSize=15,
                    width='match_parent'
                ),
                width='match_parent',
                height='match_parent',
                weight=1,
                StrokeWidth=1
            ),
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@unit',
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
            BackgroundColor='#F0F8FF'
        )

        return row_view

    def _show_filters(self):
        self.hash_map.put("Show_get_prices_controls", "1")
        self.hash_map.put("Show_show_filters", "-1")

    def _on_back_pressed(self):
        self._reset_prices_tables()
        self._finish_process_result()

    def _reset_prices_tables(self):
        vars_list = ['input_good_art', 'prices_object_name', 'selected_price_type_id', 'selected_price_type_name',
                     'price_type_select', 'selected_property_id', 'selected_property_name', 'property_select',
                     'selected_unit_id', 'selected_unit_name', 'unit_select', 'prices_custom_table', 'input_good_id',
                     'barcode', 'barcode_info', 'prices_table']
        dict_data = {var: "" for var in vars_list}
        self.hash_map.put_data(dict_data)

    class TextView(widgets.TextView):
        def __init__(self, value):
            super().__init__()
            self.TextSize = '15'
            self.TextBold = True
            self.width = 'match_parent'
            self.Value = value

    class LinearLayout(widgets.LinearLayout):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.orientation = 'horizontal'
            self.height = "match_parent"
            self.width = "match_parent"
            self.StrokeWidth = 1

# ^^^^^^^^^^^^^^^^^^^^^ GoodsPrices ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
