import json
import os
from typing import Tuple, Any, Union
from ru.travelfood.simple_ui import SimpleUtilites as suClass
import requests
import zpl
from PIL import Image
from bs4 import BeautifulSoup
import barcode
from barcode.writer import ImageWriter
import qrcode
from jinja2 import Environment, FileSystemLoader, select_autoescape, meta
import base64
from io import BytesIO
from pathlib import Path
from java import jclass
from ui_utils import HashMap
from ru.travelfood.simple_ui import SimpleBluetooth
noClass = jclass("ru.travelfood.simple_ui.NoSQL")
print_ncl = noClass("print_ncl")
bt = SimpleBluetooth()


class HTMLDocument:
    def __init__(self, template_directory, template_file):
        self.template_directory = template_directory
        self.template_file = template_file

    @staticmethod
    def generate_barcode(data, barcode_type='ean13'):
        ean_class = barcode.get_barcode_class(barcode_type)
        writer = ImageWriter()
        ean = ean_class(data, writer=writer)

        barcode_image = BytesIO()
        ean.write(barcode_image)
        return base64.b64encode(barcode_image.getvalue()).decode()

    @staticmethod
    def generate_qr_code(barcode_data):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(barcode_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffered = BytesIO()
        img.save(buffered, format="PNG")

        return base64.b64encode(buffered.getvalue()).decode()

    def create_html(self, parameters, barcode_type='ean13'):
        env = Environment(
            loader=FileSystemLoader(self.template_directory),
            autoescape=select_autoescape(['html', 'xml']),
            variable_start_string='[',
            variable_end_string=']',
        )
        if barcode_type == 'qr-code':
            barcode_image_base64 = self.generate_qr_code(parameters['barcode'])
        else:
            barcode_image_base64 = self.generate_barcode(parameters['barcode'],
                                                         barcode_type)

        template = env.get_template(self.template_file)

        aa = template.render(parameters)

        soup = BeautifulSoup(aa, 'html.parser')
        for imgtag in soup.find_all("img"):
            imgtag['src'] = ("data:image/png; width:auto; height:auto; base64,"
                             + barcode_image_base64)

        return str(soup)

    @staticmethod
    def find_template_variables(directory: str, file_name: str):
        env = Environment(
            loader=FileSystemLoader(directory),
            autoescape=select_autoescape(['html', 'xml']),
            variable_start_string='[',
            variable_end_string=']',
        )
        template_source = env.loader.get_source(env, file_name)[0]
        parsed_content = env.parse(template_source)
        params = meta.find_undeclared_variables(parsed_content)
        if 'barcode' not in params:
            params.add('barcode')
        return params

    def get_template(self):

        with open(Path(self.template_directory) / self.template_file, "r",
                  encoding="utf-8") as file:
            html_body = file.read()

        return html_body

    @staticmethod
    def inject_css_style(html, width: str, height: str, x: str, y: str):
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


class PrintService:

    @staticmethod
    def make_zpl_from_label(
            image_width_print_template: int,
            image_height_print_template: int,
            dpmm_print_template: int,
            image_x_print_template: int,
            image_y_print_template: int,
            image_ll_print_template: int,
            image_pw_print_template: int,
            path_to_img: str
    ) -> str:
        """Возвращает строку zpl с картинкой внутри"""
        label = zpl.Label(
            width=image_width_print_template * 2,
            height=image_height_print_template * 2,
            dpmm=dpmm_print_template
        )
        label.origin(image_x_print_template, image_y_print_template)
        label.write_graphic(
            image=Image.open(path_to_img),
            width=image_width_print_template * 2,
            height=image_height_print_template * 2
        )
        label.endorigin()
        zpl_data = label.dumpZPL()
        ll = image_ll_print_template
        pw = image_pw_print_template
        if ll and pw:
            zpl_data = zpl_data.replace('^XA', '^XA' + f'^LL{ll}' + f'^PW{pw}', 1)
        return zpl_data

    @staticmethod
    def zpl_to_png_from_api(
            zpl_data: str,
            dpmm: int,
            label_width: int,
            label_height: int,
    ) -> Tuple[bool, Any]:
        """
        Делает запрос к API. Отправляются zpl код и размеры этикетки.
        """
        files = {'file': zpl_data}

        url = (f'http://api.labelary.com/v1/printers/{dpmm}dpmm/'
               f'labels/{mm_to_inch(label_width * 2)}x{mm_to_inch(label_height * 2)}/0/')
        try:
            response = requests.post(url, files=files, stream=True)
        except Exception as e:
            return False, str(e)
        if response.status_code != 200:
            return False, response.text

        response.raw.decode_content = True
        return True, response.raw

    @staticmethod
    def print(hash_map, data: dict):
        if not data:
            return

        label_path = print_ncl.get('current_label_template_path')
        if not label_path:
            hash_map.toast('Нет шаблона')
            return
        matching_table = json.loads(print_ncl.get('matching_table'))
        template_directory, template_file = os.path.split(label_path)
        data_for_printing = replase_params_names(data, matching_table)

        htmlresult = HTMLDocument(
            template_directory, template_file
        ).create_html(data_for_printing, barcode_type=print_ncl.get('barcode_type'))

        htmlresult = HTMLDocument.inject_css_style(
            htmlresult,
            width=str(int(print_ncl.get('barcode_width'))),
            height=str(int(print_ncl.get('barcode_height'))),
            x=str(int(print_ncl.get('barcode_right'))
                  - int(print_ncl.get('barcode_left'))),
            y=str(int(print_ncl.get('barcode_down'))
                  - int(print_ncl.get('barcode_up'))),
        )

        hash_map.toast('Отправлено на печать')
        hash_map.put(
            "RunEvent",
            json.dumps([{
                "action": "runasync",
                "type": "html2image",
                "method": htmlresult,
                "postExecute": json.dumps([{
                    "action": "run",
                    "type": "python",
                    "method": "print_post_execute"
                }])
            }])
        )

        filename = suClass.get_temp_file("png")
        print_ncl.put('path_to_html2image_file', filename, True)
        hash_map.put("html2image_ToFile", filename)

    @staticmethod
    def print_post_execute(hash_map: HashMap):
        path_to_img = print_ncl.get('path_to_html2image_file')
        saved_template = print_ncl.get('saved_print_template')
        if not saved_template:
            hash_map.toast('Нет сохраненного шаблона печати')
            return
        saved_template = json.loads(saved_template)
        zpldata = PrintService.make_zpl_from_label(
            path_to_img=path_to_img, **saved_template)
        PrintService.print_zpl(zpldata, hash_map)

    @staticmethod
    def print_zpl(zpl_data: str, hash_map: HashMap):
        print_through = print_ncl.get('print_through')
        if not print_through:
            hash_map.toast('Не выбрано устройство для печати')
        elif print_through == 'BT':
            sent, result = PrintService.print_bt(zpl_data)
            hash_map.toast(result)
        elif print_through == 'WiFi':
            print_ncl.put('wifi_data_to_print', zpl_data, True)
            hash_map.run_event_async('print_wifi')

    @staticmethod
    def print_wifi(hash_map: HashMap):
        ip = print_ncl.get('current_ip')
        if not ip:
            hash_map.toast('Не указан ip')
            return
        data = print_ncl.get('wifi_data_to_print')
        if not data:
            hash_map.toast('Нет данных для печати wifi')
            return
        print_ncl.delete('wifi_data_to_print')
        fail_handlers = [{"action": "run", "type": "python", "method": "wifi_error"}]
        sended = suClass.write_socket(ip, 9100, data, json.dumps(fail_handlers))
        hash_map.toast('Успешно' if sended else 'Не отправлено')

    @staticmethod
    def print_bt(data: Union[str, int, bytes]):
        ncl = noClass("bt_settings")
        bt_handlers = [{"action": "run", "type": "python", "method": "bluetooth_error"}]
        printer = ncl.get("default_printer")
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

    @staticmethod
    def bluetooth_error(hashmap: HashMap):
        hashmap.playsound('error')
        hashmap.put("speak", "Не удалось подключиться Bluetooth")

    @staticmethod
    def wifi_error(hash_map: HashMap):
        hash_map.playsound('error')
        hash_map.put("speak", "Не удалось подключиться WiFi")


def mm_to_inch(size_mm: int) -> float:
    return size_mm / 25.4


def inch_to_mm(size_inch: int) -> float:
    return size_inch * 25.4


def replase_params_names(data_for_printing, params_match):
    new_data = {}
    for match in params_match:
        if match['value'] in data_for_printing.keys():
            new_data[match['key']] = data_for_printing[match['value']]
    return new_data
