import unittest
from unittest.mock import MagicMock

from ui_models import SeriesSelectScreen, SeriesItem
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
        qtty = 'qtty_123'

        sut = SeriesItem(self.hash_map, series_id='123')
        sut.service.get_series_data_by_id = MagicMock(return_value={
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
        self.assertEqual(self.hash_map['FillingSeriesScreen_qtty'], qtty)

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
        sut.service.add_new_series = MagicMock()
        sut.service.get_count_series = MagicMock(return_value=0)
        sut.hash_map['number'] = expect['name']
        sut.hash_map['best_before'] = expect['best_before']
        sut.hash_map['production_date'] = expect['production_date']
        sut.hash_map['FillingSeriesScreen_qtty'] = expect['qtty']

        sut.on_input()
        sut.service.add_new_series.assert_called_once_with(expect)
        self.assertFalse(sut.hash_map['toast'])

    def test_can_update_series(self):
        expect = self.get_series_data()
        expect['qtty'] = 6

        self.hash_map.hash_map.put('listener', 'btn_save')
        sut = SeriesItem(
            self.hash_map,
            series_id='111'
        )
        sut.screen_data = self.get_series_data()
        sut.service.update_series_by_id = MagicMock()
        sut.service.get_count_series = MagicMock(return_value=0)

        sut.hash_map['name'] = sut.screen_data['name']
        sut.hash_map['number'] = sut.screen_data['number']
        sut.hash_map['best_before'] = sut.screen_data['best_before']
        sut.hash_map['production_date'] = sut.screen_data['production_date']
        sut.hash_map['FillingSeriesScreen_qtty'] = 6

        sut.on_input()
        sut.service.update_series_by_id.assert_called_once_with(expect)
        self.assertFalse(sut.hash_map['toast'])

    def get_series_data(self):
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