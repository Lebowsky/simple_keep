import unittest
from unittest.mock import MagicMock

from ui_models import SeriesSelectScreen, SeriesItem
from db_services import SeriesService
from ui_utils import HashMap
from main import noClass

from data_for_tests.utils_for_tests import hashMap


class TestSeriesItem(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings')
        self.rs_settings.put('path_to_databases', './', True)

    def test_cant_show_not_inited_series_screen(self):
        sut = SeriesItem(self.hash_map)
        with self.assertRaises(ValueError):
            sut.show()

    def test_can_show_new_series_screen(self):
        expect = {
            'cell_id': '',
            'id_doc': '123',
            'item_id': '123',
            'property_id': '',
            'warehouse_id': ''
        }
        sut = SeriesItem(self.hash_map, id_doc='123', item_id='123')
        sut.show()

        actual = sut.screen_data
        self.assertEqual(expect, actual)

    def test_can_show_series_screen_by_series_id(self):
        name = 'name123'
        number = 'number123'
        production_date = 'production_date_123'
        best_before = 'best_before_123'
        qtty = 10

        sut = SeriesItem(self.hash_map, series_id='123')
        sut.service.get_series_item_data_by_id = MagicMock(return_value={
            'name': name,
            'best_before': best_before,
            'number': number,
            'production_date': production_date,
            'qtty': qtty,
        })
        sut.show()

        self.assertEqual(self.hash_map['name'], name)
        self.assertEqual(self.hash_map['best_before'], best_before)
        self.assertEqual(self.hash_map['number'], number)
        self.assertEqual(self.hash_map['production_date'], production_date)
        self.assertEqual(self.hash_map['FillingSeriesScreen_qtty'], str(qtty))

    def test_can_save_new_series(self):
        expect = self.get_series_data()
        self.hash_map.hash_map.put('listener', 'btn_save')
        sut = SeriesItem(
            self.hash_map,
            id_doc='111',
            item_id='222',
            property_id='333',
            warehouse_id='444',
            cell_id='555'
        )
        sut.service.get_count_series = MagicMock(return_value=0)
        sut.hash_map['number'] = expect['name']
        sut.hash_map['best_before'] = expect['best_before']
        sut.hash_map['production_date'] = expect['production_date']
        sut.hash_map['FillingSeriesScreen_qtty'] = expect['qtty']
        sut.on_input()

        self.assertFalse(sut.hash_map['toast'])
        self.assertIsNotNone(sut.data_to_save)

    def test_can_update_series(self):
        self.hash_map.hash_map.put('listener', 'btn_save')
        sut = SeriesItem(
            self.hash_map,
            series_id='111'
        )
        sut.screen_data = self.get_series_data()
        sut.service.get_count_series = MagicMock(return_value=0)

        sut.hash_map['name'] = sut.screen_data['name']
        sut.hash_map['number'] = sut.screen_data['number']
        sut.hash_map['best_before'] = sut.screen_data['best_before']
        sut.hash_map['production_date'] = sut.screen_data['production_date']
        sut.hash_map['FillingSeriesScreen_qtty'] = 6

        sut.on_input()
        self.assertFalse(sut.hash_map['toast'])
        self.assertIsNotNone(sut.data_to_save)
        self.assertEqual(sut.data_to_save['qtty'], 6)

    @staticmethod
    def get_series_data():
        return {
            'id_doc': '111',
            'item_id': '222',
            'property_id': '333',
            'warehouse_id': '444',
            'qtty': 5,
            'name': 'sn_123',
            'number': 'sn_123',
            'cell_id': '555',
            'best_before': '0001-01-01',
            'production_date': '0001-01-01',
        }

class TestSeriesSelectScreen(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings')
        self.rs_settings.put('path_to_databases', './', True)

    def test_can_init_screen_with_series(self):
        sut = SeriesSelectScreen(self.hash_map, doc_row_id='000')
        SeriesService.get_screen_data = MagicMock(return_value=self.get_screen_data())
        SeriesService.get_series_data = MagicMock(return_value=self.get_series_data())

        sut.init_screen()

        self.assertEqual(sut.hash_map['qtty'], '5.5')
        self.assertEqual(sut.hash_map['qtty_plan'], '10')
        self.assertTrue(sut.hash_map.get_json('series_cards')['customcards']['cardsdata'])
        self.assertFalse(self.hash_map.containsKey('empty_series'))

    def test_can_init_screen_without_series(self):
        sut = SeriesSelectScreen(self.hash_map, doc_row_id='000')
        SeriesService.get_screen_data = MagicMock(return_value=self.get_screen_data())
        SeriesService.get_series_data = MagicMock(return_value={})
        sut.init_screen()

        self.assertIsNone(self.hash_map['series_cards'])
        self.assertTrue(self.hash_map.containsKey('empty_series'))

    def test_can_add_series_item_by_barcode(self):
        self.hash_map.hash_map.put('listener', 'barcode')
        sut = SeriesSelectScreen(self.hash_map, doc_row_id='000')
        SeriesService.get_screen_data = MagicMock(return_value=self.get_screen_data())
        SeriesService.get_series_data = MagicMock(return_value=self.get_series_data())
        sut.init_screen()
        sut.hash_map['barcode'] = '4567'

        sut.on_input()

        self.assertTrue(sut.series_item_data_to_save)
        self.assertEqual(sut.series_item_data_to_save['qtty'], 1)

    def test_can_add_qty_item_by_barcode(self):
        self.hash_map.hash_map.put('listener', 'barcode')
        sut = SeriesSelectScreen(self.hash_map, doc_row_id='000')
        SeriesService.get_screen_data = MagicMock(return_value=self.get_screen_data())
        SeriesService.get_series_data = MagicMock(return_value=self.get_series_data())
        sut.init_screen()
        sut.hash_map['barcode'] = '456'

        sut.on_input()
        print(sut.series_item_data_to_save)
        self.assertTrue(sut.series_item_data_to_save)
        self.assertEqual(sut.series_item_data_to_save['qtty'], 6)


    @staticmethod
    def get_screen_data():
        return {
            'id_doc': '111',
            'item_id': '222',
            'property_id': '333',
            'unit_id': '444',
            'qtty': 5.5,
            'qtty_plan': 10.0,
            'price': 5000,
            'item_name': 'item_name',
            'article': 'article',
            'property': 'property',
            'unit': 'unit',
            'cell_id': '555'
        }

    @staticmethod
    def get_series_data():
        return [
            {
                'key': 1,
                'qtty': 3,
                'name': 'sn_name_1',
                'number': 'sn_number_1',
                'best_before': '0001-01-01',
                'production_date': '0001-01-01',
            },
            {
                'key': 2,
                'qtty': 2,
                'name': 'sn_name_2',
                'number': 'sn_number_2',
                'best_before': '0001-01-01',
                'production_date': '0001-01-01',
            },
            {
                'key': 3,
                'qtty': 5,
                'name': 'sn_name_3',
                'number': '456',
                'best_before': '0001-01-01',
                'production_date': '0001-01-01',
            },
        ]

    @staticmethod
    def get_series_item_data_to_save():
        return {
            'id': 2,
            'id_doc': '111',
            'id_good': '222',
            'id_properties': '333',
            'id_unit': '',
            'cell': '555',
            'name': 'sn_name_3',
            'number': 'sn_name_3',
            'best_before': '0001-01-01',
            'production_date': '0001-01-01',
            'qtty': 6
        }
