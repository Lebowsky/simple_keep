from ui_global import get_query_result
from db_services import DbCreator
class hashMap:
    def __init__(self):
        self.d = {}

    def put(self, key, val):
        if key == 'toast':
            print(val)
        self.d[key] = val

    def get(self, key):
        return self.d.get(key)

    def remove(self, key):
        if key in self.d:
            self.d.pop(key)

    def delete(self, key):
        if key in self.d:
            self.d.pop(key)

    def containsKey(self, key):
        return key in self.d

    def export(self):
        ex_hashMap = []
        for key in self.d.keys():
            ex_hashMap.append({"key": key, "value": self.d[key]})
        return ex_hashMap

class DataCreator:
    def __init__(self):
        self.service = DbCreator()


        self.samples = {
            'RS_docs': {
                'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'doc_type': '""',
                'doc_n': '""',
                'doc_date': '""',
                'id_countragents': '""',
                'id_warehouse': '""',
                'verified': '1',
                'sent': '0'
            },
            'RS_adr_docs': {
                'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'doc_type': '""',
                'doc_n': '""',
                'doc_date': '""',
                'id_warehouse': '""',
                'verified': '1',
                'sent': '0'
            },
            'RS_docs_table': {
                'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_good': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_properties': '""',
                'id_series': '""',
                'id_unit': '""',
                'qtty': '1',
                'qtty_plan': '5',
                'sent': '0'
            },
            'RS_adr_docs_table': {
                'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_good': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_properties': '""',
                'id_series': '""',
                'id_unit': '""',
                'id_cell': '""',
                'table_type': '"in"',
                'qtty': '1',
                'qtty_plan': '5',
                'sent': '0'
            },
            'RS_docs_barcodes': {
                'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_good': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'id_property': '""',
                'id_series': '""',
                'id_unit': '""',
                'barcode_from_scanner': '"07623900408085tEjE+7qAAAAXi6n"',
                'GTIN': '"07623900408085"',
                'Series': '"tEjE+7q"'
            },
            'RS_barc_flow': {
                'id_doc': '"37c4c709-d22b-11e4-869d-0050568b35ac1"',
                'barcode': '"4680134840398"',
            },
            'RS_goods': {
                'id': '"03d8d818-f585-11e4-92f1-0050568b35ac"',
                'code': '"00-00000109"',
                'name': '"Ящик пластмассовый 80х50 "',
                'art': '"СО-90"',
                'unit': '"bd72d926-55bc-11d9-848a-00112f43529a"',
                'type_good': '"f93e1126-c83a-11e2-8026-0015e9b8c48d"',
                'description': '"Описание"',
            },
            'RS_types_goods': {
                'id': '"f93e1126-c83a-11e2-8026-0015e9b8c48d"',
                'name': '"Тара"',
                'use_mark': '0',
            },
            'RS_units': {
                'id': '"bd72d926-55bc-11d9-848a-00112f43529a"',
                'id_owner': '"03d8d818-f585-11e4-92f1-0050568b35ac"',
                'code': '""',
                'name': '"ящ (10 упак)"',
                'nominator': '10',
                'denominator': '1',
                'int_reduction': '""',
            },
        }

    def insert_data(self, *args):
        for arg in args:
            q = 'INSERT INTO {} ({}) VALUES({})'.format(
                arg,
                ','.join(self.samples[arg].keys()),
                ','.join(self.samples[arg].values())
            )
            get_query_result(q)

    def drop_all_tables(self):
        self.service.drop_all_tables()

    def create_tables(self):
        self.service.create_tables()