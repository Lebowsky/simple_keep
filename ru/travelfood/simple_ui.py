import json

from ui_global import get_query_result, bulk_query


class SimpleUtilites:
    def urovo_set_lock_trigger(self, bol: bool):
        pass

    def urovo_open_scanner(self):
        pass

    def urovo_start_decode(self):
        pass

    def urovo_stop_decode(self):
        pass


class ImportUtils:
    def __init__(self):
        self.views = {'btn_barcodes': self.get_btn_barcodes}

    def getView(self, view):
        return self.views[view]()

    def get_btn_barcodes(self):
        return BtnBarcodes()


class BtnBarcodes:
    def setBackground(self, background):
        self.background = background

    def setElevation(self, elevation):
        self.elevation = elevation


class SimpleSQLProvider:
    def __init__(self):
        self.sql_text = ''
        self.sql_params = None

    def SQLExec(self, q, params):
        self.sql_text = q
        self.sql_params = params

        if params:
            return json.dumps(get_query_result(q, tuple(params.split(','))))
        else:
            return json.dumps(get_query_result(q))

    def SQLExecMany(self, q, params):
        self.sql_text = q
        self.sql_params = params

        bulk_query(q, json.loads(params))

    def SQLQuery(self, q, params):
        self.sql_text = q
        self.sql_params = params

        if params:
            return json.dumps(get_query_result(q, tuple(params.split(',')), return_dict=True))
        else:
            return json.dumps(get_query_result(q, return_dict=True))
