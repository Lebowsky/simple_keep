import json
import widgets

barcode_cards = {"customcards": {
    "options": {
        "search_enabled": True,
        "save_position": True
    },

    "layout": {
        "type": "LinearLayout",
        "orientation": "vertical",
        "height": "match_parent",
        "width": "match_parent",
        "weight": "1",
        "Padding": "0",
        "Elements": [
            {
                "type": "LinearLayout",
                "orientation": "horizontal",
                "height": "match_parent",
                "width": "match_parent",
                "weight": "1",
                "BackgroundColor": "#F0F8FF",
                "Padding": "0",
                "Elements": [

                    {
                        "type": "TextView",
                        "show_by_condition": "",
                        "Value": "@properties",
                        "NoRefresh": False,
                        "document_type": "",
                        "mask": "",
                        "Variable": "",
                        "TextSize": "15",
                        "TextColor": "",
                        "TextBold": True,
                        "TextItalic": False,
                        "BackgroundColor": "",
                        "width": "match_parent",
                        "height": "wrap_content",
                        "weight": 1
                    }
                ]
            },
            {
                "type": "LinearLayout",
                "orientation": "horizontal",
                "height": "match_parent",
                "width": "match_parent",
                "weight": "1",
                "BackgroundColor": "#F0F8FF",
                "Padding": "0",
                "Elements": [

                    {
                        "type": "TextView",
                        "show_by_condition": "",
                        "Value": "@unit",
                        "NoRefresh": False,
                        "document_type": "",
                        "mask": "",
                        "Variable": "",
                        "TextSize": "15",
                        "TextColor": "",
                        "TextBold": True,
                        "TextItalic": False,
                        "BackgroundColor": "",
                        "width": "match_parent",
                        "height": "wrap_content",
                        "weight": 1
                    },
                    {
                        "type": "TextView",
                        "show_by_condition": "",
                        "Value": "@barcode",
                        "NoRefresh": False,
                        "document_type": "",
                        "mask": "",
                        "Variable": "",
                        "TextSize": "15",
                        "TextColor": "",
                        "TextBold": True,
                        "TextItalic": False,
                        "BackgroundColor": "",
                        "width": "match_parent",
                        "height": "wrap_content",
                        "weight": 1
                    }
                ]
            },
            {
                "type": "LinearLayout",
                "orientation": "horizontal",
                "height": "match_parent",
                "width": "match_parent",
                "weight": "1",
                "BackgroundColor": "#F0F8FF",
                "Padding": "0",
                "Elements": [

                    {
                        "type": "TextView",
                        "show_by_condition": "",
                        "Value": "@series",
                        "NoRefresh": False,
                        "document_type": "",
                        "mask": "",
                        "Variable": "",
                        "TextSize": "15",
                        "TextColor": "",
                        "TextBold": True,
                        "TextItalic": False,
                        "BackgroundColor": "",
                        "width": "match_parent",
                        "height": "wrap_content",
                        "weight": 1
                    }
                ]
            }
        ]
        }
    }
}

def get_doc_card(settings_global, AddMenu=''):
    doc_list = {"customcards": {
        "options": {
            "search_enabled": True,
            "save_position": True
        },
        "layout": {
            "Value": "",
            "Variable": "",
            "type": "LinearLayout",
            "weight": "0",
            "height": "wrap_content",
            "width": "match_parent",
            "orientation": "vertical",
            "Elements": [
                {
                    "type": "LinearLayout",
                    "height": "wrap_content",
                    "width": "match_parent",
                    "weight": "0",
                    "Value": "",
                    "Variable": "",
                    "orientation": "horizontal",
                    "Elements": [
                        {
                            "type": "CheckBox",
                            "Value": "@completed",
                            "Variable": "CheckBox1",
                            "TextSize": "32",
                            "NoRefresh": False,
                            "document_type": "",
                            "mask": "",
                            "BackgroundColor": "#DB7093",
                            "width": "match_parent",
                            "height": "wrap_content",
                            "weight": 2
                        },
                        {
                            "type": "TextView",
                            "height": "wrap_content",
                            "width": "wrap_content",
                            "weight": "0",
                            "Value": "@type",
                            "Variable": "",
                            "TextSize": settings_global.get("TitleTextSize") #"18"
                        },
                        {
                            "type": "PopupMenuButton",
                            "show_by_condition": "",
                            "Value": f"Удалить;Подтвердить;Очистить данные пересчета{AddMenu}",  #;Сканировать штрихкоды потоком
                            "NoRefresh": False,
                            "document_type": "",
                            "mask": "",
                            "Variable": "menu_delete"

                        }

                    ]
                },
                {
                    "type": "LinearLayout",
                    "height": "wrap_content",
                    "width": "wrap_content",
                    "weight": "0",
                    "Value": "",
                    "Variable": "",
                    "orientation": "horizontal",
                    "Elements": [
                        {
                            "type": "TextView",
                            "height": "wrap_content",
                            "width": "wrap_content",
                            "weight": "0",
                            "Value": "@number",
                            "Variable": "",
                            "TextBold": True,
                            "TextSize": settings_global.get('CardTitleTextSize')  #"20"
                        }#,
                        # {
                        #     "type": "TextView",
                        #     "height": "wrap_content",
                        #     "width": "wrap_content",
                        #     "weight": "0",
                        #     "Value": "@data",
                        #     "Variable": "",
                        #     "TextSize": settings_global.get('CardDateTextSize')
                        # }
                    ]
                },
                {
                    "type": "LinearLayout",
                    "height": "wrap_content",
                    "width": "wrap_content",
                    "weight": "0",
                    "Value": "",
                    "Variable": "",
                    "orientation": "vertical",
                    "Elements": [
                        {
                            "type": "TextView",
                            "height": "wrap_content",
                            "width": "wrap_content",
                            "weight": "0",
                            "Value": "@countragent",
                            "Variable": "",
                            "TextSize": settings_global.get('CardDateTextSize')
                        },
                        {
                            "type": "TextView",
                            "height": "wrap_content",
                            "width": "wrap_content",
                            "weight": "0",
                            "Value": "@warehouse",
                            "Variable": "",
                            "TextSize": settings_global.get('CardDateTextSize')
                        }
                    ]
                }
            ]
        }
    }}

    return doc_list


def get_doc_card_new(settings_global, table_data):
    doc_list = widgets.CustomCards(
        widgets.LinearLayout(
            widgets.LinearLayout(
                widgets.TextView(
                    weight=8,
                    width='match_parent',
                    Value='@type',
                    gravity_horizontal='right',
                    TextSize=settings_global.get("TitleTextSize"),
                ),
                widgets.PopupMenuButton(
                    weight=2,
                    Value='Удалить',
                    Variable="menu_delete"
                ),
                orientation='horizontal',
                width='match_parent'
            ),
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@number',
                    TextBold=True,
                    TextSize=settings_global.get('CardTitleTextSize')
                )
            ),
            widgets.LinearLayout(
                widgets.TextView(
                    Value='@countragent',
                    TextSize=settings_global.get('CardDateTextSize')
                ),
                widgets.TextView(
                    Value='@warehouse',
                    TextSize=settings_global.get('CardDateTextSize')
                )
            ),
            width="match_parent"
        ),
        options=widgets.Options().options,
        cardsdata=table_data
    )

    return doc_list.to_json()


def get_doc_query(arg=''):
    query_text = """
    SELECT RS_docs.id_doc,
    RS_docs.doc_type,
    RS_docs.doc_n,
    RS_docs.doc_date,
    RS_docs.id_countragents,
    RS_docs.id_warehouse,
    ifnull(RS_countragents.full_name,'') as RS_countragent,
    ifnull(RS_warehouses.name,'') as RS_warehouse,
    RS_docs.verified,
    RS_docs.sent,
    RS_docs.add_mark_selection

     FROM RS_docs
     LEFT JOIN RS_countragents as RS_countragents
     ON RS_countragents.id = RS_docs.id_countragents
     LEFT JOIN RS_warehouses as RS_warehouses
     ON RS_warehouses.id=RS_docs.id_warehouse
     """
    if not (arg == '' or arg == 'Все'):
        query_text = query_text + '''
        Where RS_docs.doc_type=?'''

    query_text = query_text + """
    ORDER
    BY
    RS_docs.doc_date"""
    return query_text

def get_adr_doc_query(arg=''):
    query_text = """
    SELECT RS_adr_docs.id_doc,
    RS_adr_docs.doc_type,
    RS_adr_docs.doc_n,
    RS_adr_docs.doc_date,
    RS_adr_docs.id_warehouse,
    ifnull(RS_warehouses.name,'') as RS_warehouse,
    RS_adr_docs.verified,
    RS_adr_docs.sent,
    RS_adr_docs.add_mark_selection

     FROM RS_adr_docs

     LEFT JOIN RS_warehouses as RS_warehouses
     ON RS_warehouses.id=RS_adr_docs.id_warehouse
     """
    if not (arg == '' or arg == 'Все'):
        query_text = query_text + '''
        Where RS_adr_docs.doc_type=?'''

    query_text = query_text + """
    ORDER
    BY
    RS_adr_docs.doc_date"""
    return query_text

def get_doc_type_query():
    ls = 'SELECT DISTINCT doc_type from RS_docs'
    return ls


# -----------------------------------------Товары

def get_goods_query():
    query_text = """
    SELECT RS_goods.id,
    RS_goods.code,
    RS_goods.art,
    RS_goods.name,
    RS_goods.type_good,
    RS_types_goods.name AS types_goods,
    RS_goods.unit,
    RS_units.name
    FROM RS_goods
    LEFT JOIN RS_types_goods
    ON RS_types_goods.id = RS_goods.type_good
    LEFT JOIN RS_units
    ON RS_units.id_owner = RS_goods.id"""
    return query_text


def get_price_card(settings_global):
    txt = {"customcards": {
        "options": {
            "search_enabled": False,
            "save_position": True
        },
        "type": "LinearLayout",
        "weight": "0",
        "height": "wrap_content",
        "width": "match_parent",
        "orientation": "vertical",
        "Elements": [
            {
                "type": "LinearLayout",
                "height": "wrap_content",
                "width": "match_parent",
                "weight": "0",
                "Value": "",
                "Variable": "",
                "orientation": "vertical",
                "Elements": [
                    {
                        "type": "TextView",
                        "height": "wrap_content",
                        "width": "wrap_content",
                        "weight": "2",
                        "Value": "@price_type",
                        "Variable": "",
                        "TextSize": settings_global.get('CardTitleTextSize')
                    },
                    {
                        "type": "TextView",
                        "height": "wrap_content",
                        "width": "wrap_content",
                        "weight": "1",
                        "Value": "@price",
                        "Variable": "",
                        "TextSize": settings_global.get('CardTextSize')
                    }
                ]
            }
        ]
    }
    }
    return txt


def get_doc_details_query(isAdr = False, curCell = False):
    if isAdr:
        query_text = '''
            SELECT
            RS_adr_docs_table.id,
            RS_adr_docs_table.id_doc,
            RS_adr_docs_table.id_good,
            ifnull(RS_goods.name, :NullValue) as good_name,
            ifnull(RS_goods.code, :EmptyString) as code,
            ifnull(RS_goods.art, :EmptyString) as art,
            ifnull(RS_adr_docs_table.id_properties, :EmptyString) as id_properties,
            ifnull(RS_properties.name, :EmptyString) as properties_name,
            ifnull(RS_adr_docs_table.id_series, :EmptyString) as id_series,
            ifnull(RS_series.name, :EmptyString) as series_name,
            ifnull(RS_adr_docs_table.id_unit, :EmptyString) as id_unit,
            ifnull(RS_units.name, :EmptyString) as units_name,
            RS_adr_docs_table.qtty as qtty,
            RS_adr_docs_table.qtty_plan as qtty_plan,
            RS_adr_docs_table.qtty_plan - RS_adr_docs_table.qtty as IsDone,
            ifnull(RS_adr_docs_table.id_cell, :EmptyString) as id_cell,
            ifnull(RS_cells.name, :NullValue) as cell_name
            
            
            FROM RS_adr_docs_table 

            LEFT JOIN RS_goods 
            ON RS_goods.id=RS_adr_docs_table.id_good
            LEFT JOIN RS_properties
            ON RS_properties.id = RS_adr_docs_table.id_properties
            LEFT JOIN RS_series
            ON RS_series.id = RS_adr_docs_table.id_series
            LEFT JOIN RS_units
            ON RS_units.id=RS_adr_docs_table.id_unit
            LEFT JOIN RS_cells
            ON RS_cells.id=RS_adr_docs_table.id_cell

            WHERE id_doc = :id_doc and table_type = :table_type
            
            '''

        if curCell:
            query_text = query_text + '''
             and (id_cell=:current_cell OR id_cell="" OR id_cell is Null)
            '''

        query_text = query_text + ' ORDER BY RS_cells.name, RS_adr_docs_table.last_updated DESC'

    else:
        query_text = """
        SELECT
        RS_docs_table.id,
        RS_docs_table.id_doc,
        RS_docs_table.id_good,
        RS_goods.name as good_name,
        RS_goods.code,
        RS_goods.art,
        RS_docs_table.id_properties,
        RS_properties.name as properties_name,
        RS_docs_table.id_series,
        RS_series.name as series_name,
        RS_docs_table.id_unit,
        RS_units.name as units_name,
        RS_docs_table.qtty,
        RS_docs_table.qtty_plan,
        RS_docs_table.price,
        RS_price_types.name as price_name,
        RS_docs_table.qtty_plan - RS_docs_table.qtty as IsDone
        FROM RS_docs_table 
    
        LEFT JOIN RS_goods 
        ON RS_goods.id=RS_docs_table.id_good
        LEFT JOIN RS_properties
        ON RS_properties.id = RS_docs_table.id_properties
        LEFT JOIN RS_series
        ON RS_series.id = RS_docs_table.id_series
        LEFT JOIN RS_units
        ON RS_units.id=RS_docs_table.id_unit
        LEFT JOIN RS_price_types
        ON RS_price_types.id = RS_docs_table.id_price
        WHERE id_doc = $arg1
        ORDER BY RS_docs_table.last_updated DESC 
        """

    return query_text


def get_doc_detail_cards(use_series, use_properties, settings_global, isAdr = False):
    cellMenuCommand = ';Изменить ячейку' if isAdr else ''
    list = {
        "customcards": {
            "options": {
                "search_enabled": True,
                "save_position": True
            },
            "layout": {
                "type": "LinearLayout",
                "orientation": "vertical",
                "height": "match_parent",
                "width": "match_parent",
                "weight": "0",
                "Elements": [
                    {
                        "type": "LinearLayout",
                        "orientation": "horizontal",
                        "height": "match_parent",
                        "width": "match_parent",
                        "weight": "0",
                        "Elements": [

                            {
                                "type": "LinearLayout",
                                "orientation": "vertical",
                                "height": "wrap_content",
                                "width": "match_parent",
                                "weight": "1",
                                "Elements": [
                                    {
                                        "type": "LinearLayout",
                                        "orientation": "horizontal",
                                        "height": "match_parent",
                                        "width": "match_parent",
                                        "weight": "0",
                                        "Elements": [
                                            {
                                                "type": "TextView",
                                                "TextBold": True,
                                                "show_by_condition": "",
                                                "Value": "@good_name",
                                                "TextSize": settings_global.get('GoodsCardTitleTextSize'),
                                                "NoRefresh": False,
                                                "document_type": "",
                                                "mask": "",
                                                "weight": "1",
                                                "Variable": ""
                                            },
                                            {
                                                "type": "TextView",
                                                "show_by_condition": "",
                                                "Value": "@picture",
                                                "TextSize": "25",
                                                "TextColor": "#DB7093",
                                                "BackgroundColor": "#FFFFFF",
                                                "height": "25",
                                                "NoRefresh": False,
                                                "document_type": "",

                                                "weight": "1",
                                                "mask": ""
                                            },
                                            {
                                                "type": "PopupMenuButton",
                                                "show_by_condition": "",
                                                "Value": f"Удалить строку{cellMenuCommand}",
                                                "NoRefresh": False,
                                                "document_type": "",
                                                "mask": "",
                                                "Variable": "menu_good_string"

                                            }
                                        ]
                                    },

                                    {
                                        "type": "TextView",
                                        "show_by_condition": "",
                                        "Value": "@code_art",
                                        "TextSize": settings_global.get('goodsTextSize'),
                                        "NoRefresh": False,
                                        "document_type": "",
                                        "mask": "",
                                        "Variable": ""
                                    },

                                    {
                                        "type": "TextView",
                                        "show_by_condition": "",
                                        "Value": "@unit_name",
                                        "TextSize": settings_global.get('goodsTextSize'),
                                        "NoRefresh": False,
                                        "document_type": "",
                                        "mask": "",
                                        "Variable": ""
                                    },
                                    {
                                        "type": "LinearLayout",
                                        "orientation": "gorizontal",
                                        "height": "match_parent",
                                        "width": "match_parent",
                                        "weight": "1",
                                        "Elements": [
                                            {
                                                "type": "LinearLayout",
                                                "orientation": "vertical",
                                                "height": "wrap_content",
                                                "width": "match_parent",
                                                "weight": "1",
                                                "Elements": [
                                                    {
                                                        "type": "TextView",
                                                        "show_by_condition": "",
                                                        "Value": "План",
                                                        "TextSize": settings_global.get('goodsTextSize'),
                                                        "NoRefresh": False,
                                                        "document_type": "",
                                                        "mask": "",
                                                        "Variable": ""
                                                    },
                                                    {
                                                        "type": "TextView",
                                                        "show_by_condition": "",
                                                        "Value": "@qtty_plan",
                                                        "NoRefresh": False,
                                                        "document_type": "",
                                                        "TextSize": settings_global.get('goodsTextSize'),
                                                        "mask": "",
                                                        "Variable": ""
                                                    }
                                                ]
                                            },
                                            {
                                                "type": "LinearLayout",
                                                "orientation": "vertical",
                                                "height": "wrap_content",
                                                "width": "match_parent",
                                                "weight": "1",
                                                "Elements": [
                                                    {
                                                        "type": "TextView",
                                                        "show_by_condition": "",
                                                        "Value": "Факт",
                                                        "TextSize": settings_global.get('goodsTextSize'),
                                                        "NoRefresh": False,
                                                        "document_type": "",
                                                        "mask": "",
                                                        "Variable": ""
                                                    },
                                                    {
                                                        "type": "TextView",
                                                        "show_by_condition": "",
                                                        "Value": "@qtty",
                                                        "NoRefresh": False,
                                                        "document_type": "",
                                                        "TextSize": settings_global.get('goodsTextSize'),
                                                        "mask": "",
                                                        "Variable": ""
                                                    }
                                                ]
                                            },
                                            {
                                                "type": "LinearLayout",
                                                "orientation": "vertical",
                                                "height": "wrap_content",
                                                "width": "match_parent",
                                                "weight": "1",
                                                "Elements": [
                                                    {
                                                        "type": "TextView",
                                                        "show_by_condition": "",
                                                        "Value": "Цена",
                                                        "TextSize": settings_global.get('goodsTextSize'),
                                                        "NoRefresh": False,
                                                        "document_type": "",
                                                        "mask": "",
                                                        "Variable": ""
                                                    },
                                                    {
                                                        "type": "TextView",
                                                        "show_by_condition": "",
                                                        "Value": "@price",
                                                        "NoRefresh": False,
                                                        "document_type": "",
                                                        "TextSize": settings_global.get('goodsTextSize'),
                                                        "mask": "",
                                                        "Variable": ""
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    }

    if use_series == 'true' or use_series == '1':
        list['customcards']['layout']['Elements'][0]['Elements'][0]['Elements'].insert(1, {'type': 'TextView',
                                                                                           "TextSize": settings_global.get('SeriesPropertiesTextSize'), #16
                                                                                           'show_by_condition': '',
                                                                                           'Value': '@series_name',
                                                                                           'NoRefresh': False,
                                                                                           'document_type': '',
                                                                                           'mask': '', 'Variable': ''})
    if use_properties == 'true' or use_properties == '1':
        list['customcards']['layout']['Elements'][0]['Elements'][0]['Elements'].insert(1, {'type': 'TextView',
                                                                                           "TextSize": settings_global.get('SeriesPropertiesTextSize'), #'16',
                                                                                           'show_by_condition': '',
                                                                                           'Value': '@properties_name',
                                                                                           'NoRefresh': False,
                                                                                           'document_type': '',
                                                                                           'mask': '', 'Variable': ''})
    if isAdr:
        list['customcards']['layout']['Elements'][0]['Elements'][0]['Elements'].insert(1, {'type': 'TextView',
                                                                                           "TextSize": settings_global.get(
                                                                                               'SeriesPropertiesTextSize'),
                                                                                           # '16',
                                                                                           'show_by_condition': '',
                                                                                           'Value': '@cell_name',
                                                                                           'NoRefresh': False,
                                                                                           'document_type': '',
                                                                                           'mask': '', 'Variable': ''})

        pass

    return list


def get_doc_detail_cards_new(settings_global, cards_data: list, add_labels: list = None):
    goods_text_size = settings_global.get('goodsTextSize')
    header = widgets.LinearLayout(
        orientation='horizontal',
        height='match_parent',
        width='match_parent',
    )

    # series_name, properties_name, cell_name
    add_labels = add_labels or []
    for label in add_labels:
        header.append(
            widgets.TextView(Value=f'@{label}', TextSize=settings_global.get('SeriesPropertiesTextSize')),
        )

    header.append(
        widgets.TextView(
            Value='@good_name',
            TextBold=True,
            TextSize=settings_global.get('GoodsCardTitleTextSize'),
            weight='1'
        ),
        widgets.TextView(
            Value='@picture',
            TextSize='25',
            TextColor='#DB7093',
            BackgroundColor="#FFFFFF",
            weight=1,
            height=25,
        ),
    )

    code_art = widgets.TextView(Value='@code_art', TextSize=settings_global.get('goodsTextSize'))
    unit_name = widgets.TextView(Value='@unit_name', TextSize=settings_global.get('goodsTextSize'))
    footer = widgets.LinearLayout(
        widgets.LinearLayout(
            widgets.TextView(Value='План', TextSize=goods_text_size),
            widgets.TextView(Value='@qtty_plan', TextSize=goods_text_size),
            width='match_parent',
            weight=1,
        ),
        widgets.LinearLayout(
            widgets.TextView(Value='Факт', TextSize=goods_text_size),
            widgets.TextView(Value='@qtty', TextSize=goods_text_size),
            width='match_parent',
            weight=1,
        ),
        widgets.LinearLayout(
            widgets.TextView(Value='Цена', TextSize=goods_text_size),
            widgets.TextView(Value='@price', TextSize=goods_text_size),
            width='match_parent',
            weight=1,
        ),
        height='match_parent',
        width='match_parent',
        orientation='horizontal',
        weight=1,
    )

    detail_cards = widgets.CustomCards(
        widgets.LinearLayout(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    header,
                    code_art,
                    unit_name,
                    footer,
                    width='match_parent',
                    weight='1'
                ),
                height='match_parent',
                width='match_parent',
                orientation='horizontal'
            ),
            height='match_parent',
            width='match_parent'
        ),
        options=widgets.Options().options,
        cardsdata=cards_data
    )

    return detail_cards.to_json()


def get_doc_barc_flow_query():
    return '''
    Select * from RS_barc_flow WHere id_doc =?
    '''

def doc_barc_flow_card(settings_global):
    list = {
        "customcards": {
            "options": {
                "search_enabled": True,
                "save_position": True
            },
            "layout": {
                "type": "LinearLayout",
                "orientation": "vertical",
                "height": "match_parent",
                "width": "match_parent",
                "weight": "0",
                "Elements": [
                                {
                                    "type": "LinearLayout",
                                    "orientation": "horizontal",
                                    "height": "match_parent",
                                    "width": "match_parent",
                                    "weight": "0",
                                    "Elements": [
                                        {
                                            "type": "TextView",
                                            "TextBold": True,
                                            "show_by_condition": "",
                                            "Value": "@barcode",
                                            "TextSize": settings_global.get('GoodsCardTitleTextSize'),
                                            "NoRefresh": False,
                                            "document_type": "",
                                            "mask": "",
                                            "weight": "1",
                                            "Variable": ""
                                        }
                                    ]
                                }
                            ]
            }
        }
    }


    return list

def get_price_query():
    txt = """
    SELECT *,
    RS_price_types.name
     from RS_prices 
     LEFT JOIN RS_price_types ON RS_price_types.id=RS_prices.id_price_types
     where id_goods=?"""
    return txt


# Современное поле ввода, не используется
def get_num_field_descr(qtty):
    json_descr = {
        "hint": 'количество',
        "default_text": qtty,
        'inputType ': 'TYPE_CLASS_NUMBER'
    }
    return json_descr


# def get_barcode_query():
#     query_text = 'SELECT * FROM RS_docs_barcodes Where RS_docs_barcodes.id_doc = ?'
#     return query_text


# Запрос находит все записи таблицы документа RS_docs_barcodes по полному совпадению штрихкода или только по GTIN
def get_query_mark_find_in_doc():
    query = '''
    SELECT 
    id,
    id_doc,
    IFNULL(GTIN, '0') AS GTIN,
    IFNULL(Series, '0') AS Series,
    IFNULL(id_good, '') AS id_good,
    IFNULL(id_property, '') AS id_property ,
    IFNULL(id_series, '') AS id_series,
    IFNULL(id_unit, '')  AS id_unit,
    is_plan,
    approved

    FROM RS_docs_barcodes

    WHERE id_doc = :id_doc  and GTIN = :GTIN And Series = :Series'''

    #
    #
    #     '''
    # SELECT * FROM (
    #
    # SELECT
    # RS_docs_barcodes.id,
    # RS_docs_barcodes.id_doc,
    #
    # RS_docs_barcodes.id_barcode,
    #
    # IFNULL(RS_marking_codes.mark_code, '0') AS mark_code,
    # IFNULL(RS_marking_codes.id_good, '') AS id_good,
    # IFNULL(RS_marking_codes.id_property, '') AS id_property ,
    # IFNULL(RS_marking_codes.id_series, '') AS id_series,
    # IFNULL(RS_marking_codes.id_unit, '')  AS id_unit,
    #
    # RS_docs_barcodes.is_plan,
    # RS_docs_barcodes.approved
    #
    # FROM RS_docs_barcodes
    #
    #     LEFT JOIN RS_marking_codes As RS_marking_codes
    #     ON RS_marking_codes.id = RS_docs_barcodes.id_barcode
    #
    # WHERE id_doc = :id_doc  and RS_marking_codes.mark_code = :set_barcode)
    # '''
    #
    # SELECT * FROM (
    #     SELECT
    #     'on_GTIN' as TypeOfUnion,
    #     RS_docs_barcodes.id,
    #     RS_docs_barcodes.id_doc,
    #     RS_docs_barcodes.barcode,
    #     RS_docs_barcodes.id_barcode,
    #     RS_barcodes.GTIN,
    #     RS_barcodes.id_good,
    #     RS_barcodes.id_property,
    #     RS_barcodes.id_series,
    #     RS_barcodes.id_unit,
    #     RS_docs_barcodes.is_plan,
    #     RS_docs_barcodes.approved
    #     FROM RS_docs_barcodes
    #         LEFT JOIN (Select RS_barcodes.barcode as GTIN,
    #         RS_barcodes.id_good,
    #         RS_barcodes.id_property,
    #         RS_barcodes.id_series,
    #         RS_barcodes.id_unit FROM RS_barcodes
    #         WHERE RS_barcodes.barcode=:gtin LIMIT 1) AS RS_barcodes
    #         ON TRUE
    #         LEFT JOIN RS_barcodes as FullBarcode
    #         ON FullBarcode.barcode = RS_docs_barcodes.barcode
    #
    #     WHERE id_doc = :id_doc  and RS_docs_barcodes.barcode Like '%'+:gtin + '%'
    #
    #     UNION ALL
    #
    #     SELECT
    #     'FullMatch',
    #     RS_docs_barcodes.id,
    #     RS_docs_barcodes.id_doc,
    #     RS_docs_barcodes.barcode,
    #     RS_docs_barcodes.id_barcode,
    #     IFNULL(RS_barcodes.barcode,RS_barcodes_inaccurate.GTIN),
    #     IFNULL(RS_barcodes.id_good,RS_barcodes_inaccurate.id_good),
    #     IFNULL(RS_barcodes.id_property,RS_barcodes_inaccurate.id_property),
    #     IFNULL(RS_barcodes.id_series,RS_barcodes_inaccurate.id_series),
    #     IFNULL(RS_barcodes.id_unit,RS_barcodes_inaccurate.id_unit),
    #     RS_docs_barcodes.is_plan,
    #     RS_docs_barcodes.approved
    #     FROM RS_docs_barcodes
    #         LEFT JOIN RS_barcodes
    #         ON RS_barcodes.barcode = RS_docs_barcodes.barcode
    #         LEFT JOIN (Select RS_barcodes.barcode as GTIN,
    #         RS_barcodes.id_good,
    #         RS_barcodes.id_property,
    #         RS_barcodes.id_series,
    #         RS_barcodes.id_unit FROM RS_barcodes
    #         WHERE RS_barcodes.barcode Like '%'+:gtin + '%' LIMIT 1) AS RS_barcodes_inaccurate
    #         ON TRUE
    #         LEFT JOIN RS_barcodes as FullBarcode
    #         ON FullBarcode.barcode = RS_docs_barcodes.barcode
    #
    #     WHERE id_doc = :id_doc  and RS_docs_barcodes.barcode = :set_barcode)
    #
    # ORDER  BY TypeOfUnion
    # '''
    return query


def get_barcode_card(settings_global):
    ls = {"customcards": {
        "options": {
            "search_enabled": False,
            "save_position": True
        },
        "layout": {
            "type": "LinearLayout",
            "orientation": "vertical",
            "height": "match_parent",
            "width": "match_parent",
            "weight": "0",
            "Elements": [
                {
                    "type": "LinearLayout",
                    "orientation": "horizontal",
                    "height": "match_parent",
                    "width": "match_parent",
                    "weight": "0",
                    "Elements": [
                        {"type": "TextView",
                         "height": "wrap_content",
                         "width": "match_parent",
                         "weight": "1",
                         "Value": "@barcode",
                         "TextSize": settings_global.get('goodsTextSize'),
                         "Variable": ""
                         },
                        {
                            "type": "TextView",
                            "show_by_condition": "",
                            "Value": "@picture",
                            "TextColor": "#DB7093",
                            "BackgroundColor": "#FFFFFF",
                            "Variable": "btn_tst1",
                            "NoRefresh": False,
                            "document_type": "",
                            "cardCornerRadius": "15dp",
                            "weight": "1",
                            "mask": ""
                        }]}

            ]
        }}
    }
    return ls


def get_doc_barcode_query():
    ls = '''
    SELECT
    "(01)" || GTIN || "(21)" || Series as mark_code,
    approved
    FROM RS_docs_barcodes
    Where
    id_doc = :id_doc AND
    id_good = :id_good AND
    id_property = :id_property AND
    id_series = :id_series 
    --AND  id_unit = :id_unit
 '''
    return ls


def get_doc_barcode_query_no_RS_markcodes():
    return '''
    SELECT 
    id_barcode,
    RS_marking_codes.mark_code as mark_code,
    approved
    FROM RS_docs_barcodes

    JOIN RS_marking_codes 
    ON RS_marking_codes.id = RS_docs_barcodes.id_barcode AND
    RS_marking_codes.id_good = :id_good AND
    RS_marking_codes.id_property = :id_property AND
    RS_marking_codes.id_series = :id_series AND
    RS_marking_codes.id_unit = :id_unit 

     WHERE RS_docs_barcodes.id_doc = :id_doc '''


def get_markcode_query():
    return '''
    SELECT 
    RS_docs_barcodes.id as CurStr,
    RS_docs_barcodes.GTIN,
    RS_docs_barcodes.Series,
    RS_docs_barcodes.approved,
    RS_docs_barcodes.id_good,
    RS_docs_barcodes.id_property as id_property,
    RS_docs_barcodes.id_series,
    RS_docs_barcodes.id_unit,
    RS_goods.name as good_name,
    RS_properties.name as properties,
    RS_series.name as series,
    RS_units.name as unit,
    RS_goods.code AS good_code,
    RS_docs_barcodes.is_plan

 FROM RS_docs_barcodes 

 LEFT JOIN RS_goods 
    ON RS_goods.id=RS_docs_barcodes.id_good
    LEFT JOIN RS_properties
    ON RS_properties.id = RS_docs_barcodes.id_property
    LEFT JOIN RS_series
    ON RS_series.id = RS_docs_barcodes.id_series
    LEFT JOIN RS_units
    ON RS_units.id=RS_docs_barcodes.id_unit

     WHERE RS_docs_barcodes.id_doc = :id_doc AND GTIN = :GTIN And Series = :Series'''


#     '''
#     SELECT
#     Temp_query.CurStr as CurStr,
#     Temp_query.id_barcode,
#     Temp_query.mark_code,
#     Temp_query.approved,
#     Temp_query.id_good,
#     Temp_query.id_properties as id_property,
#     Temp_query.id_series,
#     Temp_query.id_unit,
#     RS_goods.name as good_name,
#     RS_properties.name as properties,
#     RS_series.name as series,
#     RS_units.name as unit,
#     RS_goods.code AS good_code,
#     Temp_query.is_plan
#
#
#  FROM (
# SELECT
#     RS_docs_barcodes.id as CurStr,
#     id_barcode,
#     RS_marking_codes.mark_code,
#     approved,
#     RS_marking_codes.id_good,
#     RS_marking_codes.id_property as id_properties,
#     RS_marking_codes.id_series,
#     RS_marking_codes.id_unit,
#     RS_docs_barcodes.is_plan
#
#     FROM RS_docs_barcodes
#
#     JOIN RS_marking_codes
#     ON RS_marking_codes.id = RS_docs_barcodes.id_barcode
#
#      WHERE RS_docs_barcodes.id_doc = :id_doc AND id_barcode = :id_barcode) AS Temp_query
#
#  LEFT JOIN RS_goods
#     ON RS_goods.id=Temp_query.id_good
#     LEFT JOIN RS_properties
#     ON RS_properties.id = Temp_query.id_properties
#     LEFT JOIN RS_series
#     ON RS_series.id = Temp_query.id_series
#     LEFT JOIN RS_units
#     ON RS_units.id=Temp_query.id_unit
#     '''


def get_barcode_query() -> str:
    return '''
    With barc as (
SELECT 
barcode,
id_good,
RS_goods.type_good,
id_property,
id_series,
id_unit,
ratio
 FROM RS_barcodes 
 Left Join RS_goods
 ON RS_barcodes.id_good = RS_goods.id
WHERE barcode = ?)

Select * From barc
Left JOIN RS_types_goods
ON RS_types_goods.id = barc.type_good

'''


def get_mark_qtty_conformity():
    return '''
    SELECT ifnull(doc_table.qtty_plan,0) - ifnull(tmp.qtty_of_mark,0)  FROM 

    (SELECT qtty_plan
    FROM RS_docs_table
    WHERE 
    id_doc = :idDoc 
    AND id_good = :id_good
    AND id_properties = :id_properties
    AND id_series = :id_series
    ) As doc_table  --AND id_unit = :id_unit
       LEFT JOIN (SELECT Count(id_barcode) As qtty_of_mark
        FROM RS_docs_barcodes 
        WHERE id_doc=:idDoc 
        AND id_barcode LIke :barcode AND approved = :approved) As tmp
        ON TRUE
    '''


def get_plan_good_from_doc():
    return '''

    SELECT ifnull(qtty_plan,0) as qtty_plan,
    ifnull(qtty,0) as qtty, id_good, use_series, id
    FROM RS_docs_table
    WHERE 
    id_doc = :idDoc 
    AND id_good = :id_good
    AND id_properties = :id_properties
    AND id_series = :id_series
    --AND id_unit = :id_unit
    '''

def get_qtty_add_mark_text():
    return '''
    SELECT RS_docs.add_mark_selection As Marked,
    Tmp.Qtty 
    from RS_docs 
    Left Join (Select Sum(RS_docs_table.qtty_plan) as Qtty From RS_docs_table Where RS_docs_table.id_doc= :id_doc) As Tmp
    ON True
    WHERE id_doc = :id_doc'''


def get_qtty_string_count_query():
    return '''
    SELECT distinct count(id) as col_str,
    sum(ifnull(qtty_plan,0)) as qtty_plan
    from RS_docs_table Where id_doc = :id_doc'''


def get_have_mark_codes_query():  # Запрос возвращает количество кодов маркировки "План" (т.е. загруженных из учетной
    # системы)
    return '''
    SELECT distinct count(id) as col_str
    from RS_docs_barcodes Where id_doc = :id_doc AND is_plan = :is_plan'''


def get_docs_stat_query():
    return '''
   with tmp as (
    Select 
    doc_type,
    RS_docs.id_doc,
    1 as doc_Count,
    ifnull(RS_docs.sent,0) as sent,
    ifnull(verified,0) as verified, 
    CASE
    WHEN ifnull(verified,0)=0 THEN count(RS_docs_table.id)
    else 0 END as count_verified,
    CASE
    WHEN ifnull(verified,0)=1 THEN count(RS_docs_table.id)
    else 0 END as count_unverified,
    CASE
        WHEN ifnull(verified,0)=0 THEN sum(RS_docs_table.qtty_plan)
    else 0 END as qtty_plan_verified,
    CASE
        WHEN ifnull(verified,0)=1 THEN sum(RS_docs_table.qtty_plan)
    else 0 END as qtty_plan_unverified
     from RS_docs
    Left Join RS_docs_table 
    ON RS_docs_table.id_doc = RS_docs.id_doc
    Group by RS_docs.id_doc
    )
   Select doc_type as docType, 
   count(id_doc),
   sum(doc_Count) as count, 
   sum(sent) as sent, 
   sum(verified) as verified,
   sum(count_verified) as count_verified,
   sum(count_unverified) as count_unverified,
   sum(qtty_plan_verified) as qtty_plan_verified,
   sum(qtty_plan_unverified) as qtty_plan_unverified
    from tmp
    group by doc_type
   '''


def get_doc_tiles(settings_global):

    small_tile = {
        "type": "LinearLayout",
        "orientation": "vertical",
        "height": "wrap_content",
        "width": "match_parent",
        "autoSizeTextType" : "uniform",
        "weight": "0",
        "Elements": [
            {
                "type": "TextView",
                "show_by_condition": "",
                "Value": "@docName",
                "NoRefresh": False,
                "document_type": "",
                "mask": "",
                "Variable": "",
                "TextSize": settings_global.get('titleDocTypeCardTextSize'), # "25",
                "TextColor": "#000000",
                "TextBold": False,
                "TextItalic": False,
                "BackgroundColor": "",
                "width": "match_parent",
                "height": "wrap_content",
                "weight": 0,
                "gravity_horizontal": "center"
            },
            {
                "type": "LinearLayout",
                "orientation": "horizontal",
                "height": "wrap_content",
                "width": "match_parent",
                "weight": "1",
                "Elements": [
                    {
                        "type": "TextView",
                        "show_by_condition": "",
                        "Value": "@QttyOfDocs",
                        "NoRefresh": False,
                        "document_type": "",
                        "mask": "",
                        "Variable": "",
                        "TextSize": settings_global.get('DocTypeCardTextSize'),
                        "TextColor": "#333333",
                        "TextBold": False,
                        "TextItalic": False,
                        "BackgroundColor": "FFCC99",
                        "width": "wrap_content",
                        "height": "wrap_content",
                        "weight": 0
                    }
                ]
            },
            {
                "type": "LinearLayout",
                "orientation": "horizontal",
                "height": "wrap_content",
                "width": "match_parent",
                "weight": "1",
                "Elements": [
                    {
                        "type": "TextView",
                        "show_by_condition": "",
                        "Value": "Строк: ",
                        "NoRefresh": False,
                        "document_type": "",
                        "mask": "",
                        "Variable": "",
                        "TextSize": settings_global.get('DocTypeCardTextSize'), #"15",
                        "TextColor": "#333333",
                        "TextBold": False,
                        "TextItalic": False,
                        "BackgroundColor": "FFCC99",
                        "width": "wrap_content",
                        "height": "wrap_content",
                        "weight": 0
                    },
                    {
                        "type": "TextView",
                        "show_by_condition": "",
                        "Value": "@count_verified",
                        "NoRefresh": False,
                        "document_type": "",
                        "mask": "",
                        "Variable": "",
                        "TextSize": settings_global.get('DocTypeCardTextSize'),
                        "TextColor": "#333333",
                        "TextBold": False,
                        "TextItalic": False,
                        "BackgroundColor": "FFCC99",
                        "width": "wrap_content",
                        "height": "wrap_content",
                        "weight": 0
                    }
                ]
            },
            {
                "type": "LinearLayout",
                "orientation": "horizontal",
                "height": "wrap_content",
                "width": "match_parent",
                "weight": "1",
                "Elements": [
                    {
                        "type": "TextView",
                        "show_by_condition": "",
                        "Value": "Товаров: ",
                        "NoRefresh": False,
                        "document_type": "",
                        "mask": "",
                        "Variable": "",
                        "TextSize": settings_global.get('DocTypeCardTextSize'),
                        "TextColor": "#333333",
                        "TextBold": False,
                        "TextItalic": False,
                        "BackgroundColor": "FFCC99",
                        "width": "wrap_content",
                        "height": "wrap_content",
                        "weight": 0
                    },
                    {
                        "type": "TextView",
                        "show_by_condition": "",
                        "Value": "@qtty_plan_verified",
                        "NoRefresh": False,
                        "document_type": "",
                        "mask": "",
                        "Variable": "",
                        "TextSize": settings_global.get('DocTypeCardTextSize'),
                        "TextColor": "#333333",
                        "TextBold": False,
                        "TextItalic": False,
                        "BackgroundColor": "FFCC99",
                        "width": "wrap_content",
                        "height": "wrap_content",
                        "weight": 0
                    }
                ]
            }

        ]
    }

    return small_tile

class ModernField:
    def __init__(self, hint=None, default_text=None, password=False):  # counter=False, counter_max=None, input_type= 1 ,
        self.hint = hint
        self.default_text = default_text
        #self.counter = counter
        #self.counter_max = counter_max
        #self.input_type = input_type
        self.password = password

    def to_json(self):
        ret = {
            "hint": self.hint,
            "default_text": self.default_text}
        # "counter": self.counter,
        # "counter_max": self.counter_max,
        # "input_type": self.input_type,
        if self.password:
            ret["password"] = self.password

        return json.dumps(ret)


# http_settings = {'url':'192', 'user':'AMD', 'pass':'123'}
# print(ModernField(hint='url', default_text=http_settings['url'], password=False).to_json())
# print(ModernField(hint='user', default_text=http_settings['user'], password=False).to_json())
# print(ModernField(hint='pass', default_text=http_settings['pass'], password=True).to_json())