import unittest
from unittest.mock import MagicMock

from ui_models import GoodsListScreen, SelectGoodsType, ItemCard
from ui_utils import HashMap
from main import noClass

from data_for_tests.utils_for_tests import hashMap


class TestModelGoodsListScreen(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings_local')
        self.sut = GoodsListScreen(self.hash_map, self.rs_settings)

    def test_on_back_pressed_must_set_hash_map_value_BackScreen(self):
        # init test data
        self.sut.listener = 'ON_BACK_PRESSED'

        # execute test method
        self.sut.on_input()
        actual = self.hash_map.containsKey('FinishProcess')

        # assert test method results
        self.assertTrue(actual)

    def test_on_select_type_good_hash_map_value_ShowScreen(self):
        expect = 'Выбор категории товаров'

        # init test data
        self.sut.listener = 'select_goods_type'

        # execute test method
        self.sut.on_input()

        # init test data
        actual = self.hash_map['ShowScreen']

        # assert test method results
        self.assertEqual(expect, actual)

    def test_on_cards_click_hash_map_values_selected_card(self):
        # init test data
        self.sut.listener = 'CardsClick'
        selected_card_data = {
            'key': 'key_id_123',
            'code': 'code_123',
            'name': 'name_123',
            'art': 'art_123',
            'unit': 'unit_123',
            'type_good': 'type_good_123',
            'description': 'description_123'
        }
        self.sut.hash_map.put("selected_card_data", selected_card_data, to_json=True)

        # execute test method
        self.sut.on_input()
        taken_card_data = self.hash_map.get('selected_card_data', from_json=True)

        self.assertDictEqual(selected_card_data, taken_card_data)

    def test_barcode_returns_hash_map_values_if_found(self):
        # init test data
        id_good_data = [{
            'id_good': 'dee6e19a-55bc-11d9-848a-00112f43529a'
        }]

        item_data = [{
            'id': 'dee6e19a-55bc-11d9-848a-00112f43529a',
            'code': 'Телевизор "JVC"',
            'name': 'Т-123456',
            'art': '000000082',
            'unit': "—",
            'type_good': "Телевизоры",
            'description': "—"
        }]

        expect = item_data[0]['name']

        self.sut.listener = 'barcode'
        self.sut.hash_map.put('barcode', '2000000058160')

        self.sut.service.get_values_from_barcode = MagicMock()
        self.sut.service.get_values_from_barcode.return_value = id_good_data
        self.sut.service.get_goods_list_data = MagicMock()
        self.sut.service.get_goods_list_data.return_value = item_data

        # execute test method
        self.sut.on_input()

        # assert test method results
        self.sut.service.get_values_from_barcode.assert_called_once_with('barcode', '2000000058160')
        self.sut.service.get_goods_list_data.assert_called_once()
        actual = self.sut.hash_map.get('good_name')
        self.assertEqual(expect, actual)

    def test_barcode_returns_hash_map_values_if_not_found(self):
        expect = "Товар не распознан по штрихкоду"

        # init test data
        self.sut.listener = 'barcode'
        self.sut.hash_map.put('barcode', '2000000058161')

        self.sut.service.get_values_from_barcode = MagicMock()
        self.sut.service.get_values_from_barcode.return_value = []

        # execute test method
        self.sut.on_input()

        # assert test method results
        self.sut.service.get_values_from_barcode.assert_called_once_with('barcode', '2000000058161')
        self.assertEqual(expect, self.sut.hash_map.get('toast'))


class TestModelSelectGoodsType(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings_local')
        self.sut = SelectGoodsType(self.hash_map, self.rs_settings)

    def test_on_back_pressed_must_set_hash_map_value_BackScreen(self):
        # init test data
        self.sut.listener = 'ON_BACK_PRESSED'

        # execute test method
        self.sut.on_input()
        actual = self.hash_map.containsKey('BackScreen')

        # assert test method results
        self.assertTrue(actual)
        self.assertEqual("", self.sut.hash_map.get('select_goods_type'))
        self.assertEqual("", self.sut.hash_map.get('selected_goods_type'))

    def test_on_cards_click_hash_map_values_selected_card(self):
        # init test data
        self.sut.listener = 'CardsClick'
        selected_card_data = {
            'key': 'f93e1126-c83a-11e2-8026-0015e9b8c48d',
            'name': 'Тара',
        }
        self.sut.hash_map.put("selected_card_data", selected_card_data, to_json=True)

        # execute test method
        self.sut.on_input()
        taken_card_data = self.hash_map.get('selected_card_data', from_json=True)

        self.assertDictEqual(selected_card_data, taken_card_data)


class TestModelItemCard(unittest.TestCase):
    def setUp(self) -> None:
        self.hash_map = HashMap(hash_map=hashMap())
        self.rs_settings = noClass('rs_settings_local')
        self.sut = ItemCard(self.hash_map, self.rs_settings)

    def test_on_back_pressed_must_set_hash_map_value_BackScreen(self):
        # init test data
        self.sut.listener = 'ON_BACK_PRESSED'
        self.hash_map.put('barcode_cards', '23213213')

        # execute test method
        self.sut.on_input()
        actual = self.hash_map.containsKey('BackScreen')

        # assert test method results
        self.assertTrue(actual)
        self.assertEqual("", self.sut.hash_map.get('barcode_cards'))
