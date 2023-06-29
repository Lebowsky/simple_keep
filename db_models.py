from datetime import datetime
from pony.orm import *

db = Database()
db.bind(provider='sqlite', filename='database.sqlite', create_db=True)


class BaseEntity(object):
    _pk_attrs_ = []
    _table_ = ''

    @classmethod
    def get_pk(cls):
        pk_list = [str(pk).split('.')[1] for pk in cls._pk_attrs_]
        return pk_list[0] if pk_list else None

    @classmethod
    def get_table_name(cls):
        return cls._table_


class Document(BaseEntity, db.Entity):
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

    barc_flows = Set('BarcFlow')
    goods = Set('DocumentGoods')


class Countragent(BaseEntity, db.Entity):
    _table_ = 'RS_countragents'

    id = PrimaryKey(str, auto=True)
    name = Required(str)
    full_name = Optional(str)
    inn = Optional(str)
    kpp = Optional(str)

    documents = Set(Document)


class Warehouse(BaseEntity, db.Entity):
    _table_ = 'RS_warehouses'

    id = PrimaryKey(str, auto=True)
    name = Required(str)

    documents = Set(Document)
    # adr_documents = Set('RS_adr_docs')


class DocumentGoods(BaseEntity, db.Entity):
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
    id_unit = Optional('GoodsUnit')
    id_price = Optional('PriceType')
    id_cell = Optional('Cell')


class Goods(BaseEntity, db.Entity):
    _table_ = 'RS_goods'

    id = PrimaryKey(str, auto=True)
    code = Required(str)
    name = Required(str)
    art = Optional(str)
    description = Optional(str)

    document_tables = Set(DocumentGoods)
    # adr_document_tables = Set('RS_adr_docs_table')
    property = Optional('GoodsProperty')
    type_good = Required('GoodsType')
    goods_unit = Optional('GoodsUnit')
    barcodes = Set('Barcode')
    unit = Required('ClassifierUnit')


class GoodsProperty(BaseEntity, db.Entity):
    _table_ = 'RS_properties'

    id = PrimaryKey(str, auto=True)
    name = Required(str)
    id_owner = Required(Goods)
    document_tables = Set(DocumentGoods)
    # adr_document_tables = Set('RS_adr_docs_table')
    barcodes = Set('Barcode')


class Series(BaseEntity, db.Entity):
    _table_ = 'RS_series'

    id = PrimaryKey(str, auto=True)
    name = Required(str)
    best_before = Optional(str)
    number = Optional(str)
    production_date = Optional(str)

    document_tables = Set(DocumentGoods)
    # adr_document_table = Set('RS_adr_docs_table')
    type_goods = Required('GoodsType')
    barcodes = Set('Barcode')


class GoodsType(BaseEntity, db.Entity):
    _table_ = 'RS_types_goods'
    id = PrimaryKey(str, auto=True)
    name = Required(str)
    use_mark = Required(bool, default=False)
    goods = Set(Goods)
    series = Set(Series)


class GoodsUnit(BaseEntity, db.Entity):
    _table_ = 'RS_units'

    id = PrimaryKey(str, auto=True)
    code = Optional(str)
    name = Required(str)
    nominator = Required(int)
    denominator = Required(int)
    int_reduction = Optional(str)

    id_owner = Required(Goods)
    document_tables = Set(DocumentGoods)
    # adr_docs_table = Set('RS_adr_docs_table')
    barcodes = Set('Barcode')


class PriceType(BaseEntity, db.Entity):
    _table_ = 'RS_price_types'

    id = PrimaryKey(str, auto=True)
    name = Required(str)

    document_tables = Set(DocumentGoods)


class Cell(BaseEntity, db.Entity):
    _table_ = 'RS_cells'

    id = PrimaryKey(str, auto=True)
    name = Required(str)
    barcode = Optional(str)

    document_tables = Set(DocumentGoods)
    # adr_docs_table = Set('RS_adr_docs_table')


class BarcFlow(BaseEntity, db.Entity):
    _table_ = 'RS_barc_flow'

    id_doc = Required(Document)
    barcode = Optional(str)


class Barcode(BaseEntity, db.Entity):
    _table_ = 'RS_barcodes'

    barcode = PrimaryKey(str)

    id_good = Required(Goods)
    id_property = Optional(GoodsProperty)
    id_series = Optional(Series)
    id_unit = Optional(GoodsUnit)


class ErrorLog(BaseEntity, db.Entity):
    _table_ = 'Error_log'
    log = Optional(str, default="")
    timestamp = Required(datetime, sql_default='CURRENT_TIMESTAMP')


class ClassifierUnit(BaseEntity, db.Entity):
    _table_ = 'RS_classifier_units'

    id = PrimaryKey(str)
    code = Required(str)
    name = Optional(str)

    goods = Set(Goods)


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


models = [
    Document,
    Countragent,
    Warehouse,
    DocumentGoods,
    Goods,
    GoodsProperty,
    GoodsType,
    Series,
    GoodsUnit,
    PriceType,
    Cell,
    Barcode,
    BarcFlow,
    ErrorLog,
    ClassifierUnit
    # RS_constants,
    # RS_adr_docs,
    # RS_adr_docs_table,
    # RS_doc_types
    # RS_classifier_units,
    # RS_marking_codes
    # RS_prices
]

db.generate_mapping(create_tables=True)

if __name__ == '__main__':
    # db.generate_mapping()
    pass
    # import os
    # os.remove('database.sqlite')
    # set_sql_debug(False)
