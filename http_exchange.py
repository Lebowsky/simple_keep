import ipaddress
import json
import requests
from requests.auth import HTTPBasicAuth
#import time
import ui_barcodes

import ui_global
from hs_services import HsService
from db_services import DocService
from ui_global import get_query_result

def replase_gs_in_res(struct):
    return [{k: v.replace(chr(29), '').replace(chr(232), '').replace(chr(32),'') if isinstance(v, str) else v for k, v in d.items()} for d in struct]
    # for el in struct:
    #     if el.get('barcode_from_scanner'):
    #         el['barcode_from_scanner'] = el['barcode_from_scanner'].replace(chr(29),'')
    #         el['barcode_from_scanner'] = el['barcode_from_scanner'].replace(chr(232), '')


def parse_barcode(val):
    if len(val) < 21:
        return {'GTIN': '', 'Series': ''}

    val.replace('(01)','01')
    val.replace('(21)', '21')
    if val[:2]=='01':
        GTIN = val[2:16]
        Series = val[18:]

    else:
        GTIN = val[:14]
        Series = val[14:]

    return {'GTIN':GTIN, 'Series':Series}


def server_load_data(http):
    username = http['user']
    password =http['pass']
    url = http['url']
    android_id = http['android_id']


    #android_id ='7b1bc913358b7049'
    # r = requests.get(url + '/get_data?android_id=' + android_id, auth=HTTPBasicAuth(username, password, ),
    #                  headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'},
    #                  params={'code': android_id, 'full_load': full_load})
    r = requests.get(url + '/simple_accounting/data?android_id=' + android_id, auth=HTTPBasicAuth(username, password, ),
                     headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'},
                     params={'user_name': http['user_name'], 'device_model': http['device_model']})
    # print(r.status_code)
    # print(r.text)
    answer = {'status_code': r.status_code}
    if r.status_code == 200:
        r.encoding = 'utf-8'
        jdata = json.loads(r.text.encode("utf-8"))

        if 'format' in jdata.keys():
            answer['format'] = jdata['format']
            if jdata['format'] == 'is_data':
                #Парсим, параметр data содержит список словарей с данными запроса
                res_for_sql = json_to_sqlite_query(jdata['data'])
                if res_for_sql:
                    answer['res_for_sql'] = res_for_sql

            elif jdata['format'] == 'is_ok': #Наш запрос принят, но вернуть пока нечего. Данные или готовятся или их нет
                if jdata.get('batch') is not None:
                    answer['batch'] = jdata.get('batch')

            elif jdata['format'] == 'file_list':
                column_names = []
                for files in jdata['data']:
                    column_names.append(files)

        else:
            answer['format'] = None


    elif r.status_code == 403:

        answer['error_pool'] =[r.text]
    elif r.status_code == 401:
        answer['error_pool']=[r.reason]
    else:
        answer['error_pool']=[r.text]

    return answer



    # подтверждаем принятие пакета данных в 1С
    # r = requests.get(url + '/get_exchange_confirmation?android_id=' + android_id,
    #                  auth=HTTPBasicAuth(username, password, ),
    #                  headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'},
    #                  params={'code': android_id, 'NNmessage': NNmessage})



def json_to_sqlite_query(data):

    qlist = []
    #Цикл по именам таблиц
    table_list = (
    'RS_doc_types', 'RS_goods', 'RS_properties', 'RS_units', 'RS_types_goods', 'RS_series', 'RS_countragents',
    'RS_warehouses', 'RS_price_types', 'RS_cells', 'RS_barcodes', 'RS_prices', 'RS_doc_types', 'RS_docs',
    'RS_docs_table', 'RS_docs_barcodes', 'RS_adr_docs', 'RS_adr_docs_table') #,, 'RS_barc_flow'
    table_for_delete = ('RS_docs_table', 'RS_docs_barcodes, RS_adr_docs_table')  #, 'RS_barc_flow'
    doc_id_list = []
    for table_name in table_list:
        if data.get(table_name) is None:
            continue

    #for table_name in data['data']:
        if data[table_name] == []:
            continue
        #Добавим в запросы удаление из базы строк тех документов, что мы загружаем
        if table_name in table_for_delete:
            query = f"DELETE FROM {table_name} WHERE id_doc in ({', '.join(doc_id_list)}) "
            qlist.append(query)

        column_names = data[table_name][0].keys()
        if 'mark_code' in column_names:
            query_col_names = list(column_names)
            query_col_names.append('GTIN')
            query_col_names.append('Series')
            query_col_names.remove('mark_code')
        else:
            query_col_names = column_names

        query = f"REPLACE INTO {table_name} ({', '.join(query_col_names)}) VALUES "
        values = []

        for row in data[table_name]:

            row_values = []
            list_quoted_fields = ('name', 'full_name', "mark_code", "art")
            for col in column_names:
                if col in list_quoted_fields and  "\"" in row[col]:
                    row[col] = row[col].replace("\"", "\"\"")
                if row[col] is None:
                    row[col] = ''
                if col == 'mark_code':   #Заменяем это поле на поля GTIN и Series
                    barc_struct = parse_barcode(row[col])
                    row_values.append(barc_struct['GTIN'])
                    row_values.append(barc_struct['Series'])
                else:
                    row_values.append(row[col])  #(f'"{row[col]}"')
                if col == 'id_doc' and table_name == 'RS_docs':
                    doc_id_list.append('"'+row[col]+'"')
            formatted_val  = [f'"{x}"' if isinstance(x, str) else str(x) for x in row_values]
            values.append(f"({', '.join(formatted_val)})")
        query += ", ".join(values)
        qlist.append(query)


    return qlist



def get_all_changes_from_database(doc_list=''):
    try:
        qtext = f'''
        SELECT * FROM RS_docs WHERE id_doc in ({doc_list})'''
        res = ui_global.get_query_result(qtext,None,True)
        qtext = f'''
            SELECT * FROM RS_docs_table WHERE id_doc in ({doc_list})'''# in (
            #SELECT id_doc FROM RS_docs WHERE verified is Null)'''
        res_docs_table = ui_global.get_query_result(qtext,None,True)
        qtext = f'''
            SELECT * FROM RS_docs_barcodes WHERE id_doc in ({doc_list}) and barcode_from_scanner is not Null'''# in (
            #SELECT id_doc FROM RS_docs WHERE verified is Null)'''
        res_docs_barcode = ui_global.get_query_result(qtext,None,True)
        res_docs_barcode = replase_gs_in_res(res_docs_barcode)
        qtext = f'''
            SELECT * FROM RS_barc_flow WHERE id_doc in ({doc_list})'''# in (
            #SELECT id_doc FROM RS_docs WHERE verified is Null)'''
        res_flow = ui_global.get_query_result(qtext,None,True)
        res_flow = replase_gs_in_res(res_flow)
    except Exception as e:
            sql_error = True
            #error_pool.append(e.args[0])
            return {'Error':e.args[0]}
    # if len(res) == 0:
    #     return None

    for item in res:
        filtered_list = [d for d in res_docs_table if d['id_doc'] == item['id_doc']]
        item['RS_docs_table'] = filtered_list

        filtered_list = [d for d in res_docs_barcode if d['id_doc'] == item['id_doc']]
        item['RS_docs_barcodes'] = filtered_list

        filtered_list = [d for d in res_flow if d['id_doc'] == item['id_doc']]
        item['RS_barc_flow'] = filtered_list
    #Адресное хранение
    try:
        qtext = f'''
        SELECT * FROM RS_adr_docs WHERE id_doc in ({doc_list})'''
        res_adr = ui_global.get_query_result(qtext,None,True)
        qtext = f'''
            SELECT * FROM RS_adr_docs_table WHERE id_doc in ({doc_list})'''# in (
            #SELECT id_doc FROM RS_docs WHERE verified is Null)'''
        res_adr_docs_table = ui_global.get_query_result(qtext,None,True)

    except Exception as e:
            sql_error = True
            #error_pool.append(e.args[0])
            return {'Error':e.args[0]}
    # if len(res) == 0:
    #     return None

    for item in res_adr:
        filtered_list = [d for d in res_adr_docs_table if d['id_doc'] == item['id_doc']]
        item['RS_adr_docs_table'] = filtered_list



    if len(res) + len(res_adr) == 0:
        return None

    return json.dumps(res + res_adr)


def post_changes_to_server(doc_list, htpparams):
    url = htpparams['url']
    username = htpparams['user']
    password = htpparams['pass']
    android_id = htpparams['android_id']
    res = get_all_changes_from_database(doc_list)
    if type(res) == type(dict) and res.get('Error'):
        answer = {'empty': True, 'Error':res.get('Error')}

        return answer
    answer = {'empty':True}
    if res is not None:

        r = requests.post(url + '/simple_accounting/documents?android_id=' + android_id,
                         auth=HTTPBasicAuth(username, password, ),
                         headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'},
                         params={'user_name': htpparams['user_name'], 'device_model': htpparams['device_model']},
                          data=res )
        answer['status_code'] =r.status_code
        if r.status_code == 200:
            answer['empty']=False
        else:
            answer['empty'] = True
            answer['Error'] = r.text

    return answer


def post_goods_to_server(doc_id, http_params):
    hs_service = HsService(http_params)
    doc_service = DocService(doc_id)

    res = doc_service.get_last_edited_goods(to_json=False)

    if isinstance(res, dict) and res.get('Error'):
        answer = {'empty': True, 'Error': res.get('Error')}
        return answer
    elif res:
        hs_service.send_documents(res)
        if not res or (isinstance(res, dict) and res.get('Error')):
            answer = {'empty': True, 'Error': res.get('Error')}
            return answer
        else:
            doc_service.update_sent_data(res)

    timer_server_load_data(http_params)


def timer_server_load_data(http_params):
    hs_service = HsService(http_params)
    doc_service = DocService('')

    docs_data = hs_service.get_data()
    if docs_data.get('data'):
        try:
            existing_docs_list = doc_service.get_existing_docs_names_list()
            doc_service.update_data_from_json(docs_data['data'])
            docs_list_after_load = doc_service.get_existing_docs_names_list()
            diff = [x[0] for x in docs_list_after_load if x not in existing_docs_list]
            if diff:
                return " ".join(diff)
        except Exception as e:
            raise e
            # return {'empty': True, 'Error': e.args[0]}



