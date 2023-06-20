from datetime import datetime
from pony.orm import *

db = Database()
db.bind(provider='sqlite', filename='database.sqlite', create_db=True)


class Document(db.Entity):
    _table_ = 'RS_docs'

    id_doc = PrimaryKey(str, auto=True)
    doc_type = Required(str)
    doc_n = Required(str)
    doc_date = Required(str)
    verified = Required(bool, default=False)
    sent = Required(bool, default=False)
    add_mark_selection = Required(bool, default=False)
    control = Required(bool, default=False)
    created_at = Optional(datetime, sql_default='CURRENT_TIMESTAMP')

    id_countragents = Required('Countragent')
    id_warehouse = Optional('Warehouse')

    # barc_flows = Set('RS_barc_flow')
    goods = Set('DocumentGoods')


class Countragent(db.Entity):
    _table_ = 'RS_countragents'

    id = PrimaryKey(str, auto=True)
    name = Required(str)
    full_name = Optional(str)
    inn = Optional(str)
    kpp = Optional(str)

    documents = Set(Document)


class Warehouse(db.Entity):
    _table_ = 'RS_warehouses'

    id = PrimaryKey(str, auto=True)
    name = Required(str)

    documents = Set(Document)
    # adr_documents = Set('RS_adr_docs')


class DocumentGoods(db.Entity):
    _table_ = 'RS_docs_table'

    id = PrimaryKey(int, auto=True)
    qtty = Required(float, default=0)
    qtty_plan = Required(float, default=0)
    price = Required(float, default=0)
    sent = Required(bool, default=False)
    is_plan = Required(bool, default=False)
    last_updated = Optional(datetime, sql_default='CURRENT_TIMESTAMP')
    id_doc = Required(Document)
    id_good = Required('Goods')

    id_properties = Optional('GoodsProperty')
    id_series = Optional('Series')
    # id_unit = Optional('RS_units')
    # id_price = Optional('RS_price_types')
    # id_cell = Optional('RS_cells')


class Goods(db.Entity):
    _table_ = 'RS_goods'

    id = PrimaryKey(str, auto=True)
    code = Required(str)
    name = Required(str)
    art = Optional(str)
    description = Optional(str)
    document_tables = Set(DocumentGoods)
    property = Optional('GoodsProperty')
    type_good = Required('GoodsType')
    # adr_document_tables = Set('RS_adr_docs_table')


class GoodsProperty(db.Entity):
    _table_ = 'RS_properties'

    id = PrimaryKey(str, auto=True)
    name = Required(str)
    id_owner = Required(Goods)
    document_tables = Set(DocumentGoods)
    # adr_document_tables = Set('RS_adr_docs_table')


class Series(db.Entity):
    _table_ = 'RS_series'

    id = PrimaryKey(str, auto=True)
    name = Required(str)
    best_before = Optional(str)
    number = Optional(str)
    production_date = Optional(str)

    document_tables = Set(DocumentGoods)
    # adr_document_table = Set('RS_adr_docs_table')
    type_goods = Required('GoodsType')


class GoodsType(db.Entity):
    _table_ = 'RS_types_goods'
    id = PrimaryKey(str, auto=True)
    name = Required(str)
    use_mark = Required(bool, default=False)
    goods = Set(Goods)
    series = Set(Series)

#
#
# class RS_units(db.Entity):
#     id = PrimaryKey(int, auto=True)
#     document_tables = Set('RS_docs_table')
#     code = Optional(str)
#     name = Optional(str)
#     nominator = Optional(str)
#     denominator = Optional(str)
#     int_reruction = Optional(str)
#     adr_docs_table = Set('RS_adr_docs_table')
#
#
# class RS_price_types(db.Entity):
#     id = PrimaryKey(int, auto=True)
#     document_tables = Set('RS_docs_table')
#     name = Optional(str)
#
#
# class RS_cells(db.Entity):
#     id = PrimaryKey(int, auto=True)
#     name = Optional(str)
#     barcode = Optional(str)
#     document_tables = Set('RS_docs_table')
#     adr_docs_table = Set('RS_adr_docs_table')
#
#
# class RS_adr_docs(db.Entity):
#     id_doc = Required(str)
#     doc_type = Required(str)
#     doc_date = Optional(str)
#     verified = Optional(bool)
#     sent = Optional(bool)
#     add_mark_selection = Optional(bool)
#     created_at = Optional(datetime, sql_default='CURRENT_TIMESTAMP')
#     control = Optional(bool)
#     id_warehouses = Required('RS_warehouses')
#     goods = Set('RS_adr_docs_table')
#     PrimaryKey(id_doc, doc_type)
#
#
# class RS_adr_docs_table(db.Entity):
#     id = PrimaryKey(int, auto=True)
#     id_doc = Required('RS_adr_docs')
#     id_goods = Required('RS_goods')
#     id_properties = Required('RS_properties')
#     id_series = Required('RS_series')
#     id_unit = Required('RS_units')
#     id_cells = Required('RS_cells')
#     qtty = Optional(float)
#     qtty_plan = Optional(float)
#     sent = Optional(bool)
#     last_updated = Optional(str, sql_default='CURRENT_TIMESTAMP')
#     is_plan = Optional(bool, sql_default='True')
#     table_type = Required(str, sql_default='out')
#
#
# class RS_barc_flow(db.Entity):
#     id_doc = Required('RS_docs')
#     barcode = Optional(str)
#
#
# class RS_barcodes(db.Entity):
#     barcode = PrimaryKey(str)
#     id_goods = Required(str)
#     id_property = Optional(str)
#     id_series = Optional(str)
#     id_unit = Optional(str)
#
#
# class RS_classifier_units(db.Entity):
#     id = PrimaryKey(str, auto=True)
#     code = Required(str)
#     name = Required(str)
#
#
# class RS_constants(db.Entity):
#     id = PrimaryKey(int, auto=True)
#     use_series = Required(bool)
#     use_properties = Required(bool)
#     use_mark = Optional(bool)
#     add_if_not_in_plan = Required(bool)
#     path = Optional(str)
#     delete_files = Required(bool)
#     reserved = Optional(bool)
#     max_id_doc = Optional(int)
#     allow_overscan = Optional(str)
#     release = Optional(str)


models = [
    Document,
    Countragent,
    Warehouse,
    DocumentGoods,
    Goods,
    GoodsProperty,
    GoodsType,
    Series,
    # RS_units,
    # RS_price_types,
    # RS_cells,
    # RS_adr_docs,
    # RS_adr_docs_table,
    # RS_barc_flow,
    # RS_barcodes,
    # RS_classifier_units,
    # RS_constants

]

db.generate_mapping(create_tables=True)

if __name__ == '__main__':
    # db.generate_mapping()
    pass
    # import os
    # os.remove('database.sqlite')
    # set_sql_debug(False)
