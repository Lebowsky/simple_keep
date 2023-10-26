from barcode.errors import NumberOfDigitsError

from ru.travelfood.simple_ui import SimpleUtilites as suClass
from tiny_db_services import NoSQLProvider
from java import jclass
from bs4 import BeautifulSoup
from ui_utils import HashMap, create_file
from io import BytesIO
from jinja2 import Environment, FileSystemLoader, select_autoescape, meta, Undefined

import qrcode
import barcode
from barcode.writer import ImageWriter

import base64
import uuid
import json
import os
from typing import Dict, Tuple, Any, Union, Literal, Optional
import re
import requests
import zpl
from PIL import Image
from ru.travelfood.simple_ui import SimpleBluetooth

bt = SimpleBluetooth()
noClass = jclass("ru.travelfood.simple_ui.NoSQL")
print_nosql = NoSQLProvider('print_nosql')


class HTMLDocument:
    @staticmethod
    def generate_barcode(data, type='ean13'):
        EAN = barcode.get_barcode_class(type)
        writer = ImageWriter()
        ean = EAN(data, writer=writer)

        barcode_image = BytesIO()
        ean.write(barcode_image)
        return base64.b64encode(barcode_image.getvalue()).decode()

    @staticmethod
    def generate_qr_code(barcode):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(barcode)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffered = BytesIO()
        img.save(buffered, format="PNG")

        return base64.b64encode(buffered.getvalue()).decode()

    @staticmethod
    def generate_datamatrix(barcode_data, width: int = 500, height: int = 500):
        path_to_file = suClass.generateDataMatrix(barcode_data, width, height)
        with open(path_to_file, "rb") as image_file:
            data = base64.b64encode(image_file.read()).decode()
        return data

    @staticmethod
    def create_html(
            data: Dict,
            barcode_parameters: Dict,
            current_1c_template_path: str
    ):
        class SilentUndefined(Undefined):
            def _fail_with_undefined_error(self, *args, **kwargs):
                return ''

        template_dir, template_name = os.path.split(current_1c_template_path)
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            variable_start_string='[',
            variable_end_string=']',
            undefined=SilentUndefined
        )
        barcode_type = barcode_parameters['barcode_type']
        try:
            if barcode_type == 'qr-code':
                barcode_image_base64 = HTMLDocument.generate_qr_code(data['barcode'])
            elif barcode_type == 'datamatrix':
                barcode_image_base64 = HTMLDocument.generate_datamatrix(data['barcode'])
            else:
                barcode_image_base64 = HTMLDocument.generate_barcode(data['barcode'],
                                                                     barcode_type)
        except NumberOfDigitsError:
            barcode_image_base64 = None
        template = env.get_template(template_name)
        data.update(
            Штрихкод=(f'<img id=barcode src="data:image/png; width:auto; height:auto;'
                      f' base64,{barcode_image_base64}" alt="{data["barcode"]}" />'))
        aa = template.render(data)
        soup = BeautifulSoup(aa, 'html.parser')
        html_with_css = HTMLDocument.inject_css_style(str(soup), barcode_parameters)
        return html_with_css

    @staticmethod
    def inject_css_style(html: str, barcode_parameters: Dict):
        width = barcode_parameters['barcode_width']
        height = barcode_parameters['barcode_height']
        x = str(int(barcode_parameters['barcode_right']) - int(
            barcode_parameters['barcode_left']))
        y = str(int(barcode_parameters['barcode_down']) - int(
            barcode_parameters['barcode_up']))
        css_template2 = '''
          @page {
            margin: 1mm; /* Adjust if necessary */
        }

        body {
            margin: 0;
            padding: 0;
            background: #ffffff;
            font-family: Arial;
            font-size: 8pt;
            font-style: normal;
        }

        .full-template {
            width: calc(100vw - 2mm);
            height: calc(100vh - 2mm);
            min-width: 40mm;    /* Minimum width */
            min-height: 40mm;   /* Minimum height */
            border: 1pt solid black;
            box-sizing: border-box; /* ensures padding and border are included in the total width and height */
            page-break-inside: avoid; /* Avoid breaking inside the template */
        }

        img {
            transform: translate(''' + x + '''px, ''' + y + '''px);
            width: ''' + width + '''mm;
            height: ''' + height + '''mm;
        }

        table {
            width: 100%;
            height: 100%;
            table-layout: fixed;
            border-collapse: collapse;
            page-break-inside: avoid; /* Avoid breaking inside the table */
        }

        td {
            text-align: center;
            vertical-align: middle;
            overflow: hidden;
        }
        '''

        soup = BeautifulSoup(html, "html.parser")
        # Добавляем свои стили в документ
        head_tag = soup.head
        style_tag = soup.new_tag("style")
        style_tag.string = css_template2
        head_tag.append(style_tag)
        # Запихуем весь документ в контейнер
        wrapper = soup.new_tag("div")
        wrapper['class'] = 'full-template'
        body_children = list(soup.body.children)
        soup.body.clear()
        soup.body.append(wrapper)
        for child in body_children:
            wrapper.append(child)

        # Удаляем пустые ячейки из таблицы, которые так любит 1с
        for tr in soup.find_all('tr'):

            for td in tr.find_all('td'):
                if not td.attrs.get('class'):
                    td.decompose()
        # Лишние колонки справа удаляем тоже
        for col in soup.find_all('col'):
            if not col.attrs:
                col.decompose()

        return str(soup)

    @staticmethod
    def find_template_variables(path_to_template: str):
        template_dir, template_name = os.path.split(path_to_template)
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            variable_start_string='[',
            variable_end_string=']',
        )
        template_source = env.loader.get_source(env, template_name)[0]
        parsed_content = env.parse(template_source)
        params = meta.find_undeclared_variables(parsed_content)
        if 'barcode' not in params:
            params.add('barcode')
        return params

    @staticmethod
    def replase_params_names(print_data: Dict, matching_table: Dict):
        new_data = {}
        for match in matching_table:
            if match['value'] in print_data:
                new_data[match['key']] = print_data[match['value']]
        return new_data


class PrintService:
    def __init__(self, hash_map: HashMap):
        self.hash_map = hash_map

    def print(self, data: Dict, many: bool = False):
        print_template_type = print_nosql.get('print_template_type')
        if print_template_type == '1C':
            self.print_1c_template(data)
        elif print_template_type == 'ZPL':
            self.print_zpl_template(data, many)

    def print_1c_template(self, data: Dict):
        label_path = print_nosql.get('current_1c_template_path')
        if not label_path or not os.path.isfile(label_path):
            self.hash_map.toast('Не выбран шаблон печати 1C')
            return
        template_sizes = print_nosql.get('saved_print_template_sizes')
        if not template_sizes:
            self.hash_map.toast('Не указаны размеры шаблона печати 1C')
            return
        matching_table = json.loads(print_nosql.get('matching_table'))
        data_for_printing = HTMLDocument.replase_params_names(data, matching_table)
        self.hash_map.toast(data_for_printing)
        barcode_parameters = print_nosql.get('barcode_parameters', from_json=True)
        html = HTMLDocument.create_html(
            data_for_printing, barcode_parameters, label_path)
        post_handler = {'action': 'run', 'type': 'python',
                        'method': 'print_post_execute'}
        self.hash_map.html2png(html, 'runasync', [post_handler])
        self.hash_map.toast('Отправлено на печать')

        img_path = create_file(
            ext='png', file_name=str(uuid.uuid4()), folder='temp')
        print_nosql.put('path_to_html2image_file', img_path)
        self.hash_map.put("html2image_ToFile", img_path)

    def print_zpl_template(self, data: Dict, many: bool = False):
        zpl_template_path = print_nosql.get('default_zpl_template_path')
        template_from_string = print_nosql.get('default_zpl_template_from_string')
        if zpl_template_path:
            self.print_zpl_template_from_file(data, many)
        elif template_from_string:
            self.print_zpl_template_from_string(data, many)
        else:
            self.hash_map.toast('Не выбран ZPL шаблон')

    def make_zpl_from_label(
            self,
            print_image_width: int,
            print_image_height: int,
            print_template_dpmm: int,
            print_template_x_origin: int,
            print_template_y_origin: int,
            print_template_ll: int,
            print_template_pw: int,
            path_to_img: str,
            **kwargs
    ) -> str:
        """Возвращает строку zpl с картинкой внутри"""
        label = zpl.Label(
            width=print_image_width,
            height=print_image_height,
            dpmm=print_template_dpmm
        )
        label.origin(print_template_x_origin, print_template_y_origin)
        label.write_graphic(
            image=Image.open(path_to_img),
            width=print_image_width,
            height=print_image_height
        )
        label.endorigin()
        zpl_data = label.dumpZPL()
        ll = print_template_ll
        pw = print_template_pw
        if ll and pw:
            zpl_data = zpl_data.replace('^XA', '^XA' + f'^LL{ll}' + f'^PW{pw}', 1)
        return zpl_data

    def zpl_to_png_from_api(
            self,
            zpl_data: str,
            print_template_dpmm: int,
            print_template_width: int,
            print_template_height: int,
            **kwargs
    ) -> Tuple[bool, Any]:
        """
        Делает запрос к API. Отправляются zpl код и размеры этикетки.
        """
        files = {'file': zpl_data}

        url = (f'http://api.labelary.com/v1/printers/{print_template_dpmm}dpmm/'
               f'labels/{self.mm_to_inch(print_template_width)}x{self.mm_to_inch(print_template_height)}/0/')
        try:
            response = requests.post(url, files=files, stream=True)
        except Exception as e:
            return False, str(e)
        if response.status_code != 200:
            return False, response.text

        response.raw.decode_content = True
        return True, response.raw

    def print_zpl_template_from_file(self, data, many: bool = False):
        zpl_template_path = print_nosql.get('default_zpl_template_path')
        if not os.path.isfile(zpl_template_path):
            self.hash_map.toast('ZPL шаблон недоступен, укажите другой')
            return
        with open(zpl_template_path, 'r') as f:
            zpl_template = json.loads(f.read())
        if many:
            data_to_print = []
            for item in data:
                new_zpl = self.get_zpl_for_print_file(item, zpl_template)
                data_to_print.append(new_zpl)
            data_to_print = ''.join(data_to_print)
        else:
            data_to_print = self.get_zpl_for_print_file(data, zpl_template)
        self.print_zpl(data_to_print)

    def print_zpl_template_from_string(self, data, many: bool = False):
        template_from_string = print_nosql.get('default_zpl_template_from_string')
        if many:
            data_to_print = []
            for item in data:
                new_zpl = self.get_zpl_for_print_str(item, template_from_string)
                data_to_print.append(new_zpl)
            data_to_print = ''.join(data_to_print)
        else:
            data_to_print = self.get_zpl_for_print_str(data, template_from_string)
        self.print_zpl(data_to_print)

    def get_zpl_for_print_str(self, data, template_from_string):
        zpl = self.zpl_from_string_replace_values(template_from_string, data)
        zpl = self.add_ascii_zpl(zpl)
        return zpl

    def get_zpl_for_print_file(self, data, zpl_template):
        for element in zpl_template['elements']:
            if element['type'] == 'variable':
                default_value = element['params']['text']
                for key in data:
                    if element['params']['text'] == key:
                        element['params']['text'] = data[key]
                if element['params']['text'] == default_value:
                    element['params']['text'] = ''
            elif element['type'] in ['qrcode', 'datamatrix']:
                default_value = element['params']['code']
                for key in data:
                    if key == 'barcode':
                        element['params']['code'] = data[key]
                if element['params']['code'] == default_value:
                    element['params']['code'] = 'No value :('
        zpl_data = ZPLConstructor(
            width=zpl_template['label_width'],
            height=zpl_template['label_height'],
            dpmm=zpl_template['dpmm'],
            hash_map=self.hash_map
        ).get_zpl(zpl_template, to_print=True)
        return zpl_data

    def zpl_from_string_replace_values(self, text, dictionary):
        pattern = r'\[(.*?)\]'
        replaced_text = re.sub(pattern,
                               lambda match: dictionary.get(match.group(1), ''),
                               text)
        return replaced_text

    def print_post_execute(self):
        path_to_img = print_nosql.get('path_to_html2image_file')
        template_sizes = print_nosql.get('saved_print_template_sizes', from_json=True)
        zpldata = self.make_zpl_from_label(path_to_img=path_to_img,
                                                   **template_sizes)
        self.print_zpl(zpldata)

    def print_zpl(self, zpl_data: str):
        print_through = print_nosql.get('print_through')
        if not print_through:
            self.hash_map.toast('Не выбрано устройство для печати')
        elif print_through == 'BT':
            sent, result = self.print_bt(zpl_data)
            self.hash_map.toast(result)
        elif print_through == 'WiFi':
            print_nosql.put('wifi_data_to_print', zpl_data, True)
            self.hash_map.run_event_async('print_wifi')

    def print_wifi(self):
        ip = print_nosql.get('current_wi_fi_printer_ip')
        if not ip:
            self.hash_map.toast('Не указан ip')
            return
        data = print_nosql.get('wifi_data_to_print')
        if not data:
            self.hash_map.toast('Нет данных для печати wifi')
            return
        print_nosql.delete('wifi_data_to_print')
        fail_handlers = [{"action": "run", "type": "python", "method": "wifi_error"}]
        sended = suClass.write_socket(ip, 9100, data, json.dumps(fail_handlers))
        self.hash_map.toast('Успешно' if sended else 'Не отправлено')

    def print_bt(self, data: Union[str, int, bytes]):
        bt_handlers = [{"action": "run", "type": "python", "method": "bluetooth_error"}]
        printer = print_nosql.get("default_printer")
        if printer is None:
            return False, "Не отправлено.Не выбран BT-принтер"
        device = bt.get_device(printer)
        if device is None:
            return False, "Не отправлено.Не получилось подключиться к устройству"
        try:
            bt.write_data(data, json.dumps(bt_handlers))
            return True, ("Отправлено на печать."
                          " Переподключите принтер, если печать не началась")
        except Exception as e:
            try:
                bt.connect_to_client(device, json.dumps(bt_handlers))
                bt.write_data(data, json.dumps(bt_handlers))
                return True, "Успешно отправлено на печать"
            except Exception as e:
                return False, str(e)

    def bluetooth_error(self):
        self.hash_map.playsound('error')

    def wifi_error(self):
        self.hash_map.playsound('error')

    def add_ascii_zpl(self, zpl_data) -> str:
        if '^CI28' not in zpl_data:
            zpl_data = zpl_data.replace('^XA', '^XA^CI28')
        if '^CF0,' not in zpl_data:
            zpl_data = zpl_data.replace('^CI28', '^CI28^CF0,50')
        return zpl_data

    @staticmethod
    def mm_to_inch(size_mm: int) -> float:
        return size_mm / 25.4

    @staticmethod
    def inch_to_mm(size_inch: int) -> float:
        return size_inch * 25.4

    @staticmethod
    def valide_ip(ip: str):
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        return True if re.match(pattern, ip) else False


class ZPLConstructor:
    allowed_elements = {
        'string': {'text': 'text'},
        'variable': {'text': 'text'},
        'qrcode': {'code': 'text', 'magnification': 10},
        'datamatrix': {'code': 'text', 'height': 10}}

    def __init__(self, width: int, height: int, dpmm: int, hash_map: HashMap):
        self.label = zpl.Label(width, height, dpmm)
        self.hash_map = hash_map

    def get_element(self, element_name):
        element = {
            'uuid': str(uuid.uuid4()),
            'type': element_name,
            'x': 0,
            'y': 0,
            'params': self.allowed_elements[element_name]}
        return element

    @staticmethod
    def get_test_zpl():
        l = zpl.Label(50, 50)
        height = 0
        l.origin(0, 0)
        l.write_text("Problem?", char_height=8, char_width=6, line_width=20,
                     justification='C')
        l.endorigin()

        height += 13
        image_width = 5
        l.origin((l.width - image_width) / 2, height)
        image_height = l.write_graphic(
            Image.open(
                os.path.join(os.path.dirname(zpl.__file__), 'trollface-large.png')),
            image_width)
        l.endorigin()

        height += image_height + 5
        l.origin(10, height)
        l.barcode('U', '07000002198', height=20, check_digit='Y')
        l.endorigin()

        l.origin(32, height)
        l.barcode('Q', 'https://github.com/cod3monk/zpl/', magnification=5)
        l.endorigin()

        height += 20
        l.origin(0, height)
        l.write_text('Happy Troloween!', char_height=5, char_width=4, line_width=30,
                     justification='C')
        l.endorigin()

        return l.dumpZPL()

    def get_zpl(self, template: Dict, to_print: Optional[bool] = False):
        self.label.change_international_font()
        self.label.set_default_font(2, 2)
        self._parse_zpl_template(template, to_print)
        return self.label.dumpZPL()

    def add_graphical_box(
            self,
            x: int,
            y: int,
            width: int,
            height: int,
            thickness: int = 1,
            rounding: int = 0,
            color: str = 'B'
    ) -> zpl.Label:
        self.label.origin(x, y)
        self.label.draw_box(width, height, thickness, color, rounding)
        self.label.endorigin()
        return self.label

    def add_border(self, thickness: int):
        self.add_graphical_box(
            x=0,
            y=0,
            width=self._mm_to_dots(self.label.width),
            height=self._mm_to_dots(self.label.height),
            thickness=thickness
        )

    def add_text(
            self,
            x: int,
            y: int,
            text: str,
            char_height: Any = None,
            char_width: Any = None,
            font: str = '0',
            orientation: str = 'N',
            line_width: Any = None,
            max_line: int = 1,
            line_spaces: int = 0,
            justification: str = 'L',
            hanging_indent: int = 0,
            qrcode: bool = False
    ):
        self.label.origin(x, y)
        self.label.write_text(text, char_height, char_width, font, orientation,
                              line_width, max_line, line_spaces, justification,
                              hanging_indent, qrcode)
        self.label.endorigin()

    def add_variable(self, x: int, y: int, text: str):
        text = '[' + text + ']'
        self.add_text(x, y, text)

    def add_barcode(
            self,
            x: int,
            y: int,
            barcode_type: str,
            code: str,
            height: int = 70,
            orientation: str = 'N',
            check_digit: str = 'N',
            print_interpretation_line: str = 'Y',
            print_interpretation_line_above: str = 'N',
            magnification: int = 1,
            errorCorrection: str = 'Q',
            mask: str = '7',
            mode: str = 'N'
    ):
        self.label.origin(x, y)
        self.label.barcode(barcode_type, code, height, orientation, check_digit,
                           print_interpretation_line, print_interpretation_line_above,
                           magnification, errorCorrection, mask, mode)
        self.label.endorigin()

    def add_qrcode(self, x: int, y: int, code: str, magnification: int):
        self.add_barcode(x, y, 'X', code, magnification)

    def add_datamatrix(self, x: int, y: int, code: str, height: int):
        self.add_barcode(x, y, 'Q', code, height)

    def _mm_to_dots(self, value):
        return value * self.label.dpmm

    def _parse_zpl_template(self, template: Dict, to_print: Optional[bool] = False):
        for element in template['elements']:
            func = self._get_func(element['type'])
            if to_print and element['type'] == 'variable':
                func = self.add_text
            func(**element['params'], x=element['x'], y=element['y'])

    def _get_func(self, type: Literal['string', 'variable', 'qrcode', 'datamatrix']):
        functions = {
            'string': self.add_text,
            'variable': self.add_variable,
            'qrcode': self.add_qrcode,
            'datamatrix': self.add_datamatrix,
        }
        return functions[type]



