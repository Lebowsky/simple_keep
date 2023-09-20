import re
from abc import ABC, abstractmethod
import json
from json.decoder import JSONDecodeError
import os
from pathlib import Path
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import db_services
import hs_services
import printing_factory
from ui_utils import HashMap, RsDoc, BarcodeWorker, get_ip_address
from db_services import (DocService, ErrorService, GoodsService, BarcodeService, AdrDocService, TimerService,
                         UniversalCardsService, SqlQueryProvider)
from tiny_db_services import ScanningQueueService, TinyNoSQLProvider
from hs_services import HsService
from ru.travelfood.simple_ui import SimpleUtilites as suClass

#import http_exchange
from http_exchange import post_changes_to_server
#from PIL import Image
import widgets
import ui_global
import base64
from java import jclass
noClass = jclass("ru.travelfood.simple_ui.NoSQL")


class Screen(ABC):
    screen_name: str
    process_name: str

    def __init__(self, hash_map: HashMap, rs_settings):
        self.hash_map: HashMap = hash_map
        self.screen_values = {}
        self.rs_settings = rs_settings
        self.listener = self.hash_map['listener']
        self.event: str = self.hash_map['event']

    @abstractmethod
    def on_start(self):
        pass

    @abstractmethod
    def on_input(self):
        pass

    @abstractmethod
    def on_post_start(self):
        pass

    @abstractmethod
    def show(self, args=None):
        pass

    def toast(self, text):
        self.hash_map.toast(text)

    def _is_result_positive(self, listener) -> bool:
        return self.listener == listener and self.event == 'onResultPositive'

    def _is_result_negative(self, listener) -> bool:
        return self.listener == listener and self.event == 'onResultNegative'

    def __str__(self):
        return f'{self.process_name} / {self.screen_name}'

    def _validate_screen_values(self):
        for key, value in self.screen_values.items():
            if value is None:
                raise ValueError(f'Process: {self.process_name}, screen: {self.screen_name}.'
                                 f'For key {key} must be set value not None')

    def get_http_settings(self):
        http_settings = {
            'url': self.rs_settings.get("URL"),
            'user': self.rs_settings.get('USER'),
            'pass': self.rs_settings.get('PASS'),
            'device_model': self.hash_map['DEVICE_MODEL'],
            'android_id': self.hash_map['ANDROID_ID'],
            'user_name': self.rs_settings.get('user_name')}
        return http_settings

    def put_notification(self, text, title=None):
        self.hash_map.notification(text, title)


    @staticmethod
    def delete_template_settings(rs_settings):
        for item in ScreensFactory.screens:
            param_name =  getattr(item, 'printing_template_name', '')
            if param_name and rs_settings.get(param_name):
                rs_settings.delete(param_name)

    def can_launch_timer(self):
        return True

    class TextView(widgets.TextView):
        def __init__(self, value, rs_settings):
            super().__init__()
            self.TextSize = rs_settings.get('DocTypeCardTextSize')
            self.TextColor = '#333333'
            self.BackgroundColor = 'FFCC99'
            self.weight = 0
            self.Value = value

    class LinearLayout(widgets.LinearLayout):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.orientation = 'horizontal'
            self.height = "match_parent"
            self.width = "match_parent"
            self.StrokeWidth = 1


# ==================== Pritnting screens =============================
class HtmlView(Screen):

    screen_name = 'Результат'
    process_name = 'Печать'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.params = json.loads(self.hash_map.get('print_parameters'))
        self.param_name_for_settings = self.hash_map['template_settings_name'] #self.hash_map['current_operation_name'] + '/' + self.hash_map['current_screen_name']
        self.hash_map.put('noRefresh','')

    def on_start(self, ):
        # Если установлен шаблон в настройках печати, ищем его в локальных файлах
        if self.params.get('file_name') and self.params.get('full_path'):
            pass
        else: #Файл шаблона не найден, возвращаемся обратно
            self.hash_map.toast('Не найден файл шаблона')
            self.hash_map.finish_process_result()
            return

        if not (self.params.get('picture_with') and self.params.get('picture_highth')):
            self.params['picture_highth'] = '20'
            self.params['picture_with'] = '20'
            self.hash_map['picture_highth'] = '20'
            self.hash_map['picture_with'] = '20'

        # Список допустимых видов штрихкода
        # barcode_types = ['ean13', 'ean8', 'ean8-guard',  'ean13-guard', 'ean', 'gtin', 'ean14', 'jan', 'upc', 'upca', 'isbn', 'isbn13',
        #  'gs1', 'isbn10', 'issn', 'code39', 'pzn', 'code128', 'itf', 'gs1_128', 'codabar', 'nw-7']
        barcode_types = ['ean13', 'code39', 'code128', 'qr-code']
        self.hash_map.put('barcode_types', ';'.join(barcode_types))
        # self.params['template_folder'], self.params['template'] = self.get_template_by_default(rs_settings= self.rs_settings)
        template_dir, template_file = self.get_template_by_default(self.params)
        html_doc = printing_factory.HTMLDocument(template_dir, template_file).get_template()
        self.hash_map.put('html', html_doc)

        doc_details = self.get_details_data()
        print_parameters = self.hash_map.get('print_parameters')
        if print_parameters:
            print_parameters = json.loads(print_parameters)
            self.fill_knowing_values(doc_details, print_parameters)
        table_data = self._prepare_table_data(doc_details)
        table_view = self._get_doc_table_view(table_data=table_data)
        self.hash_map['matching_table'] = table_view.to_json()

        # Создаем список параметров в виде листа, для последующей передачи в форму выбора

        list_excludes = ('file_name', 'full_path', 'picture_with', 'picture_highth')
        list_fc = [x for x in list(self.params.keys()) if x not in list_excludes]
        list_fc.insert(0,'-пустое значение-')

        list_for_choose = ';'.join(list_fc)
        self.hash_map.put('str_field', list_for_choose)

        #self.hash_map.finish_process_result()


    def get_details_data(self, matching_table=None):
        #Распарсим шаблон и вытащим переменные
        if matching_table:
            return matching_table
        template_dir, template_file = self.get_template_by_default(self.params)
        html_doc_params = printing_factory.HTMLDocument(template_dir, template_file).find_template_variables()

        #Загрузим, настройки соответствия и если их нет то подставим пустые значения
        json_text = self.rs_settings.get(self.param_name_for_settings)
        if json_text:
            saved_template_params = json.loads(json_text)
            dict_lookup = {d['key']: d['value'] for d in saved_template_params}
        else:
            dict_lookup = {}
        return_list = []
        for elem in html_doc_params:
            value = dict_lookup.get(elem, '-пустое значение-')
            return_list.append({'key':elem, 'value':value})

        return return_list

    def fill_knowing_values(self, doc_details, parameters):
        for d in doc_details:
            if d['key'] in parameters.keys():
                d['value'] =  d['key']

    def on_input(self):
        super().on_input()
        if self.listener == 'ON_BACK_PRESSED':
            #self.hash_map.remove('matching_table')
            #self.hash_map.put('run_screen', '2')
            self.hash_map.finish_process_result()

        elif self.listener ==  'btn_cancel':
            #self.hash_map.remove('matching_table')
            #self.hash_map.put('run_screen','2')
            self.hash_map.finish_process_result()

        elif self.listener == 'btn_save':

            jlist = json.loads(self.hash_map.get("matching_table"))
            current_table = jlist['customtable']['tabledata']
            current_table.pop(0)
            for el in current_table:
                if el.get('key'):
                    el.pop('_layout')

            settings_for_wrote = {'full_path' : self.params.get('full_path'),
            'file_name' : self.params.get('file_name'),
            'picture_with':self.hash_map.get('picture_with'),
            'picture_highth': self.hash_map.get('picture_highth'),
            'print_params' : current_table }

            current_table_json = json.dumps(settings_for_wrote)

            self.rs_settings.put(self.param_name_for_settings, current_table_json, False)  #current_table_json
            #self.hash_map.remove('matching_table')
            #self.hash_map.put('run_screen','2')
            self.hash_map.finish_process_result()

        elif self.listener == "TableClick" or self.listener =='CardsClick':
                current_str = self.hash_map.get("selected_card_position")
                jlist = json.loads(self.hash_map.get("matching_table"))
                current_elem = jlist['customtable']['tabledata'][int(current_str)]
                name = str(current_elem['key'])
                self.hash_map.put("field", name)
                self.hash_map.put('list_field', str(self.hash_map.get('str_field')))
                self.hash_map.put('ShowDialog', 'НастройкаСоответствияДиалог')
                self.hash_map.put("ShowDialogStyle",
                            json.dumps({"title": name, "yes": "Да", "no": "Нет"}))

        elif self.hash_map.get("event") == 'onResultPositive':
            key_card = int(self.hash_map.get('selected_card_position'))

            jrecord = json.loads(self.hash_map.get("matching_table"))
            rec = jrecord['customtable']['tabledata'][key_card]
            # for elem in rec:
            #     if elem.get('key') == key_card:
            rec['value'] = self.hash_map.get('select_field')
            #self._set_background_row_color(rec)
            self.hash_map.put("matching_table", json.dumps(jrecord, ensure_ascii=False).encode('utf8').decode())
            self.hash_map.refresh_screen()

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    @staticmethod
    def get_template_by_default(print_params: dict):

        file_name = ''
        if 'full_path' not in print_params:
            raise ValueError("Ключа 'full_path' не найдено в настройках.")
        else:
            file_name = print_params['full_path']

        if file_name and os.path.exists(file_name):
            return os.path.split(file_name)
        else:
            #return os.path.split(file_name) #DEBUG, must delete
            raise ValueError(f'Файл шаблона {file_name} не найден')



    def _prepare_table_data(self, details):
        table_data = [{}]
        for record in details:
            product_row = {'key': str(record['key']), 'value': str(record['value']),
                           '_layout': self._get_doc_table_row_view()}

            self._set_background_row_color(product_row)

            # if self._added_goods_has_key(product_row['key']):
            #     table_data.insert(1, product_row)
            # else:
            table_data.append(product_row)

        return table_data

    def _get_doc_table_view(self, table_data):
        table_view = widgets.CustomTable(
            widgets.LinearLayout(
                self.LinearLayout(
                    self.TextView('Ключ', self.rs_settings),
                    weight=3
                ),
                self.LinearLayout(
                    self.TextView('Значение', self.rs_settings),
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

    def _get_doc_table_row_view(self):
        row_view = widgets.LinearLayout(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.LinearLayout(
                        self.TextView('@key', self.rs_settings),

                        width='match_parent',
                    ),
                    width='match_parent',
                    orientation='horizontal',
                    StrokeWidth=1
                ),
                width='match_parent',
                weight=3,
                StrokeWidth=1
            ),
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@value',
                    TextSize=15,
                    width='match_parent',
                ),
                width='match_parent',
                height='match_parent',
                weight=1,
                StrokeWidth=1
            ),
            orientation='horizontal',
            width='match_parent',
            BackgroundColor='#FFFFFF'
        )

        return row_view


    def _set_background_row_color(self, product_row):
        background_color = '#FBE9E7' #FBE9E7  "#FFF9C4"
        value = product_row['value']

        if value:
            background_color = "#FFFFFF"

        product_row['_layout'].BackgroundColor = background_color

    @staticmethod
    def show_screen(hash_map, data_for_printing):
        if data_for_printing:
            hash_map.put('print_parameters', json.dumps(data_for_printing))
            # if self.params:
            hash_map.show_process_result('Печать', 'Результат')

    @staticmethod
    def print_from_any_screen(hash_map, rs_settings, template_name, data_for_printing):
        if not data_for_printing:
            return
        else:
            str_table_view = rs_settings.get(template_name)
            if str_table_view:  #Нашли настройки для вызвавшего экрана
                params_match = json.loads(str_table_view)
                data_for_printing = HtmlView.replase_params_names(data_for_printing, params_match.get('print_params'))
                template_directory, template_file  = HtmlView.get_template_by_default(params_match)
                #hash_map.toast(f'Путь:{template_directory}  Файл:{template_file}')
                htmlresult = printing_factory.HTMLDocument(template_directory, template_file).create_html(data_for_printing)
                htmlresult = printing_factory.HTMLDocument.inject_css_style(htmlresult, params_match)
                # with open(suClass.get_temp_dir() + '//template.html', 'w', encoding='utf-8') as file:
                #     file.write(htmlresult)
                # self.params['template'],self.params['template_folder']

                hash_map.put("PrintPreview", htmlresult)

            else:  #Вызываем этот экан средствами симпла, для настройки параметров
                hash_map.put('print_parameters', json.dumps(data_for_printing))
                hash_map['template_settings_name'] = template_name
                #hash_map.show_process_result('Печать', 'Результат')
                hash_map.show_process_result('Печать', 'Список шаблонов')


    @staticmethod
    def replase_params_names(data_for_printing, params_match):
        new_data = {}

        for match in params_match:
            if match['value'] in data_for_printing.keys():
                new_key = match['key']
                new_value = data_for_printing[match['value']]
                new_data[new_key] = new_value
        return new_data


class TemplatesList(Screen):
    screen_name = 'Список шаблонов'
    process_name = 'Печать'

    def __init__(self,hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)

        self.hs_service = HsService(self.get_http_settings())
        self.print_parameters = json.loads(self.hash_map.get('print_parameters'))


    def on_start(self):
        current_template_js = self.rs_settings.get('current_template')
        if current_template_js:
            current_template = json.loads(current_template_js) if current_template_js else None
            if current_template:
                self.hash_map.put('current_template', current_template.get('name') or '')
            else:
                self.hash_map.put('current_template','-не определено-')
        else:
            self.hash_map.put('current_template', '-не определено-')

        target_dir = suClass.get_temp_dir()
        list_data = self.get_all_files_from_patch(target_dir)

        doc_cards = self._get_doc_cards_view(list_data)
        self.hash_map['templates_cards'] = doc_cards.to_json()


    def on_input(self):
        if self.listener == 'ON_BACK_PRESSED':
            self.hash_map.finish_process_result()
        elif self.listener == 'btn_get_http_templates':
            self.get_from_server_write_on_disc()
        elif self.hash_map.get('onClick')== 'btn_get_http_templates':
            self.get_from_server_write_on_disc()
            self.hash_map.put('onClick','')
        elif self.listener == 'LayoutAction':
            self._layout_action()
        elif self.listener == 'CardsClick':

            #selected_card = json.loads(self.hash_map.get('selected_card_data'))
            current_str = self.hash_map.get("selected_card_position")
            jlist = json.loads(self.hash_map.get("templates_cards"))
            selected_card = jlist['customcards']['cardsdata'][int(current_str)]

            if selected_card and isinstance(selected_card, dict):
                self.print_parameters['file_name'] = selected_card.get('file_name')
                self.print_parameters['full_path'] = selected_card.get('full_path')
                self.hash_map.put('print_parameters', json.dumps(self.print_parameters))
                # self.rs_settings.put('current_template',json.dumps(file_parameters),False)

                self.hash_map.put('current_template', selected_card.get('file_name'))

                # self.delete_template_settings(self.rs_settings)
                self.hash_map.show_screen('Результат')  # .show_process_result('Печать', 'Результат')


    def on_post_start(self):
        pass


    def show(self):
        pass


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

    @staticmethod
    def correct_filename(filename):

        illegal_chars = ['<', '>', ':', '"',"'", '/', '\\', '|', '?', '*', "<", ">", '\x00']
        for char in illegal_chars:
            filename = filename.replace(char, '')
        return filename


    def get_from_server_write_on_disc(self):
        answer = self.hs_service.get_templates()
        output_folder = suClass.get_temp_dir()
        #self.hash_map.notification(output_folder,'Путь',True)
        # Create the output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        if answer['status_code'] == 200:
            data_list = answer['data']
        else:
            reason = answer['error_pool']
            raise f'Ошибка соединения с сервером: {reason}'

        for data_dict in data_list:
            file_name = self.correct_filename(data_dict['name']) + '.htm'
            file_path = os.path.join(output_folder, file_name)

            # Decode the BASE64 encoded HTML data
            #html_data = printing_factory.HTMLDocument(file_name, file_path).inject_css_style(base64.b64decode(data_dict['html']).decode('utf-8'))

            # Write the HTML data to the file
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(base64.b64decode(data_dict['html']).decode('utf-8'))
            except:
                raise f'Ошибка сохранения файла {file_path}'
        #     print(f'Saved {file_name}')
        #
        # print('All files saved.')


    @staticmethod
    def get_all_files_from_patch(folder_path, mask=''):

        html_files_info = []

        # Walk through the folder and its subdirectories
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

        # print(html_files_info)
        return html_files_info

    def _layout_action(self):
        selected_card = None
        if self.hash_map.get('layout_listener') == 'Задать по умолчанию':
            selected_card = json.loads(self.hash_map.get('card_data'))

            if selected_card and isinstance(selected_card, dict):
                self.print_parameters['file_name'] = selected_card.get('file_name')
                self.print_parameters['full_path'] = selected_card.get('full_path')
                self.hash_map.put('print_parameters', json.dumps(self.print_parameters))
                # self.rs_settings.put('current_template',json.dumps(file_parameters),False)

                self.hash_map.put('current_template', selected_card.get('file_name'))

                # self.delete_template_settings(self.rs_settings)
                self.hash_map.show_screen('Результат')  # .show_process_result('Печать', 'Результат')


class SimpleFileBrowser(Screen):
    screen_name = 'Список файлов'
    process_name = 'Проводник'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.hs_service = hs_services.DebugService(ip_host=self.hash_map.get('ip_host'))  # '192.168.1.77'

    def on_start(self):
        if not self.hash_map.get('current_dir'):
            self.hash_map['current_dir'] = suClass.get_temp_dir()
        target_dir = self.hash_map.get('current_dir')
        list_data = self.get_all_files_from_patch(target_dir)

        doc_cards = self._get_doc_cards_view(list_data)
        self.hash_map['templates_cards'] = doc_cards.to_json()

    def on_input(self):
        current_directory = Path(self.hash_map.get('current_dir'))
        if self.listener == 'ON_BACK_PRESSED':
            self.hash_map.finish_process()

        elif self.listener == 'btn_get_up':
            current_directory = current_directory.parent
            self.hash_map['current_dir'] = current_directory
            self.on_start()
            self.hash_map.refresh_screen()
        elif self.listener == 'CardsClick':
            current_str = self.hash_map.get("selected_card_position")
            jlist = self.hash_map.get_json("templates_cards")
            current_elem = jlist['customcards']['cardsdata'][int(current_str)]
            if current_elem['item_type'] == 'Folder':
                self.hash_map['current_dir'] = current_directory / current_elem['file_name']
                self.hash_map.refresh_screen()


        elif self.listener == 'LayoutAction':
            self._layout_action()

    def on_post_start(self):
        pass

    def show(self):
        pass

    def _get_doc_cards_view(self, table_data):

        card_title_text_size = self.rs_settings.get('CardTitleTextSize')
        card_date_text_size = self.rs_settings.get('CardDateTextSize')

        doc_cards = widgets.CustomCards(
            widgets.LinearLayout(

                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@picture',
                        TextBold=False,
                        TextSize=card_title_text_size,
                        weight=1
                    ),
                    widgets.TextView(
                        Value='@file_name',
                        TextBold=True,
                        TextSize=card_title_text_size,
                        weight=3
                    ),
                    widgets.PopupMenuButton(
                        Value='Передать на ББ',
                        Variable="sent",
                        gravity_horizontal='right',
                        weight=1
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

    @staticmethod
    def get_all_files_from_patch(directory):

        files_info = []
        # Walk through the folder and its subdirectories
        directory_path = Path(directory)
        items = [item for item in directory_path.iterdir()]

        for item in items:
            file_path = item.name
            item_type = "File" if item.is_file() else "Folder"

            file_size_kb = item.stat().st_size / 1024  # Convert bytes to kilobytes
            creation_time = item.stat().st_ctime
            formatted_creation_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(
                int(creation_time)))  # Format datetime for user eyes ))
            pic = '#f15b' if item.is_file() else '#f07b'
            if item.is_symlink():
                pic = '#f0c1'

            file_info = {
                'picture': pic,
                'item_type': item_type,
                'full_path': str(directory_path.joinpath(file_path)),
                'file_name': file_path,
                'file_size': f'{file_size_kb:.2f} KB',  # Format file size with 2 decimal places
                'creation_time': formatted_creation_time
            }
            files_info.append(file_info)

        # print(html_files_info)
        return files_info

    def _layout_action(self):
        if self.hash_map.get('layout_listener') == 'Передать на ББ':

            selected_card = json.loads(self.hash_map.get('card_data'))
            if selected_card and isinstance(selected_card, dict):
                file = Path(selected_card['full_path'])
                if file.is_file():
                    self._copy_file(file)

    def _copy_file(self, file):
        ip_host = self.hash_map.get('ip_host')  # '192.168.1.77'

        with open(file, 'rb') as f:
            # send_service = self.hs_service(ip_host)
            res = self.hs_service.export_file(file.name, f)

            if res['status_code'] == 200:
                self.hash_map.toast(f'Файл {file.name} успешно выгружен')
            else:
                self.hash_map.toast('Ошибка соединения')


# ^^^^^^^^^^^^^^^^^^^^^ Pritnting screens ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== Tiles =============================

class Tiles(Screen):
    def on_start(self):
        pass

    def on_input(self):
        pass

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _get_tile_row(self, layout, tile_element, start_screen='Документы'):
        tile = {
            "layout": layout,
            "data": self._get_tile_data(tile_element),
            "height": "wrap_content",
            "color": '#FFFFFF',
            "start_screen": f"{start_screen}",
            "start_process": "",
            'key': tile_element['docType']
        }
        return tile

    def _get_message_tile(self, message, text_color='#000000'):
        tile_view = widgets.LinearLayout(
            widgets.TextView(
                Value='@no_data',
                TextSize=self.rs_settings.get('titleDocTypeCardTextSize'),
                TextColor=text_color,
                height='match_parent',
                width='match_parent',
                weight=0,
                gravity_horizontal="center",
                gravity_vertical="center",
                StrokeWidth=0,
                BackgroundColor="#ffffff",
                Padding=0

            ),
            width='match_parent',
            autoSizeTextType='uniform',
            weight=0,
            height='match_parent',
            gravity_horizontal="center",
            gravity_vertical="center",
            StrokeWidth=3,
            BackgroundColor="#ffffff",
            Padding=0
        )

        layout = json.loads(tile_view.to_json())

        tiles_list = [{
            "layout": layout,
            "data": {"no_data": message},
            "height": "wrap_content",
            "color": '#ffffff',
            "start_screen": "",
            "start_process": "",
            'StrokeWidth': '',
        }]

        count_row_elements = 1
        tiles = {
            'tiles': [tiles_list],
            'background_color': '#ffffff',
            'StrokeWidth': '',
            'height': ''

        }

        return tiles

    @staticmethod
    def _get_tile_data(tile_element):
        count_verified = tile_element['count_verified'] or 0
        count_unverified = tile_element['count_unverified'] or 0
        qtty_plan_verified = tile_element['qtty_plan_verified'] or 0
        qtty_plan_unverified = tile_element['qtty_plan_unverified'] or 0

        return {
            "docName": tile_element['docType'],
            'QttyOfDocs': '{}/{}'.format(tile_element['count'], tile_element['verified']),
            'count_verified': '{}/{}'.format(
                count_verified + count_unverified,
                count_unverified),
            'qtty_plan_verified': '{}/{}'.format(
                qtty_plan_verified + qtty_plan_unverified,
                qtty_plan_unverified)
        }

    def _get_tile_view(self) -> widgets.LinearLayout:
        tiles_view = widgets.LinearLayout(
            widgets.TextView(
                Value='@docName',
                TextSize=self.rs_settings.get('titleDocTypeCardTextSize'),
                TextColor='#000000',
                width='match_parent',
                weight=0
            ),
            widgets.LinearLayout(
                self.TextView('@QttyOfDocs', self.rs_settings),
                orientation='horizontal',
                width="match_parent",
                weight=1
            ),
            widgets.LinearLayout(
                self.TextView('Строк: ', self.rs_settings),
                self.TextView('@count_verified', self.rs_settings),
                orientation='horizontal',
                width="match_parent",
                weight=1
            ),
            widgets.LinearLayout(
                self.TextView('Товаров: ', self.rs_settings),
                self.TextView('@qtty_plan_verified', self.rs_settings),
                orientation='horizontal',
                width="match_parent",
                weight=1
            ),
            width='match_parent',
            autoSizeTextType='uniform',
            weight=0
        )

        return tiles_view

    class TextView(widgets.TextView):
        def __init__(self, value, rs_settings):
            super().__init__()
            self.TextSize = rs_settings.get('DocTypeCardTextSize')
            self.TextColor = '#333333'
            self.BackgroundColor = 'FFCC99'
            self.weight = 0
            self.Value = value


class FlowTilesScreen(Tiles):
    screen_name = 'Плитки'
    process_name = 'Сбор ШК'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.db_service = DocService()

    def on_start(self) -> None:

        data = self.db_service.get_doc_flow_stat()
        if data:
            # layout = self._get_tile_view()
            layout = json.loads(self._get_tile_view().to_json())

            tiles_list = [self._get_tile_row(layout, item) for item in data]

            # split list by two element in row
            count_row_elements = 2
            tiles = {
                'tiles': [
                    tiles_list[i:i + count_row_elements]
                    for i in range(0, len(tiles_list), count_row_elements)
                ],
                'background_color': '#f5f5f5'

            }
        else:
            tiles = self._get_message_tile("Нет загруженных документов")

        self.hash_map.put('tiles', tiles, to_json=True)
        self.hash_map.refresh_screen()

    def on_input(self) -> None:
        super().on_input()
        if self.listener == 'ON_BACK_PRESSED':
            self.hash_map.put('FinishProcess', '')
        # elif self.listener == 'CardsClick':
        #     self.hash_map.show_screen('Документы')

    def _get_tile_view(self) -> widgets.LinearLayout:
        tiles_view = widgets.LinearLayout(
            widgets.TextView(
                Value='@docName',
                TextSize=self.rs_settings.get('titleDocTypeCardTextSize'),
                TextColor='#000000',
                width='match_parent',
                weight=0
            ),
            widgets.LinearLayout(
                self.TextView('@QttyOfDocs', self.rs_settings),
                orientation='horizontal',
                width="match_parent",
                weight=1
            ),
            widgets.LinearLayout(
                self.TextView('Строк: ', self.rs_settings),
                self.TextView('@barc_count', self.rs_settings),
                orientation='horizontal',
                width="match_parent",
                weight=1
            ),

            width='match_parent',
            autoSizeTextType='uniform',
            weight=0
        )

        return tiles_view

    def _get_tile_row(self, layout, tile_element, start_screen='Документы'):
        tile = {
            "layout": layout,
            "data": self._get_tile_data(tile_element),
            "height": "wrap_content",
            "color": '#FFFFFF',
            "start_screen": f"{start_screen}",
            "start_process": "",
            'key': tile_element['docType']
        }
        return tile

    @staticmethod
    def _get_tile_data(tile_element):
        count_verified = tile_element['verified'] or 0
        # count_unverified = tile_element['count_unverified'] or 0
        barc_count = tile_element['barc_count'] or 0

        return {
            "docName": tile_element['docType'],
            'QttyOfDocs': '{}/{}'.format(tile_element['count'], tile_element['verified']),
            'count_verified': str(count_verified),
            'barc_count': str(barc_count)
        }


class GroupScanTiles(Tiles):
    screen_name = 'Плитки'
    process_name = 'Групповая обработка'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.db_service = DocService()
        self.screen_name = self.hash_map.get_current_screen()
        self.process_name = self.hash_map.get_current_process()

    def on_start(self) -> None:
        if not self.hash_map.containsKey('check_connection') and not self._check_connection():
            tiles = self._get_message_tile("Отсутствует соединение с сервером", text_color="#ff0000")
            self.hash_map.put('tiles', tiles, to_json=True)
            self.hash_map.refresh_screen()
            self.hash_map['check_connection'] = False
            return

        self.hash_map['check_connection'] = True

        data = self.db_service.get_docs_stat()
        if data:
            layout = json.loads(self._get_tile_view().to_json())

            tiles_list = [self._get_tile_row(layout, item) for item in data]

            # split list by two element in row
            count_row_elements = 2
            tiles = {
                'tiles': [
                    tiles_list[i:i + count_row_elements]
                    for i in range(0, len(tiles_list), count_row_elements)
                ],
                'background_color': '#f5f5f5'

            }
        else:
            tiles = self._get_message_tile("Нет загруженных документов")

        self.hash_map.put('tiles', tiles, to_json=True)
        self.hash_map.refresh_screen()

    def on_input(self) -> None:
        super().on_input()
        if self.listener == 'ON_BACK_PRESSED':
            self.hash_map.put('FinishProcess', '')

    def on_post_start(self):
        pass

    def show(self, args=None):
        self.hash_map.show_screen(self.screen_name, args)

    def _check_connection(self):
        hs_service = hs_services.HsService(self.get_http_settings())
        try:
            hs_service.communication_test(timeout=1)
            answer = hs_service.http_answer
        except Exception as e:
            answer = hs_service.HttpAnswer(
                error=True,
                error_text=str(e.args[0]),
                status_code=404,
                url=hs_service.url)
        return not answer.error


class DocumentsTiles(GroupScanTiles):
    screen_name = 'Плитки'
    process_name = 'Документы'

    def on_start(self):
        super().on_start()

    def _check_connection(self):
        return True


# ^^^^^^^^^^^^^^^^^^^^^ Tiles ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== DocsList =============================


class DocsListScreen(Screen):
    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = DocService()
        self.screen_values = {}
        self.popup_menu_data = ''

    def on_start(self) -> None:
        doc_types = self.service.get_doc_types()
        self.hash_map['doc_type_select'] = ';'.join(['Все'] + doc_types)
        self.hash_map['doc_status_select'] = 'Все;К выполнению;Выгружен;К выгрузке'

        doc_type = self.hash_map['selected_tile_key'] or self.hash_map['doc_type_click']
        doc_status = self.hash_map['selected_doc_status']
        self.hash_map['doc_type_click'] = doc_type
        self.hash_map['selected_tile_key'] = ''

        list_data = self._get_doc_list_data(doc_type, doc_status)
        self.hash_map['return_selected_data'] = ''
        doc_cards = self._get_doc_cards_view(list_data, self.popup_menu_data)
        self.hash_map['docCards'] = doc_cards.to_json()

    def on_input(self) -> None:
        super().on_input()
        if self.listener == "doc_status_click":
            self.hash_map['selected_doc_status'] = self.hash_map["doc_status_click"]

        elif self.listener == 'LayoutAction':
            self._layout_action()

        elif self._is_result_positive('confirm_delete'):
            self.confirm_delete_doc_listener()

        elif self.listener == 'ON_BACK_PRESSED':
            self.hash_map.show_screen('Плитки')

    def on_post_start(self):
        pass

    def show(self, args=None):
        self._validate_screen_values()
        self.hash_map.show_screen(self.screen_name, args)

    def _layout_action(self) -> None:
        layout_listener = self.hash_map['layout_listener']

        if layout_listener == 'Удалить':
            self.hash_map.show_dialog(
                listener='confirm_delete',
                title='Удалить документ с устройства?'
            )
        elif layout_listener == 'Очистить данные пересчета':
            self.hash_map.show_dialog(
                listener='confirm_clear_barcode_data',
                title='Очистить данные пересчета?'
            )
        elif layout_listener == 'Отправить повторно':
            self.hash_map.show_dialog(
                listener='confirm_resend_doc',
                title='Отправить документ повторно?'
            )

    def _get_doc_list_data(self, doc_type='', doc_status='') -> list:
        results = self.service.get_doc_view_data(doc_type, doc_status)
        table_data = []

        for record in results:
            doc_status = ''

            if record['verified'] and record['sent']:
                doc_status = 'Выгружен'
            elif record['verified']:
                doc_status = 'К выгрузке'
            elif not (record['verified'] and record['sent']):
                doc_status = 'К выполнению'

            table_data.append({
                'key': record['id_doc'],
                'type': record['doc_type'],
                'number': record['doc_n'],
                'data': record['doc_date'],
                'warehouse': record['RS_warehouse'],
                'countragent': record['RS_countragent'],
                'add_mark_selection': record['add_mark_selection'],
                'status': doc_status
            })

        return table_data

    def _get_doc_cards_view(self, table_data, popup_menu_data):
        title_text_size = self.rs_settings.get("TitleTextSize")
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')
        card_date_text_size = self.rs_settings.get('CardDateTextSize')

        doc_cards = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@status',
                        width='match_parent',
                        gravity_horizontal='left',
                        weight=2
                    ),
                    widgets.TextView(
                        Value='@type',
                        TextSize=title_text_size,
                    ),
                    widgets.PopupMenuButton(
                        Value=popup_menu_data,
                        Variable="menu_delete",
                    ),

                    orientation='horizontal',
                    width='match_parent',

                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@number',
                        TextBold=True,
                        TextSize=card_title_text_size
                    )
                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@countragent',
                        TextSize=card_date_text_size
                    ),
                    widgets.TextView(
                        Value='@warehouse',
                        TextSize=card_date_text_size
                    )
                ),
                width="match_parent"
            ),
            options=widgets.Options().options,
            cardsdata=table_data
        )

        return doc_cards

    def _get_selected_card_put_data(self, put_data=None):
        card_data = self.hash_map.get("selected_card_data", from_json=True)

        put_data = put_data or {}
        put_data['id_doc'] = card_data['key']
        put_data['doc_type'] = card_data['type']
        put_data['doc_n'] = card_data['number']
        put_data['doc_date'] = card_data['data']
        put_data['warehouse'] = card_data['warehouse']
        put_data['countragent'] = card_data['countragent']

        return put_data

    def _set_doc_verified(self, id_doc, value=True):
        # service = DocService(id_doc)
        value = str(int(value))

        try:
            self.service.set_doc_value('verified', value)
        except Exception as e:
            self.hash_map.error_log(e.args[0])

    def doc_delete(self, id_doc):

        result = True

        try:
            self.service.delete_doc(id_doc)
        except Exception as e:
            self.hash_map.error_log(e.args[0])
            result = False

        return result

    def get_docs_count(self, doc_type=''):
        doc_type = '' if not doc_type or doc_type == 'Все' else doc_type
        return self.service.get_docs_count(doc_type)

    def _clear_barcode_data(self, id_doc):
        return self.service.clear_barcode_data(id_doc)

    def confirm_delete_doc_listener(self):
        card_data = self.hash_map.get_json("card_data")
        id_doc = card_data['key']
        doc_type = self.hash_map['doc_type_click']

        if self.doc_delete(id_doc):
            docs_count = self.get_docs_count(doc_type=doc_type)
            self.hash_map.toast('Документ успешно удалён')
            if docs_count:
                self.on_start()
            else:
                self.hash_map.show_screen('Плитки')
        else:
            self.hash_map.toast('Ошибка удаления документа')

    def get_id_doc(self):
        card_data = self.hash_map.get_json("card_data") or {}
        id_doc = card_data.get('key') or self.hash_map['selected_card_key']
        return id_doc


class GroupScanDocsListScreen(DocsListScreen):
    screen_name = 'Документы'
    process_name = 'Групповая обработка'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.popup_menu_data = 'Удалить'

    def on_start(self):
        super().on_start()

    def on_input(self):
        super().on_input()
        if self.listener == "CardsClick":
            self.hash_map.show_dialog('Подтвердите действие')
            selected_card_key = self.hash_map['selected_card_key']
            self.hash_map['id_doc'] = selected_card_key

        elif self._is_result_positive('Подтвердите действие'):
            id_doc = self.hash_map['id_doc']
            self.service.doc_id = id_doc
            self.service.set_doc_value('verified', 1)

            screen_name = 'Документ товары'
            screen = ScreensFactory.create_screen(
                screen_name=screen_name,
                process=self.process_name,
                hash_map=self.hash_map,
                rs_settings=self.rs_settings)

            screen.show(args=self._get_selected_card_put_data())

    def can_launch_timer(self):
        return False

class DocumentsDocsListScreen(DocsListScreen):
    screen_name = 'Документы'
    process_name = 'Документы'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service.docs_table_name = 'RS_docs'
        self.popup_menu_data = ';'.join(
            ['Удалить', 'Очистить данные пересчета', 'Отправить повторно'])

    def on_start(self):
        super().on_start()

    def on_input(self):
        super().on_input()

        if self.listener == "CardsClick":
            id_doc = self.get_id_doc()
            self.hash_map['id_doc'] = id_doc
            # id_doc = self.hash_map['selected_card_key']
            self.service.doc_id = id_doc

            screen_name = 'Документ товары'
            screen = ScreensFactory.create_screen(
                screen_name=screen_name,
                process=self.process_name,
                hash_map=self.hash_map,
                rs_settings=self.rs_settings)

            screen.show(args=self._get_selected_card_put_data())

        elif self._is_result_positive('confirm_clear_barcode_data'):
            id_doc = self.get_id_doc()
            res = self._clear_barcode_data(id_doc)
            if res.get('result'):
                self.toast('Данные пересчета и маркировки очищены')
                self.service.set_doc_status_to_upload(id_doc)
            else:
                self.toast('При очистке данных пересчета возникла ошибка.')
                self.hash_map.error_log(res.get('error'))

        elif self._is_result_positive('confirm_resend_doc'):
            id_doc = self.get_id_doc()
            http_params = self.get_http_settings()
            answer = post_changes_to_server(f"'{id_doc}'", http_params)
            if answer.get('Error') is not None:
                ui_global.write_error_on_log(f'Ошибка повторной отправки документа {self.get_doc_number()}: '
                                             f'{str(answer.get("Error"))}')
                self.put_notification(text=f'Ошибка при отправке документа {self.get_doc_number()}, '
                                           f'подробнее в логе ошибок.')
                self.toast('Не удалось отправить документ повторно')
            else:
                self.service.doc_id = id_doc
                self.service.set_doc_value('sent', 1)
                self.toast('Документ отправлен повторно')

    def get_id_doc(self):
        card_data = self.hash_map.get_json("card_data") or {}
        id_doc = card_data.get('key') or self.hash_map['selected_card_key']
        return id_doc

    def get_doc_number(self):
        card_data = self.hash_map.get_json("card_data") or {}
        doc_number = card_data.get('number')
        return doc_number


class AdrDocsListScreen(DocsListScreen):
    screen_name = 'Документы'
    process_name = 'Адресное хранение'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = AdrDocService()
        self.service.docs_table_name = 'RS_adr_docs'
        self.service.details_table_name = 'RS_adr_docs_table'
        self.screen_values = {}
        self.listener = self.hash_map['listener']
        self.event = self.hash_map['event']

    def on_start(self) -> None:
        doc_types = self.service.get_doc_types()
        self.hash_map['doc_adr_type_select'] = ';'.join(['Все', 'Отбор', 'Размещение', 'Перемещение'])
        self.hash_map['doc_status_select'] = 'Все;К выполнению;Выгружен;К выгрузке'

        doc_type = self.hash_map['doc_type_click']
        if not doc_type:
            doc_type = 'Все'
            self.hash_map['doc_type_click'] = doc_type
        doc_status = self.hash_map['selected_doc_status']
        if not doc_status:
            doc_status = 'Все'
            self.hash_map['selected_doc_status'] = doc_status
        # self.hash_map['doc_type_click'] = doc_type
        self.hash_map['selected_tile_key'] = ''
        list_data = self._get_doc_list_data(doc_type, doc_status)
        doc_cards = self._get_doc_cards_view(list_data,
                                             popup_menu_data='Удалить;Очистить данные пересчета;Отправить повторно')
        self.hash_map['docAdrCards'] = doc_cards.to_json()

    def on_input(self) -> None:
        super().on_input()
        if self.listener == "doc_status_click":
            self.hash_map['selected_doc_status'] = self.hash_map["doc_status_click"]

        elif self.listener == 'LayoutAction':
            self._layout_action()

        elif self._is_result_positive('confirm_delete'):
            self.confirm_delete_doc_listener()

        elif self.listener == "CardsClick":
            args = self._get_selected_card_put_data()

            screen = AdrDocDetailsScreen(self.hash_map, self.rs_settings)
            screen.show(args=args)

        elif self.listener == "doc_adr_type_click":
            self.hash_map['doc_type_click'] = self.hash_map['doc_adr_type_click']

        elif self.listener == 'ON_BACK_PRESSED':
            self.hash_map.finish_process()

        elif self.listener == 'confirm_clear_barcode_data':

            self._clear_barcode_data(self.get_id_doc())

    def _layout_action(self) -> None:
        layout_listener = self.hash_map['layout_listener']

        if layout_listener == 'Удалить':
            self.hash_map.show_dialog(
                listener='confirm_delete',
                title='Удалить документ с устройства?'
            )
        elif layout_listener == 'Очистить данные пересчета':
            self.hash_map.show_dialog(
                listener='confirm_clear_barcode_data',
                title='Очистить данные пересчета?'
            )
        elif layout_listener == 'Отправить повторно':
            self.hash_map.show_dialog(
                listener='confirm_resend_doc',
                title='Отправить документ повторно?'
            )

    def _get_doc_list_data(self, doc_type='', doc_status='') -> list:
        results = self.service.get_doc_view_data(doc_type, doc_status)
        table_data = []

        for record in results:
            doc_status = ''

            if record['verified'] and record['sent']:
                doc_status = 'Выгружен'
            elif record['verified']:
                doc_status = 'К выгрузке'
            elif not (record['verified'] and record['sent']):
                doc_status = 'К выполнению'

            table_data.append({
                'key': record['id_doc'],
                'type': record['doc_type'],
                'number': record['doc_n'],
                'data': record['doc_date'],
                'warehouse': record['RS_warehouse'],
                'add_mark_selection': record['add_mark_selection'],
                'status': doc_status
            })

        return table_data

    def _get_doc_cards_view(self, table_data, popup_menu_data):
        title_text_size = self.rs_settings.get("TitleTextSize")
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')
        card_date_text_size = self.rs_settings.get('CardDateTextSize')

        doc_cards = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@status',
                        width='match_parent',
                        gravity_horizontal='left',
                        weight=2
                    ),
                    widgets.TextView(
                        Value='@type',
                        TextSize=title_text_size,
                    ),
                    widgets.PopupMenuButton(
                        Value=popup_menu_data,
                        Variable="menu_delete",
                    ),

                    orientation='horizontal',
                    width='match_parent',

                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@number',
                        TextBold=True,
                        TextSize=card_title_text_size
                    )
                ),
                widgets.LinearLayout(

                    widgets.TextView(
                        Value='@warehouse',
                        TextSize=card_date_text_size
                    )
                ),

                width="match_parent"
            ),
            options=widgets.Options().options,
            cardsdata=table_data
        )

        return doc_cards

    def _doc_delete(self, id_doc):
        result = True
        try:
            self.service.delete_adr_doc(id_doc)
        except Exception as e:
            self.hash_map.error_log(e.args[0])
            result = False

        return result

    def _get_selected_card_put_data(self, put_data=None):
        card_data = self._get_selected_card()

        put_data = put_data or {}
        put_data['id_doc'] = card_data['key']
        put_data['doc_type'] = card_data['type']
        put_data['doc_n'] = card_data['number']
        put_data['doc_date'] = card_data['data']
        put_data['warehouse'] = card_data['warehouse']

        return put_data

    def _get_docs_count(self, doc_type=''):
        doc_type = '' if not doc_type or doc_type == 'Все' else doc_type
        return self.service.get_docs_count(doc_type)

    def confirm_delete_doc_listener(self):
        card_data = self.hash_map.get_json("card_data")
        id_doc = card_data['key']
        doc_type = self.hash_map['doc_type_click']

        if self.doc_delete(id_doc):
            docs_count = self.get_docs_count(doc_type=doc_type)
            self.hash_map.toast('Документ успешно удалён')
            if docs_count:
                self.on_start()
            else:
                self.hash_map.finish_process()
        else:
            self.hash_map.toast('Ошибка удаления документа')

    def _get_selected_card(self):
        current_str = self.hash_map.get("selected_card_position")
        jlist = self.hash_map.get_json("docAdrCards")
        selected_card = jlist['customcards']['cardsdata'][int(current_str)]

        return selected_card

    def _clear_barcode_data(self, id_doc):
        return self.service.clear_barcode_data(id_doc)

    def get_id_doc(self):
        card_data = self.hash_map.get_json("card_data") or {}
        id_doc = card_data.get('key') or self.hash_map['selected_card_key']
        return id_doc


class DocsOfflineListScreen(DocsListScreen):
    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.popup_menu_data = ';'.join(
            ['Удалить', 'Очистить данные пересчета'])


class FlowDocScreen(DocsListScreen):
    screen_name = 'Документы'
    process_name = 'Сбор ШК'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = db_services.FlowDocService()
        self.service.docs_table_name = 'RS_docs'
        self.popup_menu_data = 'Удалить;Очистить данные пересчета'

    def on_start(self):
        super().on_start()


    def on_input(self):
        if self.listener == "CardsClick":
            args = self._get_selected_card_put_data()
            self.hash_map.show_screen('ПотокШтрихкодовДокумента', args)
            # screen: FlowDocDetailsScreen = FlowDocDetailsScreen(self.hash_map, self.rs_settings)
            # screen.show(args=args)
        elif self.listener == "ON_BACK_PRESSED":
            self.hash_map.show_screen('Плитки')  # finish_process()
        elif self.listener == 'doc_type_click':
            self.hash_map.refresh_screen()
        elif self._is_result_positive('confirm_clear_barcode_data'):
            id_doc = self.get_id_doc()
            res = self._clear_barcode_data(id_doc)
            self.service.set_doc_status_to_upload(id_doc)
            if res.get('result'):
                self.toast('Все штрихкоды удалены из документа')
            else:
                self.toast('При очистке данных возникла ошибка.')
                self.hash_map.error_log(res.get('error'))

        super().on_input()


# ^^^^^^^^^^^^^^^^^^^^^ DocsList ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== DocDetails =============================


class DocDetailsScreen(Screen):
    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.rs_settings = rs_settings
        self.id_doc = self.hash_map['id_doc']
        self.service = DocService(self.id_doc)
        self.items_on_page = 20
        self.queue_service = ScanningQueueService()

    def on_start(self) -> None:
        pass

    def on_input(self) -> None:

        listener = self.listener

        if listener == "next_page":
            self._next_page()
        elif listener == 'previous_page':
            self._previous_page()

        elif listener == 'items_on_page_click':
            self._set_items_on_page()

        elif listener == 'btn_rows_filter_on':
            self.hash_map.put('current_first_element_number', '0')
            self.hash_map.put('current_page', '1')
            self.hash_map.put('rows_filter', '1')
            self.hash_map.refresh_screen()

        elif listener == 'btn_rows_filter_off':
            self.hash_map.remove('rows_filter')
            self.hash_map.put('SearchString', '')
            self.hash_map.refresh_screen()

        elif listener == "Search":
            self.hash_map.put('current_first_element_number', '0')
            self.hash_map.put('current_page', '1')
            self._on_start()
            self.hash_map.refresh_screen()

    def on_post_start(self):
        pass

    def show(self, args=None):
        self.hash_map.show_screen(self.screen_name, args)
        self._validate_screen_values()

    def _on_start(self):
        self._set_visibility_on_start()
        self.hash_map.put('SetTitle', self.hash_map["doc_type"])

        have_qtty_plan = False
        have_zero_plan = False
        have_mark_plan = False

        last_scanned_details = self._get_doc_details_data(last_scanned=True)
        last_scanned_data = self._prepare_table_data(last_scanned_details)
        last_scanned_item = last_scanned_data[1] if len(last_scanned_data) >= 2 else None
        doc_details = self._get_doc_details_data()
        table_data = self._prepare_table_data(doc_details)
        if table_data and last_scanned_item:
            table_data.insert(1, last_scanned_item)
            if self.hash_map.get('current_page') == '1':
                table_data.pop(1)
            table_data[1] = last_scanned_item
        table_view = self._get_doc_table_view(table_data=table_data)

        self.hash_map['items_on_page_select'] = '20;40;60'
        if self.hash_map.get_bool('highlight'):
            self.hash_map.put('highlight', False)
            # self.enable_highlight(table_view.customtable)
            # self.hash_map.run_event_async('highlight_scanned_item')

        if doc_details:
            self.hash_map['table_lines_qtty'] = len(doc_details)
            have_qtty_plan = sum(
                [self._format_to_float(str(item['qtty_plan'])) for item in doc_details if item['qtty_plan']]) > 0
            # have_zero_plan = not have_qtty_plan
            have_zero_plan = True
            have_mark_plan = self._get_have_mark_plan()

        self.hash_map['have_qtty_plan'] = have_qtty_plan
        self.hash_map['have_zero_plan'] = have_zero_plan
        self.hash_map['have_mark_plan'] = have_mark_plan

        control = self.service.get_doc_value('control', self.id_doc) not in (0, '0', 'false', 'False', None)
        self.hash_map['control'] = control

        self.hash_map['return_selected_data'] = ''
        self.hash_map.put("doc_goods_table", table_view.to_json())

    def _barcode_scanned(self):
        id_doc = self.hash_map.get('id_doc')
        doc = RsDoc(id_doc)
        self.hash_map.put("SearchString", "")
        if self.hash_map.get("event") == "onResultPositive":
            barcode = self.hash_map.get('fld_barcode')
        else:
            barcode = self.hash_map.get('barcode_camera')

        if not barcode:
            return {}

        have_qtty_plan = self.hash_map.get_bool('have_qtty_plan')
        have_zero_plan = self.hash_map.get_bool('have_zero_plan')
        have_mark_plan = self.hash_map.get_bool('have_mark_plan')
        control = self.hash_map.get_bool('control')
        # self.toast(have_zero_plan)

        res = doc.process_the_barcode(
            barcode,
            have_qtty_plan,
            have_zero_plan,
            control,
            have_mark_plan,
            use_mark_setting=self.rs_settings.get('use_mark'))

        # self.toast(res['Error'])

        if res is None:
            self.hash_map.put('scanned_barcode', barcode)
            self.hash_map.show_screen('Ошибка сканера')
            res = {'Error': 'BarcodeError'}
        elif res['Error']:
            if res['Error'] == 'AlreadyScanned':
                self.hash_map.put('barcode', json.dumps({'barcode': res['Barcode'], 'doc_info': res['doc_info']}))
                self.hash_map.show_screen('Удаление штрихкода')
            elif res['Error'] == 'QuantityPlanReached':
                self.hash_map.put('Error_description', 'Количество план в документе превышено')
                self.hash_map.show_dialog(
                    listener='Ошибка превышения плана',
                    title='Количество план в документе превышено')

            elif res['Error'] == 'Must_use_series':
                self.open_series_screen(id_doc, res)
                return res

            elif res['Error'] == 'Zero_plan_error':
                self.hash_map.toast(res['Descr'])
            else:
                self.hash_map.toast(res['Descr'])
        else:
            # self.hash_map.toast('Товар добавлен в документ')
            self.hash_map.put('highlight', True)
            self.hash_map.put('barcode_scanned', True)

        if res.get('Error'):
            self.hash_map.put('scan_error', res['Error'])
        else:
            self.hash_map.put('scan_error', '')

        return res

    def _set_visibility_on_start(self):
        _vars = ['warehouse', 'countragent']

        for v in _vars:
            name = f'Show_{v}'
            self.hash_map[name] = '1' if self.hash_map[v] else '-1'

        allow_fact_input = self.rs_settings.get('allow_fact_input') or False
        self.hash_map.put("Show_fact_qtty_input", '1' if allow_fact_input else '-1')
        self.hash_map.put("Show_fact_qtty_note", '-1' if allow_fact_input else '1')

    def _get_doc_details_data(self, last_scanned=False):
        self._check_previous_page()
        first_element = int(self.hash_map.get('current_first_element_number'))
        row_filters = self.hash_map.get('rows_filter')
        search_string = self.hash_map.get('SearchString') if self.hash_map.get('SearchString') else None

        data = self.service.get_doc_details_data(self.id_doc, 0 if last_scanned else first_element,
                                                 1 if last_scanned else self.items_on_page, row_filters, search_string)
        if not last_scanned:
            self._check_next_page(len(data))
        return data

    def _next_page(self):
        first_element = int(self.hash_map.get('current_first_element_number')) + self.items_on_page
        self.hash_map.put('current_first_element_number', str(first_element))
        current_page = int(self.hash_map.get('current_page')) + 1 or 1
        self.hash_map.put('current_page', str(current_page))

    def _previous_page(self):
        first_element = int(self.hash_map.get('current_first_element_number')) - self.items_on_page
        self.hash_map.put('current_first_element_number', str(first_element))
        current_page = int(self.hash_map.get('current_page')) - 1 or 1
        self.hash_map.put('current_page', str(current_page))

    def _check_previous_page(self):
        if self.hash_map.get('current_first_element_number'):
            first_element = int(self.hash_map.get('current_first_element_number'))
            if first_element > 0:
                self.hash_map.put("Show_previous_page", "1")
                return
        self.hash_map.put('current_first_element_number', '0')
        self.hash_map.put('current_page', '1')
        self.hash_map.put("Show_previous_page", "0")

    def _check_next_page(self, elems_count):
        if elems_count < self.items_on_page:
            if not self.hash_map.containsKey('current_first_element_number'):
                self.hash_map.put('current_first_element_number', '0')
            self.hash_map.put("Show_next_page", "0")
        else:
            self.hash_map.put("Show_next_page", "1")

        if self.hash_map.get('Show_previous_page') == '0' and self.hash_map.get('Show_next_page') == '0':
            self.hash_map.put("Show_pagination_controls", "-1")
        else:
            self.hash_map.put("Show_pagination_controls", "1")

    def _set_items_on_page(self):
        value = self.hash_map.get('items_on_page_click')
        self.items_on_page = int(value)
        new_page = int(self.hash_map.get('current_first_element_number'))//self.items_on_page + 1
        self.hash_map.put('current_page', new_page)
        new_current_first = self.items_on_page * (new_page - 1)
        self.hash_map.put('current_first_element_number', str(new_current_first))

    def _prepare_table_data(self, doc_details):
        table_data = [{}]
        row_filter = self.hash_map.get_bool('rows_filter')

        for record in doc_details:
            if row_filter and record['qtty'] == record['qtty_plan']:
                continue

            pic = '#f02a' if record['IsDone'] != 0 else '#f00c'
            if record['qtty'] == 0 and record['qtty_plan'] == 0:
                pic = ''

            product_row = {
                'key': str(record['id']),
                'good_name': str(record['good_name']),
                'id_good': str(record['id_good']),
                'id_properties': str(record['id_properties']),
                'properties_name': str(record['properties_name'] or ''),
                'id_series': str(record['id_series']),
                'series_name': str(record['series_name'] or ''),
                'id_unit': str(record['id_unit']),
                'units_name': str(record['units_name'] or ''),
                'code_art': 'Код: ' + str(record['code']),
                'art': str(record['art']),
                'price': str(record['price'] if record['price'] is not None else 0),
                'price_name': str(record['price_name'] or ''),
                'picture': pic,
                'use_series': str(record['use_series'])
            }

            props = [
                '{} '.format(product_row['art']) if product_row['art'] else '',
                '({}) '.format(product_row['properties_name']) if product_row['properties_name'] else '',
                '{}'.format(product_row['series_name']) if product_row['series_name'] else '',
                ', {}'.format(product_row['units_name']) if product_row['units_name'] else '',
            ]
            product_row['good_info'] = ''.join(props)

            for key in ['qtty', 'd_qtty', 'qtty_plan']:
                value = self._format_to_float(str(record.get(key, 0.0) or 0.0))
                product_row[key] = str(int(value)) if value.is_integer() else value

            product_row['_layout'] = self._get_doc_table_row_view()
            self._set_background_row_color(product_row)

            if self._added_goods_has_key(product_row['key']):
                table_data.insert(1, product_row)
            else:
                table_data.append(product_row)

        return table_data

    def _get_doc_table_view(self, table_data):
        table_view = widgets.CustomTable(
            widgets.LinearLayout(
                self.LinearLayout(
                    self.TextView('Название'),
                    weight=3
                ),
                self.LinearLayout(
                    self.TextView('План'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('Факт'),
                    weight=1
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

    def _get_doc_table_row_view(self):
        row_view = widgets.LinearLayout(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.LinearLayout(
                        self.TextView('@good_name'),
                        widgets.TextView(
                            Value='@good_info',
                            TextSize=15,
                            width='match_parent'
                        ),
                        width='match_parent',
                    ),
                    width='match_parent',
                    orientation='horizontal',
                    StrokeWidth=1
                ),
                width='match_parent',
                weight=3,
                StrokeWidth=1
            ),
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@qtty_plan',
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
                    Value='@qtty',
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
            BackgroundColor='#FFFFFF'
        )

        return row_view

    def _set_background_row_color(self, product_row):
        background_color = '#FFFFFF'
        qtty, qtty_plan = float(product_row['qtty']), float(product_row['qtty_plan'])

        if qtty_plan > qtty:
            background_color = "#FBE9E7"

        elif qtty_plan < qtty:
            background_color = "#FFF9C4"

        product_row['_layout'].BackgroundColor = background_color

    def _added_goods_has_key(self, key):
        added_goods = self.hash_map.get_json('added_goods')
        result = False

        if added_goods:
            added_goods_doc = added_goods.get(self.id_doc, [])
            result = str(key) in [str(item) for item in added_goods_doc]
            self.toast(result)

        return result

    @staticmethod
    def enable_highlight(customtable):
        customtable['tabledata'][1]['_layout'].BackgroundColor = '#F0F8FF'

    def disable_highlight(self):
        self._on_start()
        self.hash_map.refresh_screen()

    def _fill_none_values(self, data, keys, default=''):
        none_list = [None, 'None']
        for key in keys:
            data[key] = default if data[key] in none_list else data[key]

    def scan_error_sound(self):
        if self.hash_map.get('scan_error') and self.hash_map.get('scan_error') != "None":
            if self.hash_map.get('scan_error') in ['QuantityPlanReached', 'AlreadyScanned', 'Zero_plan_error']:
                self.hash_map.playsound('warning')
            else:
                self.hash_map.playsound('error')
        self.hash_map.refresh_screen()

    def _format_to_float(self, value: str):
        return float(value.replace(u'\xa0', u'').replace(',', '.') or '0.0')

    def _get_have_mark_plan(self):
        count = self.service.get_count_mark_codes(id_doc=self.id_doc)
        return count > 0


    def open_series_screen(self, id_doc, current_elem):
        current_elem['id_doc'] = id_doc
        current_elem['warehouse'] = self.hash_map.get('warehouse')

        params_for_series_screen = json.dumps(current_elem['current_elem']
                                              if current_elem.get('current_elem') else current_elem)
        self.hash_map['params_for_series_screen'] = params_for_series_screen
        # self.hash_map.show_process_result(SeriesList.process_name, SeriesList.screen_name)
        self.hash_map['back_screen'] = self.hash_map.get_current_screen()
        self.hash_map.show_screen(SeriesList.screen_name)

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


class GroupScanDocDetailsScreen(DocDetailsScreen):
    screen_name = 'Документ товары'
    process_name = 'Групповая обработка'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.hs_service = hs_services.HsService(self.get_http_settings())
        self.screen_values = {
            'id_doc': hash_map['id_doc'],
            'doc_type': hash_map['doc_type'],
            'doc_n': hash_map['doc_n'],
            'doc_date': hash_map['doc_date'],
            'warehouse': hash_map['warehouse'],
            'countragent': hash_map['countragent'],
        }

    def on_start(self) -> None:
        super()._on_start()
        self.hash_map.put('stop_timer_update', 'true')

    def on_input(self) -> None:
        super().on_input()
        listener = self.hash_map['listener']

        if listener == "CardsClick":
            pass

        elif listener == 'barcode':
            self.hash_map.put("SearchString", "")
            self._run_progress_barcode_scanning()

        elif self._is_result_positive('ВвестиШтрихкод'):
            self._run_progress_barcode_scanning()

        elif self._is_result_positive('RetryConnection'):
            self._run_progress_barcode_scanning()

        elif self._is_result_negative('RetryConnection'):
            self.set_scanner_lock(False)

        elif listener == 'btn_barcodes':
            self.hash_map.show_dialog('ВвестиШтрихкод')

        elif listener in ['ON_BACK_PRESSED', 'BACK_BUTTON']:
            self.hash_map.put("SearchString", "")
            self.hash_map.put("ShowScreen", "Документы")
            self.hash_map.put('stop_timer_update', 'false')

    def _run_progress_barcode_scanning(self):
        self.hash_map.run_event_progress('doc_details_before_process_barcode')

    def before_process_barcode(self):
        self.set_scanner_lock(True)
        if self._check_connection():
            self._update_document_data()
            scan_result = self._barcode_scanned()

            if scan_result.get('Error'):
                self.hash_map.run_event('doc_scan_error_sound')
            else:
                self.hash_map.run_event_async('doc_run_post_barcode_scanned',
                                              post_execute_method='doc_scan_error_sound')
            self.set_scanner_lock(False)

        else:
            self.hash_map.beep('70')
            self.hash_map.show_dialog(listener="RetryConnection", title='Отсутствует соединение с сервером',
                                      buttons=["Повторить", "Отмена"])

    def _update_document_data(self):
        docs_data = self._get_update_current_doc_data()
        if docs_data:
            try:
                self.service.update_data_from_json(docs_data)
            except Exception as e:
                self.service.write_error_on_log(f'Ошибка записи документа:  {e}')

    def _get_update_current_doc_data(self):
        try:
            self.hs_service.get_data()
            answer = self.hs_service.http_answer

            if answer.unauthorized:
                self.hash_map.toast('Ошибка авторизации сервера 1С')
            elif answer.forbidden:
                self.hash_map.notification(answer.error_text, title='Ошибка обмена')
                self.hash_map.toast(answer.error_text)
            elif answer.error:
                self.service.write_error_on_log(f'Ошибка загрузки документа:  {answer.error_text}')
            else:
                return answer.data
        except:
            self.set_scanner_lock(False)

    def post_barcode_scanned(self):
        if self.hash_map.get_bool('barcode_scanned'):
            answer = None
            try:
                answer = self._post_goods_to_server()
            except Exception as e:
                self.service.write_error_on_log(e.args[0])

            if answer and answer.get('Error') is not None:
                self.hash_map.error_log(answer.get('Error'))

            self.on_start()

    def _post_goods_to_server(self):
        res = self.service.get_last_edited_goods(to_json=False)
        hs_service = HsService(self.get_http_settings())

        if isinstance(res, dict) and res.get('Error'):
            answer = {'empty': True, 'Error': res.get('Error')}
            return answer
        elif res:
            hs_service.send_documents(res)
            answer = hs_service.http_answer
            if answer.error:
                self.service.write_error_on_log(answer.error_text)
            else:
                try:
                    self.service.update_sent_data(res)
                except Exception as e:
                    self.service.write_error_on_log(e.args[0])

        # пока что отключил дополнительный get-запрос, проверяем производительность

        # docs_data = hs_service.get_data()
        #
        # if docs_data.get('data'):
        #     try:
        #         self.service.update_data_from_json(docs_data['data'])
        #     except Exception as e:
        #         self.service.write_error_on_log(e.args[0])

    def _check_connection(self):
        try:
            self.hs_service.communication_test(timeout=1)
            answer = self.hs_service.http_answer
        except Exception as e:
            answer = self.hs_service.HttpAnswer(
                error=True,
                error_text=str(e.args[0]),
                status_code=404,
                url=self.hs_service.url)

        return not answer.error

    def __get_doc_table_view(self, table_data):
        table_view = widgets.CustomTable(
            widgets.LinearLayout(
                self.LinearLayout(
                    self.TextView('Название'),
                    weight=4
                ),
                self.LinearLayout(
                    self.TextView('План'),
                    weight=2
                ),
                self.LinearLayout(
                    self.TextView('Факт устройства'),
                    weight=2
                ),
                self.LinearLayout(
                    self.TextView('Общий факт'),
                    weight=2
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

    def __get_doc_table_row_view(self):
        row_view = widgets.LinearLayout(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.LinearLayout(
                        self.TextView('@good_name'),
                        widgets.TextView(
                            Value='@good_info',
                            TextSize=15,
                            width='match_parent'
                        ),
                        width='match_parent',
                    ),
                    width='match_parent',
                    orientation='horizontal',
                    StrokeWidth=1
                ),
                width='match_parent',
                weight=4,
                StrokeWidth=1
            ),
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@qtty_plan',
                    TextSize=15,
                    width='match_parent',
                ),
                width='match_parent',
                height='match_parent',
                weight=2,
                StrokeWidth=1
            ),
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@d_qtty',
                    TextSize=15,
                    width='match_parent',
                ),
                width='match_parent',
                height='match_parent',
                weight=2,
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
                weight=2,
                StrokeWidth=1
            ),
            orientation='horizontal',
            width='match_parent',
            BackgroundColor='#FFFFFF'
        )

        return row_view

    def scan_error_sound(self):
        super().scan_error_sound()

    def set_scanner_lock(self, value: bool):
        if 'urovo' in self.hash_map.get('DEVICE_MODEL').lower():
            suClass.urovo_set_lock_trigger(value)

    def can_launch_timer(self):
        return False

class GroupScanDocDetailsScreenNew(DocDetailsScreen):
    screen_name = 'Документ товары'
    process_name = 'Групповая обработка'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.hs_service = hs_services.HsService(self.get_http_settings())
        self.db_service = db_services.BarcodeService()
        self.queue_service = ScanningQueueService()

    def on_start(self):
        super()._on_start()

    def on_input(self) -> None:
        super().on_input()
        listeners = {
            'barcode': self._barcode_scanned,
            'ON_BACK_PRESSED': self.go_back
        }
        if self.listener in listeners:
            listeners[self.listener]()

    def _barcode_scanned(self):
        if self.hash_map.get("event") == "onResultPositive":
            barcode = self.hash_map.get('fld_barcode')
        else:
            barcode = self.hash_map.get('barcode_camera')

        if not barcode:
            return

        self.barcode_worker = BarcodeWorker(id_doc=self.id_doc, **self._get_barcode_process_params(),
                                            use_scanning_queue=True)
        result = self.barcode_worker.process_the_barcode(barcode)

        if result.error:
            self._process_error_scan_barcode(result)
            return result.error

        if not self.hash_map.get_bool('send_document_lines_running'):
            self.hash_map.run_event_async('send_post_lines_data', post_execute_method='after_send_post_lines_data')
            self.hash_map.put('send_document_lines_running', True)

    def go_back(self):
        self.hash_map.show_screen('Документы')

    def send_post_lines_data(self):
        send_data = self.queue_service.get_send_document_lines(self.id_doc)
        http_result = self.hs_service.send_document_lines(self.id_doc, send_data)

        if http_result.status_code == 200:
            self.queue_service.update_sent_lines(send_data)
            if http_result.data:
                for element in http_result.data['data']:
                    self.service.provider.table_name = "RS_docs_table"
                    table_line = self.db_service.get_table_line('RS_docs_table', {'id_doc': element['id_doc'],
                                                               'id_good': element['id_good'],
                                                               'id_properties': element['id_properties'],
                                                               'id_unit': element['id_unit']})

                    if table_line:
                        table_line['qtty'] = element['d_qtty']
                        table_line['sent'] = 1
                        self.db_service.update_table('RS_docs_table', table_line)
                    else:
                        new_table_line = self.create_new_table_line(element)

                        self.toast(new_table_line)
                        self.db_service.update_table('RS_docs_table', new_table_line)

    def after_send_data(self):
        self.hash_map.put('send_document_lines_running', False)
        self.hash_map.refresh_screen()
        self.on_start()

    @staticmethod
    def create_new_table_line(element):
        new_table_line = element
        new_table_line['qtty'] = new_table_line['d_qtty']
        del new_table_line['d_qtty']
        del new_table_line['table_type']
        new_table_line['id_series'] = ''
        new_table_line['id_price'] = ''
        new_table_line['qtty_plan'] = None
        return new_table_line

    def _get_barcode_process_params(self):
        return {
            'have_qtty_plan': self.hash_map.get_bool('have_qtty_plan'),
            'have_zero_plan': self.hash_map.get_bool('have_zero_plan'),
            'have_mark_plan': self.hash_map.get_bool('have_mark_plan'),
            'control': self.hash_map.get_bool('control')
        }

    def _process_error_scan_barcode(self, scan_result):
        self.hash_map.toast(scan_result.description)
        self.hash_map.playsound('error')


class DocumentsDocDetailScreen(DocDetailsScreen):
    screen_name = 'Документ товары'
    process_name = 'Документы'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)

    def on_start(self) -> None:
        super()._on_start()

    def on_input(self) -> None:
        super().on_input()
        listener = self.hash_map['listener']
        id_doc = self.hash_map.get('id_doc')

        if listener == "CardsClick":
            selected_card_key = self.hash_map['selected_card_key']
            doc_goods_table = self.hash_map.get_json('doc_goods_table')
            table_data = doc_goods_table['customtable']['tabledata']

            current_elem = None
            current_elem_filter = [item for item in table_data if item.get('key') == selected_card_key]

            if current_elem_filter:
                current_elem = current_elem_filter[0]

            current_str = self.hash_map["selected_card_position"]
            table_lines_qtty = self.hash_map['table_lines_qtty']

            # текущий элемент не найден или это заголовок таблицы
            if current_elem is None or 'good_name' not in current_elem:
                return
            # ----------- Блок работы с сериями товара. Если строка документа должна хранить серии
            # ВАЖНО! Заменяет экран товара по умолчанию
            if current_elem['use_series'] == '1':
                current_elem['id'] = current_elem['key']
                self.open_series_screen(id_doc, current_elem)
                return

            title = '{} № {} от {}'.format(self.hash_map['doc_type'], self.hash_map['doc_n'], self.hash_map['doc_date'])
            put_data = {
                'Doc_data': title,
                'Good': current_elem['good_name'],
                'items_on_page': self.items_on_page,
                'id_good': current_elem['id_good'],
                'id_unit': current_elem['id_unit'],
                'id_property': current_elem['id_properties'],
                'good_art': current_elem['art'],
                'good_sn': current_elem['series_name'],
                'good_property': current_elem['properties_name'],
                'good_price': current_elem['price'],
                'good_unit': current_elem['units_name'],
                'good_str': f'{current_str} / {table_lines_qtty}',
                'qtty_plan': current_elem['qtty_plan'],
                'good_plan': current_elem['qtty_plan'],
                'key': current_elem['key'],
                'price': current_elem['price'],
                'price_type': current_elem['price_name'],
                'qtty': current_elem['qtty'] if current_elem['qtty'] and float(current_elem['qtty']) != 0 else '',
            }
            self._fill_none_values(
                put_data,
                ('good_art', 'good_sn', 'good_property', 'good_price', 'good_plan'),
                default='отсутствует')

            self.hash_map.put_data(put_data)

            # Формируем таблицу QR кодов------------------

            args = {
                'id_doc': id_doc,
                'id_good': current_elem['id_good'],
                'id_property': current_elem['id_properties'],
                'id_series': current_elem['id_series'],
                'id_unit': current_elem['id_unit'],
            }
            res = self._get_doc_barcode_data(args)

            # TODO Переделать через виджеты
            cards = self._get_barcode_card()

            # Формируем список карточек баркодов
            cards['customcards']['cardsdata'] = []
            for el in res:
                picture = '#f00c' if el['approved'] in ['True', 'true', '1'] else ''
                row = {
                    'barcode': el['mark_code'],
                    'picture': picture
                }
                cards['customcards']['cardsdata'].append(row)

            self.hash_map.put('barcode_cards', cards, to_json=True)
            self.hash_map.show_screen("Товар выбор")

        elif listener == 'barcode' or self._is_result_positive('ВвестиШтрихкод'):
            res = self._barcode_scanned()
            if res.get('Error') and res['Error'] == 'Must_use_series':
                return
            if res.get('key'):
                self.service.update_rs_docs_table_sent_status(res.get('key'))
                self.service.set_doc_status_to_upload(id_doc)

            self.hash_map.put('scan_error', res['Error'])
            super().scan_error_sound()

        elif listener == 'btn_goods_ocr':
            self.hash_map.delete('finded_articles')
            self.hash_map.put('art_info', 'Найденные артикулы: ')
            list_art = self.service.get_all_articles_in_document()
            self.hash_map.put('list_art', list_art)
            self.hash_map.put('RunCV', 'Распознавание артикулов')

        elif listener == 'ActiveCV':
            if self.hash_map.containsKey('button_manage_articles'):
                finded_articles = self.hash_map.get('finded_articles')

                if finded_articles is None:
                    self.hash_map.toast('Артикулы не найдены')
                else:
                    title = 'Выберите товар'
                    allowed_fact_input = self.rs_settings.get('allow_fact_input')
                    if allowed_fact_input:
                        title += ' и укажите количество'
                    self.hash_map.put('title_select_good_article', title)
                    self.hash_map.show_screen('ВыборТовараАртикул')

            self.hash_map.delete('button_manage_articles')

        elif listener == 'btn_barcodes':
            self.hash_map.show_dialog('ВвестиШтрихкод')

        elif listener in ['ON_BACK_PRESSED', 'BACK_BUTTON']:
            self.hash_map.remove('rows_filter')
            self.hash_map.put('current_first_element_number', '0')
            self.hash_map.put('items_on_page_click', '')
            self.hash_map.put("SearchString", "")
            self.hash_map.put("ShowScreen", "Документы")

        elif self._is_result_positive('confirm_verified'):
            id_doc = self.hash_map['id_doc']
            doc = RsDoc(id_doc)
            doc.mark_verified(1)
            self.hash_map.put("SearchString", "")
            self.hash_map.show_screen("Документы")

        elif listener == 'btn_doc_mark_verified':
            self.hash_map.show_dialog('confirm_verified', 'Завершить документ?', ['Да', 'Нет'])

    def _get_barcode_card(self):
        # TODO Переделать через виджеты

        ls = {"customcards": {
            "options": {
                "search_enabled": False,
                "save_position": True
            },
            "layout": {
                "type": "LinearLayout",
                "orientation": "vertical",
                "height": "match_parent",
                "width": "match_parent",
                "weight": "0",
                "Elements": [
                    {
                        "type": "LinearLayout",
                        "orientation": "horizontal",
                        "height": "match_parent",
                        "width": "match_parent",
                        "weight": "0",
                        "Elements": [
                            {"type": "TextView",
                             "height": "wrap_content",
                             "width": "match_parent",
                             "weight": "1",
                             "Value": "@barcode",
                             "TextSize": self.rs_settings.get('goodsTextSize'),
                             "Variable": ""
                             },
                            {
                                "type": "TextView",
                                "show_by_condition": "",
                                "Value": "@picture",
                                "TextColor": "#DB7093",
                                "BackgroundColor": "#FFFFFF",
                                "Variable": "btn_tst1",
                                "NoRefresh": False,
                                "document_type": "",
                                "cardCornerRadius": "15dp",
                                "weight": "1",
                                "mask": ""
                            }]
                    }
                ]
            }}
        }
        return ls

    def _get_doc_barcode_data(self, args):
        return self.service.get_doc_barcode_data(args)

class AdrDocDetailsScreen(DocDetailsScreen):
    screen_name = 'Документ товары'
    process_name = 'Адресное хранение'
    table_types_from_doc_type = {'Отбор': ['out', ], 'Размещение': ['in', ],
                                 'Перемещение': ['in', 'out']}

    def __init__(self, hash_map, rs_settings):
        super().__init__(rs_settings=rs_settings, hash_map=hash_map)

        self.current_cell = self.hash_map.get('current_cell_id')
        self.screen_values = {'doc_n': '', 'doc_date': '', 'warehouse': ''}
        self.table_type = ''
        self.service = AdrDocService(self.id_doc, table_type=self.table_type)

    def on_start(self):
        if not self.table_type:
            self.table_type = self._get_table_type_for_screen()
        else:
            self.table_type = self._get_table_type_from_name(self.hash_map['table_type'])
        self.service.table_type = self.table_type

        super()._on_start()

    def _get_doc_details_data(self, last_scanned=False):
        super()._check_previous_page()
        row_filters = self.hash_map.get('rows_filter')
        first_element = int(self.hash_map.get('current_first_element_number'))
        search_string = self.hash_map.get('SearchString') if self.hash_map.get('SearchString') else None
        data = self.service.get_doc_details_data(id_doc=self.id_doc, curCell=self.current_cell,
                                                 first_elem=0 if last_scanned else first_element,
                                                 items_on_page=1 if last_scanned else self.items_on_page,
                                                 row_filters=row_filters,
                                                 search_string=search_string)
        if not last_scanned:
            super()._check_next_page(len(data))
        return data

    def on_input(self) -> None:
        super().on_input()
        listener = self.hash_map['listener']

        if listener == "CardsClick":
            self._fill_one_string_screen()
            # self.hash_map.show_screen("Товар выбор") ---*** Экран в функции _fill_one_string_screen
        elif listener == "BACK_BUTTON":
            self.hash_map.put("SearchString", "")
            self.hash_map.remove('rows_filter')
            self.hash_map.show_screen("Документы")
        elif listener == "btn_barcodes":

            self.hash_map.put("ShowDialog", "ВвестиШтрихкод")

        elif listener == 'barcode' or self.hash_map.get("event") == "onResultPositive":
            self.hash_map.remove('rows_filter')
            self.hash_map.put("SearchString", "")
            current_cell = self.hash_map.get('current_cell')

            doc = ui_global.Rs_adr_doc
            doc.id_doc = self.hash_map.get('id_doc')
            if self.hash_map.get("event") == "onResultPositive":
                barcode = self.hash_map.get('fld_barcode')
            else:
                barcode = self.hash_map.get('barcode_camera')

            doc_cell = doc.find_cell(doc, barcode)

            if doc_cell:
                self.hash_map.put('current_cell', doc_cell['name'])
                self.hash_map.put('current_cell_id', doc_cell['id'])
                self.current_cell = doc_cell['id']
                self.hash_map.put('current_first_element_number', '0')
                return

            if not current_cell and not doc_cell:
                self.hash_map.playsound('warning')
                self.hash_map.put('toast', 'Не найдена ячейка')
                return

            have_qtty_plan = self.hash_map.get_bool('have_qtty_plan')
            have_zero_plan = self.hash_map.get_bool('have_zero_plan')
            have_mark_plan = self.hash_map.get_bool('have_mark_plan')
            control = self.hash_map.get_bool('control')

            res = doc.process_the_barcode(doc, barcode
                                          , (have_qtty_plan), (have_zero_plan), (control),
                                          self.hash_map.get('current_cell_id'), self.table_type)

            # self.service.update_rs_docs_table_sent_status(res.get('key'))
            self.service.set_doc_status_to_upload(self.id_doc)

            if res is None:
                self.hash_map.put('scanned_barcode', barcode)
                # suClass.urovo_set_lock_trigger(True)
                self.hash_map.playsound('error')
                self.hash_map.put('ShowScreen', 'Ошибка сканера')
                # self.hash_map.put('toast',
                #             'Штрих код не зарегистрирован в базе данных. Проверьте товар или выполните обмен данными')
            elif res['Error']:
                self.hash_map.playsound('warning')
                if res['Error'] == 'AlreadyScanned':
                    self.hash_map.put('barcode', json.dumps({'barcode': res['Barcode'], 'doc_info': res['doc_info']}))
                    self.hash_map.put('ShowScreen', 'Удаление штрихкода')
                elif res['Error'] == 'QuantityPlanReached':
                    self.hash_map.put('toast', res['Descr'])
                elif res['Error'] == 'Zero_plan_error':
                    self.hash_map.put('toast', res['Descr'])
                elif res['Error'] == 'Must_use_series':
                    self.open_series_screen(doc.id_doc, res)
                    return res
                else:
                    self.hash_map.put('toast', res['Descr'])  # + ' '+ res['Barcode']
            else:
                self.hash_map.put('toast', 'Товар добавлен в документ')

                # ---------------------------------------------------------
        elif listener == 'btn_doc_mark_verified':
            doc = ui_global.Rs_adr_doc
            doc.id_doc = self.hash_map.get('id_doc')
            doc.mark_verified(doc, 1)
            self.hash_map.put("SearchString", "")
            self.hash_map.show_screen("Документы")

        elif listener == 'ON_BACK_PRESSED':
            self.hash_map.put("SearchString", "")
            if self.hash_map.get('current_cell_id'):
                self.hash_map.remove('current_cell')
                self.hash_map.remove('current_cell_id')
                self.current_cell = None
                self.hash_map.refresh_screen()
            else:
                self.hash_map.show_screen("Документы")

        elif listener == 'btn_clear_cell':
            self.hash_map.remove('current_cell')
            self.hash_map.remove('current_cell_id')
            self.current_cell = None
            self.hash_map.refresh_screen()

        elif listener == 'btn_select_cell':  # Кнопка выбрать ячейку

            self.hash_map.remove('current_cell')
            self.hash_map.remove('current_cell_id')
            self.hash_map.remove('SearchString')
            self.hash_map.put('table_for_select', 'RS_cells')  # Таблица для выбора значения
            self.hash_map.put('SetResultListener', 'select_cell_value')
            self.hash_map.put('filter_fields', 'name;barcode')
            self.hash_map.put('ShowProcessResult', 'Универсальный справочник|Справочник')

        elif listener == 'select_cell_value':
            if self.hash_map.get('current_id'):
                self.hash_map.put('current_cell_id', self.hash_map.get('current_id'))
                self.hash_map.put('current_cell', self.hash_map.get('current_name'))
                self.current_cell = self.hash_map.get('current_id')
                # self._on_start()
                # self.hash_map.refresh_screen()
        elif listener == 'LayoutAction':
            self._layout_action()


        elif listener == 'select_cell_value_for_card':
            # TODO Изменение данных отправить в класс в db_service
            current_key = self.hash_map.get("key")
            if current_key:
                ui_global.get_query_result('Update RS_adr_docs_table SET id_cell = ? Where id = ?',
                                           (self.hash_map.get('current_id'), current_key))
                self.hash_map.put('RefreshScreen', '')

        elif listener == 'btn_add_string':

            self.hash_map.put("Doc_data",
                              self.hash_map.get('doc_type') + ' №' + self.hash_map.get('doc_n') +
                              ' от' + self.hash_map.get('doc_date'))
            self.hash_map.put("Good", '')
            self.hash_map.put("properties", '')
            self.hash_map.put("qtty_plan", '')

            self.hash_map.show_screen("Товар")

        elif listener == 'table_type':
            self.table_type = self._get_table_type_from_name(self.hash_map['table_type'])
            self._on_start()
            self.hash_map.refresh_screen()

    # В зависимости от вида документа назначаем для отображения табличную часть по умолчаниюю
    # Например, для документа Отбор это out а для Размещение in
    def _get_table_type_for_screen(self):
        tables_type = 'Отбор;Размещение'  # ';'.join(self.table_types_from_doc_type[
        # self.hash_map['doc_type']])
        self.hash_map.put('tables_type', tables_type)

        if self.hash_map.get('doc_type') in ['Отбор', 'Перемещение']:
            self.hash_map['table_type'] = 'Отбор'
            return 'out'
        else:
            self.hash_map['table_type'] = 'Размещение'
            return 'in'

    @staticmethod
    def _get_table_type_from_name(_val):

        return 'in' if _val == 'Размещение' else 'out'
        # current_table_type']]

    def _layout_action(self):
        layout_listener = self.hash_map.get('layout_listener')

        current_key = self.hash_map.get("key")
        if layout_listener == 'Удалить строку':

            if current_key:  # current_elem['key']:
                ui_global.get_query_result('DELETE FROM RS_adr_docs_table WHERE id = ?',
                                           (current_key,))  # current_elem['key'],))
                self.hash_map.put('RefreshScreen', '')
        elif layout_listener == 'Изменить ячейку':

            self.hash_map.remove('SearchString')
            self.hash_map.put('table_for_select', 'RS_cells')  # Таблица для выбора значения
            self.hash_map.put('SetResultListener', 'select_cell_value_for_card')
            self.hash_map.put('filter_fields', 'name;barcode')
            self.hash_map.put('ShowProcessResult', 'Универсальный справочник|Справочник')

    def _fill_one_string_screen(self, _filter=''):
        # hashMap = self.hash_map
        # Находим ID документа
        current_str = self.hash_map.get("selected_card_position")
        jlist = json.loads(self.hash_map.get("doc_goods_table"))
        current_elem = jlist['customtable']['tabledata'][int(current_str)]
        id_doc =  self.hash_map.get('id_doc')
        self.hash_map.put("Doc_data",
                          self.hash_map.get('doc_type') + ' №' + self.hash_map.get('doc_n') +
                          ' от' + self.hash_map.get('doc_date'))
        self.hash_map.put("current_cell_name", 'Ячейка: ' + current_elem['cell'])
        self.hash_map.put('id_cell', current_elem['id_cell'])
        self.hash_map.put("Good", current_elem['good_name'])
        self.hash_map.put("qtty_plan", str(current_elem['qtty_plan']))
        if not current_elem['qtty']:  # or float(current_elem['qtty']) == 0:
            self.hash_map.put("qtty", '')
        else:
            if float(current_elem['qtty']) == 0:
                self.hash_map.put("qtty", '')
            else:
                self.hash_map.put("qtty", str(current_elem['qtty']))
        self.hash_map.put('key', current_elem['key'])
        self.hash_map.put('id_good', current_elem['id_good'])
        self.hash_map.put('id_unit', current_elem['id_unit'])
        self.hash_map.put('id_property', current_elem['id_properties'])

        # ----------- Блок работы с сериями товара. Если строка документа должна хранить серии
        # ВАЖНО! Заменяет экран товара по умолчанию
        if current_elem['use_series'] == '1':
            current_elem['id'] = current_elem['key']
            self.open_series_screen(id_doc, current_elem)
        else:
            self.hash_map.put("ShowScreen", "Товар выбор")

    def _prepare_table_data(self, doc_details):
        # TODO добавить группировку по ячейкам
        table_data = [{}]  # было [{}]
        row_filter = self.hash_map.get_bool('rows_filter')

        for record in doc_details:
            if row_filter and record['qtty'] == record['qtty_plan']:
                continue

            pic = '#f02a' if record['IsDone'] != 0 else '#f00c'
            if record['qtty'] == 0 and record['qtty_plan'] == 0:
                pic = ''

            product_row = {
                'key': str(record['id']),
                'cell': str(record['cell_name']),
                'id_cell': str(record['id_cell']),
                'good_name': str(record['good_name']),
                'id_good': str(record['id_good']),
                'id_properties': str(record['id_properties']),
                'properties_name': str(record['properties_name'] or ''),
                'id_series': str(record['id_series']),
                'series_name': str(record['series_name'] or ''),
                'id_unit': str(record['id_unit']),
                'units_name': str(record['units_name'] or ''),
                'code_art': 'Код: ' + str(record['code']),
                'art': str(record['art']),
                'picture': pic,
                'use_series': str(record['use_series'])
            }

            props = [
                '{} '.format(product_row['art']) if product_row['art'] else '',
                '({}) '.format(product_row['properties_name']) if product_row['properties_name'] else '',
                '{}'.format(product_row['series_name']) if product_row['series_name'] else '',
                ', {}'.format(product_row['units_name']) if product_row['units_name'] else '',
            ]
            product_row['good_info'] = ''.join(props)
            if record['qtty'] is not None:
                product_row['qtty'] = str(int(record['qtty']) if record['qtty'].is_integer() else record['qtty'])
            else:
                product_row['qtty'] = "0"
            if record['qtty_plan'] is not None:
                product_row['qtty_plan'] = str(int(record['qtty_plan']) if record['qtty_plan'].is_integer()
                                               else record['qtty_plan'])
            else:
                product_row['qtty_plan'] = "0"

            product_row['_layout'] = self._get_doc_table_row_view()
            self._set_background_row_color(product_row)

            if self._added_goods_has_key(product_row['key']):
                table_data.insert(1, product_row)
            else:
                table_data.append(product_row)

        return table_data

    def _get_doc_table_view(self, table_data):
        table_view = widgets.CustomTable(
            widgets.LinearLayout(
                self.LinearLayout(
                    self.TextView('Ячейка'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('Название'),
                    weight=2
                ),
                self.LinearLayout(
                    self.TextView('План'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('Факт'),
                    weight=1
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

    def _get_doc_table_row_view(self):

        row_view = widgets.LinearLayout(
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@cell',
                    TextSize=15,
                    width='match_parent',
                ),
                width='match_parent',
                height='match_parent',
                weight=1,
                StrokeWidth=1
            ),
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.LinearLayout(
                        self.TextView('@good_name'),
                        widgets.TextView(
                            Value='@good_info',
                            TextSize=15,
                            width='match_parent'
                        ),
                        width='match_parent',
                    ),
                    width='match_parent',
                    orientation='horizontal',
                    StrokeWidth=1
                ),
                width='match_parent',
                weight=2,
                StrokeWidth=1
            ),
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@qtty_plan',
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
                    Value='@qtty',
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
            BackgroundColor='#FFFFFF'
        )

        return row_view

    def _get_detail_cards(self, q_result):
        results = q_result
        hashMap = self.hash_map
        cards = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.TextView(Value='@good_name', TextSize=self.rs_settings.get('GoodsCardTitleTextSize'),
                                 TextBold=True,
                                 weight=1),
                widgets.PopupMenuButton(Value="Удалить строку"),
                widgets.LinearLayout(
                    widgets.TextView(TextBold=True, weight=1, Value='@code_art'),
                    widgets.TextView(TextBold=False, weight=1, Value='@art'),
                    orientation="horizontal"),
                widgets.LinearLayout(
                    widgets.TextView(Value='План', TextSize=self.rs_settings.get('goodsTextSize')),
                    widgets.TextView(Value='@qtty_plan'),
                    widgets.TextView(Value='Факт'),
                    widgets.TextView(Value='@qtty'),
                    # widgets.TextView(Value = '@'),
                    widgets.TextView(Value='Цена'),
                    widgets.TextView(Value='@picture'),
                    orientation="horizontal"), orientation="vertical"), options=widgets.Options())

        if results:
            self.hash_map.put('id_doc', str(results[0]['id_doc']))
            current_cell = ''
            for record in results:
                if self.row_filter and record['qtty'] == record['qtty_plan']:
                    continue
                pic = '#f02a' if record['IsDone'] != 0 else '#f00c'
                if record['qtty'] == 0 and record['qtty_plan'] == 0:
                    pic = ''

                if current_cell != record['cell_name']:
                    c = {"group": record['cell_name']}
                    # doc_detail_list['customcards']['cardsdata'].append(c)
                    cards.customcards['cardsdata'].append(c)
                    current_cell = record['cell_name']

                product_row = {
                    'key': str(record['id']),
                    'good_name': str(record['good_name']),
                    'id_good': str(record['id_good']),
                    'id_properties': str(record['id_properties']),
                    'properties_name': str(record['properties_name']),
                    'id_series': str(record['id_series']),
                    'series_name': str(record['series_name']),
                    'id_unit': str(record['id_unit']),
                    'units_name': str(record['units_name']),
                    'code_art': 'Код: ' + str(record['code']),
                    'cell_name': str(record['cell_name']),
                    'id_cell': str(record['id_cell']),

                    'qtty': str(record['qtty'] if record['qtty'] is not None else 0),
                    'qtty_plan': str(record['qtty_plan'] if record['qtty_plan'] is not None else 0),
                    'picture': pic
                }

                #            doc_detail_list['customcards']['cardsdata'].append(product_row)
                cards.customcards['cardsdata'].append(product_row)

    def open_series_screen(self, id_doc, current_elem):
        current_elem['id_doc'] = id_doc
        current_elem['warehouse'] = self.hash_map.get('warehouse')
        current_elem['doc_basic_handler_name'] = 'RS_adr_docs'
        current_elem['doc_basic_table_name'] = 'RS_adr_docs_table'

        params_for_series_screen = json.dumps(current_elem['current_elem']
                                              if current_elem.get('current_elem') else current_elem)
        self.hash_map['params_for_series_screen'] = params_for_series_screen
        # self.hash_map.show_process_result(SeriesList.process_name, SeriesList.screen_name)
        self.hash_map['back_screen'] = self.hash_map.get_current_screen()
        self.hash_map.show_screen(SeriesAdrList.screen_name)



class FlowDocDetailsScreen(DocDetailsScreen):
    screen_name = 'ПотокШтрихкодовДокумента'
    process_name = 'Сбор ШК'
    printing_template_name = 'flow_doc_details_screen'
    ocr_nosql = noClass("ocr_nosql")

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = db_services.FlowDocService(self.id_doc)

    def show(self, args=None):
        self.hash_map.show_screen(self.screen_name, args)
        # self._validate_screen_values()

    def on_start(self):
        self._barcode_flow_on_start()
        self._set_vision_settings()

    def on_input(self):
        listener = self.hash_map.get('listener')
        if listener == "CardsClick":
            current_str = self.hash_map.get("selected_card_position")
            jlist = json.loads(self.hash_map.get("doc_barc_flow"))
            current_elem = jlist['customtable']['tabledata'][int(current_str)]
            data_dict = {'barcode': current_elem['barcode'],
                         'Номенклатура': current_elem['name'],
                         'qtty': current_elem['qtty'], 'Характеристика': ''}

            HtmlView.print_from_any_screen(
                self.hash_map,
                self.rs_settings,
                self.printing_template_name,
                data_for_printing=data_dict)

        elif listener == "BACK_BUTTON":
            self.hash_map.remove('rows_filter')
            self.hash_map.put("SearchString", "")
            self.hash_map.finish_process()

        elif listener == 'btn_barcodes':
            self.hash_map.show_dialog('ВвестиШтрихкод')

        elif listener == 'barcode':
            barcode = self.hash_map.get('barcode_camera')
            self.service.add_barcode_to_database(barcode)
            self.service.set_doc_status_to_upload(self.id_doc)

        elif self._is_result_positive('ВвестиШтрихкод'):
            barcode = self.hash_map.get('fld_barcode')
            self.service.add_barcode_to_database(barcode)
            self.service.set_doc_status_to_upload(self.id_doc)

        elif self._is_result_positive('confirm_verified'):
            RsDoc(self.id_doc).mark_verified(1)
            self.hash_map.show_screen("Документы")

        elif listener == 'btn_doc_mark_verified':
            self.hash_map.show_dialog('confirm_verified',
                                      'Завершить документ?',
                                      ['Да', 'Нет'])

        elif listener == 'btn_ocr_serial_template_settings':
            min_rec_amount = self.rs_settings.get('ocr_serial_template_min_rec_amount') or 5
            self.hash_map.put('ocr_serial_template_min_rec_amount', str(min_rec_amount))
            num_amount = self.rs_settings.get('ocr_serial_template_num_amount') or 10
            self.hash_map.put('ocr_serial_template_num_amount', str(num_amount))
            prefix = self.rs_settings.get('ocr_serial_template_prefix') or 'SN'
            self.hash_map.put('ocr_serial_template_prefix', prefix)
            flag_rec = self.rs_settings.get('ocr_serial_template_continuous_recognition')
            flag_rec = str(flag_rec).lower() if flag_rec is not None else 'false'
            flag_pref = self.rs_settings.get('ocr_serial_template_use_prefix')
            flag_pref = str(flag_pref).lower() if flag_pref is not None else 'false'
            current_template = f'Текущий шаблон: {prefix if flag_pref == "true" else ""}{"*"*num_amount}'
            self.hash_map.put('current_ocr_serial_template', current_template)
            self.hash_map.put('ocr_serial_template_continuous_recognition', flag_rec)
            self.hash_map.put('ocr_serial_template_use_prefix', flag_pref)
            self.hash_map.show_dialog('ШаблонРаспознавания',
                                      'Настройка шаблона распознавания',
                                      ['Принять', 'Отмена'])

        elif self._is_result_positive('ШаблонРаспознавания'):
            min_rec_amount = self.hash_map.get('ocr_serial_template_min_rec_amount')
            num_amount = self.hash_map.get('ocr_serial_template_num_amount') or '10'
            prefix = self.hash_map.get('ocr_serial_template_prefix')
            continuous_recognition = self.hash_map.get('ocr_serial_template_continuous_recognition')
            continuous_recognition = True if continuous_recognition == 'true' else False
            use_prefix = self.hash_map.get('ocr_serial_template_use_prefix')
            use_prefix = True if use_prefix == 'true' else False
            is_valid, error = self._validate_ocr_settings(min_rec_amount, num_amount,
                                                          prefix, use_prefix)
            if not is_valid:
                self.hash_map.toast(error)
                return
            prefix = prefix.strip()
            self.rs_settings.put('ocr_serial_template_num_amount', int(num_amount), True)
            self.rs_settings.put('ocr_serial_template_prefix', prefix, True)
            self.rs_settings.put('ocr_serial_template_continuous_recognition', continuous_recognition, True)
            self.rs_settings.put('ocr_serial_template_use_prefix', use_prefix, True)
            self.rs_settings.put('ocr_serial_template_min_rec_amount', int(min_rec_amount), True)

            if use_prefix:
                patterns = [rf'^{prefix}', rf'([^\doO])(\d{{{num_amount}}})$']
            else:
                patterns = [rf'\d{{{num_amount}}}']
            self.rs_settings.put('ocr_serial_template_patterns', json.dumps(patterns), True)
            self.hash_map.toast('Шаблон сохранён')

        elif listener == 'ON_BACK_PRESSED':
            self.hash_map.show_screen("Документы")

        elif listener == 'vision_cancel':
            FlowDocDetailsScreen.ocr_nosql.destroy()

        elif listener == 'vision':
            FlowDocDetailsScreen.ocr_nosql.destroy()

    def _barcode_flow_on_start(self):

        id_doc = self.hash_map.get('id_doc')
        falseValueList = (0, '0', 'false', 'False', None)
        # Формируем таблицу карточек и запрос к базе

        doc_details = self.service.get_flow_table_data()
        table_data = self._prepare_table_data(doc_details)
        table_view = self._get_doc_table_view(table_data=table_data)

        if doc_details:
            # hashMap.put('id_doc', str(results[0]['id_doc']))

            # Признак, have_qtty_plan ЕстьПланПОКОличеству  -  Истина когда сумма колонки Qtty_plan > 0
            # Признак  have_mark_plan "ЕстьПланКОдовМаркировки – Истина, когда количество строк табл. RS_docs_barcodes с заданным id_doc и is_plan  больше нуля.
            # Признак have_zero_plan "Есть строки товара в документе" Истина, когда есть заполненные строки товаров в документе
            # Признак "Контролировать"  - признак для документа, надо ли контролировать

            qtext = '''
                SELECT distinct count(id) as col_str,
                sum(ifnull(qtty_plan,0)) as qtty_plan
                from RS_docs_table Where id_doc = :id_doc'''
            res = ui_global.get_query_result(qtext, {'id_doc': id_doc})
            if not res:
                have_qtty_plan = False
                have_zero_plan = False
            else:
                have_zero_plan = res[0][0] > 0  # В документе есть строки
                if have_zero_plan:
                    have_qtty_plan = res[0][1] > 0  # В документе есть колво план
                else:
                    have_qtty_plan = False
            # Есть ли в документе план по кодам маркировки
            qtext = '''
                SELECT distinct count(id) as col_str
                from RS_docs_barcodes Where id_doc = :id_doc AND is_plan = :is_plan'''
            res = ui_global.get_query_result(qtext, {'id_doc': id_doc, 'is_plan': '1'})
            if not res:
                have_mark_plan = False

            else:
                have_mark_plan = res[0][0] > 0
        else:
            have_qtty_plan = False
            have_zero_plan = False
            have_mark_plan = False

        self.hash_map.put('have_qtty_plan', str(have_qtty_plan))
        self.hash_map.put('have_zero_plan', str(have_zero_plan))
        self.hash_map.put('have_mark_plan', str(have_mark_plan))
        res = ui_global.get_query_result('SELECT control from RS_docs  WHERE id_doc = ?', (id_doc,))
        # Есть ли контроль плана в документе
        if res:
            if res[0][0]:
                if res[0][0] in falseValueList:
                    control = 'False'
                else:
                    control = 'True'

                # control = res[0][0] #'True'
            else:
                control = 'False'
        else:
            control = 'False'

        self.hash_map.put('control', control)
        self.hash_map.put("doc_barc_flow", table_view.to_json())

        if True in (have_qtty_plan, have_zero_plan, have_mark_plan, control):
            self.hash_map.put('toast',
                              'Данный документ содержит плановые строки. Список штрихкодов в него поместить нельзя')
            self.hash_map.put('ShowScreen', 'Документы')

    def on_post_start(self):
        pass

    def _get_doc_table_view(self, table_data):
        table_view = widgets.CustomTable(
            widgets.LinearLayout(
                self.LinearLayout(
                    self.TextView('Название'),
                    weight=3
                ),
                self.LinearLayout(
                    self.TextView('План'),
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

    def _get_doc_table_row_view(self):
        row_view = widgets.LinearLayout(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.LinearLayout(
                        self.TextView('@barcode'),
                        widgets.TextView(
                            Value='@name',
                            TextSize=15,
                            width='match_parent'
                        ),
                        width='match_parent',
                    ),
                    width='match_parent',
                    orientation='horizontal',
                    StrokeWidth=1
                ),
                width='match_parent',
                weight=3,
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
            orientation='horizontal',
            width='match_parent',
            BackgroundColor='#FFFFFF'
        )

        return row_view

    def _prepare_table_data(self, doc_details):

        if self.hash_map.get("event") == "onResultPositive":
            barcode = str(self.hash_map.get('fld_barcode'))
        else:
            barcode = str(self.hash_map.get('barcode_camera'))
        
        if barcode:
            doc_details = self._sort_table_by_barcode(doc_details, barcode)
        
        table_data = [{}]
        # self.hash_map.toast(self.hash_map.get('added_goods'))
        
        for record in doc_details:

            product_row = {'key': str(record['barcode']), 'barcode': str(record['barcode']),
                           'name': record['name'] if record['name'] is not None else '-нет данных-',
                           'qtty': str(record['qtty']),
                           '_layout': self._get_doc_table_row_view()}

            product_row['_layout'].BackgroundColor = '#FFFFFF' if record['name'] is not None else "#FBE9E7" 

            # это не работает судя по всему потому что нет в hash_map ключа added_goods
            if self._added_goods_has_key(product_row['key']):
                table_data.insert(1, product_row)
            else:
                table_data.append(product_row)

        return table_data

    def _sort_table_by_barcode(self, table, barcode):
        
        for i, row in enumerate(table):
            if str(row.get('barcode')) == barcode:
                del table[i]
                table.insert(0, row)
                break  

        return table 
    
    def _set_vision_settings(self) -> None:
        """Устанавливает настройки для кнопки распознавания текста"""
        num_amount = self.rs_settings.get('ocr_serial_template_num_amount') or 10
        use_prefix = self.rs_settings.get('ocr_serial_template_use_prefix')
        if use_prefix:
            prefix = self.rs_settings.get('ocr_serial_template_prefix')
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
            mesure_qty=1,
            min_freq=1,
        )
        self.hash_map.set_vision_settings(**rec_settings)

    def _validate_ocr_settings(
            self,
            min_rec_amount: str,
            num_amount: str,
            prefix: str,
            use_prefix: bool
    ) -> Tuple[bool, str]:
        """Валидация данных введенных в диалоге ШаблонРаспознавания"""
        if not min_rec_amount.isdigit() or int(min_rec_amount) == 0:
            error = 'Укажите минимальное количество обнаружений серийного номера'
            return False, error
        if not num_amount.isdigit():
            error = 'Количество цифр в шаблоне не корректно'
            return False, error
        if not 1 < int(num_amount) < 21:
            error = 'Количество цифр в шаблоне должно быть в интервале от 2 до 20'
            return False, error
        if prefix.isspace() and use_prefix:
            error = 'Не указан префикс'
            return False, error
        return True, ''

    @staticmethod
    def serial_key_recognition_ocr(hash_map: HashMap, rs_settings) -> None:
        """Находит в переданной из OCR строке серийный номер, по заданному шаблону"""
        ocr_nosql = FlowDocDetailsScreen.ocr_nosql
        ocr_text = hash_map.get("ocr_text")
        use_prefix = rs_settings.get('ocr_serial_template_use_prefix')
        num_amount = rs_settings.get('ocr_serial_template_num_amount') or 10
        patterns = rs_settings.get('ocr_serial_template_patterns')
        patterns = json.loads(patterns) if patterns else [rf'\d{{{num_amount}}}']
        for pattern in patterns:
            match_num = re.search(pattern, ocr_text)
            if not match_num:
                return
        result = match_num.group(2) if use_prefix else match_num.group()
        min_rec_amount = rs_settings.get('ocr_serial_template_min_rec_amount')
        result_in_memory = ocr_nosql.get(result)
        if result_in_memory is None:
            ocr_nosql.put(result, 1, True)
        elif result_in_memory < min_rec_amount:
            ocr_nosql.put(result, result_in_memory + 1, True)
        elif result_in_memory == min_rec_amount:
            ocr_nosql.put(result, result_in_memory + 1, True)
            db_services.FlowDocService(hash_map['id_doc']).add_barcode_to_database(result)
            hash_map.beep()
            hash_map.toast('Серийный номер: ' + result)
            if not rs_settings.get('ocr_serial_template_continuous_recognition'):
                hash_map.put("ocr_result", result)
                return
            for serial in json.loads(ocr_nosql.getallkeys()):
                if ocr_nosql.get(serial) < min_rec_amount:
                    ocr_nosql.put(serial, 0, True)


# ^^^^^^^^^^^^^^^^^^^^^ DocDetails ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== Goods select =============================

class BaseGoodSelect(Screen):
    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.id_doc = self.hash_map['id_doc']
        self.service = DocService(self.id_doc)
    
    def on_start(self):
        # Режим работы с мультимедиа и файлами по ссылкам (флаг mm_local)
        self.hash_map['mm_local'] = ''

        if not self.hash_map.get('qtty'):
            self.hash_map.put('qtty', '0')

        if not self.hash_map.get('new_qtty'):
            self.hash_map.put('new_qtty', self.hash_map.get('qtty'))

        if not self.hash_map.get('delta'):
            self._set_delta(reset=True)

    def on_input(self):

        listener = self.listener

        if listener is None:
            """Ввод дельты из современного поля ввода (через enter клавиатуры)"""
            if self._validate_delta_input():
                self._set_delta(0)

        elif listener == "btn_ok":
            self._handle_btn_ok()
        elif 'ops' in listener:
            """Префикс кнопок +/-, значение в названиях кнопок"""
            self._set_delta(int(listener[4:]))
        elif listener in ["btn_cancel", 'BACK_BUTTON', 'ON_BACK_PRESSED']:
            self._save_new_delta()
            self._set_delta(reset=True)
            self.hash_map.put('new_qtty', '')
            self.hash_map.show_screen("Документ товары")
        elif listener == 'btn_print':
            self.print_ticket()
        elif listener == 'barcode':
            self._process_the_barcode()    
        elif listener == "CardsClick":
            current_elem = self.hash_map.get_json('selected_card_data')
            self.print_ticket()
        elif listener == 'btn_doc_good_barcode':
            self.hash_map.show_screen("ТоварШтрихкоды")
        elif listener == 'btn_series_show':
            current_elem = self.hash_map.get_json('selected_card_data')
            self.hash_map['back_screen'] = self.hash_map.get_current_screen()
            self.open_series_screen('', current_elem)

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass
    
    def _handle_btn_ok(self):
        if int(self.hash_map.get('new_qtty')) < 0:
            self.hash_map.toast('Итоговое количество меньше 0')
            self.hash_map.playsound('error')
            self._set_delta(reset=True)
            return
        control = self.hash_map.get_bool('control')
        if control:
            if int(self.hash_map.get('new_qtty')) > int(self.hash_map.get('qtty_plan')):
                self.toast('Количество план в документе превышено')
                self.hash_map.playsound('error')
                self._set_delta(reset=True)
                return
        current_elem = self.hash_map.get_json('selected_card_data')
        qtty = self.hash_map['new_qtty']
        price = self.hash_map.get('price') or 0

        if self.hash_map.get('parent_screen') == 'ВыборТовараАртикул':
            self._handle_choice_by_article(current_elem, qtty)
        else:
            self._handle_choice_by_other(current_elem, qtty)

        self._set_delta(reset=True)
        self.hash_map.put('new_qtty', '')

    def _handle_choice_by_article(self, current_elem, qtty):
        if int(qtty) == int(current_elem['qtty']):
            self.hash_map.show_screen("ВыборТовараАртикул")
            return
        finded_goods_cards = self.hash_map.get('finded_goods_cards', from_json=True)
        cardsdata = finded_goods_cards['customcards']['cardsdata']

        card_data = next(elem for elem in cardsdata if elem['key'] == current_elem['key'])
        card_data['qtty'] = float(qtty)
        self.hash_map.put('finded_goods_cards', finded_goods_cards, to_json=True)
        self.hash_map.show_screen("ВыборТовараАртикул")

    def _handle_choice_by_other(self, current_elem, qtty):
        if int(qtty) != int(current_elem['qtty']):
            update_data = {
                'sent': 0,
                'qtty': float(qtty) if qtty else 0,
            }
            row_id = int(current_elem['key'])
            self.service.update_doc_table_row(data=update_data, row_id=row_id)
            self.service.set_doc_status_to_upload(self.hash_map.get('id_doc'))
            self.hash_map.show_screen("Документ товары")
        
    def _validate_delta_input(self):
        try:
            int(self.hash_map.get('delta'))
            return True
        except:
            self.toast('Введенное значение не является целым числом')
            self.hash_map.playsound('error')
            self._set_delta(reset=True)

    def _fill_none_values(self, data, keys, default=''):
        none_list = [None, 'None']
        for key in keys:
            data[key] = default if data[key] in none_list else data[key]

    def _match_record(self, record, id_good, id_property, id_unit):
        return (record['id_good'] == id_good and
                record['id_properties'] == id_property and
                record['id_unit'] == id_unit)

    def _find_matching_good(self, table_data, id_good, id_property, id_unit):
        for i, record in enumerate(table_data[1:], start=1):
            if self._match_record(record, id_good, id_property, id_unit):
                return i
        return None

    def _handle_found_barcode(self, res, id_good, id_property, id_unit):
        id_good_br, id_property_br, id_unit_br, ratio = res['id_good'], res['id_property'], res['id_unit'], int(res['ratio'])

        if id_good == id_good_br and id_property == id_property_br and id_unit == id_unit_br:
            self._set_delta(ratio)
            return True

        return False

    def _get_current_elem(self):
        return self.hash_map.get_json('selected_card_data')

    def _save_new_delta(self):
        new_qtty = float(self.hash_map.get('new_qtty')) if self.hash_map.get('new_qtty')  else 0
        if new_qtty < 0:
            self.hash_map.toast('Итоговое количество меньше 0')
            self.hash_map.playsound('error')
            self._set_delta(reset=True)
            return

        control = self.hash_map.get_bool('control')
        if control:
            if new_qtty > float(
                    self.hash_map.get('qtty_plan')):
                self.toast('Количество план в документе превышено')
                self.hash_map.playsound('error')
                self._set_delta(reset=True)
                return
        
        current_elem = self._get_current_elem()
            
        qtty = new_qtty
        # price = self.hash_map.get('price') or 0  # это не используется

        if self.hash_map.get('parent_screen') == 'ВыборТовараАртикул':
            if qtty == float(current_elem['qtty']) if current_elem['qtty'] else 0:
                self.hash_map.show_screen("ВыборТовараАртикул")
                return
            finded_goods_cards = self.hash_map.get('finded_goods_cards', from_json=True)
            cardsdata = finded_goods_cards['customcards']['cardsdata']

            card_data = next(elem for elem in cardsdata
                                if elem['key'] == current_elem['key'])
            card_data['qtty'] = qtty
            self.hash_map.put('finded_goods_cards', finded_goods_cards, to_json=True)
            self.hash_map.show_screen("ВыборТовараАртикул")

        else:
            if qtty != float(current_elem['qtty']):
                update_data = {
                    'sent': 0,
                    'qtty': qtty,
                    # 'price': float(price) # в Adr docs нет колонки прайс, не понятно нужна она вообще или нет
                }
                row_id = int(current_elem['key'])
                self.service.update_doc_table_row(data=update_data, row_id=row_id)
                self.hash_map.put('new_qtty', str(qtty))
                self.hash_map.put('qtty', str(qtty))

    def _process_the_barcode(self):
        barcode = self.hash_map.get('barcode_good_select')
        allowed_fact_input = self.rs_settings.get('allow_fact_input')
        
        if not (barcode and allowed_fact_input):
            self.hash_map.playsound('error')
            self.hash_map.toast('Штрихкод не найден в документе!') # пока тост, модалка очищает дельту
            # self.hash_map.show_dialog(listener='barcode_not_found', title='Штрихкод не найден в документе!')
            return

        id_good = self.hash_map.get('id_good')
        id_property = self.hash_map.get('id_property')
        id_unit = self.hash_map.get('id_unit')

        res = self.service.get_barcode(barcode)

        if res and self._handle_found_barcode(res, id_good, id_property, id_unit):
            return
        self.hash_map.playsound('error')
        self.hash_map.toast(f'Штрихкод не найден в документе!') # пока тост, модалка очищает дельту
        #self.hash_map.show_dialog(listener='barcode_not_found', title='Штрихкод не найден в документе!')        

    def _set_delta(self, value: int = 0, reset: bool = False):
        """Создаем (обнуляем) поле ввода"""
        if reset:
            delta_field = widgets.ModernField(default_text='', input_type=3)
            self.hash_map.put('new_qtty', self.hash_map.get('qtty'))
        else:
            delta = int(self.hash_map.get('delta')) + value if self.hash_map.get('delta') else value
            delta_field = widgets.ModernField(default_text=delta, input_type=3)
            self._set_result_qtty(delta)
        self.hash_map.put('delta', delta_field.to_json())

    def _set_result_qtty(self, delta):
        new_qtty = str(int(self.hash_map.get('qtty')) + delta)
        self.hash_map.put('new_qtty', new_qtty)

    def print_ticket(self):
        # Получим первый баркод документа

        barcode = db_services.BarcodeService().get_barcode_from_doc_table(self.hash_map.get('key'))

        param_list = {'Дата_док': 'Doc_data', 'Номенклатура': 'Good', 'Артикул': 'good_art',
                      'Серийный номер': 'good_sn', 'Характеристика': 'good_property'
            , 'Цена': 'good_price', 'ЕдИзм': 'good_unit', 'Ключ': 'key', 'Валюта': 'price_type'}
        for key in param_list.keys():
            param_list[key] = self.hash_map.get(param_list[key])
        if barcode:
            param_list['barcode'] = barcode
        else:
            param_list['barcode'] = '0000000000000'
        HtmlView.print_from_any_screen(
            self.hash_map,
            self.rs_settings,
            self.printing_template_name,
            data_for_printing=param_list)

    def open_series_screen(self, id_doc, current_elem):
        current_elem['id'] = current_elem.get('key')
        current_elem['id_doc'] = id_doc
        current_elem['warehouse'] = self.hash_map.get('warehouse')

        params_for_series_screen = json.dumps(current_elem['current_elem']
                                              if current_elem.get('current_elem') else current_elem)
        self.hash_map['params_for_series_screen'] = params_for_series_screen
        # self.hash_map.show_process_result(SeriesList.process_name, SeriesList.screen_name)
        self.hash_map.show_screen(SeriesList.screen_name)


class GoodsSelectScreen(BaseGoodSelect):
    screen_name = 'Товар выбор'
    process_name = 'Документы'
    printing_template_name = 'goods_select_screen'


    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        
    def on_start(self):
        super().on_start()
        
        doc_rows = self.service.get_doc_rows_count(self.id_doc)['doc_rows']
        doc_data = self.service.get_doc_details_data(self.id_doc, 0, doc_rows)
        doc_data.insert(0, {})
        self.hash_map.put('doc_rows', doc_rows)    
        self.hash_map.put('doc_data', doc_data, to_json=True)

        current_str = int(self.hash_map.get('selected_card_position'))
        current_page = int(self.hash_map.get('current_page'))
        items_on_page = int(self.hash_map.get('items_on_page'))
        doc_position = (current_page - 1) * items_on_page + current_str
        self.hash_map.put('good_str', f'{doc_position} / {doc_rows}')
        self.hash_map.put('selected_card_position', doc_position)

    def on_input(self):
        super().on_input()

        listener = self.listener

        if listener == 'btn_next_good':
            self._goods_selector("next")
        elif listener == 'btn_previous_good':
            self._goods_selector("previous")

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def get_doc(self):
        pass

    def _get_current_elem(self):
        selected_card_position = int(self.hash_map.get('selected_card_position'))
        table_data = self.hash_map.get('doc_data', from_json=True)
        current_elem = table_data[selected_card_position]
        current_elem['key'] = current_elem.get('id')
        return current_elem

    def _goods_selector(self, action, index = None):
        selected_card_position = int(self.hash_map.get('selected_card_position'))
        table_lines_qtty = int(self.hash_map.get('doc_rows'))
        table_data = self.hash_map.get('doc_data', from_json=True)
        
        if action == 'next':
            if selected_card_position != table_lines_qtty:
                pos = selected_card_position + 1
            else:
                pos = selected_card_position + 1 - table_lines_qtty
        elif action == 'previous':
            if selected_card_position != 1:
                pos = selected_card_position - 1
            else:
                pos = selected_card_position + table_lines_qtty - 1
        elif action == 'index' and index:
            pos = index

        current_str = pos
        current_elem = table_data[pos]

        # текущий элемент не найден или это заголовок таблицы
        if current_elem is None or 'good_name' not in current_elem:
            return

        title = '{} № {} от {}'.format(self.hash_map['doc_type'], self.hash_map['doc_n'], self.hash_map['doc_date'])
        put_data = {
            'Doc_data': title,
            'Good': current_elem['good_name'],
            'id_good': current_elem['id_good'],
            'good_art': current_elem['art'],
            'good_sn': current_elem['series_name'],
            'good_property': current_elem['properties_name'],
            'good_price': current_elem['price'] if 'price' in current_elem else '',
            'good_unit': current_elem['units_name'],
            'good_str': f'{current_str} / {table_lines_qtty}',
            'qtty_plan': self._format_quantity(current_elem['qtty_plan']) if current_elem['qtty_plan'] else 0,
            'good_plan': current_elem['qtty_plan'],
            'key': current_elem['id'],
            'price': current_elem['price'] if 'price' in current_elem else '',
            'price_type': current_elem['price_name'] if 'price_name' in current_elem else '',
            'qtty': self._format_quantity(current_elem['qtty']) if current_elem['qtty'] else 0,
            'new_qtty': self._format_quantity(current_elem['qtty']) if current_elem['qtty'] else 0,
        }

        self._fill_none_values(
            put_data,
            ('good_art', 'good_sn', 'good_property', 'good_price', 'good_plan', 'price', 'price_type'),
            default='отсутствует')

        self._save_new_delta()
        self.hash_map.put("selected_card_position", current_str)
        self.hash_map.put_data(put_data)

    def _handle_found_barcode(self, res, id_good, id_property, id_unit):
        id_good_br, id_property_br, id_unit_br, ratio = res['id_good'], res['id_property'], res['id_unit'], int(res['ratio'])

        if id_good == id_good_br and id_property == id_property_br and id_unit == id_unit_br:
            self._set_delta(ratio)
            return True

        if id_good != id_good_br:
            table_data = self.hash_map.get('doc_data', from_json=True) 	 
            match_index = self._find_matching_good(table_data, id_good_br, id_property_br, id_unit_br)

            if match_index is not None:
                self._goods_selector("index", index=match_index)
                self._set_delta(ratio)
                return True

        return False

    def _format_quantity(self, qtty):
        if qtty % 1 == 0:
            return int(qtty)
        else:
            return qtty
    
class AdrGoodsSelectScreen(BaseGoodSelect):
    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.id_doc = self.hash_map['id_doc']
        self.service = AdrDocService()
    
class GoodBarcodeRegister(Screen):
    screen_name = 'ТоварШтрихкоды'
    process_name = 'Документы'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = BarcodeService()
        self.goods_service = GoodsService()

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def on_start(self):

        good_name = self.hash_map.get("Good")
        self.hash_map.put("good_name_barcode", good_name)

    def on_input(self):

        listener = self.listener

        if listener in ['BACK_BUTTON', 'ON_BACK_PRESSED']:
            self.hash_map.remove("scanned_barcode")
            self.hash_map['property_select'] = ''
            self.hash_map['unit_select'] = ''
            self.hash_map.show_screen("Товар выбор")
        elif listener == 'property_select':
            self.hash_map.show_screen('Выбор характеристик')
        elif listener == 'unit_select':
            self.hash_map.show_screen('Выбор упаковки')
        elif listener == 'btn_ok':
            scanned_barcode = self.hash_map.get("scanned_barcode")
            if scanned_barcode is None:
                self.hash_map.toast("Поле штрихкод не заполнено. Отсканируйте штрихкод!")
            else:
                barcode_data = {
                    "id_good" : self.hash_map.get("id_good"),
                    "barcode" : scanned_barcode,
                    "id_property" :self.hash_map.get('selected_property_id'),
                    "id_unit" : self.hash_map.get('selected_unit_id'),
                }
                check_barcode = self.goods_service.get_values_from_barcode("barcode", scanned_barcode)
                if check_barcode:
                    query_good = self.goods_service.get_values_by_field("RS_goods", "id", check_barcode[0]['id_good'])
                    self.hash_map.put("ShowDialog", "Такой штрихкод уже есть")
                    self.hash_map.put("good_name_msg", query_good[0]['name'])
                    self.hash_map.put("property_msg", check_barcode[0]['property'])
                    self.hash_map.put("unit_msg", check_barcode[0]['unit'])
                else:
                    result = self.service.add_barcode(barcode_data)
                    if result is None:
                        self.hash_map.toast("Успешно добавлено.")
                        self.hash_map.show_screen("Товар выбор")
                    else:
                        print("Возникла ошибка при добавлении в БД:", result)
        elif self._is_result_positive('Такой штрихкод уже есть'):
            self.hash_map.remove("scanned_barcode")

class GoodItemBarcodeRegister(GoodBarcodeRegister):
    screen_name = 'ТоварШтрихкоды'
    process_name = 'Товары'

    def on_start(self):

        good_name = self.hash_map.get('good_name')
        self.hash_map.put("good_name_barcode", good_name)

    def on_input(self):

        listener = self.listener

        if listener in ['BACK_BUTTON', 'ON_BACK_PRESSED']:
            self.hash_map.remove("scanned_barcode")
            self.hash_map['property_select'] = ''
            self.hash_map['unit_select'] = ''
            self.hash_map.show_screen("Карточка товара")
        elif listener == 'property_select':
            self.hash_map.show_screen('Выбор характеристик')
        elif listener == 'unit_select':
            self.hash_map.show_screen('Выбор упаковки')
        elif listener == 'btn_ok':
            scanned_barcode = self.hash_map.get("scanned_barcode")
            if scanned_barcode is None:
                self.hash_map.toast("Поле штрихкод не заполнено. Отсканируйте штрихкод!")
            else:
                barcode_data = {
                    "id_good" : self.hash_map.get("selected_good_id"),
                    "barcode" : scanned_barcode,
                    "id_property" :self.hash_map.get('selected_property_id'),
                    "id_unit" : self.hash_map.get('selected_unit_id'),
                }
                check_barcode = self.goods_service.get_values_from_barcode("barcode", scanned_barcode)
                if check_barcode:
                    query_good = self.goods_service.get_values_by_field("RS_goods", "id", check_barcode[0]['id_good'])
                    self.hash_map.put("ShowDialog", "Такой штрихкод уже есть")
                    self.hash_map.put("good_name_msg", query_good[0]['name'])
                    self.hash_map.put("property_msg", check_barcode[0]['property'])
                    self.hash_map.put("unit_msg", check_barcode[0]['unit'])
                else:
                    result = self.service.add_barcode(barcode_data)
                    if result is None:
                        self.hash_map.toast("Успешно добавлено.")
                        self.hash_map.show_screen("Карточка товара")
                    else:
                        print("Возникла ошибка при добавлении в БД:", result)
        elif self._is_result_positive('Такой штрихкод уже есть'):
            self.hash_map.remove("scanned_barcode")

class GoodsSelectArticle(Screen):
    screen_name = 'ВыборТовараАртикул'
    process_name = 'Документы'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.id_doc = self.hash_map['id_doc']
        self.service = DocService(self.id_doc)

    def on_input(self):
        listener = self.listener
        if listener == 'CardsClick':
            if not self.rs_settings.get('allow_fact_input'):
                current_elem = self.hash_map.get('selected_card_data', from_json=True)
                self._update_doc_table_row(current_elem, current_elem['qtty'] + 1.0)
                self.hash_map.delete('finded_goods_cards')
                self.hash_map.show_screen('Документ товары')
                return
            current_element = json.loads(self.hash_map.get('selected_card_data'))
            selected_card_position = self.hash_map["selected_card_position"]
            table_lines_qtty = self.hash_map['table_lines_qtty']
            put_data = {
                'Doc_data': f'{self.hash_map["doc_type"]} № {self.hash_map["doc_n"]} от {self.hash_map["doc_date"]}',
                'Good': current_element['name'],
                'id_good': current_element['id_good'],
                'id_unit': current_element['id_unit'],
                'id_property': current_element['id_properties'],
                'good_art': current_element['art'],
                'good_sn': current_element['series_name'],
                'good_property': current_element['property_name'],
                'good_price': current_element['price'],
                'good_unit': current_element['units_name'],
                'good_str': f'{selected_card_position} / {table_lines_qtty}',
                'qtty_plan': current_element['qtty_plan'],
                'good_plan': current_element['qtty_plan'],
                'key': current_element['key'],
                'price': current_element['price'],
                'price_type': current_element['price_name'],
                'qtty': current_element['qtty'] if current_element['qtty'] and float(current_element['qtty']) != 0 else '',
            }
            self.hash_map.put_data(put_data)
            self.hash_map.show_screen("Товар выбор")

        elif listener == 'ON_BACK_PRESSED':
            self.hash_map.delete('finded_goods_cards')
            self.hash_map.show_screen("Документ товары")

        elif listener == 'update_docs_table_article':
            finded_goods_cards = self.hash_map.get('finded_goods_cards', from_json=True)
            cardsdata = finded_goods_cards['customcards']['cardsdata']

            for card_data in cardsdata:
                self._update_doc_table_row(card_data)
            self.hash_map.delete('finded_goods_cards')
            self.hash_map.show_screen('Документ товары')

    def on_start(self):
        if not self.hash_map['finded_goods_cards']:
            articles = self.hash_map['finded_articles']
            if not articles:
                raise Exception('GoodsSelectArticle on_start. Не переданы артикулы')
            goods = self.service.get_goods_list_with_doc_data(articles.split(';'))
            self.hash_map.put('selected_goods', json.dumps(goods))
            cards_data = self._get_goods_list_data(goods)
            goods_cards = self._get_goods_cards_view(cards_data)
            self.hash_map['finded_goods_cards'] = goods_cards.to_json()

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _get_goods_cards_view(self, cards_data: List[Dict]) -> widgets.CustomCards:
        card_title_text_size = str(self.rs_settings.get('CardTitleTextSize'))
        card_text_size = str(self.rs_settings.get('CardTextSize'))

        v_layout_1 = widgets.LinearLayout(
                widgets.TextView(
                    Value='@name',
                    width='match_parent',
                    gravity_horizontal='left',
                    TextSize=card_title_text_size,
                    TextColor='#7A005C'
                ),
                widgets.TextView(
                    Value='@code',
                    TextSize=card_text_size,
                ),
                widgets.TextView(
                    Value='@art',
                    TextSize=card_text_size,
                ),
                widgets.TextView(
                    Value='@unit',
                    TextSize=card_text_size,
                ),
                widgets.TextView(
                    Value='@type_good',
                    TextSize=card_text_size,
                ),
                widgets.TextView(
                    Value='@property_name',
                    TextSize=card_text_size,
                ),
                orientation='vertical',
                width='match_parent',
                StrokeWidth=1,
                weight=2
            )
        v_layout_2 = widgets.LinearLayout(
                widgets.TextView(
                    Value='План:',
                    TextSize=card_text_size,
                    height='match_parent',
                    weight=1,
                ),
                widgets.TextView(
                    Value='Факт:',
                    TextSize=card_text_size,
                    height='match_parent',
                    weight=1,
                ),

                orientation='vertical',
                width='match_parent',
                height='match_parent',
                StrokeWidth=1,
                weight=1
            )
        v_layout_3 = widgets.LinearLayout(
                widgets.TextView(
                    Value='@qtty_plan',
                    TextSize=card_text_size,
                    height='match_parent',
                    weight=1,
                ),
                widgets.TextView(
                    Value='@qtty',
                    TextSize=card_text_size,
                    height='match_parent',
                    weight=1,
                ),
                orientation='vertical',
                width='match_parent',
                height='match_parent',
                StrokeWidth=1,
                weight=1
            )
        h_layout = widgets.LinearLayout(
                v_layout_1, v_layout_2, v_layout_3,
                orientation='horizontal',
                width='match_parent'
            )
        goods_cards = widgets.CustomCards(
            h_layout,
            options=widgets.Options().options,
            cardsdata=cards_data
        )
        return goods_cards

    def _get_goods_list_data(self, goods_list: List[Dict]) -> List[Dict]:
        cards_data = []

        for record in goods_list:
            single_card_data = {
                'key': record['doc_table_id'],
                'code': record.get('code', '—'),
                'name': record['name'],
                'art': record.get('art', '—'),
                'description': record.get('description', '—'),
                'unit': record.get('id_unit', '—'),
                'units_name': record['unit_name'],
                'type_good': record.get('type_good', '—'),
                'qtty_plan': record['qtty_plan'],
                'qtty': record['qtty'],
                'property_name': record['property_name'],
                'series_name': record['series_name'],
                'price': record['price'],
                'price_name': record['price_name'],
            }
            cards_data.append(single_card_data)

        return cards_data

    def _update_doc_table_row(self, data: Dict, qtty: Optional[float] = None):
        update_data = {
            'sent': 0,
            'qtty': qtty or float(data['qtty']),
        }
        row_id = int(data['key'])
        self.service.update_doc_table_row(data=update_data, row_id=row_id)
        self.service.set_doc_status_to_upload(self.hash_map.get('id_doc'))

# ^^^^^^^^^^^^^^^^^^^^^ Goods select ^^^^^^^^^^^^^^^^^^^^^^^^^^^^


# ==================== Goods(Process) =============================
class GoodsListScreen(Screen):
    screen_name = 'Товары список'
    process_name = 'Товары'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = GoodsService()

    def on_start(self) -> None:
        cards_data = self._get_goods_list_data(self.hash_map.get('selected_goods_type'))
        goods_cards = self._get_goods_cards_view(cards_data)
        self.hash_map['goods_cards'] = goods_cards.to_json()
        self.hash_map['return_selected_data'] = ""

    def on_input(self):
        listener = self.listener
        if listener == "CardsClick":
            self.hash_map.put('selected_good_id', self.hash_map.get("selected_card_key"))
            self.hash_map.put('barcode', '')
            self.hash_map.show_screen("Карточка товара")
        elif listener == "select_goods_type":
            self.hash_map.show_screen("Выбор категории товаров")
        elif listener == "ON_BACK_PRESSED":
            self.hash_map.put("FinishProcess", "")
        elif listener == 'barcode':
            self._identify_barcode_goods()

    def on_post_start(self):
        pass

    def show(self, args=None):
        self._validate_screen_values()
        self.hash_map.show_screen(self.screen_name, args)

    def _get_goods_list_data(self, selected_good_type=None) -> list:
        results = self.service.get_goods_list_data(selected_good_type)
        cards_data = []
        for record in results:
            single_card_data = {
                'key': record['id'],
                'code': record['code'],
                'name': record['name'],
                'art': record['art'] if record['art'] else "—",
                'unit': record['unit'] if record['unit'] else "—",
                'type_good': record['type_good'],
                'description': record['description'] if record['description'] else "—"
            }
            cards_data.append(single_card_data)

        return cards_data

    def _get_goods_cards_view(self, cards_data):
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')
        card_text_size = self.rs_settings.get('CardTextSize')

        goods_cards = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@name',
                    width='match_parent',
                    gravity_horizontal='left',
                    TextSize=card_title_text_size,
                    TextColor='#7A005C'
                ),
                widgets.TextView(
                    Value='@code',
                    TextSize=card_text_size,
                ),
                widgets.TextView(
                    Value='@art',
                    TextSize=card_text_size,
                ),
                widgets.TextView(
                    Value='@unit',
                    TextSize=card_text_size,
                ),
                widgets.TextView(
                    Value='@type_good',
                    TextSize=card_text_size,
                ),

                orientation='vertical',
                width='match_parent',
            ),
            options=widgets.Options().options,
            cardsdata=cards_data
        )

        return goods_cards

    def _identify_barcode_goods(self):
        if self.hash_map.get('barcode'):
            barcode = self.hash_map.get('barcode')
            values = self.service.get_values_from_barcode("barcode", barcode)
            if values:
                item_id = values[0]['id_good']
                item_values = self.service.get_goods_list_data(item_id=item_id)[0]
                self.hash_map.put("selected_good_id", item_id)
                self.hash_map.put("good_name", item_values['name'])
                self.hash_map.put("good_art", item_values['art'] if item_values['art'] else "—")
                self.hash_map.put("good_code", item_values['code'])
                self.hash_map.put("good_descr", item_values['description'] if item_values['description'] else "—")
                self.hash_map.put("good_type", item_values['type_good'])
                self.hash_map.show_screen('Карточка товара')
            else:
                self.toast('Товар не распознан по штрихкоду')
                self.hash_map.playsound('error')


class SelectGoodsType(Screen):
    screen_name = 'Выбор категории товаров'
    process_name = 'Товары'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = GoodsService()

    def on_start(self):
        goods_types_data = self._get_goods_types_data()
        goods_types_cards = self._get_goods_types_cards_view(goods_types_data)
        self.hash_map['goods_types_cards'] = goods_types_cards.to_json()
        self.hash_map['return_selected_data'] = ""

    def on_input(self):
        listener = self.listener
        if listener == "CardsClick":
            card_data = self.hash_map.get("selected_card_data", from_json=True)
            type_id = card_data['key']
            type_name = card_data['name']
            self.hash_map.put('select_goods_type', type_name)
            self.hash_map.put('selected_goods_type', type_id)
            self.hash_map.put("ShowScreen", "Товары список")
        elif listener == "ON_BACK_PRESSED":
            self.hash_map.put('select_goods_type', "")
            self.hash_map.put('selected_goods_type', "")
            self.hash_map.put("BackScreen", "")

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _get_goods_types_data(self):
        goods_types_data_result = self.service.get_all_goods_types_data()
        goods_types_data = []
        for record in goods_types_data_result:
            single_card_data = {
                'key': record['id'],
                'name': record['name'],
            }
            goods_types_data.append(single_card_data)
        return goods_types_data

    def _get_goods_types_cards_view(self, goods_types_data):
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')

        type_cards = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@name',
                    width='match_parent',
                    gravity_horizontal='left',
                    TextSize=card_title_text_size,
                    TextColor='#000000'
                ),

                orientation='vertical',
                width='match_parent',
            ),
            options=widgets.Options().options,
            cardsdata=goods_types_data
        )

        return type_cards


class ItemCard(Screen):
    screen_name = 'Карточка товара'
    process_name = 'Товары'
    printing_template_name = 'item_card'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = GoodsService()

    def on_start(self):
        pass

    def on_input(self):
        listeners = {
            'ON_BACK_PRESSED': self._back_screen,
            'CardsClick': self._print_ticket,
            'btn_print': self._print_ticket,
            'to_prices': self._to_prices,
            'to_balances': self._to_balances,
            'btn_item_good_barcode': lambda : self.hash_map.show_screen("ТоварШтрихкоды")
        }
        if self.listener in listeners:
            listeners[self.listener]()

    def on_post_start(self):
        selected_good_id = self.hash_map.get("selected_good_id")
        barcode = self.hash_map.get('barcode')
        if barcode:
            goods_barcode = self.service.get_values_from_barcode("barcode", barcode)
        elif selected_good_id:  # Выбор товара через карточку
            goods_barcode = self.service.get_values_from_barcode("id_good", selected_good_id)

        if goods_barcode:
            variants_cards_data = self._get_variants_cards_data(goods_barcode)
            variants_cards = self._get_variants_cards_view(variants_cards_data)
            self.hash_map['barcode_cards'] = variants_cards.to_json()
            self.hash_map.put("load_info", "")
        else:
            self.hash_map.put("load_info", "Данные о характеристиках отсутствуют")

    def show(self, args=None):
        pass

    def _back_screen(self):
        if self.hash_map.get('barcode_cards'):
            self.hash_map.put('barcode_cards', '')
        self.hash_map.show_screen("Товары список")

    def _to_balances(self):
        dict_data = {'input_item_id': self.hash_map.get('selected_good_id'),
                     'item_art_input': self.hash_map.get('good_art'),
                     'selected_object_name': f'{self.hash_map.get("good_name")}, {self.hash_map.get("good_code")}',
                     'object_name': self.hash_map.get('good_name'),
                     "return_to_item_card": "true",
                     'ShowProcessResult': 'Остатки|Проверить остатки', "noRefresh": ''}
        self.hash_map.put_data(dict_data)

    def _to_prices(self):
        dict_data = {'input_good_id': self.hash_map.get('selected_good_id'),
                     'input_good_art': self.hash_map.get('good_art'),
                     'prices_object_name': f'{self.hash_map.get("good_name")}, {self.hash_map.get("good_code")}',
                     "return_to_item_card": "true",
                     'object_name': self.hash_map.get('good_name'),
                     'ShowProcessResult': 'Цены|Проверка цен', "noRefresh": ''}
        self.hash_map.put_data(dict_data)


    @staticmethod
    def _get_variants_cards_data(goods_barcode):
        variants_cards_data = []
        i = 0
        for element in goods_barcode:
            c = {"key": str(i), "barcode": element['barcode'],
                 "properties": element['property'] if element['property'] else "",
                 "unit": element['unit'], "series": element['series']}
            variants_cards_data.append(c)
            i += 1
        return variants_cards_data

    def _get_variants_cards_view(self, cards_data):
        card_title_text_size = self.rs_settings.get('CardTitleTextSize') if self.rs_settings.get(
            'CardTitleTextSize') else 20
        card_text_size = self.rs_settings.get('CardTextSize') if self.rs_settings.get('CardTextSize') else 15

        variants_cards = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@properties',
                        width='match_parent',
                        gravity_horizontal='center',
                        TextSize=card_title_text_size,
                        TextColor='#000000'
                    ),
                    orientation='horizontal',
                    width='match_parent',
                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@unit',
                        width='match_parent',
                        gravity_horizontal='left',
                        TextSize=card_text_size,
                        TextColor='#000000',
                        weight=1
                    ),
                    widgets.TextView(
                        Value='@barcode',
                        width='match_parent',
                        gravity_horizontal='left',
                        TextSize=card_text_size,
                        TextColor='#000000',
                        weight=1
                    ),
                    orientation='horizontal',
                    width='match_parent',
                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@series',
                        width='match_parent',
                        gravity_horizontal='center',
                        TextSize=card_text_size,
                        TextColor='#000000'
                    ),
                    orientation='horizontal',
                    width='match_parent',
                ),
                orientation='vertical',
                width='match_parent',
            ),
            options=widgets.Options().options,
            cardsdata=cards_data
        )
        return variants_cards

    def _print_ticket(self):
        current_card = self._get_selected_card_data()

        data_dict = {
            'barcode': current_card.get('barcode', '0000000000000'),
            'Номенклатура': self.hash_map.get('good_name'),
            'Характеристика': current_card.get('properties', ''),
            'Упаковка': current_card.get('unit', '')
        }

        HtmlView.print_from_any_screen(
            self.hash_map,
            self.rs_settings,
            self.printing_template_name,
            data_for_printing=data_dict)

    def _get_selected_card_data(self) -> dict:
        result = {}
        card_key = self.hash_map.get('selected_card_key')
        cards = self.hash_map.get_json("barcode_cards")

        if card_key and cards:
            result = cards['customcards']['cardsdata'][int(card_key)]

        return result

class ItemCardOfflineScreen(ItemCard):

    def _to_prices(self):
        self.hash_map.show_dialog('prices_not_available_modal', title='В этом продукте запрос цен недоступен')

    def _to_balances(self):
        self.hash_map.show_dialog('balances_not_available_modal', title='В этом продукте запрос остатков недоступен')

    def _print_ticket(self):
        self.hash_map.show_dialog('print_ticket_not_available_modal', title='В этом продукте печать недоступна')



# ^^^^^^^^^^^^^^^^^^^^^ Goods(Process) ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== GoodsBalances =============================

class GoodsBalancesItemCard(Screen):
    screen_name = 'Проверить остатки'
    process_name = 'Остатки'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = GoodsService()
        self.hs_service = hs_services.HsService(self.get_http_settings())
        self.table_type = 'warehouses'

    def on_start(self):
        self._set_visibility_on_start(['error_msg', 'selected_object_name', 'selected_cell_name', 'selected_wh_name',
                                       'item_barcode'])
        if not self.hash_map.get('balances_table'):
            self.hash_map.put("Show_get_balances_controls", "1")
            self.hash_map.put("Show_show_filters", "-1")
        if self.hash_map.get_bool('new_art'):
            self._check_item_variants()

    def on_input(self):

        listener = self.listener

        if listener == 'wh_select':
            self.hash_map.show_screen('Выбор склада')
        elif listener == 'get_balance_btn':
            self._get_balances()
        elif listener == 'barcode':
            self._identify_barcode_balances()
        elif listener == 'ON_BACK_PRESSED':
            self._reset_balances_tables()
            if self.hash_map.get('return_to_item_card'):
                self.hash_map.put('noRefresh', '')
                self.hash_map.put("FinishProcessResult", "")
            else:
                self.hash_map.put("FinishProcess", "")

        elif listener == 'show_filters':
            self.hash_map.put("Show_get_balances_controls", "1")
            self.hash_map.put("Show_show_filters", "-1")
        elif listener == "CardsClick":
            card_data = self.hash_map.get('selected_card_data', from_json=True)
            self.hash_map.put_data({'selected_object_name': f"{card_data['name']}, {card_data['code']}",
                                    "input_item_id": card_data['id'], 'item_code': card_data['code'],
                                    'variant_selected': True})
            self.hash_map.remove('new_art')
        elif self._is_result_positive('Выберите вариант товара:'):
            self.hash_map.put("Show_get_balances_controls", "1")

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _get_balances(self):
        if self.hash_map.get('item_art_input') != self.hash_map.get('good_art') and not \
                self.hash_map.get_bool('variant_selected'):
            self.hash_map.put('new_art', True)
            self.validate_input()
        raw_balances_data = self._get_balances_data()
        balances_data = self._prepare_table_data(raw_balances_data)
        balances_table = self._get_balances_table_view(balances_data)
        self.hash_map.put_data({'balances_table': balances_table.to_json(), 'Show_get_balances_controls': '-1',
                                'Show_show_filters': '1', 'property_id': '', 'from_barcode': False, 'item_code': '',
                                'variant_selected': False})

    def validate_input(self):
        self._process_input_item_art()
        self._process_input_cell()

        if not (self.hash_map.get('item_art_input') or self.hash_map.get('cell_input') or self.hash_map.get('wh_select')
                or self.hash_map.get('selected_cell_id')):
            self.hash_map.put_data({'balances_tables': '', 'object_name': '', 'cell_name': '',
                                    'error_msg': "Должен быть выбран склад, товар или ячейка"})

    def _process_input_item_art(self):

        item_art_input = self.hash_map.get('item_art_input')
        if self.hash_map.get('item_art_input'):
            item_values_result = self.service.get_values_by_field(table_name='RS_goods', field='art',
                                                                  field_value=item_art_input)
            if item_values_result:
                self.hash_map.put_data({'object_name': item_values_result[0]['name'],
                                        'input_item_id': item_values_result[0]['id'],
                                        'selected_object_name': f'{item_values_result[0]["name"]}, {item_values_result[0]["code"]}',
                                        'item_code': item_values_result[0]['code'], 'error_msg': '',
                                        'item_art_input': self.hash_map.get('item_art_input'), 'item_barcode': ''})

            else:
                if item_art_input != '—' and self.hash_map.get('return_to_item_card'):
                    self.hash_map.put('error_msg', " Товар с артикулом " + "'" + item_art_input + "'" + " не найден")
        else:
            self.hash_map.put('input_item_id', '')
            self.hash_map.put('object_name', '')
            self.hash_map.put('selected_object_name', '')

    def _process_input_cell(self):
        if self.hash_map.get('cell_input'):
            cell_values_result = self.service.get_values_by_field(table_name='RS_cells', field='name',
                                                                  field_value=self.hash_map.get('cell_input'))
            if cell_values_result:
                self.table_type = 'cells'
                self.hash_map.put('selected_cell_id', cell_values_result[0]['id'])
                self.hash_map.put('cell_name', self.hash_map.get('cell_input'))

            else:
                if self.hash_map.get('error_msg'):
                    self.hash_map.put('error_msg', self.hash_map.get('error_msg') + "\n" + " Ячейка c именем " + "'" +
                                      self.hash_map.get('cell_input') + "'" + " не найдена")
                else:
                    self.hash_map.put('error_msg', " Ячейка c именем " + "'" + self.hash_map.get('cell_input') + "'" + " не найдена")

        else:
            self.hash_map.put('selected_cell_id', '')
            self.hash_map.put('cell_name', '')
            self.hash_map.put('selected_cell_name', '')

    def _identify_barcode_balances(self):
        no_data = False
        barcode_data = self.service.get_values_by_field(table_name="RS_barcodes", field='barcode',
                                                        field_value=self.hash_map.get('barcode'))
        if barcode_data:
            self.hash_map.put('item_barcode', self.hash_map.get('barcode'))

            if barcode_data[0].get('id_property'):
                self.hash_map.put('property_id', barcode_data[0].get('id_property'))

            if barcode_data[0].get('id_good'):
                item_id = barcode_data[0]['id_good']

                item_data = self.service.get_values_by_field(table_name="RS_goods", field='id', field_value=item_id)
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
            cell_data = self.service.get_values_by_field(table_name="RS_cells", field='barcode',
                                                         field_value=self.hash_map.get('barcode'))

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

        data = self.hs_service.get_balances_goods(id_good=self.hash_map.get('input_item_id'),
                                                  id_cell=self.hash_map.get('selected_cell_id'),
                                                  id_warehouse=self.hash_map.get('selected_wh_id')).data
        return data

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

    def _prepare_table_data(self, raw_balances_data):
        table_data = [{}]
        for el in raw_balances_data:
            storage_name = str(el['name_warehouse']) if self.table_type == 'warehouses' else str(el['name_cell'])
            table_row = {'key': str(el['id_good']),
                         'item_name': str(el['name_good']),
                         'storage_name': storage_name,
                         'qtty': str(el['qtty']),
                         'properties': str(el['name_property'] or '—'),
                         '_layout': self._get_item_table_row_view({'storage_name_len': len(storage_name),
                                                                   'item_name_len': len(el['name_good'])})}
            if self.hash_map.get('property_id'):
                """Фильтруем по взятой характеристике"""
                if self.hash_map.get('property_id') == str(el['id_property']):
                    table_data.append(table_row)
            else:
                table_data.append(table_row)

        return table_data

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
            item_values_result = self.service.get_values_by_field(table_name='RS_goods', field='art',
                                                                  field_value=item_art_input)
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


class SelectWH(Screen):
    screen_name = 'Выбор склада'
    process_name = 'Остатки'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = GoodsService()

    def on_start(self):
        cards_data = self._get_data(table_name='RS_warehouses')
        cards = self._get_cards(cards_data)
        self.hash_map.put('wh_cards', cards.to_json())

    def on_input(self):
        listener = self.listener

        if listener == "CardsClick":
            self.hash_map['selected_wh_id'] = self.hash_map.get("selected_card_key")
            wh_name = self.service.get_values_by_field(table_name='RS_warehouses', field='id',
                                                       field_value=self.hash_map.get
                                                       ("selected_card_key"))[0]['name']
            self.hash_map['wh_select'] = wh_name
            self.hash_map['selected_wh_name'] = wh_name
            self.hash_map.show_screen('Проверить остатки')

        elif listener == "ON_BACK_PRESSED" or 'go_back':
            self.hash_map['selected_wh_id'] = ''
            self.hash_map['selected_wh_name'] = ''
            self.hash_map['wh_select'] = ''
            self.hash_map.show_screen('Проверить остатки')

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _get_data(self, table_name):
        raw_data = self.service.get_select_data(table_name)
        cards_data = []
        for element in raw_data:
            card_data = {
                'key': element['id'],
                'name': element['name']
            }
            cards_data.append(card_data)
        return cards_data

    def _get_cards(self, cards_data):
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')
        card_text_size = self.rs_settings.get('CardTextSize')

        cards = widgets.CustomCards(
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
                ))
            ,
            options=widgets.Options().options,
            cardsdata=cards_data
        )
        return cards


# ^^^^^^^^^^^^^^^^^^^^^ GoodsBalances ^^^^^^^^^^^^^^^^^^^^^^^^^^^^


# ==================== GoodsPrices =============================
class GoodsPricesItemCard(GoodsBalancesItemCard):
    screen_name = 'Проверка цен'
    process_name = 'Цены'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)

    def on_start(self):
        self._set_visibility_on_start(['prices_error_msg', 'prices_object_name', 'selected_price_type_name',
                                       'selected_property_name', 'selected_unit_name', 'barcode_info'])
        if not self.hash_map.get('prices_table'):
            self.hash_map.put("Show_get_prices_controls", "1")
            self.hash_map.put("Show_show_filters", "-1")

    def on_input(self):

        listener = self.listener

        if listener == 'price_type_select':
            self.hash_map.show_screen('Выбор типа цены')
        elif listener == 'property_select':
            self.hash_map.show_screen('Выбор характеристик')
        elif listener == 'unit_select':
            self.hash_map.show_screen('Выбор упаковки')
        elif listener == 'get_prices_btn':
            self._get_prices()
        elif listener == 'barcode':
            self._identify_barcode_prices()
        elif listener == 'ON_BACK_PRESSED':
            self._reset_prices_tables()
            if self.hash_map.get('return_to_item_card'):
                self.hash_map.put('noRefresh', '')
                self.hash_map.put("FinishProcessResult", "")
            else:
                self.hash_map.put("FinishProcess", "")
        elif listener == 'show_filters':
            self.hash_map.put("Show_get_prices_controls", "1")
            self.hash_map.put("Show_show_filters", "-1")

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _get_prices(self):
        self._validate_input()
        raw_prices_data = self._get_prices_data()
        prices_data = self._prepare_table_data(raw_prices_data)
        prices_table = self._get_prices_table_view(prices_data)
        self.hash_map.put('prices_table', prices_table.to_json())
        # self.hash_map.show_screen("Таблица цен")
        self.hash_map.put("Show_get_prices_controls", "-1")
        self.hash_map.put("Show_show_filters", "1")

    def _validate_input(self):
        self._process_input_good_art()
        if not (self.hash_map.get('input_good_art')):
            self.hash_map.put('prices_tables', '')
            self.hash_map.put('prices_object_name', '')
            self.hash_map.put('prices_error_msg', "Должен быть выбран товар")

    def _process_input_good_art(self):
        item_art_input = self.hash_map.get('input_good_art')
        if item_art_input:
            item_values_result = self.service.get_values_by_field(table_name='RS_goods', field='art',
                                                                  field_value=item_art_input)
            if item_values_result:
                self.hash_map.put('prices_object_name', item_values_result[0]['name'])
                self.hash_map.put('input_good_id', item_values_result[0]['id'])
                if item_values_result[0]['id'] != self.hash_map.get('selected_good_id'):
                    self.hash_map.put('prices_object_name', '')
                self.hash_map.put('prices_object_name', f'{item_values_result[0]["name"]}, '
                                                        f'{item_values_result[0]["code"]}')
                self.hash_map.put('good_code', item_values_result[0]['code'])
                self.hash_map.put('error_msg', "")
                self.hash_map.put('item_art_input', self.hash_map.get('item_art_input'))
            else:
                if item_art_input != '—' and self.hash_map.get('return_to_item_card'):
                    self.hash_map.put('error_msg', " Товар с артикулом " + "'" + item_art_input + "'" + " не найден")
        else:
            self.hash_map.put('input_good_id', '')
            self.hash_map.put('prices_object_name', '')

    def _identify_barcode_prices(self):
        self.hash_map.put('barcode_info', str(self.hash_map.get('barcode')))
        self.hash_map.put('prices_object_name', '')
        no_data = False

        barcode_data = self.service.get_values_by_field(table_name="RS_barcodes", field='barcode',
                                                        field_value=self.hash_map.get('barcode'))
        if barcode_data[0]:
            if barcode_data[0].get('id_property'):
                self.hash_map.put('selected_property_id', barcode_data[0].get('id_property'))
                selected_property_name = self.service.get_values_by_field(table_name='RS_properties', field='id',
                                                                          field_value=barcode_data[0].get(
                                                                              'id_property'))
                if selected_property_name[0].get('name'):
                    self.hash_map.put('selected_property_name', selected_property_name[0].get('name'))
            else:
                self.hash_map.put('selected_property_id', '')
                self.hash_map.put('selected_property_name', '')

            if barcode_data[0].get('id_good'):
                item_id = barcode_data[0]['id_good']

                item_data = self.service.get_values_by_field(table_name="RS_goods", field='id', field_value=item_id)
                if item_data[0]:
                    self.hash_map.put('input_good_id', item_id)
                    if item_data[0]['art']:
                        self.hash_map.put('input_good_art', item_data[0]['art'])
                    else:
                        self.hash_map.put('input_good_art', '—')
                    self.hash_map.put('prices_object_name', item_data[0]['name'])
                    self.hash_map.put('error_msg', "")

        else:
            no_data = True
            self.hash_map.put('object_name', "")
            self.hash_map.put('error_msg', "Штрихкод не распознан")

        if not no_data:
            self._get_prices()

    def _reset_prices_tables(self):
        vars_list = ['input_good_art', 'prices_object_name', 'selected_price_type_id', 'selected_price_type_name',
                     'price_type_select', 'selected_property_id', 'selected_property_name', 'property_select',
                     'selected_unit_id', 'selected_unit_name', 'unit_select', 'prices_custom_table', 'input_good_id',
                     'barcode', 'barcode_info', 'prices_table']
        dict_data = {var: "" for var in vars_list}
        self.hash_map.put_data(dict_data)

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


class SelectPriceType(SelectWH):
    screen_name = 'Выбор типа цены'
    process_name = 'Цены'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = GoodsService()

    def on_start(self):
        cards_data = self._get_data(table_name='RS_price_types')
        price_type_cards = self._get_cards(cards_data)
        self.hash_map.put('price_type_cards', price_type_cards.to_json())

    def on_input(self):
        listener = self.listener

        if listener == "CardsClick":
            selected_price_type_id = self.hash_map.get("selected_card_key")
            selected_type_name = self.service.get_values_by_field(table_name='RS_price_types', field='id',
                                                                  field_value=self.hash_map.get("selected_card_key"))[
                0]['name']
            self.hash_map.put('selected_price_type_id', selected_price_type_id)
            self.hash_map['price_type_select'] = selected_type_name
            self.hash_map['selected_price_type_name'] = selected_type_name
            self.hash_map.show_screen('Проверка цен')

        elif listener == "ON_BACK_PRESSED" or 'back_to_prices':
            self.hash_map['selected_price_type_id'] = ''
            self.hash_map['price_type_select'] = ''
            self.hash_map['selected_price_type_name'] = ''
            self.hash_map.show_screen('Проверка цен')


class SelectProperties(GoodsPricesItemCard):
    screen_name = 'Выбор характеристик'
    process_name = 'Цены'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = GoodsService()

    def on_start(self):
        self._validate_input()
        cards_data = self._get_data()
        properties_cards = self._get_cards(cards_data)
        self.hash_map.put('property_cards', properties_cards.to_json())

    def _get_data(self):
        table_name = "RS_properties"
        raw_data = self.service.get_values_by_field(table_name, field='id_owner',
                                                    field_value=self.hash_map.get('input_good_id'))
        cards_data = []
        for element in raw_data:
            card_data = {
                'key': element['id'],
                'name': element['name']
            }
            cards_data.append(card_data)
        return cards_data

    def _get_cards(self, cards_data):
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')
        card_text_size = self.rs_settings.get('CardTextSize')

        cards = widgets.CustomCards(
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
                ))
            ,
            options=widgets.Options().options,
            cardsdata=cards_data
        )
        return cards

    def on_input(self):
        listener = self.listener

        if listener == "CardsClick":
            selected_property_id = self.hash_map.get("selected_card_key")
            selected_property_name = self.service.get_values_by_field(table_name='RS_properties', field='id',
                                                                      field_value=selected_property_id)[0]['name']
            self.hash_map.put('selected_property_id', selected_property_id)
            self.hash_map['property_select'] = selected_property_name
            self.hash_map['selected_property_name'] = selected_property_name
            self.hash_map.show_screen('Проверка цен')

        elif listener == "ON_BACK_PRESSED" or 'back_to_prices':
            self.hash_map['selected_property_id'] = ''
            self.hash_map['property_select'] = ''
            self.hash_map['selected_property_name'] = ''
            self.hash_map.show_screen('Проверка цен')

class DocGoodSelectProperties(SelectProperties):
    screen_name = 'Выбор характеристик'
    process_name = 'Документы'

    def _get_data(self):
        table_name = "RS_properties"
        raw_data = self.service.get_select_data(table_name)
        cards_data = []
        for element in raw_data:
            card_data = {
                'key': element['id'],
                'name': element['name']
            }
            cards_data.append(card_data)
        return cards_data

    def on_input(self):
        listener = self.listener

        if listener == "CardsClick":
            selected_property_id = self.hash_map.get("selected_card_key")
            selected_property_name = self.service.get_values_by_field(table_name='RS_properties', field='id',
                                                                      field_value=selected_property_id)[0]['name']
            self.hash_map.put('selected_property_id', selected_property_id)
            self.hash_map['property_select'] = selected_property_name
            self.hash_map['selected_property_name'] = selected_property_name
            self.hash_map.show_screen('ТоварШтрихкоды')

        elif listener == "ON_BACK_PRESSED" or 'back_to_prices':
            self.hash_map['selected_property_id'] = ''
            self.hash_map['property_select'] = ''
            self.hash_map['selected_property_name'] = ''
            self.hash_map.show_screen('ТоварШтрихкоды')

class ItemGoodSelectProperties(DocGoodSelectProperties):
    screen_name = 'Выбор характеристик'
    process_name = 'Товары'

class SelectUnit(GoodsPricesItemCard):
    screen_name = 'Выбор упаковки'
    process_name = 'Цены'

    def __init__(self, hash_map, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = GoodsService()

    def on_start(self):
        super().on_start()
        self._validate_input()
        cards_data = self._get_data()
        properties_cards = self._get_cards(cards_data)
        self.hash_map.put('unit_cards', properties_cards.to_json())

    def _get_data(self):
        table_name = "RS_units"
        raw_data = self.service.get_values_by_field(table_name, field='id_owner',
                                                    field_value=self.hash_map.get('input_good_id'))
        cards_data = []
        for element in raw_data:
            card_data = {
                'key': element['id'],
                'name': element['name']
            }
            cards_data.append(card_data)
        return cards_data

    def _get_cards(self, cards_data):
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')
        card_text_size = self.rs_settings.get('CardTextSize')

        cards = widgets.CustomCards(
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
                ))
            ,
            options=widgets.Options().options,
            cardsdata=cards_data
        )
        return cards

    def on_input(self):
        listener = self.listener

        if listener == "CardsClick":
            selected_unit_id = self.hash_map.get("selected_card_key")
            selected_unit_name = self.service.get_values_by_field(table_name='RS_units', field='id',
                                                                  field_value=selected_unit_id)[0]['name']
            self.hash_map.put('selected_unit_id', selected_unit_id)
            self.hash_map['unit_select'] = selected_unit_name
            self.hash_map.put('selected_unit_name', selected_unit_name)
            self.hash_map.show_screen('Проверка цен')

        elif listener == "ON_BACK_PRESSED" or 'back_to_prices':
            self.hash_map['selected_unit_id'] = ''
            self.hash_map['unit_select'] = ''
            self.hash_map.put('selected_unit_name', '')

            self.hash_map.show_screen('Проверка цен')

class DocGoodSelectUnit(SelectUnit):
    screen_name = 'Выбор упаковки'
    process_name = 'Документы'

    def _get_data(self):
            table_name = "RS_units"
            raw_data = self.service.get_select_data(table_name)
            cards_data = []
            for element in raw_data:
                card_data = {
                    'key': element['id'],
                    'name': element['name']
                }
                cards_data.append(card_data)
            return cards_data

    def on_start(self):
        cards_data = self._get_data()
        properties_cards = self._get_cards(cards_data)
        self.hash_map.put('unit_cards', properties_cards.to_json())

    def on_input(self):
        listener = self.listener

        if listener == "CardsClick":
            selected_unit_id = self.hash_map.get("selected_card_key")
            selected_unit_name = self.service.get_values_by_field(table_name='RS_units', field='id',
                                                                  field_value=selected_unit_id)[0]['name']
            self.hash_map.put('selected_unit_id', selected_unit_id)
            self.hash_map['unit_select'] = selected_unit_name
            self.hash_map.put('selected_unit_name', selected_unit_name)
            self.hash_map.show_screen('ТоварШтрихкоды')

        elif listener == "ON_BACK_PRESSED" or 'back_to_barcode_register':
            self.hash_map['selected_unit_id'] = ''
            self.hash_map['unit_select'] = ''
            self.hash_map.put('selected_unit_name', '')
            self.hash_map.show_screen('ТоварШтрихкоды')


class ItemGoodSelectUnit(DocGoodSelectUnit):
    screen_name = 'Выбор упаковки'
    process_name = 'Товары'

# ^^^^^^^^^^^^^^^^^^^^^ GoodsPrices ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== Series =============================
class SeriesList(Screen):
    process_name = 'Серии'
    screen_name = 'Выбор серии'
    doc_basic_table_name = 'RS_docs_table'
    doc_basic_handler_name = 'RS_docs'
    id: str = None

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)

        list_of_params = ['id_doc', 'Doc_data', 'code_art', 'properties_name',
                          'price', 'units_name', 'good_name', 'qtty_plan', 'qtty']
        str_params = self.hash_map.get('params_for_series_screen')
        if str_params:
            self.params = json.loads(str_params)
        else:
            self.params = {}

        self.service = db_services.SeriesService(self.params)
        self.popup_menu_data = 'Удалить;Изменить'
        res = self.service.get_series_prop_by_id(self.params['id'])
        self.params.update(res)

        res = self.service.get_doc_prop_by_id(self.params['id_doc'])
        self.params.update(res)

    def on_start(self):
        # Сохраним текущий hash_map чтобы вернуть его при выходе
        # self.rs_settings.put('_stored_hash_', json.dumps(self.hash_map.export()), True)

        for key in self.params.keys():
            self.hash_map[key] = self.params[key]

        query_data = self.service.get_series_by_doc_and_goods()
        list_data = query_data  # self._prepare_table_data(query_data)
        doc_cards = self._get_doc_cards_view(list_data)
        self.hash_map['series_cards'] = doc_cards.to_json()

        #Обновим количесмтво факт по сериям
        real_qtty = self.service.get_total_qtty()
        self.hash_map['qtty'] = str(real_qtty)
        self.service.set_total_qtty(real_qtty)


    def on_input(self):
        listener = self.listener
        if listener == "CardsClick":
            self.hash_map.put('current_series_id', self.hash_map.get("selected_card_key"))
            #self.update_hash_map_keys()
            self.hash_map.put('barcode', '')

            self.hash_map.show_screen("Заполнение серии", self.params)
        elif listener == "ON_BACK_PRESSED":
            real_qtty = self.service.get_total_qtty()
            self.service.set_total_qtty(real_qtty)
            # self.hash_map.importing(json.loads(self.rs_settings.get('_stored_hash')))
            # self.hash_map.put("FinishProcess", "")
            self.hash_map.show_screen(self.hash_map.get('back_screen'))
        elif listener == 'barcode':
            self._identify_add_barcode_series()
        elif self.listener == 'LayoutAction':
            self._layout_action()

    def update_hash_map_keys(self):
        params = self.params
        exclude_keys = ('hash_map', 'screen_values', 'rs_settings')
        for key in params.keys():
            if key in exclude_keys:
                continue
            self.hash_map[key] = self.params[key]

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _get_doc_cards_view(self, table_data):

        title_text_size = self.rs_settings.get("TitleTextSize")
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')
        card_date_text_size = self.rs_settings.get('CardDateTextSize')

        doc_cards = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@name',
                        width='match_parent',
                        gravity_horizontal='left',
                        weight=2
                    ),
                    widgets.TextView(
                        Value='@best_before',
                        TextSize=title_text_size,
                    ),
                    # widgets.PopupMenuButton(
                    #     Value=self.popup_menu_data,
                    #     Variable="menu_series",
                    # ),

                    orientation='horizontal',
                    width='match_parent',

                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@qtty',
                        TextBold=True,
                        TextSize=card_title_text_size
                    ),
                    widgets.TextView(
                        Value='@number',
                        TextBold=True,
                        TextSize=card_title_text_size
                    ),
                    widgets.TextView(
                        Value='@production_date',
                        TextBold=True,
                        TextSize=card_title_text_size
                    )

                ),

                width="match_parent"
            ),
            options=widgets.Options().options,
            cardsdata=table_data
        )

        return doc_cards

    def _prepare_table_data(self, doc_details):

        table_data = [{}]

        for record in doc_details:
            product_row = {}
            for el in record.keys():
                product_row[el] = record[el]

            # product_row = {'key': str(record['barcode']), 'barcode': str(record['barcode']),
            #                'name': record['name'] if record['name'] is not None else '-нет данных-', 'qtty': str(record['qtty'])}

            product_row['_layout'].BackgroundColor = '#FFFFFF' if record['name'] is not None else "#FBE9E7"

            if self._added_goods_has_key(product_row['key']):
                table_data.insert(1, product_row)
            else:
                table_data.append(product_row)

            # table_data.append(product_row)

        return table_data

    def _identify_add_barcode_series(self):
        barcode = self.hash_map.get('barcode')
        if barcode:

            values = self.service.get_series_by_barcode(barcode)
            if values:
                item_id = values[0]['id']
                self.service.add_qtty_to_table_str(item_id)
            else:
                self.service.add_new_series_in_doc_series_table(barcode)

    def _layout_action(self):
        layout_listener = self.hash_map.get('layout_listener')
        if layout_listener == 'Удалить':
            id = self.hash_map.get('selected_card_key')
            self.service.delete_current_st(id)
        elif layout_listener == 'Изменить':
            self.hash_map['current_series_id'] = self.hash_map.get('selected_card_key')
            self.hash_map.show_screen('Заполнение серии', self.params)


class SeriesItem(SeriesList):
    process_name = 'Серии'
    screen_name = 'Заполнение серии'


    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)


    def on_start(self):
        prop_list = self.service.get_series_table_str(self.hash_map.get('current_series_id'))
        for key, value in prop_list.items():
            if value:
                self.hash_map.put(key, value)
            else:
                self.hash_map.put(key, '_')

    def on_input(self):
        listener = self.listener
        if listener == "btn_save":

            self.save_data()
            self.hash_map.show_screen('Выбор серии')
        elif listener == "ON_BACK_PRESSED":
            self.hash_map.show_screen('Выбор серии')
        elif listener == "btn_cancel":
            self.hash_map.show_screen('Выбор серии')


    def save_data(self):
        params = {'id': int(self.hash_map.get('current_series_id')),
                  'id_doc': self.params['id_doc'],
                  'id_good':  self.params['id_good'],
                  'id_properties': self.params['id_properties'],
                  'id_series': self.params['id_series'],
                  'id_warehouse': self.params['id_warehouse'],
                  'qtty': self.hash_map['qtty'],
                  'name': self.hash_map['name'],
                  'best_before': self.hash_map['best_before'],
                  'number': self.hash_map['number'],
                  'production_date': self.hash_map['production_date'],
                  'cell': None
                  }
        self.service.save_table_str(params)


class SeriesAdrList(Screen):
    process_name = 'Адресное хранение'
    screen_name = 'Выбор серии'
    doc_basic_table_name = 'RS_docs_table'
    doc_basic_handler_name = 'RS_docs'
    id: str = None

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)

        list_of_params = ['id_doc', 'Doc_data', 'code_art', 'properties_name',
                          'price', 'units_name', 'good_name', 'qtty_plan', 'qtty']
        str_params = self.hash_map.get('params_for_series_screen')
        if str_params:
            self.params = json.loads(str_params)

        else:
            self.params = {}

        self.service = db_services.SeriesService(self.params)
        self.service.doc_basic_table_name = 'RS_adr_docs_table'
        self.service.doc_basic_handler_name = 'RS_adr_docs'
        self.popup_menu_data = 'Удалить;Изменить'
        res = self.service.get_series_prop_by_id(self.params['id'])
        self.params.update(res)

        res = self.service.get_doc_prop_by_id(self.params['id_doc'])
        self.params.update(res)

    def on_start(self):
        # Сохраним текущий hash_map чтобы вернуть его при выходе
        # self.rs_settings.put('_stored_hash_', json.dumps(self.hash_map.export()), True)

        for key in self.params.keys():
            self.hash_map[key] = self.params[key]

        query_data = self.service.get_series_by_adr_doc_and_goods()
        list_data = query_data  # self._prepare_table_data(query_data)
        doc_cards = self._get_doc_cards_view(list_data)
        self.hash_map['series_cards'] = doc_cards.to_json()

        #Обновим количесмтво факт по сериям
        real_qtty = self.service.get_adr_total_qtty()
        if real_qtty is None:
            real_qtty = 0
        self.hash_map['qtty'] = str(real_qtty)
        self.service.set_total_qtty(real_qtty)


    def on_input(self):
        listener = self.listener
        if listener == "CardsClick":
            self.hash_map.put('current_series_id', self.hash_map.get("selected_card_key"))
            #self.update_hash_map_keys()
            self.hash_map.put('barcode', '')

            self.hash_map.show_screen("Заполнение серии", self.params)
        elif listener == "ON_BACK_PRESSED":
            real_qtty = self.service.get_adr_total_qtty()
            self.service.set_adr_total_qtty(real_qtty)
            # self.hash_map.importing(json.loads(self.rs_settings.get('_stored_hash')))
            # self.hash_map.put("FinishProcess", "")
            self.hash_map.show_screen(self.hash_map.get('back_screen'))
        elif listener == 'barcode':
            self._identify_add_barcode_series()
        elif self.listener == 'LayoutAction':
            self._layout_action()

    def update_hash_map_keys(self):
        params = self.params
        exclude_keys = ('hash_map', 'screen_values', 'rs_settings')
        for key in params.keys():
            if key in exclude_keys:
                continue
            self.hash_map[key] = self.params[key]

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _get_doc_cards_view(self, table_data):

        title_text_size = self.rs_settings.get("TitleTextSize")
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')
        card_date_text_size = self.rs_settings.get('CardDateTextSize')

        doc_cards = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@name',
                        width='match_parent',
                        gravity_horizontal='left',
                        weight=2
                    ),
                    widgets.TextView(
                        Value='@best_before',
                        TextSize=title_text_size,
                    ),
                    # widgets.PopupMenuButton(
                    #     Value=self.popup_menu_data,
                    #     Variable="menu_series",
                    # ),

                    orientation='horizontal',
                    width='match_parent',

                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@qtty',
                        TextBold=True,
                        TextSize=card_title_text_size
                    ),
                    widgets.TextView(
                        Value='@number',
                        TextBold=True,
                        TextSize=card_title_text_size
                    ),
                    widgets.TextView(
                        Value='@production_date',
                        TextBold=True,
                        TextSize=card_title_text_size
                    )

                ),

                width="match_parent"
            ),
            options=widgets.Options().options,
            cardsdata=table_data
        )

        return doc_cards

    def _prepare_table_data(self, doc_details):

        table_data = [{}]

        for record in doc_details:
            product_row = {}
            for el in record.keys():
                product_row[el] = record[el]

            # product_row = {'key': str(record['barcode']), 'barcode': str(record['barcode']),
            #                'name': record['name'] if record['name'] is not None else '-нет данных-', 'qtty': str(record['qtty'])}

            product_row['_layout'].BackgroundColor = '#FFFFFF' if record['name'] is not None else "#FBE9E7"

            if self._added_goods_has_key(product_row['key']):
                table_data.insert(1, product_row)
            else:
                table_data.append(product_row)

            # table_data.append(product_row)

        return table_data

    def _identify_add_barcode_series(self):
        barcode = self.hash_map.get('barcode')
        if barcode:

            values = self.service.get_adr_series_by_barcode(barcode)
            if values:
                item_id = values[0]['id']
                self.service.add_qtty_to_table_str(item_id)
            else:
                self.service.add_new_series_in_doc_series_table(barcode)

    def _layout_action(self):
        layout_listener = self.hash_map.get('layout_listener')
        if layout_listener == 'Удалить':
            id = self.hash_map.get('selected_card_key')
            self.service.delete_current_st(id)
        elif layout_listener == 'Изменить':
            self.hash_map['current_series_id'] = self.hash_map.get('selected_card_key')
            self.hash_map.show_screen('Заполнение серии', self.params)


class SeriesAdrItem(SeriesAdrList):
    process_name = 'Адресное хранение'
    screen_name = 'Заполнение серии'


    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)


    def on_start(self):
        prop_list = self.service.get_series_table_str(self.hash_map.get('current_series_id'))
        for key, value in prop_list.items():
            if value:
                self.hash_map.put(key, value)
            else:
                self.hash_map.put(key, '_')

    def on_input(self):
        listener = self.listener
        if listener == "btn_save":
            self.save_data()
            self.hash_map.show_screen('Выбор серии')
        elif listener == "ON_BACK_PRESSED":
            self.hash_map.show_screen('Выбор серии')
        elif listener == "btn_cancel":
            self.hash_map.show_screen('Выбор серии')


    def save_data(self):
        params = {'id': int(self.hash_map.get('current_series_id')),
                  'id_doc': self.params['id_doc'],
                  'id_good':  self.params['id_good'],
                  'id_series': self.params['id_series'],
                  'id_warehouse': self.params['id_warehouse'],
                  'id_properties': self.params['id_properties'],
                  'qtty': self.hash_map['qtty'],
                  'name': self.hash_map['name'],
                  'best_before': self.hash_map['best_before'],
                  'number': self.hash_map['number'],
                  'production_date': self.hash_map['production_date'],
                  'cell': self.hash_map['cell']
                  }
        self.service.save_table_str(params)

# ^^^^^^^^^^^^^^^^^^^^^ Series ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== Settings =============================

class SettingsScreen(Screen):
    screen_name = 'Настройки и обмен'
    process_name = 'Параметры'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.db_service = db_services.DocService()

    def on_start(self):
        # self.hash_map.remove('toast')
        settings_keys = [
            'use_mark',
            'allow_fact_input',
            'add_if_not_in_plan',
            'path',
            'delete_files',
            'allow_overscan',
        ]

        put_data = {key: self.rs_settings.get(key) for key in settings_keys}
        put_data['ip_adr'] = self._get_ip_address()

        self.hash_map.put_data(put_data)

    def on_input(self):
        self._update_rs_settings()

        listeners = {
            'btn_http_settings': lambda: self._show_screen('Настройки http соединения'),
            'btn_size': lambda: self._show_screen('Настройки Шрифтов'),
            'btn_sound_settings': lambda: self._show_screen('Настройка звука'),
            'btn_documents_settings': lambda: self._show_screen('Настройки документов'),
            'btn_test_barcode': lambda: self._show_screen('Тест сканера'),
            'btn_err_log': lambda: self._show_screen('Ошибки'),
            'btn_upload_docs': self._upload_docs,
            'btn_timer': self._load_docs,
            'btn_delete_template_settings': self.delete_template_settings(self.rs_settings),
            'ON_BACK_PRESSED': lambda: self.hash_map.put('FinishProcess', ''),
        }
        if self.listener in listeners:
            listeners[self.listener]()

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _upload_docs(self):
        if self._check_http_settings():
            timer = Timer(self.hash_map, self.rs_settings)
            # timer.upload_all_docs()
            timer._upload_data()
        else:
            self.toast('Не заданы настройки соединения')

    def _load_docs(self):
        if self._check_http_settings():
            timer = Timer(self.hash_map, self.rs_settings)
            timer.timer_on_start()
        else:
            self.toast('Не заданы настройки соединения')

    def _update_rs_settings(self) -> None:
        use_mark = self.hash_map.get('use_mark') or 'false'
        path = self.hash_map.get('path') or '//storage/emulated/0/Android/data/ru.travelfood.simple_ui/'
        allow_fact_input = self.hash_map.get_bool('allow_fact_input') or False

        self.rs_settings.put('use_mark', use_mark, True)
        self.rs_settings.put('path', path, True)
        self.rs_settings.put('allow_fact_input', allow_fact_input, True)

    def _show_screen(self, screen_name) -> None:
        self.hash_map.show_screen(screen_name)

    def _get_http_settings(self) -> dict:
        http_settings = {
            'url': self.rs_settings.get("URL"),
            'user': self.rs_settings.get('USER'),
            'pass': self.rs_settings.get('PASS'),
            'device_model': self.hash_map['DEVICE_MODEL'],
            'android_id': self.hash_map['ANDROID_ID'],
            'user_name': self.rs_settings.get('user_name')}
        return http_settings

    @staticmethod
    def _get_ip_address() -> str:
        res = get_ip_address()
        if res:
            return res
        else:
            return 'нет сети'

    def _check_http_settings(self) -> bool:
        http = self._get_http_settings()
        return all([http.get('url'), http.get('user'), http.get('pass')])


class FontSizeSettingsScreen(Screen):
    screen_name = 'Настройки Шрифтов'
    process_name = 'Параметры'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)

    def on_start(self):
        put_data = {}
        fields_data = {
            'TitleTextSize': 'Размер заголовка',
            'CardTitleTextSize': 'Размер заголовка карточки',
            "CardDateTextSize": 'Данные карточки',
            'CardTextSize': 'Размер текста элементов',
            'GoodsCardTitleTextSize': 'Заголовок товара',
            'goodsTextSize': 'Товар',
            'SeriesPropertiesTextSize': 'Серии свойства',
            'DocTypeCardTextSize': 'Тип документа',
            'titleDocTypeCardTextSize': 'Название документа в карточке'
        }

        for field, hint in fields_data.items():
            put_data[field] = widgets.ModernField(
                hint=hint,
                default_text=self.rs_settings.get(field) or ''
            ).to_json()

        self.hash_map.put_data(put_data)

    def on_input(self):
        if self.listener == 'btn_on_save':
            save_data = {
                'TitleTextSize': self.hash_map['TitleTextSize'],
                'CardTitleTextSize': self.hash_map['CardTitleTextSize'],
                'CardTextSize': self.hash_map['CardTextSize'],
                'CardDateTextSize': self.hash_map['CardDateTextSize'],
                'GoodsCardTitleTextSize': self.hash_map['GoodsCardTitleTextSize'],
                'goodsTextSize': self.hash_map['goodsTextSize'],
                'SeriesPropertiesTextSize': self.hash_map['SeriesPropertiesTextSize'],
                'DocTypeCardTextSize': self.hash_map['DocTypeCardTextSize'],
                'titleDocTypeCardTextSize': self.hash_map['titleDocTypeCardTextSize'],
            }

            for k, v in save_data.items():
                self.rs_settings.put(k, v, True)

            self.hash_map.show_screen('Настройки и обмен')

        elif self.listener == 'btn_on_cancel' or self.listener == 'ON_BACK_PRESSED':
            self.hash_map.put('BackScreen', '')

        self.hash_map['noRefresh'] = ''

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass


class BarcodeTestScreen(Screen):
    screen_name = 'Тест сканера'
    process_name = 'Параметры'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)

    def on_start(self):
        pass

    def on_input(self):
        listeners = {
            'barcode': self._barcode_scanned,
            'ON_BACK_PRESSED': self._back_screen,
            'BACK_BUTTON': self._back_screen,
        }

        if self.listener in listeners:
            listeners[self.listener]()

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _back_screen(self):
        self.hash_map.put('BackScreen', '')

    def _barcode_scanned(self):
        barcode = self.hash_map.get('barcode_camera')
        if not barcode:
            return

        barcode_parser = BarcodeWorker(id_doc='')
        result = barcode_parser.parse(barcode)
        fields_count = 7

        keys_list = ['ERROR', 'GTIN', 'SERIAL', 'FullCode', 'BARCODE', 'SCHEME', 'EXPIRY', 'BATCH', 'NHRN', 'CHECK',
                     'WEIGHT', 'PPN']

        values = [f'{key}: {result[key]}' for key in keys_list if result.get(key) is not None]

        put_data = {
            f'fld_{i + 1}': values[i] if len(values) > i else ''
            for i in range(0, fields_count)
        }

        self.hash_map.put_data(put_data)


class HttpSettingsScreen(Screen):
    screen_name = 'Настройки http соединения'
    process_name = 'Параметры'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.hs_service = None

    def on_start(self) -> None:
        self.hash_map['btn_test_connection'] = 'Тест соединения'
        http_settings = self._get_http_settings()

        put_data = {
            'url': self._get_modern_field(hint='Адрес сервера', default_text=http_settings['url'] or ''),
            'user': self._get_modern_field(hint='Пользователь', default_text=http_settings['user'] or ''),
            'pass': self._get_modern_field(hint='Пароль', default_text=http_settings['pass'] or '', password=True),
            'user_name': self._get_modern_field(hint='Ваше имя для идентификации в 1С',
                                                default_text=http_settings['user_name'] or ''),
        }
        self.hash_map.put_data(put_data)

    def on_input(self) -> None:
        listeners = {
            'btn_test_connection': self._test_connection,
            'btn_save': self._save_settings,
            'barcode': self._barcode_scanned,
            'btn_cancel': self._back_screen,
            'ON_BACK_PRESSED': self._back_screen,
        }
        if self.listener in listeners:
            listeners[self.listener]()

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _test_connection(self):
        self.hs_service = hs_services.HsService(self._get_http_settings())

        if self._check_http_settings():
            self.hs_service.communication_test(timeout=3)
            result = self.hs_service.http_answer

            if result.unauthorized:
                self.hash_map.toast('Ошибка авторизации сервера 1С')
            elif result.forbidden:
                self.toast('Запрос на авторизацию принят')
            elif result.error:
                self.toast('Не удалось установить соединение')
                self.hash_map.playsound('error')
            else:
                self.toast('Соединение установлено')
                self.hash_map.playsound('success')

        else:
            self.toast("Не указаны настройки HTTP подключения к серверу")
            self.hash_map.playsound('error')

    def _save_settings(self):
        self.rs_settings.put('URL', self.hash_map['url'], True)
        self.rs_settings.put('USER', self.hash_map['user'], True)
        self.rs_settings.put('PASS', self.hash_map['pass'], True)
        self.rs_settings.put('user_name', self.hash_map['user_name'], True)

        self._back_screen()

    def _barcode_scanned(self):
        barcode = self.hash_map.get('barcode_camera2')
        try:
            barc_struct = json.loads(barcode)

            self.rs_settings.put('URL', barc_struct.get('url'), True)
            self.rs_settings.put('USER', barc_struct.get('user'), True)
            self.rs_settings.put('PASS', barc_struct.get('pass'), True)
            self.rs_settings.put('user_name', barc_struct.get('user_name'), True)

            self.hash_map.put('url', self._get_modern_field(hint='url', default_text=barc_struct.get('url')))
            self.hash_map.put('user', self._get_modern_field(hint='user', default_text=barc_struct.get('user')))
            self.hash_map.put('pass', self._get_modern_field(hint='pass', default_text=barc_struct.get('pass')))
            self.hash_map.put('user_name',
                              self._get_modern_field(hint='user_name', default_text=barc_struct.get('user_name')))
        except (JSONDecodeError, AttributeError) as e:
            self.toast('Неверный формат QR-кода')

    def _back_screen(self):
        self.hash_map.put('BackScreen', '')

    def _get_modern_field(self, **data):
        return widgets.ModernField(**data).to_json()

    def _check_http_settings(self) -> bool:
        http = self._get_http_settings()
        return all([http.get('url'), http.get('user'), http.get('pass')])

    def _get_http_settings(self):
        http_settings = {
            'url': self.rs_settings.get("URL"),
            'user': self.rs_settings.get('USER'),
            'pass': self.rs_settings.get('PASS'),
            'device_model': self.hash_map['DEVICE_MODEL'],
            'android_id': self.hash_map['ANDROID_ID'],
            'user_name': self.rs_settings.get('user_name')}
        return http_settings


class SoundSettings(Screen):
    screen_name = 'Настройка звука'
    process_name = 'Параметры'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.events = {'success': 'Сигнал удачного события', 'warning': 'Сигнал предупреждения',
                       'error': 'Сигнал ошибки'}

    def on_start(self):
        self._init_sounds()
        events_data = self._get_events_data()
        events_cards = self._get_event_cards_view(events_data, popup_menu_data='1;2;3;4;5;6;7;8;9;10;11;12;13;14;15')
        self.hash_map.put('event_cards', events_cards.to_json())

    def on_input(self):
        if self.listener == 'save_btn':
            self.rs_settings.put('success_signal', self.hash_map.get("current_success_signal"), True)
            self.rs_settings.put('warning_signal', self.hash_map.get("current_warning_signal"), True)
            self.rs_settings.put('error_signal', self.hash_map.get("current_error_signal"), True)
            self.hash_map.show_screen('Настройки и обмен')
            # self.hash_map.finish_process()

        elif self.listener == 'btn_on_cancel' or self.listener == 'ON_BACK_PRESSED':
            self.hash_map.put('current_success_signal', '')
            self.hash_map.put('current_warning_signal', '')
            self.hash_map.put('current_error_signal', '')
            self.hash_map.show_screen('Настройки и обмен')

        elif self.listener == 'CardsClick':
            selected_event = self.hash_map.get('selected_card_key')
            self.hash_map.playsound(event=selected_event,
                                    sound_val=self.hash_map.get(f'current_{selected_event}_signal'))

        elif self.listener == 'LayoutAction':
            self._layout_action()

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _init_sounds(self):
        # for key, val in self.events.items():
        #     if not self.hash_map.get(f'current_{key}_signal'):
        #         self.hash_map.put(f'current_{key}_signal', self.rs_settings.get(f'{event}_signal' or "6"))

        if not self.hash_map.get('current_success_signal'):
            self.hash_map.put('current_success_signal', self.rs_settings.get('success_signal'))
        if not self.hash_map.get('current_warning_signal'):
            self.hash_map.put('current_warning_signal', self.rs_settings.get('warning_signal'))
        if not self.hash_map.get('current_error_signal'):
            self.hash_map.put('current_error_signal', self.rs_settings.get('error_signal'))

    def _get_events_data(self):
        data = []
        for key, val in self.events.items():
            event = {
                'key': key,
                'event_name': val,
                'selected_value': self.hash_map.get(f'current_{key}_signal')
            }
            data.append(event)
        return data

    def _get_event_cards_view(self, events_data, popup_menu_data):
        title_text_size = self.rs_settings.get("TitleTextSize")
        card_title_text_size = self.rs_settings.get("CardTitleTextSize")
        doc_cards = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@event_name',
                        TextBold=True,
                        TextSize=title_text_size,
                        gravity_horizontal='center',
                        width='match_parent',
                    ),
                    orientation='horizontal',
                    width='match_parent',
                    gravity_horizontal='center',
                    weight=0
                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@selected_value',
                        TextSize=28,
                        gravity_horizontal='center',
                        weight=1,
                    ),
                    widgets.PopupMenuButton(
                        Value=popup_menu_data,
                        Variable="menu_select_sound",
                        gravity_horizontal='center',
                        weight=1
                    ),
                    widgets.TextView(
                        Value="Прослушать",
                        gravity_horizontal='center',
                        TextSize=card_title_text_size,
                        weight=1
                    ),

                    orientation='horizontal',
                    width='match_parent',

                ),

                width="match_parent",
                orientation='vertical',
                gravity_horizontal='center',
                gravity_vertical="center",
            ),
            options=widgets.Options().options,
            cardsdata=events_data
        )

        return doc_cards

    def _layout_action(self):
        layout_listener = self.hash_map.get('layout_listener')
        current_key = self.hash_map.get_json("card_data")['key']
        self.hash_map.put(f'current_{current_key}_signal', layout_listener)


class DocumentsSettings(Screen):
    screen_name = 'Настройки документов'
    process_name = 'Параметры'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)

    def on_start(self):
        if not self.hash_map.containsKey('doc_settings_on_start'):
            self.hash_map.put('doc_settings_on_start', 'true')
            self._init_old_doc_delete_settings()

    def on_input(self):
        if self.listener == 'save_btn':
            del_docs_flag = self.hash_map.get('doc_settings_confirm_delete_old_docs')
            del_docs_flag = True if del_docs_flag == 'true' else False
            if not del_docs_flag:
                self.rs_settings.put('delete_old_docs', False, True)
                self.rs_settings.delete('doc_delete_settings_days')
            else:
                days = self.hash_map.get('doc_delete_settings_days')
                if not days or days == '0' or not days.isdigit():
                    self.hash_map.playsound('error')
                    self.hash_map.toast('Укажите корректное количество дней'
                                        ' для настройки удаления старых документов')
                    return
                if days >= '9999':
                    self.hash_map.playsound('error')
                    self.hash_map.toast('Количество дней превышает 9999')
                    return
                self.rs_settings.put('delete_old_docs', True, True)
                self.rs_settings.put('doc_delete_settings_days', days, True)

            self.hash_map.toast('Настройки сохранены')
            self.hash_map.delete('doc_settings_on_start')
            self.hash_map.show_screen('Настройки и обмен')

        elif self.listener == 'ON_BACK_PRESSED':
            self.hash_map.delete('doc_settings_on_start')
            self.hash_map.show_screen('Настройки и обмен')

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _init_old_doc_delete_settings(self):
        current_days_value = self.rs_settings.get('doc_delete_settings_days')
        init_days = str(current_days_value) if current_days_value is not None else '1'
        self.hash_map.put('doc_delete_settings_days', init_days)

        flag = self.rs_settings.get('delete_old_docs')
        init_flag = str(flag).lower() if flag is not None else 'false'
        self.hash_map.put('doc_settings_confirm_delete_old_docs', init_flag)


class ErrorLogScreen(Screen):
    screen_name = 'Ошибки'
    process_name = 'Параметры'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.service = ErrorService()
        self.screen_values = {}

    def on_start(self) -> None:
        date_sort = self.hash_map['selected_date_sort']
        errors_table_data = self.service.get_all_errors(date_sort)
        table_raws = self._get_errors_table_rows(errors_table_data)
        table_view = self._get_errors_table_view(table_raws)
        self.hash_map.put("error_log_table", table_view.to_json())
        self.hash_map['date_sort_select'] = 'Новые;Cтарые'

    def on_input(self) -> None:
        super().on_input()

        if self.listener == "btn_clear_err":
            self.service.clear()
        if self.listener == 'ON_BACK_PRESSED':
            self.hash_map.put("ShowScreen", "Настройки и обмен")

        elif self.listener == "date_sort_click":
            self.hash_map['selected_date_sort'] = self.hash_map["date_sort_click"]

    def on_post_start(self):
        pass

    def show(self, args=None):
        self._validate_screen_values()
        self.hash_map.show_screen(self.screen_name, args)

    def _get_errors_table_rows(self, errors_table_data):
        table_data = [{}]
        i = 1
        for record in errors_table_data:
            error_row = {"key": i, "message": record[0], "time": record[1],
                         '_layout': self._get_errors_table_row_layout()}
            table_data.append(error_row)
            i += 1

        return table_data

    def _get_errors_table_view(self, table_rows):
        table_view = widgets.CustomTable(
            widgets.LinearLayout(
                self.LinearLayout(
                    self.TextView('Время'),
                    weight=1
                ),
                self.LinearLayout(
                    self.TextView('Сообщение'),
                    weight=3
                ),
                orientation='horizontal',
                height="match_parent",
                width="match_parent",
                BackgroundColor='#FFFFFF'
            ),
            options=widgets.Options().options,
            tabledata=table_rows
        )
        return table_view

    def _get_errors_table_row_layout(self):
        row_view = widgets.LinearLayout(
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@time',
                    TextSize=15,
                    width='match_parent'
                ),
                width='match_parent',
                height='wrap_content',
                weight=1,
                StrokeWidth=0
            ),
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@message',
                    TextSize=15,
                    width='match_parent',
                ),
                width='match_parent',
                height='wrap_content',
                weight=3,
            ),
            orientation='horizontal',
            width='match_parent',
            BackgroundColor='#FFFFFF',
            height='wrap_content',
            StrokeWidth=1
        )

        return row_view

    class LinearLayout(widgets.LinearLayout):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.orientation = 'vertical'
            self.height = "match_parent"
            self.width = "match_parent"
            self.StrokeWidth = 1

    class TextView(widgets.TextView):
        def __init__(self, value):
            super().__init__()
            self.TextSize = '15'
            self.TextBold = True
            self.width = 'match_parent'
            self.Value = value


# ^^^^^^^^^^^^^^^^^^^^^ Settings ^^^^^^^^^^^^^^^^^^^^^^^^^^^^


# ==================== Debug settings =============================


class DebugSettingsScreen(Screen):
    process_name = 'Отладка'
    screen_name = 'Отладочный экран'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.hs_service = hs_services.DebugService

    def on_start(self):
        debug_host_ip = self.rs_settings.get('debug_host_ip') or self.hash_map['ip_host']
        self.hash_map.put(
            'ip_host',
            {'hint': 'IP-адрес для выгрузки базы/лога', 'default_text': debug_host_ip or ''},
            to_json=True)

    def on_input(self):
        listeners = {
            'btn_fill_ratio': self._fill_ratio,
            'btn_copy_base': self._copy_base,
            'btn_unload_log': self._unload_log,
            'btn_local_files': self._local_files,
            'btn_templates': self.open_templates_screen,
            'ON_BACK_PRESSED': self._on_back_pressed
        }
        if self.listener in listeners:
            listeners[self.listener]()

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def _fill_ratio(self):
        qtext = '''
        UPDATE RS_barcodes
        SET ratio = COALESCE((
            SELECT RS_units.nominator / RS_units.denominator
            FROM RS_units
            WHERE RS_units.id = RS_barcodes.id_unit
        ), 1)'''

        res = ui_global.get_query_result(qtext)
        self.hash_map.toast('Таблица баркодов заполнена значениями из единиц измерения')

    def _copy_base(self):
        ip_host = self.hash_map['ip_host']
        path_to_databases = self.rs_settings.get('path_to_databases')
        base_name = self.rs_settings.get('sqlite_name')
        file_path = os.path.join(path_to_databases, base_name)

        if os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                res = self.hs_service(ip_host).export_database(f)

                if res['status_code'] == 200:
                    self.hash_map.toast('База SQLite успешно выгружена')
                else:
                    self.hash_map.toast('Ошибка соединения')
        else:
            self.hash_map.toast('Файл не найден')

    def _unload_log(self):
        ip_host = self.hash_map['ip_host']

        path_to_databases = self.rs_settings.get('path_to_databases')
        base_name = self.rs_settings.get('log_name')
        file_path = os.path.join(path_to_databases, base_name)

        # TODO Здесь нужно будет вызывать класс-сервис для взаимодействия с TinyDB
        from tinydb import TinyDB

        db = TinyDB(file_path)
        data = db.all()

        res = self.hs_service(ip_host).export_log(data)
        if res['status_code'] == 200:
            self.hash_map.toast('Лог успешно выгружен')
        else:
            self.hash_map.toast('Ошибка соединения')

    def _local_files(self):
        import ui_csv

        path = self.hash_map['path']
        delete_files = self.hash_map['delete_files']

        if not delete_files:
            delete_files = '0'
        if not path:
            path = '//storage/emulated/0/download/'

        ret_text = ui_csv.list_folder(path, delete_files)

        self.hash_map.toast(ret_text)

    def _on_back_pressed(self):
        ip_host = self.hash_map['ip_host']
        self.rs_settings.put('debug_host_ip', ip_host, True)
        self.hash_map.put('FinishProcess', '')

    def open_templates_screen(self):
        self.hash_map.show_process_result('Печать', 'Список шаблонов')


# ^^^^^^^^^^^^^^^^^^^^^ Debug settings ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== ActiveCV =============================

class ActiveCVArticleRecognition(Screen):
    screen_name = 'Новый шаг ActiveCV'
    process_name = 'Распознавание артикулов'

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)
        self.id_doc = self.hash_map['id_doc']
        self.service = DocService(self.id_doc)

    def on_start(self):
        pass

    def on_input(self):
        pass

    def on_object_detected(self):
        self.hash_map.beep()
        current_object = self.hash_map.get('current_object')
        self.hash_map.add_to_cv_list(current_object, 'finded_articles')
        good_name = self.get_good_info(current_object)
        self.hash_map.add_to_cv_list(
            {'object': str(current_object),
             'info': f'Товар: <big>{good_name}</big>'},
            'object_info_list', _dict=True)
        self.hash_map.add_to_cv_list(current_object, 'yellow_list')

        self.hash_map.put(
            'art_info','Найденные артикулы: ' + self.hash_map.get('finded_articles'))

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass

    def get_good_info(self, article: str) -> str:
        query = ('SELECT RS_goods.name as name'
                 ' FROM RS_docs_table'
                 ' LEFT JOIN RS_goods ON RS_docs_table.id_good = RS_goods.id'
                 ' WHERE RS_docs_table.id_doc = ? AND RS_goods.art = ?')
        goods = self.service.provider.sql_query(query, f'{self.id_doc},{article}')
        return goods[0]['name'] if goods else 'Не найдено'

# ^^^^^^^^^^^^^^^^^^^^^ ActiveCV ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==================== Timer =============================


class Timer:
    def __init__(self, hash_map: HashMap, rs_settings):
        self.hash_map = hash_map
        self.rs_settings = rs_settings
        self.http_settings = self._get_http_settings()
        self.db_service = DocService()
        self.http_service = HsService(self.http_settings)

    def timer_on_start(self):
        if self.hash_map.get_bool('stop_timer_update'):
            return

        self.load_docs()
        self._upload_data()
        # self.upload_all_docs()

    def put_notification(self, text, title=None):
        self.hash_map.notification(text, title)

    def _get_http_settings(self):
        http_settings = {
            'url': self.rs_settings.get("URL"),
            'user': self.rs_settings.get('USER'),
            'pass': self.rs_settings.get('PASS'),
            'device_model': self.hash_map['DEVICE_MODEL'],
            'android_id': self.hash_map['ANDROID_ID'],
            'user_name': self.rs_settings.get('user_name')}
        return http_settings

    def load_docs(self):
        if not self._check_http_settings():
            return

        try:
            docs_data = self.http_service.get_data()
            data = docs_data.get('data')
            if not data:
                return

            service = db_services.TimerService()
            new_documents = service.get_new_load_docs(data)
            service.save_load_data(data)
            self.db_service.update_data_from_json(docs_data['data'])

            if new_documents:
                notify_text = self._get_notify_text(new_documents)
                self.put_notification(text=notify_text, title="Загружены документы:")

        except Exception as e:
            self.db_service.write_error_on_log(f'Ошибка загрузки документов: {e}')

    def _upload_data(self):
        if not self._check_http_settings():
            return

        service = TimerService()
        data = service.get_data_to_send()

        if not data:
            return

        try:
            answer = self.http_service.send_data(data)
        except Exception as e:
            self.db_service.write_error_on_log(f'Ошибка выгрузки документов: {e}')
            return

        if answer.error:
            # self.put_notification(title='Ошибка при отправке документов', text=answer.error_text)
            self.db_service.write_error_on_log(f'Ошибка выгрузки документов: {answer.error_text}')
        else:
            docs_list_string = ', '.join([f"'{d['id_doc']}'" for d in data])
            self.db_service.update_uploaded_docs_status(docs_list_string)

    def upload_all_docs(self):
        self.db_service = DocService()
        self.upload_docs()
        self.db_service = AdrDocService()
        self.upload_docs()

    def load_all_docs(self):
        self.db_service = DocService()
        self.load_docs()
        self.db_service = AdrDocService()
        self.load_docs()

    def upload_docs(self):

        if self._check_http_settings():
            try:

                docs_goods_formatted_list = self.db_service.get_docs_and_goods_for_upload()
                if docs_goods_formatted_list:
                    answer = self.http_service.send_documents(docs_goods_formatted_list)
                    if answer:
                        if answer.get('Error') is not None:
                            self.put_notification(text='Ошибка при отправке документов')
                            err_text = answer.get('text').decode('utf-8')
                            error = answer.get("Error") or ''
                            self.db_service.write_error_on_log(f'Ошибка выгрузки документов: {err_text}\n{error}')
                        else:
                            docs_list_string = ', '.join([f"'{d['id_doc']}'" for d in docs_goods_formatted_list])
                            self.db_service.update_uploaded_docs_status(docs_list_string)
            except Exception as e:
                self.db_service.write_error_on_log(f'Ошибка выгрузки документов: {e}')

    def _check_http_settings(self) -> bool:
        http = self._get_http_settings()
        return all([http.get('url'), http.get('user'), http.get('pass')])

    @staticmethod
    def _get_notify_text(new_documents):
        doc_titles = [
            '{} № {} от {}'.format(item['doc_type'], item['doc_n'], item['doc_date'])
            for item in new_documents.values()]
        return ", ".join(doc_titles)


# ^^^^^^^^^^^^^^^^^^^^^ Timer ^^^^^^^^^^^^^^^^^^^^^^^^^^^^


# ==================== Main events =============================


class MainEvents:
    def __init__(self, hash_map: HashMap, rs_settings):
        self.hash_map = hash_map
        self.rs_settings = rs_settings

    def app_on_start(self):

        self.hash_map.put('StackAddMode', '')  # Включает режим объединения переменных hash_map в таймерах

        # TODO Обработчики обновления!
        release = self.rs_settings.get('Release') or ''
        toast = 'Готов к работе'

        current_release = self.hash_map['_configurationVersion']
        # toast = (f'Обновляемся с {release} на {current_release}')

        self._create_tables()

        if current_release is None:
            toast = 'Не удалось определить версию конфигурации'

        # self.hash_map.toast(f'Обновляемся с {release} на {current_release}')
        if current_release and release != current_release:
            # toast = (f'Обновляемся с {release} на {current_release}')
            # pass
            # import version_control
            # result_list = version_control.run_releases(release, current_release)
            # for elem in result_list:
            #     if not elem['result']:
            #         pass
            self.hash_map.put('InstallConfiguration', '')
            self.rs_settings.put('Release', current_release, True)
            toast = f'Выполнено обновление на версию {current_release}'

        if self.rs_settings.get('delete_old_docs') is True:
            deleted_docs = self._delete_old_docs()
            if deleted_docs:
                self.hash_map.notification(
                    text=f'Удалены документы: ({len(deleted_docs)})',
                    title='Очистка неактуальных данных')

        rs_default_settings = {
            'TitleTextSize': 18,
            'titleDocTypeCardTextSize': 18,
            'CardTitleTextSize': 20,
            'CardDateTextSize': 10,
            'CardTextSize': 15,
            'GoodsCardTitleTextSize': 18,
            'goodsTextSize': 18,
            'SeriesPropertiesTextSize': 16,
            'DocTypeCardTextSize': 15,
            'signal_num': 5,
            'use_mark': 'false',
            'add_if_not_in_plan': 'false',
            'path': '',
            'delete_files': 'false',
            'success_signal': 7,
            'warning_signal': 8,
            'error_signal': 5,
            'allow_overscan': 'false',
            "path_to_databases": "./",
            'sqlite_name': 'SimpleKeep',
            'log_name': 'log.json',
            'timer_is_disabled': False,
            'allow_fact_input': False,
            'delete_old_docs': False
        }

        if os.path.exists('//data/data/ru.travelfood.simple_ui/databases/'):  # локально
            rs_default_settings['path_to_databases'] = '//data/data/ru.travelfood.simple_ui/databases'
        else:
            rs_default_settings['path_to_databases'] = "./"  # D:\PythonProjects\RightScan\SUI_noPony\

        for k, v in rs_default_settings.items():
            if self.rs_settings.get(k) is None:
                self.rs_settings.put(k, v, True)

        self.hash_map["SQLConnectDatabase"] = "SimpleKeep"
        self.hash_map.toast(toast)

    def on_sql_error(self):
        sql_error = self.hash_map['SQLError']
        if sql_error:
            service = db_services.DocService()
            service.write_error_on_log(f'SQL_Error: {sql_error}')

    def _create_tables(self):
        service = db_services.DbCreator()
        service.create_tables()

    def _delete_old_docs(self) -> list:
        days = int(self.rs_settings.get('doc_delete_settings_days'))
        service = db_services.DocService()
        return service.delete_old_docs(days)


# ^^^^^^^^^^^^^^^^^^^^^ Main events ^^^^^^^^^^^^^^^^^^^^^^^^^^^^


class ScreensFactory:
    screens = [GoodsSelectScreen,
        HtmlView,
        TemplatesList,
        AdrDocsListScreen,
        AdrDocDetailsScreen,
        FlowTilesScreen,
        FlowDocScreen,
        FlowDocDetailsScreen,
        GroupScanTiles,
        DocumentsTiles,
        GroupScanDocsListScreen,
        DocumentsDocsListScreen,
        GroupScanDocDetailsScreenNew,
        DocumentsDocDetailScreen,
        ErrorLogScreen,
        DebugSettingsScreen,
        HttpSettingsScreen,
        SettingsScreen,
        GoodsListScreen,
        SelectGoodsType,
        ItemCard,
        FontSizeSettingsScreen,
        BarcodeTestScreen,
        SoundSettings,
        GoodsBalancesItemCard,
        SelectWH,
        GoodsPricesItemCard,
        SelectPriceType,
        SelectProperties,
        SelectUnit,
        GoodBarcodeRegister,
        GoodItemBarcodeRegister,
        DocGoodSelectProperties,
        ItemGoodSelectProperties,
        DocGoodSelectUnit,
        ItemGoodSelectUnit,
    ]

    @staticmethod
    def get_screen_class(screen_name=None, process=None, **kwargs):
        if not screen_name:
            screen_name = kwargs['hash_map'].get_current_screen()
        if not process:
            process = kwargs['hash_map'].get_current_process()

        for item in ScreensFactory.screens:
            if getattr(item, 'screen_name') == screen_name and getattr(item, 'process_name') == process:
                return item

    @staticmethod
    def create_screen(screen_name=None, process=None, **kwargs):
        if not screen_name:
            screen_name = kwargs['hash_map'].get_current_screen()
        if not process:
            process = kwargs['hash_map'].get_current_process()

        screen_class = ScreensFactory.get_screen_class(screen_name, process)
        return screen_class(**kwargs)


class MockScreen(Screen):
    screen_name = 'Mock'
    process_name = 'Mock'

    def on_start(self):
        pass

    def on_input(self):
        pass

    def on_post_start(self):
        pass

    def show(self, args=None):
        pass
