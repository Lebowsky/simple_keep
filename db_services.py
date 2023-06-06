import json
from ui_global import get_query_result


class DocService:
    def __init__(self, doc_id):
        self.doc_id = doc_id

    def get_last_edited_goods(self, to_json=False):
        query_docs = f'SELECT * FROM RS_docs WHERE id_doc = ?'

        query_goods = '''
        SELECT T2.* 
        FROM (
            SELECT 
                id_doc, 
                max(last_updated) as last_updated 
            FROM RS_docs_table 
            WHERE id_doc = ? 
            GROUP BY id_doc) as T1 
        JOIN RS_docs_table as T2 ON T1.id_doc = T2.id_doc AND T1.last_updated = T2.last_updated
        '''

        try:
            res_docs = get_query_result(query_docs, (self.doc_id,), True)
            res_goods = get_query_result(query_goods, (self.doc_id,), True)
        except Exception as e:
            return {'Error': e.args[0]}

        for item in res_docs:
            filtered_list = [d for d in res_goods if d['id_doc'] == item['id_doc']]
            item['RS_docs_table'] = filtered_list
            item['RS_docs_barcodes'] = []
            item['RS_barc_flow'] = []

        if to_json:
            return json.dumps(res_docs)
        else:
            return res_docs
