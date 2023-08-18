from java import jclass
noClass = jclass("ru.travelfood.simple_ui.NoSQL")
rs_settings = noClass("rs_settings")


import json

from flask import Flask
from flask import request

import main
import ui_models
#from rs_settings import RSSettings as rs_settings
from ui_utils import HashMap

app = Flask(__name__)

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
    'signal_num': 83,
    'beep_duration': 1000,
    'use_mark': 'false',
    'add_if_not_in_plan': 'false',
    'path': '',
    'delete_files': 'false',
    'allow_overscan': 'false',
    'path_to_databases': '//data/data/ru.travelfood.simple_ui/databases',
    'sqlite_name': 'SimpleKeep',
    'log_name': 'log.json',
    'timer_is_disabled': False,
    'allow_fact_input': 'false',
    'URL':'http://192.168.1.77/Mark/hs/',
    'USER' : 'user_1',
    'PASS' : '111',
    'DEVICE_MODEL':'Python',
    'ANDROID_ID':'f0559476b8a26877',
    'user_name':'Kjuzma'
}

for k, v in rs_default_settings.items():
    if rs_settings.get(k) is None:
        rs_settings.put(k, v, True)

def tiles_on_input(hash_map: HashMap):
    main.tiles_on_input(hash_map)

def tiles_on_start(hash_map: HashMap):
    main.tiles_on_start(hash_map)

def docs_on_start(hash_map: HashMap):
    main.docs_on_start(hash_map)


def docs_on_select(hash_map: HashMap):
    main.docs_on_select(hash_map)


def app_on_start(hash_map: HashMap):
    main.app_on_start(hash_map)

def doc_details_on_start(hash_map: HashMap):
    main.doc_details_on_start(hash_map)

def doc_details_listener(hash_map):
    main.doc_details_listener(hash_map)


def doc_details_barcode_scanned(hash_map):
    main.doc_details_barcode_scanned(hash_map)

def adr_docs_on_start(hash_map):
    main.adr_docs_on_start(hash_map)

def docs_adr_on_select(hash_map):
    main.docs_adr_on_select(hash_map)

def adr_doc_on_select(hash_map):
    main.adr_doc_on_select(hash_map)

def adr_doc_details_on_start(hash_map):
    main.adr_doc_details_on_start(hash_map)

def adr_doc_details_on_input(hash_map):
    main.adr_doc_details_on_input(hash_map)

def settings_on_click(hash_map):
    main.rs_settings = rs_settings.RSSettings()
    main.rs_settings.put('URL' , 'http://192.168.1.77/Mark/hs/')
    main.rs_settings.put('USER' , 'ADM')
    main.rs_settings.put('PASS' , '1')
    main.rs_settings.put('DEVICE_MODEL' , 'Python')
    main.rs_settings.put('ANDROID_ID','f0559476b8a26877')  # 'c51133488568c92b',
    main.rs_settings.put('user_name', 'Gerald')

    main.settings_on_click(hash_map)

def debug_listener(hash_map):
    main.debug_listener(hash_map)

def universal_cards_on_start(hash_map):
    main.universal_cards_on_start(hash_map)


def universal_cards_listener(hash_map):
    main.universal_cards_listener(hash_map)


def flow_docs_on_start(hash_map):
    main.flow_docs_on_start(hash_map)



def flow_docs_on_select(hash_map):
    main.flow_docs_on_select(hash_map)



def barcode_flow_on_start(hash_map):
    main.barcode_flow_on_start(hash_map)

def barcode_flow_listener(hash_map):
    main.barcode_flow_listener(hash_map)

def html_view_on_start(hash_map):
    main.html_view_on_start(hash_map)

def good_card_on_input(hash_map):
    main.good_card_on_input(hash_map)

def good_card_post_start(hash_map):
    main.good_card_post_start(hash_map)


def good_card_on_start(hash_map):
    main.good_card_on_start(hash_map)


def html_view_on_input(hash_map):
    main.html_view_on_input(hash_map)


def template_list_on_start(hash_map):
    main.template_list_on_start(hash_map)


def template_list_on_input(hash_map):
    main.template_list_on_input(hash_map)

def file_browser_on_start(hash_map):
    main.file_browser_on_start(hash_map)


def file_browser_on_input(hash_map):
    main.file_browser_on_input(hash_map)

def elem_viev_on_click(hash_mao):
    main.elem_viev_on_click(hash_mao)

class hashMap:
    d = {}

    def put(key, val):
        if key == 'toast':
            print(val)
        hashMap.d[key] = val

    def get(key):
        return hashMap.d.get(key)

    def remove(key):
        if key in hashMap.d:
            hashMap.d.pop(key)

    def delete(key):
        if key in hashMap.d:
            hashMap.d.pop(key)

    def containsKey(key):
        return key in hashMap.d

    def export(self):
        ex_hashMap = []
        for key in self.d.keys():
            ex_hashMap.append({"key": key, "value": hashMap.d[key]})
        return ex_hashMap

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/set_input_direct/<method>', methods=['POST'])
def set_input(method):
    # func = method.replace('_', '', 1)
    jdata = json.loads(request.data.decode("utf-8"))
    f = globals()[method]
    hashMap.d = jdata['hashmap']
    f(hashMap)
    jdata['hashmap'] = hashMap.export(hashMap)
    jdata['stop'] = False
    jdata['ErrorMessage'] = ""
    jdata['Rows'] = []

    return json.dumps(jdata)


#Tест соединения


#http = get_http_settings(hashMap)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2075, debug=True)
