from ui_utils import HashMap
from db_services import DocService
import widgets


class Screen:
    def __init__(self, hash_map: HashMap):
        self.hash_map = hash_map


class DocsListScreen(Screen):
    def __init__(self, hash_map: HashMap,  rs_settings):
        super().__init__(hash_map)
        self.listener = self.hash_map['listener']
        self.event = self.hash_map['event']
        self.id_doc = self.hash_map['id_doc']
        self.rs_settings = rs_settings
        self.service = DocService(self.id_doc)

    def on_start(self):
        doc_types = self.service.get_doc_types()
        self.hash_map['doc_type_select'] = ';'.join(['Все'] + doc_types)

        doc_type = self.hash_map['selected_tile_key'] or self.hash_map['doc_type_click']

        if doc_type:
            doc_cards = self._get_doc_list_view(doc_type)
            self.hash_map['doc_type_click'] = doc_type
            self.hash_map['selected_tile_key'] = ''
        else:
            doc_cards = self._get_doc_list_view()

        self.hash_map['docCards'] = doc_cards

    def _get_doc_list_view(self, doc_type='') -> str:
        if doc_type and doc_type != 'Все':
            results = self.service.get_doc_view_data(doc_type)
        else:
            results = self.service.get_doc_view_data()

        table_data = []

        for record in results:
            table_data.append({
                'key': record['id_doc'],
                'type': record['doc_type'],
                'number': record['doc_n'],
                'data': record['doc_date'],
                'warehouse': record['RS_warehouse'],
                'countragent': record['RS_countragent'],
                'add_mark_selection': record['add_mark_selection']
            })

        return self._get_doc_cards_view(table_data)

    def on_input(self):
        pass

    def _get_doc_cards_view(self, table_data):
        title_text_size = self.rs_settings.get("TitleTextSize")
        card_title_text_size = self.rs_settings.get('CardTitleTextSize')
        card_date_text_size = self.rs_settings.get('CardDateTextSize')

        doc_list = widgets.CustomCards(
            widgets.LinearLayout(
                widgets.LinearLayout(
                    widgets.TextView(
                        weight=8,
                        width='match_parent',
                        Value='@type',
                        gravity_horizontal='right',
                        TextSize=title_text_size,
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
                        TextSize=card_title_text_size
                    )
                ),
                widgets.LinearLayout(
                    widgets.TextView(
                        Value='@countragent',
                        TextSize=card_date_text_size
                    ),
                    widgets.TextView(
                        Value='@warehouse',
                        TextSize=card_date_text_size
                    )
                ),
                width="match_parent"
            ),
            options=widgets.Options().options,
            cardsdata=table_data
        )

        return doc_list.to_json()

    # def barcode_scanned_async(self):
    #     if self.hash_map['barcode_scanned'] == 'true':
    #         doc = ui_global.Rs_doc
    #         doc.id_doc = hash_map.get('id_doc')
    #
    #         answer = http_exchange.post_goods_to_server(doc.id_doc, get_http_settings(hash_map))
    #
    #         if answer and answer.get('Error') is not None:
    #             hash_map.debug(answer.get('Error'))
    #
    #         doc_details_on_start(hash_map)
    #         hash_map.refresh_screen()
