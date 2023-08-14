from bs4 import BeautifulSoup
import barcode
from barcode.writer import ImageWriter
from jinja2 import Environment, FileSystemLoader, select_autoescape, meta
import base64
from io import BytesIO


class HTMLDocument:

    def __init__(self, template_file, template_directory):
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
            imgtag['src'] = "data:image/png;base64," + barcode_image_base64

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

        with open(self.template_directory +'/'+ self.template_file, "r", encoding="utf-8") as file:
           html_body  = file.read()

        return html_body


    def inject_css_style(self, html):
        css_style = """
        <style>
          .scaled-table {
            transform: scale({scale_value}); 
            transform-origin: top left; 
          }
        </style>
        """
        soup = BeautifulSoup(html, "html.parser")

        body_tag = soup.body
        if body_tag:
            body_tag.insert(0, css_style)

        table_tags = soup.find_all("table")
        for table_tag in table_tags:
            table_tag["class"] = table_tag.get("class", []) + ["scaled-table"]

        updated_template_content = str(soup)
        return updated_template_content



