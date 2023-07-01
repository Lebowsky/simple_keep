from datetime import datetime
from pony.orm import *

db = Database()
db.bind(provider='sqlite', filename='database.sqlite', create_db=True)


class Document(db.Entity):
    _table_ = 'documents'
    id_doc = PrimaryKey(str, auto=True)
    doc_type = Required(str)
    doc_number = Required(str)
    doc_date = Required(str)
    counteragent = Optional(str)
    is_verified = Required(bool, default=False)
    is_sent = Required(bool, default=False)
    add_mark_selection = Required(bool, default=False)
    on_control = Required(bool, default=False)
    created_at = Required(datetime, sql_default='CURRENT_TIMESTAMP')
    documentgoods = Required('DocumentGoods')


class DocumentGoods(db.Entity):
    _table_ = 'document_goods'
    id = PrimaryKey(int, auto=True)
    qtty = Required(float, default=0)
    qtty_plan = Required(float, default=0)
    price = Required(float, default=0)
    is_sent = Required(bool, default=False)
    last_udated = Required(datetime, sql_default='CURRENT_TIMESTAMP')
    is_plan = Required(bool, default=False)
    documents = Set(Document)


db.generate_mapping(create_tables=True)
set_sql_debug(True)


@db_session
def create_doc():
    goods = Document_goods(is_plan=True)
    d = Document(
        id_doc='11',
        doc_type='type',
        doc_number='1',
        doc_date='123',
        document_goods=goods)


if __name__ == '__main__':
    create_doc()
