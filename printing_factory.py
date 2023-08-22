from bs4 import BeautifulSoup
import barcode
from barcode.writer import ImageWriter
from jinja2 import Environment, FileSystemLoader, select_autoescape, meta
import base64
from io import BytesIO
from pathlib import Path


class HTMLDocument:

    def __init__(self, template_directory, template_file):
        self.template_directory = template_directory
        self.template_file = template_file


    @staticmethod
    def generate_barcode(data):
        EAN = barcode.get_barcode_class('ean13')
        ean = EAN(data, writer=ImageWriter())
        barcode_image = BytesIO()
        ean.write(barcode_image)
        return base64.b64encode(barcode_image.getvalue()).decode()

    def create_html(self, parameters):
        env = Environment(
            loader=FileSystemLoader(self.template_directory),
            autoescape=select_autoescape(['html', 'xml']),
            variable_start_string='[',
            variable_end_string=']',
        )

        barcode_image_base64 = self.generate_barcode(parameters['barcode'])

        template = env.get_template(self.template_file)

        aa = template.render(parameters)

        soup = BeautifulSoup(aa, 'html.parser')
        for imgtag in soup.find_all("img"):
            imgtag['src'] = "data:image/png; width:auto; height:auto; base64," + barcode_image_base64

        return str(soup)

    def find_template_variables(self):
        env = Environment(
            loader=FileSystemLoader(self.template_directory),
            autoescape=select_autoescape(['html', 'xml']),
            variable_start_string='[',
            variable_end_string=']',
        )
        template_source = env.loader.get_source(env, self.template_file)[0]
        parsed_content = env.parse(template_source)
        params = meta.find_undeclared_variables(parsed_content)
        if not 'barcode' in params:
            params.add('barcode')
        return params

    def get_template(self):

        with open(Path(self.template_directory) / self.template_file, "r", encoding="utf-8") as file:
            html_body = file.read()

        return html_body

    @staticmethod
    def inject_css_style(html):

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
            min-width: 20mm;    /* Minimum width for the image */
            min-height: 20mm;   /* Minimum height for the image */
            width: 100%;
            height: 70%;        /* This is to keep the height as per your requirements: 70% of the template */
            object-fit: cover;
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

# html_doc = HTMLDocument(template_file='template.html', template_directory='templates')
# html_text = HTMLDocument.default_html
# html_doc.inject_css_style(html_text)
# print(html_text)
