#import ui_global
def database_shema():
    Rs = []


    #Константы и хранимые настройки RS_constants
    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_constants (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        use_series     TEXT    DEFAULT 0
                               NOT NULL,
        use_properties TEXT    DEFAULT 0
                               NOT NULL,
        use_mark       TEXT    DEFAULT 0
                               NOT NULL,
        add_if_not_in_plan     TEXT    DEFAULT 0
                               NOT NULL,
        path           TEXT    NOT NULL
                            DEFAULT "//storage/emulated/0/Android/data/ru.travelfood.simple_ui/",
        delete_files   TEXT    DEFAULT 0
                               NOT NULL,
        reserved       TEXT    NOT NULL,
        max_id_doc         INTEGER NOT NULL
                               DEFAULT (1),
        allow_overscan TEXT    DEFAULT 0
                               NOT NULL,
        release        TEXT
    )
    ''')


    # Классификатор единиц измерения RS_classifier_units
    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_classifier_units (
        id TEXT NOT NULL
                     PRIMARY KEY,
        code    TEXT NOT NULL,
        name    TEXT NOT NULL
    )
    ''')

    # Виды номенклатуры RS_types_goods
    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_types_goods (
    id       TEXT NOT NULL
                  PRIMARY KEY,
    name     TEXT NOT NULL,
    use_mark INT  DEFAULT (0) 
    )
    ''')

    # Номенклатура RS_goods
    Rs.append('''
        CREATE TABLE IF NOT EXISTS RS_goods (
            id     TEXT NOT NULL
                             PRIMARY KEY,
            code        TEXT NOT NULL,
            name        TEXT NOT NULL,
            art         TEXT,
            unit        TEXT  REFERENCES RS_classifier_units (id),
            type_good   TEXT NOT NULL
                             REFERENCES RS_types_goods (id) ON DELETE NO ACTION
                                                                 MATCH [FULL],
            description TEXT
        )
        ''')


    # Характеристики номенклатуры RS_properties
    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_properties (
    id       TEXT NOT NULL
                  PRIMARY KEY ON CONFLICT REPLACE,
    id_owner TEXT NOT NULL
                  REFERENCES RS_goods (id) ON DELETE NO ACTION
                                           ON UPDATE NO ACTION,
    name     TEXT NOT NULL
    )
    ''')


    # Упаковки Единицы измерения RS_units
    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_units (
        id       TEXT    NOT NULL
                              PRIMARY KEY,
        id_owner      TEXT    NOT NULL
                              REFERENCES RS_goods (id),
        code          TEXT    NOT NULL,
        name          TEXT    NOT NULL,
        nominator     INTEGER NOT NULL,
        denominator   INTEGER NOT NULL,
        int_reduction TEXT    NOT NULL
    )
    ''')



    # Серии номенклатуры RS_series
    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_series (
        id         TEXT NOT NULL
                             PRIMARY KEY,
        name            TEXT NOT NULL,
        best_before     TEXT,
        type_goods      TEXT NOT NULL,
        number          TEXT NOT NULL,
        production_date TEXT NOT NULL
    )
    ''')

    #Индексы RS_series
    Rs.append('''CREATE INDEX IF NOT EXISTS  Series_name ON RS_series (
    name ASC )
    ''')

    # Штрихкоды RS_barcodes
    Rs.append( '''
    CREATE TABLE IF NOT EXISTS RS_barcodes (
    barcode     TEXT NOT NULL
                     PRIMARY KEY,
    id_good     TEXT NOT NULL,
    id_property TEXT,
    id_series   TEXT,
    id_unit     TEXT,
    ratio       INT  DEFAULT (1) 
                NOT NULL
    )
    ''')

    #Коды маркировки RS_marking_codes
    Rs.append( '''
    CREATE TABLE IF NOT EXISTS RS_marking_codes (
        id          TEXT NOT NULL
                         PRIMARY KEY,
        mark_code   TEXT NOT NULL,
        id_good     TEXT NOT NULL
                         REFERENCES RS_goods (id),
        id_property TEXT NOT NULL
                         REFERENCES RS_properties (id),
        id_series   TEXT NOT NULL
                         REFERENCES RS_series (id),
        id_unit     TEXT NOT NULL
                         REFERENCES RS_units (id) 
    )
    ''')



    # Контрагенты RS_countragents
    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_countragents (
        id   TEXT NOT NULL
                       PRIMARY KEY,
        name      TEXT NOT NULL,
        full_name TEXT NOT NULL,
        inn       TEXT NOT NULL,
        kpp       TEXT NOT NULL
    )
    ''')

    # Склады RS_warehouses
    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_warehouses (
        id TEXT NOT NULL
                     PRIMARY KEY,
        name    TEXT NOT NULL
    )
    ''')

    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_cells (
    id   TEXT PRIMARY KEY
              NOT NULL,
    name TEXT NOT NULL,
    barcode TEXT
    )''')

    # Виды цен номенклатуры RS_price_types
    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_price_types (
        id   TEXT NOT NULL
                  PRIMARY KEY,
        name TEXT NOT NULL
    )
    ''')

    # Цены номенклатуры RS_prices
    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_prices (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        id_price_types TEXT    NOT NULL
                               REFERENCES RS_price_types (id),
        id_goods       TEXT    NOT NULL
                               REFERENCES RS_goods (id),
        id_properties  TEXT    NOT NULL
                               REFERENCES RS_properties (id),
        price          REAL,
        id_unit        TEXT    NOT NULL
                               REFERENCES RS_units (id) 
    )
    ''')

    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_doc_types (
    doc_type TEXT PRIMARY KEY ON CONFLICT REPLACE
                NOT NULL,
    is_adr_storage INT  DEFAULT (0) 
    )
    ''')

    # Все документы списком RS_docs
    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_docs (
        id_doc             TEXT     NOT NULL
                                    PRIMARY KEY,
        doc_type           TEXT     NOT NULL,
        doc_n              TEXT     NOT NULL,
        doc_date           TEXT     NOT NULL,
        id_countragents    TEXT     NOT NULL
                                    REFERENCES RS_countragents (id),
        id_warehouse       TEXT     NOT NULL
                                    REFERENCES RS_warehouses (id),
        verified           INTEGER,
        sent               INTEGER,
        add_mark_selection INTEGER,
        created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
        control            TEXT DEFAULT 0,
        is_group_scan      TEXT DEFAULT 0,
        allow_fact_input   TEXT DEFAULT 0
        
    )
    ''')


    # Табличная часть документов RS_docs_table
    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_docs_table (
        id            INTEGER  PRIMARY KEY AUTOINCREMENT,
        id_doc        TEXT     NOT NULL
                               REFERENCES RS_docs (id_doc) ON DELETE CASCADE
                                                           ON UPDATE SET DEFAULT,
        id_good       TEXT     NOT NULL
                               REFERENCES RS_goods (id),
        id_properties TEXT     REFERENCES RS_properties (id),
        id_series     TEXT     REFERENCES RS_series (id),
        id_unit       TEXT     NOT NULL
                               REFERENCES RS_units (id),
        qtty          REAL,
        d_qtty        REAL,  
        qtty_plan     REAL,
        price         REAL,
        id_price      TEXT     REFERENCES RS_price_types (id),
        sent          INTEGER,
        last_updated  DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_plan       TEXT DEFAULT "True",
        id_cell          TEXT     REFERENCES RS_cells (id),
        use_series      INTEGER DEFAULT 0 
    )
    ''')


    # Коды маркировки в документе RS_docs_barcodes
    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_docs_barcodes (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    id_doc               TEXT    NOT NULL 
                                 REFERENCES RS_docs (id_doc) ON DELETE CASCADE,
    id_good     TEXT NOT NULL
         REFERENCES RS_goods (id),
    id_property TEXT NOT NULL
                     REFERENCES RS_properties (id),
    id_series   TEXT NOT NULL
                     REFERENCES RS_series (id),
    id_unit     TEXT NOT NULL
                     REFERENCES RS_units (id) ,
    --# id_barcode           TEXT    NOT NULL
    --#                              REFERENCES RS_marking_codes (id),
    barcode_from_scanner TEXT,
    is_plan              TEXT    DEFAULT 0
                                 NOT NULL,
    approved             TEXT    DEFAULT 0,
    GTIN                 TEXT,
    Series               TEXT
    )
    ''')

    #Поток произвольных штрихкодов
    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_barc_flow (
    id_doc  TEXT REFERENCES RS_docs (id_doc),
    barcode TEXT
    )
    ''')

    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_adr_docs (
    id_doc             TEXT     NOT NULL
                                PRIMARY KEY,
    doc_type           TEXT     NOT NULL,
    doc_n              TEXT     NOT NULL,
    doc_date           TEXT     NOT NULL,
    id_warehouse       TEXT     NOT NULL
                                REFERENCES RS_warehouses (id),
    verified           INTEGER,
    sent               INTEGER,
    add_mark_selection INTEGER,
    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    control            TEXT     DEFAULT 0,
    allow_fact_input   TEXT DEFAULT 0
    
    )
    ''')

    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_adr_docs_table (
    id            INTEGER  PRIMARY KEY AUTOINCREMENT,
    id_doc        TEXT     NOT NULL
                           REFERENCES RS_adr_docs (id_doc) ON DELETE CASCADE
                                                           ON UPDATE SET DEFAULT,
    id_good       TEXT     NOT NULL
                           REFERENCES RS_goods (id),
    id_properties TEXT     REFERENCES RS_properties (id),
    id_series     TEXT     REFERENCES RS_series (id),
    id_unit       TEXT     REFERENCES RS_units (id),
    qtty          REAL,
    qtty_plan     REAL,
    sent          INTEGER,
    last_updated  DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_plan       TEXT     DEFAULT True,
    id_cell       TEXT     REFERENCES RS_cells (id), 
    table_type    TEXT     NOT NULL
                           DEFAULT 'out',
    use_series         INTEGER (1) DEFAULT (0)
    )
    ''')

    Rs.append('''
        CREATE TABLE IF NOT EXISTS Error_log (
        log       TEXT     NOT NULL
                           DEFAULT (''),
        timestamp DATETIME DEFAULT (CURRENT_TIMESTAMP)) 
    ''')

    Rs.append('''
    CREATE INDEX  IF NOT EXISTS cell_name ON RS_cells (
    name
    )
    ''')

    Rs.append('''
    CREATE INDEX  IF NOT EXISTS cell_barcode ON RS_cells (
    barcode
    )
    ''')

    Rs.append('''
    CREATE TABLE IF NOT EXISTS RS_docs_series (
    id              INTEGER  NOT NULL
                             PRIMARY KEY AUTOINCREMENT,
    id_doc          TEXT     NOT NULL
                             REFERENCES RS_docs (id_doc),
    id_good         TEXT     NOT NULL
                             REFERENCES RS_goods (id),
    id_properties   TEXT     REFERENCES RS_properties (id),
    id_series       TEXT     REFERENCES RS_series (id),
    id_warehouse    TEXT     REFERENCES RS_warehouses (id),
    qtty            REAL,
    name            TEXT     NOT NULL,
    best_before     DATETIME,
    number          TEXT     NOT NULL,
    production_date DATETIME,
    cell            TEXT     REFERENCES RS_cells (id) ON DELETE NO ACTION
                                                      ON UPDATE NO ACTION
    )''')



# RS_constants + RS_classifier_units + RS_types_goods
#     Rs = + RS_goods + RS_properties\
#          + RS_series + RS_units + RS_barcodes + RS_marking_codes + RS_docs + RS_docs_barcodes\
#          + RS_docs_table + RS_price_types + RS_prices + RS_countragents + RS_warehouses

    return Rs
#print(database_shema())
    #
    # Rs.append(RS_constants)
    # Rs.append(RS_classifier_units)
    # Rs.append(RS_types_goods)
    #
    # Rs.append(RS_goods)
    # Rs.append(RS_properties)
    # Rs.append(RS_series)
    # Rs.append(RS_units)
    #
    # Rs.append(RS_barcodes)
    # Rs.append(RS_marking_codes)
    #
    # Rs.append(RS_docs)
    # Rs.append(RS_docs_barcodes)
    # Rs.append(RS_docs_table)
    #
    # Rs.append(RS_price_types)
    # Rs.append(RS_prices)
    #
    # Rs.append(RS_countragents)
    # Rs.append(RS_warehouses)
    #ui_global.get_query_result(Rs)

