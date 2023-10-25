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

    def test_can_show_new_item_screen(self):
        sut = SeriesItem(self.hash_map)
        sut.show()

        self.assertEqual(self.hash_map['name'], '')
        self.assertEqual(self.hash_map['best_before'], '')
        self.assertEqual(self.hash_map['number'], '')
        self.assertEqual(self.hash_map['production_date'], '')
        self.assertEqual(self.hash_map['FillingSeriesScreen_qtty'], '0')

    def test_can_show_series_screen(self):
        series_item_data = self.get_series_item_data()
        sut = SeriesItem(self.hash_map, series_item_data=series_item_data)
        sut.show()

        self.assertEqual(self.hash_map['name'], series_item_data['name'])
        self.assertEqual(self.hash_map['best_before'], series_item_data['best_before'])
        self.assertEqual(self.hash_map['number'], series_item_data['number'])
        self.assertEqual(self.hash_map['production_date'], series_item_data['production_date'])
        self.assertEqual(self.hash_map['FillingSeriesScreen_qtty'], str(series_item_data['qtty']))

    def test_can_save_new_series(self):
        series_item_data = self.get_series_item_data()

        self.hash_map.hash_map.put('listener', 'btn_save')
        sut = SeriesItem(
            self.hash_map,
            series_item_data=self.get_empty_series_item_data(),
            is_new_item=True,
        )
        sut.show()
        sut.hash_map['name'] = series_item_data['name']
        sut.hash_map['best_before'] = series_item_data['best_before']
        sut.hash_map['number'] = series_item_data['number']
        sut.hash_map['production_date'] = series_item_data['production_date']
        sut.hash_map['FillingSeriesScreen_qtty'] = '6'
        sut.on_input()

        self.assertFalse(sut.hash_map['toast'])
        self.assertIsNotNone(sut.data_to_save)
        self.assertEqual(sut.data_to_save['qtty'], 6)

    def test_must_set_error_toast(self):
        series_item_data = self.get_series_item_data()
        self.hash_map.hash_map.put('listener', 'btn_save')
        sut = SeriesItem(
            self.hash_map,
            series_item_data=self.get_empty_series_item_data(),
            is_new_item=True,
            series_barcode_data = {'sn_123': ''}
        )
        sut.show()
        sut.hash_map['name'] = series_item_data['name']
        sut.hash_map['best_before'] = series_item_data['best_before']
        sut.hash_map['number'] = ''
        sut.hash_map['production_date'] = series_item_data['production_date']
        sut.hash_map['FillingSeriesScreen_qtty'] = '6'

        self.assertFalse(sut.hash_map['toast'])
        sut.on_input()
        self.assertTrue(sut.hash_map['toast'])
        self.assertIsNone(sut.data_to_save)

        sut.hash_map['number'] = series_item_data['number']
        sut.on_input()
        self.assertTrue(sut.hash_map['toast'])
        self.assertIsNone(sut.data_to_save)

    def test_can_update_series(self):
        series_item_data = self.get_series_item_data()

        self.hash_map.hash_map.put('listener', 'btn_save')
        sut = SeriesItem(
            self.hash_map,
            series_item_data=series_item_data
        )

        sut.hash_map['name'] = sut.screen_data['name']
        sut.hash_map['number'] = sut.screen_data['number']
        sut.hash_map['best_before'] = sut.screen_data['best_before']
        sut.hash_map['production_date'] = sut.screen_data['production_date']
        sut.hash_map['FillingSeriesScreen_qtty'] = 6

        sut.on_input()

        self.assertFalse(sut.hash_map['toast'])
        self.assertIsNotNone(sut.data_to_save)
        self.assertEqual(sut.data_to_save['qtty'], 6)
        print(sut.data_to_save)


    @staticmethod
    def get_series_item_data():
        return {
            'id': '001',
            'key': '001',
            'id_doc': '111',
            'item_id': '222',
            'property_id': '333',
            'warehouse_id': '444',
            'qtty': 5,
            'name': 'sn_123',
            'number': 'sn_123',
            'cell_id': '555',
            'best_before': '<..>',
            'production_date': '0001-01-01',
        }

    def get_empty_series_item_data(self):
        return {
            'id': None,
            'key': None,
            'id_doc': '111',
            'item_id': '222',
            'property_id': '333',
            'warehouse_id': '444',
            'cell_id': '555',
            'qtty': 0,
            'name': '',
            'number': '',
            'best_before': '',
            'production_date': '',
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
        self.assertEqual(self.hash_map['Show_empty_series'], '-1')

    def test_can_init_screen_without_series(self):
        sut = SeriesSelectScreen(self.hash_map, doc_row_id='000')
        SeriesService.get_screen_data = MagicMock(return_value=self.get_screen_data())
        SeriesService.get_series_data = MagicMock(return_value={})
        sut.init_screen()

        self.assertFalse(self.hash_map['series_cards'])
        self.assertEqual(self.hash_map['Show_empty_series'], '1')

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
